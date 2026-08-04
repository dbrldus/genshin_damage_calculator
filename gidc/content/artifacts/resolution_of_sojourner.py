from gidc.core.artifact import Artifact
from gidc.core.profile import SkillType


class ResolutionOfSojourner(Artifact):
    """행자의 마음
    2세트: 공격력 +18%
    4세트: 강공격 치명타 확률 +30%
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", 0.18, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            if hit.skill_type == SkillType.CHARGED_ATK:
                hit.add("crit_rate", 0.30, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass