from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class TenacityOfTheMillelith(Artifact):
    """견고한 천암
    2세트: HP +20%
    4세트: 원소전투 스킬이 적을 명중하면 파티 내 주변 모든 캐릭터의 공격력이 20% 증가하고, 보호막 강화 효과가 30% 증가한다. 지속 시간: 3초. 
    해당 효과는 0.5초마다 최대 1회 발동되며, 해당 성유물을 장착 한 캐릭터가 대기 상태 일 때도 발동된다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("hp_pct", 0.20, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        # 파티 전체 버프라 동명 세트끼리 중첩되지 않는다. 고정값이므로 다른 착용자가
        # 이미 최대치를 채웠다면 같은 질문을 반복하지 않는다.
        source = (self.artifact_set, 4)
        sample = next(iter(all_hits[wearer].values()), None)
        if sample is not None and sample.buff_value(source, "atk_pct") >= 0.20:
            return

        if ask_bool("[견고한 천암 4세트] 원소 스킬 명중 후 3초 이내?"):
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.apply_unique_buff(source, "atk_pct", 0.20)

    def apply_4set_dependent(self, all_hits, wearer):
        pass