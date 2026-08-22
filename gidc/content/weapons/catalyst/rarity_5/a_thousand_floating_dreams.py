from gidc.core.weapon import Weapon
from gidc.core.profile import element_dmg_field
from gidc.enums import WeaponType
from gidc.enums import StatType


class AThousandFloatingDreams(Weapon):
    """떠오르는 천일 밤의 꿈 (A Thousand Floating Dreams) | 법구 | 5성
    패시브: 천 개의 새벽이 부르는 노래
    - 장착 캐릭터와 파티 내 기타 캐릭터의 원소 타입 동일 여부에 따라, 장착한 캐릭터에게
      제공되는 효과가 달라진다. 같은 경우: 원소 마스터리가 32/40/48/56/64pt 증가한다.
      다른 경우: 장착 캐릭터의 원소 타입의 원소 피해 보너스가 10/14/18/22/26% 증가한다.
      해당 증가 효과는 각각 최대 3회까지 중첩된다. 추가로, 파티 내 장착 캐릭터를 제외한
      주변 캐릭터의 원소 마스터리가 40/42/44/46/48pt 증가한다. 동명의 무기를 여러 개
      장착 시, 해당 효과는 중첩 가능하다
    """

    _EM_PER_SAME  = [32, 40, 48, 56, 64]
    _DMG_PER_DIFF = [0.1, 0.14, 0.18, 0.22, 0.26]
    _EM_PER_OTHER = [40, 42, 44, 46, 48]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.ELEMENTAL_MASTERY,
        )

    _MAX_ELEM_STACKS = 3

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 떠오르는 천일 밤의 꿈"

        # 효과 1·2: 같은/다른 원소 여부는 파티 구성만으로 정해지므로 묻지 않고 유도한다.
        # 「기타 캐릭터」이므로 착용자 자신은 센 대상에서 뺀다.
        others = [c for c in all_hits if c is not wearer]
        same_n = sum(1 for c in others if c.element is wearer.element)
        diff_n = len(others) - same_n
        same_n = min(same_n, self._MAX_ELEM_STACKS)
        diff_n = min(diff_n, self._MAX_ELEM_STACKS)

        wearer_hits = all_hits[wearer].values()
        if same_n:
            em_bonus = same_n * self._EM_PER_SAME[r]
            for hit in wearer_hits:
                hit.add("em_from_flat", em_bonus, label, note="천 개의 새벽이 부르는 노래 (동원소)")
        if diff_n:
            field = element_dmg_field(wearer.element)
            if field is not None:   # 물리 등 원소가 없는 캐릭터는 대상 필드가 없다
                dmg_bonus = diff_n * self._DMG_PER_DIFF[r]
                for hit in wearer_hits:
                    hit.add(field, dmg_bonus, label, note="천 개의 새벽이 부르는 노래 (이원소)")

        # 효과 3: 착용자를 제외한 파티원 전원에게 고정 EM. 「동명의 무기를 여러 개
        # 장착 시 중첩 가능」이 실측으로 확인된 규칙이라, 다른 파티 버프처럼
        # apply_unique_buff로 비중첩 제출하지 않고 그냥 add로 쌓이게 둔다 — 착용자가
        # 둘이면 다른 파티원은 이 몫을 두 번 받는다.
        other_bonus = self._EM_PER_OTHER[r]
        for char in others:
            for hit in all_hits[char].values():
                hit.add("em_from_flat", other_bonus, label, note="천 개의 새벽이 부르는 노래 (파티원)")
