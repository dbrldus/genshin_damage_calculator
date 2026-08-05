from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class StarcallersWatch(Weapon):
    """별지기의 시선 (Starcaller's Watch) | 법구 | 5성
    패시브: 바람과 태양에 바치는 연기 제사
    - 원소 마스터리가 100/125/150/175/200pt 증가 (조건 없음, 착용자 전용)
    - 장착 캐릭터가 창조한 보호막이 「주시」 효과를 생성한다. 지속 시간: 15초.
      해당 기간 동안 파티 내에 있는 필드 위 캐릭터가 자신과 가까운 범위 내의 적에게
      주는 피해가 28/35/42/49/56% 증가한다. 주시 효과는 15초마다 최대 1회 발동된다.

    「필드 위 캐릭터」는 스냅샷된 특정 1명이 아니라 15초 동안 필드에 서는 캐릭터 전원이라
    파티 전원의 히트에 넣는다 (시틀라리 C1·에스코피에 C2와 같은 계열 — 「현재 필드 위
    캐릭터」 1명을 고르는 하늘의 은총 4세트 쪽이 아니다). 제외 문구가 없으므로 착용자도
    포함된다. 「가까운 범위 내의 적」은 사거리 조건이라 항상 참으로 본다.
    파티 전체에 뿌리는 효과이므로 동명의 무기끼리는 중첩되지 않는다.
    """

    _EM_BONUS  = [100, 125, 150, 175, 200]
    _WATCH_DMG = [0.28, 0.35, 0.42, 0.49, 0.56]

    _SOURCE = "무기: 별지기의 시선"

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.ELEMENTAL_MASTERY,
        )

    # 두 효과 모두 고정값이라 스탯을 읽지 않는다 → Phase 3에서 넣어도 순서와 무관하다.
    def apply_passive(self, all_hits, wearer) -> None:
        r = self.refinement - 1

        # 효과 1: 착용자 원소 마스터리 — 부옵션과 별개로 더해지는 무조건 상승분.
        for hit in all_hits[wearer].values():
            hit.add("elemental_mastery", self._EM_BONUS[r], self._SOURCE,
                    note="연기 제사")

        # 효과 2: 「주시」 — 착용자가 보호막을 창조했을 때만 켜진다.
        if not ask_bool("[별지기의 시선] 착용자가 만든 보호막으로 「주시」 효과가 발동 중인지 여부"):
            return

        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.apply_unique_buff(self._SOURCE, "all_dmg_bonus", self._WATCH_DMG[r])
