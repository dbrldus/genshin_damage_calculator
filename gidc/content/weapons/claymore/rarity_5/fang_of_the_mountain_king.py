from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class FangOfTheMountainKing(Weapon):
    """산왕의 엄니 (Fang of the Mountain King) | 양손검 | 5성
    패시브: 터키석의 사냥
    - 원소전투 스킬이 적에게 명중 후, 「나무살이 축복」을 1스택 획득한다.
      해당 효과는 0.5초마다 최대 1회 발동한다.
    - 주변에 있는 파티 내 캐릭터가 연소 또는 발화 반응 발동 후, 장착 캐릭터는
      「나무살이 축복」을 3스택 획득한다. 해당 효과는 2초마다 최대 1회 발동하고,
      파티 내 캐릭터가 대기 상태일 때도 발동한다.
    - 나무살이 축복: 원소전투 스킬과 원소폭발 피해가 10/12.5/15/17.5/20% 증가한다.
      지속 시간: 6초, 최대 중첩수: 6스택. 스택마다 지속 시간은 독립적으로 계산된다
    """

    _SKILL_BURST_DMG_PER_STACK = [0.1, 0.125, 0.15, 0.175, 0.2]

    _MAX_STACKS = 6

    # 한 스택이 두 필드를 함께 올린다 — 히트는 자기 종류의 필드만 읽으므로(profile.
    # _skill_dmg_bonus) 착용자 히트 전부에 둘 다 얹어도 평타·낙하에는 실리지 않는다.
    _DMG_FIELDS = ("skill_dmg_bonus", "burst_dmg_bonus")

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CLAYMORE,
            rarity        = 5,
            tier          = 4,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 산왕의 엄니"

        # 트리거가 둘(착용자 E 명중 1스택 / 파티원의 연소·발화 3스택)이지만 묻는 것은
        # **실린 스택 수 하나**다. 어느 쪽으로 쌓았든 스택당 효과가 같고, 6초 안에 무엇이
        # 몇 번 터졌는지는 로테이션의 문제다.
        #
        # 파티 구성으로 게이팅하지 않는다. 연소·발화는 불과 풀이 둘 다 적에게 붙어야
        # 성립하고 한쪽은 적이 원래 두르고 있을 수 있다. 확산으로 옮겨 붙은 불도 연소를
        # 일으키므로 파티 원소만으로는 막을 수 없다(등방울꽃의 애가와 같은 판단).
        stacks = ask_int(
            "[산왕의 엄니] 「나무살이 축복」 스택 수 "
            f"(원소전투 스킬 명중 1스택 / 파티원의 연소·발화 반응 3스택, 최대 {self._MAX_STACKS})",
            0, self._MAX_STACKS,
        )
        if not stacks:
            return

        bonus = stacks * self._SKILL_BURST_DMG_PER_STACK[r]
        for hit in all_hits[wearer].values():
            for field in self._DMG_FIELDS:
                hit.add(field, bonus, label, note="나무살이 축복 스택")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 트리거별 획득량(1스택/3스택)과 발동 제한(0.5초·2초), 지속 시간 6초와 스택별 독립
    #   만료 — 스택이 몇 개 실려 있는지만 묻고 유지 여부는 유저가 판단한다.
    # · 「파티 내 캐릭터가 대기 상태일 때도 발동한다」 — 필드 등장 여부를 묻지 않는 근거일
    #   뿐, 켜졌을 때의 값을 바꾸지 않는다.
