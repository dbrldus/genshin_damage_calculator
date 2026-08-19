from gidc.content.characters import make_character
from gidc.core.artifact import SubStat
from gidc.content.weapons import make_weapon
from gidc.content.artifacts import make_artifact
from gidc.enums import ArtifactSet, ArtifactSlot, StatType


def build():
    """이 프리셋의 캐릭터를 새로 만들어 반환한다."""
    char = make_character(name="에스코피에")
    char.level         = 90
    char.constellation = 1
    char.na_level      = 1
    char.skill_level   = 9
    char.burst_level   = 7

    char.weapon = make_weapon(name="천공의 마루", refinement=1)

    char.flower = make_artifact(
        artifact_set   = ArtifactSet.SCROLL_OF_THE_HERO_OF_CINDER_CITY,
        slot           = ArtifactSlot.FLOWER,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.HP,
        sub_stats      = [
            SubStat(StatType.ATK_PCT, 11.1),
            SubStat(StatType.ENERGY_RECHARGE, 18.1),
            SubStat(StatType.DEF,  32),
            SubStat(StatType.DEF_PCT, 7.3),
        ],
    )

    char.feather = make_artifact(
        artifact_set   = ArtifactSet.AUBADE_OF_MORNINGSTAR_AND_MOON,
        slot           = ArtifactSlot.FEATHER,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.ATK,
        sub_stats      = [
            SubStat(StatType.ENERGY_RECHARGE, 21.4),
            SubStat(StatType.HP, 299),
            SubStat(StatType.CRIT_RATE, 3.1),
            SubStat(StatType.HP_PCT, 11.1),
        ],
    )

    char.sands = make_artifact(
        artifact_set   = ArtifactSet.SCROLL_OF_THE_HERO_OF_CINDER_CITY,
        slot           = ArtifactSlot.SANDS,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.ENERGY_RECHARGE,
        sub_stats      = [
            SubStat(StatType.CRIT_DMG, 14.8),
            SubStat(StatType.ATK_PCT, 5.3),
            SubStat(StatType.ATK, 62),
            SubStat(StatType.ELEMENTAL_MASTERY, 23),
        ],
    )

    char.goblet = make_artifact(
        artifact_set   = ArtifactSet.SCROLL_OF_THE_HERO_OF_CINDER_CITY,
        slot           = ArtifactSlot.GOBLET,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.ATK_PCT,
        sub_stats      = [
            SubStat(StatType.CRIT_DMG, 7.0),
            SubStat(StatType.ELEMENTAL_MASTERY, 16),
            SubStat(StatType.DEF_PCT, 17.5),
            SubStat(StatType.ENERGY_RECHARGE, 17.5),
        ],
    )

    char.circlet = make_artifact(
        artifact_set   = ArtifactSet.SCROLL_OF_THE_HERO_OF_CINDER_CITY,
        slot           = ArtifactSlot.CIRCLET,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.CRIT_DMG,
        sub_stats      = [
            SubStat(StatType.DEF, 23),
            SubStat(StatType.ENERGY_RECHARGE, 19.4),
            SubStat(StatType.ELEMENTAL_MASTERY, 51),
            SubStat(StatType.CRIT_RATE, 3.1),
        ],
    )
    return char
