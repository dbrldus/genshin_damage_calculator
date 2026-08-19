from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class Lavawalker(Artifact):
    """불 위를 걷는 현인
    2세트: 불 원소 내성+40%
    4세트: 불 원소의 영향을 받은 적에게 주는 피해가 35% 증가한다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        pass

    def apply_4set(self, all_hits, wearer) -> None:
        if ask_bool("[불 위를 걷는 현인 4세트] 적이 불 원소 영향 받음?"):
            for hit in all_hits[wearer].values():
                hit.add("all_dmg_bonus", 0.35, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass