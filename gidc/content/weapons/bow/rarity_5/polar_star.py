from gidc.core.weapon import Weapon
from gidc.core.profile import SkillType
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class PolarStar(Weapon):
    """극지의 별 (Polar Star) | 활 | 5성
    패시브: 백야의 전조자
    - 원소전투 스킬과 원소폭발로 주는 피해가 12/15/18/21/24% 증가한다.
    - 일반 공격, 강공격, 원소전투 스킬 또는 원소폭발이 적에게 명중하면 12초간
      지속되는 「백야의 극성」 효과를 1스택 획득한다. 「백야의 극성」은 1/2/3/4스택
      마다 공격력이 10/12.5/15/17.5/20%·20/25/30/35/40%·30/37.5/45/52.5/60%·
      48/60/72/84/96% 증가한다. 일반 공격, 강공격, 원소전투 스킬 또는 원소폭발이
      생성한 「백야의 극성」은 각각 따로 존재한다.
    """

    _SKILL_BURST_DMG = [0.12, 0.15, 0.18, 0.21, 0.24]
    _ATK_STACK1      = [0.1, 0.125, 0.15, 0.175, 0.2]
    _ATK_STACK2      = [0.2, 0.25, 0.3, 0.35, 0.4]
    _ATK_STACK3      = [0.3, 0.375, 0.45, 0.525, 0.6]
    _ATK_STACK4      = [0.48, 0.6, 0.72, 0.84, 0.96]

    # 스택 수 → 그 스택에서의 배율표. 스택마다 「추가분」이 아니라 보유 스택 수에 대한
    # 누적 총량이 그대로 게임 표기값이다(안개를 가르는 회광·비뢰의 고동과 같은 구조).
    _STACK_TABLE = (_ATK_STACK1, _ATK_STACK2, _ATK_STACK3, _ATK_STACK4)

    _MAX_STACKS = 4

    _DMG_FIELD = {
        SkillType.SKILL: "skill_dmg_bonus",
        SkillType.BURST:  "burst_dmg_bonus",
    }

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.BOW,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 극지의 별"
        hits  = all_hits[wearer].values()

        # 효과 1: 원소전투 스킬·원소폭발 피해 — 조건 없이 착용자에게만 붙는다.
        for hit in hits:
            field = self._DMG_FIELD.get(hit.skill_type)
            if field is not None:
                hit.add(field, self._SKILL_BURST_DMG[r], label)

        # 효과 2 「백야의 극성」. 네 스킬 타입(일반 공격/강공격/원소전투 스킬/원소폭발)이
        # 각각 독립된 스택을 생성한다(「각각 따로 존재한다」) — 즉 실제로 중첩되는 것은
        # 같은 타입 반복 명중이 아니라 **몇 가지 타입이 최근 12초 안에 명중했는가**다.
        # 그래서 묻는 것은 「현재 활성 상태인 타입 수」 하나이고(안개를 가르는 회광과
        # 같은 스택 질문 관용구), 어느 타입이 활성인지는 배율에 영향을 주지 않는다 —
        # 표가 스택 수(=활성 타입 수)에만 종속되기 때문이다.
        stacks = ask_int(
            "[극지의 별] 「백야의 극성」 활성 타입 수 (일반 공격/강공격/원소전투 스킬/"
            f"원소폭발 중 최근 12초 내 명중한 타입 수, 최대 {self._MAX_STACKS})",
            0, self._MAX_STACKS,
        )
        if not stacks:
            return

        bonus = self._STACK_TABLE[stacks - 1][r]
        for hit in hits:
            hit.add("atk_pct", bonus, label, note="백야의 극성")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 스택(타입)별 12초 독립 지속 시간 — 지금 몇 가지 타입이 활성 상태인지만 묻고,
    #   유지 여부는 유저가 판단한다.
