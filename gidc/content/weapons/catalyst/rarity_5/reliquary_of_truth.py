from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class ReliquaryOfTruth(Weapon):
    """진실의 함 (Reliquary of Truth) | 법구 | 5성
    패시브: 거짓말의 진심
    - 치명타 확률이 8%/10%/12%/14%/16% 증가한다. 원소전투 스킬 발동 시, 장착 캐릭터가
      「거짓의 비밀」 효과를 획득한다: 원소 마스터리가 80/100/120/140/160pt 증가한다,
      지속 시간: 12초. 장착 캐릭터가 적에게 달 개화 반응 피해를 줄 시, 장착 캐릭터가
      「진실의 달」 효과를 획득한다: 치명타 피해가 24%/30%/36%/42%/48% 증가한다, 지속
      시간: 4초. 「거짓의 비밀」 효과와 「진실의 달」 효과가 동시에 존재할 경우, 해당
      효과가 각각 50% 증가한다
    """

    _CRIT_RATE_BONUS   = [0.08, 0.1, 0.12, 0.14, 0.16]
    _EM_PER_SECRET     = [80, 100, 120, 140, 160]
    _CRIT_DMG_PER_MOON = [0.24, 0.3, 0.36, 0.42, 0.48]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 진실의 함"
        hits  = all_hits[wearer].values()

        # 효과 1: 치명타 확률 — 조건 없이 착용자에게만 붙는다.
        for hit in hits:
            hit.add("crit_rate", self._CRIT_RATE_BONUS[r], label, note="거짓말의 진심")

        # 효과 2·3 「거짓의 비밀」(EM)·「진실의 달」(치명타 피해) — 둘 다 착용자 자신에게만
        # 붙고, 트리거(스킬 발동/달개화 반응 피해)가 로테이션이 정하므로 각각 물어서
        # 받는다. 둘이 동시에 존재하면 각 효과가 50% 더 커진다(밤을 엮는 거울처럼 별도
        # 버프를 새로 얹는 게 아니라, 기존 두 효과 자체가 커지는 조건이다).
        secret = ask_bool(
            "[진실의 함] 「거짓의 비밀」 활성 여부 (원소전투 스킬 발동, 12초 지속)"
        )
        moon = ask_bool(
            "[진실의 함] 「진실의 달」 활성 여부 (적에게 달개화 반응 피해, 4초 지속)"
        )
        multiplier = 1.5 if (secret and moon) else 1.0

        if secret:
            for hit in hits:
                hit.add("em_from_flat", self._EM_PER_SECRET[r] * multiplier, label, note="거짓의 비밀")
        if moon:
            for hit in hits:
                hit.add("crit_dmg", self._CRIT_DMG_PER_MOON[r] * multiplier, label, note="진실의 달")
