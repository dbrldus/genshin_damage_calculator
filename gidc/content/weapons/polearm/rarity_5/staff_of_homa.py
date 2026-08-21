from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class StaffOfHoma(Weapon):
    """호마의 지팡이 (Staff of Homa) | 장병기 | 5성
    패시브: 자유의 붉은 나비
    - HP가 20/25/30/35/40% 증가하고, 이 무기를 장착한 캐릭터 HP 최대치의
      0.8/1/1.2/1.4/1.6%에 해당하는 공격력 보너스를 획득한다.
    - 이 무기를 장착한 캐릭터의 HP가 50% 미만일 경우, 공격력이 추가로 HP 최대치의
      1/1.2/1.4/1.6/1.8%만큼 증가한다
    """

    _HP_PCT            = [0.2, 0.25, 0.3, 0.35, 0.4]
    _ATK_HP_PCT        = [0.008, 0.01, 0.012, 0.014, 0.016]
    _LOW_HP_ATK_HP_PCT = [0.01, 0.012, 0.014, 0.016, 0.018]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.POLEARM,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 호마의 지팡이"

        # 효과 1: HP% — 조건 없이 착용자에게만 붙는다.
        for hit in all_hits[wearer].values():
            hit.add("hp_pct", self._HP_PCT[r], label, note="자유의 붉은 나비")

        # 효과 2의 「HP 50% 미만」 조건은 실시간 체력 상태라 파티 구성으로 유도되지
        # 않는다 — 묻는다. 실제 HP→공격력 환산은 apply_passive_dependent(Phase 5)에서
        # 최종 HP를 읽어 계산한다.
        self._low_hp = ask_bool("[호마의 지팡이] 장착 캐릭터 HP 50% 미만 여부")

    # ── 효과 2 — 착용자의 최종 HP 기반 (방식 B) ────────────────────────────
    # HP → 공격력은 반암결록과 같은 판단(공격력 재변환이 아니라 HP 비례 몫을 그대로
    # 얻는 효과)이라 atk_from_pct_share에 flat으로 출력한다. 재료는 convertible_hp()
    # — %-파생 HP 지분은 재료에서 뺀다. 순서 의존을 피하려고 값이 아니라 읽는 함수로
    # 넘긴다(지연 기여).
    def apply_passive_dependent(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 호마의 지팡이"

        source_hit = next(iter(all_hits[wearer].values()))
        bonus = lambda: source_hit.convertible_hp() * self._ATK_HP_PCT[r]
        for hit in all_hits[wearer].values():
            hit.add("atk_from_pct_share", bonus, label, note="자유의 붉은 나비")

        if not self._low_hp:
            return
        low_hp_bonus = lambda: source_hit.convertible_hp() * self._LOW_HP_ATK_HP_PCT[r]
        for hit in all_hits[wearer].values():
            hit.add("atk_from_pct_share", low_hp_bonus, label, note="HP 50% 미만")
