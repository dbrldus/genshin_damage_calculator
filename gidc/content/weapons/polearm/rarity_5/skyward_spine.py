from gidc.core.weapon import Weapon, WeaponSubStat
from gidc.enums import WeaponType
from gidc.enums import StatType


class SkywardSpine(Weapon):
    """천공의 마루 (Skyward Spine) | 장병기 | 5성
    패시브: 검은 날개를 절단하는 이빨
    - 치명타 확률 +8/10/12/14/16%
    - 일반 공격 속도 +12% (피해 계산에 들어가지 않아 미구현)
    - 일반 공격과 강공격이 적 명중 시 50% 확률로 진공 칼날을 날려 작은 범위 내의 적에게
      추가로 공격력 40/55/70/85/100%의 피해를 준다. 2초마다 1회 발동
      → 추가 타격은 별도 SkillHit으로 모델링 (vacuum_blade_coeff 참조, 천공의 검과 동일한 방식)
    """

    _CRIT_RATE_BONUS    = [0.08, 0.10, 0.12, 0.14, 0.16]
    _VACUUM_BLADE_COEFF = [0.40, 0.55, 0.70, 0.85, 1.00]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type = WeaponType.POLEARM,
            base_atk    = 674,
            refinement  = refinement,
            sub_stat    = WeaponSubStat(StatType.ENERGY_RECHARGE, 36.8),
        )

    @property
    def vacuum_blade_coeff(self) -> float:
        """진공 칼날 추가 타격의 공격력 계수 (물리 피해).

        50% 확률 · 2초 쿨은 반영하지 않은 1회분 계수다 — 확률 발동을 기대값으로 접지 않는
        프로젝트 방침(콜롬비나 A4와 동일)을 따른다. 발동 횟수는 로테이션 문제라 히트를
        만드는 쪽에서 정한다."""
        return self._VACUUM_BLADE_COEFF[self.refinement - 1]

    def apply_passive(self, all_hits, wearer) -> None:
        # 조건 없이 상시 적용되는 치명타 확률 — 착용자에게만 들어간다.
        for hit in all_hits[wearer].values():
            hit.add("crit_rate", self._CRIT_RATE_BONUS[self.refinement - 1], "무기: 천공의 마루")
