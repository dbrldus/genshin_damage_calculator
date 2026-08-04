from gidc.content.characters import make_character
from gidc.core.artifact import MainStat, SubStat
from gidc.content.weapons import make_weapon
from gidc.content.artifacts import make_artifact
from gidc.enums import ArtifactSet, ArtifactSlot, StatType


def build():
    """이 프리셋의 캐릭터를 새로 만들어 반환한다."""
    char = make_character(name="푸리나")
    char.level         = 90
    char.constellation = 0
    char.na_level      = 1
    char.skill_level   = 8
    char.burst_level   = 10

    char.weapon = make_weapon(name="페보니우스 검", refinement=5)

    char.flower = make_artifact(
        artifact_set = ArtifactSet.TENACITY_OF_THE_MILLELITH,
        slot         = ArtifactSlot.FLOWER,
        main_stat    = MainStat(StatType.HP, 4780.0),
        sub_stats    = [
            SubStat(StatType.ENERGY_RECHARGE, 13.0),
            SubStat(StatType.CRIT_RATE, 3.1),
            SubStat(StatType.HP_PCT, 5.3),
            SubStat(StatType.DEF_PCT, 24.8),
        ],
    )

    char.feather = make_artifact(
        artifact_set = ArtifactSet.TENACITY_OF_THE_MILLELITH,
        slot         = ArtifactSlot.FEATHER,
        main_stat    = MainStat(StatType.ATK, 311.0),
        sub_stats    = [
            SubStat(StatType.HP_PCT, 19.2),
            SubStat(StatType.ENERGY_RECHARGE, 5.2),
            SubStat(StatType.ELEMENTAL_MASTERY,  42),
            SubStat(StatType.ATK_PCT,   4.1),
        ],
    )

    char.sands = make_artifact(
        artifact_set = ArtifactSet.TENACITY_OF_THE_MILLELITH,
        slot         = ArtifactSlot.SANDS,
        main_stat    = MainStat(StatType.ENERGY_RECHARGE, 51.8),
        sub_stats    = [
            SubStat(StatType.DEF_PCT, 7.3),
            SubStat(StatType.ATK_PCT, 5.8),
            SubStat(StatType.CRIT_RATE, 8.9),
            SubStat(StatType.ATK,  54),
        ],
    )

    char.goblet = make_artifact(
        artifact_set = ArtifactSet.A_DAY_CARVED_FROM_RISING_WINDS,
        slot         = ArtifactSlot.GOBLET,
        main_stat    = MainStat(StatType.HP_PCT, 46.6),
        sub_stats    = [
            SubStat(StatType.HP, 209),
            SubStat(StatType.CRIT_RATE,        3.5),
            SubStat(StatType.ENERGY_RECHARGE,  33.7),
            SubStat(StatType.ATK_PCT, 4.1),
        ],
    )

    char.circlet = make_artifact(
        artifact_set = ArtifactSet.TENACITY_OF_THE_MILLELITH,
        slot         = ArtifactSlot.CIRCLET,
        main_stat    = MainStat(StatType.CRIT_RATE, 31.1),
        sub_stats    = [
            SubStat(StatType.ATK_PCT,         19),
            SubStat(StatType.HP,        807),
            SubStat(StatType.CRIT_DMG,  7.0),
            SubStat(StatType.DEF_PCT,  25.5),
        ],
    )
    return char
