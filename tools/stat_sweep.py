"""스탯 모델 전수 대조 — 구조 변경 전후로 돌려 diff한다.

    python tools/stat_sweep.py > before.txt
    (코드 수정)
    python tools/stat_sweep.py > after.txt
    diff before.txt after.txt

`_baseline`이 **한 파티**를 깊게 보는 오라클이라면, 이쪽은 **많은 조합**을 얕게 훑는다.
스탯 풀(atk_flat / atk_from_pct_share / em_from_flat …)의 분류를 바꾸는 작업은 특정
조합에서만 값이 달라지므로, 파티 하나로는 변화가 아예 안 보이거나 반대로 어디까지
번졌는지 알 수 없다. 실제로 EM 두 조각 저장 리팩터링과 %-파생 지분 규칙 적용이
이 방식으로 검증됐다(각각 「값 차이 0줄」, 「변한 줄이 전부 베넷 조합」).

쓰는 법은 둘 중 하나다.

  · **값 불변 리팩터링** — diff가 비어야 한다.
  · **의도적 동작 변경** — diff가 비지 않는다. 변한 줄이 **의도한 조합에만** 있는지
    본다(`diff ... | grep '^[<>]' | awk -F'|' '{print $1}' | sort -u`).

전후 비교는 `git worktree`로 옛 코드를 꺼내 놓고 양쪽에서 돌리면 작업 트리를 건드리지
않는다. 스크립트가 저장소 밖에 있어도 되도록 PYTHONPATH를 각각 맞춰 준다.

    git worktree add /tmp/old HEAD
    cp tools/stat_sweep.py /tmp/old/tools/          # 도구는 새 것으로 통일한다
    (cd /tmp/old && python tools/stat_sweep.py > /tmp/before.txt 2>/dev/null)
    python tools/stat_sweep.py > /tmp/after.txt 2>/dev/null
    diff /tmp/before.txt /tmp/after.txt
    git worktree remove /tmp/old

## 무엇을 찍는가

히트마다 한 줄이고, **스탯 풀을 조각까지 펼쳐** 찍는다. 합계만 찍으면 분류가 바뀌어도
(flat → from_pct_share) 총합이 같아 diff가 비어 버려서, 정작 이 도구가 잡아야 할 변화를
놓친다. 피해도 같이 찍는다 — 스탯이 같아도 피해 공식 쪽이 바뀌면 그건 여기서 잡힌다.

## 한계

- 답변은 「전부 끄기」와 「전부 켜기」 두 벌뿐이다. 중간 상태(스택 2/3 등)는 안 본다.
- 반응은 `ReactionType.NONE` 고정이다. 반응 계열 변경은 `bench.py` 쪽이 본다.
- 조합 목록은 아래 상수에 손으로 적는다. **스탯을 읽거나 쓰는 캐릭터·무기를 새로
  구현하면 여기 추가한다** — 안 그러면 그 조합은 그물에 안 걸린다.
"""
from __future__ import annotations

import itertools
import pathlib
import sys
import warnings

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from gidc.content.artifacts import make_artifact
from gidc.content.characters import CHARACTER_REGISTRY, make_character
from gidc.content.weapons import make_weapon
from gidc.core.artifact import SubStat
from gidc.core.damage import calculate
from gidc.core.enemy import Enemy
from gidc.core.party import Party
from gidc.core.profile import CyclicBuffError, build_damage_context
from gidc.enums import ArtifactSet, ArtifactSlot, ReactionType, StatType
from gidc import prompt


# ══════════════════════════════════════════════════════════════════════════
#  대상 목록 — 스탯을 읽거나 쓰는 캐릭터·무기를 새로 구현하면 여기 추가한다
# ══════════════════════════════════════════════════════════════════════════
# 스탯 → 다른 스탯/버프 변환을 가진 캐릭터. 서로 짝지어 전수로 돌린다.
# (버퍼가 만든 스탯을 또 다른 버퍼가 재료로 읽는 사슬이 여기서 생긴다)
CONVERTER_CHARS = (
    "설탕", "시틀라리", "산드로네", "콜롬비나", "이네파", "얀사", "베넷", "슈브르즈",
)

