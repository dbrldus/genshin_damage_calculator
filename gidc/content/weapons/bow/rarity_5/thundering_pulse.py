from gidc.core.weapon import Weapon
from gidc.core.profile import SkillType
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class ThunderingPulse(Weapon):
    """비뢰의 고동 (Thundering Pulse) | 활 | 5성
    패시브: 비뢰 어궁
    - 공격력이 20/25/30/35/40% 증가하고, 「비뢰의 문장」의 위세를 획득한다. 비뢰의
      문장: 1/2/3스택의 비뢰의 문장 보유 시, 일반 공격으로 주는 피해가 각각
      12/15/18/21/24%·24/30/36/42/48%·40/50/60/70/80% 증가한다. 캐릭터가 비뢰의 문장
      1스택을 획득할 수 있는 상황: 일반 공격으로 피해를 가하면 5초간 지속. 원소전투
      스킬을 발동하면 10초간 지속. 이 외에 캐릭터의 원소 에너지가 100% 미만이면
      비뢰의 문장을 1스택 획득한다. 해당 비뢰의 문장은 캐릭터의 원소 에너지가 가득
      차면 사라지며, 비뢰의 문장의 각 스택 지속 시간은 따로 계산된다
    """

    _ATK_PCT       = [0.2, 0.25, 0.3, 0.35, 0.4]
    _NA_DMG_STACK1 = [0.12, 0.15, 0.18, 0.21, 0.24]
    _NA_DMG_STACK2 = [0.24, 0.3, 0.36, 0.42, 0.48]
    _NA_DMG_STACK3 = [0.4, 0.5, 0.6, 0.7, 0.8]

    # 스택 수 → 그 스택에서의 배율표. 스택마다 「추가분」이 아니라 보유 스택 수에 대한
    # 누적 총량이 그대로 게임 표기값이다(예: 정련1에서 2스택은 1스택×2가 아니라 24%),
    # 안개를 가르는 회광과 같은 구조다.
    _STACK_TABLE = (_NA_DMG_STACK1, _NA_DMG_STACK2, _NA_DMG_STACK3)

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
        label = "무기: 비뢰의 고동"
        hits  = all_hits[wearer].values()

        # 효과 1: 상시 공격력% — 조건 없이 착용자에게만 붙는다.
        for hit in hits:
            hit.add("atk_pct", self._ATK_PCT[r], label)

        # 효과 2 「비뢰의 문장」. 획득 경로가 셋(일반 공격 명중/원소전투 스킬 발동/원소
        # 에너지 100% 미만)이고 스택마다 독립 지속 시간을 갖지만, 묻는 것은 **현재 보유
        # 스택 수** 하나다 — 안개를 가르는 회광·산왕의 엄니와 같은 이유로, 어느 경로로
        # 몇 스택이 쌓였는지가 아니라 지금 몇 스택이 살아 있는지만 히트 단가에 들어간다.
        stacks = ask_int(
            "[비뢰의 고동] 「비뢰의 문장」 스택 수 (일반 공격 명중/원소전투 스킬 발동/"
            f"원소 에너지 100% 미만 시 1스택, 최대 {self._MAX_STACKS})",
            0, self._MAX_STACKS,
        )
        if not stacks:
            return

        bonus = self._STACK_TABLE[stacks - 1][r]
        for hit in hits:
            if hit.skill_type is not SkillType.NORMAL_ATK:
                continue
            hit.add("normal_atk_dmg_bonus", bonus, label, note="비뢰의 문장")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 스택별 독립 지속 시간(일반 공격 5초/원소전투 스킬 10초)과 원소 에너지 100%
    #   미만 조건 — 이 엔진은 원소 에너지를 모델링하지 않는다. 현재 살아 있는 스택
    #   수만 묻는다.
