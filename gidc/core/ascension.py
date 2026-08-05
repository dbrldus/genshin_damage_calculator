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

# ── 레벨 ↔ 돌파 단계 ────────────────────────────────────────────────────────
# 단계별 레벨 상한. 돌파는 상한에 닿아야 할 수 있고, 돌파하면 상한만 열릴 뿐 레벨은
# 그대로다. 그래서 **상한 레벨에서는 두 상태가 모두 유효하다** — 게임에서 Lv.20/20
# (미돌파)과 Lv.20/40(돌파 완료)은 기초 스탯도 어센션 보너스도 다른 캐릭터다.
# 그 밖의 레벨은 단계가 하나로 정해지므로 물어볼 것이 없다.
PHASE_CAP: tuple[int, ...] = (20, 40, 50, 60, 70, 80, 90)
# 각 단계에서 가능한 최저 레벨 = 직전 단계의 상한 (0단계만 Lv.1부터).
_PHASE_MIN: tuple[int, ...] = (1, *PHASE_CAP[:-1])

assert len(PHASE_CAP) == MAX_PHASE + 1, "돌파 단계 수와 레벨 상한 표가 어긋납니다"

MAX_LEVEL = PHASE_CAP[-1]


def phases_for_level(level: int) -> tuple[int, ...]:
    """그 레벨에서 가능한 돌파 단계. 상한 레벨(20/40/50/60/70/80)만 둘이고 나머지는 하나다.

    선택지를 만드는 쪽(웹 드롭다운)과 값을 검증하는 쪽(resolve_phase)이 같은 표를
    읽게 하려고 함수로 둔다 — 화면이 규칙을 베껴 들고 있으면 조용히 어긋난다."""
    if not 1 <= level <= MAX_LEVEL:
        raise ValueError(f"레벨은 1~{MAX_LEVEL}입니다. (입력: {level})")
    return tuple(p for p in range(MAX_PHASE + 1) if _PHASE_MIN[p] <= level <= PHASE_CAP[p])


def resolve_phase(level: int, phase: int | None = None) -> int:
    """(레벨, 돌파 단계) 짝을 확정한다.

    phase가 None이면 그 레벨의 기본값 — 상한 레벨에서는 **돌파한 쪽**을 고른다
    (돌파를 미룬 상태가 예외적이므로). 짝이 성립하지 않으면 조용히 잘라 쓰지 않고
    실패시킨다 — Lv.90인데 0돌파 같은 조합은 게임에 없고, 기초 스탯이 통째로 틀어진다."""
    allowed = phases_for_level(level)
    if phase is None:
        return allowed[-1]
    if phase not in allowed:
        raise ValueError(
            f"Lv.{level}에서 가능한 돌파 단계는 {list(allowed)}입니다. (입력: {phase})"
        )
    return phase

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
