from gidc.core.weapon import Weapon, WeaponSubStat
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class Azurelight(Weapon):
    """창백한 섬광 (Azurelight) | 한손검 | 5성 | 스커크 전용 무기
    패시브: 하얀 산의 선물
    - 원소전투 스킬 발동 후 12초 동안 공격력 +24/30/36/42/48%
    - 위 지속 시간 동안 장착 캐릭터의 원소 에너지가 0이 되면, 추가로
      공격력 +24/30/36/42/48%, 치명타 피해 +40/50/60/70/80%

    무기 효과는 전부 착용자에게만 적용된다 — 파티 버프가 없어 비중첩 처리가 필요 없다.
    """

    _ATK_PCT          = [0.24, 0.30, 0.36, 0.42, 0.48]
    _ZERO_ENERGY_ATK  = [0.24, 0.30, 0.36, 0.42, 0.48]
    _ZERO_ENERGY_CRIT = [0.40, 0.50, 0.60, 0.70, 0.80]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type = WeaponType.SWORD,
            base_atk    = 674,
            refinement  = refinement,
            sub_stat    = WeaponSubStat(StatType.CRIT_RATE, 22.1),
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 창백한 섬광"

        # 효과 1: 원소전투 스킬 발동 후 공격력 증가
        if not ask_bool("[창백한 섬광] 원소전투 스킬 발동 여부"):
            return

        for hit in all_hits[wearer].values():
            hit.add("atk_pct", self._ATK_PCT[r], label, note="하얀 산의 선물")

        # 효과 2: 위 지속 시간 동안 원소 에너지가 0이 되면 추가 증가.
        # 효과 1이 선행 조건이라 켜져 있을 때만 묻는다.
        # (스커크는 원소 에너지가 아니라 뱀의 계략으로 폭발을 쓰므로 에너지가 상시 0이다.)
        if not ask_bool("[창백한 섬광] 지속 시간 동안 원소 에너지 0 여부"):
            return

        for hit in all_hits[wearer].values():
            hit.add("atk_pct",  self._ZERO_ENERGY_ATK[r],  label, note="원소 에너지 0")
            hit.add("crit_dmg", self._ZERO_ENERGY_CRIT[r], label, note="원소 에너지 0")
