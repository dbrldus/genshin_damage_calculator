from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class Deathmatch(Weapon):
    """결투의 창
    패시브: 검투사
    - 주변에 적이 2기 이상일 때: 공격력 +16/20/24/28/32%, 방어력 +16/20/24/28/32%
    - 주변에 적이 2기 미만일 때: 공격력 +24/30/36/42/48%

    무기 효과는 착용자에게만 적용된다.
    """

    _ATK_CROWD  = [0.16, 0.20, 0.24, 0.28, 0.32]  # 적 2기 이상
    _DEF_CROWD  = [0.16, 0.20, 0.24, 0.28, 0.32]  # 적 2기 이상
    _ATK_SOLO   = [0.24, 0.30, 0.36, 0.42, 0.48]  # 적 2기 미만

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.POLEARM,
            rarity        = 4,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r = self.refinement - 1

        if ask_bool("[결투의 창] 주변에 적이 2기 이상?"):
            for hit in all_hits[wearer].values():
                hit.add("atk_pct", self._ATK_CROWD[r], "무기: 결투의 창", note="적 2기+")
                hit.add("def_pct", self._DEF_CROWD[r], "무기: 결투의 창", note="적 2기+")
        else:
            for hit in all_hits[wearer].values():
                hit.add("atk_pct", self._ATK_SOLO[r], "무기: 결투의 창", note="적 <2")
