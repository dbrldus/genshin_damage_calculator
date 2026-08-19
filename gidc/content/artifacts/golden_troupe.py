from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class GoldenTroupe(Artifact):
    """황금 극단
    2세트: 원소 스킬 피해 보너스 +20%
    4세트: 원소 스킬 피해 보너스 추가 +25%, 대기 상태 시 추가 +25%
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("skill_dmg_bonus", 0.20, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        off_field = ask_bool("[황금 극단 4세트] 대기 상태?")

        for hit in all_hits[wearer].values():
            hit.add("skill_dmg_bonus", 0.25, (self.artifact_set, 4))
        if off_field:
            for hit in all_hits[wearer].values():
                hit.add("skill_dmg_bonus", 0.25, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass