from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class BlizzardStrayer(Artifact):
    """얼음바람 속에서 길잃은 용사
    2세트: 얼음 원소 피해 보너스 +15%
    4세트: 얼음 원소의 영향을 받은 적을 공격 시 치명타 확률이 20% 증가한다. 만약 적이 빙결 상태라면 치명타 확률이 추가로 20% 증가한다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("cryo_dmg_bonus", 0.15, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        cryo = ask_bool("[얼음바람 속에서 길잃은 용사 4세트] 적 얼음 원소 영향")
        frozen = ask_bool("[얼음바람 속에서 길잃은 용사 4세트] 적 빙결 상태")
        if frozen and cryo:
            for hit in all_hits[wearer].values():
                hit.add("crit_rate", 0.40, (self.artifact_set, 4))
        if cryo:
            for hit in all_hits[wearer].values():
                hit.add("crit_rate", 0.20, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass