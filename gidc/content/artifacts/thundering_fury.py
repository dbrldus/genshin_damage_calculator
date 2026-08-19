from gidc.core.artifact import Artifact


class ThunderingFury(Artifact):
    """번개 같은 분노
    2세트: 번개 원소 피해 보너스 +15%
    4세트: 과부하, 감전, 초전도, 만개 반응이 주는 피해가 40% 증가하고 촉진 반응이 주는 피해가 20% 증가하며, 달 감전 반응으로 주는 피해가 20% 증가한다. 
    위와 같은 원소 반응 또는 활성화 반응 발동 시, 원소전투 스킬의 재사용 대기시간이 1초 줄어든다. 해당 효과는 0.8초마다 최대 1회 발동한다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("electro_dmg_bonus", 0.15, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("overloaded_bonus", 0.40, (self.artifact_set, 4))
            hit.add("electrocharged_bonus", 0.40, (self.artifact_set, 4))
            hit.add("superconduct_bonus", 0.40, (self.artifact_set, 4))
            hit.add("hyperbloom_bonus", 0.40, (self.artifact_set, 4))
            hit.add("lunar_charged_bonus", 0.20, (self.artifact_set, 4))
            hit.add("aggravate_bonus", 0.20, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass