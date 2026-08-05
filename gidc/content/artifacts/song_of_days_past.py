from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool, ask_int


class SongOfDaysPast(Artifact):
    """지난날의 노래
    2세트: 치유 보너스 +15%
    4세트: 장착 캐릭터가 파티 내 캐릭터 치유 시 6초 동안 지속되는 갈망 효과를 생성해 치유한 HP 회복량(초과치 포함)을 기록한다. 
    지속 시간 종료 시 갈망 효과는 「그때의 파도」 효과로 전환되어 아래 효과를 얻는다: 
    파티 내 자신의 현재 필드 위 캐릭터의 일반 공격, 강공격, 낙하 공격, 원소전투 스킬, 원소폭발이 적에게 명중 시 
    갈망 효과가 기록한 회복량의 8%에 기반해 주는 피해가 증가한다. 「그때의 파도」는 5회 발동 또는 10초 후 사라진다. 
    한 번의 갈망 효과는 회복량을 최대 15,000pt 기록하며 동시에 최대 1개만 존재할 수 있으나, 
    여러 장착 캐릭터가 생성한 회복량을 기록할 수 있다. 장착 캐릭터가 대기 상태일 때도 해당 효과는 발동된다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("healing_bonus", 0.15, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        if ask_bool("[지난날의 노래 4세트] '그리운 회상' 버프 활성?"):
            recorded = ask_int("[지난날의 노래 4세트] 기록된 치유량 (pt)", 0, 15000)
            for hit in all_hits[wearer].values():
                hit.add("flat_dmg_bonus", recorded * 0.08, (self.artifact_set, 4),
                        note="그때의 파도")
