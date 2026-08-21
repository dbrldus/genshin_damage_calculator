from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.core.party_state import has_hexerei_rite
from gidc.prompt import ask_int


class GestOfTheMightyWolf(Weapon):
    """늑대의 무용담 (Gest of the Mighty Wolf) | 양손검 | 5성
    패시브: 불멸의 기사도
    - 공격 속도가 10% 증가한다.
    - 일반 공격으로 적 명중/원소전투 스킬 발동/강공격 시작 시, 장착 캐릭터가 각각
      「사풍의 시」를 1/2/2스택 획득한다: 주는 피해가 7.5/9.5/11.5/13.5/15.5% 증가한다.
      해당 효과 지속 시간: 4초, 최대 중첩수: 4스택, 0.01초마다 최대 1회 발동된다.
    - 또한 파티가 「마도 · 비밀 의식」 효과 보유 시, 「사풍의 시」 스택마다 장착한 캐릭터의
      치명타 피해가 7.5/9.5/11.5/13.5/15.5% 증가한다
    """

    _DMG_PER_STACK      = [0.075, 0.095, 0.115, 0.135, 0.155]
    _CRIT_DMG_PER_STACK = [0.075, 0.095, 0.115, 0.135, 0.155]

    _MAX_STACKS = 4

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CLAYMORE,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 늑대의 무용담"
        hits  = all_hits[wearer].values()

        # 「사풍의 시」 스택. 트리거가 셋(일반 공격 명중 1스택 / 원소전투 스킬 발동·강공격
        # 시작 각 2스택)이지만 묻는 것은 **실린 스택 수 하나**다. 어느 트리거로 쌓았든
        # 스택당 효과가 같고, 4초 안에 무엇을 몇 번 넣었는지는 로테이션의 문제다.
        stacks = ask_int(
            "[늑대의 무용담] 「사풍의 시」 스택 수 "
            f"(일반 공격 명중 1스택 / 원소전투 스킬 발동·강공격 시작 각 2스택, 최대 {self._MAX_STACKS})",
            0, self._MAX_STACKS,
        )
        if not stacks:
            return

        for hit in hits:
            hit.add("all_dmg_bonus", stacks * self._DMG_PER_STACK[r], label, note="사풍의 시 스택")

        # 「파티가 「마도·비밀 의식」 효과 보유 시」 — 파티 구성만으로 정해지므로 묻지 않고
        # 유도한다(마도 캐릭터 2명 이상). 조건의 주어가 **파티**라 has_hexerei_rite를 읽는다.
        # 착용자 자신의 마도 여부를 보는 hexerei_rite_for가 아니다 — 이 무기는 착용자가
        # 마도 캐릭터일 것을 요구하지 않는다(하늘의 은총 4세트가 「마녀의 과제를 완료한
        # 경우」로 착용자를 못 박은 것과 갈리는 자리다).
        if not has_hexerei_rite(all_hits):
            return

        for hit in hits:
            hit.add("crit_dmg", stacks * self._CRIT_DMG_PER_STACK[r], label,
                    note="사풍의 시 스택 (마도·비밀 의식)")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 공격 속도 +10% — 히트 단가를 바꾸지 않는다. 로테이션에 히트를 몇 개 더 넣느냐의
    #   문제이고, 이 계산기는 히트 목록을 유저가 정한 대로 받는다.
    # · 트리거별 획득량(1/2/2)·지속 시간 4초·0.01초 발동 제한 — 스택이 몇 개 실려 있는지만
    #   묻고 유지 여부는 유저가 판단한다(등방울꽃의 애가·초월의 열쇠와 같다).
