from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool
from gidc.prompt import ask_int


class CalamityQueller(Weapon):
    """식재 (Calamity Queller) | 장병기 | 5성
    - 모든 원소의 피해 보너스를 12/15/18/21/24% 획득한다.
    - 원소전투 스킬 발동 시, 20초 동안 지속되는 「원돈」을 획득하고 공격력이 1초마다
      3.2/4/4.8/5.6/6.4% 증가한다. 해당 공격력 증가 효과는 최대 6회 중첩된다.
    - 해당 무기를 장착한 캐릭터가 대기 상태일 때 「원돈」의 공격력 증가 효과는 2배가 된다
    """

    _ALL_DMG_BONUS = [0.12, 0.15, 0.18, 0.21, 0.24]
    _ATK_PCT_TICK  = [0.032, 0.04, 0.048, 0.056, 0.064]

    _MAX_STACKS = 6

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.POLEARM,
            rarity        = 5,
            tier          = 4,
            refinement    = refinement,
            sub_stat_type = StatType.ATK_PCT,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 식재"

        # 효과 1: 모든 원소 피해 보너스 — 조건 없이 착용자에게만 붙는다.
        for hit in all_hits[wearer].values():
            hit.add("all_dmg_bonus", self._ALL_DMG_BONUS[r], label, note="멸각의 계법")

        # 효과 2 「원돈」의 스택 수와 대기 상태 여부만 여기서 받는다. 원소전투 스킬 발동
        # 시점부터 1초마다 쌓여 20초에 6스택으로 가득 차는 진행은 로테이션 몫이라, 실제로
        # 몇 스택이 실려 있는지만 묻는다. 대기 상태(필드 밖) 여부는 스택과 독립이라 따로
        # 묻는다 — 필드 위/대기 상태 모두 스택을 쌓을 수 있고 배율만 갈린다.
        self._stacks    = ask_int(
            "[식재] 「원돈」 스택 수 (원소전투 스킬 발동 시 1초마다 1스택, 20초 지속,"
            f" 최대 {self._MAX_STACKS})",
            0, self._MAX_STACKS,
        )
        self._off_field = False
        if self._stacks:
            self._off_field = ask_bool("[식재] 장착 캐릭터가 대기 상태 (공격력 증가 2배)")

        if not self._stacks:
            return
        multiplier = 2 if self._off_field else 1
        bonus = self._ATK_PCT_TICK[r] * self._stacks * multiplier
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", bonus, label, note="원돈")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 「원돈」 20초 지속과 1초당 1스택 축적 속도 — 몇 스택이 실려 있는지만 묻고
    #   유지·재축적 여부는 유저가 판단한다.
