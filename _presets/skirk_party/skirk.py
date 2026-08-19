from gidc.content.characters import make_character
from gidc.core.artifact import SubStat
from gidc.content.weapons import make_weapon
from gidc.content.artifacts import make_artifact
from gidc.enums import ArtifactSet, ArtifactSlot, StatType


def build():
    """이 프리셋의 캐릭터를 새로 만들어 반환한다."""
    char = make_character(name="스커크")
    char.level         = 90
    char.constellation = 4
    char.na_level      = 6
    char.skill_level   = 10
    char.burst_level   = 10

    char.weapon = make_weapon(name="창백한 섬광", refinement=1)

    char.flower = make_artifact(
        artifact_set   = ArtifactSet.FINALE_OF_THE_DEEP_GALLERIES,
        slot           = ArtifactSlot.FLOWER,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.HP,
        sub_stats      = [
            SubStat(StatType.CRIT_DMG, 19.4),
            SubStat(StatType.ATK, 14),
            SubStat(StatType.ATK_PCT,  5.3),
            SubStat(StatType.CRIT_RATE, 10.5),
        ],
    )

    char.feather = make_artifact(
        artifact_set   = ArtifactSet.FINALE_OF_THE_DEEP_GALLERIES,
        slot           = ArtifactSlot.FEATHER,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.ATK,
        sub_stats      = [
            SubStat(StatType.DEF_PCT, 6.6),
            SubStat(StatType.DEF, 19),
            SubStat(StatType.CRIT_DMG,  18.7),
            SubStat(StatType.CRIT_RATE, 14.8),
        ],
    )

    char.sands = make_artifact(
        artifact_set   = ArtifactSet.FINALE_OF_THE_DEEP_GALLERIES,
        slot           = ArtifactSlot.SANDS,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.ATK_PCT,
        sub_stats      = [
            SubStat(StatType.CRIT_RATE, 10.9),
            SubStat(StatType.CRIT_DMG, 21.0),
            SubStat(StatType.DEF, 44),
            SubStat(StatType.HP_PCT, 5.3),
        ],
    )

    char.goblet = make_artifact(
        artifact_set   = ArtifactSet.FRAGMENT_OF_HARMONIC_WHIMSY,
        slot           = ArtifactSlot.GOBLET,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.CRYO_DMG,
        sub_stats      = [
            SubStat(StatType.ATK_PCT, 15.2),
            SubStat(StatType.DEF, 16),
            SubStat(StatType.CRIT_DMG, 13.2),
            SubStat(StatType.CRIT_RATE, 9.3),
        ],
    )

    char.circlet = make_artifact(
        artifact_set   = ArtifactSet.FINALE_OF_THE_DEEP_GALLERIES,
        slot           = ArtifactSlot.CIRCLET,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.CRIT_DMG,
        sub_stats      = [
            SubStat(StatType.ATK_PCT, 15.2),
            SubStat(StatType.CRIT_RATE, 10.5),
            SubStat(StatType.DEF, 16),
            SubStat(StatType.ATK, 33),
        ],
    )
    return char
