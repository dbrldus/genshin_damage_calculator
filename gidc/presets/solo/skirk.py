from gidc.content.characters import make_character
from gidc.core.artifact import MainStat, SubStat
from gidc.content.weapons import make_weapon
from gidc.content.artifacts import make_artifact
from gidc.enums import ArtifactSet, ArtifactSlot, StatType


def build():
    """이 프리셋의 캐릭터를 새로 만들어 반환한다."""
    char = make_character(name="스커크")
    char.level         = 90
    char.constellation = 0
    char.na_level      = 1
    char.skill_level   = 10
    char.burst_level   = 8

    char.weapon = make_weapon(name="에슈의 재앙", refinement=5)

    char.flower = make_artifact(
        artifact_set = ArtifactSet.FINALE_OF_THE_DEEP_GALLERIES,
        slot         = ArtifactSlot.FLOWER,
        main_stat    = MainStat(StatType.HP, 4780.0),
        sub_stats    = [
            SubStat(StatType.CRIT_DMG, 19.4),
            SubStat(StatType.ATK_PCT, 8.7),
            SubStat(StatType.CRIT_RATE,  5.4),
            SubStat(StatType.HP_PCT, 5.8),
        ],
    )

    char.feather = make_artifact(
        artifact_set = ArtifactSet.FINALE_OF_THE_DEEP_GALLERIES,
        slot         = ArtifactSlot.FEATHER,
        main_stat    = MainStat(StatType.ATK, 311.0),
        sub_stats    = [
            SubStat(StatType.CRIT_DMG, 14.0),
            SubStat(StatType.CRIT_RATE, 9.7),
            SubStat(StatType.ENERGY_RECHARGE,  5.8),
            SubStat(StatType.ATK_PCT, 11.1),
        ],
    )

    char.sands = make_artifact(
        artifact_set = ArtifactSet.FINALE_OF_THE_DEEP_GALLERIES,
        slot         = ArtifactSlot.SANDS,
        main_stat    = MainStat(StatType.ATK_PCT, 46.6),
        sub_stats    = [
            SubStat(StatType.CRIT_RATE, 10.9),
            SubStat(StatType.CRIT_DMG, 7.8),
            SubStat(StatType.ELEMENTAL_MASTERY, 40),
            SubStat(StatType.DEF,  42),
        ],
    )

    char.goblet = make_artifact(
        artifact_set = ArtifactSet.NIGHTTIME_WHISPERS_IN_THE_ECHOING_WOODS,
        slot         = ArtifactSlot.GOBLET,
        main_stat    = MainStat(StatType.CRYO_DMG, 46.6),
        sub_stats    = [
            SubStat(StatType.CRIT_RATE, 14.0),
            SubStat(StatType.ATK_PCT, 9.3),
            SubStat(StatType.CRIT_DMG, 7.8),
            SubStat(StatType.ELEMENTAL_MASTERY, 21),
        ],
    )

    char.circlet = make_artifact(
        artifact_set = ArtifactSet.FINALE_OF_THE_DEEP_GALLERIES,
        slot         = ArtifactSlot.CIRCLET,
        main_stat    = MainStat(StatType.CRIT_DMG, 62.2),
        sub_stats    = [
            SubStat(StatType.DEF, 19),
            SubStat(StatType.ATK, 33),
            SubStat(StatType.CRIT_RATE, 13.6),
            SubStat(StatType.DEF_PCT,  7.3),
        ],
    )
    return char
