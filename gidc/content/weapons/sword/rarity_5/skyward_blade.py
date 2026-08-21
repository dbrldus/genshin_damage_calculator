from gidc.core.weapon import Weapon
from gidc.core.profile import SkillHit, SkillType
from gidc.enums import Element, WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class SkywardBlade(Weapon):
    """천공의 검
    패시브: 높은 하늘을 뚫는 이빨
    - 치명타 확률 +4/5/6/7/8%
    - 원소폭발 발동 시 「파공의 기세」 (12초):
        이동속도/공격속도 +10% (계산 불가, 무시)
        일반/강공격 명중 시 ATK 20/25/30/35/40%의 추가 타격 발생
        → 추가 타격은 Phase 1에서 착용자 히트로 주입한다 (add_hits 참조)
    """

    _CRIT_RATE_BONUS = [0.04, 0.05, 0.06, 0.07, 0.08]
    _SKY_FANG_COEFF  = [0.20, 0.25, 0.30, 0.35, 0.40]

    _SKY_FANG_HIT = "파공의 기세 추가 타격"

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.SWORD,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.ENERGY_RECHARGE,
        )

    def add_hits(self, hits, wearer) -> None:
        """Phase 1 — 파공의 기세 추가 타격을 착용자의 히트로 만든다 (물리 피해).

        일단 무조건 만들고, 원소폭발을 안 썼다면 apply_passive(Phase 3)가 도로 뺀다 —
        질문은 Phase 3에 모으는 규약이라 여기서 물을 수 없고, 한 번 만들어 둬야 기초
        스탯·부옵션·성유물·세트가 정상적으로 실린다(천공의 긍지와 같은 꼴).
        """
        hits[self._SKY_FANG_HIT] = SkillHit(
            name       = self._SKY_FANG_HIT,
            skill_type = SkillType.WEAPON,
            coeff      = self._SKY_FANG_COEFF[self.refinement - 1],
            element    = Element.PHYSICAL,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r = self.refinement - 1
        for hit in all_hits[wearer].values():
            hit.add("crit_rate", self._CRIT_RATE_BONUS[r], "무기: 천공의 검")

        # 「파공의 기세」는 원소폭발 발동 후 12초 — 로테이션이 정하므로 묻는다.
        if not ask_bool("[천공의 검] 파공의 기세 활성화 여부 (원소폭발 발동 후 12초)"):
            all_hits[wearer].pop(self._SKY_FANG_HIT, None)

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 이동속도/공격속도 +10% — 히트 단가를 바꾸지 않는다.
    # · 지속 시간 12초 — 활성 여부만 묻고, 추가 타격이 몇 번 들어가는지는 유저가 정한다.
