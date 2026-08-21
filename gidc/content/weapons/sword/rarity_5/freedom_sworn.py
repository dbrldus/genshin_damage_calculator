from gidc.core.weapon import Weapon
from gidc.core.profile import SkillType, skill_dmg_field
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class FreedomSworn(Weapon):
    """오래된 자유의 서약 (Freedom Sworn) | 한손검 | 5성
    패시브: 항쟁의 실천곡
    - 바람 속을 유랑하는 「천년의 대악장」의 일부분으로 주는 피해가 10%/12.5%/15%/17.5%/20%
      증가한다. 원소 반응을 발동할 시 캐릭터는 투쟁의 부적을 1장 획득하며, 0.5초마다 한 번씩
      발동하고 캐릭터가 대기 상태일 때도 발동할 수 있다. 투쟁의 부적 2장 보유 시 부적을 모두
      사용하면 파티 내 모든 캐릭터가 12초동안 「천년의 대악장·투쟁의 노래」 효과를 획득한다.
      이때 일반 공격, 강공격, 낙하 공격 피해는 16%/20%/24%/28%/32% 증가하고, 공격력은
      20%/25%/30%/35%/40% 증가한다. 발동 후 20초 동안은 투쟁의 부적을 획득할 수 없으며,
      「천년의 대악장」 발동 효과는 동일 수치의 다른 효과들과 중첩되지 않는다
    """

    _BASE_DMG      = [0.1, 0.125, 0.15, 0.175, 0.2]
    _PARTY_HIT_DMG = [0.16, 0.2, 0.24, 0.28, 0.32]
    _PARTY_ATK_PCT = [0.2, 0.25, 0.3, 0.35, 0.4]

    _SONG_SKILL_TYPES = (SkillType.NORMAL_ATK, SkillType.CHARGED_ATK, SkillType.PLUNGING)

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.SWORD,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.ELEMENTAL_MASTERY,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 오래된 자유의 서약"

        # 효과 1: 「천년의 대악장」 조각으로 주는 피해 — 조건 없이 착용자에게만 붙는다.
        for hit in all_hits[wearer].values():
            hit.add("all_dmg_bonus", self._BASE_DMG[r], label, note="항쟁의 실천곡")

        # 효과 2 「천년의 대악장·투쟁의 노래」. 투쟁의 부적 2장 소모가 트리거인데, 반응
        # 발동 여부(0.5초 1회)와 20초 재발동 제한은 로테이션 몫이라 활성 여부만 묻는다.
        # 대기 상태에서도 부적을 얻을 수 있으므로 필드 등장 여부는 따로 묻지 않는다.
        if not ask_bool(
            "[오래된 자유의 서약] 「천년의 대악장·투쟁의 노래」 효과 여부"
        ):
            return

        # 파티 전원(착용자 포함) 대상이라 동명 무기 간 비중첩 규약을 지키려면
        # apply_unique_buff로 제출한다. 「동일 수치의 다른 효과들과 중첩되지 않는다」는
        # 원문도 같은 방향이다.
        hit_bonus = self._PARTY_HIT_DMG[r]
        atk_bonus = self._PARTY_ATK_PCT[r]
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.apply_unique_buff(label, "atk_pct", atk_bonus)
                if hit.skill_type in self._SONG_SKILL_TYPES:
                    field = skill_dmg_field(hit.skill_type)
                    hit.apply_unique_buff(label, field, hit_bonus)

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 투쟁의 부적 획득(반응 발동 시 1장, 0.5초 1회 제한)과 2장 소모 트리거, 발동 후
    #   20초 부적 획득 정지 — 실제로 「투쟁의 노래」가 켜져 있는지 결과 상태만 묻는다.
