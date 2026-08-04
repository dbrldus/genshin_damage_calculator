from gidc.core.artifact import Artifact
from gidc.core.profile import SkillType
from gidc.prompt import ask_bool


class EchoesOfAnOffering(Artifact):
    """제사의 여운
    2세트: 공격력 +18%
    4세트: 일반 공격이 적 명중 시, 36%의 확률로 「유곡의 축사」를 발동한다. 
    「유곡의 축사」: 일반 공격으로 주는 피해가 공격력의 70%만큼 증가한다. 
    해당 효과는 일반 공격으로 피해를 가한 다음 0.05초 후에 사라진다. 
    일반 공격으로 「유곡의 축사」가 발동되지 않을 때, 다음 공격에서 발동될 확률이 20% 증가한다. 
    0.2초 내 최대 1회 발동 여부를 판정한다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", 0.18, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        # 공격력에 스케일하는 효과라 Phase 5(apply_4set_dependent)에서 처리한다.
        pass

    def apply_4set_dependent(self, all_hits, wearer) -> None:
        # 발동 확률(36% + 미발동 시 20% 누적)은 모델링하지 않고 발동 여부를 직접 묻는다.
        if not ask_bool("[제사의 여운 4세트] '유곡의 축사' 발동?"):
            return

        # 「유곡의 축사」는 일반 공격 피해만 증가시킨다.
        for hit in all_hits[wearer].values():
            if hit.skill_type is not SkillType.NORMAL_ATK:
                continue
            # 방식 B: 모든 코어 스탯 기여가 끝난 뒤 히트별 최신 ATK를 읽어
            #         피해 풀(flat_dmg_bonus)로 차원 변환한다.
            hit.add("flat_dmg_bonus", hit.current_atk() * 0.70, (self.artifact_set, 4))
