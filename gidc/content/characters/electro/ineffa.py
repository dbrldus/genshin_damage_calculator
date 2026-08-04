from gidc.core.character import Character, clamp_talent_index
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import CharacterTrait, DmgType, Element, ReactionType
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_choice


class Ineffa(Character):
    """이네파 (Ineffa) | 번개 | 창 | 5성 | 어센션 스탯: 치명타 확률

    E : 청소 모드 · 반송파 (CD 16초)
    이네파가 고급 청소 모듈을 가동해 주변의 적에게 번개 원소 범위 피해를 1회 주고,
    광학 보호막을 펼치며, 다용도 스마트 보조 유닛 「비르지타」를 소환한다. (지속 시간: 각 20초)
    광학 보호막은 이네파 공격력의 영향을 받으며, 번개 원소 피해에 대해 250%의 흡수 효과가 있다.

    Q : 지고한 율령 · 광역 소탕 (CD 15초, 원소 에너지 60)
    다용도 스마트 보조 유닛 「비르지타」의 로켓 펀치로 적을 쓸어버린다! 이네파가 비르지타를 발사해 번개 원소 범위 피해를 주고, 비르지타를 필드 위에 남긴다.
    필드 위에 이네파 자신이 소환한 비르지타가 존재할 경우, 목표 위치에 다시 비르지타를 소환하고 지속 시간을 갱신한다.

    A1 : 오버클럭
    「비르지타」 주변에 달 감전 반응으로 생성된 번개구름이 존재할 경우,
    비르지타가 방전 공격 시 추가로 1회 공격해 이네파 공격력의 65%에 해당하는 번개 원소 범위 피해를 준다. 
    해당 피해는 달 감전 반응으로 주는 피해로 간주한다

    A4 : 광역 재구축 프로토콜
    원소폭발 지고한 율령 · 광역 소탕 발동 시, 주변에 있는 파티 내 모든 캐릭터에게 「매개변수 재구성」 효과를 부여한다: 
    이네파 공격력의 6%를 기반으로, 이네파와 현재 필드 위에 있는 파티 내 자신의 캐릭터의 원소 마스터리가 증가한다. 지속 시간: 20초

    Moonsign : 파티 내 캐릭터가 감전 반응 발동 시, 달 감전 반응으로 전환되며, 이네파의 공격력에 기반해 달 감전 반응의 기본 피해가 증가한다: 
                공격력 100pt마다 기본 피해가 0.7% 증가하며, 해당 방식으로 피해가 최대 14% 증가한다.
                이네파가 파티에 있을 경우 파티의 달빛 징조가 1레벨 상승한다

    C1 : 이네파가 광학 보호막을 펼칠 시, 주변에 있는 파티 내 모든 캐릭터에게 20초 동안 지속되는 「캐리어 재결합」 효과를 부여한다: 
        이네파의 공격력 100pt마다, 달 감전 반응으로 주는 피해가 2.5% 증가한다. 해당 방식으로 피해가 최대 50%까지 증가한다

    C2 : 원소폭발 지고한 율령 · 광역 소탕이 적에게 명중 후, 그중 1기 적에게 「징벌 칙령」 상태를 부여한다: 
        짧은 시간이 지난 후, 또는 해당 적이 처치될 시, 해당 적 주변의 적에게 이네파 공격력의 300%에 해당하는 번개 원소 범위 피해를 준다.
        해당 피해는 달 감전 반응으로 주는 피해로 간주한다. 또한 원소폭발 지고한 율령 · 광역 소탕 발동 시, 주변에 있는 필드 위의 캐릭터에게도 광학 보호막을 부여한다

    C3 : 원소전투 스킬 정화 모드 · 반송파의 스킬 레벨+3

    C4 : 파티 내 자신의 캐릭터가 달 감전 반응 발동 시, 원소 에너지를 5pt 회복한다. 해당 효과는 4초마다 최대 1회 발동된다

    C5 : 원소폭발 지고한 율령 · 광역 소탕의 스킬 레벨+3

    C6 : 이네파가 「캐리어 재결합」 효과의 영향을 받는 상황에서 주변의 번개구름이 적에게 뇌격 진행 후, 
        이네파가 현재 필드 위에 있는 자신의 캐릭터 주변의 적에게 이네파 공격력의 135%에 해당하는 번개 원소 범위 피해를 준다. 
        해당 피해는 달 감전 반응으로 주는 피해로 간주하며 해당 효과는 3.5초마다 최대 1회 발동된다
    """
    name = "이네파"
    weapon_type = WeaponType.POLEARM
    # 놋 크라이 출신 — 파티 달빛 징조에 기여한다.
    innate_traits = frozenset({CharacterTrait.MOONSIGN})

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # 일반 공격 사이클론 더스터 (% ATK, L1~L11)
    # 3단은 같은 계수로 2타가 들어간다.
    _NA_HIT1 = [0.3484, 0.3767, 0.4051, 0.4456, 0.4739, 0.5063, 0.5509, 0.5954, 0.6400, 0.6886, 0.7372]
    _NA_HIT2 = [0.3422, 0.3701, 0.3979, 0.4377, 0.4656, 0.4974, 0.5412, 0.5849, 0.6287, 0.6765, 0.7242]
    _NA_HIT3 = [0.2276, 0.2461, 0.2646, 0.2911, 0.3096, 0.3307, 0.3599, 0.3890, 0.4181, 0.4498, 0.4816]
    _NA_HIT4 = [0.5607, 0.6063, 0.6520, 0.7171, 0.7628, 0.8149, 0.8867, 0.9584, 1.0301, 1.1083, 1.1865]

    # 강공격 (% ATK, L1~L11) — 스태미나 소모 25
    _CA = [0.9494, 1.0267, 1.1040, 1.2144, 1.2917, 1.3800, 1.5014, 1.6229, 1.7443, 1.8768, 2.0093]

    # 낙하 공격 — 대검을 제외한 무기 공통 표 (베넷/실로닌과 동일, 대검인 나비아는 별도 표)
    _PLUNGE      = [0.6393, 0.6914, 0.7434, 0.8177, 0.8698, 0.9292, 1.0110, 1.0928, 1.1746, 1.2638, 1.3530]
    _LOW_PLUNGE  = [1.2784, 1.3824, 1.4865, 1.6351, 1.7392, 1.8581, 2.0216, 2.1851, 2.3486, 2.5270, 2.7054]
    _HIGH_PLUNGE = [1.5968, 1.7267, 1.8567, 2.0424, 2.1723, 2.3209, 2.5251, 2.7293, 2.9336, 3.1564, 3.3792]

    # 원소 스킬 청소 모드·반송파 (% ATK, L1~L13, C3 적용 시 최대 L13)
    _SKILL_DMG = [
        0.864, 0.9288, 0.9936, 1.080, 1.1448,
        1.2096, 1.296, 1.3824, 1.4688, 1.5552,
        1.6416, 1.728, 1.836,
    ]

    # 비르지타 방전 피해 (% ATK, L1~L13) — 원소 스킬로 소환, 지속 20초
    _BIRGITTA_DISCHARGE_DMG = [
        0.960, 1.032, 1.104, 1.200, 1.272,
        1.344, 1.440, 1.536, 1.632, 1.728,
        1.824, 1.920, 2.040,
    ]

    # 광학 보호막 흡수량 (% ATK + 고정값, L1~L13). 지속 20초, 번개 원소 흡수 250%.
    # 보호막은 피해가 아니라 SkillHit을 만들지 않는다 — 명함/세트 조건 판정용으로 보관한다.
    _SKILL_SHIELD_ATK = [
        2.2118, 2.3777, 2.5436, 2.7648, 2.9307,
        3.0966, 3.3178, 3.5389, 3.7601, 3.9813,
        4.2025, 4.4237, 4.7002,
    ]
    _SKILL_SHIELD_FLAT = [
        1387, 1525, 1676, 1837, 2011,
        2196, 2392, 2600, 2820, 3051,
        3294, 3548, 3814,
    ]
    _SKILL_SHIELD_ELECTRO_ABSORPTION = 2.50

    # 원소 폭발 지고한 율령·광역 소탕 (% ATK, L1~L13, C5 적용 시 최대 L13)
    # 번개 원소로 1회만 공격한다. CD 15초, 원소 에너지 60.
    _BURST_DMG = [
        6.768, 7.2756, 7.7832, 8.460, 8.9676,
        9.4752, 10.152, 10.8288, 11.5056, 12.1824,
        12.8592, 13.536, 14.382,
    ]

    # ── 「달 감전 반응으로 주는 피해로 간주」되는 고정 계수 (% ATK) ──────────────
    # 셋 다 달감전 '직접 피해'로 분류한다 → reaction_type=LUNAR_CHARGED + dmg_type=LUNAR_DIRECT.
    # 이 조합은 _calc_lunar_direct를 타며 RM 3.0이 계수에 곱해진다. 대신 방어력 계수와
    # 원소/스킬 피해 보너스는 적용되지 않는다(반응 피해 계열).
    _A1_OVERCLOCK_DMG    = 0.65   # A1 오버클럭 — 비르지타 방전 시 추가 1회
    _C2_PUNITIVE_DMG     = 3.00   # C2 징벌 칙령
    _C6_THUNDERSTRIKE_DMG = 1.35  # C6 — 3.5초마다 최대 1회

    # ── 공격력 스케일 버프 계수 ────────────────────────────────────────────────
    # Moonsign : 공격력 100pt당 달감전 '기본 피해' +0.7%, 최대 +14% (공격력 2000에서 상한)
    _MOONSIGN_BASE_DMG_PER_100_ATK = 0.007
    _MOONSIGN_BASE_DMG_CAP         = 0.14
    # C1 캐리어 재결합 : 공격력 100pt당 달감전 피해 +2.5%, 최대 +50% (공격력 2000에서 상한)
    _C1_LUNAR_DMG_PER_100_ATK = 0.025
    _C1_LUNAR_DMG_CAP         = 0.50
    # A4 매개변수 재구성 : 이네파 공격력의 6%만큼 원소 마스터리 증가
    _A4_EM_FROM_ATK = 0.06
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 3
    BURST_LEVEL_UP_CONSTELLATION = 5
    NA_TABLES = (_NA_HIT1, _NA_HIT2, _NA_HIT3, _NA_HIT4, _CA, _PLUNGE, _LOW_PLUNGE,
        _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_DMG, _BIRGITTA_DISCHARGE_DMG,)
    BURST_TABLES = (_BURST_DMG,)

    rarity         = 5
    ascension_stat = StatType.CRIT_RATE

    @property
    def element(self)  -> Element: return Element.ELECTRO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        c = self.constellation

        sk = self._skill_index()
        bl = self._burst_index()
        nl = self._na_index()

        hits: list[SkillHit] = []

        # 창 캐릭터라 일반/강/낙하 공격은 물리 피해(element 미지정 → PHYSICAL)
        for name, coeff in [
            ("1단 공격 피해",     self._NA_HIT1[nl]),
            ("2단 공격 피해",     self._NA_HIT2[nl]),
            ("3단 공격 피해 1타", self._NA_HIT3[nl]),
            ("3단 공격 피해 2타", self._NA_HIT3[nl]),
            ("4단 공격 피해",     self._NA_HIT4[nl]),
        ]:
            hits.append(SkillHit(name, SkillType.NORMAL_ATK, coeff, ScalingStat.ATK))

        hits.append(SkillHit("강공격 피해", SkillType.CHARGED_ATK, self._CA[nl], ScalingStat.ATK))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK))

        hits.append(SkillHit("원소 스킬 피해",   SkillType.SKILL, self._SKILL_DMG[sk],              ScalingStat.ATK, Element.ELECTRO))
        hits.append(SkillHit("비르지타 방전 피해", SkillType.SKILL, self._BIRGITTA_DISCHARGE_DMG[sk], ScalingStat.ATK, Element.ELECTRO))

        hits.append(SkillHit("원소 폭발 피해", SkillType.BURST, self._BURST_DMG[bl], ScalingStat.ATK, Element.ELECTRO))

        # ── 달감전 직접 피해 히트 ────────────────────────────────────────────
        # 조건부 히트도 반드시 build_hits에서 만든다 — apply_self_buffs에서 만들면
        # 기초 스탯을 채우는 루프가 이미 끝난 뒤라 공격력이 0으로 남는다.
        hits.append(SkillHit(
            "A1 오버클럭 추가 공격", SkillType.SKILL, self._A1_OVERCLOCK_DMG,
            ScalingStat.ATK, Element.ELECTRO,
            reaction_type=ReactionType.LUNAR_CHARGED, dmg_type=DmgType.LUNAR_DIRECT,
        ))

        if c >= 2:
            hits.append(SkillHit(
                "C2 징벌 칙령 피해", SkillType.BURST, self._C2_PUNITIVE_DMG,
                ScalingStat.ATK, Element.ELECTRO,
                reaction_type=ReactionType.LUNAR_CHARGED, dmg_type=DmgType.LUNAR_DIRECT,
            ))

        if c >= 6:
            hits.append(SkillHit(
                "C6 뇌격 추가 피해", SkillType.SKILL, self._C6_THUNDERSTRIKE_DMG,
                ScalingStat.ATK, Element.ELECTRO,
                reaction_type=ReactionType.LUNAR_CHARGED, dmg_type=DmgType.LUNAR_DIRECT,
            ))

        return {h.name: h for h in hits}

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        # 이네파의 자기 버프는 없다 — 모든 버프가 파티 단계에서 걸린다.
        pass

    # ── 파티 버프 4: 유저 입력 수집 ────────────────────────────────────────
    # 이네파는 코어 스탯(atk/def/hp)에 기여하지 않는다 — 모든 버프가 자신의 최종
    # 공격력을 읽는 방식 B라 Phase 5에서 처리한다. 여기서는 입력만 한 번 모은다.
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # C1은 광학 보호막 전개가 조건 — 보호막은 E로 펼치고, C2는 Q에도 부여한다.
        self._shield_active = (c >= 1) and ask_bool("[이네파 C1] 광학 보호막 전개 여부")
        self._burst_used    = ask_bool("[이네파 A4] 원소 폭발 발동 여부")
        # A4는 이네파 자신과 '현재 필드 위 캐릭터' 1명에게만 원소 마스터리를 준다.
        self._on_field      = self._ask_on_field_member(all_hits) if self._burst_used else None

    def _ask_on_field_member(self, all_hits):
        """A4 대상이 될 현재 필드 위 캐릭터를 고르게 한다. 파티원이 1명뿐이면 묻지 않는다."""
        members = list(all_hits.keys())
        if len(members) == 1:
            return members[0]
        options = [
            f"{char.name} ({char.element.value})" + (" ← 이네파" if char is self else "")
            for char in members
        ]
        return members[ask_choice("[이네파 A4] 현재 필드 위 캐릭터", options)]

    # ── 파티 버프 5: 최종 스탯을 읽어 스케일하는 버프 (방식 B) ────────────────
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # 이네파의 최신 공격력 — 값이 아니라 **읽는 함수**로 넘긴다(지연 기여).
        # 이 몫을 받은 EM을 다시 읽어 피해로 바꾸는 캐릭터(시틀라리 A4/C1)가 있어서,
        # 여기서 값을 미리 확정해 버리면 누가 먼저 실행되느냐가 결과를 바꾼다.
        # 항상 같은 히트(첫 히트)를 읽으므로 언제 계산되든 값은 같다.
        source_hit = next(iter(all_hits[self].values()))
        atk_per_100 = lambda: source_hit.current_atk() / 100.0

        # Moonsign: 달감전 '기본 피해' 증가 — 파티 전원의 달감전에 적용된다.
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.add(
                    "lunar_reaction_base_dmg_bonus",
                    lambda: min(atk_per_100() * self._MOONSIGN_BASE_DMG_PER_100_ATK,
                                self._MOONSIGN_BASE_DMG_CAP),
                    self, note="Moonsign",
                )

        # C1 캐리어 재결합: 달감전으로 주는 피해 증가 — 파티 전원.
        if self._shield_active:
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.add(
                        "lunar_charged_bonus",
                        lambda: min(atk_per_100() * self._C1_LUNAR_DMG_PER_100_ATK,
                                    self._C1_LUNAR_DMG_CAP),
                        self, note="C1",
                    )

        # A4 매개변수 재구성: 이네파 공격력의 6%를 원소 마스터리로 — 이네파 + 필드 위 1명.
        # 이네파 공격력에서 파생된 EM이므로 em_from_pct_share에 함께 태그해,
        # 카즈하처럼 EM을 **다시 %로 변환**하는 버프가 이 지분을 재료로 쓰지 못하게 막는다.
        # (EM에 비례한 몫을 피해에 직접 더하는 쪽 — 시틀라리 A4/C1 — 은 재변환이 아니라
        #  이 지분도 그대로 재료로 쓴다.)
        if self._burst_used:
            em = lambda: source_hit.current_atk() * self._A4_EM_FROM_ATK
            targets = {id(self): self}
            if self._on_field is not None:
                targets[id(self._on_field)] = self._on_field
            for char in targets.values():
                for hit in all_hits[char].values():
                    hit.add("elemental_mastery", em, self, note="A4 매개변수 재구성")
                    hit.add("em_from_pct_share", em, self, note="A4 매개변수 재구성")
