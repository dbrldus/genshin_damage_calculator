from gidc.core.artifact import Artifact


class TheExile(Artifact):
    """유배자
    2세트: 원소 충전 효율 +20%
    4세트: 원소폭발 발동 후 2초마다 파티 내 모든 캐릭터(자신을 포함하지 않음)의 원소 에너지를 2pt 회복한다. 해당 효과는 6초간 지속하며 중첩되지 않는다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("energy_recharge", 0.20, (self.artifact_set, 2))

    def apply_4set(self, profiles, wearer) -> None:
        pass

    def apply_4set_dependent(self, all_hits, wearer):
        pass