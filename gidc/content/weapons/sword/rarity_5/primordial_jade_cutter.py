from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType


class PrimordialJadeCutter(Weapon):
    """반암결록 (Primordial Jade Cutter) | 한손검 | 5성
    패시브: 수호자의 무구한 마음
    - HP가 20%/25%/30%/35%/40% 증가하고, 이 무기를 장착한 캐릭터 HP 최대치의
      1.2%/1.5%/1.8%/2.1%/2.4%에 해당하는 공격력 보너스를 획득한다
    """

    _HP_PCT     = [0.2, 0.25, 0.3, 0.35, 0.4]
    _ATK_HP_PCT = [0.012, 0.015, 0.018, 0.021, 0.024]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.SWORD,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 반암결록"

        # 효과 1: HP% — 조건 없이 착용자에게만 붙는다.
        for hit in all_hits[wearer].values():
            hit.add("hp_pct", self._HP_PCT[r], label, note="수호자의 무구한 마음")

    # ── 효과 2 — 착용자의 최종 HP 기반 (방식 B) ────────────────────────────
    # HP → 공격력은 공격력을 다시 재변환하는 효과가 아니라 HP에 비례한 몫을 그대로 얻는
    # 효과라(성현의 열쇠의 HP→EM과 같은 판단) atk_flat에 직접 출력한다. 자기 참조가 아니라
    # 순환 위험이 없지만, 파티 멤버 순서 의존을 피하려고 값이 아니라 읽는 함수로 넘긴다
    # (지연 기여) — 코어 정확성 가드도 즉시 값 변경만 감시하므로 지연 기여는 통과한다.
    def apply_passive_dependent(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 반암결록"

        source_hit = next(iter(all_hits[wearer].values()))
        bonus = lambda: source_hit.current_hp() * self._ATK_HP_PCT[r]
        for hit in all_hits[wearer].values():
            hit.add("atk_flat", bonus, label, note="수호자의 무구한 마음")
