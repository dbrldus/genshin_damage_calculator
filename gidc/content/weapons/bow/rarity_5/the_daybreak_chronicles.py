from gidc.core.weapon import Weapon
from gidc.core.profile import SkillType
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_step


class TheDaybreakChronicles(Weapon):
    """여명이 트는 역사 (The Daybreak Chronicles) | 활 | 5성
    패시브: 아득한 찬송의 노래
    - 「여명의 바람」: 전투 이탈 3초 후 일반 공격·원소전투 스킬·원소폭발 피해가
      60/75/90/105/120%까지 증가하고, 전투 중에는 1초마다 10/12.5/15/17.5/20%씩
      감소한다. 세 공격 타입은 각각 명중 시(0.1초당 최대 1회) 10/12.5/15/17.5/20%씩
      증가해 같은 상한까지 쌓인다.
    - 파티 내 마도 캐릭터 2명 편성 시(「마도·비밀 의식」), 타입별 개별 누적 대신
      세 타입 모두에 적용되는 단일 피해 증가 효과로 전환되고, 명중당 증가폭이
      20/25/30/35/40%로(2배) 오른다. 상한은 동일하다.
    """

    _TYPE_MAX        = [0.6, 0.75, 0.9, 1.05, 1.2]
    _PER_HIT         = [0.1, 0.125, 0.15, 0.175, 0.2]
    _SECRET_RITE_HIT = [0.2, 0.25, 0.3, 0.35, 0.4]

    _DMG_FIELD = {
        SkillType.NORMAL_ATK: "normal_atk_dmg_bonus",
        SkillType.SKILL:      "skill_dmg_bonus",
        SkillType.BURST:      "burst_dmg_bonus",
    }

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.BOW,
            rarity        = 5,
            tier          = 3,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 여명이 트는 역사"
        cap   = self._TYPE_MAX[r] * 100     # ask_step은 %값으로 받는다

        # 「마도·비밀 의식」은 파티 내 마도 캐릭터 수로만 정해지므로 묻지 않고 유도한다
        # (최초의 대마술 등과 같은 판단). 착용자는 활을 쓰므로 이 카운트에 들지 않는다.
        catalyst_n = sum(1 for c in all_hits if c.weapon_type is WeaponType.CATALYST)
        secret_rite = catalyst_n >= 2

        # 전투 이탈/재진입·초당 감소·타입별 0.1초 명중 가산은 로테이션이 만드는 값이라
        # 최종 결과인 "현재 실린 피해 증가량(%)"을 ask_step으로 직접 받는다 — 증가·감소를
        # 몇 번 거쳤는지 몰라도 되고, 화면 숫자가 곧 실제 버프량이라 검증이 쉽다
        # (툴레이툴라의 기억과 같은 관용구). 상한이 곧 최댓값이라 ask_step의 max_val
        # 자체가 캡이다.
        if secret_rite:
            step = self._SECRET_RITE_HIT[r] * 100
            pct  = ask_step(
                "[여명이 트는 역사] 「마도·비밀 의식」 통합 피해 증가량 "
                "(파티 내 마도 캐릭터 2명 이상 — 모든 공격 타입 공통, 명중당 가산분 2배)",
                0.0, cap, step,
            )
            if not pct:
                return
            for hit in all_hits[wearer].values():
                field = self._DMG_FIELD.get(hit.skill_type)
                if field is not None:
                    hit.add(field, pct / 100, label, note="여명의 바람 (비밀 의식)")
            return

        step = self._PER_HIT[r] * 100
        for skill_type, field in self._DMG_FIELD.items():
            pct = ask_step(
                f"[여명이 트는 역사] 「여명의 바람」 {skill_type.value} 피해 증가량",
                0.0, cap, step,
            )
            if not pct:
                continue
            for hit in all_hits[wearer].values():
                if hit.skill_type is skill_type:
                    hit.add(field, pct / 100, label, note="여명의 바람")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 전투 이탈 3초 대기·초당 10~20% 감소·타입별 0.1초 명중 제한 — 세 타입 각각의
    #   현재 누적량만 묻고 어떻게 그 값에 도달했는지는 유저가 판단한다.
