from gidc.core.artifact import Artifact
from gidc.enums import Element
from gidc.prompt import ask_choice

# 확산 가능한 원소 → SkillHit 내성 감소 필드
_SWIRLABLE_RES_FIELD: dict[Element, str] = {
    Element.PYRO:    "pyro_res_reduction",
    Element.HYDRO:   "hydro_res_reduction",
    Element.CRYO:    "cryo_res_reduction",
    Element.ELECTRO: "electro_res_reduction",
}


class ViridescentVenerer(Artifact):
    """청록색 그림자
    2세트: 바람 원소 피해 보너스 +15%
    4세트: 확산 반응이 주는 피해가 60% 증가한다. 확산되는 원소 타입에 따라 피해 범위 내 적의 해당 원소의 내성이 40% 감소한다. 지속 시간: 10초
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("anemo_dmg_bonus", 0.15, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        # 확산 반응 피해 증가는 장착 캐릭터 본인의 확산에만 적용된다.
        for hit in all_hits[wearer].values():
            hit.add("swirl_bonus", 0.60, (self.artifact_set, 4))

        elements = list(_SWIRLABLE_RES_FIELD)
        idx = ask_choice(
            "[청록색 그림자 4세트] 확산된 원소",
            ["없음"] + [e.value for e in elements],
        )
        if idx == 0:
            return

        # 내성 감소는 적에게 걸리는 디버프이므로 파티 전원의 피해에 적용되며,
        # 동명 세트끼리는 중첩되지 않는다. 다만 착용자마다 확산시킨 원소가 다를 수 있으므로
        # 원소 필드별로 따로 잡는다 (불 확산 + 얼음 확산이면 둘 다 -40%).
        field = _SWIRLABLE_RES_FIELD[elements[idx - 1]]
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.apply_unique_buff((self.artifact_set, 4), field, -0.40)

    def apply_4set_dependent(self, all_hits, wearer):
        pass
