from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class ObsidianCodex(Artifact):
    """흑요석 비전
    2세트: 밤혼 가호 상태의 장착 캐릭터가 필드 위에 있을 시, 주는 피해가 15% 증가한다.
    4세트: 장착 캐릭터가 필드 위에서 밤혼을 1pt 소모한 후, 치명타 확률이 40% 증가한다. 지속시간: 6초. 해당 효과는 1초마다 최대 1회 발동된다.
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        if ask_bool("[흑요석 비전 2세트] 온필드 밤혼 가호 상태?"):
            for hit in all_hits[wearer].values():
                hit.add("all_dmg_bonus", 0.15, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        if ask_bool("[흑요석 비전 4세트] 밤혼 소모"):
            for hit in all_hits[wearer].values():
                hit.add("crit_rate", 0.40, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass