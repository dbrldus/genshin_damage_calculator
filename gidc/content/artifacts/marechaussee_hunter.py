from gidc.core.artifact import Artifact
from gidc.prompt import ask_int


class MarechausseeHunter(Artifact):
    """그림자 사냥꾼
    2세트: 일반 공격과 강공격으로 주는 피해+15%
    4세트: 캐릭터의 현재 HP에 변화가 생기면 치명타 확률이 12% 증가한다. 지속 시간: 5초, 최대 중첩수: 3회
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("normal_atk_dmg_bonus", 0.15, (self.artifact_set, 2))
            hit.add("charged_atk_dmg_bonus", 0.15, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        stacks = ask_int("[그림자 사냥꾼 4세트] 스택 수 (HP 증가/감소, 최대 3스택a)", 0, 3)
        for hit in all_hits[wearer].values():
            hit.add("crit_rate", stacks * 0.12, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass