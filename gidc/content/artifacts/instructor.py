from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class Instructor(Artifact):
    """교관
    2세트: 원소 마스터리 +80
    4세트: 원소 반응 후 파티 내 모든 캐릭터의 원소 마스터리가 120pt 증가한다. 지속 시간: 8초
    """

    RARITIES = (3, 4)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("elemental_mastery", 80, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        if ask_bool("[교관 4세트] 원소 반응 발동?"):
            for hit in all_hits[wearer].values():
                hit.add("elemental_mastery", 120, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass