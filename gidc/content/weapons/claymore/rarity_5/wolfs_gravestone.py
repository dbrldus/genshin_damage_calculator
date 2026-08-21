from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class WolfsGravestone(Weapon):
    """늑대의 말로 (Wolf's Gravestone) | 양손검 | 5성
    패시브: 늑대 같은 사냥꾼
    - 공격력+20/25/30/35/40%. HP가 30% 미만인 적을 명중 시 모든 파티원의 공격력이
      40/50/60/70/80% 증가한다. 지속 시간: 12초. 해당 효과는 30초마다 1번 발동한다.
    """

    _ATK_PCT       = [0.2, 0.25, 0.3, 0.35, 0.4]
    _PARTY_ATK_PCT = [0.4, 0.5, 0.6, 0.7, 0.8]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CLAYMORE,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.ATK_PCT,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 늑대의 말로"

        # 효과 1: 상시 공격력% (착용자) — 조건 없이 항상 붙는다.
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", self._ATK_PCT[r], label)

        # 효과 2: HP 30% 미만인 적 명중 시 파티 전원 공격력% (12초 지속, 30초 재발동 제한).
        # 발동 여부는 적 체력과 로테이션 타이밍이 정하므로 묻는다 — 파티 구성으로 유도되지
        # 않는다. 파티 전원(장착자 포함) + 비중첩 — 동명의 무기 두 자루가 각자 발동해도
        # 공격력 보너스는 겹치지 않는다.
        if not ask_bool("[늑대의 말로] 「늑대 같은 사냥꾼」 발동 중 여부 (HP 30% 미만 적 명중, 12초 지속)"):
            return
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.apply_unique_buff(label, "atk_pct", self._PARTY_ATK_PCT[r])

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 재발동 제한 30초 — 12초 지속 동안 발동 중인지만 묻고, 유지 여부는 유저가 판단한다.
