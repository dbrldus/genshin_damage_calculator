from gidc.core.artifact import Artifact
from gidc.prompt import ask_int


class CrimsonWitchOfFlames(Artifact):
    """불타오르는 화염의 마녀
    2세트: 불 원소 피해 보너스 +15%
    4세트: 과부하, 연소, 발화 반응으로 주는 피해가 40% 증가하고 증발, 융해 반응의 보너스 계수가 15% 증가한다.
    원소전투 스킬 발동 후 10초 동안 2세트의 효과가 50% 증가한다. 최대 중첩수: 3회
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("pyro_dmg_bonus", 0.15, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("overloaded_bonus", 0.40, (self.artifact_set, 4))
            hit.add("burning_bonus", 0.40, (self.artifact_set, 4))
            hit.add("burgeon_bonus", 0.40, (self.artifact_set, 4))
            hit.add("vaporize_bonus", 0.15, (self.artifact_set, 4))
            hit.add("melt_bonus", 0.15, (self.artifact_set, 4))
        stacks = ask_int("[불타오르는 화염의 마녀 4세트] 원소 스킬 발동 횟수 (최대 3회)", 0, 3)
        for hit in all_hits[wearer].values():
            hit.add("pyro_dmg_bonus", stacks * 0.075, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass