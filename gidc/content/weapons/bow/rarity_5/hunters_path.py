from gidc.core.weapon import Weapon
from gidc.core.profile import SkillType, add_all_elemental_dmg_bonus
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class HuntersPath(Weapon):
    """사냥꾼의 길 (Hunter's Path) | 활 | 5성
    패시브: 짐승이 거니는 길의 끝
    - 모든 원소 피해 보너스를 12/15/18/21/24% 획득한다. 강공격으로 적 명중 후, 「무한
      사냥」을 획득한다: 강공격으로 주는 피해가 원소 마스터리 수치의
      160/200/240/280/320%만큼 증가한다. 해당 효과는 12회 발동 또는 10초 후 사라지고,
      12초마다 무한 사냥 효과를 최대 1회 획득할 수 있다
    """

    _ALL_ELEM_DMG  = [0.12, 0.15, 0.18, 0.21, 0.24]
    _CA_EM_DMG_PCT = [1.6, 2.0, 2.4, 2.8, 3.2]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.BOW,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 사냥꾼의 길"

        # 효과 1: 모든 원소 피해 보너스 — 조건 없이 착용자에게만 붙는다.
        for hit in all_hits[wearer].values():
            add_all_elemental_dmg_bonus(hit, self._ALL_ELEM_DMG[r], label)

        # 효과 2 「무한 사냥」의 트리거만 여기서 받는다. 강공격 명중 여부와 12초 재발동
        # 제한은 로테이션 몫이라 묻는다 — 실제 배율은 착용자의 **최종** 원소 마스터리를
        # 읽어야 하므로 apply_passive_dependent(Phase 5)에서 계산한다
        # (잎을 가르는 빛과 같은 구조).
        self._hunting = ask_bool(
            "[사냥꾼의 길] 강공격 명중 후 10초 이내 (무한 사냥) 여부"
        )

    # ── 「무한 사냥」 — 착용자의 최종 원소 마스터리 기반 (방식 B) ──────────────
    # 「피해가 원소 마스터리의 N%만큼 증가」는 원마를 다시 %나 원마로 재변환하는 효과가
    # 아니라 원마에 비례한 몫을 피해에 직접 더하는 효과다(잎을 가르는 빛과 같은 문구·
    # 같은 판단) — em_from_flat이 아니라 elemental_mastery를 그대로 읽고, %-보너스
    # 풀이 아니라 flat_dmg_bonus로 차원 변환해 넣는다.
    def apply_passive_dependent(self, all_hits, wearer) -> None:
        if not self._hunting:
            return
        r     = self.refinement - 1
        label = "무기: 사냥꾼의 길"

        # 값이 아니라 **읽는 함수**로 넘긴다(지연 기여) — 이 단계에서 다른 캐릭터가 아직
        # 원소 마스터리를 더하는 중일 수 있어, 지금 확정하면 파티 멤버 순서가 결과를 바꾼다.
        source_hit = next(iter(all_hits[wearer].values()))
        bonus = lambda: source_hit.elemental_mastery * self._CA_EM_DMG_PCT[r]

        for hit in all_hits[wearer].values():
            if hit.skill_type is SkillType.CHARGED_ATK:
                hit.add("flat_dmg_bonus", bonus, label, note="무한 사냥")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 12회 발동 제한과 10초 지속·12초 재발동 제한 — 트리거 후 실제로 그 창 안에서
    #   몇 번 실리는지는 로테이션 몫이라 위 질문 하나로 대신한다.
