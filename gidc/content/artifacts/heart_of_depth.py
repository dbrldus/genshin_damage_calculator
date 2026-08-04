from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class HeartOfDepth(Artifact):
    """몰락한 마음
    2세트: 물 원소 피해 보너스 +15%
    4세트: 원소전투 스킬 발동 후 15초 동안 일반 공격과 강공격으로 주는 피해가 30% 증가한다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("hydro_dmg_bonus", 0.15, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        if ask_bool("[몰락한 마음 4세트] 원소 스킬 사용 후 15초 이내?"):
            for hit in all_hits[wearer].values():
                hit.add("normal_atk_dmg_bonus", 0.30, (self.artifact_set, 4))
                hit.add("charged_atk_dmg_bonus", 0.30, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass