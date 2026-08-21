from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class Absolution(Weapon):
    """사면 (Absolution) | 한손검 | 5성
    패시브: 죽음의 계약
    - 치명타 피해가 20%/25%/30%/35%/40% 증가한다. 생명의 계약 증가 시 캐릭터가 주는 피해가
      16%/20%/24%/28%/32% 증가한다. 지속 시간: 6초, 최대 중첩수: 3스택
    """

    _CRIT_DMG  = [0.2, 0.25, 0.3, 0.35, 0.4]
    _STACK_DMG = [0.16, 0.2, 0.24, 0.28, 0.32]

    _MAX_STACKS = 3

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.SWORD,
            rarity        = 5,
            tier          = 3,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 사면"

        # 효과 1: 치명타 피해 — 조건 없이 착용자에게만 붙는다.
        for hit in all_hits[wearer].values():
            hit.add("crit_dmg", self._CRIT_DMG[r], label, note="죽음의 계약")

        # 효과 2: 스택. 이 엔진은 「생명의 계약」 수치를 상태로 들고 있지 않다(붉은 달의
        # 형상과 같은 이유) — 무엇이 그 값을 늘리는지는 캐릭터·성유물마다 다르고 로테이션
        # 안에서 몇 번 증가했는지도 유저 몫이다. 그래서 결과 스택 수를 직접 묻는다.
        stacks = ask_int(
            "[사면] 「생명의 계약」 증가로 쌓인 스택 수 (생명의 계약이 늘어날 때마다 1스택,"
            " 6초 지속, 최대 3)",
            0, self._MAX_STACKS,
        )
        if stacks == 0:
            return

        bonus = self._STACK_DMG[r] * stacks
        for hit in all_hits[wearer].values():
            hit.add("all_dmg_bonus", bonus, label, note="죽음의 계약")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 스택 지속 시간 6초 — 각 스택이 개별 6초 창을 갖고 로테이션 중 몇 개가 겹쳐
    #   유지되는지는 히트 단가에 들어갈 항이 없다. 결과 스택 수만 묻는다.
