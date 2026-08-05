"""무기 기본 공격력·부옵션 — 성급·티어·레벨·돌파 단계로 정해진다.

    기본 공격력 = 기초값(성급·티어) × 레벨 배율(성급·티어·레벨) + 돌파 보너스(성급·단계)
    부옵션      = 기초값(스탯·성급·티어) × 레벨 배율(레벨)

캐릭터 쪽(core/base_stats.py)과 같은 축 분리이고, 무기만의 차이가 둘 있다.

  · **부옵션은 5레벨마다 오른다.** 기본 공격력은 매 레벨 오르지만 부옵션은 Lv.1~4가
    한 칸, 그 뒤로 5의 배수에서만 바뀐다. 그래서 배율 표가 19행뿐이고, 자료를 90행으로
    펴지 않았다 — 규칙은 여기 substat_multiplier() 하나에만 있다.
  · **부옵션에는 돌파 항이 없다.** 같은 레벨이면 돌파 전/후의 부옵션이 같고
    기본 공격력만 달라진다.

그래서 무기가 선언할 것은 **성급 · 티어 · 부옵션 종류** 셋뿐이다. 「티어」는 한 성급 안의
기본 공격력 등급(1이 가장 낮다)이며, 부옵션 등급도 겸한다 — 기본 공격력이 낮은 티어일수록
부옵션이 높은 게임의 교환 관계라, 축이 둘이 아니라 하나다. 5성 무기 542/608/674/741이
곧 Tier 1/2/3/4다.

자료는 data/weapon_level_scaling/ 의 CSV 다섯이며 tools/extract_weapon_scaling.py 가
엑셀에서 구워 낸다. 표 하나가 파일 하나다.

    main_base_value.csv            (성급, 티어) → Lv.1 기본 공격력
    main_level_multiplier.csv      레벨 → 성급·티어별 배율
    main_ascension_value.csv       (성급, 돌파 단계) → 더해지는 공격력
    secondary_base_value.csv       (스탯, 성급, 티어) → Lv.1 부옵션 값 (게임 표기 단위)
    secondary_level_multiplier.csv 레벨 → 부옵션 배율 (19행)
"""
from __future__ import annotations

import csv
import pathlib

from gidc.core import ascension
from gidc.enums import StatType

_DIR = pathlib.Path(__file__).parent / "data" / "weapon_level_scaling"


def _rows(name: str) -> list[list[str]]:
    with (_DIR / name).open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        return next(reader), [row for row in reader if row]


_, _base_rows           = _rows("main_base_value.csv")
_, _ascension_rows      = _rows("main_ascension_value.csv")
_mult_header, _mult_rows = _rows("main_level_multiplier.csv")
_, _sub_base_rows       = _rows("secondary_base_value.csv")
_, _sub_mult_rows       = _rows("secondary_level_multiplier.csv")

# (성급, 티어) → Lv.1 기본 공격력
_BASE_ATK: dict[tuple[int, int], float] = {
    (int(r[0]), int(r[1])): float(r[2]) for r in _base_rows
}

# 성급 → 돌파 단계별 추가 공격력 (인덱스가 곧 단계, 0단계는 0)
_ASCENSION: dict[int, tuple[float, ...]] = {}
for _r in _ascension_rows:
    _ASCENSION.setdefault(int(_r[0]), ())
    _ASCENSION[int(_r[0])] += (float(_r[2]),)

# 레벨 배율 열 머리글은 "<블록>_tier<N>" 꼴이고, 블록 하나가 여러 성급을 덮는다
# (1~3성은 곡선이 같고 기초값만 다르다).
_BLOCK_RARITIES: dict[str, tuple[int, ...]] = {"1-3star": (1, 2, 3), "4star": (4,), "5star": (5,)}

# (성급, 티어) → {레벨: 배율}
_LEVEL_MULTIPLIER: dict[tuple[int, int], dict[int, float]] = {}
for _column, _label in enumerate(_mult_header[1:], start=1):
    _block, _tier = _label.rsplit("_tier", 1)
    for _rarity in _BLOCK_RARITIES[_block]:
        _LEVEL_MULTIPLIER[(_rarity, int(_tier))] = {
            int(row[0]): float(row[_column]) for row in _mult_rows
        }

