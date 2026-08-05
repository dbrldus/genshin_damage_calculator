from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class SkywardBlade(Weapon):
    """천공의 검
    패시브: 높은 하늘을 뚫는 이빨
    - 치명타 확률 +4/5/6/7/8%
    - 원소폭발 발동 시 「파공의 기세」 (12초):
        이동속도/공격속도 +10% (계산 불가, 무시)
        일반/강공격 명중 시 ATK 20/25/30/35/40%의 추가 타격 발생
        → 추가 타격은 별도 SkillHit으로 모델링 (sky_fang_coeff 참조)
    """

    _CRIT_RATE_BONUS = [0.04, 0.05, 0.06, 0.07, 0.08]
    _SKY_FANG_COEFF  = [0.20, 0.25, 0.30, 0.35, 0.40]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.SWORD,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.ENERGY_RECHARGE,
        )
        self._sky_fang_active = False

    @property
    def sky_fang_coeff(self) -> float:
        """파공의 기세 활성 시 추가 타격 계수 (0이면 비활성)."""
        return self._SKY_FANG_COEFF[self.refinement - 1] if self._sky_fang_active else 0.0

    def apply_passive(self, all_hits, wearer) -> None:
        r = self.refinement - 1
        for hit in all_hits[wearer].values():
            hit.add("crit_rate", self._CRIT_RATE_BONUS[r], "무기: 천공의 검")

        # self._sky_fang_active = ask_bool("[천공의 검] 파공의 기세 활성화 여부")
