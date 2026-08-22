from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool

_REACTION_DMG_FIELDS = ("bloom_bonus", "hyperbloom_bonus", "burgeon_bonus", "lunar_bloom_bonus")


class NightweaverSLookingGlass(Weapon):
    """밤을 엮는 거울 (Nightweaver's Looking Glass) | 법구 | 5성
    패시브: 천 년의 찬송가
    - 원소전투 스킬로 물 원소 또는 풀 원소 피해를 줄 경우, 장착 캐릭터가 「극북의 성언」
      효과를 획득한다: 원소 마스터리가 60/75/90/105/120pt 증가한다, 지속 시간: 4.5초.
      주변에 있는 파티 내 캐릭터가 달 개화 반응 발동 시, 장착 캐릭터가 「삭월의 시」
      효과를 획득한다: 원소 마스터리가 60/75/90/105/120pt 증가한다, 지속 시간: 10초.
      「극북의 성언」 효과와 「삭월의 시」 효과가 동시에 존재할 경우, 주변에 있는 파티 내
      모든 캐릭터가 발동한 개화 반응으로 주는 피해가 120%/150%/180%/210%/240%, 만개,
      발화 반응으로 주는 피해가 80%/100%/120%/140%/160%, 달 개화 반응으로 주는 피해가
      40%/50%/60%/70%/80% 증가한다. 해당 효과는 중첩되지 않는다. 장착 캐릭터가 대기
      상태일 때도 상술한 효과가 발동된다
    """

    _EM_PER_BUFF            = [60, 75, 90, 105, 120]
    _BLOOM_DMG              = [1.2, 1.5, 1.8, 2.1, 2.4]
    _HYPERBLOOM_BURGEON_DMG = [0.8, 1, 1.2, 1.4, 1.6]
    _LUNAR_BLOOM_DMG        = [0.4, 0.5, 0.6, 0.7, 0.8]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.ELEMENTAL_MASTERY,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 밤을 엮는 거울"
        wearer_hits = all_hits[wearer].values()

        # 「극북의 성언」·「삭월의 시」 — 둘 다 착용자 자신에게만 붙는 EM이고, 트리거가
        # 로테이션(스킬로 물/풀 피해를 줬는지, 파티 내 달개화가 최근 발동했는지)이 정하므로
        # 각각 물어서 받는다. 두 효과는 동시에 켜질 수 있고 값이 같아도 각자 더해진다
        # (동일 이름 효과가 아니라 서로 다른 이름의 버프다).
        aria = ask_bool(
            "[밤을 엮는 거울] 「극북의 성언」 활성 여부"
            " (원소전투 스킬로 물/풀 원소 피해, 4.5초 지속)"
        )
        if aria:
            for hit in wearer_hits:
                hit.add("em_from_flat", self._EM_PER_BUFF[r], label, note="극북의 성언")

        verse = ask_bool(
            "[밤을 엮는 거울] 「삭월의 시」 활성 여부"
            " (파티 내 캐릭터 달개화 반응 발동, 10초 지속)"
        )
        if verse:
            for hit in wearer_hits:
                hit.add("em_from_flat", self._EM_PER_BUFF[r], label, note="삭월의 시")

        # 두 효과가 동시에 존재할 때만 파티 전원(비중첩)에게 개화 계열 반응 피해 보너스.
        if not (aria and verse):
            return

        bonuses = dict(zip(
            _REACTION_DMG_FIELDS,
            (self._BLOOM_DMG[r], self._HYPERBLOOM_BURGEON_DMG[r],
             self._HYPERBLOOM_BURGEON_DMG[r], self._LUNAR_BLOOM_DMG[r]),
        ))
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                for field, value in bonuses.items():
                    hit.apply_unique_buff(label, field, value)
