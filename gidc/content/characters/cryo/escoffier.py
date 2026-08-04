from gidc.core.character import Character, clamp_talent_index
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import Element
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool


class Escoffier(Character):
    """에스코피에 (Escoffier) | 얼음 | 창 | 5성 | 어센션 스탯: 치명타 확률

    일반 공격 : 창으로 최대 3번 공격한다.
    강공격 : 일정 스태미나를 소모해 올려치기 공격을 한다.
    낙하 공격 : 공중에서 땅을 내려찍어 경로상의 적을 공격하고 착지 시 범위 피해를 준다.

    E : 저온 조리법
        「냉장」 모드로 전방위 다목적 요리 장치를 가동해 주변의 적에게 얼음 원소 범위 피해를 준다.
        요리 장치 · 냉장 모드
        현재 필드 위 캐릭터를 따라다니며, 간헐적으로 주변의 적에게 「서리 파르페」를 발사해 얼음 원소 피해를 준다.

        아르케의 힘: 우시아
        일정 시간마다 에스코피에가 「냉장」 모드로 요리 장치 가동 시, 솟구치는 칼날을 소환해 우시아 성질의 얼음 원소 범위 피해를 준다.

    Q : 현란한 칼솜씨
        극한의 칼솜씨로 얼음 원소 범위 피해를 주고 주변에 있는 파티 내 모든 캐릭터의 HP 회복한다. 
        회복량은 에스코피에 공격력의 영향을 받는다.

    A1 : 원소폭발 현란한 칼솜씨 발동 후, 에스코피에가 9초 동안 지속되는 「식이요법」 효과를 획득한다: 
         1초마다 주변에 있는 현재 필드 위 캐릭터의 HP를 회복한다.

    A4 : 파티 내 물 원소 또는 얼음 원소 캐릭터가 1/2/3/4명 존재할 경우, 
         에스코피에의 원소전투 스킬 저온 조리법 또는 원소폭발 현란한 칼솜씨가 적에게 명중 시, 
         해당 적의 물 원소 내성과 얼음 원소 내성이 5%/10%/15%/55% 감소한다. 지속 시간: 12초

    C1 : 파티 내 캐릭터 4명의 원소 타입이 모두 물 원소 또는 얼음 원소일 경우, 
        에스코피에의 원소전투 스킬 저온 조리법 또는 원소폭발 현란한 칼솜씨 발동 후, 
        15초 동안 주변에 있는 파티 내 모든 캐릭터가 얼음 원소 피해를 줄 때의 치명타 피해가 60% 증가한다.
        고유 특성 「영감의 조미료」를 해금해야 한다

    C2 : 에스코피에가 냉장 모드로 요리 장치 가동 시, 15초 동안 지속되는 「즉석 요리」 효과를 획득한다: 
         지속 시간 동안 에스코피에가 「냉요리」를 5스택 획득한다. 
         에스코피에를 제외한 주변의 필드 위 캐릭터가 일반 공격, 강공격, 낙하 공격, 원소전투 스킬 또는 
         원소폭발로 얼음 원소 피해를 줄 시, 「냉요리」를 1스택 소모하고 주는 피해가 에스코피에 공격력의 240%만큼 증가한다.
         한 번의 얼음 원소 피해가 동시에 다수의 적에게 명중 시, 명중한 적의 수에 따라 「냉요리」의 스택이 소모된다

    C3 : 원소전투 스킬 저온 조리법의 스킬 레벨+3

    C4 : 식이요법의 지속 시간이 6초 연장된다. 지속 시간 동안 식이요법을 통해 치유 발동 시, 
         일정 확률로 치유량이 100% 증가하고 에스코피에가 원소 에너지를 2pt 회복한다. 확률은 에스코피에 자신의 치명타 확률과 동일하다.
         한 번의 식이요법 지속 시간 동안 해당 효과는 최대 7회 발동된다.
         고유 특성 「밥이 보약」을 해금해야 한다
        
    C5 : 원소폭발 현란한 칼솜씨의 스킬 레벨+3

    C6 : 요리 장치 · 냉장 모드가 강화된다:
        · 현재 필드 위에 있는 파티 내 자신의 캐릭터의 일반 공격, 강공격 또는 낙하 공격이 적에게 명중 시, 
        요리 장치 · 냉장 모드가 추가로 특급 서리 파르페를 1개 발사해 에스코피에 공격력의 500%에 해당하는 얼음 원소 범위 피해를 준다. 
        해당 피해는 원소전투 스킬 피해로 간주한다. 해당 효과는 0.5초마다 최대 1회 발동되고, 
        한 번의 요리 장치 · 냉장 모드 지속 시간 동안 최대 6회 발동된다
    """
    name = "에스코피에"
    weapon_type = WeaponType.POLEARM

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # 일반 공격 「주방의 솜씨」 (% ATK, L1~L11) — 창이므로 물리 피해, 최대 3단.
    # 3단은 두 타로 나뉘어 들어간다(33% + 40.33% @L1).
    _NA_HIT1   = [0.5155, 0.5575, 0.5994, 0.6594, 0.7013, 0.7493, 0.8152, 0.8812, 0.9471, 1.0190, 1.0910]
    _NA_HIT2   = [0.4759, 0.5147, 0.5534, 0.6088, 0.6475, 0.6918, 0.7526, 0.8135, 0.8744, 0.9408, 1.0072]
    _NA_HIT3_1 = [0.3300, 0.3569, 0.3837, 0.4221, 0.4489, 0.4796, 0.5219, 0.5641, 0.6063, 0.6523, 0.6984]
    _NA_HIT3_2 = [0.4033, 0.4362, 0.4690, 0.5159, 0.5487, 0.5862, 0.6378, 0.6894, 0.7410, 0.7973, 0.8536]

    # 강공격 (% ATK, L1~L11) — 스태미나 소모 25
    _CA = [1.1541, 1.2481, 1.3420, 1.4762, 1.5701, 1.6775, 1.8251, 1.9727, 2.1204, 2.2814, 2.4424]

    # 낙하 공격 — 대검을 제외한 무기 공통 표 (베넷/이네파/실로닌과 동일)
    _PLUNGE      = [0.6393, 0.6914, 0.7434, 0.8177, 0.8698, 0.9292, 1.0110, 1.0928, 1.1746, 1.2638, 1.3530]
    _LOW_PLUNGE  = [1.2784, 1.3824, 1.4865, 1.6351, 1.7392, 1.8581, 2.0216, 2.1851, 2.3486, 2.5270, 2.7054]
    _HIGH_PLUNGE = [1.5968, 1.7267, 1.8567, 2.0424, 2.1723, 2.3209, 2.5251, 2.7293, 2.9336, 3.1564, 3.3792]

    # ── 원소 스킬 「저온 조리법」 (% ATK, L1~L13, C3 적용 시 최대 L13) ──────────
    # 짧은 터치 CD 15초 / 홀드 CD 6초, 요리 장치·냉장 모드 지속 20초
    _SKILL_DMG = [
        0.5040, 0.5418, 0.5796, 0.6300, 0.6678,
        0.7056, 0.7560, 0.8064, 0.8568, 0.9072,
        0.9576, 1.0080, 1.0710,
    ]
    # 서리 파르페 — 냉장 모드가 필드 위 캐릭터를 따라다니며 간헐적으로 발사한다.
    _FROSTY_PARFAIT_DMG = [
        1.2000, 1.2900, 1.3800, 1.5000, 1.5900,
        1.6800, 1.8000, 1.9200, 2.0400, 2.1600,
        2.2800, 2.4000, 2.5500,
    ]
    # 솟구치는 칼날 — 아르케 「우시아」, 발동 간격 10초
    _SURGING_BLADE_DMG = [
        0.3360, 0.3612, 0.3864, 0.4200, 0.4452,
        0.4704, 0.5040, 0.5376, 0.5712, 0.6048,
        0.6384, 0.6720, 0.7140,
    ]

    # ── 원소 폭발 「현란한 칼솜씨」 (% ATK, L1~L13, C5 적용 시 최대 L13) ────────
    # CD 15초, 원소 에너지 60
    _BURST_DMG = [
        5.9280, 6.3726, 6.8172, 7.4100, 7.8546,
        8.2992, 8.8920, 9.4848, 10.0776, 10.6704,
        11.2632, 11.8560, 12.5970,
    ]
    # 원소 폭발 치유량 (% ATK + 고정값, L1~L13).
    # 치유는 피해가 아니라 SkillHit을 만들지 않는다 — 세트/명함 조건 판정용으로 보관한다.
    _BURST_HEAL_ATK = [
        1.7203, 1.8493, 1.9784, 2.1504, 2.2794,
        2.4084, 2.5805, 2.7525, 2.9245, 3.0966,
        3.2686, 3.4406, 3.6557,
    ]
    _BURST_HEAL_FLAT = [
        1079, 1186, 1303, 1429, 1564,
        1708, 1861, 2022, 2193, 2373,
        2562, 2759, 2966,
    ]

    # C6 「특급 서리 파르페」: 공격력의 500%, 원소 스킬 피해로 간주.
    # 0.5초마다 최대 1회, 냉장 모드 1회당 최대 6회 발동.
    _C6_SUPREME_PARFAIT_DMG = 5.00

    # ── 버프 계수 (히트 아님 — 아래 훅에서 사용) ────────────────────────────────
    # A4 : 파티 내 물/얼음 캐릭터 1/2/3/4명 → 적 물·얼음 내성 감소.
    #      스킬 레벨이 아니라 파티 구성으로 결정된다.
    #      내성 감소는 음수로 *_res_reduction에 넣는다 (실로닌 참고).
    _A4_RES_REDUCTION = (0.05, 0.10, 0.15, 0.55)
    # C1 : 파티 전원이 물/얼음일 때, 파티 전원의 얼음 원소 치명타 피해 증가
    _C1_CRYO_CRIT_DMG = 0.60
    # C2 「냉요리」: 에스코피에 공격력의 240%만큼 피해 증가, 5스택
    _C2_COLD_DISH_DMG    = 2.40
    _C2_COLD_DISH_STACKS = 5
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 3
    BURST_LEVEL_UP_CONSTELLATION = 5
    NA_TABLES = (_NA_HIT1, _NA_HIT2, _NA_HIT3_1, _NA_HIT3_2, _CA, _PLUNGE, _LOW_PLUNGE,
        _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_DMG, _FROSTY_PARFAIT_DMG, _SURGING_BLADE_DMG,)
    BURST_TABLES = (_BURST_DMG, _BURST_HEAL_ATK, _BURST_HEAL_FLAT,)

    rarity         = 5
    ascension_stat = StatType.CRIT_RATE

    @property
    def element(self)  -> Element: return Element.CRYO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        c = self.constellation

        # C3: 원소 스킬 레벨 +3 (최대 13) / C5: 원소 폭발 레벨 +3 (최대 13)
        sk = self._skill_index()
        bl = self._burst_index()
        nl = self._na_index()

        hits: list[SkillHit] = []

        # 창 캐릭터라 일반/강/낙하 공격은 물리 피해(element 미지정 → PHYSICAL)
        for name, coeff in [
            ("1단 공격 피해",     self._NA_HIT1[nl]),
            ("2단 공격 피해",     self._NA_HIT2[nl]),
            ("3단 공격 피해 1타", self._NA_HIT3_1[nl]),
            ("3단 공격 피해 2타", self._NA_HIT3_2[nl]),
        ]:
            hits.append(SkillHit(name, SkillType.NORMAL_ATK, coeff, ScalingStat.ATK))

        hits.append(SkillHit("강공격 피해", SkillType.CHARGED_ATK, self._CA[nl], ScalingStat.ATK))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK))

        hits.append(SkillHit("원소 스킬 피해",   SkillType.SKILL, self._SKILL_DMG[sk],          ScalingStat.ATK, Element.CRYO))
        hits.append(SkillHit("서리 파르페 피해",  SkillType.SKILL, self._FROSTY_PARFAIT_DMG[sk], ScalingStat.ATK, Element.CRYO))
        hits.append(SkillHit("솟구치는 칼날 피해", SkillType.SKILL, self._SURGING_BLADE_DMG[sk],  ScalingStat.ATK, Element.CRYO))

        hits.append(SkillHit("원소 폭발 피해", SkillType.BURST, self._BURST_DMG[bl], ScalingStat.ATK, Element.CRYO))

        # C6 특급 서리 파르페 — 「해당 피해는 원소전투 스킬 피해로 간주한다」
        # 조건부 히트도 반드시 build_hits에서 만든다 — apply_self_buffs에서 만들면
        # 기초 스탯을 채우는 루프가 이미 끝난 뒤라 공격력이 0으로 남는다.
        if c >= 6:
            hits.append(SkillHit(
                "C6 특급 서리 파르페 피해", SkillType.SKILL,
                self._C6_SUPREME_PARFAIT_DMG, ScalingStat.ATK, Element.CRYO,
            ))

        return {h.name: h for h in hits}

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        # 에스코피에의 자기 버프는 없다.
        #   A1(식이요법)·C4(밥이 보약)는 순수 치유/에너지 회복이라 피해 모델에 넣지 않는다.
        #   나머지(A4/C1/C2/C6)는 전부 파티 대상이라 아래 Phase 4.5 / 5 훅이 담당한다.
        pass

    # ── 파티 버프 4: 코어 스탯 기여 + 유저 입력 수집 ─────────────────────────
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # 에스코피에는 코어 스탯(atk/def/hp/em)에 기여하지 않는다 — 여기서는
        # Phase 4.5(A4/C1)와 Phase 5(C2)가 함께 쓸 입력만 한 번 모은다.
        c = self.constellation

        # 파티 내 물/얼음 캐릭터 수 — A4 내성 감소량과 C1 발동 조건의 재료.
        # 유저에게 묻지 않고 파티 구성에서 유도한다.
        self._aqua_cryo = sum(
            1 for char in all_hits if char.element in (Element.HYDRO, Element.CRYO)
        )

        # A4는 E 또는 Q 명중이 조건이라 둘 중 하나만 켜져도 성립한다.
        # C1은 추가로 파티 4명 전원이 물/얼음이어야 하고, C2는 E(냉장 모드)만 본다.
        self._e_active = ask_bool("[에스코피에 E] 저온 조리법 가동 여부")
        self._q_active = ask_bool("[에스코피에 Q] 현란한 칼솜씨 발동 여부")

        # C1 「영감의 조미료」: 파티 4명의 원소가 모두 물 또는 얼음 + E/Q 발동.
        self._c1_active = (
            c >= 1
            and len(all_hits) == 4
            and self._aqua_cryo == 4
            and (self._e_active or self._q_active)
        )

    # ── 파티 버프 4.5: 스탯을 읽지 않는 크로스 버프 ─────────────────────────
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # A4 「미식의 정수」: E 또는 Q 명중 시 적의 물·얼음 내성 감소 (12초).
        # 감소량은 스킬 레벨이 아니라 파티 내 물/얼음 캐릭터 수(1~4명)로 정해진다.
        # 내성 감소는 음수로 넣는다 (실로닌 E와 동일한 계열).
        if (self._e_active or self._q_active) and self._aqua_cryo:
            reduction = self._A4_RES_REDUCTION[self._aqua_cryo - 1]
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.add("cryo_res_reduction",  -reduction, self, note="A4")
                    hit.add("hydro_res_reduction", -reduction, self, note="A4")

        # C1: 파티 전원이 얼음 원소 피해를 줄 때의 치명타 피해 +60% (15초).
        # 「얼음 원소 피해를 줄 때」이므로 element가 CRYO인 히트에만 건다.
        if self._c1_active:
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    if hit.element is Element.CRYO:
                        hit.add("crit_dmg", self._C1_CRYO_CRIT_DMG, self, note="C1")

    # ── 파티 버프 5: 최종 스탯을 읽어 스케일하는 버프 (방식 B) ────────────────
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # C2 「냉요리」: 냉장 모드 가동 시, 에스코피에를 제외한 필드 위 캐릭터가 주는
        # 얼음 원소 피해가 에스코피에 공격력의 240%만큼 증가한다.
        # 에스코피에의 최종 공격력을 읽는 방식 B라 flat_dmg_bonus로 차원 변환한다
        # (ATK 코어 풀에 되먹이면 무한 루프이며 정확성 가드가 실패시킨다).
        if self.constellation < 2 or not self._e_active:
            return

        # 에스코피에의 최종 공격력을 값이 아니라 **읽는 함수**로 넘긴다(지연 기여) —
        # 다른 캐릭터가 Phase 5에서 공격력을 더해 줄 수도 있어 지금 확정하면 순서에 좌우된다.
        source_hit = next(iter(all_hits[self].values()))

        # 「지속 시간 동안 5스택」은 히트 단가가 아니라 로테이션당 발동 횟수라
        # 단일 히트 표에는 반영하지 않는다 — _C2_COLD_DISH_STACKS는 로테이션 합산용.
        for char, char_hits in all_hits.items():
            if char is self:      # 「에스코피에를 제외한」
                continue
            for hit in char_hits.values():
                if hit.element is Element.CRYO:
                    hit.add("flat_dmg_bonus",
                            lambda: source_hit.current_atk() * self._C2_COLD_DISH_DMG,
                            self, note="C2 냉요리")
