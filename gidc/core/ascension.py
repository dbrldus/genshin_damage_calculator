"""어센션 보너스 스탯 — 돌파할 때마다 오르는 캐릭터 고유 스탯 하나.

    보너스 값 = 기초값(스탯·성급으로 결정) × 어센션 배율(돌파 단계로 결정)

두 축이 완전히 분리돼 있어서, 캐릭터는 「무슨 스탯이 붙는가」와 「몇 성인가」만
선언하면 된다. 값은 여기서 나온다 — 캐릭터마다 0.384 같은 최종 숫자를 손으로
적어 두면 돌파 단계를 바꿀 수 없고, 틀려도 드러나지 않는다.

출처: Genshin Impact Wiki — Character/Level Scaling (Bonus Attribute)
"""
from __future__ import annotations

from gidc.enums import StatType

# 돌파 단계(0~6) → 배율. 2·3·5·6단계에서만 오른다 (4단계는 3단계와 같다).
# 0단계는 아직 한 번도 돌파하지 않은 상태라 보너스가 없다.
BONUS_MULTIPLIER: tuple[int, ...] = (0, 0, 1, 2, 2, 3, 4)

MAX_PHASE = len(BONUS_MULTIPLIER) - 1

# 원소 피해 보너스는 7원소가 같은 기초값을 쓴다.
_ELEMENTAL_DMG_STATS = (
    StatType.PYRO_DMG, StatType.HYDRO_DMG, StatType.CRYO_DMG, StatType.ELECTRO_DMG,
    StatType.ANEMO_DMG, StatType.GEO_DMG, StatType.DENDRO_DMG,
)

# 기초값 — 게임 표기가 %인 스탯은 비율로, 원소 마스터리만 실수치로 둔다
# (엔진의 SkillHit 필드 단위와 같다). 4성에는 치명타 확률·피해가 없다(위키 표의 '—').
_BASE_VALUE: dict[int, dict[StatType, float]] = {
    4: {
        **{stat: 0.06 for stat in _ELEMENTAL_DMG_STATS},
        StatType.ATK_PCT:           0.06,
        StatType.HP_PCT:            0.06,
        StatType.DEF_PCT:           0.075,
        StatType.PHYSICAL_DMG:      0.075,
        StatType.ENERGY_RECHARGE:   0.067,
        StatType.ELEMENTAL_MASTERY: 24.0,
        StatType.HEALING_BONUS:     0.0462,
    },
    5: {
        **{stat: 0.072 for stat in _ELEMENTAL_DMG_STATS},
        StatType.ATK_PCT:           0.072,
        StatType.HP_PCT:            0.072,
        StatType.DEF_PCT:           0.09,
        StatType.PHYSICAL_DMG:      0.09,
        StatType.ENERGY_RECHARGE:   0.08,
        StatType.ELEMENTAL_MASTERY: 28.8,
        StatType.HEALING_BONUS:     0.0554,
        StatType.CRIT_RATE:         0.048,
        StatType.CRIT_DMG:          0.096,
    },
}


def bonus_value(rarity: int, stat: StatType, phase: int) -> float:
    """어센션 보너스 스탯의 최종 값. phase는 돌파 단계(0~6).

    캐릭터 고유 치명타 확률 5%처럼 SkillHit이 이미 기본값으로 들고 있는 몫은
    여기 포함되지 않는다 — 이 함수가 주는 것은 돌파로 늘어난 증가분뿐이다."""
    if not 0 <= phase <= MAX_PHASE:
        raise ValueError(f"돌파 단계는 0~{MAX_PHASE}입니다. (입력: {phase})")

    table = _BASE_VALUE.get(rarity)
    if table is None:
        raise ValueError(f"어센션 기초값 표는 4성/5성만 있습니다. (입력: {rarity}성)")
    if stat not in table:
        raise ValueError(
            f"{rarity}성 어센션 보너스 스탯으로 '{stat.value}'는 없습니다. "
            f"가능: {sorted(s.value for s in table)}"
        )
    return table[stat] * BONUS_MULTIPLIER[phase]
