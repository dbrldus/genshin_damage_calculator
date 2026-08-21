from gidc.core.weapon import Weapon
from gidc.core.profile import add_all_elemental_dmg_bonus
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class HaranGeppakuFutsu(Weapon):
    """하란 월백의 후츠 (Haran Geppaku Futsu) | 한손검 | 5성
    패시브: 흐르는 칼날
    - 모든 원소 피해 보너스를 12%/15%/18%/21%/24% 획득한다. 근처 파티 내 다른 캐릭터가
      원소전투 스킬 발동 시, 해당 무기를 장착한 캐릭터가 「하스이」 효과를 1스택 획득한다.
      최대 중첩수: 2스택, 0.3초마다 최대 1회 발동한다. 해당 무기를 장착한 캐릭터가 원소전투
      스킬 발동 시, 쌓여있는 「하스이」스택이 있다면 스택을 소모하여 「하란」을 획득한다.
      소모한 스택마다 일반 공격 피해가 20%/25%/30%/35%/40% 증가한다. 지속 시간: 8초
    """

    _ELEM_DMG             = [0.12, 0.15, 0.18, 0.21, 0.24]
    _NORMAL_DMG_PER_STACK = [0.2, 0.25, 0.3, 0.35, 0.4]

    _MAX_STACKS = 2

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.SWORD,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 하란 월백의 후츠"
        hits  = all_hits[wearer].values()

        # 효과 1: 모든 원소 피해 보너스 — 조건 없이 착용자에게만 붙는다.
        for hit in hits:
            add_all_elemental_dmg_bonus(hit, self._ELEM_DMG[r], label)

        # 효과 2·3 「하스이」→「하란」. 「하스이」 자체는 스택만 쌓일 뿐 피해에 직접
        # 들어가지 않고, 착용자가 스킬을 쓰면 그 스택이 통째로 「하란」으로 소모되는
        # 일방 파이프라인이다. 그래서 중간 상태(하스이 스택)를 따로 묻지 않고 결과인
        # 「소모된 스택 수」 하나로 받는다 — 다른 파티원의 스킬 명중 횟수·0.3초 재발동
        # 제한·착용자 자신의 스킬 사용 시점은 전부 이 값으로 흡수된다.
        stacks = ask_int(
            "[하란 월백의 후츠] 원소전투 스킬 발동 시 소모한 「하스이」 스택 수 "
            f"(다른 파티원 스킬 명중 시 1스택, 최대 {self._MAX_STACKS})",
            0, self._MAX_STACKS,
        )
        if not stacks:
            return

        bonus = self._NORMAL_DMG_PER_STACK[r] * stacks
        for hit in hits:
            hit.add("normal_atk_dmg_bonus", bonus, label, note="하란")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 「하스이」 최대 2스택·0.3초 재발동 제한과 「하란」 8초 지속 — 소모된 스택 수만
    #   묻고 유지 여부는 유저가 판단한다.
