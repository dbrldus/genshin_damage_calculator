from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType


class SacrificialFragments(Weapon):
    """제례의 악장 (Sacrificial Fragments) | 법구 | 4성
    패시브: 침착
    - 원소전투 스킬로 피해를 줄 때 40/50/60/70/80% 확률로 해당 스킬의 재발동
      대기시간이 초기화된다. 30/26/22/19/16초마다 1회만 발동 (스탯에 영향 없음)

    피해식에 들어가는 것은 부옵션 원소 마스터리뿐이다 — 쿨타임 초기화는 스킬을
    한 번 더 쓰게 해 줄 뿐 계수·스탯 어디에도 항이 없다(페보니우스 계열과 같다).
    """

    # 재련 단계별 초기화 확률 / 발동 간격(초) — 시간축 모델이 생기면 여기서 읽는다.
    _RESET_CHANCE   = [0.40, 0.50, 0.60, 0.70, 0.80]
    _RESET_COOLDOWN = [30, 26, 22, 19, 16]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 4,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.ELEMENTAL_MASTERY,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        pass
