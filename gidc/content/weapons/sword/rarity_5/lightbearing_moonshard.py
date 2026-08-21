from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class LightbearingMoonshard(Weapon):
    """신월의 달빛 (Lightbearing Moonshard) | 한손검 | 5성
    패시브: 낭간의 유물
    - 방어력이 20%/25%/30%/35%/40% 증가한다. 장착 캐릭터가 원소전투 스킬 발동 후 5초 동안
      달 결정 반응 피해가 64%/80%/96%/112%/128% 증가한다.
    """

    _DEF_PCT               = [0.2, 0.25, 0.3, 0.35, 0.4]
    _LUNAR_CRYSTALLIZE_DMG = [0.64, 0.8, 0.96, 1.12, 1.28]

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
        label = "무기: 신월의 달빛"
        hits  = all_hits[wearer].values()

        # 효과 1: 방어력 — 조건 없이 착용자에게만 붙는다.
        for hit in hits:
            hit.add("def_pct", self._DEF_PCT[r], label, note="낭간의 유물")

        # 효과 2: 원소전투 스킬 발동 후 5초 동안 달 결정 반응 피해 증가. 스킬 명중 여부와
        # 그 5초 창 안에 달 결정 반응이 실제로 발생하는지는 로테이션이 정하므로 묻는다.
        # 「장착 캐릭터가」로 주어가 한정되어 파티 전원이 아니라 착용자 히트에만 붙인다.
        if not ask_bool("[신월의 달빛] 원소전투 스킬 발동 후 5초 이내"):
            return

        for hit in hits:
            hit.add("lunar_crystallize_bonus", self._LUNAR_CRYSTALLIZE_DMG[r], label,
                     note="낭간의 유물")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 「원소전투 스킬 발동 후 5초」라는 지속 시간 창 — 스택/지속 여부는 위 질문 하나로
    #   대신 묻는다(다른 무기들과 동일하게 지속 시간은 히트 단가에 들어갈 자리가 없다).
