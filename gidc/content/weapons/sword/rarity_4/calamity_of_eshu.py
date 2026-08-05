from gidc.core.weapon import Weapon
from gidc.core.profile import SkillType
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class CalamityOfEshu(Weapon):
    """에슈의 재앙 (Calamity of Eshu) | 한손검 | 4성
    패시브: 자욱한 경계
    - 캐릭터가 보호막의 보호를 받고 있을 시:
      일반 공격과 강공격의 피해 +20/25/30/35/40%,
      일반 공격과 강공격의 치명타 확률 +8/10/12/14/16%

    무기 효과는 착용자에게만 적용된다.
    """

    _NA_CA_DMG  = [0.20, 0.25, 0.30, 0.35, 0.40]
    _NA_CA_CRIT = [0.08, 0.10, 0.12, 0.14, 0.16]

    # 스킬 타입 → 누산할 피해 보너스 필드
    _DMG_FIELD = {
        SkillType.NORMAL_ATK:  "normal_atk_dmg_bonus",
        SkillType.CHARGED_ATK: "charged_atk_dmg_bonus",
    }

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.SWORD,
            rarity        = 4,
            tier          = 3,
            refinement    = refinement,
            sub_stat_type = StatType.ATK_PCT,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        if not ask_bool("[에슈의 재앙] 보호막의 보호를 받는 중인지 여부"):
            return

        r     = self.refinement - 1
        label = "무기: 에슈의 재앙"

        # 피해 보너스는 타입별 필드라 그 자체로 범위가 한정되지만, 치명타 확률은
        # 히트 전역 필드라 일반/강공격 히트만 골라서 넣어야 한다.
        for hit in all_hits[wearer].values():
            field = self._DMG_FIELD.get(hit.skill_type)
            if field is None:
                continue
            hit.add(field,       self._NA_CA_DMG[r],  label, note="자욱한 경계")
            hit.add("crit_rate", self._NA_CA_CRIT[r], label, note="자욱한 경계")
