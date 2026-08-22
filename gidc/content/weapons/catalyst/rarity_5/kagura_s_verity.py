from gidc.core.weapon import Weapon
from gidc.core.profile import add_all_elemental_dmg_bonus
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class KaguraSVerity(Weapon):
    """카구라의 진의 (Kagura's Verity) | 법구 | 5성
    패시브: 카구라의 춤
    - 원소전투 스킬 발동 시, 「카구라의 춤」의 효과를 받아 해당 무기를 장착한 캐릭터의
      원소전투 스킬의 피해가 12/15/18/21/24% 증가하고, 별 초전도 반응 피해가
      12/15/18/21/24% 증가한다. 지속 시간: 16초. 최대 중첩수: 3회. 3스택 중첩 시
      모든 원소 피해 보너스를 12/15/18/21/24% 획득한다
    """

    _DMG_PER_STACK = [0.12, 0.15, 0.18, 0.21, 0.24]
    _ALL_DMG_AT_3  = [0.12, 0.15, 0.18, 0.21, 0.24]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    _MAX_STACKS = 3

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 카구라의 진의"
        hits  = all_hits[wearer].values()

        # 「카구라의 춤」 스택. 트리거는 스킬 발동 1개뿐이지만 16초 지속·최대 3회
        # 중첩이라 재발동 시점(로테이션)에 따라 실제로 몇 스택이 살아 있는지가 갈린다.
        # 그래서 결과 스택 수만 묻는다.
        stacks = ask_int(
            "[카구라의 진의] 「카구라의 춤」 스택 수 (원소전투 스킬 발동 시 1스택, 16초 지속,"
            f" 최대 {self._MAX_STACKS})",
            0, self._MAX_STACKS,
        )
        if not stacks:
            return

        bonus = stacks * self._DMG_PER_STACK[r]
        for hit in hits:
            hit.add("skill_dmg_bonus", bonus, label, note="카구라의 춤")
            # 별 초전도(ReactionType.STELLAR_CONDUCT) 반응 피해 보너스 — 초전도(SUPERCONDUCT)와
            # 다른 필드다. 산드로네처럼 별 초전도 직접 히트를 선언하는 캐릭터만 이 필드를
            # 실제로 읽는다.
            hit.add("stellar_conduct_bonus", bonus, label, note="카구라의 춤")

        # 3스택 전용 — 스택마다 쌓이는 게 아니라 3스택 도달 시 한 번만 붙는 별도 효과다.
        if stacks == self._MAX_STACKS:
            for hit in hits:
                add_all_elemental_dmg_bonus(hit, self._ALL_DMG_AT_3[r], label)