# 스탯 풀을 읽거나 쓰는 무기. 착용 가능한 모든 캐릭터에게 물려 본다.
CONVERTER_WEAPONS = (
    "성현의 열쇠",            # HP% → EM
    "반암결록",               # HP% → ATK
    "적색 사막의 지팡이",     # EM% → ATK
    "잎을 가르는 빛",         # EM% → 피해
    "나른한 새해",            # 고정 EM
    "식재",                   # 고정 ATK%
    "홍각의 돌망치",          # DEF% → 피해
    "바위산을 맴도는 노래",   # DEF% → 파티 원소 피해
)

# 3~4인 파티 — 비중첩 버프와 파티 전체 훅은 2인으로는 안 서는 것이 있다.
MULTI_PARTIES = (
    ("베넷", "이네파", "산드로네"),
    ("콜롬비나", "이네파", "설탕", "시틀라리"),
    ("슈브르즈", "이네파", "베넷"),
    ("얀사", "베넷", "산드로네", "설탕"),
)

ENEMY     = Enemy(level=100)
CHAR_LV   = 90
EM_SUBSTAT = 200      # 원소 마스터리 경로를 깨우려고 모래시계를 하나 물린다

# 조각까지 펼쳐 찍는 스탯 풀. 합계만 보면 분류 변경(flat ↔ from_pct_share)이 안 보인다.
STAT_FIELDS = (
    "hp_flat", "hp_pct", "hp_from_pct_share",
    "atk_flat", "atk_pct", "atk_from_pct_share",
    "def_flat", "def_pct", "def_from_pct_share",
    "em_from_flat", "em_from_pct_share",
)


# ══════════════════════════════════════════════════════════════════════════
#  빌더
# ══════════════════════════════════════════════════════════════════════════
def _make(name: str, weapon: str | None = None, *, em: int = EM_SUBSTAT):
    """명함 6 · 특성 10 · EM 모래시계로 고정한 캐릭터. 조건을 최대한 켜 두려는 설정이다."""
    char = make_character(name=name)
    char.level         = CHAR_LV
    char.constellation = 6
    char.na_level = char.skill_level = char.burst_level = 10
    if weapon:
        char.weapon = make_weapon(name=weapon, refinement=5)
    if em:
        char.sands = make_artifact(
            artifact_set   = ArtifactSet.EMBLEM_OF_SEVERED_FATE,
            slot           = ArtifactSlot.SANDS,
            rarity         = 5,
            level          = 20,
            main_stat_type = StatType.ELEMENTAL_MASTERY,
            sub_stats      = [SubStat(StatType.ELEMENTAL_MASTERY, em)],
        )
    return char


def _answers_all_on(questions) -> dict:
    """수집된 질문을 전부 '켠' 답변. int는 최대, choice는 첫 항목, multi는 전체."""
    out = {}
    for q in questions:
        if q.kind == "bool":
            out[q.id] = True
        elif q.kind == "int":
            out[q.id] = q.max_val
        elif q.kind == "choice":
            # 마지막이 아니라 첫 항목이다 — 「없음」이 0번인 질문도 있지만, 마지막을 고르면
            # 파티 구성에 따라 선택지 수가 달라져 조합끼리 비교가 흔들린다. 0은 항상 있다.
            out[q.id] = 0
        elif q.kind == "multi":
            out[q.id] = list(range(len(q.options)))
    return out


def _build(specs, answers):
    """캐릭터를 **새로** 만들어 파티를 세운다.

    캐릭터가 self._e_active 같은 per-run 상태를 들고 있어 재사용하면 계산이 오염된다
    (bench.py의 프리셋이 build() 팩토리인 것과 같은 이유).
    """
    chars = [make() for make in specs]
    src   = prompt.MappingSource(answers)
    with prompt.using(src):
        hits = Party(*chars).build_profiles()
    return chars, hits, src


# ══════════════════════════════════════════════════════════════════════════
#  출력
# ══════════════════════════════════════════════════════════════════════════
def _damage(hit) -> str:
    try:
        ctx = build_damage_context(
            hit, ENEMY, reaction_type=ReactionType.NONE, dmg_type=None, char_level=CHAR_LV
        )
        return f"{calculate(ctx).non_crit:.4f}"
    except Exception as exc:                       # 계산이 안 서는 히트도 있다(흡수 자리표 등)
        return f"ERR:{type(exc).__name__}"


