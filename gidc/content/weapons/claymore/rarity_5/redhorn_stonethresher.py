from gidc.core.weapon import Weapon
from gidc.core.profile import SkillType
from gidc.enums import WeaponType
from gidc.enums import StatType


class RedhornStonethresher(Weapon):
    """쇄석의 붉은 뿔 (Redhorn Stonethresher) | 양손검 | 5성
    패시브: 오토기 대왕의 동화
    - 방어력이 28/35/42/49/56% 증가한다.
    - 일반 공격과 강공격의 피해량이 방어력의 40/50/60/70/80%만큼 증가한다.
    """

    _DEF_PCT         = [0.28, 0.35, 0.42, 0.49, 0.56]
    _NA_CA_DEF_SCALE = [0.4, 0.5, 0.6, 0.7, 0.8]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CLAYMORE,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 쇄석의 붉은 뿔"

        # 효과 1: 방어력% (착용자)
        for hit in all_hits[wearer].values():
            hit.add("def_pct", self._DEF_PCT[r], label)

    # 효과 2: 일반/강공격 피해량이 착용자 최종 방어력의 X%만큼 증가 — 방식 B(최종 스탯
    # 기반)이므로 효과 1을 포함한 모든 코어 DEF 기여가 끝난 뒤인 Phase 5에서
    # current_def()를 읽는다. 착용자 자신의 일반/강공격 히트에만 붙으므로 add로 제출한다
    # (파티·제3자로 뿌리는 효과가 아니라 apply_unique_buff 대상이 아니다).
    def apply_passive_dependent(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 쇄석의 붉은 뿔"
        wearer_hits = all_hits[wearer]
        source_hit  = next(iter(wearer_hits.values()))

        for hit in wearer_hits.values():
            if hit.skill_type not in (SkillType.NORMAL_ATK, SkillType.CHARGED_ATK):
                continue
            hit.add("flat_dmg_bonus", lambda: source_hit.current_def() * self._NA_CA_DEF_SCALE[r], label)

    # ── 의도적 미구현 ─────────────────────────────────────────────────────────
    # (없음 — 문구 전체가 히트 단가에 반영된다)
