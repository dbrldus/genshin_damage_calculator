from gidc.core.character import Character
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import CharacterTrait, DmgType, Element, MoonsignLevel, ReactionType
from gidc.enums import StatType
from gidc.core.party_state import moonsign_level
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_choice, ask_int


class Linnea(Character):
    """린네아 (Linnea) | 바위 | 활 | 5성 | 어센션 스탯: 치명타 확률

    일반 공격
    활로 최대 3번 공격한다.

    강공격
    피해가 더 크고 정확한 조준 사격을 한다.
    조준 시 바위 결정이 화살촉에 모이고, 바위 결정이 가득 찬 화살은 바위 원소 피해를 준다.

    낙하 공격
    공중에서 화살비를 쏜 후 빠른 속도로 땅에 착지한다. 착지 시 범위 피해를 준다.

    E : 해결사 · 루미 야호!
    루미와 함께 모험을! 발동 방식에 따라 루미가 다른 형태로 출격한다.

    짧은 터치
    루미가 슈퍼 파워 형태로 출격해 주변의 적을 지속적으로 공격하며 바위 원소 범위 피해를 준다. 주변에 달빛 조각이 존재할 경우, 루미는 주변의 적에게 달 결정 반응 피해로 간주되는 바위 원소 범위 피해를 준다.

    연속 짧은 터치
    진짜 실력을 보여줄 때야! 원소전투 스킬 발동 후, 연속으로 원소전투 스킬 혹은 일반 공격을 짧게 터치하면 린네아가 루미에게 반짝이는 보석을 먹여준다. 배가 빵빵해진 루미는 울트라 파워 형태로 출격해 주변의 적에게 달 결정 반응 피해로 간주되는 매우 강력한 바위 원소 범위 피해를 1회 주고, 일반 파워 형태로 전환된다.
    또한 원소전투 스킬을 연속으로 짧게 터치 시, 린네아의 경직 저항력이 증가한다.

    Q : 비망록 · 생존 가이드
    마스터급 모험가라도 적당한 휴식은 필요한 법! 린네아가 루미를 슈퍼 파워 형태로 출격시켜, 주변에 있는 파티 내 모든 캐릭터의 HP를 회복한다. 또한 이후 일정 시간 동안 주변에 있는 현재 필드 위 캐릭터의 HP를 지속적으로 회복한다. 회복량은 린네아 방어력의 영향을 받는다.
    원소폭발 발동 시 루미가 이미 출격 중이라면, 루미의 지속 시간만 초기화되고, 루미의 출격 형태는 변경되지 않는다

    A1 : 야외 관찰 일지
    루미가 필드 위에 있을 때, 루미 주변 적의 바위 원소 내성이 15% 감소한다.

    달빛 징조·보름: 린네아의 원소전투 스킬 해결사 · 루미 야호!와 원소폭발 비망록 · 생존 가이드가 강화되며, 루미를 불러낸 후 루미 주변 적의 바위 원소 내성이 추가로 15% 감소한다

    A4 : 만물 도감
    파티 내 자신의 현재 필드 위 캐릭터에 따라, 린네아가 파티 내 특정 캐릭터의 원소 마스터리를 증가시킨다. 증가량은 린네아 방어력의 5%에 해당한다. 만약 파티 내 자신의 현재 필드 위 캐릭터가
    ·달빛 징조 캐릭터일 경우: 해당 캐릭터의 원소 마스터리가 증가한다.
    · 달빛 징조 캐릭터가 아닐 경우: 린네아 자신의 원소 마스터리가 증가한다

    C1 : 미완의 분류
    원소전투 스킬 해결사 · 루미 야호를 발동하거나 달빛 조각 화음 발동 시, 린네아가 「답사 기록」 효과를 6스택 획득한다. 해당 효과 지속 시간: 10초, 최대 중첩수: 18스택. 파티 내 캐릭터가 달 결정 반응 피해를 주면 「답사 기록」 1스택을 소모해 주는 피해를 증가시킨다. 증가량은 린네아 방어력의 75%에 해당한다.
    또한 루미가 울트라 파워 형태에서 메가톤 해머 강타 사용 시, 린네아는 최대 5스택의 「답사 기록」을 소모할 수 있으며, 스택마다 주는 피해가 증가한다. 증가량은 린네아 방어력의 150%에 해당한다

    C2 : 희비의 예언
    달빛 조각 화음 발동 후 8초 동안, 파티 내 원소 타입이 물 원소와 바위 원소인 모든 캐릭터의 치명타 피해가 40% 증가한다. 또한, 루미가 울트라 파워 형태에서 메가톤 해머 강타를 사용할 경우, 추가로 치명타 피해가 150% 증가한다.

    달빛 징조·보름: 루미가 슈퍼 파워 형태에서 해머 강타를 사용하거나 울트라 파워 형태에서 메가톤 해머 강타 사용 시, 주변에 달빛 조각이 존재하면 달빛 조각 화음이 1회 발동된다. 또한 이번 달빛 조각 화음은 파티 내 원소 타입이 물 원소와 바위 원소인 모든 캐릭터가 해당 반응에 원소를 부여한 것으로 간주한다

    C3 : 즐거운 탐사의 기록
    해결사 · 루미 야호!의 스킬 레벨+3
    최대 Lv.15까지 상승

    C4 : 전문가의 직감
    달빛 조각 화음 발동 후 5초 동안, 린네아와 현재 필드 위에 있는 파티 내 자신의 캐릭터의 방어력이 각각 25% 증가한다. 린네아가 필드 위에 있을 경우, 상술한 방어력 증가 효과는 중첩 가능하다

    C5 : 고향의 작별 선물
    비망록 · 생존 가이드의 스킬 레벨+3
    최대 Lv.15까지 상승

    C6 : 골든 비글호의 꿈
    운명의 자리 「미완의 분류」의 효과가 강화된다: 원소전투 스킬 해결사 · 루미 야호! 또는 달빛 조각 화음 발동 시, 린네아가 즉시 「답사 기록」의 최대 스택 효과를 획득한다. 「답사 기록」 소모 시, 추가로 기존의 2배의 스택 수를 소모하고 피해 증가 효과가 기존의 150%까지 증가한다.

    달빛 징조·보름: 주변에 있는 파티 내 캐릭터가 주는 달 결정 반응 피해가 25% 승격된다

    달빛 징조의 축복 · 서식지 조사
    파티 내 캐릭터가 물 원소 결정 반응 발동 시, 달 결정 반응 발동으로 전환되며, 린네아의 방어력에 기반해 파티 내 캐릭터가 주는 달 결정 반응의 기본 피해가 증가한다: 방어력 100pt마다 달 결정 반응 기본 피해가 0.7% 증가하며, 해당 방식으로 피해는 최대 14% 증가한다.

    또한, 린네아가 파티에 있을 경우 파티의 달빛 징조가 1레벨 상승한다
    """
    name = "린네아"
    weapon_type = WeaponType.BOW
    # 놋 크라이 출신 — 파티 달빛 징조에 기여한다.
    # 「서식지 조사」의 "파티의 달빛 징조가 1레벨 상승"은 이 특성이 곧 그 상승이다 —
    # party_state의 인원수 임계값 표가 이미 그렇게 세고 있다(이네파도 같은 문구다).
    # 파티에 있으면 물 원소 결정 → 달결정으로 전환된다(core.reaction.lunar_candidates).
    innate_traits = frozenset({
        CharacterTrait.MOONSIGN,
        CharacterTrait.LUNAR_CRYSTALLIZE_CONVERTER,
    })

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # ── 일반공격 (L1~L11) ──
    # 일반 공격 — 활로 최대 3번 (물리)
    _NA = [
        [0.590, 0.638, 0.686, 0.755, 0.803, 0.858, 0.933, 1.008, 1.084, 1.166, 1.249],
        [0.512, 0.553, 0.595, 0.654, 0.696, 0.743, 0.809, 0.874, 0.940, 1.011, 1.083],
        [0.816, 0.883, 0.949, 1.044, 1.111, 1.187, 1.291, 1.395, 1.500, 1.614, 1.728],
    ]
    # 「조준 시 바위 결정이 화살촉에 모이고, 바위 결정이 가득 찬 화살은 바위 원소 피해를 준다」
    _AIMED = [0.4390, 0.4740, 0.5100, 0.5610, 0.5970, 0.6380, 0.6940, 0.7500, 0.8060, 0.8670, 0.9280]
    _AIMED_FULL = [1.24, 1.33, 1.43, 1.55, 1.64, 1.74, 1.86, 1.98, 2.11, 2.23, 2.36]
    _PLUNGE = [0.5680, 0.6150, 0.6610, 0.7270, 0.7730, 0.8260, 0.8990, 0.9710, 1.0440, 1.1230, 1.2030]
    _LOW_PLUNGE = [1.14, 1.23, 1.32, 1.45, 1.55, 1.65, 1.80, 1.94, 2.09, 2.25, 2.40]
    _HIGH_PLUNGE = [1.42, 1.53, 1.65, 1.82, 1.93, 2.06, 2.24, 2.43, 2.61, 2.81, 3.00]

    # ── 원소스킬 (L1~L15) ──
    # 해머 강타 × 0.96이다.
    _SMASH = [
        [ 0.96, 1.032, 1.104,  1.20, 1.272, 1.344,  1.44, 1.536, 1.632, 1.728, 1.824,  1.92,  2.04,  2.16,  2.28],
        [ 0.96, 1.032, 1.104,  1.20, 1.272, 1.344,  1.44, 1.536, 1.632, 1.728, 1.824,  1.92,  2.04,  2.16,  2.28],
    ]
    # 루미 해머 강타 — 슈퍼 파워 형태
    _HAMMER = [
         1.00, 1.075,  1.15,  1.25, 1.325,
         1.40,  1.50,  1.60,  1.70,  1.80,
         1.90,  2.00, 2.125,  2.25, 2.375,
    ]
    # 히트 자체는 build_hits에서 달결정 직접 피해로 세운다(달·별 히트는 coeff만 쓴다).
    _MEGATON = [4.00, 4.30, 4.60, 5.00, 5.30, 5.60, 6.00, 6.40, 6.80, 7.20, 7.60, 8.00, 8.50, 9.00, 9.50]

    # ── 원소폭발 (L1~L15) ──
    # 최초 치유량 = 방어력의 N% + M (M은 퍼센트가 아닌 실수치)
    _BURST_HEAL_PCT = [1.60, 1.72, 1.84, 2.00, 2.12, 2.24, 2.40, 2.56, 2.72, 2.88, 3.04, 3.20, 3.40, 3.60, 3.80]
    _BURST_HEAL_FLAT = [
         770,  847,  931, 1021, 1117,
        1220, 1329, 1445, 1567, 1695,
        1830, 1971, 2119, 2273, 2433,
    ]
    # 지속 치유량 = 방어력의 N% + M
    _BURST_HOT_PCT = [
         0.32, 0.344, 0.368,  0.40, 0.424,
        0.448,  0.48, 0.512, 0.544, 0.576,
        0.608,  0.64,  0.68,  0.72,  0.76,
    ]
    _BURST_HOT_FLAT = [154, 169, 186, 204, 223, 244, 266, 289, 313, 339, 366, 394, 424, 455, 487]

    # ── 상수 (레벨로 스케일하지 않는 값) ──
    _A1_GEO_RES_REDUCTION          = 0.15    # A1 야외 관찰 일지 — 루미 주변 적의 바위 원소 내성 감소. 보름이면 추가로 한 번 더.
    _A1_FULLMOON_GEO_RES_REDUCTION = 0.15
    _A4_EM_DEF_RATIO               = 0.05    # A4 만물 도감 — 린네아 방어력의 5%만큼 원소 마스터리 증가
    _C1_STACKS_PER_TRIGGER         = 6       # C1 미완의 분류 — 「답사 기록」 스택
    _C1_MAX_STACKS                 = 18
    _C1_STACK_DEF_RATIO            = 0.75    # 달 결정 반응 피해 1회당 1스택 소모, 방어력의 75%
    _C1_MEGATON_MAX_STACKS         = 5       # 메가톤 해머 강타는 최대 5스택까지 소모
    _C1_MEGATON_DEF_RATIO          = 1.50    # 그 스택당 방어력의 150%
    _C2_CRIT_DMG                   = 0.40    # C2 희비의 예언 — 달빛 조각 화음 후 8초, 파티 내 물·바위 캐릭터의 치명타 피해 증가
    _C2_MEGATON_CRIT_DMG           = 1.50    # 메가톤 해머 강타에는 추가로 더 붙는다
    _C4_DEF_PCT                    = 0.25    # C4 전문가의 직감 — 화음 후 5초, 린네아와 필드 위 캐릭터의 방어력 증가(린네아가 필드면 중첩)
    _C6_STACK_CONSUME_MULT         = 2       # 소모 스택 수가 2배
    _C6_STACK_BOOST                = 1.50    # 피해 증가 효과가 기존의 150%
    _C6_FULLMOON_ELEVATION         = 0.25    # 보름: 파티의 달 결정 반응 피해 25% 승격
    _MOONSIGN_BASE_PER_100_DEF     = 0.007   # 달빛 징조의 축복 · 서식지 조사 — 방어력 100pt마다 달 결정 반응 기본 피해 증가, 상한 있음
    _MOONSIGN_BASE_CAP             = 0.14

    # C1·C2가 이름으로 골라 쓰는 히트. build_hits와 두 훅이 같은 문자열을 읽게 묶어 둔다 —
    # 한쪽만 고치면 보너스가 아무 히트에도 안 붙고 아무 데서도 안 걸린다.
    MEGATON_HIT = "루미 메가톤 해머 강타 피해"
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 3
    BURST_LEVEL_UP_CONSTELLATION = 5
    NA_TABLES = (*_NA, _AIMED, _AIMED_FULL, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (*_SMASH, _HAMMER, _MEGATON,)
    BURST_TABLES = (_BURST_HEAL_PCT, _BURST_HEAL_FLAT, _BURST_HOT_PCT, _BURST_HOT_FLAT,)

    rarity         = 5
    ascension_stat = StatType.CRIT_RATE

    @property
    def element(self) -> Element: return Element.GEO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        nl = self._na_index()
        sk = self._skill_index()   # C3: 레벨 +3
        bl = self._burst_index()   # C5: 레벨 +3

        hits: list[SkillHit] = []

        # 일반공격
        for i, row in enumerate(self._NA):
            hits.append(SkillHit(f"{i+1}단 공격 피해", SkillType.NORMAL_ATK, row[nl], ScalingStat.ATK))
        hits.append(SkillHit("조준 사격 피해", SkillType.CHARGED_ATK, self._AIMED[nl], ScalingStat.ATK))
        hits.append(SkillHit("풀차지 조준 사격 피해", SkillType.CHARGED_ATK, self._AIMED_FULL[nl], ScalingStat.ATK, Element.GEO))
        hits.append(SkillHit("낙하 기간 피해", SkillType.PLUNGING, self._PLUNGE[nl], ScalingStat.ATK))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl], ScalingStat.ATK))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK))

        # 원소스킬
        for i, row in enumerate(self._SMASH):
            hits.append(SkillHit(f"루미 쾅쾅 난타 피해 {i+1}타", SkillType.SKILL, row[sk], ScalingStat.DEF, Element.GEO))
        # 해머 강타·메가톤 해머 강타는 「달 결정 반응 피해로 간주」되는 히트다 —
        # 달결정 직접 피해라 반응 배율·기초 피해 증가·승격을 타고, 원소/스킬 피해 보너스는
        # 받지 않는다(damage._calc_lunar_direct). 쾅쾅 난타는 그냥 바위 원소 피해다.
        # 달·별 히트는 coeff_amp가 아니라 coeff를 쓴다 — 공식에 coeff_amp 자리가 없다.
        hits.append(SkillHit(
            "루미 해머 강타 피해", SkillType.SKILL, self._HAMMER[sk], ScalingStat.DEF, Element.GEO,
            reaction_type=ReactionType.LUNAR_CRYSTALLIZE, dmg_type=DmgType.LUNAR_DIRECT,
        ))
        hits.append(SkillHit(
            self.MEGATON_HIT, SkillType.SKILL, self._MEGATON[sk], ScalingStat.DEF, Element.GEO,
            reaction_type=ReactionType.LUNAR_CRYSTALLIZE, dmg_type=DmgType.LUNAR_DIRECT,
        ))

        # 원소폭발 — 치유뿐이라 히트가 없다(맨 아래 「의도적 미구현」 참고).

        return {h.name: h for h in hits}

    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        # 린네아의 킷에는 「자기만 받는」 효과가 없다. C4가 자기 방어력도 올리지만 같은 답
        # (달빛 조각 화음 발동 여부)이 필드 위 캐릭터 몫도 가르므로 Phase 4에서 한 번에 묻고
        # 한 자리에서 건다 — 같은 질문을 두 번 하지 않기 위해서다.
        pass

    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # ── 유저 입력은 전부 여기서 모은다 (Phase 4.5·5에서는 묻지 않는다) ───────
        # A1은 「루미가 필드 위에 있을 때」가 조건이다. 로테이션이 정하는 값이라 묻는다.
        self._lumi_on_field = ask_bool("[린네아 A1] 루미가 필드 위에 있는지 여부")
        # A4·C4가 함께 쓰는 대상. 「현재 필드 위 캐릭터」는 1명만 고르게 한다.
        self._on_field = self._ask_on_field_member(all_hits)
        # 달빛 조각 화음 — C2(8초)와 C4(5초)의 공통 게이트. 둘 다 없으면 묻지 않는다.
        self._chorus = ask_bool("[린네아 C2/C4] 달빛 조각 화음 발동 여부") if c >= 2 else False
        # C1 「답사 기록」 스택. C6은 발동 즉시 최대 스택을 주므로 묻지 않고 유도한다 —
        # 감쇠를 없애는 명함이 있으면 묻지 않는다는 규칙이 그대로 적용되는 자리다.
        self._record_stack = True if c >= 6 else (
            ask_bool("[린네아 C1] 달 결정 반응 피해 시 「답사 기록」 스택 보유 여부")
            if c >= 1 else False
        )
        self._megaton_stacks = self._C1_MEGATON_MAX_STACKS if c >= 6 else (
            ask_int("[린네아 C1] 메가톤 해머 강타가 소모한 「답사 기록」 스택 수",
                    min_val=0, max_val=self._C1_MEGATON_MAX_STACKS)
            if c >= 1 else 0
        )

        # ── A4 만물 도감 : 린네아 방어력의 5%만큼 원소 마스터리 증가 ──────────────
        # 대상은 파티 구성이 정한다 — 필드 위 캐릭터가 달빛 징조 캐릭터면 그 캐릭터, 아니면
        # 린네아 자신. 묻지 않고 유도한다.
        #
        # 린네아의 방어력을 **읽는 함수**로 넘긴다(지연 기여). 바로 아래 C4가 그 방어력을
        # 올리고 다른 캐릭터가 같은 Phase 4에서 더 올릴 수도 있어, 지금 확정하면 파티원
        # 처리 순서가 결과를 바꾼다.
        #
        # 「다른 스탯의 %에서 파생된」 EM 지분이라 em_from_pct_share로 낸다 — 이 지분은
        # EM을 다시 %로 변환하는 버프의 재료에서 빠진다(profile.SkillHit 참고).
        target = (self._on_field
                  if CharacterTrait.MOONSIGN in self._on_field.traits else self)
        source_hit = next(iter(all_hits[self].values()))
        em_bonus = lambda: source_hit.convertible_def() * self._A4_EM_DEF_RATIO
        for hit in all_hits[target].values():
            hit.add("em_from_pct_share", em_bonus, self, note="A4 만물 도감")

        # ── C4 전문가의 직감 : 화음 후 린네아와 필드 위 캐릭터의 방어력 각각 +25% ──
        # 「린네아가 필드 위에 있을 경우 중첩 가능」 — 두 몫이 각각 걸리므로 self와 _on_field가
        # 같으면 저절로 두 번 더해진다(합계 +50%). 특례를 따로 쓰지 않는다.
        if c >= 4 and self._chorus:
            for target in (self, self._on_field):
                for hit in all_hits[target].values():
                    hit.add("def_pct", self._C4_DEF_PCT, self, note="C4 전문가의 직감")

    def _ask_on_field_member(self, all_hits):
        """A4·C4가 함께 쓰는 「현재 필드 위 캐릭터」. 파티원이 1명뿐이면 묻지 않는다."""
        members = list(all_hits.keys())
        if len(members) == 1:
            return members[0]
        options = [
            f"{char.name} ({char.element.value})" + (" ← 린네아" if char is self else "")
            for char in members
        ]
        return members[ask_choice("[린네아 A4/C4] 현재 필드 위 캐릭터", options)]

    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation
        full_moon = moonsign_level(all_hits) is MoonsignLevel.FULL

        # ── A1 야외 관찰 일지 : 루미 주변 적의 바위 원소 내성 감소 ────────────────
        # 적에게 걸리는 효과라 파티 전원의 바위 히트가 함께 받는다.
        # 보름이면 한 번 더 깎인다 — 린네아 혼자면 초승이므로 노드크라이 캐릭터가 한 명 더
        # 있어야 붙는다. 판정은 묻지 않고 party_state에서 유도한다.
        if self._lumi_on_field:
            reduction = self._A1_GEO_RES_REDUCTION
            if full_moon:
                reduction += self._A1_FULLMOON_GEO_RES_REDUCTION
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.add("geo_res_reduction", reduction, self, note="A1 야외 관찰 일지")

        # ── C2 희비의 예언 : 화음 후 파티 내 물·바위 캐릭터의 치명타 피해 +40% ─────
        if c >= 2 and self._chorus:
            for char, char_hits in all_hits.items():
                if char.element not in (Element.HYDRO, Element.GEO):
                    continue
                for hit in char_hits.values():
                    hit.add("crit_dmg", self._C2_CRIT_DMG, self, note="C2 희비의 예언")

            # 「메가톤 해머 강타를 사용할 경우 추가로 치명타 피해가 150% 증가」 —
            # 그 히트를 보고 있다는 것 자체가 그 상황이므로 따로 묻지 않고 히트에만 건다.
            # 파티 전원에게 거는 읽기도 가능하지만, 메가톤은 린네아 자신의 단발 히트라
            # 그쪽으로 읽으면 같은 순간 다른 캐릭터의 히트까지 +150%가 붙어 부풀려진다.
            megaton = all_hits[self].get(self.MEGATON_HIT)
            if megaton is not None:
                megaton.add("crit_dmg", self._C2_MEGATON_CRIT_DMG, self, note="C2 메가톤")

        # ── C6 보름 : 파티가 주는 달 결정 반응 피해 25% 승격 ─────────────────────
        # 승격 필드는 반응별로 나뉘어 있다 — 달결정 전용 자리에만 넣으므로 콜롬비나와 함께
        # 편성해도 달감전·달개화로 새지 않는다(profile.celestial_elevation_field).
        # 파티 달결정 **반응 피해**는 참여자의 첫 히트를 캐리어로 읽으므로 전원에게 건다.
        if c >= 6 and full_moon:
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.add("lunar_crystallize_elevation", self._C6_FULLMOON_ELEVATION,
                            self, note="C6 보름 승격")

    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # 린네아의 방어력을 **읽는 함수**로 넘긴다(지연 기여) — 자기 C4와 다른 캐릭터의
        # 기여가 같은 단계에서 그 방어력을 올릴 수 있어, 지금 확정하면 순서가 결과를 바꾼다.
        # 항상 같은 히트(첫 히트)를 읽어 값이 하나로 정해지게 한다.
        source_hit = next(iter(all_hits[self].values()))

        # ── 달빛 징조의 축복 · 서식지 조사 ───────────────────────────────────────
        # 방어력 100pt마다 달 결정 반응 **기본 피해** +0.7%, 최대 +14%(방어력 2000에서 상한).
        # 달결정 전용 필드라 직접 피해 히트와 파티 반응 피해가 같은 값을 읽는다.
        moonsign_base = lambda: min(
            source_hit.convertible_def() / 100.0 * self._MOONSIGN_BASE_PER_100_DEF,
            self._MOONSIGN_BASE_CAP,
        )
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.add("lunar_crystallize_base_dmg_bonus", moonsign_base, self,
                        note="달빛 징조 서식지 조사")

        # ── C1 미완의 분류 「답사 기록」 ─────────────────────────────────────────
        # 피해 자체를 키우는 효과라 flat_dmg_bonus로 넣는다(코어 풀이 아니라 Phase 5에서
        # 안전하다). C6이면 증가 효과가 기존의 150%다.
        if c < 1:
            return
        boost = self._C6_STACK_BOOST if c >= 6 else 1.0

        # (1) 파티의 달 결정 반응 피해 1회당 1스택 — 달결정 **직접 피해 히트** 전부.
        #     메가톤은 아래 전용 조항이 따로 있어 제외한다(같은 히트에 두 조항을 겹쳐
        #     읽으면 원문에 없는 합산이 된다).
        if self._record_stack:
            bonus = lambda: source_hit.convertible_def() * self._C1_STACK_DEF_RATIO * boost
            for char, char_hits in all_hits.items():
                for name, hit in char_hits.items():
                    if char is self and name == self.MEGATON_HIT:
                        continue
                    if self._is_lunar_crystallize_direct(hit):
                        hit.add("flat_dmg_bonus", bonus, self, note="C1 답사 기록")

        # (2) 메가톤 해머 강타 — 최대 5스택, 스택마다 방어력의 150%.
        megaton = all_hits[self].get(self.MEGATON_HIT)
        if megaton is not None and self._megaton_stacks:
            stacks = self._megaton_stacks
            megaton.add(
                "flat_dmg_bonus",
                lambda: source_hit.convertible_def() * self._C1_MEGATON_DEF_RATIO * stacks * boost,
                self, note="C1 답사 기록 (메가톤)",
            )

    @staticmethod
    def _is_lunar_crystallize_direct(hit: SkillHit) -> bool:
        """달 결정 **직접 피해** 히트인가 — C1이 붙을 수 있는 자리.

        내재 반응과 dmg_type을 함께 본다. 반응만 보면 달결정 반응 피해 쪽까지 걸리는데,
        그쪽은 flat_dmg_bonus를 읽지 않아(damage._calc_lunar_reaction) 조용히 무효가 된다.
        """
        return (hit.reaction_type is ReactionType.LUNAR_CRYSTALLIZE
                and hit.dmg_type is DmgType.LUNAR_DIRECT)

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · Q 「비망록 · 생존 가이드」 전체 — 치유뿐이다. 이 엔진은 치유를 히트로 만들지 않는다.
    #   계수는 자료의 일부라 표(_BURST_HEAL_PCT/_FLAT, _BURST_HOT_PCT/_FLAT)로만 남겼다.
    # · A1 보름의 「E와 Q가 강화된다」 — 무엇이 얼마나 강화되는지 자료에 수치가 없다.
    #   같은 줄의 내성 추가 감소만 구현했다.
    # · E 연속 짧은 터치의 경직 저항력 증가 — 피해식에 들어갈 항이 없다.
    # · 「답사 기록」 스택 수지 — 자원 모델이 없다. 스택 획득량·최대치·C6의 2배 소모
    #   (_C1_STACKS_PER_TRIGGER / _C1_MAX_STACKS / _C6_STACK_CONSUME_MULT)는 수지를 서술할
    #   뿐이고, 피해에 들어가는 것은 「이번에 소모된 스택이 있는가/몇 개인가」다. 그래서 그
    #   둘만 묻는다. C6은 즉시 최대 스택을 주므로 묻지 않고 최대치로 유도한다.
    # · C1이 파티의 달 결정 **반응 피해 인스턴스**에 붙는 몫 — damage._calc_lunar_reaction에
    #   고정 피해 가산 자리가 없다(캐리어의 flat_dmg_bonus를 일부러 읽지 않는다). 직접 피해
    #   히트에만 걸었다 — 사용자 확인을 거친 자리다.
    # · C2 보름의 「해머 강타/메가톤 사용 시 달빛 조각 화음이 1회 발동 + 물·바위 캐릭터가
    #   원소를 부여한 것으로 간주」 — 화음 발동 빈도와 반응 참여자 판정이라 히트 단가가
    #   아니다. 참여자는 이미 유저가 고른다(party._ask_lunar_participants).
    # · C6의 「즉시 최대 스택 획득」·「2배 소모」 — 위 스택 수지와 같은 이유. 피해에 실제로
    #   들어가는 몫(증가 효과 150%)만 구현했다.
