"""캐릭터 자료(스펙 파일) → 캐릭터 클래스 뼈대 + 등록 2곳.

    python tools/new_character.py <스펙파일>          # 검사 후 생성
    python tools/new_character.py <스펙파일> --check   # 검사만, 파일은 건드리지 않는다
    python tools/new_character.py --template          # 빈 스펙 양식 출력

`tools/new_weapon.py`의 캐릭터판이다. 무기 쪽과 마찬가지로 이 스크립트는 **판단하지 않는다** —
효과를 어느 훅에 어떤 필드로 넣을지는 사람(혹은 AI)이 정하고, 여기서는 손으로 타이핑하면
반드시 어긋나는 것들만 맡는다.

  · 계수 표 — 특성 하나에 딸린 표들의 **길이가 서로 같은지**, 그리고 명함 상승을 포함한
    최대 실효 레벨을 덮는지. 표가 짧으면 clamp_talent_index가 조용히 마지막 레벨로 잘라
    쓰고, 그 경고는 `*_TABLES`에 등록된 표에서만 살아난다.
  · `*_TABLES` 등록 — 섹션에 적힌 표를 빠짐없이 등록한다. 손으로 쓰면 반드시 하나 샌다
    (등록된 17명 중 3명이 실제로 빠뜨렸다).
  · 단조성 — 계수는 특성 레벨이 오르면 커진다. 오르내림이 섞이면 옮겨 적다 틀린 것이다.
  · 퍼센트 변환 — `47.00 %` → `0.4700`. 소수점을 자리 이동으로 옮겨 자릿수를 그대로 남긴다
    (`float(x)/100`은 `0.47`로 줄어들고 반올림 오차가 낀다).
  · 히트 이름 중복 — build_hits는 마지막에 `{h.name: h for h in hits}`로 접히므로 이름이
    겹치면 **예외도 경고도 없이 히트 하나가 사라진다.**
  · 명함 번호 대조 — `스킬명함: 3`이라고 적었으면 설명 원문의 C3 줄이 스킬 레벨을 올린다고
    말해야 한다. C3/C5를 바꿔 적는 사고를 여기서 잡는다.
  · 등록 2곳 — content/characters/<원소>/__init__.py 와 CHARACTER_REGISTRY. 하나라도
    빠지면 make_character가 **조용히** DefaultCharacter로 대체한다(예외도 경고도 없다).

생성된 파일의 훅 넷은 전부 `pass` + 관용구 주석 + `# TODO(생성기)` 표시로 남는다.
`python tools/check_characters.py`가 그 표시를 잔존 여부로 검사한다.
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import re
import sys
from decimal import Decimal

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from gidc.core.profile import ScalingStat, SkillType
from gidc.enums import CharacterTrait, Element, StatType, WeaponType

ROOT       = pathlib.Path(__file__).resolve().parent.parent
CHARACTERS = ROOT / "gidc" / "content" / "characters"
BASE_VALUE = ROOT / "gidc" / "core" / "data" / "character_level_scaling" / "character_base_value.csv"

# 이 꼬리표로 끝나는 이름은 퍼센트다 — `%` 없이 적으면 값이 100배가 된다.
PERCENT_NAME_SUFFIXES = ("_PCT", "_RATIO", "_BONUS", "_DMG", "_RES", "_RATE", "_MULT")

# 손으로 올릴 수 있는 특성 레벨의 상한과 명함 1개가 올리는 폭 — core/character.py와 같은 값.
MAX_TALENT_LEVEL      = 10
CONSTELLATION_LEVEL_UP = 3

TEMPLATE = """\
이름: 얀사
영문: Iansan
원소: ELECTRO
종류: POLEARM
성급: 4
어센션: ATK_PCT
스킬명함: 3
폭발명함: 5

일반공격:
  ## 표 이름  "히트 이름"  [옵션...] = 값/값/... %
  ##   `##`로 시작하는 줄은 이 양식 설명 — 생성된 코드로 넘어가지 않는다.
  ##   `#` 한 개로 시작하는 줄은 바로 아래 표에 붙는 주석 — 코드에 그대로 실린다.
  ##   옵션 없이는 섹션 기본값을 쓴다 (일반공격→NORMAL_ATK, 원소스킬→SKILL, 원소폭발→BURST /
  ##   스케일 스탯 ATK / 원소는 법구 캐릭터만 자기 원소, 나머지는 물리).
  ##   옵션에 SkillType·Element·ScalingStat 이름을 적으면 그 항목만 덮어쓴다.
  ##   히트 이름 자리에 "-"를 적으면 계수 표만 만들고 히트는 만들지 않는다.
  ##   _NA[1] _NA[2] … 로 적으면 2차원 표 _NA 로 묶이고, 히트 이름의 {n}이 단수로 채워진다.
  _NA[1] "{n}단 공격 피해" = 47.00/50.80/54.60/60.10/63.90/68.30/74.30/80.30/86.30/92.90/99.40 %
  _NA[2] "{n}단 공격 피해" = 42.80/46.20/49.70/54.70/58.20/62.20/67.60/73.10/78.60/84.50/90.50 %
  _NA[3] "{n}단 공격 피해" = 64.40/69.60/74.90/82.40/87.60/93.60/101.80/110.10/118.30/127.30/136.30 %

  _CA "강공격 피해" CHARGED_ATK = 100.30/108.40/116.60/128.30/136.40/145.70/158.60/171.40/184.20/198.20/212.20 %

  _PLUNGE      "낙하 기간 피해"     PLUNGING = 63.93/69.14/74.34/81.77/86.98/92.92/101.10/109.28/117.46/126.38/135.30 %
  _LOW_PLUNGE  "저공 추락 충격 피해" PLUNGING = 127.84/138.24/148.65/163.51/173.92/185.81/202.16/218.51/234.86/252.70/270.54 %
  _HIGH_PLUNGE "고공 추락 충격 피해" PLUNGING = 159.68/172.67/185.67/204.24/217.23/232.09/252.51/272.93/293.36/315.64/337.92 %

