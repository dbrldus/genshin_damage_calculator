from gidc.core.weapon import Weapon
from gidc.core.profile import SkillType
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class AstralVulturesCrimsonPlumage(Weapon):
    """붉은 깃 별독수리 (Astral Vulture's Crimson Plumage) | 활 | 5성
    패시브: 동공 속 달무리
    - 확산 반응 발동 후 12초 동안, 공격력이 24/30/36/42/48% 증가한다.
    - 파티 내에 장착 캐릭터와 원소 타입이 다른 캐릭터가 최소 1/2명 있을 시, 강공격
      피해가 20/25/30/35/40%·48/60/72/84/96% 증가하고 원소폭발 피해가
      10/12.5/15/17.5/20%·24/30/36/42/48% 증가한다.
    """

    _ATK_PCT         = [0.24, 0.3, 0.36, 0.42, 0.48]
    _CA_DMG_TIER1    = [0.2, 0.25, 0.3, 0.35, 0.4]
    _CA_DMG_TIER2    = [0.48, 0.6, 0.72, 0.84, 0.96]
    _BURST_DMG_TIER1 = [0.1, 0.125, 0.15, 0.175, 0.2]
    _BURST_DMG_TIER2 = [0.24, 0.3, 0.36, 0.42, 0.48]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.BOW,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 붉은 깃 별독수리"
        hits  = all_hits[wearer].values()

        # 효과 1: 확산 반응 발동 여부는 로테이션이 정하므로 묻는다.
        if ask_bool("[붉은 깃 별독수리] 확산 반응 발동 후 12초 이내 여부"):
            for hit in hits:
                hit.add("atk_pct", self._ATK_PCT[r], label, note="동공 속 달무리")

        # 효과 2: 이원소 파티원 수는 파티 구성만으로 정해지므로 묻지 않고 유도한다
        # (최초의 대마술·떠오르는 천일 밤의 꿈과 같은 판단). 착용자 자신은
        # 「장착 캐릭터와 원소 타입이 다른 캐릭터」에 해당하지 않으므로 제외한다.
        others = [c for c in all_hits if c is not wearer]
        diff_n = sum(1 for c in others if c.element is not wearer.element)

        if diff_n >= 2:
            ca_bonus, burst_bonus = self._CA_DMG_TIER2[r], self._BURST_DMG_TIER2[r]
        elif diff_n >= 1:
            ca_bonus, burst_bonus = self._CA_DMG_TIER1[r], self._BURST_DMG_TIER1[r]
        else:
            return

        for hit in hits:
            if hit.skill_type is SkillType.CHARGED_ATK:
                hit.add("charged_atk_dmg_bonus", ca_bonus, label, note="동공 속 달무리")
            elif hit.skill_type is SkillType.BURST:
                hit.add("burst_dmg_bonus", burst_bonus, label, note="동공 속 달무리")
