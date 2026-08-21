from gidc.core.weapon import Weapon
from gidc.core.profile import SkillHit, SkillType
from gidc.enums import Element, WeaponType
from gidc.enums import StatType


class SkywardSpine(Weapon):
    """천공의 마루 (Skyward Spine) | 장병기 | 5성
    패시브: 검은 날개를 절단하는 이빨
    - 치명타 확률 +8/10/12/14/16%
    - 일반 공격 속도 +12% (피해 계산에 들어가지 않아 미구현)
    - 일반 공격과 강공격이 적 명중 시 50% 확률로 진공 칼날을 날려 작은 범위 내의 적에게
      추가로 공격력 40/55/70/85/100%의 피해를 준다. 2초마다 1회 발동
      → 추가 타격은 Phase 1에서 착용자 히트로 주입한다 (add_hits 참조)
    """

    _CRIT_RATE_BONUS    = [0.08, 0.10, 0.12, 0.14, 0.16]
    _VACUUM_BLADE_COEFF = [0.40, 0.55, 0.70, 0.85, 1.00]

    _VACUUM_BLADE_HIT = "진공 칼날 피해"

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.POLEARM,
            rarity        = 5,
            tier          = 3,
            refinement    = refinement,
            sub_stat_type = StatType.ENERGY_RECHARGE,
        )

    def add_hits(self, hits, wearer) -> None:
        """Phase 1 — 진공 칼날을 착용자의 히트로 만든다 (물리 피해).

        발동 조건이 없어 천공의 긍지와 달리 묻지 않는다 — 50% 확률·2초 쿨은 확률 발동을
        기대값으로 접지 않는 프로젝트 방침(콜롬비나 A4와 동일)에 따라 계수에 반영하지
        않는다. **히트 1개가 칼날 1발**이고, 몇 발이 로테이션에 들어가는지는 유저가 정한다.

        skill_type이 WEAPON인 것이 요점이다 — 일반/강공격 명중으로 발동하지만 그 자신은
        일반 공격이 아니라서 「일반 공격 피해 보너스」를 받지 않는다.
        """
        hits[self._VACUUM_BLADE_HIT] = SkillHit(
            name       = self._VACUUM_BLADE_HIT,
            skill_type = SkillType.WEAPON,
            coeff      = self._VACUUM_BLADE_COEFF[self.refinement - 1],
            element    = Element.PHYSICAL,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        # 조건 없이 상시 적용되는 치명타 확률 — 착용자에게만 들어간다.
        # 진공 칼날 히트에도 함께 붙는다(Phase 1에서 이미 만들어져 있다).
        for hit in all_hits[wearer].values():
            hit.add("crit_rate", self._CRIT_RATE_BONUS[self.refinement - 1], "무기: 천공의 마루")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 일반 공격 속도 +12% — 히트 단가를 바꾸지 않는다.
    # · 50% 확률 · 2초 쿨 — 확률을 기대값으로 접지 않는다. 칼날 1발이 히트 1개다.
