from gidc.core.weapon import Weapon
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_choice


class CrimsonMoonsSemblance(Weapon):
    """붉은 달의 형상 (Crimson Moon's Semblance) | 장병기 | 5성
    패시브: 핏빛 태양의 그림자
    - 강공격이 적에게 명중 시, HP 최대치의 25%에 해당하는 생명의 계약을 부여한다.
      해당 효과는 14초마다 최대 1회 발동한다.
    - 또한 장착 캐릭터가 생명의 계약 보유 시, 주는 피해가 12/16/20/24/28% 증가한다.
    - 만약 생명의 계약 수치가 HP 최대치의 30% 이상이면
      주는 피해가 24/32/40/48/56% 더 증가한다
    """

    _HELD_DMG = [0.12, 0.16, 0.20, 0.24, 0.28]   # 생명의 계약 보유
    _DEEP_DMG = [0.24, 0.32, 0.40, 0.48, 0.56]   # HP 최대치의 30% 이상일 때 **추가**

    # 생명의 계약 상태 — 뒤가 앞을 함의하므로 배타적인 하나로 받는다.
    _CONTRACT_STATES = (
        "없음",
        "보유 · HP 최대치의 30% 미만",
        "보유 · HP 최대치의 30% 이상",
    )

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.POLEARM,
            rarity        = 5,
            tier          = 3,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 붉은 달의 형상"

        # 두 단계가 「보유」와 「30% 이상」인데 뒤가 앞을 함의한다. ask_bool 둘로 받으면
        # 「30% 이상인데 미보유」라는 모순 입력이 가능해지므로 배타적인 상태 하나로 받는다.
        #
        # 이 무기 자신이 강공격당 HP 최대치의 25%를 부여한다 — 한 번으로는 30%에 못 미치므로
        # 두 번째 단계는 재발동(14초)이나 다른 출처(푸리나 등)가 필요하다. 그 수지는 로테이션
        # 몫이라 결과 상태만 묻는다.
        state = ask_choice(
            "[붉은 달의 형상] 장착 캐릭터의 생명의 계약 (강공격 명중 시 HP 최대치의 25% 부여)",
            list(self._CONTRACT_STATES),
        )
        if state == 0:
            return

        bonus = self._HELD_DMG[r]
        if state == 2:
            bonus += self._DEEP_DMG[r]

        for hit in all_hits[wearer].values():
            hit.add("all_dmg_bonus", bonus, label, note="핏빛 태양의 그림자")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 생명의 계약 부여(강공격 명중 시 HP 최대치의 25%, 14초 1회) — 이 엔진은 생명의 계약을
    #   상태로 들고 있지 않다(조화로운 공상의 단편 4세트도 스택을 직접 묻는다). 부여량과
    #   회복에 의한 소모를 따라가는 대신, 실제로 실린 결과 상태를 묻는다.
