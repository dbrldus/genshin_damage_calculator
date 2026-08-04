"""캐릭터 기초 HP/공격력/방어력 — 레벨과 돌파 단계로 정해진다.

    스탯 = 기초값 × 레벨 배율 + 최대 어센션 값 × 어센션 배율

세 축이 완전히 분리돼 있다. 기초값과 최대 어센션 값은 캐릭터별 상수, 레벨 배율은
레벨과 성급으로, 어센션 배율은 돌파 단계로만 정해진다. 그래서 캐릭터는 이름과 성급만
알려주면 되고 Lv.90 숫자를 손에 들고 있을 필요가 없다.

자료는 data/character_level_scaling/ 의 CSV 넷이며 tools/extract_level_scaling.py 가
엑셀에서 구워 낸다. 표 하나가 파일 하나다.

    ascension_multiplier.csv     돌파 단계 → 분자, 분모
    level_multiplier.csv         레벨 → 4성/5성 배율
    character_base_value.csv     캐릭터 → 기초 HP/공격력/방어력 (Lv.1)
    character_max_ascension.csv  캐릭터 → 6돌파에서 더해지는 몫

캐릭터 이름은 그 표의 영문 이름이 열쇠이고, 등록된 캐릭터의 클래스명과 같다
(Skirk, Xilonen, …).

어센션 배율이 분자/분모로 나뉘어 있는 것은 원래 0/182, 38/182 … 182/182 라는 분수이기
때문이다. 부동소수점으로 미리 접어 두면 마지막 자리가 흔들리므로 곱셈 뒤에 나눈다.

여기서 쓰는 level_multiplier.csv 는 캐릭터 기초 스탯의 성장 곡선이다 —
같은 data/ 아래 level_multiplier.json 은 반응 피해용이라 이름만 같고 다른 표다
(core/level_multiplier.py 가 읽는다).
"""
from __future__ import annotations

import csv
import pathlib
from typing import NamedTuple

_DIR = pathlib.Path(__file__).parent / "data" / "character_level_scaling"


def _rows(name: str) -> list[list[str]]:
    """CSV 한 장을 머리글 빼고 읽는다. 값은 전부 단순 숫자·영문이라 따옴표가 없다."""
    with (_DIR / name).open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader)                      # 머리글
        return [row for row in reader if row]


def _stat_table(name: str) -> dict[str, tuple[float, float, float]]:
    return {row[0]: (float(row[1]), float(row[2]), float(row[3])) for row in _rows(name)}


_ascension = _rows("ascension_multiplier.csv")
# 분모는 모든 행이 같다 — 표를 나눠 적었을 뿐 하나의 분수 수열이다.
_ASCENSION_NUMERATORS: tuple[int, ...] = tuple(int(row[1]) for row in _ascension)
_ASCENSION_DENOMINATOR: int            = int(_ascension[0][2])

# 레벨 → 성급 → 배율
_LEVEL_MULTIPLIER: dict[int, dict[int, float]] = {
    int(row[0]): {4: float(row[1]), 5: float(row[2])} for row in _rows("level_multiplier.csv")
}

_BASE_VALUE    = _stat_table("character_base_value.csv")
_MAX_ASCENSION = _stat_table("character_max_ascension.csv")

MAX_LEVEL = max(_LEVEL_MULTIPLIER)
MAX_PHASE = len(_ASCENSION_NUMERATORS) - 1


class BaseStats(NamedTuple):
    hp:      float
    atk:     float
    defense: float


def is_known(name: str) -> bool:
    """표에 이 이름의 캐릭터가 있는가."""
    return name in _BASE_VALUE


def names() -> list[str]:
    return sorted(_BASE_VALUE)


def base_stats(name: str, rarity: int, level: int, phase: int) -> BaseStats:
    """레벨 level, 돌파 phase일 때의 기초 HP/공격력/방어력.

    게임 화면의 표시값은 반올림된 정수지만 여기서는 소수를 그대로 돌려준다 — 반올림은
    보여줄 때 하면 되고, 중간에 접으면 버프가 쌓일수록 오차가 커진다."""
    base = _BASE_VALUE.get(name)
    asc  = _MAX_ASCENSION.get(name)
    if base is None or asc is None:
        raise KeyError(
            f"레벨 스케일링 표에 '{name}'이(가) 없습니다. tools/extract_level_scaling.py 참고."
        )
    if not 1 <= level <= MAX_LEVEL:
        raise ValueError(f"레벨은 1~{MAX_LEVEL}입니다. (입력: {level})")
    if not 0 <= phase <= MAX_PHASE:
        raise ValueError(f"돌파 단계는 0~{MAX_PHASE}입니다. (입력: {phase})")

    by_rarity = _LEVEL_MULTIPLIER[level]
    if rarity not in by_rarity:
        raise ValueError(f"레벨 배율 표는 {sorted(by_rarity)}성만 있습니다. (입력: {rarity}성)")

    level_mult = by_rarity[rarity]
    numerator  = _ASCENSION_NUMERATORS[phase]

    return BaseStats(*(
        b * level_mult + a * numerator / _ASCENSION_DENOMINATOR
        for b, a in zip(base, asc)
    ))