원소스킬:
  _SKILL_DMG "원소 스킬 피해" = 286.40/307.90/329.40/358.00/379.50/401.00/429.60/458.20/486.90/515.50/544.20/572.80/608.60 %

원소폭발:
  _BURST_DMG "원소 폭발 피해" = 430.40/462.70/495.00/538.00/570.30/602.60/645.60/688.60/731.70/774.70/817.80/860.80/914.60 %
  # 비율로 계산한 값이 이 값을 넘으면 여기서 잘린다 (퍼센트가 아닌 실수치라 % 를 붙이지 않는다).
  _MEASURER_ATK_CAP "-" = 330/370/410/450/490/530/570/610/650/690/730/770/810

상수:
  ## 레벨로 스케일하지 않는 값. % 를 붙이면 100으로 나눈다.
  _NIGHTSOUL_MAX          = 54          # E 표의 「밤혼 최대치 54.0pt」
  _MEASURER_HOT_THRESHOLD = 42          # 이 값 이상이면 「뜨거운 응원!」 모드
  _A1_ATK_PCT             = 20 %        # A1 「표준 동작」 — 얀사 자신의 공격력 +20%

설명:
일반 공격 : 창으로 최대 3번 공격한다.
강공격 : 일정 스태미나를 소모해 전방으로 돌진하며 경로상의 적에게 피해를 준다.
낙하 공격 : 공중에서 땅을 내려찍어 경로상의 적을 공격하고 착지 시 범위 피해를 준다.

E : 전광석화
얀사가 전방으로 일정 거리 돌진해 경로상의 적에게 밤혼 성질의 번개 원소 피해를 준다.

Q : 힘의 3요소
「힘」의 이름으로 대지를 짓밟아 밤혼 성질의 번개 원소 범위 피해를 준다.

A1 : 근력 운동
「낙뢰파」가 적에게 명중 후, 얀사의 공격력이 20% 증가한다.

A4 : 운동량 테스트
얀사가 밤혼을 회복 시 현재 필드 위 캐릭터의 HP를 회복한다.

C1 : 뭐든 시작이 어려운 법
C2 : 게으름은 운동의 적!
C3 : 과학적인 식단 — 원소전투 스킬 전광석화의 스킬 레벨+3
C4 : 가장 중요한 건 꾸준함
C5 : 아직 한계가 아니다! — 원소폭발 힘의 3요소의 스킬 레벨+3
C6 : 「비옥한 터전」의 가르침
"""

# 훅을 채울 때 고를 관용구. 어느 훅이냐는 **수혜자**가 정한다 — 트리거가 아니다.
HOOK_BODIES: list[tuple[str, str, str]] = [
    (
        "apply_self_buffs",
        "self, hits: dict[str, SkillHit]",
        """        # ── Phase 3 · 자기 자신만 받는 효과 ──────────────────────────────────
        # 트리거가 히트여도 받는 쪽이 자기뿐이면 여기다. 유저 입력도 여기서 받는다.
        #     self._q_active = ask_bool("[{name} Q] … 여부")
        #     for hit in hits.values():
        #         hit.add("atk_pct", self._A1_ATK_PCT, self, note="A1 …")
        # `hit.field += x`로 직접 더하지 않는다 — explain 원장에 출처가 남지 않는다.""",
    ),
    (
        "contribute_dependent_stats",
        'self, all_hits: dict["Character", dict[str, SkillHit]]',
        """        # ── Phase 4 · 남의 ATK/DEF/HP/EM 풀에 고정값을 더한다 ────────────────
        # 유저 입력을 모으는 마지막 자리이기도 하다(Phase 4.5·5에서는 묻지 않는다).
        #     for hit in all_hits[target].values():
        #         hit.add("atk_pct", self._C2_ATK_PCT, self, note="C2 …")
        # EM %-공유는 elemental_mastery와 em_from_pct_share에 **동시에** 태그한다.""",
    ),
    (
        "apply_party_buffs",
        'self, all_hits: dict["Character", dict[str, SkillHit]]',
        """        # ── Phase 4.5 · 스탯을 읽지 않는 크로스 버프 ─────────────────────────
        # 내성 감소, 고정 all_dmg_bonus, 치명타, 방어 무시.
        # Phase 4에서 저장해 둔 답을 재사용해 같은 질문을 두 번 묻지 않는다.""",
    ),
    (
        "apply_dependent_buffs",
        'self, all_hits: dict["Character", dict[str, SkillHit]]',
        """        # ── Phase 5 · 버퍼의 최종 스탯을 읽어 만드는 버프 (방식 B) ────────────
        # **값이 아니라 함수를 넘긴다.** 지금 계산하면 파티 멤버 순서가 결과를 바꾼다.
        #     source_hit = next(iter(all_hits[self].values()))
        #     bonus = lambda: source_hit.convertible_atk() * self._RATIO
        #     for hit in all_hits[target].values():
        #         hit.add("atk_flat_derived", bonus, self, note="Q …")
        # 공격력→공격력은 convertible_atk()를 읽고 atk_flat_derived로 내보내 순환을 끊는다.
        # 코어 풀(atk_flat 등)에 **즉시 값으로** 되먹이면 정확성 가드가 실패시킨다.""",
    ),
]


