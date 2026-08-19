from gidc.core.artifact import Artifact


class LuckyDog(Artifact):
    """행운아
    2세트: 방어력 +100
    4세트: 모라 획득 시 HP를 300pt 회복한다
    """

    RARITIES = (1, 2, 3)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("def_flat", 100.0, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        pass

    def apply_4set_dependent(self, all_hits, wearer):
        pass