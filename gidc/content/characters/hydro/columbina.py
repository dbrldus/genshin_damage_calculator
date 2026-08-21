from gidc.core.character import Character, clamp_talent_index
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import CharacterTrait, DmgType, Element, MoonsignLevel, ReactionType
from gidc.enums import StatType
from gidc.core.party_state import moonsign_level
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_choice, ask_int


class Columbina(Character):
    """콜롬비나 (Columbina) | 물 | 법구 | 5성 | 어센션 스탯: 치명타 확률

    일반 공격
    달빛 조석을 소환하여 최대 3번 공격해 물 원소 피해를 준다.

    강공격
    일정 스태미나를 소모해 짧은 영창 후 물 원소 범위 피해를 준다.
    풀 이슬을 1개 이상 보유한 경우, 콜롬비나의 강공격은 스태미나를 소모하지 않는 특수 강공격 달 이슬 세례로 대체된다: 풀 이슬 1개를 소모해 전방의 적에게 풀 원소 범위 피해를 3회 준다. 해당 피해는 달 개화 피해로 간주된다.

    낙하 공격
    공중에서 땅을 내려찍어 경로상의 적을 공격하고 착지 시 물 원소 범위 피해를 준다

    E : 아득한 조석
        달바다의 조석을 일으켜 물 원소 범위 피해를 주고 인력 파동을 소환한다.
        인력 파동은 필드 위 캐릭터를 따라다니며 주변의 적에게 지속적으로 물 원소 범위 피해를 준다. 
        인력 파동 존재 기간 동안, 주변에 있는 파티 내 캐릭터가 달빛 반응을 발동하거나 달빛 반응 피해를 줄 시, 
        콜롬비나에게 특별한 인력이 축적된다, 최대치에 도달하면 콜롬비나에게 가장 많은 인력을 축적한 달빛 반응의 타입 따라 적에게 각기 다른 타입의 피해를 준다.

        달빛 징조·보름: 인력 파동으로 더 큰 범위의 물 원소 범위 피해를 준다

        원소전투 스킬 아득한 조석 발동 후, 콜롬비나가 인력 파동을 소환한다.
        인력 파동은 현재 필드 위 캐릭터를 따라다니며, 주변의 적에게 지속적으로 물 원소 범위 피해를 준다.

        또한, 인력 파동이 존재하는 동안 주변에 있는 파티 내 캐릭터가 달빛 반응을 발동하거나 달빛 반응 피해를 줄 시, 
        콜롬비나는 이후 2초 동안 신월 계시 효과를 얻어 인력을 지속적으로 축적한다. 2초마다 인력을 20pt 축적할 수 있다.
        인력은 최대 60pt까지 축적 가능하며, 인력 파동의 지속 시간이 종료되면 사라진다.
        인력이 최대치에 도달 시, 모든 인력을 소모하고 특수한 인력 간섭을 발동해 콜롬비나가 가장 많은 인력을 축적한 달빛 반응 타입에 따라 서로 다른 효과가 발생한다. 
        콜롬비나가 가장 많은 인력을 축적한 달빛 반응 타입이:
        · 달 감전 반응일 경우: 간섭파가 번개 원소 범위 피해를 1회 준다. 해당 피해는 달 감전 반응 피해로 간주한다.
        · 달 개화 반응일 경우: 간섭파가 주변의 적들에게 달이슬 인장을 5개 발사해 풀 원소 피해를 준다. 해당 피해는 달 개화 반응 피해로 간주한다.
        · 달 결정 반응일 경우: 간섭파가 바위 원소 범위 피해를 1회 준다. 해당 피해는 달 결정 반응 피해로 간주한다
    
    Q : 향수에 잠긴 달
        무구한 새로운 달의 이름으로 산과 바다를 잇고, 주변의 대지를 잠시 순결한 달 영역으로 바꾸어 물 원소 범위 피해를 준다.
        현재 필드 위 캐릭터가 달 영역 내에 있을 시, 파티 내 모든 캐릭터의 달빛 반응 피해가 증가한다
    
    A1 : 인력 간섭 발동 시, 콜롬비나는 유혹 효과를 획득해 자신의 치명타 확률이 5% 증가한다, 지속 시간: 10초, 최대 중첩수: 3스택

    A4 : 달 영역 안에 있는 캐릭터가 달빛 반응 발동 시, 다음과 같은 효과를 각각 획득한다:
        · 달 감전 반응: 번개구름이 조건에 부합하는 목표에게 뇌격 진행 시, 33%의 확률로 추가 뇌격이 1회 발동된다.
        · 달 개화 반응: 달 개화 반응 발동 시, 파티에 특수한 달빛 풀 이슬을 제공한다. 18초마다 해당 방식으로 달빛 풀 이슬을 최대 3개 획득할 수 있다.
        · 달 결정 반응: 달빛 조각 화음 발동 시, 달빛 조각 울림마다 33% 확률로 추가 공격을 한다

    Moonsign : 파티 내 캐릭터가 감전/개화/물 원소 결정 반응 발동 시, 달 감전/달 개화/달 결정 반응으로 전환되며, 
    콜롬비나의 HP 최대치에 기반해 파티 내 캐릭터가 주는 달빛 반응의 기본 피해가 증가한다: HP 최대치 1000pt마다 달빛 반응의 기본 피해가 0.2% 증가한다. 
    해당 방식으로 피해가 최대 7% 증가한다.

    C1 : 원소전투 스킬 아득한 조석 발동 시, 인력 간섭과 동일한 효과가 즉시 1회 발동된다. 해당 효과는 15초 마다 최대 1회 발동된다.

        달빛 징조 · 보름:
        인력 간섭 발동 시, 콜롬비나에게 가장 많은 인력이 축적된 달빛 반응 타입이:
        · 달 감전 반응일 경우: 파티 내 자신의 현재 필드 위 캐릭터의 원소 에너지를 6pt 회복한다;
        · 달 개화 반응일 경우: 현재 필드 위에 있는 파티 내 자신의 캐릭터의 경직 저항력이 8초 동안 증가한다;
        · 달 결정 반응일 경우: 비바다 보호막을 소환한다. 피해 흡수량은 콜롬비나 HP 최대치의 12%의 영향을 받고, 물 원소 피해에 대해 250%의 흡수 효과가 있다. 지속 시간: 8초.

        주변에 있는 파티 내 모든 캐릭터가 주는 달빛 반응 피해가 1.5% 승격된다

    C2 : 인력의 축적 속도가 34% 증가한다.
        인력 간섭 발동 시, 콜롬비나는 광휘 효과를 획득해 HP 최대치가 40% 증가한다, 지속 시간: 8초.

        달빛 징조 · 보름:
        광휘 효과 지속 시간 동안 이번 인력 간섭 발동 시, 콜롬비나에게 가장 많은 인력을 축적한 달빛 반응 타입이:
        · 달 감전 반응일 경우: 파티 내 자신의 현재 필드 위 캐릭터의 공격력이 콜롬비나 HP 최대치의 1%만큼 증가한다.
        · 달 개화 반응일 경우: 파티 내 자신의 현재 필드 위 캐릭터의 원소 마스터리가 콜롬비나의 HP 최대치의 0.35%만큼 증가한다.
        · 달 결정 반응일 경우: 파티 내 자신의 현재 필드 위 캐릭터의 방어력이 콜롬비나의 HP 최대치의 1%만큼 증가한다.

        주변에 있는 파티 내 모든 캐릭터가 주는 달빛 반응 피해가 7% 승격된다

    C3 : 원소전투 스킬 아득한 조석의 스킬 레벨+3
        주변에 있는 파티 내 모든 캐릭터가 주는 달빛 반응 피해가 1.5% 승격된다

    C4 : 인력 간섭 발동 시, 콜롬비나가 원소 에너지를 4pt 회복한다.
        또한, 콜롬비나에게 가장 많은 인력을 축적한 달빛 반응 타입에 따라(달 감전/달 개화/달 결정 반응), 
        이번 간섭파로 주는 달빛 반응의 피해가 콜롬비나 HP 최대치의 12.5%/2.5%/12.5%만큼 증가한다. 
        상술한 효과는 15초마다 최대 1회 발동된다.

        주변에 있는 파티 내 모든 캐릭터가 주는 달빛 반응 피해가 1.5% 승격된다

    C5 : 원소폭발 향수에 잠긴 달의 스킬 레벨+3
        주변에 있는 파티 내 모든 캐릭터가 주는 달빛 반응 피해가 1.5% 승격된다

    C6 : 달 영역 내에 있는 모든 캐릭터가 달빛 반응 발동 후 8초 동안, 반응에 참여한 원소 타입에 따라 파티 내 모든 캐릭터의 해당 원소 타입 치명타 피해가 80% 증가한다. 
        같은 원소 타입의 치명타 피해 증가 효과는 중첩되지 않는다.
        주변에 있는 파티 내 모든 캐릭터가 주는 달빛 반응 피해가 7% 승격된다
    """
    
    name = "콜롬비나"
    weapon_type = WeaponType.CATALYST
    # 놋 크라이 출신 — 파티 달빛 징조에 기여한다.
    # 파티에 있으면 감전 → 달감전, 결정 → 달결정으로 전환된다(core.reaction.lunar_candidates).
    innate_traits = frozenset({
        CharacterTrait.MOONSIGN,
        CharacterTrait.LUNAR_CHARGED_CONVERTER,
        CharacterTrait.LUNAR_CRYSTALLIZE_CONVERTER,
    })

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # 일반 공격 달빛 조석 (% ATK, L1~L11) — 물 원소, 최대 3단
    _NA_HIT1 = [0.4679, 0.5030, 0.5381, 0.5849, 0.6200, 0.6551, 0.7019, 0.7487, 0.7955, 0.8423, 0.8890]
    _NA_HIT2 = [0.3663, 0.3937, 0.4212, 0.4578, 0.4853, 0.5128, 0.5494, 0.5860, 0.6226, 0.6593, 0.6959]
    _NA_HIT3 = [0.5848, 0.6287, 0.6726, 0.7311, 0.7749, 0.8188, 0.8773, 0.9357, 0.9942, 1.0527, 1.1112]

    # 강공격 (% ATK, L1~L11) — 스태미나 소모 50
    _CA = [1.1608, 1.2479, 1.3349, 1.4510, 1.5381, 1.6251, 1.7412, 1.8573, 1.9734, 2.0894, 2.2055]

    # 특수 강공격 달 이슬 세례 (% HP 최대치, L1~L11) — 풀 이슬 1개 소모, 풀 원소로 3회.
    # 「해당 피해는 달 개화 피해로 간주된다」
    _MOONDEW_CLEANSE_DMG   = [0.0151, 0.0162, 0.0174, 0.0189, 0.0200, 0.0212, 0.0227, 0.0242, 0.0257, 0.0272, 0.0287]
    _MOONDEW_CLEANSE_HITS  = 3

    # 낙하 공격 (% ATK, L1~L11) — 콜롬비나 전용 표.
    # 표준표(0.6393…)나 같은 법구인 니콜과도 값이 다르므로 공유하지 않는다.
    _PLUNGE      = [0.5683, 0.6145, 0.6608, 0.7269, 0.7731, 0.8260, 0.8987, 0.9714, 1.0441, 1.1234, 1.2027]
    _LOW_PLUNGE  = [1.1363, 1.2288, 1.3213, 1.4535, 1.5459, 1.6517, 1.7970, 1.9423, 2.0877, 2.2462, 2.4048]
    _HIGH_PLUNGE = [1.4193, 1.5349, 1.6504, 1.8154, 1.9310, 2.0630, 2.2445, 2.4261, 2.6076, 2.8057, 3.0037]

    # ── 원소 스킬 아득한 조석 (% HP 최대치, L1~L13, C3 적용 시 최대 L13) ────────
    # 인력 최대치 60pt, 인력 파동 지속 25초, CD 17초
    _SKILL_DMG = [
        0.1672, 0.1797, 0.1923, 0.2090, 0.2215,
        0.2341, 0.2508, 0.2675, 0.2842, 0.3010,
        0.3177, 0.3344, 0.3553,
    ]
    # 인력 파동 — 필드 위 캐릭터를 따라다니며 주는 지속 피해 (물 원소)
    _GRAVITY_RIPPLE_DMG = [
        0.0936, 0.1006, 0.1076, 0.1170, 0.1240,
        0.1310, 0.1404, 0.1498, 0.1591, 0.1685,
        0.1778, 0.1872, 0.1989,
    ]
    # 인력 간섭 — 가장 많이 축적한 달빛 반응 타입에 따라 셋 중 하나만 발동한다.
    # 각각 「달 감전/달 개화/달 결정 반응 피해로 간주」된다.
    _INTERFERENCE_LUNAR_CHARGED_DMG = [
        0.0470, 0.0506, 0.0541, 0.0588, 0.0623,
        0.0659, 0.0706, 0.0753, 0.0800, 0.0847,
        0.0894, 0.0941, 0.1000,
    ]
    _INTERFERENCE_LUNAR_BLOOM_DMG = [
        0.0141, 0.0151, 0.0162, 0.0176, 0.0187,
        0.0197, 0.0211, 0.0225, 0.0239, 0.0253,
        0.0268, 0.0282, 0.0299,
    ]
    _INTERFERENCE_LUNAR_BLOOM_HITS = 5   # 달이슬 인장 5개
    _INTERFERENCE_LUNAR_CRYSTALLIZE_DMG = [
        0.0882, 0.0949, 0.1015, 0.1103, 0.1169,
        0.1235, 0.1324, 0.1412, 0.1500, 0.1588,
        0.1677, 0.1765, 0.1875,
    ]

    # ── 원소 폭발 향수에 잠긴 달 (% HP 최대치, L1~L13, C5 적용 시 최대 L13) ─────
    # 달 영역 지속 20초, CD 15초, 원소 에너지 60
    _BURST_DMG = [
        0.3224, 0.3466, 0.3708, 0.4030, 0.4272,
        0.4514, 0.4836, 0.5158, 0.5481, 0.5803,
        0.6126, 0.6448, 0.6851,
    ]
    # 달 영역 내 필드 위 캐릭터가 있을 때 파티 전원의 달빛 반응 피해 '증가' (버프 — 히트 아님)
    # → 반응 보너스 계열이므로 lunar_*_bonus 에 가산한다.
    _BURST_LUNAR_REACTION_DMG_BONUS = [
        0.13, 0.16, 0.19, 0.22, 0.25,
        0.28, 0.31, 0.34, 0.37, 0.40,
        0.43, 0.46, 0.49,
    ]

    # ── 명함 「달빛 반응 피해 승격」 ─────────────────────────────────────────
    # 원문이 Q의 '증가'와 구분해 '승격'이라 부르는 계열 → elevation_multiplier 에 가산한다.
    # 명함은 누적되므로 보유한 단계의 값을 모두 더한다 (C6 기준 합계 20%).
    _CONSTELLATION_ELEVATION = {1: 0.015, 2: 0.07, 3: 0.015, 4: 0.015, 5: 0.015, 6: 0.07}

    # C6 : 반응에 참여한 원소 타입의 치명타 피해 증가 (같은 원소끼리 비중첩)
    _C6_ELEMENTAL_CRIT_DMG = 0.80

    # A1 「유혹」: 인력 간섭 발동 시 자신의 치명타 확률 증가 (10초, 최대 3스택)
    _A1_SEDUCTION_CRIT_RATE  = 0.05
    _A1_SEDUCTION_MAX_STACKS = 3

    # Moonsign : HP 최대치 1000pt마다 달빛 반응 '기본 피해' +0.2%, 최대 +7%
    # (HP 35,000에서 상한) → 달반응 3종의 *_base_dmg_bonus
    _MOONSIGN_BASE_DMG_PER_1000_HP = 0.002
    _MOONSIGN_BASE_DMG_CAP         = 0.07

    # 인력 간섭 타입 — C2 보름 분기와 C4가 공유한다.
    _INTERFERENCE_TYPES = ("달 감전", "달 개화", "달 결정")

    # C2 「광휘」: 인력 간섭 발동 시 콜롬비나 HP 최대치 증가 (8초)
    _C2_RADIANCE_HP_PCT = 0.40
    # C2 보름 : 광휘 지속 중 필드 위 캐릭터에게 콜롬비나 HP 최대치 기반 스탯 부여.
    # 인력 간섭 타입별로 (대상 필드, HP 대비 비율)
    # EM은 '다른 캐릭터 스탯의 %'로 주는 지분이라 변환 재료가 되지 않는 조각에 넣는다
    # (합계 elemental_mastery에는 자동으로 포함된다 — profile.SkillHit 참고).
    _C2_FULLMOON_CONVERSION = (
        ("atk_from_pct_share", 0.0100),  # 달 감전 → 공격력
        ("em_from_pct_share", 0.0035),   # 달 개화 → 원소 마스터리
        ("def_from_pct_share", 0.0100),  # 달 결정 → 방어력
    )

    # C4 : 이번 간섭파의 달빛 반응 피해가 콜롬비나 HP 최대치의 12.5%/2.5%/12.5%만큼 증가
    _C4_INTERFERENCE_HP_RATIO = (0.125, 0.025, 0.125)
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 3
    BURST_LEVEL_UP_CONSTELLATION = 5
    NA_TABLES = (_NA_HIT1, _NA_HIT2, _NA_HIT3, _CA, _MOONDEW_CLEANSE_DMG, _PLUNGE, _LOW_PLUNGE,
        _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_DMG, _GRAVITY_RIPPLE_DMG, _INTERFERENCE_LUNAR_CHARGED_DMG,
        _INTERFERENCE_LUNAR_BLOOM_DMG, _INTERFERENCE_LUNAR_CRYSTALLIZE_DMG,)
    BURST_TABLES = (_BURST_DMG, _BURST_LUNAR_REACTION_DMG_BONUS,)

    rarity         = 5
    ascension_stat = StatType.CRIT_RATE

    @property
    def element(self)  -> Element: return Element.HYDRO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        c = self.constellation

        sk = self._skill_index()
        bl = self._burst_index()
        nl = self._na_index()

        hits: list[SkillHit] = []

        # 법구 캐릭터라 일반/강/낙하 공격도 원소 피해다 (니콜과 동일)
        for i, row in enumerate((self._NA_HIT1, self._NA_HIT2, self._NA_HIT3)):
            hits.append(SkillHit(f"{i+1}단 공격 피해", SkillType.NORMAL_ATK, row[nl],
                                 ScalingStat.ATK, Element.HYDRO))

        hits.append(SkillHit("강공격 피해", SkillType.CHARGED_ATK, self._CA[nl],
                             ScalingStat.ATK, Element.HYDRO))

        # 달 이슬 세례 — 풀 이슬 보유 시 강공격을 대체한다. HP 스케일 + 풀 원소 + 달개화 피해.
        for i in range(self._MOONDEW_CLEANSE_HITS):
            hits.append(SkillHit(
                f"달 이슬 세례 피해 {i+1}타", SkillType.CHARGED_ATK,
                self._MOONDEW_CLEANSE_DMG[nl], ScalingStat.HP, Element.DENDRO,
                reaction_type=ReactionType.LUNAR_BLOOM, dmg_type=DmgType.LUNAR_DIRECT,
            ))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK, Element.HYDRO))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK, Element.HYDRO))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK, Element.HYDRO))

        hits.append(SkillHit("원소 스킬 피해",   SkillType.SKILL, self._SKILL_DMG[sk],          ScalingStat.HP, Element.HYDRO))
        hits.append(SkillHit("인력 파동 지속 피해", SkillType.SKILL, self._GRAVITY_RIPPLE_DMG[sk], ScalingStat.HP, Element.HYDRO))

        # 인력 간섭 — 셋 중 축적량이 가장 많은 타입 하나만 실제로 발동한다.
        # 어느 쪽이 뜰지는 파티 구성에 달렸으므로 세 갈래를 모두 만들어 두고 골라 읽는다.
        hits.append(SkillHit(
            "인력 간섭 · 달감전 피해", SkillType.SKILL,
            self._INTERFERENCE_LUNAR_CHARGED_DMG[sk], ScalingStat.HP, Element.ELECTRO,
            reaction_type=ReactionType.LUNAR_CHARGED, dmg_type=DmgType.LUNAR_DIRECT,
        ))
        for i in range(self._INTERFERENCE_LUNAR_BLOOM_HITS):
            hits.append(SkillHit(
                f"인력 간섭 · 달개화 피해 {i+1}타", SkillType.SKILL,
                self._INTERFERENCE_LUNAR_BLOOM_DMG[sk], ScalingStat.HP, Element.DENDRO,
                reaction_type=ReactionType.LUNAR_BLOOM, dmg_type=DmgType.LUNAR_DIRECT,
            ))
        hits.append(SkillHit(
            "인력 간섭 · 달결정 피해", SkillType.SKILL,
            self._INTERFERENCE_LUNAR_CRYSTALLIZE_DMG[sk], ScalingStat.HP, Element.GEO,
            reaction_type=ReactionType.LUNAR_CRYSTALLIZE, dmg_type=DmgType.LUNAR_DIRECT,
        ))

        hits.append(SkillHit("원소 폭발 피해", SkillType.BURST, self._BURST_DMG[bl],
                             ScalingStat.HP, Element.HYDRO))

        return {h.name: h for h in hits}

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        # A1 「유혹」: 인력 간섭 발동 시 자신의 치명타 확률 +5%, 최대 3스택.
        # 콜롬비나 본인에게만 걸리는 자기 버프다.
        stacks = ask_int("[콜롬비나 A1] 「유혹」 스택 수", min_val=0, max_val=self._A1_SEDUCTION_MAX_STACKS)
        if stacks:
            for hit in hits.values():
                hit.add("crit_rate", self._A1_SEDUCTION_CRIT_RATE * stacks, self, note="A1 유혹")

        # A4 「달 영역 내 달빛 반응」: 세 갈래 모두 데미지 모델에 반영하지 않는다.
        #   · 달 감전 — 번개구름 뇌격 시 33% 확률로 추가 뇌격 1회
        #   · 달 결정 — 달빛 조각 울림마다 33% 확률로 추가 공격
        #     → 둘 다 확률 발동이라 기대값 반영을 하지 않기로 했다(사용자 결정).
        #        기대값을 넣게 되면 해당 히트의 coeff_amp에 1.33을 곱하는 형태가 된다.
        #   · 달 개화 — 파티에 달빛 풀 이슬 제공 (18초마다 최대 3개)
        #     → 자원 생성이며, 이 풀 이슬이 소모되어 나가는 피해가 곧 「달 이슬 세례」다.
        #        해당 히트는 build_hits에서 이미 만들고 있으므로 추가 처리가 없다.

        # C2 「광휘」: 인력 간섭 발동 시 자신의 HP 최대치 +40% (8초).
        # 조건 없는 자기 버프라 Phase 3에서 넣는다. 이 HP를 읽는 쪽(Moonsign/C2 보름/C4)은
        # 지연 기여라 언제 계산되든 이 증가분을 포함한다.
        if self.constellation >= 2 and ask_bool("[콜롬비나 C2] 「광휘」 효과 보유 여부"):
            self._radiance_active = True
            for hit in hits.values():
                hit.add("hp_pct", self._C2_RADIANCE_HP_PCT, self, note="C2 광휘")
        else:
            self._radiance_active = False

    # ── 파티 버프 4: 코어 스탯 기여 + 유저 입력 수집 ─────────────────────────
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # Q: 달 영역 내에 필드 위 캐릭터가 있어야 파티 반응 피해 증가가 걸린다.
        self._domain_active = ask_bool("[콜롬비나 Q] 필드 위 캐릭터가 달 영역 내에 있는지 여부")

        # 인력 간섭 타입 — C2 보름 분기와 C4가 함께 쓴다. 필요한 명함이 없으면 묻지 않는다.
        self._interference = (
            ask_choice("[콜롬비나] 가장 많이 축적한 인력의 달빛 반응 타입", list(self._INTERFERENCE_TYPES))
            if c >= 2 else None
        )
        # C2 보름 분기의 대상(현재 필드 위 캐릭터)
        self._on_field = (
            self._ask_on_field_member(all_hits)
            if c >= 2 and self._radiance_active else None
        )
        # C6: 달빛 반응에 참여한 원소 타입 2가지
        self._c6_elements = self._ask_reaction_elements() if c >= 6 else ()

        # ── C2 보름 분기: 콜롬비나 HP 기반으로 필드 위 캐릭터의 코어 스탯 증가 ──────
        # 콜롬비나의 HP를 **읽는 함수**로 넘긴다(지연 기여). 같은 Phase 4에서 다른
        # 캐릭터가 콜롬비나의 HP를 올릴 수 있어서(실로닌 C2는 물 캐릭터에게 HP +45%)
        # 여기서 값을 확정하면 파티원 처리 순서가 결과를 바꾼다.
        # 출력이 코어 풀(공격력/방어력/EM)이지만 지연 기여는 순서 무관이 보장되므로
        # 정확성 가드가 봐준다 — 순환이 생기면 CyclicBuffError가 잡는다.
        if c >= 2 and self._radiance_active and self._on_field is not None:
            if moonsign_level(all_hits) is MoonsignLevel.FULL:
                source_hit = next(iter(all_hits[self].values()))
                field_name, ratio = self._C2_FULLMOON_CONVERSION[self._interference]
                value = lambda: source_hit.convertible_hp() * ratio
                for hit in all_hits[self._on_field].values():
                    # 대상 필드가 이미 '재변환 재료에서 빠지는' 조각을 가리킨다
                    # (_C2_FULLMOON_CONVERSION) — 따로 태그할 필요가 없다.
                    hit.add(field_name, value, self, note="C2 보름 전환")

    def _ask_on_field_member(self, all_hits):
        """C2 보름 분기 대상이 될 현재 필드 위 캐릭터. 파티원이 1명뿐이면 묻지 않는다."""
        members = list(all_hits.keys())
        if len(members) == 1:
            return members[0]
        options = [
            f"{char.name} ({char.element.value})" + (" ← 콜롬비나" if char is self else "")
            for char in members
        ]
        return members[ask_choice("[콜롬비나 C2] 현재 필드 위 캐릭터", options)]

    def _ask_reaction_elements(self) -> tuple:
        """C6: 달빛 반응에 참여한 원소 타입을 고른다 (없음 선택 가능)."""
        options = ["없음", "불", "물", "얼음", "번개", "바람", "바위", "풀"]
        elements = [
            None, Element.PYRO, Element.HYDRO, Element.CRYO,
            Element.ELECTRO, Element.ANEMO, Element.GEO, Element.DENDRO,
        ]
        picked = []
        for n in (1, 2):
            elem = elements[ask_choice(f"[콜롬비나 C6] 반응 참여 원소 {n}", options)]
            if elem is not None:
                picked.append(elem)
        return tuple(picked)

    # ── 파티 버프 4.5: 스탯을 읽지 않는 크로스 버프 ─────────────────────────
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # Q 「향수에 잠긴 달」: 파티 전원의 달빛 반응 피해 '증가' → 반응 보너스 계열.
        if self._domain_active:
            bl = self._burst_index()
            bonus = self._BURST_LUNAR_REACTION_DMG_BONUS[bl]
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.add("lunar_charged_bonus",     bonus, self, note="Q 향수에 잠긴 달")
                    hit.add("lunar_bloom_bonus",       bonus, self, note="Q 향수에 잠긴 달")
                    hit.add("lunar_crystallize_bonus", bonus, self, note="Q 향수에 잠긴 달")

        # 명함 「승격」: Q의 '증가'와 구분되는 계열 → elevation_multiplier.
        # 명함은 누적이므로 보유 단계의 값을 모두 더한다.
        elevation = sum(v for lv, v in self._CONSTELLATION_ELEVATION.items() if c >= lv)
        if elevation:
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.add("elevation_multiplier", elevation, self, note="명함 승격")

        # C6: 반응에 참여한 원소 타입의 치명타 피해 +80% (해당 원소 히트에만).
        # 「같은 원소 타입끼리 비중첩」이나 파티에 콜롬비나는 1명뿐이라 중복 제출이 없다.
        if c >= 6 and self._c6_elements:
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    if hit.element in self._c6_elements:
                        hit.add("crit_dmg", self._C6_ELEMENTAL_CRIT_DMG, self, note="C6 원소 치명타")

    # ── 파티 버프 5: 최종 스탯을 읽어 스케일하는 버프 (방식 B) ────────────────
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # 콜롬비나의 HP를 **읽는 함수**로 넘긴다(지연 기여) — 다른 캐릭터가 같은 단계에서
        # HP를 더해 줄 수 있어 지금 확정하면 파티원 처리 순서가 결과를 바꾼다.
        source_hit = next(iter(all_hits[self].values()))

        # Moonsign: 달빛 반응 '기본 피해' 증가 — 파티 전원의 달빛 반응 **3종 모두**에 적용된다
        # (원문: "파티 내 캐릭터가 주는 달빛 반응의 기본 피해가 증가"). 기초 피해 증가가
        # 반응별 필드로 나뉘어 있으므로 세 자리에 모두 넣는다 — Q 「향수에 잠긴 달」이 반응
        # 보너스를 셋에 넣는 것과 같다. 달감전에만 거는 이네파 Moonsign과 갈리는 자리다.
        moonsign_base = lambda: min(
            source_hit.convertible_hp() / 1000.0 * self._MOONSIGN_BASE_DMG_PER_1000_HP,
            self._MOONSIGN_BASE_DMG_CAP,
        )
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.add("lunar_charged_base_dmg_bonus",     moonsign_base, self, note="Moonsign")
                hit.add("lunar_bloom_base_dmg_bonus",       moonsign_base, self, note="Moonsign")
                hit.add("lunar_crystallize_base_dmg_bonus", moonsign_base, self, note="Moonsign")

        # C4: 이번 간섭파의 달빛 반응 피해가 콜롬비나 HP 최대치의 12.5%/2.5%/12.5%만큼 증가.
        # 피해 자체를 키우는 효과라 flat_dmg_bonus로 넣는다(코어 풀이 아니므로 Phase 5에서 안전).
        if c >= 4 and self._interference is not None:
            ratio = self._C4_INTERFERENCE_HP_RATIO[self._interference]
            for hit in self._interference_hits(all_hits[self]):
                hit.add("flat_dmg_bonus",
                        lambda: source_hit.convertible_hp() * ratio,
                        self, note="C4 간섭파")

    def _interference_hits(self, hits: dict[str, SkillHit]):
        """현재 선택된 인력 간섭 타입에 해당하는 히트들.
        달 개화만 5타로 나뉘며, C4 증가분은 각 타에 개별 적용한다."""
        prefix = ("인력 간섭 · 달감전", "인력 간섭 · 달개화", "인력 간섭 · 달결정")[self._interference]
        return [hit for name, hit in hits.items() if name.startswith(prefix)]