def _emit(label: str, specs) -> None:
    """한 조합을 '전부 끄기'와 '전부 켜기' 두 벌로 찍는다."""
    try:
        _, _, src = _build(specs, {})
        on = _answers_all_on(src.asked)
    except CyclicBuffError as exc:
        print(f"{label} | CYCLE | {str(exc).splitlines()[0]}")
        return
    except Exception as exc:
        print(f"{label} | ERROR | {type(exc).__name__}: {exc}")
        return

    for mode, answers in (("off", {}), ("on", on)):
        try:
            chars, hits, _ = _build(specs, answers)
        except CyclicBuffError as exc:
            print(f"{label} [{mode}] | CYCLE | {str(exc).splitlines()[0]}")
            continue
        except Exception as exc:
            print(f"{label} [{mode}] | ERROR | {type(exc).__name__}: {exc}")
            continue

        for char in chars:
            for hit_name, hit in hits[char].items():
                # 없는 필드는 0으로 본다 — 이 도구는 **필드가 생기고 없어지는** 변경을
                # 사이에 두고 돌리는 것이 목적이라, 옛 코드에 새 슬롯이 없다고 죽으면 안 된다.
                # 0이던 슬롯이 값을 갖게 되는 변화는 그대로 diff에 뜬다.
                stats = " ".join(
                    f"{f}={getattr(hit, f, 0.0):.4f}" for f in STAT_FIELDS
                )
                print(
                    f"{label} [{mode}] | {char.name} | {hit_name} | "
                    f"EM={hit.elemental_mastery:.4f} "
                    f"ATK={hit.atk_final:.4f} HP={hit.hp_final:.4f} DEF={hit.def_final:.4f} | "
                    f"{stats} | DMG={_damage(hit)}"
                )


# ══════════════════════════════════════════════════════════════════════════
#  시나리오
# ══════════════════════════════════════════════════════════════════════════
def sweep_solo() -> None:
    for name in sorted(CHARACTER_REGISTRY):
        _emit(f"solo:{name}", [lambda n=name: _make(n)])


def sweep_pairs() -> None:
    present = [n for n in CONVERTER_CHARS if n in CHARACTER_REGISTRY]
    for a, b in itertools.combinations(present, 2):
        _emit(f"pair:{a}+{b}", [lambda n=a: _make(n), lambda n=b: _make(n)])


def sweep_weapons() -> None:
    """무기를 착용 가능한 모든 캐릭터에게 물리고, 변환 캐릭터를 하나 붙인다.

    파트너가 필요한 이유: 무기가 만든 스탯을 **다른 캐릭터가 재료로 읽는** 경로가
    분류 변경에 제일 민감한데, 착용자 혼자서는 그 사슬이 안 선다.
    """
    present = [n for n in CONVERTER_CHARS if n in CHARACTER_REGISTRY]
    for weapon in CONVERTER_WEAPONS:
        for name in sorted(CHARACTER_REGISTRY):
            try:
                _make(name, weapon)          # 무기 종류가 안 맞으면 여기서 걸러진다
            except Exception:
                continue
            for partner in present:
                if partner == name:
                    continue
                _emit(
                    f"wpn:{weapon}|{name}+{partner}",
                    [lambda n=name, w=weapon: _make(n, w), lambda p=partner: _make(p)],
                )


def sweep_multi() -> None:
    for members in MULTI_PARTIES:
        if any(m not in CHARACTER_REGISTRY for m in members):
            continue
        _emit(
            "multi:" + "+".join(members),
            [lambda n=m: _make(n) for m in members],
        )


def _quiet_warnings() -> None:
    """경고를 **경로 없이** stderr로 찍는다.

    기본 포맷은 절대 경로를 앞에 붙이는데, git worktree로 옛 코드를 꺼내 비교하면 그
    경로가 달라 값이 같은데도 diff가 뜬다(실제로 겪었다). 파일명과 줄만 남기면 두 트리
    에서 같은 문자열이 되고, 같은 경고가 여러 번 나오는 것도 한 번으로 접는다.
    """
    seen: set[tuple[str, int, str]] = set()

    def show(message, category, filename, lineno, file=None, line=None):
        key = (pathlib.Path(filename).name, lineno, str(message))
        if key in seen:
            return
        seen.add(key)
        print(f"{key[0]}:{lineno}: {category.__name__}: {message}", file=sys.stderr)

    warnings.showwarning = show


def main() -> int:
    # 리다이렉트 시 cp949가 '—'를 인코딩하지 못해 죽는다(bench.py와 같은 처리).
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure") and not stream.isatty():
            stream.reconfigure(encoding="utf-8")
    _quiet_warnings()

    sweep_solo()
    sweep_pairs()
    sweep_weapons()
    sweep_multi()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
