from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class PrimordialJadeWingedSpear(Weapon):
    """화박연 (Primordial Jade Winged-Spear) | 장병기 | 5성
    패시브: 정의의 솔개창
    - 적 명중 시 자신의 공격력이 3.2/3.9/4.6/5.3/6% 증가한다. 지속 시간: 6초. 최대 중첩수: 7회.
      해당 효과는 0.3초마다 1번 발동한다. 최대 중첩 시 피해가 12/15/18/21/24% 증가한다
    """

    _ATK_PER_STACK       = [0.032, 0.039, 0.046, 0.053, 0.06]
    _MAX_STACK_DMG_BONUS = [0.12, 0.15, 0.18, 0.21, 0.24]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.POLEARM,
            rarity        = 5,
            tier          = 3,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    _MAX_STACKS = 7

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 화박연"

        # 「정의의 솔개창」 스택. 트리거(적 명중, 0.3초당 최대 1회)는 하나뿐이라 스택
        # 수만 묻는다.
        stacks = ask_int(
            "[화박연] 「정의의 솔개창」 스택 수 (적 명중 시 획득, 0.3초당 최대 1회, 최대"
            f" {self._MAX_STACKS})",
            0, self._MAX_STACKS,
        )
        if not stacks:
            return

        for hit in all_hits[wearer].values():
            hit.add("atk_pct", stacks * self._ATK_PER_STACK[r], label, note="정의의 솔개창 스택")

        if stacks == self._MAX_STACKS:
            for hit in all_hits[wearer].values():
                hit.add("all_dmg_bonus", self._MAX_STACK_DMG_BONUS[r], label, note="최대 중첩")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 6초 지속 시간·0.3초당 발동 제한 — 스택이 몇 개 실려 있는지만 묻고 유지 여부는
    #   유저가 판단한다.
