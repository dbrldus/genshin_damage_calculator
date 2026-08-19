from gidc.core.artifact import Artifact


class MaidenBeloved(Artifact):
    """사랑받는 소녀
    2세트: 치유 보너스 +15%
    4세트: 원소전투 스킬 또는 원소폭발 발동 후 10초 동안 파티 내 모든 캐릭터가 받는 치유 효과가 20% 증가한다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("healing_bonus", 0.15, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        pass

    def apply_4set_dependent(self, all_hits, wearer):
        pass