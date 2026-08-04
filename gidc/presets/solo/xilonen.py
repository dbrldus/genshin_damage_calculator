from gidc.content.characters import make_character
from gidc.core.artifact import MainStat, SubStat
from gidc.content.weapons import make_weapon
from gidc.content.artifacts import make_artifact
from gidc.enums import ArtifactSet, ArtifactSlot, StatType


def build():
    """이 프리셋의 캐릭터를 새로 만들어 반환한다."""
    char = make_character(name="실로닌")
    char.level         = 90
    char.constellation = 0
    char.na_level      = 6
    char.skill_level   = 10
    char.burst_level   = 8

    char.weapon = make_weapon(name="바위산을 맴도는 노래", refinement=1)

    char.flower = make_artifact(
        artifact_set = ArtifactSet.SCROLL_OF_THE_HERO_OF_CINDER_CITY,
        slot         = ArtifactSlot.FLOWER,
        main_stat    = MainStat(StatType.HP, 4780.0),
        sub_stats    = [
            SubStat(StatType.ELEMENTAL_MASTERY,       37),
            SubStat(StatType.ENERGY_RECHARGE, 15.5),
            SubStat(StatType.DEF_PCT, 13.1),
            SubStat(StatType.CRIT_RATE,   2.7),
        ],
    )

    char.feather = make_artifact(
        artifact_set = ArtifactSet.SCROLL_OF_THE_HERO_OF_CINDER_CITY,
        slot         = ArtifactSlot.FEATHER,
        main_stat    = MainStat(StatType.ATK, 311.0),
        sub_stats    = [
            SubStat(StatType.CRIT_DMG, 17.1),
            SubStat(StatType.DEF_PCT, 11.7),
            SubStat(StatType.HP, 508),
            SubStat(StatType.ENERGY_RECHARGE, 11.0),
        ],
    )

    char.sands = make_artifact(
        artifact_set = ArtifactSet.SCROLL_OF_THE_HERO_OF_CINDER_CITY,
        slot         = ArtifactSlot.SANDS,
        main_stat    = MainStat(StatType.DEF_PCT, 58.3),
        sub_stats    = [
            SubStat(StatType.DEF, 39),
            SubStat(StatType.ENERGY_RECHARGE, 10.4),
            SubStat(StatType.CRIT_DMG, 19.4),
            SubStat(StatType.ATK,  31),
        ],
    )

    char.goblet = make_artifact(
        artifact_set = ArtifactSet.SCROLL_OF_THE_HERO_OF_CINDER_CITY,
        slot         = ArtifactSlot.GOBLET,
        main_stat    = MainStat(StatType.DEF_PCT, 58.3),
        sub_stats    = [
            SubStat(StatType.DEF, 23),
            SubStat(StatType.CRIT_DMG,        11.7),
            SubStat(StatType.ENERGY_RECHARGE,  18.1),
            SubStat(StatType.CRIT_RATE, 5.8),
        ],
    )

    char.circlet = make_artifact(
        artifact_set = ArtifactSet.SCROLL_OF_THE_HERO_OF_CINDER_CITY,
        slot         = ArtifactSlot.CIRCLET,
        main_stat    = MainStat(StatType.DEF_PCT, 58.3),
        sub_stats    = [
            SubStat(StatType.CRIT_DMG, 6.2),
            SubStat(StatType.ENERGY_RECHARGE,  13.0),
            SubStat(StatType.CRIT_RATE, 7.0),
            SubStat(StatType.HP, 1016),
        ],
    )
    return char
