from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class CashflowSupervision(Weapon):
    """현금 흐름 감독 (Cashflow Supervision) | 법구 | 5성
    패시브: 황금 혈조
    - 공격력이 16/20/24/28/32% 증가한다. 현재 HP가 증가 또는 감소 시 일반 공격이 주는 피해가
      16/20/24/28/32%, 강공격이 주는 피해가 14/17.5/21/24.5/28% 증가하고, 별 초전도 반응 피해가
      14/17.5/21/24.5/28% 증가한다. 지속 시간: 4초. 최대 중첩수: 3스택. 0.3초마다 최대 1회
      발동한다. 3스택 상태인 경우, 공격 속도가 8/10/12/14/16% 증가한다
    """

    _ATK_PCT          = [0.16, 0.2, 0.24, 0.28, 0.32]
    _NA_DMG_PER_STACK = [0.16, 0.2, 0.24, 0.28, 0.32]
    _CA_DMG_PER_STACK = [0.14, 0.175, 0.21, 0.245, 0.28]
    _SC_DMG_PER_STACK = [0.14, 0.175, 0.21, 0.245, 0.28]
    _ATK_SPD_AT_MAX   = [0.08, 0.1, 0.12, 0.14, 0.16]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 3,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    _MAX_STACKS = 3

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 현금 흐름 감독"
        hits  = all_hits[wearer].values()

        for hit in hits:
            hit.add("atk_pct", self._ATK_PCT[r], label, note="황금 혈조")

        # 「HP가 증가 또는 감소 시」 스택. 사면의 「생명의 계약」과 같은 이유로 상태를 들고
        # 있지 않는다 — 무엇이 HP를 흔드는지는 캐릭터·성유물마다 다르고 로테이션 안에서
        # 몇 번 실렸는지도 유저 몫이다. 결과 스택 수만 묻는다.
        stacks = ask_int(
            "[현금 흐름 감독] HP 증감으로 쌓인 스택 수 (HP가 늘거나 줄 때마다 1스택,"
            f" 4초 지속, 0.3초마다 최대 1회, 최대 {self._MAX_STACKS})",
            0, self._MAX_STACKS,
        )
        if not stacks:
            return

        na_bonus = stacks * self._NA_DMG_PER_STACK[r]
        ca_bonus = stacks * self._CA_DMG_PER_STACK[r]
        sc_bonus = stacks * self._SC_DMG_PER_STACK[r]
        for hit in hits:
            hit.add("normal_atk_dmg_bonus", na_bonus, label, note="황금 혈조 스택")
            hit.add("charged_atk_dmg_bonus", ca_bonus, label, note="황금 혈조 스택")
            hit.add("stellar_conduct_bonus", sc_bonus, label, note="황금 혈조 스택")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 4초 지속 시간 · 0.3초마다 최대 1회 발동 — 결과 스택 수만 묻고 유지 여부는
    #   유저가 판단한다(사면·늑대의 무용담과 같다).
    # · 3스택 시 공격 속도 +8/10/12/14/16% — 이 계산기에 공격 속도 필드가 없다.
    #   히트 단가를 바꾸지 않고 로테이션에 히트를 몇 개 더 넣느냐의 문제다.