# Character가 @abstractmethod로 선언한 훅 — 해당이 없어도 **지우면 인스턴스를 못 만든다**
# (TypeError: Can't instantiate abstract class). 나머지 둘은 기본 구현이 no-op이라 지워도 된다.
ABSTRACT_HOOKS = {"apply_self_buffs", "apply_dependent_buffs"}


class SpecError(Exception):
    pass


# ── 섹션 정의 ────────────────────────────────────────────────────────────────
# (스펙의 섹션 이름, *_TABLES 속성, build_hits의 인덱스 변수, 기본 SkillType, 명함 키)
SECTIONS = (
    ("일반공격", "NA_TABLES",    "nl", SkillType.NORMAL_ATK, "일반명함"),
    ("원소스킬", "SKILL_TABLES", "sk", SkillType.SKILL,      "스킬명함"),
    ("원소폭발", "BURST_TABLES", "bl", SkillType.BURST,      "폭발명함"),
)
SECTION_NAMES = [s[0] for s in SECTIONS]
HEADER_KEYS = (
    "이름", "영문", "원소", "종류", "성급", "어센션",
    "일반명함", "스킬명함", "폭발명함", "특성", "획득특성", "클래스",
)


class Entry:
    """계수 섹션의 한 줄 — 표 하나(와, 히트를 만든다면 히트 하나)."""

    def __init__(self, table: str, row: int | None, hit_name: str | None,
                 opts: list[str], raw_values: str, comment: str, pct: bool) -> None:
        self.table      = table       # "_NA" · "_SKILL_DMG"
        self.row        = row         # _NA[2] 의 2. 단일 표면 None
        self.hit_name   = hit_name    # None이면 히트를 만들지 않는다
        self.opts       = opts
        self.raw_values = raw_values
        self.comment    = comment
        self.pct        = pct
        self.values: list[str] = []   # 소수 문자열 (자릿수 보존)

        # `실수치` 옵션 — 「% 를 빠뜨린 것 아니냐」는 검사를 끄는 명시적 선언.
        self.flat_ok = "실수치" in opts

        self.skill_type:   SkillType | None   = None
        self.element:      Element | None     = None
        self.scaling:      ScalingStat | None = None


# ── 스펙 파싱 ────────────────────────────────────────────────────────────────
def parse_spec(text: str) -> dict:
    spec: dict = {"섹션": {n: [] for n in (*SECTION_NAMES, "상수")}, "설명": ""}
    section: str | None = None
    desc: list[str] = []
    pending_comment = ""

    head_re    = re.compile(rf"^({'|'.join(HEADER_KEYS)})\s*:(.*)$")
    section_re = re.compile(rf"^({'|'.join((*SECTION_NAMES, '상수', '설명'))})\s*:\s*$")
    entry_re   = re.compile(
        r"^\s+(_[A-Za-z0-9_]+)(?:\[(\d+)\])?"      # 표 이름과 (2차원이면) 행 번호
        r"(?:\s+\"([^\"]*)\")?"                    # "히트 이름" (없으면 히트 없음)
        r"((?:\s+[A-Za-z_가-힣]+)*)"       # 옵션들 (실수치 같은 한글 표시 포함)
        r"\s*=\s*(.*)$"                            # = 값
    )

    for lineno, line in enumerate(text.splitlines(), 1):
        if section == "설명":
            if head_re.match(line) or section_re.match(line):
                spec["설명"] = "\n".join(desc).strip("\n")
                section = None
            else:
                desc.append(line)
                continue

        m = section_re.match(line)
        if m:
            section = m.group(1)
            pending_comment = ""
            continue

        m = head_re.match(line)
        if m:
            spec[m.group(1)] = m.group(2).strip()
            section = None
            continue

        if section is None or not line.strip():
            continue

        stripped = line.strip()
        if stripped.startswith("##"):
            # `##`는 스펙 양식 설명 — 생성된 코드로 넘어가지 않는다.
            continue
        if stripped.startswith("#"):
            # `#` 한 개는 그 아래 표에 붙는 주석 — 생성된 코드에 그대로 실린다.
            pending_comment = stripped.lstrip("#").strip()
            continue

        m = entry_re.match(line)
        if m:
            table, row, hit_name, opts, rest = m.groups()
            rest, comment = _split_comment(rest)
            rest, pct = (rest[:-1].strip(), True) if rest.rstrip().endswith("%") else (rest.strip(), False)
            spec["섹션"][section].append(Entry(
                table, int(row) if row else None,
                None if hit_name in (None, "-") else hit_name,
                opts.split(), rest, comment or pending_comment, pct,
            ))
            pending_comment = ""
            continue

        # 값이 다음 줄로 이어진 경우 — 마지막 항목에 붙인다.
        entries = spec["섹션"][section]
        if entries and re.match(r"^\s+[\d./]", line):
            rest, comment = _split_comment(line.strip())
            if rest.rstrip().endswith("%"):
                rest, entries[-1].pct = rest.rstrip()[:-1], True
            entries[-1].raw_values += "/" + rest.strip().strip("/")
            entries[-1].comment = entries[-1].comment or comment
            continue

        raise SpecError(f"{lineno}번째 줄을 읽을 수 없습니다: {line.strip()!r}\n"
                        f"  꼴: _TABLE \"히트 이름\" [옵션...] = 값/값/... %")

    if section == "설명":
        spec["설명"] = "\n".join(desc).strip("\n")

    for key in ("이름", "영문", "원소", "종류", "성급", "어센션"):
        if not spec.get(key):
            raise SpecError(f"스펙에 '{key}' 항목이 없습니다. (양식은 --template)")
    return spec


