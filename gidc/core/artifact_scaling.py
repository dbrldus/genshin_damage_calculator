"""성유물 주옵션 — 성급과 강화 레벨로 정해진다.

무기(core/weapon_scaling.py)와 달리 곱셈 규칙이 없다. 무기 기본 공격력은
「기초값 × 레벨 배율 + 돌파 보너스」로 되살릴 수 있지만, 성유물 주옵션은 게임이
(성급, 스탯, 강화 레벨)마다 반올림된 값을 그대로 들고 있어 표가 곧 규칙이다.
그래서 이 모듈에는 표를 찾는 일밖에 없다.

    주옵션 값 = 표[스탯][성급][강화 레벨]

강화 레벨은 게임의 +N 그대로 **0부터** 세고, 상한이 성급마다 다르다
(5성 +20, 4성 +16, 3성 +12, 1·2성 +4). 부옵션은 이 표를 타지 않는다 — 강화할 때마다
무작위로 붙는 값이라 레벨로 정해지지 않고, 지금도 사용자가 화면에서 읽어 적는다.

자료는 data/artifact_level_scaling/main_stat_value.csv 한 장이며
tools/extract_artifact_scaling.py 가 엑셀에서 구워 낸다. 값은 **게임 표기 단위**다
(치명타 피해 62.2% → 62.2). core/stat.py의 GearStat과 같은 규칙이라 MainStat을
그대로 만들 수 있다.
"""
from __future__ import annotations

import csv
import pathlib

from gidc.enums import StatType

_PATH = pathlib.Path(__file__).parent / "data" / "artifact_level_scaling" / "main_stat_value.csv"

# (스탯, 성급) → 강화 레벨 0..N의 값. 인덱스가 곧 레벨이다.
_VALUES: dict[tuple[StatType, int], tuple[float, ...]] = {}

with _PATH.open(encoding="utf-8", newline="") as _f:
    _reader = csv.reader(_f)
    next(_reader)
    for _row in _reader:
        if not _row:
            continue
        _key = (StatType[_row[0]], int(_row[1]))
        if len(_VALUES.get(_key, ())) != int(_row[2]):
            raise ValueError(f"주옵션 표의 레벨이 이어지지 않습니다: {_row}")
        _VALUES[_key] = _VALUES.get(_key, ()) + (float(_row[3]),)


def rarities() -> tuple[int, ...]:
    return tuple(sorted({rarity for _, rarity in _VALUES}))


def main_stats(rarity: int) -> tuple[StatType, ...]:
    """그 성급의 표에 있는 주옵션 스탯. 부위별로 실제 붙을 수 있는 것은 더 좁다 —
    그 제한은 core/artifact.py의 _VALID_MAIN_STATS가 갖는다."""
    found = tuple(stat for stat, r in _VALUES if r == rarity)
    if not found:
        raise ValueError(f"성유물 주옵션 표에 {rarity}성이 없습니다. (가능: {list(rarities())})")
    return found


def max_level(rarity: int) -> int:
    """그 성급의 최대 강화 레벨. 5성 +20, 4성 +16, 3성 +12, 1·2성 +4."""
    return len(_VALUES[(main_stats(rarity)[0], rarity)]) - 1


def main_stat_value(stat: StatType, rarity: int, level: int) -> float:
    """강화 레벨 level일 때의 주옵션 값 (**게임 표기 단위**)."""
    key = (stat, rarity)
    if key not in _VALUES:
        raise ValueError(
            f"{rarity}성 성유물의 주옵션으로 '{stat.value}'는 표에 없습니다. "
            f"(가능: {sorted(s.value for s in main_stats(rarity))})"
        )
    top = max_level(rarity)
    if not 0 <= level <= top:
        raise ValueError(f"{rarity}성 성유물의 강화 레벨은 0~{top}입니다. (입력: {level})")
    return _VALUES[key][level]


def level_from_value(stat: StatType, rarity: int, value: float) -> int:
    """화면에 적힌 주옵션 값으로 강화 레벨을 되찾는다.

    무기 쪽 tier_from_substat과 같은 사정이다 — 값만 손에 들고 있을 때(주옵션 값을
    직접 적던 시절의 빌드 JSON) 표의 어느 칸인지 알아내야 한다. 표시값이 반올림돼
    있으므로(원소 마스터리 186.5 → 187) 가장 가까운 칸을 고르되, 한 칸 간격의 절반보다
    더 벌어져 있으면 표 밖의 값이라 보고 실패시킨다."""
    values = _VALUES[(stat, rarity)] if (stat, rarity) in _VALUES else ()
    if not values:
        raise ValueError(f"{rarity}성 성유물의 주옵션으로 '{stat.value}'는 표에 없습니다.")
    level = min(range(len(values)), key=lambda i: abs(values[i] - value))
    step  = min(b - a for a, b in zip(values, values[1:])) if len(values) > 1 else 1.0
    if abs(values[level] - value) > step / 2:
        raise ValueError(
            f"{rarity}성 '{stat.value}' 주옵션 값 {value}는 표에 없습니다 "
            f"(가장 가까운 +{level}은 {values[level]})."
        )
    return level
