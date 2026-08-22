from gidc.core.weapon import Weapon
from gidc.core.profile import SkillType
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class SurfSUp(Weapon):
    """서핑 타임 (Surf's Up) | 법구 | 5성
    패시브: 물빛 추억
    - HP 최대치가 20/25/30/35/40% 증가한다. 15초마다 1회, 원소전투 스킬 발동 후 14초 동안
      다음 효과가 생성된다: 「불타는 여름」을 4스택 획득한다, 스택 당 일반 공격으로 주는 피해가
      12/15/18/21/24% 증가한다. 지속 시간 동안 1.5초마다 1회: 일반 공격이 적에게 명중 후,
      1스택이 제거된다. 1.5초마다 1회: 적에게 증발 반응 발동 후, 1스택이 증가한다.
      「불타는 여름」 효과 최대 중첩수: 4스택
    """

    _HP_PCT           = [0.2, 0.25, 0.3, 0.35, 0.4]
    _NA_DMG_PER_STACK = [0.12, 0.15, 0.18, 0.21, 0.24]

    _MAX_STACKS = 4

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 서핑 타임"
        hits  = all_hits[wearer].values()

        for hit in hits:
            hit.add("hp_pct", self._HP_PCT[r], label, note="물빛 추억")

        # 「불타는 여름」 스택. 트리거가 둘(일반 공격 명중 시 감소 / 증발 반응 발동 시
        # 증가)이라 순증감이 로테이션에 달렸다 — 늑대의 무용담과 같은 방식으로 **실린
        # 스택 수 하나**만 묻는다. 발동 주기(15초 쿨 · 14초 지속 · 1.5초 판정)는 묻지 않는다.
        stacks = ask_int(
            "[서핑 타임] 「불타는 여름」 스택 수 "
            f"(일반 공격 명중 시 1스택 감소, 증발 반응 발동 시 1스택 증가, 최대 {self._MAX_STACKS})",
            0, self._MAX_STACKS,
        )
        if not stacks:
            return

        bonus = stacks * self._NA_DMG_PER_STACK[r]
        for hit in hits:
            if hit.skill_type is SkillType.NORMAL_ATK:
                hit.add("normal_atk_dmg_bonus", bonus, label, note="불타는 여름 스택")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 15초 쿨타임 · 14초 지속 시간 · 1.5초마다 1회 판정 — 스택이 몇 개 실려 있는지만
    #   묻고, 발동/유지 여부는 유저가 판단한다(늑대의 무용담·초월의 열쇠와 같다).
