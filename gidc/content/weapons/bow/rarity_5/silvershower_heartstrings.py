from gidc.core.weapon import Weapon
from gidc.core.profile import SkillType
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool, ask_int


class SilvershowerHeartstrings(Weapon):
    """심금을 울리는 하얀 비 (Silvershower Heartstrings) | 활 | 5성
    패시브: 드리아스의 야상곡
    - 장착 캐릭터가 "축복" 효과를 획득한다. 1/2/3 스택의 축복 효과 보유 시, 최대
      HP가 12/15/18/21/24%·24/30/36/42/48%·40/50/60/70/80% 증가한다. 원소전투 스킬
      발동 시(25초 지속), 생명의 계약 증가 시(25초 지속), 치유 진행 시(20초 지속)
      각각 1스택 획득한다.
    - "축복" 3스택 보유 시 원소폭발의 치명타 확률이 28/35/42/49/56% 증가한다. 해당
      효과는 축복이 3스택 미만이 된 4초 후에 사라진다.
    """

    _HP_STACK1       = [0.12, 0.15, 0.18, 0.21, 0.24]
    _HP_STACK2       = [0.24, 0.3, 0.36, 0.42, 0.48]
    _HP_STACK3       = [0.4, 0.5, 0.6, 0.7, 0.8]
    _BURST_CRIT_RATE = [0.28, 0.35, 0.42, 0.49, 0.56]

    # 스택 수 → 그 스택에서의 배율표. 스택마다 「추가분」이 아니라 보유 스택 수에 대한
    # 누적 총량이 그대로 게임 표기값이다(안개를 가르는 회광 등과 같은 구조).
    _STACK_TABLE = (_HP_STACK1, _HP_STACK2, _HP_STACK3)

    _MAX_STACKS = 3

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.BOW,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.HP_PCT,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 심금을 울리는 하얀 비"
        hits  = all_hits[wearer].values()

        # 효과 1 「축복」. 획득 경로가 셋(원소전투 스킬 발동/생명의 계약 증가/치유
        # 진행)이고 경로마다 지속 시간이 다르지만, 묻는 것은 **현재 보유 스택 수**
        # 하나다 — 안개를 가르는 회광·비뢰의 고동과 같은 이유로, 어느 경로로 몇
        # 스택이 쌓였는지가 아니라 지금 몇 스택이 살아 있는지만 히트 단가에 들어간다.
        stacks = ask_int(
            "[심금을 울리는 하얀 비] 「축복」 스택 수 (원소전투 스킬 발동 25초/생명의 "
            f"계약 증가 25초/치유 진행 20초 시 1스택, 최대 {self._MAX_STACKS})",
            0, self._MAX_STACKS,
        )
        if stacks:
            bonus = self._STACK_TABLE[stacks - 1][r]
            for hit in hits:
                hit.add("hp_pct", bonus, label, note="축복")

        # 효과 2: 원소폭발 치명타 확률. 3스택 도달 자체가 아니라 「3스택 미만이 된 지
        # 4초 이내」까지 유지되는 히스테리시스 조건이라 스택 수 하나로 결정되지
        # 않는다 — 별도 질문으로 받는다.
        if ask_bool(
            "[심금을 울리는 하얀 비] 원소폭발 치명타 확률 보너스 활성 여부 "
            "(「축복」 3스택 보유 중이거나, 3스택 미만이 된 지 4초 이내)"
        ):
            for hit in hits:
                if hit.skill_type is SkillType.BURST:
                    hit.add("crit_rate", self._BURST_CRIT_RATE[r], label, note="축복 3스택")
