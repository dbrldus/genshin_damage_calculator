from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class MartialArtist(Artifact):
    """무인
    2세트: 일반 공격과 강공격으로 주는 피해+15%
    4세트: 원소 스킬 사용 후 8초 이내 일반·강공격 피해 보너스 +25%
    """

    RARITIES = (3, 4)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("normal_atk_dmg_bonus", 0.15, (self.artifact_set, 2))
            hit.add("charged_atk_dmg_bonus", 0.15, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        if ask_bool("[무인 4세트] 원소 스킬 사용 후 8초 이내?"):
            for hit in all_hits[wearer].values():
                hit.add("normal_atk_dmg_bonus", 0.25, (self.artifact_set, 4))
                hit.add("charged_atk_dmg_bonus", 0.25, (self.artifact_set, 4))