def _split_comment(text: str) -> tuple[str, str]:
    head, _, tail = text.partition("#")
    return head.strip(), tail.strip()


# ── 값 변환 ──────────────────────────────────────────────────────────────────
def to_decimal_str(token: str, pct: bool) -> str:
    """`47.00` → `0.4700`. 자리 이동이라 자릿수도 값도 그대로 남는다.

    `float(token) / 100`은 `0.47`로 줄어들고 `92.93 → 0.9293000000000001` 같은 부동소수점
    찌꺼기가 낀다. 계수 표는 자료를 그대로 옮긴 것이라야 diff에서 대조가 된다."""
    try:
        d = Decimal(token)
    except Exception:
        raise SpecError(f"숫자로 읽을 수 없습니다: {token!r}")
    if pct:
        d = d.scaleb(-2)
    s = format(d, "f")
    return s


def fill_values(entry: Entry) -> None:
    tokens = [t for t in entry.raw_values.replace(" ", "").split("/") if t]
    if not tokens:
        raise SpecError(f"'{entry.table}'에 값이 없습니다.")
    entry.values = [to_decimal_str(t, entry.pct) for t in tokens]


# ── 검증 ─────────────────────────────────────────────────────────────────────
def resolve_options(spec: dict, entry: Entry, default_type: SkillType) -> None:
    """옵션 토큰을 SkillType·Element·ScalingStat로 가른다. 이름이 겹치는 열거형은 없다."""
    wt      = WeaponType[spec["종류"]]
    element = Element[spec["원소"]]

    unknown = [t for t in entry.opts
               if t != "실수치" and t not in SkillType.__members__
               and t not in Element.__members__ and t not in ScalingStat.__members__]
    if unknown:
        raise SpecError(
            f"'{entry.table}'의 옵션 {unknown}을 알 수 없습니다.\n"
            f"  SkillType   {list(SkillType.__members__)}\n"
            f"  Element     {list(Element.__members__)}\n"
            f"  ScalingStat {list(ScalingStat.__members__)}\n"
            f"  그 밖에 `실수치` (퍼센트 검사를 끈다)"
        )

    # SkillType을 먼저 확정한다 — 원소 기본값이 여기서 갈리므로, 나중에 처리하면
    # `_X "이름" ELECTRO CHARGED_ATK = …`처럼 순서를 바꿔 적었을 때 원소가 덮어써진다.
    types = [SkillType[t] for t in entry.opts if t in SkillType.__members__]
    entry.skill_type = types[-1] if types else default_type

    # 법구 캐릭터는 일반/강/낙하까지 자기 원소 피해다. 그 밖의 무기는 물리(element 미지정).
    # 스킬·폭발은 무기와 무관하게 자기 원소다.
    if entry.skill_type in (SkillType.NORMAL_ATK, SkillType.CHARGED_ATK, SkillType.PLUNGING):
        entry.element = element if wt is WeaponType.CATALYST else None
    else:
        entry.element = element

    entry.scaling = ScalingStat.ATK
    for tok in entry.opts:
        if tok in Element.__members__:
            entry.element = None if tok == "PHYSICAL" else Element[tok]
        elif tok in ScalingStat.__members__:
            entry.scaling = ScalingStat[tok]


def required_length(spec: dict, const_key: str) -> int:
    up = int(spec.get(const_key) or 0)
    return MAX_TALENT_LEVEL + (CONSTELLATION_LEVEL_UP if up else 0)


def check_section(spec: dict, section: str, const_key: str, notes: list[str]) -> None:
    entries = spec["섹션"][section]
    if not entries:
        return
    lengths = {len(e.values) for e in entries}
    if len(lengths) > 1:
        detail = "\n".join(f"    {e.table:<24} {len(e.values):>3}칸" for e in entries)
        raise SpecError(
            f"[{section}] 표들의 길이가 서로 다릅니다 — 한 특성의 계수 표는 레벨 수가 같아야 합니다.\n{detail}"
        )
    length = lengths.pop()
    need   = required_length(spec, const_key)
    if length < need:
        raise SpecError(
            f"[{section}] 계수가 {length}칸뿐입니다 — 최대 실효 레벨 L{need}까지 필요합니다"
            f"{' (명함 +3 포함)' if length < MAX_TALENT_LEVEL + 1 and need > MAX_TALENT_LEVEL else ''}.\n"
            f"  짧으면 clamp_talent_index가 조용히 마지막 레벨로 잘라 씁니다."
        )
    if length > need:
        notes.append(f"참고: [{section}] 표가 {length}칸입니다 (필요한 최대 레벨은 L{need}). "
                     f"파티발 레벨 상승(무예 전수 등)을 위한 여유라면 정상입니다.")

    for e in entries:
        nums = [Decimal(v) for v in e.values]
        up   = all(b >= a for a, b in zip(nums, nums[1:]))
        down = all(b <= a for a, b in zip(nums, nums[1:]))
        if not (up or down):
            raise SpecError(
                f"'{e.table}'이 단조 수열이 아닙니다 — 계수는 특성 레벨이 오르면 커집니다.\n"
                f"  옮겨 적다 틀렸을 가능성이 높습니다: {e.raw_values}"
            )
        if down and len(set(nums)) > 1:
            notes.append(f"참고: '{e.table}'은 레벨이 오를수록 **줄어드는** 수열입니다. 자료를 한 번 더 확인하세요.")
        if e.pct and max(nums) > 3000:
            notes.append(f"참고: '{e.table}'의 최대값이 {max(nums)}입니다 (퍼센트로 3000% 초과). 단위를 확인하세요.")
        check_percent_marker(e.table, nums, e.pct, e.flat_ok)


