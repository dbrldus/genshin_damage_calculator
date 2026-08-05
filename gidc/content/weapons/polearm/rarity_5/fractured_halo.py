from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class FracturedHalo(Weapon):
    """파멸의 빛고리 (Fractured Halo) | 장병기 | 5성 | 이네파 전용 무기
    패시브: 서리옥 왕관
    - 원소전투 스킬 또는 원소폭발 발동 후 20초 동안 공격력 +24/30/36/42/48% (착용자)
    - 위 지속 시간 동안 장착 캐릭터가 보호막을 생성하면, 그 후 20초 동안 「전류 칙령」 획득:
      주변에 있는 파티 내 모든 캐릭터가 발동한 달 감전 반응으로 주는 피해 +40/50/60/70/80%
    """

    _ATK_PCT              = [0.24, 0.30, 0.36, 0.42, 0.48]
    _LUNAR_CHARGED_BONUS  = [0.40, 0.50, 0.60, 0.70, 0.80]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.POLEARM,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r = self.refinement - 1

        # 효과 1: E/Q 발동 후 공격력 증가 — 착용자에게만 적용된다.
        if not ask_bool("[파멸의 빛고리] 원소전투 스킬 또는 원소폭발 발동 여부"):
            return

        for hit in all_hits[wearer].values():
            hit.add("atk_pct", self._ATK_PCT[r], "무기: 파멸의 빛고리", note="서리옥 왕관")

        # 효과 2: 「전류 칙령」 — 위 지속 시간 동안 보호막을 생성해야 발동하므로,
        # 효과 1이 켜져 있을 때만 묻는다. 파티 전원의 달 감전 반응 피해를 올린다.
        # 고정값이라 스탯을 읽지 않는다 → Phase 3에서 끝난다.
        # 동명의 무기 효과는 중첩되지 않으므로 비중첩으로 제출한다(무기 이름이 판정 키).
        if not ask_bool("[파멸의 빛고리] 지속 시간 동안 보호막 생성 여부 (전류 칙령)"):
            return

        bonus = self._LUNAR_CHARGED_BONUS[r]
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.apply_unique_buff("무기: 파멸의 빛고리", "lunar_charged_bonus", bonus)
