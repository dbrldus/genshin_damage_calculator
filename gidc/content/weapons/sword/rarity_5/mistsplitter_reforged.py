from gidc.core.weapon import Weapon
from gidc.core.profile import add_all_elemental_dmg_bonus, element_dmg_field
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class MistsplitterReforged(Weapon):
    """안개를 가르는 회광 (Mistsplitter Reforged) | 한손검 | 5성
    패시브: 무절(霧切) 어검
    - 모든 원소의 피해 보너스를 12%/15%/18%/21%/24% 획득하고 「무절(霧切)의 문장」을
      획득한다. 무절의 문장: 1/2/3스택의 무절의 문장 보유 시, 각각
      8%/10%/12%/14%/16%·16%/20%/24%/28%/32%·28%/35%/42%/49%/56%에 해당하는 자신의 원소
      타입의 원소 피해 보너스를 획득한다. 캐릭터가 무절의 문장 1스택을 획득할 수 있는 상황:
      일반 공격으로 원소 피해를 가하면 5초간 지속. 원소폭발을 발동하면 10초간 지속. 이 외에
      캐릭터의 원소 에너지가 100% 미만일 때, 무절의 문장을 1스택 획득한다. 해당 무절의 문장은
      캐릭터의 원소 에너지가 가득 차면 사라진다. 무절의 문장의 각 스택 지속 시간은 따로
      계산된다
    """

    _BASE_ELEM_DMG   = [0.12, 0.15, 0.18, 0.21, 0.24]
    _STACK1_ELEM_DMG = [0.08, 0.1, 0.12, 0.14, 0.16]
    _STACK2_ELEM_DMG = [0.16, 0.2, 0.24, 0.28, 0.32]
    _STACK3_ELEM_DMG = [0.28, 0.35, 0.42, 0.49, 0.56]

    # 스택 수 → 그 스택에서의 배율표. 스택마다 「추가분」이 아니라 보유 스택 수에 대한
    # 누적 총량이 그대로 game 표기값이다(예: 정련1에서 2스택은 1스택×2가 아니라 16%).
    _STACK_TABLE = (_STACK1_ELEM_DMG, _STACK2_ELEM_DMG, _STACK3_ELEM_DMG)

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
        label = "무기: 안개를 가르는 회광"
        hits  = all_hits[wearer].values()

        # 효과 1: 모든 원소 피해 보너스 — 조건 없이 착용자에게만 붙는다.
        for hit in hits:
            add_all_elemental_dmg_bonus(hit, self._BASE_ELEM_DMG[r], label)

        # 효과 2 「무절의 문장」. 획득 경로가 셋(일반 공격 원소 피해/원소폭발/원소 에너지
        # 100% 미만)이고 스택마다 독립 지속 시간을 갖지만, 묻는 것은 **현재 보유 스택 수**
        # 하나다 — 산왕의 엄니와 같은 이유로, 어느 경로로 몇 스택이 쌓였는지가 아니라
        # 지금 몇 스택이 살아 있는지만 히트 단가에 들어간다.
        stacks = ask_int(
            "[안개를 가르는 회광] 「무절의 문장」 스택 수 (일반 공격 원소 피해 명중/원소폭발/"
            f"원소 에너지 100% 미만 시 1스택, 최대 {self._MAX_STACKS})",
            0, self._MAX_STACKS,
        )
        if not stacks:
            return

        # 자신의 원소 타입 피해 보너스에만 붙는다. 이 무기는 다른 원소 캐릭터가 껴도
        # 성립하므로(원소 에너지 조건은 원소와 무관) 파티 원소로 게이팅하지 않는다.
        field = element_dmg_field(wearer.element)
        if field is None:      # 물리 등 원소가 없는 캐릭터는 대상 필드가 없다
            return
        bonus = self._STACK_TABLE[stacks - 1][r]
        for hit in hits:
            hit.add(field, bonus, label, note="무절의 문장")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 스택별 독립 지속 시간(일반 공격 5초/원소폭발 10초)과 원소 에너지 100% 미만 조건 —
    #   이 엔진은 원소 에너지를 모델링하지 않는다. 현재 살아 있는 스택 수만 묻는다.
