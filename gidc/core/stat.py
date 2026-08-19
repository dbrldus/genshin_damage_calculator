"""장비 옵션의 공통 표기 규칙.

성유물 주/부옵션과 무기 부옵션은 모두 **게임에 표시된 값을 그대로** 적는다.
%로 표시되는 스탯만 내부에서 0.01을 곱해 비율로 바꾸고, 실수치 스탯은 그대로 쓴다.

    SubStat(StatType.CRIT_RATE, 12.4)         → 0.124
    MainStat(StatType.HP_PCT, 46.6)           → 0.466
    WeaponSubStat(StatType.CRIT_DMG, 66.2)    → 0.662
    SubStat(StatType.ELEMENTAL_MASTERY, 40)   → 40   (실수치라 변환 없음)

Artifact와 Weapon이 이 베이스를 공유하므로 두 곳의 규칙이 갈라지지 않는다.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from gidc.enums import StatType, PERCENT_STAT_TYPES, PERCENT_SCALE


@dataclass(frozen=True)
class GearStat:
    """장비 옵션 하나. value는 게임 표기값이고, 계산에는 scaled를 쓴다."""
    stat_type: StatType
    value: float

    @property
    def is_percent(self) -> bool:
        return self.stat_type in PERCENT_STAT_TYPES

    @property
    def scaled(self) -> float:
        """계산에 실제로 쓰이는 내부 값 (%스탯이면 표기값 × 0.01)."""
        return self.value * PERCENT_SCALE if self.is_percent else self.value

    def __str__(self) -> str:
        # 계산에는 표에서 나온 소수를 그대로 쓰고(성유물 주옵션 원소 마스터리 186.5,
        # 무기 부옵션 220.512), **보여줄 때만** 게임처럼 반올림한다. 게임 표시 자리수는
        # %스탯이 소수 1자리, 실수치가 정수다. 파이썬 기본 round()는 5를 짝수 쪽으로
        # 보내(220.5 → 220) 게임과 어긋나므로 half-up으로 맞춘다 — 제례의 악장 원소
        # 마스터리가 정확히 그 경계에 있다.
        digits = 1 if self.is_percent else 0
        shown  = Decimal(str(self.value)).quantize(Decimal(1).scaleb(-digits), ROUND_HALF_UP)
        return f"{self.stat_type.value}: {shown}{'%' if self.is_percent else ''}"
