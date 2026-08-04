from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class DesertPavilionChronicle(Artifact):
    """모래 위 누각의 역사
    2세트: 바람 원소 피해 보너스 +15%
    4세트: 강공격이 적을 명중 후, 해당 캐릭터의 일반 공격 속도가 10% 증가하고 
    일반 공격, 강공격, 낙하 공격으로 주는 피해가 40% 증가한다. 지속 시간: 15초
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("anemo_dmg_bonus", 0.15, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        if ask_bool("[모래 위 누각의 역사 4세트] 강공격 명중 후 15초 이내?"):
            for hit in all_hits[wearer].values():
                hit.add("normal_atk_dmg_bonus", 0.40, (self.artifact_set, 4))
                hit.add("charged_atk_dmg_bonus", 0.40, (self.artifact_set, 4))
                hit.add("plunging_dmg_bonus", 0.40, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass