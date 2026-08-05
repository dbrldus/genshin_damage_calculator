from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType


class AquilaFavonia(Weapon):
    """매의 검
    패시브: 서풍 매의 투쟁
    - 공격력 +20/25/30/35/40%
    - 피해를 받으면 발동 (15초 쿨): ATK 100~160% HP 회복 + ATK 200~320% 피해
      → HP 회복 및 피격 반응 피해는 스탯에 영향 없음 (무시)
    """

    _ATK_BONUS = [0.20, 0.25, 0.30, 0.35, 0.40]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.SWORD,
            rarity        = 5,
            tier          = 3,
            refinement    = refinement,
            sub_stat_type = StatType.PHYSICAL_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", self._ATK_BONUS[self.refinement - 1], "무기: 매의 검")
