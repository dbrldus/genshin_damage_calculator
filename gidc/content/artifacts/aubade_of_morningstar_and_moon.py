from gidc.core.artifact import Artifact
from gidc.enums import MoonsignLevel
from gidc.core.party_state import moonsign_level
from gidc.prompt import ask_bool


class AubadeOfMorningstarAndMoon(Artifact):
    """샛별과 달의 여명
    2세트: 원소 마스터리 +80
    4세트: 장착 캐릭터가 대기 상태일 경우, 주는 달빛 반응 피해가 20% 증가한다. 
    파티의 달빛 징조 레벨이 최소 보름일 경우, 주는 달빛 반응 피해가 40% 더 증가한다. 
    상술한 효과는 장착 캐릭터가 필드에 등장 후 3초가 지나면 사라진다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("elemental_mastery", 80, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        off_field = ask_bool("[샛별과 달의 여명 4세트] 대기 상태?")
        # 달빛 징조는 파티 구성에서 유도한다 (달빛 징조 캐릭터 수).
        ascendant_gleam = moonsign_level(all_hits) is MoonsignLevel.FULL

        if off_field and ascendant_gleam:
            for hit in all_hits[wearer].values():
                hit.add("lunar_charged_bonus", 0.60, (self.artifact_set, 4))
                hit.add("lunar_bloom_bonus", 0.60, (self.artifact_set, 4))
                hit.add("lunar_crystallize_bonus", 0.60, (self.artifact_set, 4))
        elif off_field:
            for hit in all_hits[wearer].values():
                hit.add("lunar_charged_bonus", 0.20, (self.artifact_set, 4))
                hit.add("lunar_bloom_bonus", 0.20, (self.artifact_set, 4))
                hit.add("lunar_crystallize_bonus", 0.20, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass
