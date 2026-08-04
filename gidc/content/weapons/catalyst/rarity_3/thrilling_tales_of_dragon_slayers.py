from gidc.core.weapon import Weapon, WeaponSubStat
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_choice


class ThrillingTalesOfDragonSlayers(Weapon):
    """드래곤 슬레이어 영웅담
    패시브: 전승
    - 스스로 캐릭터를 교체 시 새로 등장한 캐릭터의 공격력이 24/30/36/42/48% 증가
      지속 시간: 10초. 해당 효과는 20초마다 1번 발동한다

    효과 대상은 착용자가 아니라 **교체되어 들어온 다른 캐릭터**다.
    동명의 무기가 만드는 버프는 중첩되지 않는다.
    """

    _ATK_BONUS = [0.24, 0.30, 0.36, 0.42, 0.48]

    _SOURCE = "무기: 드래곤 슬레이어 영웅담"

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type = WeaponType.CATALYST,
            base_atk    = 401,
            refinement  = refinement,
            sub_stat    = WeaponSubStat(StatType.HP_PCT, 35.2),
        )

    # 고정값 공격력% 기여라 스탯을 읽지 않는다 → Phase 3에서 넣어도 순서와 무관하다.
    # (코어 풀 출력이므로 Phase 5의 apply_passive_dependent에 두면 정확성 가드에 걸린다.)
    def apply_passive(self, all_hits, wearer) -> None:
        # 착용자가 교체되어 나가면서 거는 버프라 대상은 착용자 본인이 될 수 없다.
        targets = [char for char in all_hits if char is not wearer]
        if not targets:
            return

        options = [f"{char.name} ({char.element.value})" for char in targets] + ["없음"]
        idx = ask_choice("[드래곤 슬레이어 영웅담] 교체되어 등장한 캐릭터", options)
        if idx >= len(targets):
            return

        bonus = self._ATK_BONUS[self.refinement - 1]
        for hit in all_hits[targets[idx]].values():
            hit.apply_unique_buff(self._SOURCE, "atk_pct", bonus)
