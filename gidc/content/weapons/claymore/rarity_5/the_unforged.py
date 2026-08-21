from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool, ask_int


class TheUnforged(Weapon):
    """무공의 검 (The Unforged) | 양손검 | 5성
    패시브: 금빛의 옥 · 제군의 길
    - 보호막 강화 효과가 20/25/30/35/40% 증가한다.
    - 공격 명중 후 공격력이 4/5/6/7/8% 증가한다. 지속 시간: 8초. 최대 중첩수: 5회. 해당 효과는
      0.3초마다 1번 발동한다. 또한 보호막 존재 시 해당 효과의 공격력 증가 효과가 100% 증가한다.
    """

    _ATK_PER_STACK = [0.04, 0.05, 0.06, 0.07, 0.08]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CLAYMORE,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.ATK_PCT,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 무공의 검"

        # 「금빛의 옥」 스택. 트리거(공격 명중, 0.3초당 최대 1회)는 하나뿐이라 스택 수만
        # 묻는다 — 늑대의 무용담과 같은 꼴.
        stacks = ask_int(
            "[무공의 검] 「금빛의 옥」 스택 수 (공격 명중 시 획득, 0.3초당 최대 1회, 최대 5)",
            0, 5,
        )
        if not stacks:
            return

        # 보호막 존재 시 스택당 공격력 증가 효과가 100% 증가(2배) — 파티 구성이 아니라
        # 로테이션이 정하는 상태라 묻는다.
        multiplier = 2.0 if ask_bool("[무공의 검] 보호막 존재 여부 (「금빛의 옥」 공격력 증가 2배)") else 1.0

        for hit in all_hits[wearer].values():
            hit.add("atk_pct", stacks * self._ATK_PER_STACK[r] * multiplier, label, note="금빛의 옥 스택")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 보호막 강화 효과 +20/25/30/35/40% — 이 계산기는 보호막 흡수량을 다루지 않는다.
    # · 지속 시간 8초·0.3초당 발동 제한 — 스택이 몇 개 실려 있는지만 묻고 유지 여부는
    #   유저가 판단한다.
