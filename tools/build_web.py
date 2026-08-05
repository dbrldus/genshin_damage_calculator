"""웹 배포용 엔진 번들을 만든다.

    python tools/build_web.py

gidc/ 패키지 전체를 web/engine.zip 으로 묶는다. 브라우저에서 Pyodide가
unpackArchive()로 가상 파일시스템에 풀어 그대로 import 한다.
외부 의존성이 0(순수 stdlib)이라 wheel 빌드도 micropip도 필요 없다.

여기는 "묶기"만 한다. 검사·캐시 갱신·로컬 서버까지 한 번에 하려면
tools/sync_web.py 를 쓴다 (이 모듈의 build()를 그대로 부른다).
"""
import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PKG  = ROOT / "gidc"
OUT  = ROOT / "web" / "engine.zip"

SKIP_DIRS  = {"__pycache__"}
SKIP_SUFFIX = {".pyc", ".pyo"}


def iter_sources():
    for p in sorted(PKG.rglob("*")):
        if not p.is_file():
            continue
        parts = p.relative_to(ROOT).parts
        if SKIP_DIRS & set(parts):
            continue
        # 점으로 시작하는 것은 소스가 아니라 도구가 흘린 것이다(.omc/, .DS_Store …).
        # gidc/ 안에는 점으로 시작하는 정상 파일이 없으므로 통째로 걷어 낸다 —
        # 한 번 섞이면 배포 번들에 조용히 실려 나간다.
        if any(part.startswith(".") for part in parts):
            continue
        if p.suffix in SKIP_SUFFIX:
            continue
        yield p


def build() -> tuple[int, int, int]:
    """engine.zip 을 새로 쓴다. (파일 수, 원본 바이트, 압축 바이트)"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for src in iter_sources():
            z.write(src, src.relative_to(ROOT).as_posix())
            n += 1

    raw = sum(p.stat().st_size for p in iter_sources())
    return n, raw, OUT.stat().st_size


def main() -> None:
    n, raw, packed = build()
    print(f"{OUT.relative_to(ROOT)}  —  {n}개 파일")
    print(f"  원본 {raw/1024:7.1f} KB")
    print(f"  압축 {packed/1024:7.1f} KB")


if __name__ == "__main__":
    # 리다이렉트 시 로케일 인코딩(Windows cp949)이 —(U+2014)를 못 써서 죽는다. bench.py와 동일.
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure") and not _stream.isatty():
            _stream.reconfigure(encoding="utf-8")
    main()
