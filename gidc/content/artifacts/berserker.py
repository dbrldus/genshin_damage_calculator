from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class Berserker(Artifact):
    """전투광
    2세트: 치명타 확률 +12%
    4세트: HP 70% 미만 시 치명타 확률이 추가로 24% 증가한다
    """

    RARITIES = (3, 4)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("crit_rate", 0.12, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        if ask_bool("[전투광 4세트] HP 70% 미만?"):
            for hit in all_hits[wearer].values():
                hit.add("crit_rate", 0.24, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass