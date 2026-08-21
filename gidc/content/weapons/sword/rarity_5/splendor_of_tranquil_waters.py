from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class SplendorOfTranquilWaters(Weapon):
    """고요히 샘솟는 빛 (Splendor of Tranquil Waters) | 한손검 | 5성
    패시브: 호숫빛의 여명과 황혼
    - 장착 캐릭터의 현재 HP가 증가 또는 감소 시, 원소전투 스킬로 주는 피해가
      8%/10%/12%/14%/16% 증가한다. 지속 시간: 6초. 최대 중첩수: 3회. 0.2초마다 최대 1회
      발동된다. 파티 내 다른 캐릭터의 현재 HP가 증가 또는 감소 시, 장착 캐릭터 HP 최대치가
      14%/17.5%/21%/24.5%/28% 증가한다. 지속 시간: 6초. 최대 중첩수: 2회. 0.2초마다 최대 1회
      발동된다. 상술한 효과는 장착 캐릭터가 대기 시에도 발동할 수 있다
    """

    _SELF_SKILL_DMG_PER_STACK = [0.08, 0.1, 0.12, 0.14, 0.16]
    _OTHER_HP_PCT_PER_STACK   = [0.14, 0.175, 0.21, 0.245, 0.28]

    _SELF_MAX_STACKS  = 3
    _OTHER_MAX_STACKS = 2

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.SWORD,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 고요히 샘솟는 빛"
        hits  = all_hits[wearer].values()

        # 두 효과 모두 「현재 HP 증가 또는 감소」가 트리거다 — 이 엔진은 HP 변동 이력을
        # 들고 있지 않고(회복량·피격량은 캐릭터마다 다른 값이라 파티 구성으로 유도되지
        # 않는다), 스택마다 독립 6초 창인 것도 로테이션 몫이다. 그래서 결과 스택 수만 묻는다
        # (산왕의 엄니와 같은 관용구).
        self_stacks = ask_int(
            "[고요히 샘솟는 빛] 장착 캐릭터 HP 변동으로 쌓인 스택 수 "
            f"(HP 증가/감소 시 1스택, 6초 지속, 최대 {self._SELF_MAX_STACKS})",
            0, self._SELF_MAX_STACKS,
        )
        if self_stacks:
            bonus = self._SELF_SKILL_DMG_PER_STACK[r] * self_stacks
            for hit in hits:
                hit.add("skill_dmg_bonus", bonus, label, note="호숫빛의 여명")

        other_stacks = ask_int(
            "[고요히 샘솟는 빛] 파티 내 다른 캐릭터 HP 변동으로 쌓인 스택 수 "
            f"(HP 증가/감소 시 1스택, 6초 지속, 최대 {self._OTHER_MAX_STACKS})",
            0, self._OTHER_MAX_STACKS,
        )
        if other_stacks:
            bonus = self._OTHER_HP_PCT_PER_STACK[r] * other_stacks
            for hit in hits:
                hit.add("hp_pct", bonus, label, note="호숫빛의 황혼")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 두 효과 모두 6초 지속 시간과 0.2초 재발동 제한, 스택별 독립 만료 — 스택이 몇 개
    #   실려 있는지만 묻고 유지 여부는 유저가 판단한다.
    # · 「장착 캐릭터가 대기 시에도 발동할 수 있다」 — 필드 등장 여부를 묻지 않는 근거일
    #   뿐, 켜졌을 때의 값을 바꾸지 않는다.
