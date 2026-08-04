from gidc.core.weapon import Weapon, WeaponSubStat
from gidc.enums import WeaponType
from gidc.enums import StatType


class FavoniusCodex(Weapon):
    """페보니우스 비전
    패시브: 바람과 함께
    - 치명타 시 60/70/80/90/100% 확률로 원소 구슬 생성 → 원소 에너지 6pt 회복
      발동 간격: 12/10.5/9/7.5/6초 (스탯에 영향 없음)
    """

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type = WeaponType.CATALYST,
            base_atk    = 510,
            refinement  = refinement,
            sub_stat    = WeaponSubStat(StatType.ENERGY_RECHARGE, 45.9),
        )

    def apply_passive(self, all_hits, wearer) -> None:
        pass
