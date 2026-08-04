from gidc.core.artifact import Artifact


class EmblemOfSeveredFate(Artifact):
    """절연의 기치
    2세트: 원소 충전 효율 +20%
    4세트: 원소폭발로 주는 피해가 원소 충전 효율의 25%만큼 증가한다. 해당 방식으로 최대 75%까지 증가할 수 있다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("energy_recharge", 0.20, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        pass

    def apply_4set_dependent(self, all_hits, wearer) -> None:
        # 원소 충전 효율을 **읽는 함수**로 넘긴다(지연 기여) — 장비 패시브는 캐릭터
        # 버프와 같은 단계에서 교차 실행되므로, 지금 읽으면 뒤에 오는 충전 효율 버프를
        # 놓친다. 히트마다 값이 다를 수 있어 람다에 히트를 기본 인자로 묶는다.
        for hit in all_hits[wearer].values():
            hit.add("burst_dmg_bonus",
                    lambda h=hit: min(h.energy_recharge * 0.25, 0.75),
                    (self.artifact_set, 4))
