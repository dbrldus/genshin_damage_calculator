from gidc.content.characters import make_character
from gidc.core.artifact import MainStat, SubStat
from gidc.core.weapon import WeaponSubStat
from gidc.content.weapons import make_weapon
from gidc.content.artifacts import make_artifact
from gidc.enums import ArtifactSet, ArtifactSlot, StatType
from gidc.enums import WeaponType


def build():
    """이 프리셋의 캐릭터를 새로 만들어 반환한다."""
    char = make_character(name="이네파")
    char.level         = 90
    char.constellation = 0
    char.na_level      = 1
    char.skill_level   = 8
    char.burst_level   = 8

    char.weapon = make_weapon(name = "채굴의 삽", refinement = 4)

    char.flower = make_artifact(
        artifact_set = ArtifactSet.SILKEN_MOONS_SERENADE,
        slot         = ArtifactSlot.FLOWER,
        main_stat    = MainStat(StatType.HP, 4780.0),
        sub_stats    = [
            SubStat(StatType.CRIT_DMG,   22.5),
            SubStat(StatType.DEF,       16),
            SubStat(StatType.DEF_PCT, 5.8),
            SubStat(StatType.CRIT_RATE,  9.7)
        ],
    )

    char.feather = make_artifact(
        artifact_set = ArtifactSet.SILKEN_MOONS_SERENADE,
        slot         = ArtifactSlot.FEATHER,
        main_stat    = MainStat(StatType.ATK, 311.0),
        sub_stats    = [
            SubStat(StatType.CRIT_DMG,        13.2),
            SubStat(StatType.ATK_PCT,          9.9),
            SubStat(StatType.CRIT_RATE, 6.6),
            SubStat(StatType.DEF,       39),
        ],
    )

    char.sands = make_artifact(
        artifact_set = ArtifactSet.SILKEN_MOONS_SERENADE,
        slot         = ArtifactSlot.SANDS,
        main_stat    = MainStat(StatType.ATK_PCT, 46.6),
        sub_stats    = [
            SubStat(StatType.DEF,        53),
            SubStat(StatType.CRIT_RATE,        3.1),
            SubStat(StatType.ENERGY_RECHARGE,  11.7),
            SubStat(StatType.CRIT_DMG,         21.8),
        ],
    )

    char.goblet = make_artifact(
        artifact_set = ArtifactSet.SONG_OF_DAYS_PAST,
        slot         = ArtifactSlot.GOBLET,
        main_stat    = MainStat(StatType.ATK_PCT, 46.6),
        sub_stats    = [
            SubStat(StatType.CRIT_RATE,       17.9),
            SubStat(StatType.ELEMENTAL_MASTERY, 44),
            SubStat(StatType.DEF,             21),
            SubStat(StatType.CRIT_DMG,         5.4),
        ],
    )

    char.circlet = make_artifact(
        artifact_set = ArtifactSet.SILKEN_MOONS_SERENADE,
        slot         = ArtifactSlot.CIRCLET,
        main_stat    = MainStat(StatType.CRIT_DMG, 62.2),
        sub_stats    = [
            SubStat(StatType.ATK,         14),
            SubStat(StatType.ENERGY_RECHARGE,  22.7),
            SubStat(StatType.DEF_PCT,          10.9),
            SubStat(StatType.CRIT_RATE,       6.6),
        ],
    )
    return char