def check_percent_marker(table: str, nums: list[Decimal], pct: bool, flat_ok: bool) -> None:
    """`%`를 빠뜨렸는지 본다 — 빠뜨리면 계수가 100배가 되고 **아무 데서도 안 걸린다.**

    크기로는 가릴 수 없다: 608.6(=608.6%)도 810(공격력 보너스 상한)도 둘 다 있을 수 있는
    값이다. 가르는 것은 소수점이다 — 이 엔진의 실수치 표(보호막 고정값 1387, 공격력 상한
    330)는 전부 정수이고 계수는 소수 자리를 갖는다. 정말 소수인 실수치라면 옵션에
    `실수치`를 적어 그렇다고 말한다."""
    if pct or flat_ok:
        return
    # 이름이 퍼센트라고 말하는데 %가 없으면 정수라도 틀린 것이다 (`_A1_ATK_PCT = 20`은
    # 20%가 아니라 2000%가 된다). 소수점 규칙만으로는 정수 상수를 못 잡는다.
    if any(table.endswith(suffix) for suffix in PERCENT_NAME_SUFFIXES):
        raise SpecError(
            f"'{table}'은 이름이 퍼센트를 가리키는데 % 표시가 없습니다 — 값이 100배가 됩니다.\n"
            f"  줄 끝에 ` %`를 붙이거나, 정말 실수치라면 옵션에 `실수치`를 적으세요."
        )
    fractional = [n for n in nums if n != n.to_integral_value()]
    if fractional:
        raise SpecError(
            f"'{table}'에 % 표시가 없는데 값에 소수점이 있습니다 ({fractional[0]}) — "
            f"퍼센트 표기를 빠뜨린 것 같습니다.\n"
            f"  계수라면 줄 끝에 ` %`를 붙이고, 정말 실수치라면 옵션에 `실수치`를 적어 이 검사를 끄세요."
        )
    if max(nums) < 10:
        raise SpecError(
            f"'{table}'에 % 표시가 없는데 값이 전부 10 미만입니다 — 퍼센트 표기를 빠뜨린 것 "
            f"같습니다. 정말 실수치라면 옵션에 `실수치`를 적으세요."
        )


def check_hit_names(spec: dict) -> None:
    seen: dict[str, str] = {}
    for section in SECTION_NAMES:
        for e in spec["섹션"][section]:
            if not e.hit_name:
                continue
            if e.row is not None and "{n}" not in e.hit_name:
                raise SpecError(f"'{e.table}[{e.row}]'은 2차원 표인데 히트 이름에 {{n}}이 없습니다 — "
                                f"단수마다 이름이 같아져 히트가 하나로 접힙니다.")
            if e.row is None and "{n}" in e.hit_name:
                raise SpecError(f"'{e.table}'은 1차원 표인데 히트 이름에 {{n}}이 있습니다.")
            key = e.hit_name if e.row is None else f"{e.hit_name}#{e.row}"
            if key in seen:
                raise SpecError(
                    f"히트 이름이 겹칩니다: {e.hit_name!r} ({seen[key]} ↔ {e.table})\n"
                    f"  build_hits는 마지막에 이름으로 dict를 만들므로 겹치면 히트 하나가 "
                    f"경고 없이 사라집니다."
                )
            seen[key] = e.table


def check_tables(spec: dict) -> None:
    seen: dict[str, Entry] = {}
    for section in (*SECTION_NAMES, "상수"):
        for e in spec["섹션"][section]:
            key = e.table if e.row is None else f"{e.table}[{e.row}]"
            if key in seen:
                raise SpecError(f"표 이름이 겹칩니다: {key}")
            seen[key] = e
    for section in SECTION_NAMES:
        rows = [e for e in spec["섹션"][section] if e.row is not None]
        by_table: dict[str, list[int]] = {}
        for e in rows:
            by_table.setdefault(e.table, []).append(e.row)
        for table, idx in by_table.items():
            if sorted(idx) != list(range(1, len(idx) + 1)):
                raise SpecError(f"'{table}'의 행 번호가 1부터 연속이 아닙니다: {sorted(idx)}")


def check_stat_key(english: str) -> list[str]:
    """영문 이름이 기초 스탯 표에 있는지. 없으면 그 캐릭터의 기초 HP/공격력/방어력이 없다."""
    with BASE_VALUE.open(encoding="utf-8") as fp:
        names = [row["character"] for row in csv.DictReader(fp)]
    if english in names:
        return []
    near = [n for n in names if n.lower().startswith(english[:3].lower())]
    raise SpecError(
        f"'{english}'이 기초 스탯 표에 없습니다: {BASE_VALUE.relative_to(ROOT)}\n"
        f"  Character.stat_key가 이 표의 열쇠라 없으면 기초 스탯을 못 읽습니다.\n"
        + (f"  비슷한 이름: {near}\n" if near else "")
        + f"  표에 없는 신규 캐릭터라면 CSV에 먼저 행을 추가하세요."
    )


def check_constellation_lines(spec: dict, notes: list[str]) -> None:
    """`스킬명함: 3`이라 적었으면 설명 원문의 C3 줄이 그 말을 해야 한다."""
    desc = spec.get("설명", "")
    for key, word in (("일반명함", "일반"), ("스킬명함", "스킬"), ("폭발명함", "폭발")):
        n = int(spec.get(key) or 0)
        if not n:
            continue
        # 명함 설명은 「C3 : 과학적인 식단」 다음 줄에 본문이 오는 꼴이 흔하다.
        # 헤더 줄만 보면 본문을 놓치므로 다음 C 항목(또는 끝)까지를 한 덩어리로 읽는다.
        m = re.search(rf"^\s*C{n}\s*[:：](.*?)(?=^\s*C\d+\s*[:：]|\Z)", desc, re.M | re.S)
        if not m:
            notes.append(f"경고: {key}={n}이라고 적었는데 설명 원문에 'C{n} :' 줄이 없습니다.")
            continue
        block = m.group(0)
        if word not in block or "레벨" not in block:
            head = block.strip().splitlines()[0]
            notes.append(f"경고: {key}={n}인데 C{n} 항목이 「{word} … 레벨」 상승을 말하지 않습니다 — "
                         f"명함 번호를 바꿔 적었을 수 있습니다.\n           {head}")


# ── 코드 생성 ────────────────────────────────────────────────────────────────
def render_tables(spec: dict) -> tuple[str, dict[str, list[str]]]:
    """계수 표 블록과, `*_TABLES`에 넣을 이름 목록."""
    out: list[str] = []
    groups: dict[str, list[str]] = {attr: [] for _, attr, _, _, _ in SECTIONS}

    for section, attr, _var, _type, _const in SECTIONS:
        entries = spec["섹션"][section]
        if not entries:
            continue
        out.append(f"    # ── {section} (L1~L{len(entries[0].values)}) ──")
        emitted: set[str] = set()
        for e in entries:
            if e.comment:
                out.append(f"    # {e.comment}")
            if e.row is not None:
                if e.table in emitted:
                    continue
                emitted.add(e.table)
                rows = sorted((x for x in entries if x.table == e.table), key=lambda x: x.row or 0)
                width = max(len(v) for r in rows for v in r.values)
                out.append(f"    {e.table} = [")
                for r in rows:
                    out.append(f"        [{_row_text(r.values, width)}],")
                out.append("    ]")
                groups[attr].append(f"*{e.table}")
            else:
                out += _render_flat(e.table, e.values)
                groups[attr].append(e.table)
        out.append("")

    consts = spec["섹션"]["상수"]
    if consts:
        out.append("    # ── 상수 (레벨로 스케일하지 않는 값) ──")
        name_w = max(len(c.table) for c in consts)
        vals   = {c.table: to_decimal_str(c.raw_values.strip(), c.pct) for c in consts}
        val_w  = max(len(v) for v in vals.values())
        for c in consts:
            tail = f"   # {c.comment}" if c.comment else ""
            out.append(f"    {c.table:<{name_w}} = {vals[c.table]:<{val_w if tail else 0}}{tail}".rstrip())
        out.append("")

    return "\n".join(out).rstrip("\n"), groups


# 한 줄에 넣을 계수 개수 — 이보다 길어지면 5개씩 끊어 여러 줄로 쓴다.
_WRAP_AT = 112
_CHUNK   = 5


def _render_flat(table: str, values: list[str]) -> list[str]:
    """1차원 표. 한 줄에 다 들어가면 한 줄로, 아니면 5개씩 끊는다."""
    width = max(len(v) for v in values)
    one   = f"    {table} = [{_row_text(values, width)}]"
    if len(one) <= _WRAP_AT:
        return [one]
    lines = [f"    {table} = ["]
    for i in range(0, len(values), _CHUNK):
        chunk = values[i:i + _CHUNK]
        lines.append("        " + ", ".join(v.rjust(width) for v in chunk) + ",")
    lines.append("    ]")
    return lines


def _row_text(values: list[str], width: int) -> str:
    return ", ".join(v.rjust(width) for v in values)


def render_build_hits(spec: dict) -> str:
    lines: list[str] = []
    used_vars: list[str] = []

    for section, _attr, var, default_type, const_key in SECTIONS:
        entries = spec["섹션"][section]
        if not entries:
            continue
        used_vars.append(var)

    body: list[str] = []
    for section, _attr, var, default_type, _const in SECTIONS:
        entries = spec["섹션"][section]
        if not entries:
            continue
        body.append(f"        # {section}")
        emitted: set[str] = set()
        for e in entries:
            if not e.hit_name:
                continue
            args = f"SkillType.{e.skill_type.name}"
            tail = f", ScalingStat.{e.scaling.name}"
            if e.element is not None:
                tail += f", Element.{e.element.name}"
            if e.row is not None:
                if e.table in emitted:
                    continue
                emitted.add(e.table)
                name = e.hit_name.replace("{n}", "{i+1}")
                body.append(f"        for i, row in enumerate(self.{e.table}):")
                body.append(f'            hits.append(SkillHit(f"{name}", {args}, row[{var}]{tail}))')
            else:
                body.append(f'        hits.append(SkillHit("{e.hit_name}", {args}, '
                            f"self.{e.table}[{var}]{tail}))")
        body.append("")

    head = []
    for section, _attr, var, _type, const_key in SECTIONS:
        if not spec["섹션"][section]:
            continue
        n = int(spec.get(const_key) or 0)
        note = f"   # C{n}: 레벨 +3" if n else ""
        head.append(f"        {var} = self._{ {'nl': 'na', 'sk': 'skill', 'bl': 'burst'}[var] }_index(){note}")

    lines += head
    lines.append("")
    lines.append("        hits: list[SkillHit] = []")
    lines.append("")
    lines += body
    lines.append("        return {h.name: h for h in hits}")
    return "\n".join(lines)


