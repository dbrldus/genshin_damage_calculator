from gidc.content.characters import make_character
from gidc.core.artifact import SubStat
from gidc.content.weapons import make_weapon
from gidc.content.artifacts import make_artifact
from gidc.enums import ArtifactSet, ArtifactSlot, StatType


def build():
    """이 프리셋의 캐릭터를 새로 만들어 반환한다."""
    char = make_character(name="모나")
    char.level         = 90
    char.constellation = 4
    char.na_level      = 1
    char.skill_level   = 10
    char.burst_level   = 10

    char.weapon = make_weapon(name="드래곤 슬레이어 영웅담", refinement=5)

    char.flower = make_artifact(
        artifact_set   = ArtifactSet.NOBLESSE_OBLIGE,
        slot           = ArtifactSlot.FLOWER,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.HP,
        sub_stats      = [
            SubStat(StatType.CRIT_RATE, 9.7),
            SubStat(StatType.ATK_PCT, 14.6),
            SubStat(StatType.ENERGY_RECHARGE,  6.5),
            SubStat(StatType.CRIT_DMG, 14.0),
        ],
    )

    char.feather = make_artifact(
        artifact_set   = ArtifactSet.NOBLESSE_OBLIGE,
        slot           = ArtifactSlot.FEATHER,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.ATK,
        sub_stats      = [
            SubStat(StatType.HP, 568),
            SubStat(StatType.ENERGY_RECHARGE, 10.4),
            SubStat(StatType.CRIT_RATE, 9.3),
            SubStat(StatType.ATK_PCT, 10.5),
        ],
    )

    char.sands = make_artifact(
        artifact_set   = ArtifactSet.NOBLESSE_OBLIGE,
        slot           = ArtifactSlot.SANDS,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.ENERGY_RECHARGE,
        sub_stats      = [
            SubStat(StatType.HP_PCT,           4.7),
            SubStat(StatType.CRIT_RATE,        6.6),
            SubStat(StatType.ATK_PCT,        11.7),
            SubStat(StatType.ATK,  35),
        ],
    )

    char.goblet = make_artifact(
        artifact_set   = ArtifactSet.EMBLEM_OF_SEVERED_FATE,
        slot           = ArtifactSlot.GOBLET,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.HYDRO_DMG,
        sub_stats      = [
            SubStat(StatType.ENERGY_RECHARGE, 18.1),
            SubStat(StatType.HP_PCT,        10.5),
            SubStat(StatType.ATK_PCT,  15.2),
            SubStat(StatType.ATK, 18),
        ],
    )

    char.circlet = make_artifact(
        artifact_set   = ArtifactSet.NOBLESSE_OBLIGE,
        slot           = ArtifactSlot.CIRCLET,
        rarity         = 5,
        level          = 20,
        main_stat_type = StatType.ATK_PCT,
        sub_stats      = [
            SubStat(StatType.CRIT_RATE,         3.1),
            SubStat(StatType.ENERGY_RECHARGE,   18.1),
            SubStat(StatType.HP_PCT,            4.1),
            SubStat(StatType.DEF_PCT, 21.1),
        ],
    )
    return char
