from gidc.core.artifact import Artifact
from gidc.prompt import ask_int


class LongNightsOath(Artifact):
    """긴 밤의 맹세
    2세트: 낙하 공격 피해 보너스 +25%
    4세트: 장착 캐릭터의 낙하 공격/강공격/원소전투 스킬이 적에게 명중 후, 「영원한 광휘」를 1/2/2스택 획득한다. 
    해당 효과는 낙하 공격, 강공격 또는 원소전투 스킬로 1초마다 각각 최대 1회 발동된다. 
    「영원한 광휘」: 낙하공격으로 주는 피해가 15% 증가한다. 지속 시간: 6초, 최대 중첩수: 5스택, 스택마다 지속 시간은 독립적으로 계산한다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("plunging_dmg_bonus", 0.25, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        stacks = ask_int("[긴 밤의 맹세 4세트] '영원히 광채' 스택 수(최대 5스택)", 0, 5)
        for hit in all_hits[wearer].values():
            hit.add("plunging_dmg_bonus", stacks * 0.15, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass