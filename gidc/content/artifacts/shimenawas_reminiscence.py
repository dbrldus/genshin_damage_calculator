from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class ShimenawasReminiscence(Artifact):
    """추억의 시메나와
    2세트: 공격력 +18%
    4세트: 원소전투 스킬 발동 후 캐릭터의 원소 에너지가 15pt 이상일 경우, 15pt의 원소 에너지를 잃는다. 
    그 후 10초 동안 일반 공격, 강공격, 낙하 공격으로 주는 피해가 50% 증가한다. 지속 기간 내에 해당 효과는 다시 발동하지 않는다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", 0.18, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        if ask_bool("[추억의 시메나와 4세트] 원소 에너지 잃고 효과 발동?"):
            for hit in all_hits[wearer].values():
                hit.add("normal_atk_dmg_bonus", 0.50, (self.artifact_set, 4))
                hit.add("charged_atk_dmg_bonus", 0.50, (self.artifact_set, 4))
                hit.add("plunging_dmg_bonus", 0.50, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass