from gidc.core.weapon import Weapon, WeaponSubStat
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int
from gidc.core.profile import add_all_elemental_dmg_bonus, add_all_elemental_dmg_bonus_unique


class PeakPatrolSong(Weapon):
    """바위산을 맴도는 노래
    패시브: 시들지 않는 생명
    - 일반/낙하 공격 명중 시 「영광의 꽃노래」 획득
      스택당: 방어력 +8/10/12/14/16%, 모든 원소 피해 보너스 +10/12.5/15/17.5/20%
      최대 2스택, 6초 지속
    - 2스택(또는 2스택 갱신) 시:
      장착자 방어력 1000pt당 파티 전원 모든 원소 피해 보너스 +8/10/12/14/16%
      최대 25.6/32/38.4/44.8/51.2%
    """

    _DEF_PER_STACK        = [0.08,  0.10,  0.12,  0.14,  0.16 ]
    _ELEM_PER_STACK       = [0.10,  0.125, 0.15,  0.175, 0.20 ]
    _PARTY_ELEM_PER_1000  = [0.08,  0.10,  0.12,  0.14,  0.16 ]
    _PARTY_ELEM_CAP       = [0.256, 0.32,  0.384, 0.448, 0.512]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type = WeaponType.SWORD,
            base_atk    = 542,
            refinement  = refinement,
            sub_stat    = WeaponSubStat(StatType.DEF_PCT, 82.7),
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r = self.refinement - 1
        hits = all_hits[wearer]

        self._stacks = ask_int("[바위산을 맴도는 노래] 영광의 꽃노래 스택 수", 0, 2)

        # 효과 1: 스택당 방어력% / 원소 피해 보너스 (착용자)
        for hit in hits.values():
            hit.add("def_pct", self._stacks * self._DEF_PER_STACK[r], "무기: 바위산을 맴도는 노래", note="영광의 꽃노래 스택")
            add_all_elemental_dmg_bonus(hit, self._stacks * self._ELEM_PER_STACK[r], "무기: 바위산을 맴도는 노래")

    # 효과 2: 2스택 시 장착자 최종 방어력 기반 파티 원소 피해 보너스 — 방식 B(최종 스탯
    # 기반)이므로 모든 코어 DEF 기여(자기 버프 + 크로스 캐릭터)가 끝난 뒤인 Phase 5에서
    # current_def()를 읽는다.
    # 동명의 무기 효과는 중첩되지 않는다 — 여러 명이 착용하면 방어력이 가장 높은 쪽의
    # 보너스만 남도록 비중첩으로 제출한다(무기 클래스가 「동명」 판정 키).
    def apply_passive_dependent(self, all_hits, wearer) -> None:
        if self._stacks != 2:
            return
        r = self.refinement - 1
        est_def = next(iter(all_hits[wearer].values())).current_def()
        party_bonus = min(
            (est_def / 1000.0) * self._PARTY_ELEM_PER_1000[r],
            self._PARTY_ELEM_CAP[r],
        )
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                add_all_elemental_dmg_bonus_unique(hit, "무기: 바위산을 맴도는 노래", party_bonus)
