from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool, ask_int


class VermillionHereafter(Artifact):
    """진사 왕생록
    2세트: 공격력 +18%
    4세트: 원소폭발 시전 후 16초 동안 「숨겨진 빛」 효과가 생성되고, 공격력이 8% 증가한다. 
    캐릭터 HP가 감소할 때 공격력이 10% 더 증가한다. 이러한 방식으로 최대 4회 증가할 수 있으며, 0.8초마다 1회 발동한다. 
    「숨겨진 빛」 효과는 캐릭터 퇴장 시 사라진다. 지속 시간 동안 다시 원소폭발 발동 시 기존의 「숨겨진 빛」이 사라진다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", 0.18, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        if not ask_bool("[진사 왕생록 4세트] 원소 폭발 사용 후 16초 이내?"):
            return

        stacks = ask_int("[진사 왕생록 4세트] HP 감소 스택 수", 0, 4)
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", 0.08 + stacks * 0.10, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass
