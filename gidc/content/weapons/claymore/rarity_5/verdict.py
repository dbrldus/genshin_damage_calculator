from gidc.core.weapon import Weapon, WeaponSubStat
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class Verdict(Weapon):
    """판정
    패시브: 수많은 여명과 황혼의 맹세
    - 공격력 +20/25/30/35/40%
    - 파티원이 결정화 조각 획득 또는 달 결정 반응 발동 시 「약인」 1개 획득
      → 원소전투 스킬 피해 +18/22.5/27/31.5/36% (스택당)
      최대 2스택, 15초 지속, 스킬 피해 후 0.2초 뒤 전부 소멸
    """

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type = WeaponType.CLAYMORE,
            base_atk    = 674,
            refinement  = refinement,
            sub_stat    = WeaponSubStat(StatType.CRIT_RATE, 22.1),
        )

    def apply_passive(self, all_hits, wearer) -> None:
        atk_bonus_refinement   = [0.2,  0.25,  0.3,   0.35,  0.4  ]
        skill_bonus_refinement = [0.18, 0.225, 0.27,  0.315, 0.36 ]
        r = self.refinement - 1

        stacks = ask_int("[판정] 약인 스택 수", 0, 2)
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", atk_bonus_refinement[r], "무기: 판정")
            hit.add("skill_dmg_bonus", skill_bonus_refinement[r] * stacks, "무기: 판정", note="약인 스택")
