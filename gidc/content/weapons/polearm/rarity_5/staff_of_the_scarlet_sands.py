from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_int


class StaffOfTheScarletSands(Weapon):
    """적색 사막의 지팡이 (Staff of the Scarlet Sands) | 장병기 | 5성
    - 장착한 캐릭터 원소 마스터리의 52/65/78/91/104%에 해당하는 공격력 보너스를 획득한다.
    - 원소전투 스킬이 적을 명중하면 10초 동안 「적색 사막의 꿈」 효과를 획득한다: 장착한 캐릭터
      원소 마스터리의 28/35/42/49/56%만큼 공격력 보너스를 획득한다. 해당 효과 최대 중첩수: 3스택
    """

    _BASE_EM_ATK_PCT  = [0.52, 0.65, 0.78, 0.91, 1.04]
    _STACK_EM_ATK_PCT = [0.28, 0.35, 0.42, 0.49, 0.56]

    _MAX_STACKS = 3

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.POLEARM,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        # 효과 1(상시 EM→공격력 변환)은 조건이 없다. 효과 2 「적색 사막의 꿈」의 스택
        # 수만 여기서 받는다 — 원소전투 스킬 명중 여부와 10초 지속은 로테이션 몫이라
        # 묻는다. 실제 EM 환산은 착용자의 **최종** 원소 마스터리를 읽어야 하므로 두 효과
        # 모두 apply_passive_dependent(Phase 5)에서 계산한다.
        self._stacks = ask_int(
            "[적색 사막의 지팡이] 「적색 사막의 꿈」 스택 수 (원소전투 스킬이 적에게 명중,"
            f" 10초 지속, 최대 {self._MAX_STACKS})",
            0, self._MAX_STACKS,
        )

    # ── 효과 1·2 — 착용자의 최종 원소 마스터리 기반 (방식 B) ──────────────────
    # 이 무기의 EM→공격력 환산은 **%로 받은 EM 지분을 뺀 값**만 재료로 쓴다(설탕 A4처럼
    # 남에게서 %-변환으로 받은 EM은 여기서 제외). 재변환 목적지가 EM이 아니라 공격력이라
    # 다른 EM→피해 변환(잎을 가르는 빛 등)과는 다르지만, 「%-지분 제외」라는 재료 규칙
    # 자체는 convertible_em()의 정의와 같으므로 그대로 가져다 쓴다. 출력이 EM이 아니라
    # 공격력이라 자기 참조 순환은 없으므로 atk_flat_derived가 아니라 atk_flat에 바로
    # 쓴다(반암결록의 HP→공격력과 같은 판단).
    def apply_passive_dependent(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 적색 사막의 지팡이"

        source_hit = next(iter(all_hits[wearer].values()))

        base_bonus = lambda: source_hit.convertible_em() * self._BASE_EM_ATK_PCT[r]
        for hit in all_hits[wearer].values():
            hit.add("atk_flat", base_bonus, label, note="신기루 끝의 뜨거운 꿈")

        if not self._stacks:
            return
        stack_bonus = (
            lambda: source_hit.convertible_em() * self._STACK_EM_ATK_PCT[r] * self._stacks
        )
        for hit in all_hits[wearer].values():
            hit.add("atk_flat", stack_bonus, label, note="적색 사막의 꿈")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 「적색 사막의 꿈」 10초 지속과 스택 갱신 판정 — 스택이 몇 개 실려 있는지만
    #   묻고 유지 여부는 유저가 판단한다.
