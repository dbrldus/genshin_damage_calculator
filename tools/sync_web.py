"""파이썬 엔진의 변경을 웹에 반영한다.

    python tools/sync_web.py                # 검사 → 번들 → 캐시 버전 갱신
    python tools/sync_web.py --serve        # 위 + http://localhost:8000
    python tools/sync_web.py --watch --serve # 파일 저장할 때마다 자동 반영

엔진을 고친 뒤 브라우저에 나타나기까지 손이 가는 일이 세 가지다. 이 스크립트가
그 셋을 한 번에 한다.

  1. 검사  — 별도 인터프리터로 gidc.web_api 를 임포트해 페이지가 하는 호출
            (레지스트리 → 빌드시트 → run_calculation)을 그대로 한 바퀴 돌린다.
            파티는 개발용 _presets/ 에서 가져온다 — 아래 CHECK_PARTY 주석 참고.
            깨진 엔진을 engine.zip 에 굽고 나서 Pyodide 콘솔에서 발견하는 것보다
            여기서 파이썬 트레이스백으로 보는 편이 훨씬 빠르다.
            실패하면 번들을 건드리지 않으므로 web/ 은 마지막으로 성공한 상태에 남는다.
  2. 번들  — tools/build_web.py 의 build(). gidc/ 전체를 web/engine.zip 으로.
  3. 캐시  — index.html 의 app.js?v= 를 app.js 내용 해시로 바꾼다. 손으로 숫자를
            올리는 걸 잊어 옛 app.js 가 도는 사고를 없앤다. engine.zip 은 app.js 가
            cache:"no-cache" 로 받으므로 따로 손대지 않는다.

--serve 로 띄우는 서버는 no-store 를 붙인다. python -m http.server 는 캐시 헤더를
안 붙여서 브라우저가 옛 파일을 계속 쓴다.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import json
import re
import subprocess
import sys
import threading
import time
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_web

ROOT  = build_web.ROOT
WEB   = ROOT / "web"
INDEX = WEB / "index.html"
APPJS = WEB / "app.js"

# <script src="app.js?v=3"> — ?v= 가 아예 없는 형태도 받는다.
APPJS_TAG  = re.compile(r'(src=")app\.js(?:\?v=[^"]*)?(")')

# 검사 파티. 페이지는 빈 파티로 뜨고 프리셋을 아예 모르지만(엔진에서 빠졌다), 검사는
# 무기·성유물·명함이 다 박힌 캐릭터로 돌려야 값어치가 있다 — 맨몸 넷으로는 무기 패시브도
# 성유물 세트 효과도 버프 상호작용도 한 번을 안 지난다. 그래서 개발용 _presets/ 를 쓴다.
CHECK_PARTY = ["skirk_party/skirk", "skirk_party/furina",
               "skirk_party/escoffier", "skirk_party/mona"]

# 페이지가 쓰는 호출로 엔진을 한 바퀴 돈다. 별도 프로세스로 도는 이유는 --watch 중에
# 이미 임포트된 낡은 모듈을 다시 쓰지 않기 위해서다.
CHECK_SRC = r"""
import json, sys
from gidc.web_api import get_registries, char_to_spec, run_calculation
from _presets import PRESET_REGISTRY, build_preset

reg  = get_registries()
refs = sys.argv[1:]

missing = [r for r in refs if r not in PRESET_REGISTRY]
if missing:
    sys.exit("검사 파티의 프리셋이 없습니다: " + ", ".join(missing))

for name in sorted(PRESET_REGISTRY):   # 검사 파티에 없는 프리셋도 조립까지는 확인한다
    char_to_spec(build_preset(name))

party = [char_to_spec(build_preset(r)) for r in refs]
out   = run_calculation({
    "party":    party,
    "enemy":    {"level": 100},
    "settings": {"charLevel": 90, "targets": []},
})
if out["errors"]:
    sys.exit("계산이 오류를 돌려줬습니다: " + json.dumps(out["errors"], ensure_ascii=False))
# damage["chars"]는 캐릭터 블록이고 히트는 그 안에 있다 — 블록 수만 세면 전원의 히트가
# 통째로 비어도 통과한다. damage["lunar"]·["stellar"]는 파티 공용 반응 행이라 블록 밖이다.
hits      = sum(len(b["hits"]) for b in out["damage"]["chars"])
reactions = sum(len(b["reactions"]) for b in out["damage"]["chars"])
lunar     = len(out["damage"]["lunar"])
stellar   = len(out["damage"]["stellar"])
if not hits:
    sys.exit("히트가 하나도 안 나왔습니다 — 프로필 조립이 조용히 비었습니다.")

print(json.dumps({
    "counts":    reg["counts"],
    "presets":   len(PRESET_REGISTRY),
    "chars":     len(out["stats"]),
    "hits":      hits,
    "reactions": reactions,
    "lunar":     lunar,
    "stellar":   stellar,
    "questions": len(out["questions"]),
    "pending":   len(out["pending"]),
}, ensure_ascii=False))
"""


# ── 1. 검사 ──────────────────────────────────────────────────────────────
def check() -> dict | None:
    """엔진을 한 바퀴 돌려 본다. 성공하면 요약 dict, 실패하면 None(사유는 이미 출력)."""
    proc = subprocess.run(
        [sys.executable, "-c", CHECK_SRC, *CHECK_PARTY],
        cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        print("✗ 엔진 검사 실패 — 번들은 그대로 둡니다.\n")
        print((proc.stderr or proc.stdout).rstrip())
        return None

    summary = json.loads(proc.stdout.strip().splitlines()[-1])
    print(f"✓ 검사   캐릭터 {summary['counts']['characters']} / "
          f"무기 {summary['counts']['weapons']} / "
          f"성유물 {summary['counts']['artifactSets']}세트 · "
          f"프리셋 {summary['presets']}개")
    print(f"         검사 파티 {summary['chars']}명 · 히트 {summary['hits']}개 · "
          f"반응 {summary['reactions']}개 · "
          f"질문 {summary['questions']}개(미답 {summary['pending']})")
    return summary


# ── 3. 캐시 버전 ─────────────────────────────────────────────────────────
def bust_cache() -> str:
    """index.html 의 app.js?v= 를 app.js 내용 해시로 맞춘다. 바뀔 때만 쓴다.

    줄바꿈은 지우고 해시한다. core.autocrlf 로 체크아웃마다 CRLF/LF 가 바뀌면
    내용이 같은데도 버전이 흔들려 index.html 에 헛 diff 가 생긴다."""
    raw    = APPJS.read_bytes().replace(b"\r\n", b"\n")
    digest = hashlib.sha256(raw).hexdigest()[:8]
    html   = INDEX.read_text(encoding="utf-8")
    new    = APPJS_TAG.sub(rf"\1app.js?v={digest}\2", html)

    if new == html:
        print(f"· 캐시   app.js?v={digest} (그대로)")
    else:
        INDEX.write_text(new, encoding="utf-8")
        print(f"✓ 캐시   app.js?v={digest}")
    return digest


def sync() -> bool:
    """검사 → 번들 → 캐시. 검사가 실패하면 아무것도 안 바꾸고 False."""
    if check() is None:
        return False

    n, raw, packed = build_web.build()
    print(f"✓ 번들   web/engine.zip — {n}개 파일 · "
          f"{raw/1024:.0f}KB → {packed/1024:.0f}KB")
    bust_cache()
    return True


# ── 서버 ─────────────────────────────────────────────────────────────────
class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, fmt, *args):        # 요청 로그는 반영 로그를 덮기만 한다
        pass


def make_server(port: int) -> http.server.ThreadingHTTPServer:
    handler = functools.partial(NoCacheHandler, directory=str(WEB))
    return http.server.ThreadingHTTPServer(("", port), handler)


# ── 감시 ─────────────────────────────────────────────────────────────────
def snapshot() -> dict[pathlib.Path, int]:
    """반영에 영향을 주는 파일들의 수정 시각. index.html 은 우리가 고치므로 포함해
    두고(직접 편집도 감지된다), 스냅샷은 항상 sync 뒤에 새로 뜬다."""
    files = list(build_web.iter_sources()) + [APPJS, INDEX]
    out = {}
    for p in files:
        try:
            out[p] = p.stat().st_mtime_ns
        except OSError:                        # 저장 도중 사라진 파일은 다음 턴에 잡힌다
            pass
    return out


def watch(interval: float = 0.5) -> None:
    seen = snapshot()
    print("\n감시 중 — gidc/**/*.py · web/app.js  (Ctrl+C 로 종료)")
    while True:
        time.sleep(interval)
        now = snapshot()
        if now == seen:
            continue

        changed = sorted(p for p in set(now) | set(seen) if now.get(p) != seen.get(p))
        stamp   = time.strftime("%H:%M:%S")
        print(f"\n[{stamp}] 변경 {len(changed)}건 — "
              + ", ".join(p.relative_to(ROOT).as_posix() for p in changed[:3])
              + (" …" if len(changed) > 3 else ""))
        sync()
        seen = snapshot()          # 캐시 갱신으로 우리가 건드린 index.html 을 흡수한다


def main() -> int:
    ap = argparse.ArgumentParser(description="파이썬 엔진 변경을 web/ 에 반영한다.")
    ap.add_argument("--serve", action="store_true", help="web/ 을 로컬 서버로 띄운다")
    ap.add_argument("--watch", action="store_true", help="파일이 바뀔 때마다 다시 반영한다")
    ap.add_argument("--port", type=int, default=8000, help="--serve 포트 (기본 8000)")
    args = ap.parse_args()

    ok = sync()
    if not ok and not args.watch:
        return 1                   # 검사 실패는 CI에서 그대로 실패로 잡히게 한다

    if args.serve:
        server = make_server(args.port)
        print(f"\n▶ http://localhost:{args.port}/  (Cache-Control: no-store)")
        if not args.watch:
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\n종료")
            return 0
        threading.Thread(target=server.serve_forever, daemon=True).start()

    if args.watch:
        try:
            watch()
        except KeyboardInterrupt:
            print("\n종료")
    return 0


if __name__ == "__main__":
    # 리다이렉트 시 로케일 인코딩(Windows cp949)이 —(U+2014)를 못 써서 죽는다. bench.py와 동일.
    # line_buffering 은 --watch 용이다. 파일로 넘기면 블록 버퍼가 되어 반영 로그가
    # 프로세스가 끝날 때까지 안 보인다.
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure") and not _stream.isatty():
            _stream.reconfigure(encoding="utf-8", line_buffering=True)
    sys.exit(main())
    
