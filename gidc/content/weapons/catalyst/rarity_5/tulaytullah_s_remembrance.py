from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_step


class TulaytullahSRemembrance(Weapon):
    """툴레이툴라의 기억 (Tulaytullah's Remembrance) | 법구 | 5성
    패시브: 파묻힌 사파이어의 눈물
    - 일반 공격 속도가 10/12.5/15/17.5/20% 증가한다. 원소전투 스킬 발동 후 14초 동안 1초마다
      일반 공격으로 주는 피해가 4.8/6/7.2/8.4/9.6% 증가한다. 일반 공격이 적을 명중한 후,
      일반 공격으로 주는 피해가 9.6/12/14.4/16.8/19.2% 증가한다. 해당 효과는 0.3초마다
      최대 1회 발동된다. 지속 시간 동안 일반 공격으로 주는 피해는 해당 효과로 최대
      48/60/72/84/96%까지 증가한다. 효과는 캐릭터 퇴장 시 사라지며, 원소전투 스킬을 다시
      발동하면 기존 효과는 사라진다
    """

    _NA_DMG_PER_TICK = [0.048, 0.06, 0.072, 0.084, 0.096]
    _NA_DMG_PER_HIT  = [0.096, 0.12, 0.144, 0.168, 0.192]
    _NA_DMG_CAP      = [0.48, 0.6, 0.72, 0.84, 0.96]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 3,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    # 두 트리거(1초 경과 틱 / 명중 틱)는 정련마다 정확히 2:1 비율이고(예: R1 4.8%·9.6%),
    # 상한도 항상 틱값의 정확히 10배다(48/4.8 = 60/6 = ... = 10). 그래서 "몇 틱"을 받는
    # 대신 틱값을 간격으로 하는 실제 버프량(%)을 ask_step으로 직접 받는다 — 두 트리거의
    # 배합을 몰라도 결과가 같고, 화면에 뜨는 숫자가 곧 정련별 실수치라 스펙과 바로
    # 대조된다. 상한이 곧 최댓값이라 ask_step의 max_val 자체가 캡이다.
    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 툴레이툴라의 기억"
        hits  = all_hits[wearer].values()
        tick  = self._NA_DMG_PER_TICK[r] * 100     # ask_step은 %값으로 받는다
        cap   = self._NA_DMG_CAP[r] * 100

        pct = ask_step(
            "[툴레이툴라의 기억] 「일반 공격 강화」로 실린 일반 공격 피해 증가량"
            " (스킬 발동 후 경과 1초당 1틱, 일반 공격 명중 시 2틱 가산)",
            0.0, cap, tick,
        )
        if not pct:
            return

        for hit in hits:
            hit.add("normal_atk_dmg_bonus", pct / 100, label, note="파묻힌 사파이어의 눈물")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 일반 공격 속도 +10/12.5/15/17.5/20% — 이 계산기에 공격 속도 필드가 없다.
    #   히트 단가를 바꾸지 않고 로테이션에 히트를 몇 개 더 넣느냐의 문제다.
    # · 14초 지속 시간·0.3초 재발동 제한·캐릭터 퇴장/스킬 재발동 시 초기화 — 단계 수만
    #   묻고 유지 여부는 유저가 판단한다.
