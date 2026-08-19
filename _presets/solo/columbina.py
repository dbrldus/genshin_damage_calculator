from gidc.content.characters import make_character
from gidc.core.artifact import SubStat
from gidc.core.weapon import WeaponSubStat
from gidc.content.weapons import make_weapon
from gidc.content.artifacts import make_artifact
from gidc.enums import ArtifactSet, ArtifactSlot, StatType
from gidc.enums import WeaponType


def build():
    """이 프리셋의 캐릭터를 새로 만들어 반환한다."""
    char = make_character(name="콜롬비나")
    char.level         = 90
    char.constellation = 1
    char.na_level      = 1
    char.skill_level   = 10
    char.burst_level   = 10

    char.weapon = make_weapon(name = "페보니우스 비전", refinement  = 5)

    char.flower = make_artifact(
        artifact_set   = ArtifactSet.AUBADE_OF_MORNINGSTAR_AND_MOON,
        slot           = ArtifactSlot.FLOWER,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.HP,
        sub_stats      = [
            SubStat(StatType.CRIT_RATE,    2.7),
            SubStat(StatType.CRIT_DMG,  13.2),
            SubStat(StatType.ELEMENTAL_MASTERY,  37),
            SubStat(StatType.DEF,       58),
        ],
    )

    char.feather = make_artifact(
        artifact_set   = ArtifactSet.AUBADE_OF_MORNINGSTAR_AND_MOON,
        slot           = ArtifactSlot.FEATHER,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.ATK,
        sub_stats      = [
            SubStat(StatType.CRIT_RATE,        7.0),
            SubStat(StatType.CRIT_DMG,         14.8),
            SubStat(StatType.ENERGY_RECHARGE, 16.2),
            SubStat(StatType.HP_PCT,           9.9),
        ],
    )

    char.sands = make_artifact(
        artifact_set   = ArtifactSet.AUBADE_OF_MORNINGSTAR_AND_MOON,
        slot           = ArtifactSlot.SANDS,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.HP_PCT,
        sub_stats      = [
            SubStat(StatType.ENERGY_RECHARGE, 9.7),
            SubStat(StatType.CRIT_RATE,       10.1),
            SubStat(StatType.CRIT_DMG,        20.2),
            SubStat(StatType.ELEMENTAL_MASTERY, 19),
        ],
    )

    char.goblet = make_artifact(
        artifact_set   = ArtifactSet.AUBADE_OF_MORNINGSTAR_AND_MOON,
        slot           = ArtifactSlot.GOBLET,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.HP_PCT,
        sub_stats      = [
            SubStat(StatType.DEF,          19),
            SubStat(StatType.CRIT_DMG,        7.0),
            SubStat(StatType.CRIT_RATE,        12.4),
            SubStat(StatType.ATK_PCT,  9.3),
        ],
    )

    char.circlet = make_artifact(
        artifact_set   = ArtifactSet.SONG_OF_DAYS_PAST,
        slot           = ArtifactSlot.CIRCLET,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.CRIT_DMG,
        sub_stats      = [
            SubStat(StatType.CRIT_RATE, 12.8),
            SubStat(StatType.HP,  269),
            SubStat(StatType.ATK, 16),
            SubStat(StatType.ENERGY_RECHARGE, 9.7),
        ],
    )
    return char
