from gidc.core.artifact import Artifact
from gidc.prompt import ask_int


class FragmentOfHarmonicWhimsy(Artifact):
    """조화로운 공상의 단편
    2세트: 공격력 +18%
    4세트: 생명의 계약의 수치가 증가 또는 감소 시, 캐릭터가 주는 피해가 18% 증가한다. 지속 시간: 6초, 최대 중첩수: 3회
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", 0.18, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        stacks = ask_int("[조화로운 공상의 단편 4세트] 생명의 계약 증감 스택 수(최대 3)", 0, 3)
        for hit in all_hits[wearer].values():
            hit.add("all_dmg_bonus", stacks * 0.18, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass    