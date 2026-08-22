from gidc.core.weapon import Weapon
from gidc.core.profile import element_dmg_field
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class JadefallSSplendor(Weapon):
    """벽락의 옥 (Jadefall's Splendor) | 법구 | 5성
    패시브: 정토옥규
    - 원소폭발 발동 또는 보호막 생성 후 3초 동안 「정토옥규」 효과를 생성한다: 2.5초마다
      원소 에너지를 4.5/5/5.5/6/6.5pt 회복한다. 또한 장착 캐릭터 HP 최대치에 기반하여
      1000pt마다 해당 타입의 원소 피해 보너스가 0.3/0.5/0.7/0.9/1.1%씩 최대
      12/20/28/36/44% 증가한다. 「정토옥규」 효과는 해당 무기를 장착한 캐릭터가 대기 상태
      시에도 생성된다
    """

    _DMG_PER_1K = [0.003, 0.005, 0.007, 0.009, 0.011]
    _DMG_CAP    = [0.12, 0.2, 0.28, 0.36, 0.44]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.HP_PCT,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        # 실제 보너스는 착용자의 최종 HP를 읽어야 하므로 apply_passive_dependent
        # (Phase 5)에서 만든다. 여기서는 유저 입력만 모은다 — 질문은 반드시 이
        # 단계에서 해야 질문 집합이 흔들리지 않는다. 「대기 상태 시에도 생성된다」는
        # 로테이션에서 이탈해도 유지되는지의 문제라 켜졌는지 여부만 묻는다.
        self._active = ask_bool(
            "[벽락의 옥] 「정토옥규」 활성 여부 (원소폭발 발동 또는 보호막 생성 후 3초 이내,"
            " 대기 상태에서도 유지됨)"
        )

    # ── 「정토옥규」 HP 스케일 원소 피해 보너스 — 착용자의 최종 HP 기반 (방식 B) ──
    # HP를 읽어 **피해 보너스**로 바꾸므로 차원이 달라져 되먹임이 없다. %-파생 HP 지분은
    # 재료에서 뺀다(convertible_hp) — ATK/HP/DEF/EM 공통 규칙이다.
    def apply_passive_dependent(self, all_hits, wearer) -> None:
        if not self._active:
            return
        r     = self.refinement - 1
        label = "무기: 벽락의 옥"

        field = element_dmg_field(wearer.element)
        if field is None:      # 물리 등 원소가 없는 캐릭터는 대상 필드가 없다
            return

        source_hit = next(iter(all_hits[wearer].values()))
        bonus = lambda: min(
            (source_hit.convertible_hp() / 1000.0) * self._DMG_PER_1K[r],
            self._DMG_CAP[r],
        )
        for hit in all_hits[wearer].values():
            hit.add(field, bonus, label, note="정토옥규")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 2.5초마다 원소 에너지 4.5/5/5.5/6/6.5pt 회복 — 로테이션 빈도를 정하는 값이지
    #   히트 단가에 들어갈 항이 없다(에너지 회복은 이 엔진이 모델링하지 않는다).
