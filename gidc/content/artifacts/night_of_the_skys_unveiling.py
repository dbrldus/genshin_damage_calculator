from gidc.core.artifact import Artifact
from gidc.enums import MoonsignLevel
from gidc.core.party_state import moonsign_level
from gidc.prompt import ask_bool

# 달빛 징조 단계별 치명타 확률 증가량
_MOONSIGN_CRIT_RATE = {
    MoonsignLevel.NONE:     0.0,
    MoonsignLevel.CRESCENT: 0.15,
    MoonsignLevel.FULL:     0.30,
}


class NightOfTheSkysUnveiling(Artifact):
    """하늘 경계가 드러난 밤
    2세트: 원소 마스터리 +80
    4세트: 주변에 있는 파티 내 캐릭터가 달빛 반응 발동 시, 장착 캐릭터가 필드 위에 있을 경우 4초 동안 지속되는 「월광·음모」 효과를 획득한다:
    파티의 달빛 징조가 초승/보름인 경우, 치명타 확률이 15%/30% 증가한다.
    파티 내 캐릭터가 서로 다른 「월광」 효과를 1개 보유할 때마다, 파티 내 모든 캐릭터가 발동한 달빛 반응으로 주는 피해가 10% 증가한다.
    「월광」으로 생성된 효과는 중첩되지 않는다
    """

    def apply_2set(self, all_hits, wearer) -> None:
        for hit in all_hits[wearer].values():
            hit.add("elemental_mastery", 80, (self.artifact_set, 2))

    def apply_4set(self, all_hits, wearer) -> None:
        # 「월광·음모」는 달빛 반응 발동 + 장착 캐릭터가 필드 위일 때만 획득한다.
        if not ask_bool("[하늘 경계가 드러난 밤 4세트] 온필드 캐릭터 달빛 반응 발동"):
            return

        # 치명타 확률 — 「월광·음모」를 획득한 장착 캐릭터 본인만.
        # 달빛 징조는 파티 구성에서 유도한다 (달빛 징조 캐릭터 수).
        crit_rate = _MOONSIGN_CRIT_RATE[moonsign_level(all_hits)]
        if crit_rate:
            for hit in all_hits[wearer].values():
                hit.add("crit_rate", crit_rate, (self.artifact_set, 4))

        # 달빛 반응 피해 — 파티 내 모든 캐릭터가 대상.
        # 「서로 다른 「월광」 1개당 10%」이므로, 이 세트의 「월광·음모」는 여러 명이
        # 착용해도 1개로만 계산된다. 반면 다른 세트의 「월광」은 각자 자기 키로 더해진다.
        source = (self.artifact_set, 4)
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.apply_unique_buff(source, "lunar_charged_bonus",     0.1)
                hit.apply_unique_buff(source, "lunar_bloom_bonus",       0.1)
                hit.apply_unique_buff(source, "lunar_crystallize_bonus", 0.1)

    def apply_4set_dependent(self, all_hits, wearer):
        pass
