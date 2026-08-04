from gidc.core.artifact import Artifact
from gidc.enums import MoonsignLevel
from gidc.core.party_state import moonsign_level
from gidc.prompt import ask_bool

# 달빛 징조 단계별 원소 마스터리 증가량
_MOONSIGN_EM = {
    MoonsignLevel.NONE:     0,
    MoonsignLevel.CRESCENT: 60,
    MoonsignLevel.FULL:     120,
}


class SilkenMoonsSerenade(Artifact):
    """달을 엮는 밤노래
    2세트: 원소 충전 효율 +20%
    4세트: 원소 피해를 줄 시, 8초 동안 지속되는 「월광·신앙」 효과를 획득한다:
    파티의 달빛 징조가 초승/보름인 경우, 파티 내 모든 캐릭터의 원소 마스터리가 60pt/120pt 증가한다.
    상술한 효과는 장착 캐릭터가 대기 상태일 때도 발동한다. 파티 내 캐릭터가 서로 다른 「월광」 효과를 1개 보유할 때마다,
    파티 내 모든 캐릭터가 발동한 달빛 반응으로 주는 피해가 10% 증가한다. 「월광」으로 생성된 효과는 중첩되지 않는다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("energy_recharge", 0.20, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        # 「월광」으로 생성된 효과는 중첩되지 않는다 — 여러 명이 이 세트를 착용해도
        # 「월광·신앙」은 1개다. 값이 파티 구성으로만 정해지므로 다른 착용자가 이미
        # 적용했다면 같은 질문을 반복하지 않는다.
        source = (self.artifact_set, 4)
        sample = next(iter(all_hits[wearer].values()), None)
        if sample is not None and sample.buff_value(source, "lunar_charged_bonus") >= 0.1:
            return

        # 대기 상태에서도 발동하므로 필드 등장 여부는 묻지 않는다.
        if not ask_bool("[달을 엮는 밤노래 4세트] 원소 피해 적중 후 8초 이내?"):
            return

        # 원소 마스터리 — 파티 내 모든 캐릭터가 대상.
        # 달빛 징조는 파티 구성에서 유도한다 (달빛 징조 캐릭터 수).
        mastery = _MOONSIGN_EM[moonsign_level(all_hits)]

        # 달빛 반응 피해 — 이 세트의 「월광·신앙」이 「월광」 1개로 계산된다.
        # 다른 세트가 부여하는 「월광」은 자기 키로 각자 자기 몫을 더한다.
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.apply_unique_buff(source, "elemental_mastery",       mastery)
                hit.apply_unique_buff(source, "lunar_charged_bonus",     0.1)
                hit.apply_unique_buff(source, "lunar_bloom_bonus",       0.1)
                hit.apply_unique_buff(source, "lunar_crystallize_bonus", 0.1)

    def apply_4set_dependent(self, all_hits, wearer):
        pass
