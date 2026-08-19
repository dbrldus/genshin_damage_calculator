from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class BloodstainedChivalry(Artifact):
    """피에 물든 기사도
    2세트: 가하는 물리 피해 +25%
    4세트: 적을 처치한 후 10초 동안 강공격 사용 시 스태미나를 소모하지 않고 강공격으로 주는 피해가 50% 증가한다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("physical_dmg_bonus", 0.25, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        if ask_bool("[피에 물든 기사도 4세트] 적 처치 후 10초 이내?"):
            for hit in all_hits[wearer].values():
                hit.add("charged_atk_dmg_bonus", 0.50, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass