from gidc.core.artifact import Artifact


class TravelingDoctor(Artifact):
    """떠돌이 의사
    2세트: 캐릭터가 받는 치유 효과+20%
    4세트: 원소폭발 발동 시 HP를 20% 회복한다
    """

    RARITIES = (1, 2, 3)

    def apply_2set(self, profiles, wearer) -> None:
        pass

    def apply_4set(self, profiles, wearer) -> None:
        pass

    def apply_4set_dependent(self, all_hits, wearer):
        pass