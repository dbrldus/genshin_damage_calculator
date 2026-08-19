from gidc.core.artifact import Artifact
from gidc.prompt import ask_int


class NymphsDream(Artifact):
    """님프의 꿈
    2세트: 물 원소 피해 보너스 +15%
    4세트: 일반 공격, 강공격, 낙하 공격, 원소전투 스킬 또는 원소폭발이 적에게 명중한 후, 8초 동안 지속되는 「거울 속 님프」 효과가 1스택 생성된다. 
    「거울 속 님프」 효과가 1/2/3스택 이상일 시, 공격력이 7%/16%/25% 증가하고 물 원소 피해 보너스가 4%/9%/15% 증가한다. 
    일반 공격, 강공격, 낙하 공격, 원소전투 스킬 또는 원소폭발이 생성한 「거울 속 님프」는 각각 독립적으로 존재한다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("hydro_dmg_bonus", 0.15, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        stacks = ask_int("[님프의 꿈 4세트] 「거울 속 님프」 스택 수(최대 5스택)", 0, 5)
        if stacks == 1:
            for hit in all_hits[wearer].values():
                hit.add("atk_pct", 0.07, (self.artifact_set, 4))
                hit.add("hydro_dmg_bonus", 0.04, (self.artifact_set, 4))
        elif stacks == 2:
            for hit in all_hits[wearer].values():
                hit.add("atk_pct", 0.16, (self.artifact_set, 4))
                hit.add("hydro_dmg_bonus", 0.09, (self.artifact_set, 4))
        elif stacks >= 3:
            for hit in all_hits[wearer].values():
                hit.add("atk_pct", 0.25, (self.artifact_set, 4))
                hit.add("hydro_dmg_bonus", 0.15, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass