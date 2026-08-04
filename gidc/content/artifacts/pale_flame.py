from gidc.core.artifact import Artifact
from gidc.prompt import ask_int


class PaleFlame(Artifact):
    """창백의 화염
    2세트: 가하는 물리 피해+25%
    4세트: 원소전투 스킬로 적을 명중하면 공격력이 9% 증가한다. 지속 시간: 7초, 최대 중첩수: 2회. 
    해당 효과는 0.3초마다 1회 발동되며, 2회 중첩 시 2세트의 효과가 100% 증가한다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("physical_dmg_bonus", 0.25, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        stacks = ask_int("[창백의 화염 4세트] 원소 스킬 명중 스택 수(최대 2스택)", 0, 2)
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", stacks * 0.09, (self.artifact_set, 4))
        if stacks == 2:
            for hit in all_hits[wearer].values():
                hit.add("physical_dmg_bonus", 0.25, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass