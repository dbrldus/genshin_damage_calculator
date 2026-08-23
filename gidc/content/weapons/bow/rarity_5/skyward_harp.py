from gidc.core.weapon import Weapon
from gidc.core.profile import SkillHit, SkillType
from gidc.enums import Element, WeaponType
from gidc.enums import StatType


class SkywardHarp(Weapon):
    """천공의 날개 (Skyward Harp) | 활 | 5성
    패시브: 하늘에 메아리치는 노래
    - 치명타 피해 +20/25/30/35/40%
    - 공격 명중 시 60/70/80/90/100% 확률로 공격력 125%의 범위 물리 피해를 준다.
      4/3.5/3/2.5/2초마다 1회 발동
      → 추가 타격은 Phase 1에서 착용자 히트로 주입한다 (add_hits 참조)
    """

    _CRIT_DMG_BONUS = [0.2, 0.25, 0.3, 0.35, 0.4]

    _ECHOING_COEFF = 1.25
    _ECHOING_HIT = "메아리치는 노래 추가 타격"

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.BOW,
            rarity        = 5,
            tier          = 3,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    def add_hits(self, hits, wearer) -> None:
        """Phase 1 — 메아리치는 노래 추가 타격을 착용자의 히트로 만든다 (물리 피해).

        발동 확률·쿨타임은 정련에 따라 60~100%·4~2초로 바뀌지만 계수(125%)는 정련과
        무관하게 고정이다. 확률·쿨타임을 기대값으로 접지 않는 프로젝트 방침(천공의
        마루와 동일)에 따라 계수에 반영하지 않는다 — 히트 1개가 발동 1회이고, 몇 회가
        로테이션에 들어가는지는 유저가 정한다.

        skill_type이 WEAPON인 것이 요점이다 — 일반/강공격 명중으로 발동하지만 그 자신은
        일반 공격이 아니라서 「일반 공격 피해 보너스」를 받지 않는다.
        """
        hits[self._ECHOING_HIT] = SkillHit(
            name       = self._ECHOING_HIT,
            skill_type = SkillType.WEAPON,
            coeff      = self._ECHOING_COEFF,
            element    = Element.PHYSICAL,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        # 조건 없이 상시 적용되는 치명타 피해 — 착용자에게만 들어간다.
        # 메아리치는 노래 히트에도 함께 붙는다(Phase 1에서 이미 만들어져 있다).
        for hit in all_hits[wearer].values():
            hit.add("crit_dmg", self._CRIT_DMG_BONUS[self.refinement - 1], "무기: 천공의 날개")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 60/70/80/90/100% 발동 확률 · 4/3.5/3/2.5/2초 쿨타임 — 확률을 기대값으로
    #   접지 않는다. 추가 타격 1회가 히트 1개다.
