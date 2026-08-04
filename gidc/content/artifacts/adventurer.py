from gidc.core.artifact import Artifact


class Adventurer(Artifact):
    """모험가
    2세트: HP +1000
    4세트: 보물 상자 개봉 시 HP 30% 회복
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("hp_flat", 1000.0, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        pass

    def apply_4set_dependent(self, all_hits, wearer):
        pass