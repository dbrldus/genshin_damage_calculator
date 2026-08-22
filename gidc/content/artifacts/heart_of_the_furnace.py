from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class HeartOfTheFurnace(Artifact):
    """용광로가 빚은 심장
    2세트: 공격력 +18%
    4세트: 장착 캐릭터가 별빛 반응(별 초전도/별 확산)을 발동하거나 별빛 반응 피해를
    준 후 12초 동안 착용자 공격력이 12% 증가하고, 파티 내 모든 캐릭터가 주는
    별빛 반응 피해가 50% 증가한다. 장착 캐릭터가 대기 상태여도 발동하며, 동명 세트가
    만든 피해 보너스는 중첩되지 않는다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", 0.18, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        if not ask_bool(
            "[용광로가 빚은 심장 4세트] 별빛 반응(별 초전도/별 확산)을 발동하거나 "
            "별빛 반응 피해를 준 후 12초 이내? (대기 상태 포함)"
        ):
            return

        for hit in all_hits[wearer].values():
            hit.add("atk_pct", 0.12, (self.artifact_set, 4), note="별빛 반응 발동")

        source = (self.artifact_set, 4)
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.apply_unique_buff(source, "stellar_conduct_bonus", 0.50)
                hit.apply_unique_buff(source, "stellar_swirl_bonus", 0.50)

    def apply_4set_dependent(self, all_hits, wearer):
        pass
