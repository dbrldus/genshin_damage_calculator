from gidc.core.artifact import Artifact
from gidc.prompt import ask_bool


class GildedDreams(Artifact):
    """도금된 꿈
    2세트: 원소 마스터리 +80
    4세트: 원소 반응 발동 후 8초 동안, 장착 캐릭터는 원소 타입에 따라 다음 효과를 받는다:
    장착 캐릭터와 원소 타입이 같은 파티원 1명당 공격력이 14% 증가하고,
    장착 캐릭터와 원소 타입이 다른 파티원 1명당 원소 마스터리가 50 증가한다.
    상술한 두 가지 효과는 최대 3명의 캐릭터까지 계산한다.
    해당 세트 효과는 12초에 1번씩 발동할 수 있다. 장착 캐릭터가 대기 상태일 때도 해당 효과가 발동된다
    """

    RARITIES = (4, 5)

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("em_from_flat", 80, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        # 대기 상태에서도 발동하므로 필드 등장 여부는 묻지 않는다.
        if not ask_bool("[도금된 꿈 4세트] 원소 반응 발동 후 8초 이내?"):
            return

        # 파티 구성에서 자동 판정 — 장착 캐릭터 본인은 세지 않는다.
        same = diff = 0
        for char in all_hits:
            if char is wearer:
                continue
            if char.element is wearer.element:
                same += 1
            else:
                diff += 1

        # 각 효과는 최대 3명까지만 계산한다.
        same = min(same, 3)
        diff = min(diff, 3)

        for hit in all_hits[wearer].values():
            hit.add("atk_pct", same * 0.14, (self.artifact_set, 4))
            hit.add("em_from_flat", diff * 50, (self.artifact_set, 4))

    def apply_4set_dependent(self, all_hits, wearer):
        pass
