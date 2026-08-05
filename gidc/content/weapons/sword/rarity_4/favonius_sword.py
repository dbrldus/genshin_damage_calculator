from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType


class FavoniusSword(Weapon):
    """페보니우스 검
    패시브: 바람과 함께
    - 치명타 시 60/70/80/90/100% 확률로 원소 구슬 생성 → 원소 에너지 6pt 회복
      발동 간격: 12/10.5/9/7.5/6초 (스탯에 영향 없음)
    """

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.SWORD,
            rarity        = 4,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.ENERGY_RECHARGE,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        pass
