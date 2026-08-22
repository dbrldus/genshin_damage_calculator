from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class TomeOfTheEternalFlow(Weapon):
    """영원히 샘솟는 법전 (Tome of the Eternal Flow) | 법구 | 5성
    패시브: 영원한 파도
    - HP가 16/20/24/28/32% 증가한다. 현재 HP가 증가 혹은 감소 시 강공격이 주는 피해가
      14/18/22/26/30% 증가한다. 지속 시간: 4초. 최대 중첩수: 3회. 0.3초마다 최대 1회 발동한다.
      3스택을 달성하거나 3스택의 지속 시간이 갱신될 경우, 원소 에너지를 8/9/10/11/12pt
      회복한다. 해당 방식으로 원소 에너지를 12초마다 최대 1회 회복할 수 있다
    """

    _HP_PCT           = [0.16, 0.2, 0.24, 0.28, 0.32]
    _CA_DMG_PER_STACK = [0.14, 0.18, 0.22, 0.26, 0.3]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    _MAX_STACKS = 3

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 영원히 샘솟는 법전"
        hits  = all_hits[wearer].values()

        for hit in hits:
            hit.add("hp_pct", self._HP_PCT[r], label, note="영원한 파도")

        # 「HP가 증가 혹은 감소 시」 스택. 사면(생명의 계약)·현금 흐름 감독(황금 혈조)과 같은
        # 이유로 상태를 들지 않는다 — 결과 스택 수만 묻는다.
        stacks = ask_int(
            "[영원히 샘솟는 법전] HP 증감으로 쌓인 스택 수 (HP가 늘거나 줄 때마다 1스택,"
            f" 4초 지속, 0.3초마다 최대 1회, 최대 {self._MAX_STACKS})",
            0, self._MAX_STACKS,
        )
        if not stacks:
            return

        bonus = stacks * self._CA_DMG_PER_STACK[r]
        for hit in hits:
            hit.add("charged_atk_dmg_bonus", bonus, label, note="영원한 파도 스택")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 4초 지속 시간 · 0.3초마다 최대 1회 발동 — 결과 스택 수만 묻고 유지 여부는
    #   유저가 판단한다(사면·현금 흐름 감독과 같다).
    # · 3스택 달성/갱신 시 원소 에너지 8/9/10/11/12pt 회복(12초마다 최대 1회) — 로테이션
    #   빈도를 정하는 값이지 히트 단가에 들어갈 피해 항이 아니다.
