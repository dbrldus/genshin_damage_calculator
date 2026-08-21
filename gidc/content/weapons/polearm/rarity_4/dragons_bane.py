from gidc.core.weapon import Weapon
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool


class DragonsBane(Weapon):
    """용학살창 (Dragon's Bane) | 장병기 | 4성
    패시브: 따끈따끈 첨벙첨벙
    - 물 원소 또는 불 원소의 영향을 받은 적에게 주는 피해가 20/24/28/32/36% 증가한다
    """

    _DMG = [0.20, 0.24, 0.28, 0.32, 0.36]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.POLEARM,
            rarity        = 4,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.ELEMENTAL_MASTERY,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        # 적의 원소 부착 상태는 파티 구성으로 유도할 수 없다 — 순수수 정령처럼 원래 물을
        # 두른 적이 있어 파티에 물·불이 없어도 조건이 성립한다. 그래서 게이팅 없이 묻는다
        # (뇌명을 평정한 존자·불 위를 걷는 현인 4세트와 같은 규약).
        #
        # 물「또는」불이라 어느 쪽인지는 효과를 가르지 않는다 — 질문도 하나다.
        if not ask_bool("[용학살창] 적이 물 또는 불 원소 영향 받음?"):
            return

        for hit in all_hits[wearer].values():
            hit.add("all_dmg_bonus", self._DMG[self.refinement - 1],
                    "무기: 용학살창", note="따끈따끈 첨벙첨벙")
