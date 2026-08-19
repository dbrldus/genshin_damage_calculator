from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class DisenchantmentInDeepShadow(Artifact):
    """그림자 속 산산조각 난 꿈
    2세트: 공격력 +18%
    4세트: 초전도 반응 피해 +80%, 별 초천도 반응 피해 +40%, 적이 초전도 또는 별 초전도 반응의 영향을 받으면 공격의 치명타 확률 +16%
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", 0.18, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("superconduct_bonus", 0.80, (self.artifact_set, 4), note="초전도")
            hit.add("stellar_conduct_bonus", 0.40, (self.artifact_set, 4), note="별 초전도")
        if ask_bool("[그림자 속 산산조각 난 꿈 4세트] 초전도 또는 별 초전도 반응의 영향을 받은 적 공격"):
            for hit in all_hits[wearer].values():
                hit.add("crit_rate", 0.16, (self.artifact_set, 4), note="초전도 영향 적")
