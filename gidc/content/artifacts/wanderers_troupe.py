from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool
from gidc.enums import WeaponType

class WanderersTroupe(Artifact):
    """대지를 유랑하는 악단
    2세트: 원소 마스터리 +80
    4세트: 법구·활 사용 시 강공격 피해 +35%
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("elemental_mastery", 80, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        if wearer.weapon_type == WeaponType.CATALYST or wearer.weapon_type == WeaponType.BOW:
            for hit in all_hits[wearer].values():
                hit.add("charged_atk_dmg_bonus", 0.35, (self.artifact_set, 4))
