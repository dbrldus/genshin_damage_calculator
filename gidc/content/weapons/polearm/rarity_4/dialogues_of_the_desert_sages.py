from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType


class DialoguesOfTheDesertSages(Weapon):
    """위대한 사막 현자의 대답 (Dialogues of the Desert Sages) | 장병기 | 4성
    패시브: 균형 원리
    - 치유 진행 시 원소 에너지 8/10/12/14/16pt 회복
      10초마다 최대 1회 발동하며, 캐릭터가 대기 상태여도 발동한다 (스탯에 영향 없음)

    피해식에 들어가는 것은 부옵션 HP%뿐이다 — 에너지 회복은 자원 모델이 없어
    항이 없다(페보니우스 검과 같은 계열).
    """

    # 재련 단계별 원소 에너지 회복량 — 자원 모델이 생기면 여기서 읽는다.
    _ENERGY_RESTORE = [8, 10, 12, 14, 16]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.POLEARM,
            rarity        = 4,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.HP_PCT,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        pass
