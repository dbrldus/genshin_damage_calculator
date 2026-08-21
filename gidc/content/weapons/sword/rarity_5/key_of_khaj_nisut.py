from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class KeyOfKhajNisut(Weapon):
    """성현의 열쇠 (Key of Khaj-Nisut) | 한손검 | 5성
    패시브: 모래바다에 잠긴 서사시
    - HP가 20%/25%/30%/35%/40% 증가한다. 원소전투 스킬이 적을 명중하면 20초 동안 지속되는
      「웅장한 시편」 효과를 획득한다: 장착한 캐릭터 HP 최대치의 0.12%/0.15%/0.18%/0.21%/0.24%
      만큼 원소 마스터리를 획득한다. 해당 효과는 0.3초마다 최대 1회 발동할 수 있다.
      최대 중첩수: 3스택. 해당 효과가 3스택 중첩 또는 3스택 중첩 지속 시간이 갱신되면 장착한
      캐릭터 HP 최대치의 0.2%/0.25%/0.3%/0.35%/0.4%만큼 근처 파티 내 모든 캐릭터의 원소
      마스터리가 증가한다. 지속 시간: 20초
    """

    _HP_PCT       = [0.2, 0.25, 0.3, 0.35, 0.4]
    _SELF_EM_PCT  = [0.0012, 0.0015, 0.0018, 0.0021, 0.0024]
    _PARTY_EM_PCT = [0.002, 0.0025, 0.003, 0.0035, 0.004]

    _MAX_STACKS = 3

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.SWORD,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.HP_PCT,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 성현의 열쇠"

        # 효과 1: HP% — 조건 없이 착용자에게만 붙는다.
        for hit in all_hits[wearer].values():
            hit.add("hp_pct", self._HP_PCT[r], label, note="모래바다에 잠긴 서사시")

        # 효과 2·3의 스택 수만 여기서 받는다. 원소전투 스킬 명중 여부와 0.3초 재발동
        # 제한은 로테이션 몫이라 묻는다 — 실제 EM 환산은 착용자의 **최종** HP를 읽어야
        # 하므로 apply_passive_dependent(Phase 5)에서 계산한다.
        #
        # 3스택 파티 전원 몫은 「3스택 중첩 또는 3스택 지속 시간 갱신」이 조건이라, 3스택
        # 자체가 이미 그 성립을 함의한다 — 따로 묻지 않고 스택 수 3에서 유도한다.
        self._stacks = ask_int(
            "[성현의 열쇠] 「웅장한 시편」 스택 수 (원소전투 스킬 명중 시 1스택, 0.3초마다"
            f" 최대 1회, 20초 지속, 최대 {self._MAX_STACKS})",
            0, self._MAX_STACKS,
        )

    # ── 효과 2·3 — 착용자의 최종 HP 기반 (방식 B) ────────────────────────────
    # HP → EM은 EM을 다시 재변환하는 효과가 아니라 HP에 비례한 몫을 그대로 얻는 효과라
    # elemental_mastery에 직접 출력한다. 코어 정확성 가드는 ATK/DEF/HP 즉시 값 변경만
    # 감시하고 EM은 대상이 아니다(party.py의 _CORE_POOL_FIELDS) — 대신 파티 멤버 순서
    # 의존을 피하려고 값이 아니라 **읽는 함수**로 넘긴다(지연 기여).
    def apply_passive_dependent(self, all_hits, wearer) -> None:
        if not self._stacks:
            return
        r     = self.refinement - 1
        label = "무기: 성현의 열쇠"

        source_hit = next(iter(all_hits[wearer].values()))

        # 효과 2: 스택당 착용자 자신의 EM. 제3자에게 뿌리지 않으므로 그냥 add.
        self_bonus = lambda: source_hit.current_hp() * self._SELF_EM_PCT[r] * self._stacks
        for hit in all_hits[wearer].values():
            hit.add("em_from_flat", self_bonus, label, note="웅장한 시편")

        # 효과 3: 3스택일 때 파티 전원(착용자 포함)의 EM. 제3자 대상이라 동명 무기 간
        # 비중첩 규약을 지키려면 apply_unique_buff로 제출한다.
        if self._stacks < self._MAX_STACKS:
            return
        party_bonus = lambda: source_hit.current_hp() * self._PARTY_EM_PCT[r]
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.apply_unique_buff(label, "em_from_flat", party_bonus)

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 「웅장한 시편」 20초 지속과 0.3초 재발동 제한, 3스택 갱신 판정 — 스택이 몇 개
    #   실려 있는지만 묻고 유지 여부는 유저가 판단한다.
