from gidc.content.characters import make_character
from gidc.core.artifact import SubStat
from gidc.content.weapons import make_weapon
from gidc.content.artifacts import make_artifact
from gidc.enums import ArtifactSet, ArtifactSlot, StatType


def build():
    """이 프리셋의 캐릭터를 새로 만들어 반환한다."""
    char = make_character(name="푸리나")
    char.level         = 90
    char.constellation = 3
    char.na_level      = 1
    char.skill_level   = 10
    char.burst_level   = 10

    char.weapon = make_weapon(name="페보니우스 검", refinement=1)

    char.flower = make_artifact(
        artifact_set   = ArtifactSet.TENACITY_OF_THE_MILLELITH,
        slot           = ArtifactSlot.FLOWER,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.HP,
        sub_stats      = [
            SubStat(StatType.DEF,    19),
            SubStat(StatType.CRIT_RATE, 12.4),
            SubStat(StatType.CRIT_DMG,  13.2),
            SubStat(StatType.ELEMENTAL_MASTERY, 16),
        ],
    )

    char.feather = make_artifact(
        artifact_set   = ArtifactSet.TENACITY_OF_THE_MILLELITH,
        slot           = ArtifactSlot.FEATHER,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.ATK,
        sub_stats      = [
            SubStat(StatType.ELEMENTAL_MASTERY,       40),
            SubStat(StatType.CRIT_RATE, 7.8),
            SubStat(StatType.CRIT_DMG,  13.2),
            SubStat(StatType.ENERGY_RECHARGE,   13.0),
        ],
    )

    char.sands = make_artifact(
        artifact_set   = ArtifactSet.TENACITY_OF_THE_MILLELITH,
        slot           = ArtifactSlot.SANDS,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.ENERGY_RECHARGE,
        sub_stats      = [
            SubStat(StatType.DEF,             35),
            SubStat(StatType.HP_PCT,           8.7),
            SubStat(StatType.CRIT_DMG,        11.7),
            SubStat(StatType.ATK,  35),
        ],
    )

    char.goblet = make_artifact(
        artifact_set   = ArtifactSet.A_DAY_CARVED_FROM_RISING_WINDS,
        slot           = ArtifactSlot.GOBLET,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.HP_PCT,
        sub_stats      = [
            SubStat(StatType.ELEMENTAL_MASTERY, 21),
            SubStat(StatType.CRIT_DMG,        19.4),
            SubStat(StatType.ENERGY_RECHARGE,  11.0),
            SubStat(StatType.CRIT_RATE,        6.6),
        ],
    )

    char.circlet = make_artifact(
        artifact_set   = ArtifactSet.TENACITY_OF_THE_MILLELITH,
        slot           = ArtifactSlot.CIRCLET,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.CRIT_DMG,
        sub_stats      = [
            SubStat(StatType.HP_PCT,         8.2),
            SubStat(StatType.ELEMENTAL_MASTERY,        42),
            SubStat(StatType.DEF,             44),
            SubStat(StatType.ENERGY_RECHARGE,  17.5),
        ],
    )
    return char
