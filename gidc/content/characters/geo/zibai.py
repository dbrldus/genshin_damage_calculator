from gidc.core.character import Character
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import CharacterTrait, DmgType, Element, MoonsignLevel, ReactionType
from gidc.enums import StatType
from gidc.core.party_state import moonsign_level
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_choice, ask_int


class Zibai(Character):
    """자백 (Zibai) | 바위 | 한손검 | 5성 | 어센션 스탯: 치명타 피해

    일반 공격
    검으로 최대 4번 공격한다.

    강공격
    일정 스태미나를 소모해 순간적으로 전방을 향해 검을 2번 휘두른다.

    낙하 공격
    공중에서 땅을 내려찍어 경로상의 적을 공격하고 착지 시 범위 피해를 준다.

    E : 천지일
    옛 권능의 편린을 불러일으켜 「세월의 틈새」 모드로 전환한다.
    해당 모드에서 자백이 일반 공격과 강공격 진행 시, 다른 원소 부여 효과로 대체될 수 없는 바위 원소 피해를 주는 것으로 전환된다. 또한, 서로 다른 방식을 통해 특수한 「시간의 빛」을 축적할 수 있다. 자백은 「시간의 빛」을 소모해 특수한 원소전투 스킬 백마 돌격을 발동할 수 있다.

    달빛 징조 · 보름
    「세월의 틈새」 모드에서 자백이 일반 공격 진행 시, 4단 공격 추가로 바위 원소 피해를 1회 주고, 해당 피해는 달 결정 반응 피해로 간주된다.

    Q : 천상 삼원의 법칙
    자백이 청옥 우산 지붕을 돌려 바위 원소 피해를 2회 주고, 그 중 제2단 공격 피해는 달 결정 반응 피해로 간주한다.
    발동 시, 자백이 「세월의 틈새」 모드인 경우, 이번 「세월의 틈새」 모드의 지속 시간이 1.7초 연장된다

    A1 : 달에서 강림한 선인
    원소전투 스킬 천지일체 발동 또는 달빛 조각 화음 발동 시, 자백은 4초 동안 지속되는 「달빛 강림」 효과를 획득한다: 백마 돌격의 제2단 공격으로 주는 피해가 자백 방어력의 60%만큼 증가한다.

    A4 : 운해를 가르는 산맥
    파티에 바위 원소 타입의 다른 캐릭터가 1명 존재할 때마다 자백의 방어력이 15% 증가한다. 파티에 물 원소 타입의 다른 캐릭터가 1명 존재할 때마다 자백의 원소 마스터리가 60pt 증가한다

    C1 : 홀연한 탄생과 고요한 끝
    원소전투 스킬 천지일체 발동 후, 자백이 즉시 「시간의 빛」을 100포인트를 축적하고, 「세월의 틈새」 모드에서 백마 돌격의 최대 사용 가능 횟수가 5회로 증가한다.
    또한, 「세월의 틈새」 모드로 전환할 때마다 첫 번째 백마 돌격 발동 시, 제2단 공격으로 주는 달 결정 반응 피해가 220% 증가한다.

    C2 : 생사의 섭리
    「세월의 틈새」 모드일 때, 주변에 있는 파티 내 모든 캐릭터의 달 결정 반응으로 주는 피해가 30% 증가한다.

    달빛 징조 · 보름: 돌파 특성 달에서 강림한 선인의 효과가 강화된다: 백마 돌격의 제2단 공격으로 주는 피해가 자백 방어력의 550%만큼 추가로 증가한다. 해당 효과는 돌파 특성 달에서 강림한 선인을 해금해야 한다.

    C3 : 무소유
    원소전투 스킬 천지 일체의 스킬 레벨+3
    최대 Lv.15까지 상승

    C4 : 혼을 따르는 육신
    「세월의 틈새」 모드일 때, 자백의 일반 공격 콤보수가 초기화되지 않으며, 백마 돌격이 적 명중 시 자백은 「월화」 효과를 획득한다: 다음 일반 공격 시, 4단의 추가 공격이 기존 피해의 250%에 해당하는 달 결정 반응 피해를 준다.

    C5 : 침묵으로 깨달은 도리
    원소폭발 천상 삼원의 법칙의 스킬 레벨+3
    최대 Lv.15까지 상승

    C6 : 천지를 스쳐가는 여정
    「세월의 틈새」 모드일 때, 자백의 「시간의 빛」 축적 효율이 50% 증가한다.
    또한, 백마 돌격이 모든 「시간의 빛」을 소모하도록 변경된다. 소모한 「시간의 빛」이 70pt를 초과하면 초과 소모한 「시간의 빛」 1pt마다 이번 백마 돌격과 이어지는 3초 동안 자백이 주는 달 결정 반응 피해가 1.6% 승격된다. 해당 효과는 중첩되지 않는다.

    달빛 징조의 축복 · 빛의 흐름
    파티 내 캐릭터가 물 원소 결정 반응 발동 시, 달 결정 반응으로 전환되며, 자백의 방어력에 기반해 파티 내 캐릭터가 주는 달 결정 반응의 기본 피해가 증가한다: 방어력 100pt마다 달 결정 반응 기본 피해가 0.7% 증가하며, 해당 방식으로 피해는 최대 14% 증가한다.

    또한, 자백이 파티에 있을 때 파티의 달빛 징조가 1레벨 상승한다

    세월의 틈새
    원소전투 스킬 천지일체 발동 후, 자백은 이 모드로 전환된다. 이 모드는 최대 15초 동안 지속되며 다음과 같은 특성을 가진다:
    · 일반 공격과 강공격 시, 다른 원소 부여 효과로 대체되지 않는 바위 원소 피해를 주는 것으로 전환된다.

    · 원소전투 스킬 천지일체가 특수 원소전투 스킬 백마 돌격으로 대체된다: 자백이 「시간의 빛」 70pt 이상 보유 시, 자백은 「시간의 빛」을 70pt 소모해 백마 돌격을 발동하여 2회의 바위 원소 피해를 준다, 이 중 제2단 공격 피해는 달 결정 반응 피해로 간주된다.

    「시간의 빛」 최대치는 100pt이며, 자백은 아래의 방법으로 「시간의 빛」을 축적할 수 있다:
    · 「세월의 틈새」 모드일 때, 1초마다 「시간의 빛」을 10pt 축적한다.
    · 일반 공격이 적 명중 시, 「시간의 빛」을 5pt 축적한다, 자백은 해당 방식으로 0.5초마다 「시간의 빛」을 최대 1회 축적할 수 있다.

    달빛 징조 · 보름
    주변에 있는 파티 내 캐릭터가 달 결정 반응 발동 시, 자백이 「시간의 빛」을 35pt 축적한다. 자백은 해당 방식으로 4초마다 「시간의 빛」을 최대 1회 축적할 수 있다.
    특수 원소전투 스킬 「백마 돌격」을 발동하면 해당 방식으로 축적한 「시간의 빛」의 재사용 대기시간이 초기화된다.

    「백마 돌격」을 4회 발동하거나 지속 시간이 종료 시, 자백은 해당 모드를 종료한다
    """
    name = "자백"
    weapon_type = WeaponType.SWORD
    # 놋 크라이 출신 — 파티 달빛 징조에 기여한다.
    # 「빛의 흐름」의 "파티의 달빛 징조가 1레벨 상승"은 이 특성이 곧 그 상승이다 —
    # party_state의 인원수 임계값 표가 이미 그렇게 센다(린네아·이네파도 같은 문구다).
    # 파티에 있으면 물 원소 결정 → 달결정으로 전환된다(core.reaction.lunar_candidates).
    innate_traits = frozenset({
        CharacterTrait.MOONSIGN,
        CharacterTrait.LUNAR_CRYSTALLIZE_CONVERTER,
    })

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # ── 일반공격 (L1~L11) ──
    _NA_HIT1 = [0.506, 0.547, 0.588, 0.647, 0.688, 0.735, 0.800, 0.864, 0.929, 0.999, 1.070]
    _NA_HIT2 = [0.466, 0.503, 0.541, 0.595, 0.633, 0.677, 0.736, 0.796, 0.855, 0.920, 0.985]
    # 3단은 같은 계수로 2타가 들어간다 — 히트는 build_hits에서 두 개 세운다.
    _NA_HIT3 = [0.309, 0.334, 0.359, 0.395, 0.420, 0.449, 0.489, 0.528, 0.568, 0.611, 0.654]
    _NA_HIT4 = [0.779, 0.842, 0.906, 0.996, 1.060, 1.132, 1.232, 1.331, 1.431, 1.540, 1.649]
    # 강공격도 같은 계수로 2타 — 「순간적으로 전방을 향해 검을 2번 휘두른다」
    _CA = [0.737, 0.797, 0.857, 0.942, 1.002, 1.071, 1.165, 1.259, 1.353, 1.456, 1.559]
    _PLUNGE = [0.6390, 0.6910, 0.7430, 0.8180, 0.8700, 0.9290, 1.0110, 1.0930, 1.1750, 1.2640, 1.3530]
    _LOW_PLUNGE = [1.278, 1.382, 1.487, 1.635, 1.739, 1.858, 2.022, 2.185, 2.349, 2.527, 2.705]
    _HIGH_PLUNGE = [1.597, 1.727, 1.857, 2.042, 2.172, 2.321, 2.525, 2.729, 2.934, 3.156, 3.379]

    # ── 원소스킬 (L1~L13) ──
    _RIFT_NA1 = [
        0.5658, 0.6082, 0.6507, 0.7072, 0.7497,
        0.7921, 0.8487, 0.9053, 0.9618, 1.0184,
        1.0750, 1.1316, 1.2023,
    ]
    _RIFT_NA2 = [
        0.5210, 0.5601, 0.5992, 0.6513, 0.6903,
        0.7294, 0.7815, 0.8336, 0.8857, 0.9378,
        0.9899, 1.0420, 1.1071,
    ]
    # 3단은 같은 계수로 2타
    _RIFT_NA3 = [
        0.3457, 0.3716, 0.3975, 0.4321, 0.4580,
        0.4840, 0.5185, 0.5531, 0.5877, 0.6222,
        0.6568, 0.6914, 0.7346,
    ]
    _RIFT_NA4 = [
        0.8718, 0.9372, 1.0026, 1.0897, 1.1551,
        1.2205, 1.3077, 1.3949, 1.4820, 1.5692,
        1.6564, 1.7436, 1.8525,
    ]
    # 강공격도 같은 계수로 2타
    _RIFT_CA = [
        0.6595, 0.7090, 0.7584, 0.8244, 0.8738,
        0.9233, 0.9892, 1.0552, 1.1212, 1.1871,
        1.2531, 1.3190, 1.4014,
    ]
    # build_hits에서 달결정 직접 피해로 세운다(달·별 히트는 coeff_amp가 아니라 coeff).
    _RIFT_NA4_EXTRA = [
        0.2946, 0.3167, 0.3387, 0.3682, 0.3903,
        0.4124, 0.4418, 0.4713, 0.5008, 0.5302,
        0.5597, 0.5891, 0.6259,
    ]
    # 백마 돌격 — 「시간의 빛」 70pt를 소모하는 특수 원소전투 스킬. 2단은 달결정 피해.
    _CHARGE_HIT1 = [
        1.7253, 1.8547, 1.9841, 2.1566, 2.2860,
        2.4154, 2.5879, 2.7604, 2.9330, 3.1055,
        3.2780, 3.4506, 3.6662,
    ]
    _CHARGE_HIT2 = [
        1.4097, 1.5154, 1.6211, 1.7621, 1.8678,
        1.9736, 2.1145, 2.2555, 2.3965, 2.5374,
        2.6784, 2.8194, 2.9956,
    ]

    # ── 원소폭발 (L1~L13) ──
    _BURST_HIT1 = [
        1.2696, 1.3648, 1.4600, 1.5870, 1.6822,
        1.7774, 1.9044, 2.0314, 2.1583, 2.2853,
        2.4122, 2.5392, 2.6979,
    ]
    # 2단은 「달 결정 반응 피해로 간주」된다 — build_hits에서 달결정 직접 피해로 세운다.
    _BURST_HIT2 = [
        1.7774, 1.9107, 2.0441, 2.2218, 2.3551,
        2.4884, 2.6662, 2.8439, 3.0216, 3.1994,
        3.3771, 3.5549, 3.7771,
    ]

    # ── 상수 (레벨로 스케일하지 않는 값) ──
    _TIME_LIGHT_MAX                = 100     # 「시간의 빛」 수지 — 자원 모델이 없어 피해식에는 안 들어간다. C6 상한 유도에만 쓴다.
    _TIME_LIGHT_COST               = 70
    _MAX_CHARGES                   = 4       # 백마 돌격 4회 발동 시 모드 종료
    _A1_CHARGE2_DEF_RATIO          = 0.60    # A1 달에서 강림한 선인 — 백마 돌격 2단 피해가 자백 방어력의 60%만큼 증가
    _A4_GEO_DEF_PCT                = 0.15    # A4 운해를 가르는 산맥 — 다른 바위 1명당 방어력 +15%, 다른 물 1명당 원소 마스터리 +60
    _A4_HYDRO_EM                   = 60
    _C1_TIME_LIGHT_GAIN            = 100     # 발동 즉시 축적 (수지)
    _C1_MAX_CHARGES                = 5       # 백마 돌격 최대 사용 횟수 (수지)
    _C1_FIRST_CHARGE2_BONUS        = 2.20    # 첫 백마 돌격의 2단 달결정 피해 증가
    _C2_PARTY_LUNAR_BONUS          = 0.30    # 파티 전원의 달 결정 반응 피해 증가
    _C2_FULLMOON_CHARGE2_DEF_RATIO = 5.50    # 보름: A1이 해금돼 있어야 붙는 추가 증가
    _C4_MOONFLOWER_MULT            = 2.50    # C4 혼을 따르는 육신 — 「월화」의 4단 추가 공격이 기존 피해의 250%
    _C6_TIME_LIGHT_EFFICIENCY      = 0.50    # 축적 효율 (수지)
    _C6_ELEVATION_THRESHOLD        = 70      # 이 값을 넘긴 1pt마다
    _C6_ELEVATION_PER_POINT        = 0.016   # 달 결정 반응 피해 승격
    _MOONSIGN_BASE_PER_100_DEF     = 0.007   # 달빛 징조의 축복 · 빛의 흐름 — 방어력 100pt마다 달결정 기본 피해 증가, 상한 있음
    _MOONSIGN_BASE_CAP             = 0.14

    # A1·C1·C2 보름이 이름으로 골라 쓰는 히트. build_hits와 훅들이 같은 문자열을 읽게
    # 묶어 둔다 — 한쪽만 고치면 보너스가 아무 히트에도 안 붙고 아무 데서도 안 걸린다.
    CHARGE2_HIT = "백마 돌격 2단 공격 피해"
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 3
    BURST_LEVEL_UP_CONSTELLATION = 5
    NA_TABLES = (_NA_HIT1, _NA_HIT2, _NA_HIT3, _NA_HIT4, _CA, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_RIFT_NA1, _RIFT_NA2, _RIFT_NA3, _RIFT_NA4, _RIFT_CA, _RIFT_NA4_EXTRA, _CHARGE_HIT1, _CHARGE_HIT2,)
    BURST_TABLES = (_BURST_HIT1, _BURST_HIT2,)

    rarity         = 5
    ascension_stat = StatType.CRIT_DMG

    @property
    def element(self) -> Element: return Element.GEO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        """평상시 히트와 「세월의 틈새」 모드 히트를 **둘 다** 세운다.

        모드 전환은 로테이션이 정하고 히트 생성(Phase 1)은 그것을 모른다. 서로 배타적인
        히트는 둘 다 세워 두고 어느 쪽을 합산할지는 화면을 읽는 쪽이 고른다 — 산드로네의
        섬광 상태 두 계열과 같은 규약이다.

        달빛 징조·보름에서만 붙는 히트도 마찬가지로 이름에 「보름」을 달아 세워 둔다.
        """
        nl = self._na_index()
        sk = self._skill_index()   # C3: 레벨 +3
        bl = self._burst_index()   # C5: 레벨 +3

        hits: list[SkillHit] = []

        # ── 평상시 일반 공격 (물리, 공격력) ──────────────────────────────────
        hits.append(SkillHit("1단 공격 피해", SkillType.NORMAL_ATK, self._NA_HIT1[nl], ScalingStat.ATK))
        hits.append(SkillHit("2단 공격 피해", SkillType.NORMAL_ATK, self._NA_HIT2[nl], ScalingStat.ATK))
        # 3단은 같은 계수로 2타
        for i in (1, 2):
            hits.append(SkillHit(f"3단 공격 피해 {i}타", SkillType.NORMAL_ATK, self._NA_HIT3[nl], ScalingStat.ATK))
        hits.append(SkillHit("4단 공격 피해", SkillType.NORMAL_ATK, self._NA_HIT4[nl], ScalingStat.ATK))
        # 강공격도 같은 계수로 2타 — 「검을 2번 휘두른다」
        for i in (1, 2):
            hits.append(SkillHit(f"강공격 피해 {i}타", SkillType.CHARGED_ATK, self._CA[nl], ScalingStat.ATK))

        hits.append(SkillHit("낙하 기간 피해",      SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK))

        # ── 「세월의 틈새」 모드의 일반/강공격 (바위, 방어력) ─────────────────
        # 스킬 종류는 여전히 일반 공격·강공격이다 — 계수 표가 E에 있을 뿐 원문은
        # 「일반 공격과 강공격 진행 시 … 바위 원소 피해를 주는 것으로 전환된다」다.
        hits.append(SkillHit("세월의 틈새 1단 공격 피해", SkillType.NORMAL_ATK, self._RIFT_NA1[sk], ScalingStat.DEF, Element.GEO))
        hits.append(SkillHit("세월의 틈새 2단 공격 피해", SkillType.NORMAL_ATK, self._RIFT_NA2[sk], ScalingStat.DEF, Element.GEO))
        for i in (1, 2):
            hits.append(SkillHit(f"세월의 틈새 3단 공격 피해 {i}타", SkillType.NORMAL_ATK, self._RIFT_NA3[sk], ScalingStat.DEF, Element.GEO))
        hits.append(SkillHit("세월의 틈새 4단 공격 피해", SkillType.NORMAL_ATK, self._RIFT_NA4[sk], ScalingStat.DEF, Element.GEO))
        for i in (1, 2):
            hits.append(SkillHit(f"세월의 틈새 강공격 피해 {i}타", SkillType.CHARGED_ATK, self._RIFT_CA[sk], ScalingStat.DEF, Element.GEO))

        # E 보름 : 4단 공격에 추가로 1회. 「달 결정 반응 피해로 간주」된다.
        hits.append(SkillHit(
            "세월의 틈새 제4단 공격 추가 피해 (보름)", SkillType.NORMAL_ATK,
            self._RIFT_NA4_EXTRA[sk], ScalingStat.DEF, Element.GEO,
            reaction_type=ReactionType.LUNAR_CRYSTALLIZE, dmg_type=DmgType.LUNAR_DIRECT,
        ))
        # C4 「월화」 : 그 추가 공격이 기존 피해의 250%. 기존 히트를 대체하는 강화판이라
        # 배타적이므로 둘 다 세워 둔다. 보름 조건은 기본 히트에서 물려받는다(사용자 확인) —
        # C4 원문에 보름 줄이 따로 없지만, 강화 대상인 「기존 피해」가 보름 전용이다.
        #
        # 달·별 히트는 coeff_amp가 아니라 **coeff**를 키운다 — 공식에 coeff_amp 자리가
        # 없어 조용히 무효가 된다.
        if self.constellation >= 4:
            hits.append(SkillHit(
                "세월의 틈새 제4단 공격 추가 피해 (보름·C4 월화)", SkillType.NORMAL_ATK,
                self._RIFT_NA4_EXTRA[sk] * self._C4_MOONFLOWER_MULT, ScalingStat.DEF, Element.GEO,
                reaction_type=ReactionType.LUNAR_CRYSTALLIZE, dmg_type=DmgType.LUNAR_DIRECT,
            ))

        # ── 백마 돌격 — 「시간의 빛」 70pt를 소모하는 특수 원소전투 스킬 ──────
        hits.append(SkillHit("백마 돌격 1단 공격 피해", SkillType.SKILL, self._CHARGE_HIT1[sk], ScalingStat.DEF, Element.GEO))
        hits.append(SkillHit(
            self.CHARGE2_HIT, SkillType.SKILL, self._CHARGE_HIT2[sk], ScalingStat.DEF, Element.GEO,
            reaction_type=ReactionType.LUNAR_CRYSTALLIZE, dmg_type=DmgType.LUNAR_DIRECT,
        ))

        # ── 원소 폭발 — 2회, 그 중 2단이 달결정 피해 ─────────────────────────
        hits.append(SkillHit("원소 폭발 1단 공격 피해", SkillType.BURST, self._BURST_HIT1[bl], ScalingStat.DEF, Element.GEO))
        hits.append(SkillHit(
            "원소 폭발 2단 공격 피해", SkillType.BURST, self._BURST_HIT2[bl], ScalingStat.DEF, Element.GEO,
            reaction_type=ReactionType.LUNAR_CRYSTALLIZE, dmg_type=DmgType.LUNAR_DIRECT,
        ))

        return {h.name: h for h in hits}

    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        c = self.constellation

        # ── 유저 입력 ────────────────────────────────────────────────────────
        # 「세월의 틈새」 모드 여부가 C2·C6을 함께 가른다 — 한 번만 묻고 self에 저장해
        # 뒤 단계(Phase 4.5)가 재사용한다.
        self._rift = ask_bool("[자백 E] 「세월의 틈새」 모드 여부")
        # A1 「달빛 강림」은 4초짜리 버프라 로테이션이 정한다. C2 보름 분기도 이 답을 쓴다.
        self._moonlight_descent = ask_bool("[자백 A1] 「달빛 강림」 효과 보유 여부")
        # C1 : 모드 전환 후 **첫 번째** 백마 돌격에만 붙는다.
        self._first_charge = (
            ask_bool("[자백 C1] 이번 백마 돌격이 모드 전환 후 첫 번째인지 여부")
            if c >= 1 and self._rift else False
        )
        # C6 : 백마 돌격이 「시간의 빛」을 전부 소모한다. 상한은 축적 최대치에서 유도한다.
        self._time_light_spent = (
            ask_int("[자백 C6] 이번 백마 돌격이 소모한 「시간의 빛」",
                    min_val=self._TIME_LIGHT_COST, max_val=self._TIME_LIGHT_MAX)
            if c >= 6 and self._rift else 0
        )

        charge2 = hits.get(self.CHARGE2_HIT)

        # ── C1 : 첫 백마 돌격의 2단 달 결정 반응 피해 +220% ───────────────────
        # 「달 결정 반응 피해가 220% 증가」 → 반응 보너스 계열이다(공식의 %Reaction 자리,
        # damage._calc_lunar_direct). 스탯을 읽지 않으므로 여기서 값으로 넣는다.
        if self._first_charge and charge2 is not None:
            charge2.add("lunar_crystallize_bonus", self._C1_FIRST_CHARGE2_BONUS,
                        self, note="C1 첫 백마 돌격")

        # ── C6 : 70pt를 넘긴 1pt마다 **자백이 주는** 달 결정 반응 피해 승격 ────
        # 「자백이 주는」이라 자기 히트에만 건다 — 파티 전원에 거는 C2와 갈리는 자리다.
        # 승격은 반응별 필드라 달결정 자리에만 들어간다(profile.celestial_elevation_field).
        overflow = max(0, self._time_light_spent - self._C6_ELEVATION_THRESHOLD)
        if overflow:
            for hit in hits.values():
                hit.add("lunar_crystallize_elevation",
                        overflow * self._C6_ELEVATION_PER_POINT, self, note="C6 시간의 빛 승격")

    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # ── A4 운해를 가르는 산맥 ────────────────────────────────────────────
        # 파티 구성만으로 정해지므로 묻지 않고 센다. 「**다른** 캐릭터가 1명 존재할 때마다」
        # 라 자신은 빼고 센다 — 바위인 자백을 세면 혼자서도 +15%가 붙는다.
        #
        # 받는 쪽이 자기뿐인 자기 버프지만 Phase 3이 아니라 여기다 — apply_self_buffs는
        # 자기 히트만 받아 파티 구성을 볼 수 없다. 코어 풀에 넣는 **고정값**이라 이 단계의
        # 계약에 맞는다.
        others = [char for char in all_hits if char is not self]
        geo   = sum(1 for char in others if char.element is Element.GEO)
        hydro = sum(1 for char in others if char.element is Element.HYDRO)

        for hit in all_hits[self].values():
            if geo:
                hit.add("def_pct", self._A4_GEO_DEF_PCT * geo, self, note="A4 바위 동료")
            if hydro:
                # 고정 수치로 부여되는 EM이라 em_from_flat이다 — 다른 스탯의 %에서 파생된
                # 지분(em_from_pct_share)이 아니므로 EM 재변환 버프의 재료가 된다.
                hit.add("em_from_flat", self._A4_HYDRO_EM * hydro, self, note="A4 물 동료")

    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # ── C2 생사의 섭리 : 모드 중 파티 전원의 달 결정 반응 피해 +30% ───────
        # 「주는 피해가 증가」 → 반응 보너스 계열(C1과 같은 자리, 승격이 아니다).
        # C6과 달리 **파티 전원**이 대상이다.
        if self.constellation >= 2 and self._rift:
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.add("lunar_crystallize_bonus", self._C2_PARTY_LUNAR_BONUS,
                            self, note="C2 생사의 섭리")

    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # 자백의 방어력을 **읽는 함수**로 넘긴다(지연 기여) — 자기 A4와 다른 캐릭터의
        # 기여가 같은 단계에서 그 방어력을 올릴 수 있어, 지금 확정하면 순서가 결과를 바꾼다.
        # 항상 같은 히트(첫 히트)를 읽어 값이 하나로 정해지게 한다.
        source_hit = next(iter(all_hits[self].values()))

        # ── 달빛 징조의 축복 · 빛의 흐름 ─────────────────────────────────────
        # 방어력 100pt마다 달 결정 반응 **기본 피해** +0.7%, 최대 +14%(방어력 2000에서 상한).
        # 달결정 전용 필드라 직접 피해 히트와 파티 반응 피해가 같은 값을 읽는다.
        moonsign_base = lambda: min(
            source_hit.convertible_def() / 100.0 * self._MOONSIGN_BASE_PER_100_DEF,
            self._MOONSIGN_BASE_CAP,
        )
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.add("lunar_crystallize_base_dmg_bonus", moonsign_base, self,
                        note="달빛 징조 빛의 흐름")

        # ── A1 달에서 강림한 선인 (+ C2 보름 강화) ───────────────────────────
        # 「백마 돌격 2단으로 주는 피해가 방어력의 N%만큼 증가」 → 피해에 직접 더하는
        # 고정값이라 flat_dmg_bonus다. 달결정 **직접** 피해는 이 항을 읽는다
        # (damage._calc_lunar_direct). C2 보름은 「A1을 해금해야」 붙는 추가분이라
        # 같은 게이트(_moonlight_descent) 아래에 둔다.
        charge2 = all_hits[self].get(self.CHARGE2_HIT)
        if charge2 is not None and self._moonlight_descent:
            ratio = self._A1_CHARGE2_DEF_RATIO
            if (self.constellation >= 2
                    and moonsign_level(all_hits) is MoonsignLevel.FULL):
                ratio += self._C2_FULLMOON_CHARGE2_DEF_RATIO
            charge2.add("flat_dmg_bonus",
                        lambda: source_hit.convertible_def() * ratio,
                        self, note="A1 달빛 강림")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 「시간의 빛」 수지 전반 — 자원 모델이 없다. 축적 속도(1초 10pt·명중 5pt·보름 35pt),
    #   C1의 즉시 100pt, C6의 축적 효율 +50%는 전부 「몇 번 쏘느냐」를 정할 뿐 히트 단가가
    #   아니다(_TIME_LIGHT_MAX / _C1_TIME_LIGHT_GAIN / _C6_TIME_LIGHT_EFFICIENCY).
    #   피해에 들어가는 것은 C6이 소모한 양 하나뿐이라 그것만 묻는다.
    # · 백마 돌격 사용 횟수(기본 4회 / C1 5회, _MAX_CHARGES·_C1_MAX_CHARGES) — 로테이션
    #   빈도지 히트 단가가 아니다. 화면을 읽는 쪽이 몇 번을 합산할지 고른다.
    # · 「세월의 틈새」 지속 시간과 Q의 1.7초 연장 — 같은 이유.
    # · C4의 「일반 공격 콤보수가 초기화되지 않는다」 — 로테이션 편의지 피해항이 아니다.
    # · A1·C2 보름의 「달빛 조각 화음 발동 시」 트리거 — 화음 발동 빈도라 히트 단가가
    #   아니다. 효과가 걸렸는지 여부만 묻는다(_moonlight_descent).
    # · 자백과 린네아를 함께 편성했을 때 「방어력 기반 달결정 기본 피해 증가」가 합산된다.
    #   문구도 수치도 같은 「달빛 징조의 축복」이라 실제로는 비중첩일 수 있으나 실측 전이며,
    #   합산이 기존 선례(콜롬비나 Moonsign)와 일관된다 — 사용자 확인을 거친 자리다.
