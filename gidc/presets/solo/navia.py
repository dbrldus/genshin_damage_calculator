from gidc.content.characters import make_character
from gidc.core.artifact import MainStat, SubStat
from gidc.content.weapons import make_weapon
from gidc.content.artifacts import make_artifact
from gidc.enums import ArtifactSet, ArtifactSlot, StatType

_NWEW = ArtifactSet.NIGHTTIME_WHISPERS_IN_THE_ECHOING_WOODS
_SMS  = ArtifactSet.SILKEN_MOONS_SERENADE


def build():
    """이 프리셋의 캐릭터를 새로 만들어 반환한다."""
    char = make_character(name="나비아")
    char.level         = 90
    char.constellation = 6
    char.na_level      = 10
    char.skill_level   = 10
    char.burst_level   = 10

    char.weapon = make_weapon(name="판정", refinement=5)

    char.flower = make_artifact(
        artifact_set = _NWEW,
        slot         = ArtifactSlot.FLOWER,
        main_stat    = MainStat(StatType.HP, 4780.0),
        sub_stats    = [
            SubStat(StatType.HP_PCT,    4.1),
            SubStat(StatType.CRIT_RATE, 12.8),
            SubStat(StatType.DEF,       16),
            SubStat(StatType.CRIT_DMG,  21.0),
        ],
    )

    char.feather = make_artifact(
        artifact_set = _SMS,
        slot         = ArtifactSlot.FEATHER,
        main_stat    = MainStat(StatType.ATK, 311.0),
        sub_stats    = [
            SubStat(StatType.DEF,       23),
            SubStat(StatType.ATK_PCT,   8.7),
            SubStat(StatType.CRIT_DMG,  30.3),
            SubStat(StatType.CRIT_RATE, 7.8),
        ],
    )

    char.sands = make_artifact(
        artifact_set = _NWEW,
        slot         = ArtifactSlot.SANDS,
        main_stat    = MainStat(StatType.ATK_PCT, 46.6),
        sub_stats    = [
            SubStat(StatType.CRIT_DMG,        33.4),
            SubStat(StatType.HP_PCT,           5.3),
            SubStat(StatType.DEF,             35),
            SubStat(StatType.ENERGY_RECHARGE,  4.5),
        ],
    )

    char.goblet = make_artifact(
        artifact_set = _NWEW,
        slot         = ArtifactSlot.GOBLET,
        main_stat    = MainStat(StatType.GEO_DMG, 46.6),
        sub_stats    = [
            SubStat(StatType.CRIT_RATE,       13.2),
            SubStat(StatType.CRIT_DMG,        10.9),
            SubStat(StatType.ENERGY_RECHARGE,  6.5),
            SubStat(StatType.DEF,             23),
        ],
    )

    char.circlet = make_artifact(
        artifact_set = _NWEW,
        slot         = ArtifactSlot.CIRCLET,
        main_stat    = MainStat(StatType.CRIT_DMG, 62.2),
        sub_stats    = [
            SubStat(StatType.ATK_PCT,         19.2),
            SubStat(StatType.CRIT_RATE,        6.2),
            SubStat(StatType.ENERGY_RECHARGE,  5.2),
            SubStat(StatType.HP,             209),
        ],
    )
    return char
