from gidc.core.artifact import Artifact
from gidc.prompt import ask_choice


class ArchaicPetra(Artifact):
    """유구한 반암
    2세트: 바위 원소 피해 보너스 +15%
    4세트: 결정 반응으로 생성된 결정 조각을 획득하거나 달 결정 반응 발동 시, 파티 내 모든 캐릭터는 해당 원소 피해 보너스를 35% 획득한다. 
    지속 시간: 10초. 이러한 효과로 1가지의 원소 피해 보너스만 획득할 수 있다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("geo_dmg_bonus", 0.15, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        options = ['없음', '불', '물', '얼음', '번개']
        fields  = [None, 'pyro_dmg_bonus', 'hydro_dmg_bonus',
                   'cryo_dmg_bonus', 'electro_dmg_bonus']
        idx = ask_choice("[유구한 반암 4세트] 흡수한 결정 조각 원소", options)
        field = fields[idx]
        if field:
            setattr(all_hits, field, getattr(all_hits, field) + 0.35)

    def apply_4set_dependent(self, all_hits, wearer):
        pass