# (스탯, 성급, 티어) → Lv.1 부옵션 값. 값은 **게임 표기 단위**다(치명타 확률 4.8 → 4.8).
# core/stat.py의 GearStat과 같은 규칙이라 WeaponSubStat을 그대로 만들 수 있다.
_SUB_BASE: dict[tuple[StatType, int, int], float] = {
    (StatType[r[0]], int(r[1]), int(r[2])): float(r[3]) for r in _sub_base_rows
}

# 레벨 → 부옵션 배율. 5레벨마다 한 칸이라 19행이다.
_SUB_MULTIPLIER: dict[int, float] = {int(r[0]): float(r[1]) for r in _sub_mult_rows}

MAX_LEVEL = max(next(iter(_LEVEL_MULTIPLIER.values())))

# 돌파 단계별 레벨 상한 — 캐릭터와 같은 표를 쓴다(core/ascension.PHASE_CAP).
# 1·2성 무기만 4단계 Lv.70에서 끝나므로 앞부분을 잘라 쓴다.
_PHASE_CAP = ascension.PHASE_CAP


def rarities() -> tuple[int, ...]:
    return tuple(sorted({rarity for rarity, _ in _BASE_ATK}))


def tiers(rarity: int) -> tuple[int, ...]:
    """그 성급에 있는 티어. 1·2성은 하나뿐이고 3성은 셋, 4·5성은 넷이다."""
    found = tuple(sorted(t for r, t in _BASE_ATK if r == rarity))
    if not found:
        raise ValueError(f"무기 스케일링 표에 {rarity}성이 없습니다. (가능: {list(rarities())})")
    return found


def max_phase(rarity: int) -> int:
    """그 성급 무기의 최대 돌파 단계. 1·2성은 4, 3~5성은 6이다."""
    if rarity not in _ASCENSION:
        raise ValueError(f"무기 돌파 표에 {rarity}성이 없습니다.")
    return len(_ASCENSION[rarity]) - 1


def max_level(rarity: int) -> int:
    """그 성급 무기의 최대 레벨. 1·2성은 70, 3~5성은 90이다."""
    return _PHASE_CAP[max_phase(rarity)]


def phases_for_level(rarity: int, level: int) -> tuple[int, ...]:
    """그 레벨에서 가능한 돌파 단계. 상한 레벨(20/40/50/60/70/80)만 둘이고 나머지는 하나다.

    캐릭터와 같은 사정이다 — Lv.20/20(미돌파)과 Lv.20/40(돌파 완료)은 기본 공격력이
    다르다. 선택지를 만드는 쪽과 값을 검증하는 쪽이 같은 표를 읽게 하려고 함수로 둔다."""
    top = max_phase(rarity)
    if not 1 <= level <= _PHASE_CAP[top]:
        raise ValueError(f"{rarity}성 무기의 레벨은 1~{_PHASE_CAP[top]}입니다. (입력: {level})")
    lowest = (1, *_PHASE_CAP[:top])
    return tuple(p for p in range(top + 1) if lowest[p] <= level <= _PHASE_CAP[p])


def resolve_phase(rarity: int, level: int, phase: int | None = None) -> int:
    """(레벨, 돌파 단계) 짝을 확정한다. phase가 None이면 상한 레벨에서 **돌파한 쪽**을 고른다."""
    allowed = phases_for_level(rarity, level)
    if phase is None:
        return allowed[-1]
    if phase not in allowed:
        raise ValueError(
            f"{rarity}성 무기 Lv.{level}에서 가능한 돌파 단계는 {list(allowed)}입니다. (입력: {phase})"
        )
    return phase


def substat_multiplier(level: int) -> float:
    """부옵션 레벨 배율. 기본 공격력과 달리 **5레벨마다** 오른다.

    Lv.1~4는 첫 칸(1.000)에 머물고 그 뒤로는 5의 배수에서만 바뀐다. 표가 19행인 것도,
    이 계단 규칙이 이 함수 하나에만 있는 것도 그래서다."""
    if not 1 <= level <= MAX_LEVEL:
        raise ValueError(f"레벨은 1~{MAX_LEVEL}입니다. (입력: {level})")
    return _SUB_MULTIPLIER[1 if level < 5 else level - level % 5]


def base_atk(rarity: int, tier: int, level: int, phase: int) -> float:
    """레벨 level, 돌파 phase일 때의 기본 공격력.

    게임 화면의 표시값은 반올림된 정수지만 여기서는 소수를 그대로 돌려준다 — 캐릭터
    기초 스탯(core/base_stats.py)과 같은 이유로, 중간에 접으면 버프가 쌓일수록 오차가
    커진다. 5성 Tier 1 Lv.90/6돌파는 542가 아니라 541.83이다."""
    _validate(rarity, tier, level, phase)
    return _BASE_ATK[(rarity, tier)] * _LEVEL_MULTIPLIER[(rarity, tier)][level] \
        + _ASCENSION[rarity][phase]


def substat_value(stat: StatType, rarity: int, tier: int, level: int) -> float:
    """레벨 level일 때의 부옵션 값 (**게임 표기 단위** — 치명타 확률 22.1%면 22.1).

    돌파 단계를 받지 않는다. 부옵션에는 돌파 항이 없어서 같은 레벨이면 돌파 전/후가
    같은 값이다."""
    _validate(rarity, tier, level, phase=None)
    key = (stat, rarity, tier)
    if key not in _SUB_BASE:
        raise ValueError(
            f"{rarity}성 Tier {tier} 무기의 부옵션으로 '{stat.value}'는 표에 없습니다. "
            f"(가능: {sorted(s.value for s, r, t in _SUB_BASE if (r, t) == (rarity, tier))})"
        )
    return _SUB_BASE[key] * substat_multiplier(level)


# ── 티어 찾기 ─────────────────────────────────────────────────────────────
# 티어는 게임 화면에 적혀 있지 않다. 그래서 무기 파일을 새로 쓸 때 티어를 어디선가
# 베껴 오는 대신, **화면에서 읽히는 값**으로 되찾을 수 있게 해 둔다. 아래 둘 중 아무거나
# 쓰면 되고, 값이 티어마다 충분히 벌어져 있어(부옵션은 4:3:2:1, 기본 공격력은 성급당
# 4단계) 후보가 하나로 좁혀진다. 좁혀지지 않으면 예외로 알린다.
def tier_from_substat(rarity: int, stat: StatType, value: float, level: int = 1) -> int:
    """부옵션 종류와 값으로 티어를 되찾는다. 기본은 Lv.1 — 무기를 막 얻었을 때의 화면 값.

    표시값은 반올림돼 있으므로(원소 마스터리 57.6 → 58) 가장 가까운 티어를 고르되,
    2등과 충분히 벌어져 있지 않으면 실패시킨다."""
    candidates = {
        tier: substat_value(stat, rarity, tier, level)
        for tier in tiers(rarity) if (stat, rarity, tier) in _SUB_BASE
    }
    return _closest(candidates, value, f"{rarity}성 · {stat.value} {value}")


def tier_from_base_atk(rarity: int, value: float, level: int = 90, phase: int | None = None) -> int:
    """기본 공격력으로 티어를 되찾는다. 기본은 Lv.90 만렙 — 위키 무기 문서에 늘 적혀 있는 값
    (5성 542/608/674/741 이 곧 Tier 1/2/3/4)."""
    resolved   = resolve_phase(rarity, level, phase)
    candidates = {tier: base_atk(rarity, tier, level, resolved) for tier in tiers(rarity)}
    return _closest(candidates, value, f"{rarity}성 · 기본 공격력 {value}")


def _closest(candidates: dict[int, float], value: float, what: str) -> int:
    """가장 가까운 티어. 1등과 2등의 거리 차가 두 배 미만이면 고르지 않는다 —
    표시 반올림 때문에 살짝 어긋나는 것과, 애초에 표에 없는 값을 넣은 것은 다르다."""
    if not candidates:
        raise ValueError(f"{what}: 해당하는 티어가 표에 없습니다.")
    ranked = sorted(candidates, key=lambda tier: abs(candidates[tier] - value))
    best   = abs(candidates[ranked[0]] - value)
    if len(ranked) > 1 and best * 2 >= abs(candidates[ranked[1]] - value):
        raise ValueError(
            f"{what}: 티어가 하나로 좁혀지지 않습니다. "
            f"후보 {({t: round(v, 3) for t, v in candidates.items()})}"
        )
    return ranked[0]


def _validate(rarity: int, tier: int, level: int, phase: int | None) -> None:
    if tier not in tiers(rarity):
        raise ValueError(f"{rarity}성 무기의 티어는 {list(tiers(rarity))}입니다. (입력: {tier})")
    if phase is not None and phase not in phases_for_level(rarity, level):
        raise ValueError(
            f"{rarity}성 무기 Lv.{level}에서 가능한 돌파 단계는 "
            f"{list(phases_for_level(rarity, level))}입니다. (입력: {phase})"
        )
    if phase is None:
        phases_for_level(rarity, level)      # 레벨 범위 검사
