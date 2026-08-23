from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType


class AquaSimulacra(Weapon):
    """약수 (Aqua Simulacra) | 활 | 5성
    패시브: 만물 정화의 형상
    - HP가 16/20/24/28/32% 증가하고, 해당 무기를 장착한 캐릭터 주변에 적이 존재하면
      캐릭터가 주는 피해가 20/25/30/35/40% 증가한다. 이 효과는 해당 캐릭터가 필드
      위에 존재하거나 대기 상태인 것과 관계없이 발동된다
    """

    _HP_PCT  = [0.16, 0.2, 0.24, 0.28, 0.32]
    _ALL_DMG = [0.2, 0.25, 0.3, 0.35, 0.4]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.BOW,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 약수"

        # 「주변에 적이 존재하면」은 이 계산기의 전제(항상 적을 상대로 계산한다)와
        # 겹쳐 실질적으로 상시 조건이다. 필드/대기 무관하게도 발동하므로 로테이션이
        # 정하는 진짜 변수가 없다 — 묻지 않고 항상 붙인다.
        for hit in all_hits[wearer].values():
            hit.add("hp_pct",        self._HP_PCT[r],  label)
            hit.add("all_dmg_bonus", self._ALL_DMG[r], label)
