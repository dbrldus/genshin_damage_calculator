from gidc.core.artifact import Artifact


class OceanHuedClam(Artifact):
    """바다에 물든 거대 조개
    2세트: 치유 보너스 +15%
    4세트: 해당 성유물 세트를 장착한 캐릭터가 파티 내 캐릭터를 치유하면, 
    3초간 지속되는 바다에 물든 거품을 생성해 치유한 HP의 회복량을 기록한다(초과된 수치 포함). 
    지속 시간 종료 후 바다에 물든 거품이 폭발해 주변의 적에게 누적 회복량의 90%에 해당하는 피해를 준다
    (해당 피해 계산 방식은 감전, 초전도 등 원소 반응의 방식과 같지만, 원소 마스터리, 레벨 또는 반응 피해 보너스 효과의 영향을 받지 않는다). 
    3.5초마다 최대 1개의 바다에 물든 거품이 생성되며, 바다에 물든 거품은 초과한 부분의 치유량을 포함해 최대 30,000pt의 회복량을 기록할 수 있다. 
    자신의 파티에 바다에 물든 거품은 동시에 1개만 존재할 수 있다. 해당 성유물 세트를 장착한 캐릭터가 대기 상태일 때도 해당 효과가 발동한다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("healing_bonus", 0.15, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        pass

    def apply_4set_dependent(self, all_hits, wearer):
        pass