def render(spec: dict) -> str:
    cls     = spec["클래스"]
    wt      = WeaponType[spec["종류"]]
    element = Element[spec["원소"]]
    asc     = StatType[spec["어센션"]]
    rarity  = int(spec["성급"])

    tables, groups = render_tables(spec)

    meta: list[str] = []
    for key, attr in (("일반명함", "NA_LEVEL_UP_CONSTELLATION"),
                      ("스킬명함", "SKILL_LEVEL_UP_CONSTELLATION"),
                      ("폭발명함", "BURST_LEVEL_UP_CONSTELLATION")):
        n = int(spec.get(key) or 0)
        if n:
            meta.append(f"    {attr} = {n}")
    for _section, attr, _var, _type, _const in SECTIONS:
        if groups[attr]:
            meta.append(f"    {attr} = ({', '.join(groups[attr])},)")

    traits = ""
    for key, attr in (("특성", "innate_traits"), ("획득특성", "unlockable_traits")):
        raw = (spec.get(key) or "").strip()
        if raw:
            names = [CharacterTrait[t.strip()].name for t in raw.split(",") if t.strip()]
            traits += f"    {attr} = frozenset({{{', '.join('CharacterTrait.' + n for n in names)}}})\n"

    hooks = "\n".join(
        f"    def {name}({sig}) -> None:\n"
        f"        # TODO(생성기): 이 훅을 채우세요. 이 캐릭터에 해당이 없으면 "
        + ("본문을 pass로 두고 왜 비었는지만 적습니다\n"
           "        #              (Character의 @abstractmethod라 지우면 인스턴스를 못 만듭니다).\n"
           if name in ABSTRACT_HOOKS else
           "메서드째 지웁니다\n"
           "        #              (Character의 기본 구현이 no-op입니다).\n")
        + f"{body.format(name=spec['이름'])}\n"
        f"        pass\n"
        for name, sig, body in HOOK_BODIES
    )

    desc = "\n".join(("    " + ln).rstrip() for ln in spec["설명"].splitlines())
    imports = "from gidc.core.character import Character\n" \
              "from gidc.core.profile import SkillHit, SkillType, ScalingStat\n"
    if traits:
        imports += "from gidc.enums import CharacterTrait, Element\n"
    else:
        imports += "from gidc.enums import Element\n"
    imports += "from gidc.enums import StatType\n" \
               "from gidc.enums import WeaponType\n" \
               "from gidc.prompt import ask_bool, ask_choice, ask_int\n"

    return f'''{imports}

class {cls}(Character):
    """{spec["이름"]} ({spec["영문"]}) | {element.value} | {wt.value} | {rarity}성 | 어센션 스탯: {asc.value}

{desc}
    """
    name = "{spec["이름"]}"
    weapon_type = WeaponType.{wt.name}
{traits}
    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
{tables}
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
{chr(10).join(meta)}

    rarity         = {rarity}
    ascension_stat = StatType.{asc.name}

    @property
    def element(self) -> Element: return Element.{element.name}

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
{render_build_hits(spec)}

{hooks}
    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # TODO(생성기): 무엇을 왜 넣지 않았는지 적는다. 나중에 「빠뜨린 것」과 「안 넣기로 한 것」을
    # 구분하는 유일한 근거다. 주로 여기 들어가는 것: 에너지 회복, 치유, 쿨다운, 이동 속도,
    # 자원 게이지 수지, 실드 수치.
'''


# ── 등록 2곳 ─────────────────────────────────────────────────────────────────
def register(cls: str, module: str, element: Element, kr_name: str) -> list[str]:
    done = []
    element_dir = element.name.lower()

    # (1) content/characters/<원소>/__init__.py — import 한 줄. 최상위 __init__은 이 패키지를
    #     통째로 가져가므로(`from . import pyro, hydro, …`) 여기 빠지면 클래스가 안 보인다.
    p   = CHARACTERS / element_dir / "__init__.py"
    line = f"from .{module} import {cls}\n"
    src  = p.read_text(encoding="utf-8") if p.exists() else ""
    if line not in src:
        lines = sorted([*[l for l in src.splitlines() if l.strip()], line.rstrip()])
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        done.append(f"{p.relative_to(ROOT)}  ← import 추가")

    # (2) content/characters/__init__.py — CHARACTER_REGISTRY. 빠지면 make_character가
    #     예외도 경고도 없이 DefaultCharacter로 대체한다.
    p   = CHARACTERS / "__init__.py"
    src = p.read_text(encoding="utf-8")
    if f'"{kr_name}"' not in src:
        m = re.search(r"(CHARACTER_REGISTRY[^{]*\{)(.*?)(\n\})", src, re.S)
        if not m:
            raise SpecError("CHARACTER_REGISTRY를 찾지 못했습니다.")
        entry = f'\n    "{kr_name}":{" " * 4}{element_dir}.{cls},'
        src = src[:m.end(2)] + entry + src[m.end(2):]
        p.write_text(src, encoding="utf-8")
        done.append("gidc/content/characters/__init__.py  ← CHARACTER_REGISTRY 등록")
    return done


