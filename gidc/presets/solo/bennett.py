from gidc.content.characters import make_character
from gidc.core.artifact import MainStat, SubStat
from gidc.content.weapons import make_weapon
from gidc.content.artifacts import make_artifact
from gidc.enums import ArtifactSet, ArtifactSlot, StatType


def build():
    """이 프리셋의 캐릭터를 새로 만들어 반환한다."""
    char = make_character(name="베넷")
    char.level         = 90
    char.constellation = 6
    char.na_level      = 1
    char.skill_level   = 2
    char.burst_level   = 10

    char.weapon = make_weapon(name="매의 검", refinement=1)

    char.flower = make_artifact(
        artifact_set = ArtifactSet.NOBLESSE_OBLIGE,
        slot         = ArtifactSlot.FLOWER,
        main_stat    = MainStat(StatType.HP, 4780.0),
        sub_stats    = [
            SubStat(StatType.DEF_PCT, 13.1),
            SubStat(StatType.ENERGY_RECHARGE, 20.7),
            SubStat(StatType.ELEMENTAL_MASTERY,       16),
            SubStat(StatType.HP_PCT,   8.7),
        ],
    )

    char.feather = make_artifact(
        artifact_set = ArtifactSet.NIGHTTIME_WHISPERS_IN_THE_ECHOING_WOODS,
        slot         = ArtifactSlot.FEATHER,
        main_stat    = MainStat(StatType.ATK, 311.0),
        sub_stats    = [
            SubStat(StatType.ATK_PCT, 4.1),
            SubStat(StatType.CRIT_RATE, 2.7),
            SubStat(StatType.ENERGY_RECHARGE, 29.8),
            SubStat(StatType.CRIT_DMG, 6.2),
        ],
    )

    char.sands = make_artifact(
        artifact_set = ArtifactSet.NOBLESSE_OBLIGE,
        slot         = ArtifactSlot.SANDS,
        main_stat    = MainStat(StatType.ENERGY_RECHARGE, 51.8),
        sub_stats    = [
            SubStat(StatType.HP, 807),
            SubStat(StatType.ATK_PCT, 8.7),
            SubStat(StatType.ATK, 19),
            SubStat(StatType.DEF_PCT,  10.2),
        ],
    )

    char.goblet = make_artifact(
        artifact_set = ArtifactSet.NOBLESSE_OBLIGE,
        slot         = ArtifactSlot.GOBLET,
        main_stat    = MainStat(StatType.ELEMENTAL_MASTERY, 187),
        sub_stats    = [
            SubStat(StatType.HP_PCT, 4.1),
            SubStat(StatType.ATK_PCT,        9.3),
            SubStat(StatType.DEF_PCT,  5.8),
            SubStat(StatType.ENERGY_RECHARGE, 30.5),
        ],
    )

    char.circlet = make_artifact(
        artifact_set = ArtifactSet.NOBLESSE_OBLIGE,
        slot         = ArtifactSlot.CIRCLET,
        main_stat    = MainStat(StatType.CRIT_RATE, 31.1),
        sub_stats    = [
            SubStat(StatType.DEF, 23),
            SubStat(StatType.ELEMENTAL_MASTERY,  140),
            SubStat(StatType.ENERGY_RECHARGE, 16.8),
            SubStat(StatType.HP_PCT, 10.5),
        ],
    )
    return char
