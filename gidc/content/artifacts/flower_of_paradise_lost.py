from gidc.core.artifact import Artifact
from gidc.prompt import ask_int


class FlowerOfParadiseLost(Artifact):
    """잃어버린 낙원의 꽃
    2세트: 원소 마스터리 +80
    4세트: 장착 캐릭터가 개화, 만개, 발화 반응으로 주는 피해가 40%, 달 개화 반응으로 주는 피해가 10% 증가한다. 
    또한 장착 캐릭터가 개화, 만개, 발화, 달 개화 발동 후 상술한 효과로 증가한 보너스가 25% 증가한다. 
    지속 시간: 10초. 최대 중첩수: 4회. 해당 효과는 1초마다 최대 1회 발동되며, 장착 캐릭터가 대기 상태일 때도 발동된다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("elemental_mastery", 80, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        # 각 반응별로 스택이 쌓이는 건지, 하나 발동하면 전체가 오르는건지 확인 필요.
        stacks = ask_int("[잃어버린 낙원의 꽃 4세트] 스택 수", 0, 4)
        for hit in all_hits[wearer].values():
            hit.add("bloom_bonus", 0.40 + stacks * 0.10, (self.artifact_set, 4))
            hit.add("hyperbloom_bonus", 0.40 + stacks * 0.10, (self.artifact_set, 4))
            hit.add("burgeon_bonus", 0.40 + stacks * 0.10, (self.artifact_set, 4))
            hit.add("lunar_bloom_bonus", 0.10 + stacks * 0.025, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass   