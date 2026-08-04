from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class DeepwoodMemories(Artifact):
    """숲의 기억
    2세트: 풀 원소 피해 보너스 +15%
    4세트: 원소전투 스킬 또는 원소폭발 공격에 명중된 적은 풀 원소 내성이 30% 감소한다. 지속 시간: 8초. 
    장착 캐릭터가 대기 상태일 때도 해당 효과는 발동된다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("dendro_dmg_bonus", 0.15, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        # 내성 감소는 적에게 걸리는 디버프이므로 파티 전원의 피해에 적용되며,
        # 동명 세트끼리는 중첩되지 않는다. 고정값이라 다른 착용자가 이미 최대치를
        # 채웠다면 같은 질문을 반복하지 않는다.
        source = (self.artifact_set, 4)
        sample = next(iter(all_hits[wearer].values()), None)
        if sample is not None and sample.buff_value(source, "dendro_res_reduction") <= -0.30:
            return

        if ask_bool("[숲의 기억 4세트] 원소 스킬/폭발 명중?"):
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.apply_unique_buff(source, "dendro_res_reduction", -0.30)

    def apply_4set_dependent(self, all_hits, wearer):
        pass