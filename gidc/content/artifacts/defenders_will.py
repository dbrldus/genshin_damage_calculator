from gidc.core.artifact import Artifact


class DefendersWill(Artifact):
    """수호자의 의지
    2세트: 방어력 +30%
    4세트: 파티 내에 다른 원소 타입의 자신의 캐릭터가 1명 존재할 때마다 자신은 대응하는 원소의 내성을 30% 획득한다
    """

    RARITIES = (3, 4)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("def_pct", 0.30, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        pass

    def apply_4set_dependent(self, all_hits, wearer):
        pass