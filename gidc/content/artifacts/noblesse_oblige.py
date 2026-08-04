from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class NoblesseOblige(Artifact):
    """옛 왕실의 의식
    2세트: 원소 폭발 피해 보너스 +20%
    4세트: 원소 폭발 사용 후 12초 이내 공격력 +20%
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("burst_dmg_bonus", 0.20, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        # 파티 전체 버프라 동명 세트끼리 중첩되지 않는다. 고정값이므로 다른 착용자가
        # 이미 최대치를 채웠다면 같은 질문을 반복하지 않는다.
        source = (self.artifact_set, 4)
        sample = next(iter(all_hits[wearer].values()), None)
        if sample is not None and sample.buff_value(source, "atk_pct") >= 0.20:
            return

        if ask_bool("[옛 왕실의 의식 4세트] 원소 폭발 사용 후 12초 이내?"):
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.apply_unique_buff(source, "atk_pct", 0.20)

    def apply_4set_dependent(self, all_hits, wearer):
        pass