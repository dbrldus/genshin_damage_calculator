from gidc.core.artifact import Artifact
from gidc.prompt import ask_int


class HuskOfOpulentDreams(Artifact):
    """풍요로운 꿈의 껍데기
    2세트: 방어력 +30%
    4세트: 해당 성유물 세트를 장착한 캐릭터는 아래 상황에서 「문답」 효과를 얻는다: 
    필드 위에서 바위 원소 공격으로 적 명중 시 1스택 획득, 0.3초마다 최대 1회 발동된다. 
    대기 상태일 때 3초마다 1스택 획득. 문답 효과는 최대 4스택까지 중첩 가능하고, 
    스택 당 6%의 방어력과 6%의 바위 원소 피해 보너스를 제공한다. 6초마다 문답 효과를 획득하지 못할 경우, 1스택이 차감된다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("def_pct", 0.30, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        stacks = ask_int("[풍요로운 꿈의 껍데기 4세트] '문답' 스택 수(최대 4스택)", 0, 4)
        for hit in all_hits[wearer].values():
            hit.add("def_pct", stacks * 0.06, (self.artifact_set, 4))
            hit.add("geo_dmg_bonus", stacks * 0.06, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass