from gidc.core.weapon import Weapon
from gidc.core.profile import SkillType
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class AmosBow(Weapon):
    """아모스의 활 (Amos' Bow) | 활 | 5성
    패시브: 잊지 않은 포부
    - 일반 공격과 강공격 피해 +12/15/18/21/24%
    - 일반 공격과 강공격 화살이 발사된 후 0.1초가 지날 때마다 피해가
      8/10/12/14/16%씩 증가한다. 최대 중첩수: 5회
    """

    _NA_CA_DMG_BASE     = [0.12, 0.15, 0.18, 0.21, 0.24]
    _NA_CA_DMG_PER_TICK = [0.08, 0.10, 0.12, 0.14, 0.16]

    _MAX_STACKS = 5

    # 스킬 타입 → 누산할 피해 보너스 필드
    _DMG_FIELD = {
        SkillType.NORMAL_ATK:  "normal_atk_dmg_bonus",
        SkillType.CHARGED_ATK: "charged_atk_dmg_bonus",
    }

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.BOW,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.ATK_PCT,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 아모스의 활"

        # 0.1초 간격 5틱은 화살 비행 거리(로테이션·사거리)가 정하므로 스택 수 자체를
        # 묻는다 — 산왕의 엄니와 같은 판단. 상시분(_NA_CA_DMG_BASE)은 조건 없이 항상
        # 붙고, 틱분(_NA_CA_DMG_PER_TICK)은 스택 수만큼 곱해 더한다.
        stacks = ask_int(
            "[아모스의 활] 화살 비행 틱 수 (발사 후 0.1초마다 1스택, 최대 5)",
            0, self._MAX_STACKS,
        )
        bonus = self._NA_CA_DMG_BASE[r] + stacks * self._NA_CA_DMG_PER_TICK[r]

        for hit in all_hits[wearer].values():
            field = self._DMG_FIELD.get(hit.skill_type)
            if field is None:
                continue
            hit.add(field, bonus, label, note="잊지 않은 포부")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 0.1초 발동 간격 자체 — 스택 수만 묻고, 몇 초 지났는지는 유저가 환산해 넣는다.
