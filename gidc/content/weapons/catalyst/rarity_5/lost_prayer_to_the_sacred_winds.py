from gidc.core.weapon import Weapon
from gidc.core.profile import add_all_elemental_dmg_bonus
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class LostPrayerToTheSacredWinds(Weapon):
    """사풍 원서 (Lost Prayer to the Sacred Winds) | 법구 | 5성
    패시브: 끝없는 은혜
    - 이동속도+10%. 필드에 있을 때 4초마다 원소 피해 보너스를 8/10/12/14/16% 획득한다.
      최대 중첩수: 4회. 캐릭터가 전투 불능이 되거나 교체될 때까지 지속된다
    """

    _DMG_PER_STACK = [0.08, 0.1, 0.12, 0.14, 0.16]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    _MAX_STACKS = 4

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 사풍 원서"

        # 「끝없는 은혜」 스택. 4초마다 자동으로 쌓이고 캐릭터가 전투 불능이 되거나
        # 교체될 때까지 유지되므로, 실제 로테이션에서 몇 초째인지가 스택 수를 정한다 —
        # 결과 스택 수만 묻는다.
        stacks = ask_int(
            "[사풍 원서] 「끝없는 은혜」 스택 수 (필드 유지 4초당 1스택, 최대 4)",
            0, self._MAX_STACKS,
        )
        if not stacks:
            return

        bonus = stacks * self._DMG_PER_STACK[r]
        for hit in all_hits[wearer].values():
            add_all_elemental_dmg_bonus(hit, bonus, label)

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 이동속도 +10% — 이 계산기는 이동속도를 다루지 않는다. 피해 항이 아니다.
    # · 전투 불능/교체 시 초기화 — 스택이 몇 개 실려 있는지만 묻고 유지 여부는
    #   유저가 판단한다.
