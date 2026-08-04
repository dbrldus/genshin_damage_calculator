from gidc.core.weapon import Weapon, WeaponSubStat
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool, ask_multi_choice


class SymphonistOfScents(Weapon):
    """맛의 지휘자 (Symphonist of Scents) | 장병기 | 5성 | 에스코피에 전용 무기
    패시브: 맛의 교향곡
    - 공격력 +12/15/18/21/24% (상시, 착용자)
    - 장착 캐릭터가 대기 상태 시 공격력 추가 +12/15/18/21/24% (착용자)
    - 치유 진행 시 「달콤한 울림」: 장착 캐릭터와 치유를 받은 캐릭터의 공격력 +32/40/48/56/64%
      지속 3초. 장착 캐릭터가 대기 상태일 때도 발동한다.
    """

    _ATK_PCT             = [0.12, 0.15, 0.18, 0.21, 0.24]
    _OFF_FIELD_ATK_PCT   = [0.12, 0.15, 0.18, 0.21, 0.24]
    _SWEET_RESONANCE_ATK = [0.32, 0.40, 0.48, 0.56, 0.64]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type = WeaponType.POLEARM,
            base_atk    = 608,
            refinement  = refinement,
            sub_stat    = WeaponSubStat(StatType.CRIT_DMG, 66.2),
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 맛의 지휘자"

        # 효과 1: 상시 공격력 증가 (착용자) — 조건이 없어 묻지 않는다.
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", self._ATK_PCT[r], label, note="맛의 교향곡")

        # 효과 2: 대기 상태(오프 필드)일 때 추가 공격력 증가 (착용자)
        if ask_bool("[맛의 지휘자] 장착 캐릭터가 대기 상태 여부"):
            for hit in all_hits[wearer].values():
                hit.add("atk_pct", self._OFF_FIELD_ATK_PCT[r], label, note="대기 상태")

        # 효과 3 「달콤한 울림」: 착용자 + 치유를 받은 캐릭터의 공격력 증가.
        # 크로스 캐릭터 코어 스탯(atk_pct) 기여라 Phase 3인 여기가 유일하게 올바른 자리다
        # (Phase 5는 정확성 가드가 코어 풀 출력을 막는다).
        # 동명의 무기 효과는 중첩되지 않으므로 비중첩으로 제출한다 — 착용자가 자신의
        # 치유 대상에도 포함되는 경우 중복 적용되지 않는 효과도 함께 얻는다.
        if not ask_bool("[맛의 지휘자] 치유 진행 여부 (달콤한 울림)"):
            return

        targets = [wearer]
        others  = [char for char in all_hits if char is not wearer]
        if others:
            options = [f"{char.name} ({char.element.value})" for char in others]
            for i in ask_multi_choice("[맛의 지휘자] 치유를 받은 파티원", options):
                targets.append(others[i])

        for char in targets:
            for hit in all_hits[char].values():
                hit.apply_unique_buff(label, "atk_pct", self._SWEET_RESONANCE_ATK[r])
