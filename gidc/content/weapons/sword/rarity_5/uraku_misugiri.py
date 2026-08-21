from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class UrakuMisugiri(Weapon):
    """우라쿠의 미스기리 (Uraku Misugiri) | 한손검 | 5성
    패시브: 비단 꽃과 감실 검
    - 일반 공격으로 주는 피해가 16%/20%/24%/28%/32% 증가하고, 원소전투 스킬로 주는 피해가
      24%/30%/36%/42%/48% 증가한다. 주변에 있는 파티 내 캐릭터가 필드 위에서 바위 원소 피해를
      준 후, 상술한 효과가 100% 증가한다. 지속 시간: 15초. 또한 장착자의 방어력이
      20%/25%/30%/35%/40% 증가한다
    """

    _NORMAL_DMG = [0.16, 0.2, 0.24, 0.28, 0.32]
    _SKILL_DMG  = [0.24, 0.3, 0.36, 0.42, 0.48]
    _DEF_PCT    = [0.2, 0.25, 0.3, 0.35, 0.4]

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
        label = "무기: 우라쿠의 미스기리"
        hits  = all_hits[wearer].values()

        # 효과 1: 방어력 — 조건 없이 착용자에게만 붙는다.
        for hit in hits:
            hit.add("def_pct", self._DEF_PCT[r], label, note="비단 꽃과 감실 검")

        # 효과 2: 일반 공격·원소전투 스킬 피해. 두 필드 모두 조건 없이 기본으로 붙고,
        # 「주변 파티원이 필드 위에서 바위 원소 피해」 트리거가 들어오면 100%(×2) 증가한다.
        # 파티에 지오 캐릭터가 있어야만 성립하는 게 아니다 — 순환 방출물처럼 지오가 아닌
        # 캐릭터도 지오 피해를 줄 수 있으므로(등방울꽃의 애가와 같은 판단) 파티 구성으로
        # 게이팅하지 않고 그대로 묻는다.
        amp = 2.0 if ask_bool(
            "[우라쿠의 미스기리] 15초 이내 주변 파티원이 필드 위에서 바위 원소 피해를 줌"
        ) else 1.0

        for hit in hits:
            hit.add("normal_atk_dmg_bonus", self._NORMAL_DMG[r] * amp, label,
                     note="비단 꽃과 감실 검")
            hit.add("skill_dmg_bonus", self._SKILL_DMG[r] * amp, label,
                     note="비단 꽃과 감실 검")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 지속 시간 15초 — 트리거 후 실제로 그 창 안에서 히트가 나가는지는 로테이션 몫이라
    #   위 질문 하나로 대신한다.