def camel(english: str) -> str:
    return "".join(w[:1].upper() + w[1:] for w in re.split(r"[^A-Za-z0-9]+", english) if w)


def snake(cls_name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", cls_name).lower()


def main() -> None:
    ap = argparse.ArgumentParser(description="캐릭터 스펙 → 클래스 뼈대 + 등록 2곳")
    ap.add_argument("spec", nargs="?", help="스펙 파일 경로")
    ap.add_argument("--check", action="store_true", help="검사만 하고 파일을 쓰지 않는다")
    ap.add_argument("--template", action="store_true", help="빈 스펙 양식을 출력한다")
    ap.add_argument("--stdout", action="store_true", help="생성될 파일을 출력만 한다 (등록하지 않는다)")
    args = ap.parse_args()

    if args.template:
        print(TEMPLATE)
        return
    if not args.spec:
        ap.error("스펙 파일 경로가 필요합니다 (양식은 --template).")

    spec = parse_spec(pathlib.Path(args.spec).read_text(encoding="utf-8"))
    spec.setdefault("클래스", "")
    spec["클래스"] = spec["클래스"] or camel(spec["영문"])

    for key, enum in (("원소", Element), ("종류", WeaponType), ("어센션", StatType)):
        if spec[key] not in enum.__members__:
            raise SpecError(f"'{key}: {spec[key]}'을 알 수 없습니다. 가능한 값: {list(enum.__members__)}")
    if int(spec["성급"]) not in (4, 5):
        raise SpecError(f"성급은 4 또는 5입니다. (입력: {spec['성급']})")

    # --stdout은 생성될 코드만 내보낸다 — 파이프로 바로 받을 수 있게 보고는 stderr로 보낸다.
    out_stream = sys.stderr if args.stdout else sys.stdout

    def say(text: str = "") -> None:
        print(text, file=out_stream)

    notes: list[str] = []
    spec_path = pathlib.Path(args.spec).resolve()
    if spec_path.parent != (ROOT / "_specs" / "characters"):
        notes.append(f"참고: 스펙 파일이 _specs/characters/ 밖에 있습니다 ({spec_path}). "
                     f"계수의 출처가 저장소에 남도록 거기로 옮겨 함께 커밋하세요.")
    notes += check_stat_key(spec["영문"])

    for section, _attr, _var, default_type, _const in SECTIONS:
        for e in spec["섹션"][section]:
            fill_values(e)
            resolve_options(spec, e, default_type)
    for c in spec["섹션"]["상수"]:
        # 상수도 같은 함정에 빠진다 — `20 %`를 `20`으로 적으면 20% 버프가 2000%가 된다.
        check_percent_marker(c.table, [Decimal(to_decimal_str(c.raw_values.strip(), c.pct))],
                             c.pct, c.flat_ok)
    check_tables(spec)
    check_hit_names(spec)
    for section, _attr, _var, _type, const_key in SECTIONS:
        check_section(spec, section, const_key, notes)
    check_constellation_lines(spec, notes)
    if not spec["설명"].strip():
        notes.append("경고: '설명:' 블록이 비었습니다 — 클래스 docstring이 빈 채로 생성됩니다.")

    element = Element[spec["원소"]]
    # 2차원 표는 행 하나가 히트 하나다. 행 항목이 여러 줄이라 표 단위로 세면 이중 계산이 된다.
    n_hits = sum(1 for s in SECTION_NAMES for e in spec["섹션"][s] if e.hit_name)
    say(f"[{spec['이름']}]  {element.value} · {WeaponType[spec['종류']].value} · "
        f"{spec['성급']}성 · {spec['클래스']}")
    for section, _attr, _var, _type, const_key in SECTIONS:
        entries = spec["섹션"][section]
        if entries:
            say(f"  {section}: 표 {len({e.table for e in entries})}개 · "
                f"L1~L{len(entries[0].values)} (필요 L{required_length(spec, const_key)})")
    if spec["섹션"]["상수"]:
        say(f"  상수: {len(spec['섹션']['상수'])}개")
    say(f"  히트 {n_hits}개")
    for n in notes:
        say(f"  {n}")

    code = render(spec)

    if args.stdout:
        print(code)
        return
    if args.check:
        say("")
        say("검사만 했습니다 (--check). 파일은 그대로입니다.")
        return

    module = snake(spec["클래스"])
    out    = CHARACTERS / element.name.lower() / f"{module}.py"
    if out.exists():
        raise SpecError(f"이미 있습니다: {out.relative_to(ROOT)}")
    out.write_text(code, encoding="utf-8")
    print(f"\n{out.relative_to(ROOT)}  ← 생성")
    for line in register(spec["클래스"], module, element, spec["이름"]):
        print(line)
    print("\n다음: 훅 넷을 채우고 `python tools/check_characters.py`로 점검한 뒤 "
          "`python tools/sync_web.py`로 웹에 반영하세요.")


if __name__ == "__main__":
    try:
        main()
    except SpecError as e:
        sys.exit(f"오류: {e}")
