from gidc.core.artifact import Artifact


class Gambler(Artifact):
    """도박꾼
    2세트: 원소전투 스킬로 주는 피해+20%
    4세트: 적을 처치하면 100%의 확률로 원소전투 스킬의 재사용 대기시간이 초기화된다. 해당 효과는 15초마다 1번 발동한다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("skill_dmg_bonus", 0.20, (self.artifact_set, 2))

    def apply_4set(self, profiles, wearer) -> None:
        pass

    def apply_4set_dependent(self, all_hits, wearer):
        pass    