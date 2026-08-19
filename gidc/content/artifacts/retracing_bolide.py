from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class RetracingBolide(Artifact):
    """날아오르는 유성
    2세트: 보호막 강화 효과+35%
    4세트: 보호막이 존재 시 추가로 일반 공격과 강공격 보너스를 40% 획득한다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        pass

    def apply_4set(self, all_hits, wearer) -> None:
        if ask_bool("[날아오르는 유성 4세트] 보호막 존재?"):
            for hit in all_hits[wearer].values():
                hit.add("normal_atk_dmg_bonus", 0.40, (self.artifact_set, 4))
                hit.add("charged_atk_dmg_bonus", 0.40, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass