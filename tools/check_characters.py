"""등록된 캐릭터를 훑어 「조용히 틀리는」 것들을 잡는다.

    python tools/check_characters.py           # 전원 점검
    python tools/check_characters.py 얀사 모나  # 일부만
    python tools/check_characters.py --quiet   # 문제 있는 캐릭터만 출력

여기서 잡는 것은 전부 **예외도 경고도 나지 않고 지나가는** 종류다. 계산이 멈추지 않고
숫자만 조용히 틀리므로, 캐릭터를 추가한 뒤에는 이 스크립트를 한 번 돌린다.

FAIL — 숫자가 틀어진다 (종료 코드 1)
  · ascension_stat 미선언 → 어센션 보너스가 통째로 0이 된다 (기본값이 None이다)
  · stat_key가 기초 스탯 표에 없음 → 기초 HP/공격력/방어력을 못 읽는다
  · **특성 레벨로 인덱싱되는** 계수 표가 `*_TABLES`에 미등록 → clamp_talent_index의 경고가
    죽어 계수 누락이 안 드러난다
  · 표 길이 < 최대 실효 레벨(명함 포함) → 마지막 레벨로 조용히 잘려 쓰인다
  · CHARACTER_REGISTRY 미등록 → make_character가 DefaultCharacter로 조용히 대체한다
  · element 프로퍼티가 파일이 놓인 원소 디렉터리와 다름
  · build_hits가 예외를 낸다

WARN — 사람이 판단할 자리
  · 히트 이름 중복 → build_hits 끝의 `{h.name: h}`에서 하나가 소리 없이 사라진다
  · 계수 표가 단조 수열이 아님 → 옮겨 적다 틀렸을 가능성
  · 다른 축으로 인덱싱되거나 아무 데도 안 쓰이는 계수 표 → 레벨 표가 아니라면 클래스에
    `NON_TALENT_TABLES = (_표이름,)`으로 선언해 끈다 (나비아의 장미탄 개수 표가 그 예다)
  · `TODO(생성기)` 잔존 → tools/new_character.py가 남긴 자리를 아직 안 채웠다
  · 「의도적 미구현」 블록 없음 → 다음 사람이 누락과 구별할 수 없다
  · 특성 레벨 클램프 경고가 실제로 발생

참고 — 세지 않는다
  · `_specs/characters/<모듈>.txt` 스펙 파일 없음 → 스펙 양식 도입 전에 손으로 만든 캐릭터
"""
from __future__ import annotations

import argparse
import ast
import csv
import inspect
import pathlib
import sys
import warnings
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from gidc.content.characters import CHARACTER_REGISTRY
from gidc.core.character import Character
from gidc.core.profile import SkillHit
from gidc.enums import Element

ROOT       = pathlib.Path(__file__).resolve().parent.parent
CHARACTERS = ROOT / "gidc" / "content" / "characters"
SPECS      = ROOT / "_specs" / "characters"
BASE_VALUE = ROOT / "gidc" / "core" / "data" / "character_level_scaling" / "character_base_value.csv"

TALENTS = (
    ("일반 공격", "NA_TABLES",    "NA_LEVEL_UP_CONSTELLATION",    "NA_PASSIVE_LEVEL_UP"),
    ("원소 스킬", "SKILL_TABLES", "SKILL_LEVEL_UP_CONSTELLATION", "SKILL_PASSIVE_LEVEL_UP"),
    ("원소 폭발", "BURST_TABLES", "BURST_LEVEL_UP_CONSTELLATION", "BURST_PASSIVE_LEVEL_UP"),
)


class Report:
    def __init__(self, label: str) -> None:
        self.label = label
        self.fail: list[str] = []
        self.warn: list[str] = []
        self.note: list[str] = []   # 참고 — 세지 않고, --quiet에서는 숨긴다

    def F(self, msg: str) -> None: self.fail.append(msg)
    def W(self, msg: str) -> None: self.warn.append(msg)
    def N(self, msg: str) -> None: self.note.append(msg)

    @property
    def clean(self) -> bool:
        return not self.fail and not self.warn


def base_value_names() -> set[str]:
    with BASE_VALUE.open(encoding="utf-8") as fp:
        return {row["character"] for row in csv.DictReader(fp)}


def talent_indexed_tables(path: pathlib.Path) -> tuple[set[str], dict[str, str]]:
    """`self._TABLE[...]` 을 전부 찾아 **무엇으로 인덱싱되는지** 가른다.

    미등록 표를 무조건 FAIL로 두면 오탐이 난다 — 나비아의 `_SKILL_ROSULA_SHARDSHOT_COEFF_AMP`는
    특성 레벨이 아니라 **맞은 장미탄 개수**로 인덱싱되므로 `*_TABLES`에 들어가면 안 된다.
    그래서 「특성 레벨로 인덱싱되는데 등록이 빠진 표」만 FAIL로 올린다.

    반환: (특성 레벨로 인덱싱되는 표 이름, 그 밖의 표 이름 → 인덱스 식)
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    talent_calls = {"_na_index", "_skill_index", "_burst_index"}
    talent: set[str] = set()
    other: dict[str, str] = {}

    def is_talent_call(node: ast.AST) -> bool:
        return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in talent_calls)

    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # 함수 안에서 `sk = self._skill_index()` 로 받아 둔 지역 변수도 특성 인덱스로 본다.
        aliases = {
            t.id
            for stmt in ast.walk(fn) if isinstance(stmt, ast.Assign) and is_talent_call(stmt.value)
            for t in stmt.targets if isinstance(t, ast.Name)
        }
        for node in ast.walk(fn):
            if not (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute)
                    and isinstance(node.value.value, ast.Name) and node.value.value.id == "self"):
                continue
            table = node.value.attr
            idx   = node.slice
            if is_talent_call(idx) or (isinstance(idx, ast.Name) and idx.id in aliases):
                talent.add(table)
            else:
                other.setdefault(table, ast.unparse(idx))
    return talent, {k: v for k, v in other.items() if k not in talent}


def is_table(value) -> str | None:
    """1차원 계수 표인지, 단수별 행 묶음(2차원)인지."""
    def nums(seq):
        return isinstance(seq, list) and bool(seq) and all(isinstance(x, (int, float)) for x in seq)
    if nums(value):
        return "1d"
    if isinstance(value, list) and value and all(nums(r) for r in value):
        return "2d"
    return None


def collect_hits(char: Character) -> tuple[dict[str, SkillHit], list[str], list[warnings.WarningMessage]]:
    """build_hits를 돌리면서 **만들어진** 히트 이름을 전부 기록한다.

    반환된 dict만 보면 이름이 겹쳐 접힌 히트를 알 수 없다 — 생성 시점에 세어야 보인다."""
    created: list[str] = []
    original = SkillHit.__init__

    def spy(self, *args, **kwargs):
        original(self, *args, **kwargs)
        if self.name:
            created.append(self.name)

    SkillHit.__init__ = spy
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            hits = char.build_hits()
    finally:
        SkillHit.__init__ = original
    return hits, created, list(caught)


def check_character(kr_name: str, cls: type[Character], names: set[str]) -> Report:
    rep = Report(f"{kr_name} ({cls.__name__})")

    # ── 선언 ────────────────────────────────────────────────────────────────
    if getattr(cls, "ascension_stat", None) is None:
        rep.F("ascension_stat 미선언 — 어센션 보너스가 0으로 계산됩니다.")
    if getattr(cls, "weapon_type", None) is None:
        rep.F("weapon_type 미선언 — 무기 종류 검증이 꺼집니다.")
    if cls.rarity not in (4, 5):
        rep.F(f"rarity={cls.rarity} — 4 또는 5여야 기초 스탯 곡선이 맞습니다.")

    stat_key = getattr(cls, "stat_key", "") or cls.__name__
    if stat_key not in names:
        rep.F(f"stat_key '{stat_key}'가 기초 스탯 표에 없습니다 "
              f"({BASE_VALUE.relative_to(ROOT)}). 기초 HP/공격력/방어력을 못 읽습니다.")

    try:
        char = cls()
    except Exception as e:
        rep.F(f"인스턴스를 만들 수 없습니다: {type(e).__name__}: {e}")
        return rep

    # 파일이 놓인 원소 디렉터리와 element 프로퍼티가 같아야 한다.
    module_path = pathlib.Path(inspect.getfile(cls))
    dir_element = module_path.parent.name
    try:
        element: Element = char.element
    except Exception as e:
        rep.F(f"element 프로퍼티가 실패합니다: {type(e).__name__}: {e}")
        element = None
    if element is not None and element.name.lower() != dir_element:
        rep.F(f"element={element.name}인데 파일은 '{dir_element}/'에 있습니다.")

    # ── 계수 표 등록 ────────────────────────────────────────────────────────
    registered: set[int] = set()
    for _label, attr, _c, _p in TALENTS:
        for t in getattr(cls, attr, ()):
            registered.add(id(t))

    # 클래스가 「이건 특성 레벨 표가 아니다」라고 직접 선언했으면 그 말을 믿는다.
    declared_non_talent = {id(t) for t in getattr(cls, "NON_TALENT_TABLES", ())}
    talent_idx, other_idx = talent_indexed_tables(module_path)

    for name, value in vars(cls).items():
        kind = is_table(value)
        if kind is None or not name.startswith("_"):
            continue
        if kind == "1d" and id(value) not in registered and id(value) not in declared_non_talent:
            if name in talent_idx:
                rep.F(f"계수 표 {name}은 특성 레벨로 인덱싱되는데 NA/SKILL/BURST_TABLES에 "
                      f"없습니다 — 레벨 클램프 경고가 이 표에서 죽습니다.")
            elif name in other_idx:
                rep.W(f"계수 표 {name}은 `[{other_idx[name]}]`으로 인덱싱됩니다 — 특성 레벨 표가 "
                      f"아니라면 `NON_TALENT_TABLES`에 선언해 이 경고를 끄세요.")
            else:
                rep.W(f"계수 표 {name}이 어디서도 인덱싱되지 않습니다 — 레벨로 쓸 표라면 "
                      f"*_TABLES에 등록하고, 참고용 자료라면 `NON_TALENT_TABLES`에 선언하세요.")
        if kind == "2d" and id(value) not in declared_non_talent:
            missing = [i + 1 for i, row in enumerate(value)
                       if id(row) not in registered and id(row) not in declared_non_talent]
            if missing:
                rep.F(f"계수 표 {name}의 {missing}행이 *_TABLES에 없습니다 "
                      f"(2차원 표는 `(*{name}, …)`으로 행을 펼쳐 등록합니다).")

    # ── 표 길이 vs 최대 실효 레벨 ───────────────────────────────────────────
    for label, attr, const_attr, passive_attr in TALENTS:
        tables = getattr(cls, attr, ())
        if not tables:
            continue
        need = cls.MAX_TALENT_LEVEL + getattr(cls, passive_attr, 0)
        if getattr(cls, const_attr, 0):
            need += cls.CONSTELLATION_LEVEL_UP
        short = [len(t) for t in tables if len(t) < need]
        if short:
            rep.F(f"[{label}] 계수 표가 최대 실효 레벨 L{need}에 못 미칩니다 "
                  f"(가장 짧은 표 {min(short)}칸) — 조용히 마지막 레벨로 잘려 쓰입니다.")
        lengths = {len(t) for t in tables}
        if len(lengths) > 1:
            rep.W(f"[{label}] 표 길이가 서로 다릅니다: {sorted(lengths)} — "
                  f"한 특성의 계수 표는 보통 레벨 수가 같습니다.")
        for i, t in enumerate(tables):
            up   = all(b >= a for a, b in zip(t, t[1:]))
            down = all(b <= a for a, b in zip(t, t[1:]))
            if not (up or down):
                rep.W(f"[{label}] {attr}[{i}]가 단조 수열이 아닙니다 — 옮겨 적다 틀렸을 수 있습니다.")

    # ── build_hits ──────────────────────────────────────────────────────────
    for constellation in (0, 6):
        char = cls()
        char.constellation = constellation
        try:
            hits, created, caught = collect_hits(char)
        except Exception as e:
            rep.F(f"C{constellation}에서 build_hits가 실패합니다: {type(e).__name__}: {e}")
            continue
        if not hits:
            rep.W(f"C{constellation}에서 히트가 하나도 만들어지지 않습니다.")
        dup = [n for n, k in Counter(created).items() if k > 1 and n in hits]
        if dup:
            rep.W(f"C{constellation} 히트 이름 중복 {dup} — build_hits 끝의 "
                  f"`{{h.name: h for h in hits}}`에서 하나가 경고 없이 사라집니다.")
        for w in caught:
            rep.W(f"C{constellation} build_hits 경고: {w.message}")

    # ── 소스 관습 ───────────────────────────────────────────────────────────
    src = module_path.read_text(encoding="utf-8")
    if "TODO(생성기)" in src:
        rep.W("tools/new_character.py가 남긴 `TODO(생성기)` 자리가 아직 있습니다.")
    if "의도적 미구현" not in src:
        rep.W("「의도적 미구현」 블록이 없습니다 — 무엇을 왜 뺐는지 남기지 않으면 "
              "다음 사람이 누락과 구별하지 못합니다.")
    spec = SPECS / f"{module_path.stem}.txt"
    if not spec.exists():
        rep.N(f"스펙 파일 없음: {spec.relative_to(ROOT)} — 계수의 출처가 저장소에 남아 있지 "
              f"않습니다. 스펙 양식 도입 전에 손으로 만든 캐릭터라면 정상입니다.")

    return rep


def check_registration() -> Report:
    """캐릭터 클래스가 정의만 되고 등록되지 않은 경우를 잡는다."""
    rep = Report("등록")
    registered = {cls for cls in CHARACTER_REGISTRY.values()}
    for path in sorted(CHARACTERS.glob("*/[a-z]*.py")):
        if path.name == "__init__.py":
            continue
        package = f"gidc.content.characters.{path.parent.name}"
        module  = __import__(f"{package}.{path.stem}", fromlist=["*"])
        for _name, obj in vars(module).items():
            if (inspect.isclass(obj) and issubclass(obj, Character) and obj is not Character
                    and inspect.getfile(obj) == str(path) and obj not in registered):
                rep.F(f"{path.relative_to(ROOT)}의 {obj.__name__}이 CHARACTER_REGISTRY에 "
                      f"없습니다 — make_character가 조용히 DefaultCharacter로 대체합니다.")
    for kr, cls in CHARACTER_REGISTRY.items():
        declared = getattr(cls, "name", "")
        if declared and declared != kr:
            rep.F(f"CHARACTER_REGISTRY의 열쇠 '{kr}'와 클래스가 선언한 name '{declared}'가 다릅니다.")
    return rep


def main() -> int:
    ap = argparse.ArgumentParser(description="등록된 캐릭터 점검")
    ap.add_argument("names", nargs="*", help="점검할 캐릭터 한글 이름 (생략하면 전원)")
    ap.add_argument("--quiet", action="store_true", help="문제 있는 캐릭터만 출력한다")
    args = ap.parse_args()

    targets = args.names or list(CHARACTER_REGISTRY)
    unknown = [n for n in targets if n not in CHARACTER_REGISTRY]
    if unknown:
        print(f"등록되지 않은 이름: {unknown}")
        print(f"등록된 캐릭터: {list(CHARACTER_REGISTRY)}")
        return 2

    names   = base_value_names()
    reports = [check_registration()] if not args.names else []
    reports += [check_character(n, CHARACTER_REGISTRY[n], names) for n in targets]

    n_fail = n_warn = 0
    for rep in reports:
        n_fail += len(rep.fail)
        n_warn += len(rep.warn)
        if rep.clean and (args.quiet or not rep.note):
            if not args.quiet:
                print(f"  OK   {rep.label}")
            continue
        print(f"  {'FAIL' if rep.fail else 'WARN' if rep.warn else 'OK  '} {rep.label}")
        for m in rep.fail:
            print(f"         FAIL  {m}")
        for m in rep.warn:
            print(f"         WARN  {m}")
        if not args.quiet:
            for m in rep.note:
                print(f"         참고  {m}")

    print(f"\n캐릭터 {len(targets)}명 · FAIL {n_fail} · WARN {n_warn}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
