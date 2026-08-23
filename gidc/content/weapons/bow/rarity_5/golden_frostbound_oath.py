from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class GoldenFrostboundOath(Weapon):
    """서리 맺힌 금빛 가지 (Golden Frostbound Oath) | 활 | 5성
    패시브: 여명의 인사
    - 방어력이 16/20/24/28/32% 증가한다.
    - 장착 캐릭터가 원소전투 스킬로 피해를 주거나 달 결정 반응 피해를 주면 6초 동안
      「서리 요정의 보은」을 획득한다: 착용자의 바위 원소 피해와 달 결정 반응 피해가
      40/50/60/70/80% 증가한다.
    - 지속 시간 동안 착용자 주변에 달빛 조각이 존재하면, 파티 내 다른 모든
      캐릭터가 추가로 「서리 요정의 장난」을 획득한다: 바위 원소 피해와 달 결정
      반응 피해가 20/25/30/35/40% 증가한다. 「서리 요정의 보은」이 끝나면 함께
      사라진다.
    """

    _DEF_PCT   = [0.16, 0.2, 0.24, 0.28, 0.32]
    _SELF_DMG  = [0.4, 0.5, 0.6, 0.7, 0.8]
    _PARTY_DMG = [0.2, 0.25, 0.3, 0.35, 0.4]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.BOW,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 서리 맺힌 금빛 가지"

        # 효과 1: 방어력 — 조건 없이 착용자에게만 붙는다.
        for hit in all_hits[wearer].values():
            hit.add("def_pct", self._DEF_PCT[r], label)

        # 효과 2 「서리 요정의 보은」. 트리거가 둘(원소전투 스킬 피해/달 결정 반응
        # 피해)이지만 어느 쪽이든 켜지는 결과는 같으므로 활성 여부 하나만 묻는다 —
        # 원소전투 스킬 사용은 파티 구성과 무관하게 항상 가능해 파티로 게이팅하지
        # 않는다(피로 물든 성이 달 감전 반응 자체에만 의존하는 것과는 다르다).
        if not ask_bool(
            "[서리 맺힌 금빛 가지] 「서리 요정의 보은」 활성 여부 "
            "(원소전투 스킬 피해 또는 달 결정 반응 피해 후 6초 이내)"
        ):
            return
        for hit in all_hits[wearer].values():
            hit.add("geo_dmg_bonus",           self._SELF_DMG[r], label, note="서리 요정의 보은")
            hit.add("lunar_crystallize_bonus",  self._SELF_DMG[r], label, note="서리 요정의 보은")

        # 효과 3 「서리 요정의 장난」. 「보은」이 켜져 있어야 하고, 추가로 착용자 주변에
        # 달빛 조각이 존재해야 한다 — 조각 존재 여부는 로테이션이 정하므로 따로 묻는다.
        # 파티 전원(착용자 제외) 대상 + 동명 무기 간 비중첩이므로 apply_unique_buff로
        # 제출한다.
        if not ask_bool(
            "[서리 맺힌 금빛 가지] 착용자 주변에 달빛 조각 존재 여부 (「서리 요정의 장난」)"
        ):
            return
        for char, char_hits in all_hits.items():
            if char is wearer:
                continue
            for hit in char_hits.values():
                hit.apply_unique_buff(label, "geo_dmg_bonus",          self._PARTY_DMG[r])
                hit.apply_unique_buff(label, "lunar_crystallize_bonus", self._PARTY_DMG[r])
