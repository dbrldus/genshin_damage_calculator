from gidc.core.artifact import Artifact


class TinyMiracle(Artifact):
    """기적
    2세트: 모든 원소 내성+20%
    4세트: 받은 원소 공격에 대응하는 원소의 내성이 30% 증가한다. 지속 시간: 10초. 해당 효과는 10초마다 1번 발동한다
    """

    RARITIES = (3, 4)

    def apply_2set(self, profiles, wearer) -> None:
        pass

    def apply_4set(self, profiles, wearer) -> None:
        pass

    def apply_4set_dependent(self, all_hits, wearer):
        pass