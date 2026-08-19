from gidc.core.artifact import Artifact
from gidc.prompt import ask_choice

# 피해 증가량은 초당 10%씩 증감하므로 10% 단위 값만 가질 수 있다 (최대 50%).
_DMG_BONUS_STEPS = [0, 10, 20, 30, 40, 50]


class UnfinishedReverie(Artifact):
    """미완의 몽상
    2세트: 공격력 +18%
    4세트: 전투 상태 이탈 3초 후, 주는 피해가 50% 증가한다. 
    전투 상태에서 6초 넘게 주변에 연소 상태의 적이 없으면, 상술한 피해 증가 효과는 0%에 이를 때까지 초당 10%씩 감소한다. 
    연소 상태의 적이 있을 시, 50%에 이를 때까지 초당 10%씩 증가한다. 해당 성유물 세트를 장착한 캐릭터가 대기 상태 시에도 해당 효과는 발동된다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", 0.18, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        # 대기 상태에서도 발동하므로 필드 등장 여부는 묻지 않는다.
        idx = ask_choice(
            "[미완의 몽상 4세트] 현재 피해 증가 수치",
            [f"{v}%" for v in _DMG_BONUS_STEPS],
        )
        for hit in all_hits[wearer].values():
            hit.add("all_dmg_bonus", _DMG_BONUS_STEPS[idx] / 100.0, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass
