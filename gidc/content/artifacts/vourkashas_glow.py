from gidc.core.artifact import Artifact
from gidc.prompt import ask_int


class VourkashasGlow(Artifact):
    """감로빛 꽃바다
    2세트: HP +20%
    4세트: 원소전투 스킬 및 원소폭발로 주는 피해가 10% 증가한다. 장착 캐릭터가 피해를 입은 후 5초 동안 해당 피해 증가 효과가 80% 증가한다. 
    최대 중첩수: 5스택. 스택마다 지속 시간은 독립적으로 계산한다. 해당 효과는 장착 캐릭터가 대기 상태일 때도 발동된다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("hp_pct", 0.20, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("skill_dmg_bonus", 0.10, (self.artifact_set, 4))
            hit.add("burst_dmg_bonus", 0.10, (self.artifact_set, 4))

        stacks = ask_int("[감로빛 꽃바다 4세트] 피해 입은 횟수(스택 수)", 0, 5)
        for hit in all_hits[wearer].values():
            hit.add("skill_dmg_bonus", stacks * 0.08, (self.artifact_set, 4))
            hit.add("burst_dmg_bonus", stacks * 0.08, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass