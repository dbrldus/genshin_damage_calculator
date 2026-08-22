from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class ScarletProof(Artifact):
    """핏빛 증표
    2세트: 공격력 +18%
    4세트: 장착 캐릭터가 별 확산 반응을 발동한 후 10초 동안 치명타 확률이 16%
    증가하고, 별 확산 반응 피해가 40% 증가한다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", 0.18, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        if not ask_bool("[핏빛 증표 4세트] 별 확산 반응을 발동한 후 10초 이내?"):
            return

        for hit in all_hits[wearer].values():
            hit.add("crit_rate", 0.16, (self.artifact_set, 4))
            hit.add("stellar_swirl_bonus", 0.40, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass
