from gidc.core.weapon import Weapon
from gidc.core.profile import SkillType
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class LightOfFoliarIncision(Weapon):
    """잎을 가르는 빛 (Light of Foliar Incision) | 한손검 | 5성
    패시브: 하얀 달 가지
    - 치명타 확률이 4%/5%/6%/7%/8% 증가한다. 일반 공격으로 적에게 원소 피해를 준 후,
      일반 공격과 원소전투 스킬의 주는 피해가 원소 마스터리의 120%/150%/180%/210%/240%만큼
      증가하는 「가지치기」 효과를 획득한다. 해당 효과는 28회 발동하거나 12초가 지나면
      사라진다. 「가지치기」 효과는 12초마다 최대 1회 획득할 수 있다
    """

    _CRIT_RATE  = [0.04, 0.05, 0.06, 0.07, 0.08]
    _EM_DMG_PCT = [1.2, 1.5, 1.8, 2.1, 2.4]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.SWORD,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 잎을 가르는 빛"

        # 효과 1: 치명타 확률 — 조건 없이 착용자에게만 붙는다.
        for hit in all_hits[wearer].values():
            hit.add("crit_rate", self._CRIT_RATE[r], label, note="하얀 달 가지")

        # 효과 2 「가지치기」의 트리거만 여기서 받는다. 일반 공격 원소 피해 명중 여부와
        # 12초 재발동 제한은 로테이션 몫이라 묻는다 — 실제 배율은 착용자의 **최종** 원소
        # 마스터리를 읽어야 하므로 apply_passive_dependent(Phase 5)에서 계산한다.
        self._pruning = ask_bool(
            "[잎을 가르는 빛] 일반 공격 원소 피해 명중 후 12초 이내 (가지치기) 여부"
        )

    # ── 「가지치기」 — 착용자의 최종 원소 마스터리 기반 (방식 B) ──────────────
    # 「피해가 원소 마스터리의 N%만큼 증가」는 원마를 다시 %나 원마로 재변환하는 효과가
    # 아니라 원마에 비례한 몫을 피해에 직접 더하는 효과다(시틀라리 A4/C1과 같은 문구·같은
    # 판단) — em_from_flat이 아니라 elemental_mastery를 그대로 읽고, %-보너스 풀이
    # 아니라 flat_dmg_bonus로 차원 변환해 넣는다.
    def apply_passive_dependent(self, all_hits, wearer) -> None:
        if not self._pruning:
            return
        r     = self.refinement - 1
        label = "무기: 잎을 가르는 빛"

        # 값이 아니라 **읽는 함수**로 넘긴다(지연 기여) — 이 단계에서 다른 캐릭터가 아직
        # 원소 마스터리를 더하는 중일 수 있어, 지금 확정하면 파티 멤버 순서가 결과를 바꾼다.
        source_hit = next(iter(all_hits[wearer].values()))
        bonus = lambda: source_hit.elemental_mastery * self._EM_DMG_PCT[r]

        for hit in all_hits[wearer].values():
            if hit.skill_type in (SkillType.NORMAL_ATK, SkillType.SKILL):
                hit.add("flat_dmg_bonus", bonus, label, note="가지치기")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 28회 발동 제한과 12초 지속·재발동 제한 — 트리거 후 실제로 그 창 안에서 몇 번
    #   실리는지는 로테이션 몫이라 위 질문 하나로 대신한다.
