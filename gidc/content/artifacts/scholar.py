from gidc.core.artifact import Artifact


class Scholar(Artifact):
    """학자
    2세트: 원소 충전 효율 +20%
    4세트: 원소 입자 혹은 원소 구슬 획득 시 파티 내 모든 활과 법구를 사용하는 캐릭터는 원소 에너지를 추가로 3pt 회복한다. 해당 효과는 3초마다 1번 발동한다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("energy_recharge", 0.20, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        pass

    def apply_4set_dependent(self, all_hits, wearer):
        pass