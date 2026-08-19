from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool, ask_choice


class FinaleOfTheDeepGalleries(Artifact):
    """깊은 회랑의 피날레
    2세트: 얼음 원소 피해 보너스 +15%
    4세트: 원소 에너지 0pt 시 일반 공격 또는 원소 폭발 피해 +60%
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("cryo_dmg_bonus", 0.15, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        if ask_bool("[깊은 회랑의 피날레 4세트] 원소 에너지 0pt?"):
            idx = ask_choice(
                "[깊은 회랑의 피날레 4세트] 활성화된 버프",
                ["없음", "일반 공격 버프", "원소 폭발 버프"],
            )
            if idx == 1:
                for hit in all_hits[wearer].values():
                    hit.add("normal_atk_dmg_bonus", 0.60, (self.artifact_set, 4))
            elif idx == 2:
                for hit in all_hits[wearer].values():
                    hit.add("burst_dmg_bonus", 0.60, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass