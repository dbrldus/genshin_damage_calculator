from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class EngulfingLightning(Weapon):
    """예초의 번개 (Engulfing Lightning) | 장병기 | 5성
    패시브: 불시의 꿈·영원한 부뚜막
    - 원소 충전 효율이 100%를 초과할 경우, 초과된 부분의 28/35/42/49/56%만큼 공격력이
      증가하며, 해당 방식을 통해 최대 80/90/100/110/120% 증가할 수 있다.
    - 원소폭발 발동 후 12초 동안 원소 충전 효율이 30/35/40/45/50% 증가한다
    """

    _ATK_PCT_RATIO  = [0.28, 0.35, 0.42, 0.49, 0.56]
    _ATK_PCT_CAP    = [0.8, 0.9, 1, 1.1, 1.2]
    _BURST_ER_BONUS = [0.3, 0.35, 0.4, 0.45, 0.5]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.POLEARM,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.ENERGY_RECHARGE,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 예초의 번개"

        # 효과 2 「영원한 부뚜막」: 원소폭발 발동 후 12초 동안 원소 충전 효율 증가.
        # 트리거(원소폭발 명중)와 12초 지속 여부는 로테이션이 정하므로 묻는다 — 파티
        # 구성으로 유도되지 않는다. 여기서 건 ER은 단순 가산이라 효과 1이 나중에
        # apply_passive_dependent(Phase 5)에서 최종 ER을 읽을 때 이미 반영돼 있다.
        if ask_bool("[예초의 번개] 원소폭발 발동 후 12초 이내 (영원한 부뚜막) 여부"):
            for hit in all_hits[wearer].values():
                hit.add("energy_recharge", self._BURST_ER_BONUS[r], label, note="영원한 부뚜막")

    # ── 효과 1 「불시의 꿈」 — 착용자의 최종 원소 충전 효율 기반 (방식 B) ────────
    # 100%를 초과한 원소 충전 효율의 일부만큼 공격력이 **증가**한다 — EM→공격력
    # (적색 사막의 지팡이)과 달리 재료와 출력이 둘 다 비율(%)이라 결과 자체가 이미
    # 공격력 퍼센트다. 그래서 atk_from_pct_share(값 전환)가 아니라 atk_pct에 바로
    # 쓴다. 원소 충전 효율은 스탯 하나(base/pct/flat 분해가 없다)라 다른 캐릭터·
    # 세트의 기여가 어느 단계에서 들어오든 여기서 최종값을 읽으면 전부 반영된다 —
    # 그래서 값이 아니라 **읽는 함수**를 넘긴다(순서 무관 보장).
    def apply_passive_dependent(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 예초의 번개"
        cap   = self._ATK_PCT_CAP[r]

        for hit in all_hits[wearer].values():
            bonus = lambda h=hit: min(
                max(h.energy_recharge - 1.0, 0.0) * self._ATK_PCT_RATIO[r], cap
            )
            hit.add("atk_pct", bonus, label, note="불시의 꿈")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 「영원한 부뚜막」 12초 지속 시간 — 폭발 이후 지속 중인지만 묻고, 재발동
    #   타이밍과 지속 시간 관리는 유저가 판단한다.
