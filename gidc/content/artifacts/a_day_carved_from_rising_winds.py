from gidc.core.artifact import Artifact
from gidc.enums import CharacterTrait
from gidc.prompt import ask_bool


class ADayCarvedFromRisingWinds(Artifact):
    """바람이 시작되는 날
    2세트: 공격력 +18%
    4세트: 일반 공격, 강공격, 원소전투 스킬 또는 원소폭발이 적에게 명중 시, 6초 동안 지속되는 「바람과 목가의 가호」을 획득한다: 공격력이 25% 증가한다. 
    장착 캐릭터가 「마녀의 과제」를 완료했을 경우, 「바람과 목가의 가호」가 「바람과 목가의 결의」로 강화되어, 과제를 통과한 장착 캐릭터의 치명타 확률이 추가로 20% 증가한다. 
    상술한 효과는 장착 캐릭터가 대기 상태일 때에도 발동된다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", 0.18, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        blessing_of_pastoral_winds = ask_bool("[바람이 시작되는 날 4세트] 「바람과 목가의 가호」")
        # 「마녀의 과제」를 완료한 캐릭터 = 마도 캐릭터.
        is_hexerei = wearer.has_trait(CharacterTrait.HEXEREI)

        if blessing_of_pastoral_winds and is_hexerei:
            for hit in all_hits[wearer].values():
                hit.add("atk_pct", 0.25, (self.artifact_set, 4))
                hit.add("crit_rate", 0.2, (self.artifact_set, 4))
        elif blessing_of_pastoral_winds:
            for hit in all_hits[wearer].values():
                hit.add("atk_pct", 0.25, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass
