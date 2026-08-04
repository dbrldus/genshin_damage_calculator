from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class BraveHeart(Artifact):
    """용사의 마음
    2세트: 공격력 +18%
    4세트: HP가 50%를 초과하는 적에게 주는 피해가 30% 증가한다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", 0.18, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        if ask_bool("[용사의 마음 4세트] 적 HP 50% 초과?"):
            for hit in all_hits[wearer].values():
                hit.add("all_dmg_bonus", 0.30, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass