from gidc.core.weapon import Weapon
from gidc.core.party_state import has_hexerei_rite
from gidc.core.profile import SkillType
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_choice


def _ask_adjacent_on_field(all_hits, wearer):
    """「태양검」의 대상 — 장착 캐릭터를 제외한 현재 필드 위 캐릭터. 후보가 없으면 묻지 않는다
    (드래곤 슬레이어 영웅담과 같은 규약: 착용자 자신은 후보에서 빠진다)."""
    targets = [char for char in all_hits if char is not wearer]
    if not targets:
        return None
    options = [f"{char.name} ({char.element.value})" for char in targets] + ["없음"]
    idx = ask_choice("[검은 침식] 「태양검」 대상 — 장착 캐릭터 제외 현재 필드 위 캐릭터", options)
    return targets[idx] if idx < len(targets) else None


class AthameArtis(Weapon):
    """검은 침식 (Athame Artis) | 한손검 | 5성
    패시브: 태양의 불빛
    - 원소폭발로 주는 치명타 피해가 16%/20%/24%/28%/32% 증가한다. 원소폭발이 적에게 명중 시,
      「태양검」 효과를 획득한다: 공격력이 20%/25%/30%/35%/40% 증가하고, 장착 캐릭터를 제외한
      주변에 있는 현재 필드 위 캐릭터의 공격력이 16%/20%/24%/28%/32% 증가한다.
      지속 시간: 3초. 또한 파티가 「마도·비밀 의식」 효과 보유 시, 「태양검」 효과가 추가로
      75% 증가한다. 장착 캐릭터가 대기 상태일 때도 해당 효과가 발동된다.
    """

    _BURST_CRIT_DMG   = [0.16, 0.2, 0.24, 0.28, 0.32]
    _SELF_ATK_PCT     = [0.2, 0.25, 0.3, 0.35, 0.4]
    _ADJACENT_ATK_PCT = [0.16, 0.2, 0.24, 0.28, 0.32]

    # 마도·비밀 의식 보유 시 「태양검」 효과(양쪽 다) 추가 배율. 정련과 무관한 고정값이라
    # 수치 표에 넣지 않고 여기 상수로 둔다(일곱빛 계시의 _HEXEREI_SHARE와 같은 규약).
    _HEXEREI_AMP = 1.75

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.SWORD,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 검은 침식"

        # 효과 1: 원소폭발 치명타 피해 — 조건 없이 착용자의 폭발 히트에만 붙는다.
        # 전용 필드가 아니라 스킬 타입으로 골라 crit_dmg에 직접 더한다(빛나는 마음과 같은
        # 규약) — 폭발은 실제 SkillHit이라 skill_type으로 정확히 한정된다.
        for hit in all_hits[wearer].values():
            if hit.skill_type is SkillType.BURST:
                hit.add("crit_dmg", self._BURST_CRIT_DMG[r], label, note="태양의 불빛")

        # 효과 2 「태양검」. 원소폭발이 적에게 명중해야 트리거되므로 로테이션이 정한다 — 묻는다.
        # 대기 상태에서도 발동하므로 필드 등장 여부는 따로 묻지 않는다.
        if not ask_bool("[검은 침식] 원소폭발 적 명중 후 3초 이내 (태양검) 여부"):
            return

        # 마도·비밀 의식은 파티 구성(마도 2명 이상)만으로 정해지는 고정 배율이라 스탯을
        # 읽지 않는다 — Phase 3에서 바로 확정해도 순서와 무관하다.
        amp = self._HEXEREI_AMP if has_hexerei_rite(all_hits) else 1.0

        # 착용자 자신의 공격력 — 제3자에게 뿌리지 않으므로 그냥 add.
        self_bonus = self._SELF_ATK_PCT[r] * amp
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", self_bonus, label, note="태양검")

        # 장착 캐릭터를 제외한 현재 필드 위 캐릭터 — 제3자 대상이라 동명 무기 간 비중첩
        # 규약을 지키려면 apply_unique_buff로 제출한다.
        target = _ask_adjacent_on_field(all_hits, wearer)
        if target is None:
            return
        adjacent_bonus = self._ADJACENT_ATK_PCT[r] * amp
        for hit in all_hits[target].values():
            hit.apply_unique_buff(label, "atk_pct", adjacent_bonus)

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 「태양검」 지속 시간 3초 — 트리거 후 실제로 그 창 안에서 히트가 나가는지는
    #   로테이션 몫이라 위 질문 하나로 대신한다.
