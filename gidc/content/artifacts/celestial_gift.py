from gidc.core.artifact import Artifact
from gidc.enums import CharacterTrait, Element
from gidc.core.party_state import has_hexerei_rite
from gidc.prompt import ask_bool, ask_choice

# 원소 → SkillHit 피해 보너스 필드
_ELEMENT_DMG_FIELD: dict[Element, str] = {
    Element.PYRO:    "pyro_dmg_bonus",
    Element.HYDRO:   "hydro_dmg_bonus",
    Element.CRYO:    "cryo_dmg_bonus",
    Element.ELECTRO: "electro_dmg_bonus",
    Element.ANEMO:   "anemo_dmg_bonus",
    Element.GEO:     "geo_dmg_bonus",
    Element.DENDRO:  "dendro_dmg_bonus",
}


def _ask_on_field_member(all_hits, wearer):
    """파티원 중 현재 필드 위 캐릭터를 고르게 한다. 파티원이 1명뿐이면 묻지 않는다."""
    members = list(all_hits.keys())
    if len(members) == 1:
        return members[0]

    options = [
        f"{char.name} ({char.element.value})"
        + (" ← 장착 캐릭터" if char is wearer else "")
        for char in members
    ]
    idx = ask_choice("[하늘의 은총 4세트] 현재 필드 위 캐릭터", options)
    return members[idx]


class CelestialGift(Artifact):
    """하늘의 은총
    2세트: 원소 충전 효율+20%
    4세트: 장착 캐릭터가 마녀의 과제를 완료한 경우, 원소전투 스킬 발동 후 추가로 「천광의 인도」 효과를 획득한다:
    장착 캐릭터의 원소 타입에 따라 주변에 있는 파티 내 모든 캐릭터가 상응하는 원소 피해 보너스를 20% 획득한다. 지속 시간: 20초.
    장착 캐릭터가 대기 상태일 때도 상술한 효과가 발동되며, 동명의 성유물 세트가 생성한 피해 보너스 효과는 중첩되지 않는다.
    파티가 「마도·비밀 의식」 효과 보유 시, 「천광의 인도」 효과가 「속세의 송가」로 강화된다.
    장착 캐릭터의 원소 타입 외에도 현재 필드 위에 있는 파티 내 자신의 캐릭터의 원소 타입에 따라 주변에 있는 파티 내 모든 캐릭터가 상응하는 원소 피해 보너스를 획득하며,
    상술한 두 가지 원소 피해 보너스가 40%로 증가한다. 동명의 성유물 세트가 생성한 피해 보너스 효과는 중첩되지 않는다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("energy_recharge", 0.20, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        # 「마녀의 과제」를 완료한 캐릭터 = 마도 캐릭터.
        if not wearer.has_trait(CharacterTrait.HEXEREI):
            return
        # 대기 상태에서도 발동하므로 필드 등장 여부는 묻지 않는다.
        if not ask_bool("[하늘의 은총 4세트] 원소전투 스킬 발동 후 20초 이내?"):
            return

        # 「마도·비밀 의식」 보유 시 「천광의 인도」(20%) → 「속세의 송가」(40%)로 강화
        hexerei = has_hexerei_rite(all_hits)
        bonus = 0.40 if hexerei else 0.20

        # 장착 캐릭터의 원소 + (강화 시) 현재 필드 위 캐릭터의 원소.
        # 두 원소가 같으면 보너스는 하나로 취급된다.
        fields = {_ELEMENT_DMG_FIELD.get(wearer.element)}
        if hexerei:
            on_field = _ask_on_field_member(all_hits, wearer)
            fields.add(_ELEMENT_DMG_FIELD.get(on_field.element))
        fields.discard(None)  # 물리 등 매핑 없는 원소

        # 동명 세트가 생성한 피해 보너스는 중첩되지 않는다. 착용자마다 원소가 다를 수
        # 있으므로 원소 필드별로 최댓값을 잡는다.
        source = (self.artifact_set, 4)
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                for field in fields:
                    hit.apply_unique_buff(source, field, bonus)

    def apply_4set_dependent(self, all_hits, wearer):
        pass