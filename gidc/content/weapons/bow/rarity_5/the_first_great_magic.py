from gidc.core.weapon import Weapon
from gidc.core.profile import SkillType
from gidc.enums import WeaponType
from gidc.enums import StatType


class TheFirstGreatMagic(Weapon):
    """최초의 대마술 (The First Great Magic) | 활 | 5성
    패시브: 위대한 자·파르치팔
    - 강공격으로 주는 피해가 16/20/24/28/32% 증가한다.
    - 파티 내에 장착 캐릭터와 동일한 원소 타입의 캐릭터 1명당 (장비 장착자 자신
      포함) 1스택의 「트릭」 효과를 획득한다. 1/2/3 스택 또는 3스택 이상의 「트릭」
      효과를 받을 시, 공격력이 16/20/24/28/32%·32/40/48/56/64%·48/60/72/84/96%
      증가한다.
    - 장착 캐릭터와 다른 원소를 가진 캐릭터 한 명당 1스택의 「연기」 효과를
      획득한다(이동속도 보너스, 미구현).
    """

    _CA_DMG     = [0.16, 0.2, 0.24, 0.28, 0.32]
    _ATK_STACK1 = [0.16, 0.2, 0.24, 0.28, 0.32]
    _ATK_STACK2 = [0.32, 0.4, 0.48, 0.56, 0.64]
    _ATK_STACK3 = [0.48, 0.6, 0.72, 0.84, 0.96]

    # 스택 수 → 그 스택에서의 배율표. 스택마다 「추가분」이 아니라 보유 스택 수에 대한
    # 누적 총량이 그대로 게임 표기값이다(안개를 가르는 회광·비뢰의 고동과 같은 구조).
    _STACK_TABLE = (_ATK_STACK1, _ATK_STACK2, _ATK_STACK3)

    _MAX_STACKS = 3

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.BOW,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 최초의 대마술"
        hits  = all_hits[wearer].values()

        # 효과 1: 강공격 피해 — 조건 없이 착용자에게만 붙는다.
        for hit in hits:
            if hit.skill_type is SkillType.CHARGED_ATK:
                hit.add("charged_atk_dmg_bonus", self._CA_DMG[r], label)

        # 효과 2 「트릭」. 동원소 캐릭터 수(착용자 자신 포함)는 파티 구성만으로
        # 정해지므로 묻지 않고 유도한다(떠오르는 천일 밤의 꿈과 같은 판단).
        others = [c for c in all_hits if c is not wearer]
        same_n = 1 + sum(1 for c in others if c.element is wearer.element)
        stacks = min(same_n, self._MAX_STACKS)

        bonus = self._STACK_TABLE[stacks - 1][r]
        for hit in hits:
            hit.add("atk_pct", bonus, label, note="트릭")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 「연기」 효과(이동속도 보너스) — 히트 단가에 들어갈 자리가 없다.
