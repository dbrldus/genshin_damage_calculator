from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.enums import MoonsignLevel
from gidc.core.party_state import moonsign_level


class ProspectorsShovel(Weapon):
    """채굴의 삽
    패시브: 빠른 결단
    - 감전 반응으로 주는 피해 +48/60/72/84/96%
    - 달 감전 반응으로 주는 피해 +12/15/18/21/24%
    - 달빛 징조·보름: 달 감전 반응으로 주는 피해가 추가로 +12/15/18/21/24%

    무기 효과는 착용자에게만 적용된다. 달빛 징조 레벨은 파티 구성에서 유도한다.
    """

    _ELECTROCHARGED = [0.48, 0.60, 0.72, 0.84, 0.96]
    _LUNAR_CHARGED  = [0.12, 0.15, 0.18, 0.21, 0.24]
    _FULL_MOON_LC   = [0.12, 0.15, 0.18, 0.21, 0.24]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.POLEARM,
            rarity        = 4,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.ATK_PCT,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r = self.refinement - 1

        lunar_charged = self._LUNAR_CHARGED[r]
        # 달빛 징조·보름일 때 달 감전 피해 보너스 추가 (파티 구성에서 유도).
        if moonsign_level(all_hits) is MoonsignLevel.FULL:
            lunar_charged += self._FULL_MOON_LC[r]

        for hit in all_hits[wearer].values():
            hit.add("electrocharged_bonus", self._ELECTROCHARGED[r], "무기: 채굴의 삽")
            hit.add("lunar_charged_bonus",  lunar_charged, "무기: 채굴의 삽")
