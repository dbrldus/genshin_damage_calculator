from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class NighttimeWhispersInTheEchoingWoods(Artifact):
    """메아리숲의 야화
    2세트: 공격력 +18%
    4세트: 원소 스킬 사용 후 바위 원소 피해 보너스 +20%, 결정 보호막 존재 시 추가 +30%
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", 0.18, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        skill_used = ask_bool("[메아리숲의 야화 4세트] 원소 스킬 사용 후 10초 이내?")
        if not skill_used:
            return

        # 결정 보호막/달 결정 조각 보너스는 스킬 사용 상태에 대한 "추가" 보너스이므로
        # 스킬 사용 상태가 전제조건이다.
        crystalize_reaction = ask_bool("[메아리숲의 야화 4세트] 결정 보호막 or 달 결정 조각 존재?")
        bonus = 0.20 + (0.30 if crystalize_reaction else 0.0)
        for hit in all_hits[wearer].values():
            hit.add("geo_dmg_bonus", bonus, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass