from gidc.core.weapon import Weapon
from gidc.core.profile import SkillType
from gidc.enums import WeaponType
from gidc.enums import StatType


class EverlastingMoonglow(Weapon):
    """불멸의 달빛 (Everlasting Moonglow) | 법구 | 5성
    패시브: 백야의 밝은 달
    - 치유 보너스가 10/12.5/15/17.5/20% 증가하고, 일반 공격으로 주는 피해가 해당 장비를
      장착한 캐릭터 HP 최대치의 1/1.5/2/2.5/3%만큼 증가한다. 원소폭발 발동 후 12초 내에
      일반 공격으로 적을 명중하면 원소 에너지를 0.6pt 회복하고, 해당 방식으로 0.1초마다
      원소 에너지를 최대 1회 회복할 수 있다
    """

    _HEALING_BONUS = [0.1, 0.125, 0.15, 0.175, 0.2]
    _NA_HP_SCALE   = [0.01, 0.015, 0.02, 0.025, 0.03]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.HP_PCT,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 불멸의 달빛"

        # 효과 1: 치유 보너스 — 조건 없이 착용자에게만 붙는다.
        for hit in all_hits[wearer].values():
            hit.add("healing_bonus", self._HEALING_BONUS[r], label, note="백야의 밝은 달")

    # 효과 2: 일반 공격 피해가 착용자 최종 HP의 X%만큼 증가 — 방식 B(최종 스탯 기반)이므로
    # 효과 1을 포함한 모든 코어 HP 기여가 끝난 뒤인 Phase 5에서 convertible_hp()를 읽는다.
    # 쇄석의 붉은 뿔(방어력→일반/강공격 flat_dmg_bonus)과 같은 규약이다 — 여기는 일반
    # 공격에만 붙으므로 강공격은 필터에서 뺀다.
    def apply_passive_dependent(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 불멸의 달빛"
        wearer_hits = all_hits[wearer]
        source_hit  = next(iter(wearer_hits.values()))

        for hit in wearer_hits.values():
            if hit.skill_type is not SkillType.NORMAL_ATK:
                continue
            hit.add("flat_dmg_bonus", lambda: source_hit.convertible_hp() * self._NA_HP_SCALE[r], label,
                     note="백야의 밝은 달")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 원소폭발 발동 후 12초 내 일반 공격 명중 시 원소 에너지 0.6pt 회복(0.1초당 최대
    #   1회) — 로테이션 빈도를 정하는 값이지 히트 단가에 들어갈 항이 없다.
