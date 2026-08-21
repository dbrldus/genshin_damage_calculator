from gidc.core.character import Character, clamp_talent_index
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import Element
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_choice


class Bennett(Character):
    """베넷 (Bennett) | 불 | 한손검 | 4성 | 어센션 스탯: 원소 충전 효율

    A1 — 고난을 넘는 용기: 피격 시 CD 관련 효과 (스탯 무영향, 미구현)
    A4 — 사그러들지 않는 불꽃: 아름다운 여정 영역 내 열정 과부하 폭발 발생 안 함
         (로테이션 안전성 효과, 스탯 무영향, 미구현)
    C1 — 모험 동경: Q 공격력 증가 효과 HP 제한 해제 + 기본 공격력의 20% 추가 가산
    C2 — 궁지 돌파: HP 70% 미만 시 원소 충전 효율 +30%
    C3 — 타오르는 열정: 원소 스킬 레벨 +3 (최대 13)
    C4 — 사그러들지 않는 열정: 1단 차지 스킬 2단 공격 중 일반 공격 추가 타격 (135%)
    C5 — 넓어진 마음: 원소 폭발 레벨 +3 (최대 13)
    C6 — 열화와 용기: 한/양손검/장병기 캐릭터 불 피해 보너스 +15% + 불 원소 부여
    """
    name = "베넷"
    weapon_type = WeaponType.SWORD

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # 일반 공격
    _NA = [
        [0.4455, 0.4817, 0.5180, 0.5698, 0.6061, 0.6475, 0.7045, 0.7615, 0.8184, 0.8806, 0.9428],
        [0.4274, 0.4622, 0.4970, 0.5467, 0.5815, 0.6213, 0.6759, 0.7306, 0.7853, 0.8449, 0.9045],
        [0.5461, 0.5905, 0.6350, 0.6985, 0.7430, 0.7938, 0.8636, 0.9334, 1.0033, 1.0795, 1.1557],
        [0.5968, 0.6454, 0.6940, 0.7634, 0.8120, 0.8675, 0.9438, 1.0202, 1.0965, 1.1798, 1.2631],
        [0.7190, 0.7775, 0.8360, 0.9196, 0.9781, 1.0450, 1.1370, 1.2289, 1.3209, 1.4212, 1.5215],
    ]

    _CA_HIT1 = [0.5590, 0.6045, 0.6500, 0.7150, 0.7605, 0.8125, 0.8840, 0.9555, 1.0270, 1.1050, 1.1830]
    _CA_HIT2 = [0.6072, 0.6566, 0.7060, 0.7766, 0.8260, 0.8825, 0.9602, 1.0378, 1.1155, 1.2002, 1.2849]

    _PLUNGE      = [0.6393, 0.6914, 0.7434, 0.8177, 0.8698, 0.9292, 1.0110, 1.0928, 1.1746, 1.2638, 1.3530]
    _LOW_PLUNGE  = [1.2784, 1.3824, 1.4865, 1.6351, 1.7392, 1.8581, 2.0216, 2.1851, 2.3486, 2.5270, 2.7054]
    _HIGH_PLUNGE = [1.5968, 1.7267, 1.8567, 2.0424, 2.1723, 2.3209, 2.5251, 2.7293, 2.9336, 3.1564, 3.3792]

    # 원소 스킬
    _SKILL_PRESS         = [1.376, 1.4792, 1.5824, 1.720, 1.8232, 1.9264, 2.064, 2.2016, 2.3392, 2.4768, 2.6144, 2.752, 2.924]
    _SKILL_CHARGE1_HIT1  = [0.840, 0.903,  0.966,  1.050, 1.113,  1.176,  1.260, 1.344,  1.428,  1.512,  1.596,  1.680, 1.785]
    _SKILL_CHARGE1_HIT2  = [0.920, 0.989,  1.058,  1.150, 1.219,  1.288,  1.380, 1.472,  1.564,  1.656,  1.748,  1.840, 1.955]
    _SKILL_CHARGE2_HIT1  = [0.880, 0.946,  1.012,  1.100, 1.166,  1.232,  1.320, 1.408,  1.496,  1.584,  1.672,  1.760, 1.870]
    _SKILL_CHARGE2_HIT2  = [0.960, 1.032,  1.104,  1.200, 1.272,  1.344,  1.440, 1.536,  1.632,  1.728,  1.824,  1.920, 2.040]
    _SKILL_EXPLOSION     = [1.320, 1.419,  1.518,  1.650, 1.749,  1.848,  1.980, 2.112,  2.244,  2.376,  2.508,  2.640, 2.805]

    # 원소 폭발
    _BURST_DMG = [2.3280, 2.5026, 2.6772, 2.9100, 3.0846,
                  3.2592, 3.4920, 3.7248, 3.9576, 4.1904,
                  4.4232, 4.6560, 4.9470, 5.2400, 5.53]

    _BURST_ATK_RATIO = [
        0.56, 0.60, 0.644, 0.70, 0.742,
        0.784, 0.84, 0.896, 0.952, 1.008,
        1.064, 1.12, 1.19, 1.26, 1.33
    ]
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 3
    BURST_LEVEL_UP_CONSTELLATION = 5
    NA_TABLES = (*_NA, _CA_HIT1, _CA_HIT2, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_PRESS, _SKILL_CHARGE1_HIT1, _SKILL_CHARGE1_HIT2,
        _SKILL_CHARGE2_HIT1, _SKILL_CHARGE2_HIT2, _SKILL_EXPLOSION,)
    BURST_TABLES = (_BURST_DMG, _BURST_ATK_RATIO,)

    rarity = 4

    @property
    def element(self)  -> Element: return Element.PYRO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        c = self.constellation

        # C3: 원소 스킬 레벨 +3 (최대 13)
        sk = self._skill_index()
        # C5: 원소 폭발 레벨 +3 (최대 13)
        bl = self._burst_index()
        nl = self._na_index()

        hits: list[SkillHit] = []

        for i, row in enumerate(self._NA):
            hits.append(SkillHit(f"{i+1}단 공격", SkillType.NORMAL_ATK, row[nl], ScalingStat.ATK))

        hits.append(SkillHit("강공격 1타", SkillType.CHARGED_ATK, self._CA_HIT1[nl], ScalingStat.ATK))
        hits.append(SkillHit("강공격 2타", SkillType.CHARGED_ATK, self._CA_HIT2[nl], ScalingStat.ATK))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK))

        hits += [
            SkillHit("스킬 누르기",          SkillType.SKILL, self._SKILL_PRESS[sk],        ScalingStat.ATK, Element.PYRO),
            SkillHit("스킬 1단 차지 1타",     SkillType.SKILL, self._SKILL_CHARGE1_HIT1[sk], ScalingStat.ATK, Element.PYRO),
            SkillHit("스킬 1단 차지 2타",     SkillType.SKILL, self._SKILL_CHARGE1_HIT2[sk], ScalingStat.ATK, Element.PYRO),
            SkillHit("스킬 2단 차지 1타",     SkillType.SKILL, self._SKILL_CHARGE2_HIT1[sk], ScalingStat.ATK, Element.PYRO),
            SkillHit("스킬 2단 차지 2타",     SkillType.SKILL, self._SKILL_CHARGE2_HIT2[sk], ScalingStat.ATK, Element.PYRO),
            SkillHit("스킬 2단 차지 폭발 데미지", SkillType.SKILL, self._SKILL_EXPLOSION[sk], ScalingStat.ATK, Element.PYRO),
        ]

        if c >= 4:
            hits.append(SkillHit(
                "스킬 2단 차지 추가타 (C4)",
                SkillType.SKILL,
                self._SKILL_CHARGE1_HIT2[sk] * 1.35,
                ScalingStat.ATK,
                Element.PYRO,
            ))

        hits.append(SkillHit("원소 폭발", SkillType.BURST, self._BURST_DMG[bl], ScalingStat.ATK, Element.PYRO))

        return {h.name: h for h in hits}

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        # C2: HP 70% 미만 시 원소 충전 효율 +30%
        if self.constellation >= 2 and ask_bool("[베넷 C2] HP 70% 미만 여부"):
            for hit in hits.values():
                hit.add("energy_recharge", 0.30, self, note="C2")

    # ── 파티 버프 ─────────────────────────────────────────────────────────
    # 베넷은 코어 스탯(atk_flat)만 기여하고 스케일 읽기가 없으므로 코어는 여기서 처리.
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        self._q_active = ask_bool("[베넷 Q] 아름다운 여정 영역 활성 여부")
        if not self._q_active:
            return

        c = self.constellation

        # C1 미만: Q 공격력 증가는 파티원 HP ≥ 70% 조건 필요
        hp_ok = (c >= 1) or ask_bool("[베넷 Q] 파티원 HP 70% 이상 여부")

        # Q 버프는 「영역 안에 있는 캐릭터」에게만 붙는다 — 영역이 살아 있어도 밖에 선
        # 캐릭터는 공격력 증가도 C6 불 피해 보너스도 받지 못한다. 그래서 활성 여부와
        # 별개로 대상을 따로 받는다. (C6도 같은 대상을 쓴다 — apply_party_buffs 참고)
        self._on_field = self._ask_field_member(all_hits)

        if hp_ok:
            bl = self._burst_index()
            ratio = self._BURST_ATK_RATIO[bl]
            if c >= 1:
                ratio += 0.20
            # 자신의 첫 히트에서 기본 공격력 읽기 (모든 히트에 동일)
            self_hits = all_hits[self]
            first = next(iter(self_hits.values()))
            flat_atk = first.atk_base * ratio
            # 베넷 기초 공격력의 %에서 파생된 값이라 atk_flat이 아니라 atk_from_pct_share다
            # (유저 실측). 받는 캐릭터의 최종 공격력에는 그대로 들어가지만, 그 캐릭터의
            # 공격력을 읽어 버프를 만드는 쪽(마비카·이네파·제사의 여운 등)의 재료에서는
            # 빠진다. 니콜 E처럼 계수표의 상수로 적힌 값만 atk_flat에 남는다.
            for hit in all_hits[self._on_field].values():
                hit.add("atk_from_pct_share", flat_atk, self, note="Q 아름다운 여정")

    # C6: pyro_dmg_bonus는 코어 스탯도 스탯 스케일도 아니므로 apply_party_buffs.
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        if not self._q_active or self.constellation < 6:
            return

        # C6: 한/양손검/장병기 캐릭터 — 불 피해 보너스 +15%
        # C6도 영역 안에서만 걸린다 — 무기 종류만 맞으면 되는 게 아니다.
        melee = {WeaponType.SWORD, WeaponType.CLAYMORE, WeaponType.POLEARM}
        char = self._on_field
        if char.weapon is not None and char.weapon.weapon_type in melee:
            for hit in all_hits[char].values():
                hit.add("pyro_dmg_bonus", 0.15, self, note="C6 근접 무기")

    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        pass  # 최종 스탯을 읽어 스케일하는 버프 없음

    def _ask_field_member(self, all_hits: dict["Character", dict[str, SkillHit]]) -> "Character":
        """아름다운 여정 영역 안에 있는 캐릭터를 고르게 한다 — Q 버프의 실제 대상.

        정상적인 로테이션에서는 필드 위 캐릭터가 한 명뿐이고 그 한 명이 곧 영역 안에
        있는 캐릭터다. 그래서 복수 선택이 아니라 한 명을 고른다. 베넷 자신도 영역 안에
        설 수 있으므로 후보에 넣고, 파티원이 1명뿐이면 다른 경우가 없어 묻지 않는다."""
        members = list(all_hits.keys())
        if len(members) == 1:
            return members[0]
        options = [
            f"{char.name} ({char.element.value})" + (" ← 베넷" if char is self else "")
            for char in members
        ]
        return members[ask_choice("[베넷 Q] 아름다운 여정 영역 안에 있는 캐릭터", options)]
