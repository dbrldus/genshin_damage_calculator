from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool
from gidc.enums import WeaponType


class GladiatorsFinale(Artifact):
    """검투사의 피날레
    2세트: 공격력 +18%
    4세트: 해당 성유물 세트를 장착한 캐릭터가 한손검, 양손검, 장병기를 사용 시 캐릭터의 일반 공격으로 주는 피해가 35% 증가한다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", 0.18, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        condition = wearer.weapon_type == WeaponType.SWORD or \
            wearer.weapon_type == WeaponType.CLAYMORE or \
            wearer.weapon_type == WeaponType.POLEARM
        
        if condition:
            for hit in all_hits[wearer].values():
                hit.add("normal_atk_dmg_bonus", 0.35, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass