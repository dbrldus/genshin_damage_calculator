from gidc.core.character import Character
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.core.reaction import stellar_conditions
from gidc.enums import CharacterTrait, DmgType, Element, ReactionType
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_choice, ask_int


class Sandrone(Character):
    """산드로네 (Sandrone) | 얼음 | 양손검 | 5성 | 어센션 스탯: 치명타 확률

    일반 공격 : 계산식을 직조하여 병기를 조종하는 실을 만들고, 검으로 최대 3번 공격한다.
    강공격 :
    만능 범용 자동 장치 「파지오」를 소환하여 파지오를 연산 모드로 전환한다: 전방의 적에게 난사 공격을 하고, 주기적으로 냉각 광선을 발사하여 얼음 원소 범위 피해를 준다.
    섬광·별빛: 냉각 광선이 상응하는 별빛 반응 피해로 간주되는 얼음 원소 범위 피해를 주는 것으로 전환된다.
    연산 모드에서 파지오의 연산량이 지속적으로 증가하고, 냉각 광선 발사 시 연산량이 추가로 증가한다.
    연산량이 최대치인 100에 도달하면 파지오는 연산 과열 모드로 전환되어, 더 긴 간격으로 적에게 사격하여 얼음 원소 피해를 준다. 또한 연산 모드로 전환할 수 없다.
    연산 모드가 아닐 때 파지오의 연산량은 서서히 감소한다. 산드로네가 대기 상태일 때는 파지오 수리에 집중하여 연산량 감소 속도가 기전의 300%까지 빨라진다.
    연산량이 50 미만으로 감소하면 파지오가 연산 과열 모드를 해제한다.

    낙하 공격 : 공중에서 땅을 내려찍어 경로상의 적을 공격하고 착지 시 범위 피해를 입힌다.

    E : 현상 계산식·자유로운 해석
    숙녀의 완벽한 법도를 갖춰 티타임용 특수작전 장치에 탑승하여 6초 동안 전방으로 6초 동안 부유한다.
    이 기간 동안 산드로네는 부유 방향을 조작할 수 있으며, 대시를 짧게 누르면 스태미나를 10pt 소모해 우아한 고속 부유 모드에 진입하고,
    1초당 스태미나를 15pt씩 소모해 더 빠른 속도로 부유한다.
    부유를 시작할 때 주변에 적이 있으면, 산드로네는 프리즘 공명포를 1개 소환해 냉정하지 않은 적에게 프리즘 탄환을 2발 발사해 얼음 원소 피해를 준다.
    섬광·별빛: 두 번째 프리즘 결정 탄환은 상응하는 별빛 반응 피해로 간주되는 얼음 원소 피해를 준다.

    티타임용 특수작전 장치에 탑승하면 산드로네는 우아한 자태로 조용히 파지오를 수리해, 탑승 시작 시에는 연산량을 40pt씩 감소시키고, 탑승 기간에는 0.1초마다 추가로 10pt씩 감소시킨다

    Q : 현상 계산식·Q.E.D
    숙녀의 우아한 예의를 갖추고, 대량의 프리즘 공명포를 소환해 전방에 광역 폭격을 퍼붓고,
    부성 온도 광선을 발사해 적을 공격하여 얼음 원소 범위 피해를 준다.
    섬광·별빛 : 부성 온도 광선이 상응하는 별빛 반응 피해로 간주되는 얼음 원소 범위 피해를 주도록 전환된다

    A1 : 유구한 연산 장치
    섬광·별빛: 원소전투 스킬 현상 계산식·자유로운 해석 발동 시, 파지오의 연산량이 50pt를 초과하면 연산량을 감소시키는 동시에,
    주변의 적에게 발사된 두 번째 프리즘탄이 기존의 400%에 해당하는 피해를 준다.
    또한, 파지오의 연산량이 10pt 감소할 때마다 60초 동안 지속되는 개선 전술 효과를 1스택 획득하며, 해당 효과는 최대 10스택까지 중첩된다.
    산드로네가 섬광·별 초전도 상태에서 원소폭발 현상 계산식·Q.E.D를 발동하면 전술 개선 스택이 전부 제거되고, 부성 온도 광선이 기존의 100% + 제거된 스택 수 x 10%에 해당하는 피해를 준다

    A4 : 숙녀의 에티켓
    산드로네의 공격력을 기반으로 원소 마스터리를 증가시킨다.
    공격력 100마다 산드로네의 원소 마스터리가 8 증가하며, 이 방식으로 최대 160까지 증가할 수 있다.

    Stellar : 별빛 축복·이성의 빛
    극지의 별영역 내에 있을 때/파티 내 캐릭터가 주변에 별 확산 반응 발동 후 8초 동안, 산드로네는 각각 섬광 별 초전도/섬광 별 확산 상태에 진입한다.
    파티 내 캐릭터가 초전도/얼음 원소 확산 반응을 발동할 시 별 초전도/별 확산 반응 발동으로 전환되며, 산드로네의 공격력을 기반으로 파티 내 캐릭터가 주는 상술한 반응의 기본 피해가 증가한다:
    공격력 100pt당 상술한 반응의 기본 피해가 0.7% 증가하며, 이 방식으로 최대 14%까지 피해를 증가시킬 수 있다.

    C1 : 노을에 바래지 않은 금칠
    연산 모드에서 파지오의 연산량 증가 속도가 50% 감소하고, 파티 내 모든 캐릭터가 주는 별빛 반응 피해가 30% 증가한다

    C2 : 거울 속 흘러간 세월
    섬광·별빛: 강공격으로 발사한 냉각 광선의 치명타 피해가 40% 증가한다.
    또한 냉각 광선을 발사할 때마다 이번 연산 모드에서 발사하는 모든 냉각 광선으로 주는 치명타 피해가 추가로 20% 증가한다.
    해당 효과 최대 중첩수: 3스택

    C3 : 하루에 미련 없는 마음
    일반 공격 현상 계산식·공리의 스킬 레벨+3

    C4 : 숫자로 이루어진 만상
    산드로네의 별 초전도/별 확산 반응 피해가 적 명중 시, 추가로 프리즘 공명포 1대를 소환해 협동 공격을 진행하여 적에게 산드로네 공격력의 125%에 해당하는 얼음 원소 피해를 1회 준다.
    해당 피해는 상응하는 별빛 반응으로 주는 피해로 간주된다. 해당 효과는 4초마다 최대 1회 발동된다.

    C5 : 스러져도 명료한 이치
    원소폭발 현상 계산식·QED의 스킬 레벨+3

    C6 : 수선화 꿈에서 깬 아침
    연산 모드에서 파지오가 세 번째 냉각 광선 발사 시, 더 강한 집중 냉각 광선 지속 발사로 전환되며, 이어서 발사하는 기존 냉각 광선에 추가로 산드로네 공격력의 100%에 해당하는 얼음 원소 범위 피해를 준다, 최대: 4단.
    섬광·별빛: 집중 냉각 광선이 상응하는 별빛 반응 피해로 간주되는 얼음 원소 범위 피해를 주는 것으로 전환된다. 최대:4단.
    해당 피해는 산드로네 공격력의:
    섬광 별 초전도: 80%, 섬광 별 확산: 120%

    또한, 산드로네가 주는 모든 별빛 반응 피해가 20% 승격된다.
    """
    name = "산드로네"
    weapon_type = WeaponType.CLAYMORE
    # 별 반응 **두 계열 모두**의 전환자다 — Stellar 원문이 「초전도/얼음 원소 확산 반응을
    # 발동할 시 별 초전도/별 확산으로 전환」이라고 둘을 나란히 말한다. 파티에 있으면 그
    # 판정이 따라온다(core.reaction.stellar_conditions).
    # 별 확산은 바람 파티원이 있어야 성립하므로 등록된 캐릭터만으로는 아직 서지 않는다.
    # 달빛 징조(MOONSIGN)는 아니다 — 산드로네의 파티 특성은 「별빛 축복」이지 달빛 징조가 아니다.
    innate_traits = frozenset({
        CharacterTrait.STELLAR_CONDUCT_CONVERTER,
        CharacterTrait.STELLAR_SWIRL_CONVERTER,
    })

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # 일반 공격 (% ATK, L1~L13) — C3가 **일반 공격** 레벨을 +3 올리므로 L13까지 필요하다.
    # (E를 올리는 명함이 없는 대신 C3가 평타를 올린다 — 등록 캐릭터 중 첫 사례다.)
    # 검으로 때리는 3타라 원소가 붙지 않는다 → 물리 피해.
    _NA_HIT1 = [0.763, 0.825, 0.887, 0.976, 1.038, 1.109, 1.206, 1.304, 1.402, 1.508, 1.614, 1.721, 1.827]
    _NA_HIT2 = [0.672, 0.727, 0.781, 0.859, 0.914, 0.977, 1.063, 1.149, 1.235, 1.328, 1.422, 1.516, 1.610]
    _NA_HIT3 = [1.028, 1.112, 1.195, 1.315, 1.399, 1.494, 1.626, 1.757, 1.889, 2.032, 2.176, 2.319, 2.463]

    # 강공격 = 파지오 소환(연산 모드). 스태미나 소모 0pt.
    # 난사와 냉각 광선 둘 다 얼음 원소다(유저 확인). 섬광·별빛 상태에서는 냉각 광선이
    # 「상응하는 별빛 반응」 피해로 **전환**되므로 계수 표가 따로 있다 — 세 열은 같은
    # 히트의 세 상태이지 함께 들어가는 값이 아니다.
    #
    # 연산 과열 모드에서는 냉각 광선이 아예 나가지 않고 난사만 발사되며, 그 계수는 난사와
    # **같다**(유저 확인). 숫자가 같아도 열을 따로 세워 어느 모드의 사격인지 이름이 말하게 한다.
    #
    # 별 확산 열은 전환 전 계수와 **숫자가 같다**(유저 확인). 그래도 같은 표를 돌려 쓰지 않고
    # 열을 따로 세운다 — 한쪽만 바뀌는 날 조용히 어긋나지 않게, 그리고 어느 열이 어느 계열인지
    # 이름이 말하게 하려는 것이다. 전환 전의 2/3인 것은 별 초전도 열뿐이다.
    _CA_STRAFE          = [0.430, 0.465, 0.500, 0.550, 0.585, 0.625, 0.680, 0.735, 0.790, 0.850, 0.910, 0.970, 1.030]
    _CA_OVERHEAT_SHOT   = [0.430, 0.465, 0.500, 0.550, 0.585, 0.625, 0.680, 0.735, 0.790, 0.850, 0.910, 0.970, 1.030]
    _CA_COOLANT         = [1.226, 1.325, 1.425, 1.568, 1.667, 1.781, 1.938, 2.095, 2.252, 2.423, 2.594, 2.765, 2.936]
    _CA_COOLANT_CONDUCT = [0.817, 0.884, 0.950, 1.045, 1.111, 1.188, 1.292, 1.397, 1.501, 1.615, 1.729, 1.843, 1.957]
    _CA_COOLANT_SWIRL   = [1.226, 1.325, 1.425, 1.568, 1.667, 1.781, 1.938, 2.095, 2.252, 2.423, 2.594, 2.765, 2.936]

    # 낙하 공격 (% ATK, L1~L13) — 양손검 표준표(나비아와 L1~L11이 표시 자릿수까지 같다).
    # 나비아 표를 그대로 쓰지 않는 것은 C3 때문에 L12·L13 행이 더 필요하기 때문이다.
    _PLUNGE      = [0.746, 0.807, 0.867, 0.954, 1.015, 1.084, 1.180, 1.275, 1.370, 1.474, 1.578, 1.683, 1.787]
    _LOW_PLUNGE  = [1.490, 1.610, 1.730, 1.910, 2.030, 2.170, 2.360, 2.550, 2.740, 2.950, 3.160, 3.360, 3.570]
    _HIGH_PLUNGE = [1.860, 2.010, 2.170, 2.380, 2.530, 2.710, 2.950, 3.180, 3.420, 3.680, 3.940, 4.200, 4.460]

    # ── 원소 스킬 현상 계산식·자유로운 해석 (% ATK, L1~L11) ──────────────────────
    # 레벨을 올리는 명함이 없다. 얼음 캐릭터라 스커크 「무예 전수」로 +1까지만 올라 L11이 상한
    # 이다(L1~L10 + 파티발 1). 프리즘 탄환 2발, 섬광 상태에서는 **두 번째 탄환만** 전환된다.
    _SKILL_PRISM_SHOT         = [0.324, 0.348, 0.373, 0.405, 0.429, 0.454, 0.486, 0.518, 0.551, 0.583, 0.616]
    _SKILL_PRISM_SHOT_CONDUCT = [0.216, 0.232, 0.248, 0.270, 0.286, 0.302, 0.324, 0.346, 0.367, 0.389, 0.410]
    _SKILL_PRISM_SHOT_SWIRL   = [0.324, 0.348, 0.373, 0.405, 0.429, 0.454, 0.486, 0.518, 0.551, 0.583, 0.616]
    _SKILL_PRISM_SHOT_HITS    = 2

    # ── 원소 폭발 현상 계산식·Q.E.D (% ATK, L1~L13, C5 적용 시 최대 L13) — CD 15초, 에너지 60
    _BURST_BOMBARDMENT      = [0.882, 0.948, 1.014, 1.103, 1.169, 1.235, 1.323, 1.411, 1.500, 1.588, 1.676, 1.764, 1.875]
    _BURST_BOMBARDMENT_HITS = 3
    _BURST_SUBZERO_RAY         = [3.308, 3.556, 3.804, 4.135, 4.383, 4.631, 4.962, 5.293, 5.624, 5.954, 6.285, 6.616, 7.029]
    _BURST_SUBZERO_RAY_CONDUCT = [2.205, 2.371, 2.536, 2.757, 2.922, 3.087, 3.308, 3.529, 3.749, 3.970, 4.190, 4.411, 4.686]
    _BURST_SUBZERO_RAY_SWIRL   = [3.308, 3.556, 3.804, 4.135, 4.383, 4.631, 4.962, 5.293, 5.624, 5.954, 6.285, 6.616, 7.029]

    # ── 고정 계수 / 스케일 상수 ────────────────────────────────────────────────
    # A1 : 두 번째 프리즘탄이 「기존의 400%」 (연산량 50pt 초과 상태로 E를 켰을 때)
    _A1_PRISM_SHOT_MULT = 4.00
    # A1 : 부성 온도 광선이 「기존의 100% + 제거된 스택 수 × 10%」
    _A1_TACTIC_DMG_PER_STACK = 0.10
    _A1_TACTIC_MAX_STACKS    = 10
    # A4 : 공격력 100pt당 원소 마스터리 +8, 최대 +160 (공격력 2000에서 상한)
    _A4_EM_PER_100_ATK = 8.0
    _A4_EM_CAP         = 160.0
    # Stellar : 공격력 100pt당 별 초전도·별 확산 '기본 피해' +0.7%, 최대 +14%
    # (공격력 2000에서 상한). 원문이 두 반응을 나란히 묶어 말하므로 값도 하나다.
    _STELLAR_BASE_DMG_PER_100_ATK = 0.007
    _STELLAR_BASE_DMG_CAP         = 0.14
    # 그 증가분이 들어갈 자리 — 반응별로 필드가 갈려 있어(profile.SkillHit) 둘 다 적는다.
    _STELLAR_BASE_DMG_FIELDS = (
        "stellar_conduct_base_dmg_bonus",
        "stellar_swirl_base_dmg_bonus",
    )

    # C1 : 파티 전원의 **별빛 반응**(별 초전도·별 확산) 피해 +30%
    _C1_STELLAR_DMG    = 0.30
    _STELLAR_BONUS_FIELDS = ("stellar_conduct_bonus", "stellar_swirl_bonus")
    # C2 : 냉각 광선 치명타 피해 +40%, 발사마다 추가 +20% (최대 3스택)
    _C2_COOLANT_CRIT_DMG           = 0.40
    _C2_COOLANT_CRIT_DMG_PER_STACK = 0.20
    _C2_MAX_STACKS                 = 3
    # C4 : 별빛 반응 피해 명중 시 협동 공격 1회 (% ATK) — 「상응하는 별빛 반응으로 간주」
    _C4_COOP_DMG = 1.25
    # C6 : 집중 냉각 광선의 추가 피해 (% ATK). 전환되면 계수가 **섬광 상태마다 다르다** —
    # 원문이 「섬광 별 초전도: 80%, 섬광 별 확산: 120%」로 둘을 따로 적은 유일한 자리다.
    _C6_FOCUSED_RAY_DMG    = 1.00
    _C6_FOCUSED_RAY_STELLAR = {
        ReactionType.STELLAR_CONDUCT: 0.80,
        ReactionType.STELLAR_SWIRL:   1.20,
    }
    _C6_FOCUSED_RAY_HITS   = 4
    # C6 : 산드로네가 주는 모든 별빛 반응 피해 20% '승격' → elevation_multiplier
    _C6_STELLAR_ELEVATION = 0.20
    #endregion

    # ── 섬광 상태 = 별빛 반응 두 계열 ────────────────────────────────────────
    # 「섬광·별빛」으로 전환되는 히트는 그때 활성인 섬광 상태의 반응이 된다(원문: 「상응하는
    # 별빛 반응 피해로 간주」). 어느 쪽이 켜질지는 파티와 로테이션이 정하고 히트 생성
    # (Phase 1)은 파티를 못 보므로, 두 계열 모두를 히트로 세워 두고 화면에서 골라 읽는다
    # — 콜롬비나가 인력 간섭 세 갈래를 다 세워 두는 것과 같은 규약이다.
    _STELLAR_VARIANTS = (ReactionType.STELLAR_CONDUCT, ReactionType.STELLAR_SWIRL)

    # ── 히트 이름 (버프가 특정 히트를 집을 때 쓰는 열쇠) ────────────────────────
    # 전환 히트는 계열마다 하나씩이라 이름도 반응 이름으로 갈린다. 문자열을 두 군데 손으로
    # 적으면 한쪽만 고쳐져 버프가 조용히 아무 히트에도 안 붙으므로 조립을 한 곳에 둔다.
    _HIT_COOLANT = "냉각 광선"
    _HIT_PRISM   = "프리즘탄"
    _HIT_SUBZERO = "부성 온도 광선"

    @staticmethod
    def _stellar_hit_name(base: str, reaction: ReactionType) -> str:
        return f"{base} {reaction.value} 피해"

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    # C3는 **일반 공격**을, C5는 원소폭발을 올린다. 원소전투 스킬을 올리는 명함은 없다.
    NA_LEVEL_UP_CONSTELLATION    = 3
    BURST_LEVEL_UP_CONSTELLATION = 5
    NA_TABLES = (_NA_HIT1, _NA_HIT2, _NA_HIT3, _CA_STRAFE, _CA_OVERHEAT_SHOT, _CA_COOLANT,
        _CA_COOLANT_CONDUCT, _CA_COOLANT_SWIRL, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_PRISM_SHOT, _SKILL_PRISM_SHOT_CONDUCT, _SKILL_PRISM_SHOT_SWIRL,)
    BURST_TABLES = (_BURST_BOMBARDMENT, _BURST_SUBZERO_RAY, _BURST_SUBZERO_RAY_CONDUCT, _BURST_SUBZERO_RAY_SWIRL,)

    rarity         = 5
    ascension_stat = StatType.CRIT_RATE

    @property
    def element(self)  -> Element: return Element.CRYO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        c = self.constellation

        sk = self._skill_index()
        bl = self._burst_index()
        nl = self._na_index()

        hits: list[SkillHit] = []

        # 양손검 3타 — 원소가 붙지 않아 물리로 계산된다.
        for i, row in enumerate((self._NA_HIT1, self._NA_HIT2, self._NA_HIT3)):
            hits.append(SkillHit(f"{i+1}단 공격 피해", SkillType.NORMAL_ATK, row[nl],
                                 ScalingStat.ATK))

        # 파지오(강공격) — 난사와 냉각 광선. 전환된 냉각 광선은 계열마다 한 벌씩 세운다
        # (_STELLAR_VARIANTS 주석). 파티가 정하는 값이지만 히트 생성(Phase 1)은 파티를 못 본다.
        hits.append(SkillHit("난사 피해", SkillType.CHARGED_ATK, self._CA_STRAFE[nl],
                             ScalingStat.ATK, Element.CRYO))
        hits.append(SkillHit("냉각 광선 피해", SkillType.CHARGED_ATK, self._CA_COOLANT[nl],
                             ScalingStat.ATK, Element.CRYO))
        hits += self._stellar_variants(self._HIT_COOLANT, SkillType.CHARGED_ATK,
                                       conduct=self._CA_COOLANT_CONDUCT[nl], swirl=self._CA_COOLANT_SWIRL[nl])
        # 연산 과열 모드의 사격 — 이 모드에서는 냉각 광선이 나가지 않으므로 위의 냉각 광선
        # 계열과 **택일**이다. 어느 모드로 얼마나 굴렸는지는 로테이션 몫이라 두 히트를 다
        # 세워 두고, 화면을 읽는 쪽이 각자의 횟수를 곱한다(모드 전환은 엔진이 모른다).
        hits.append(SkillHit("연산 과열 사격 피해", SkillType.CHARGED_ATK,
                             self._CA_OVERHEAT_SHOT[nl], ScalingStat.ATK, Element.CRYO))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK))

        # E 프리즘탄 2발. 섬광 상태에서는 **두 번째 탄환만** 전환된다 — 1타는 그대로다.
        for i in range(self._SKILL_PRISM_SHOT_HITS):
            hits.append(SkillHit(f"프리즘탄 피해 {i+1}타", SkillType.SKILL,
                                 self._SKILL_PRISM_SHOT[sk], ScalingStat.ATK, Element.CRYO))
        hits += self._stellar_variants(self._HIT_PRISM, SkillType.SKILL,
                                       conduct=self._SKILL_PRISM_SHOT_CONDUCT[sk], swirl=self._SKILL_PRISM_SHOT_SWIRL[sk])

        for i in range(self._BURST_BOMBARDMENT_HITS):
            hits.append(SkillHit(f"광역 폭격 피해 {i+1}타", SkillType.BURST,
                                 self._BURST_BOMBARDMENT[bl], ScalingStat.ATK, Element.CRYO))
        hits.append(SkillHit("부성 온도 광선 피해", SkillType.BURST, self._BURST_SUBZERO_RAY[bl],
                             ScalingStat.ATK, Element.CRYO))
        hits += self._stellar_variants(self._HIT_SUBZERO, SkillType.BURST,
                                       conduct=self._BURST_SUBZERO_RAY_CONDUCT[bl], swirl=self._BURST_SUBZERO_RAY_SWIRL[bl])

        # ── 명함 추가 히트 ───────────────────────────────────────────────────
        # 조건부 히트도 반드시 여기서 만든다 — 뒤 단계에서 만들면 기초 스탯을 채우는
        # 루프가 이미 끝난 뒤라 공격력이 0으로 남는다(이네파 주석과 같은 이유).
        if c >= 4:
            # 「상응하는 별빛 반응으로 주는 피해로 간주」 — 스킬 종류는 원문에 없다.
            # 별빛 직접 피해는 스킬 종류별 피해 보너스를 읽지 않으므로(_calc_lunar_direct)
            # 어느 쪽을 골라도 숫자에는 영향이 없다. 소환원(프리즘 공명포)을 따라 SKILL로 둔다.
            hits += self._stellar_variants("C4 프리즘 공명포 협동 공격", SkillType.SKILL,
                                           conduct=self._C4_COOP_DMG, swirl=self._C4_COOP_DMG)

        if c >= 6:
            # 집중 냉각 광선의 **추가** 피해 — 냉각 광선 히트와 별개의 피해 인스턴스다.
            # 전환 전 100%(얼음), 전환 후는 계열마다 계수가 다르다(초전도 80% / 확산 120%).
            for i in range(self._C6_FOCUSED_RAY_HITS):
                hits.append(SkillHit(
                    f"C6 집중 냉각 광선 추가 피해 {i+1}단", SkillType.CHARGED_ATK,
                    self._C6_FOCUSED_RAY_DMG, ScalingStat.ATK, Element.CRYO,
                ))
            for reaction in self._STELLAR_VARIANTS:
                for i in range(self._C6_FOCUSED_RAY_HITS):
                    hits.append(SkillHit(
                        f"C6 집중 냉각 광선 {reaction.value} 추가 피해 {i+1}단",
                        SkillType.CHARGED_ATK, self._C6_FOCUSED_RAY_STELLAR[reaction],
                        ScalingStat.ATK, Element.CRYO,
                        reaction_type=reaction, dmg_type=DmgType.STELLAR_DIRECT,
                    ))

        return {h.name: h for h in hits}

    def _stellar_variants(self, base: str, skill_type: SkillType, *, conduct: float, swirl: float) -> list[SkillHit]:
        """「섬광·별빛」으로 전환되는 히트 하나를 별빛 반응 계열마다 한 벌씩 만든다.

        전환 전 히트와 달리 이쪽은 반응 피해 계열이라 방어력 배율도 %피해 보너스도 타지
        않는다(damage._calc_lunar_direct). 계수는 계열마다 따로 받는다 — 숫자가 같은 자리도
        호출부가 두 열을 각각 짚게 해서, 한쪽만 바뀌는 날 조용히 어긋나지 않게 한다.
        """
        coeff = {ReactionType.STELLAR_CONDUCT: conduct, ReactionType.STELLAR_SWIRL: swirl}
        return [
            SkillHit(self._stellar_hit_name(base, reaction), skill_type, coeff[reaction],
                     ScalingStat.ATK, Element.CRYO,
                     reaction_type=reaction, dmg_type=DmgType.STELLAR_DIRECT)
            for reaction in self._STELLAR_VARIANTS
        ]

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        # 자기 전용 효과 중 A1·C2는 섬광 상태를 조건으로 하는데, 그 판정은 파티를 봐야 한다
        # (_available_shimmers). apply_self_buffs는 파티를 못 보므로 질문과 적용을 Phase 4/4.5로
        # 옮겼다 — 「유저 입력이 필요 없는 판정은 파티가 보이는 훅으로」의 연장이다. A4는 조건
        # 없이 상시지만 최종 공격력을 읽는 방식 B라 Phase 5다. 받는 쪽은 어느 쪽이든 자기 히트뿐.
        pass

    # ── 파티 버프 4: 유저 입력 수집 ────────────────────────────────────────
    # 산드로네는 코어 스탯(ATK/DEF/HP)에 기여하지 않는다 — 파티 버프가 전부 자신의 최종
    # 공격력을 읽는 방식 B라 Phase 5에서 처리한다. 여기서는 입력만 한 번 모은다.
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # 섬광 상태 — 성립 가능한 계열을 파티에서 유도하고, 그중 어느 쪽에 들어가 있는지만
        # 묻는다. 성립하는 계열이 없으면 질문 자체가 뜨지 않는다(party._ask_stellar_state와
        # 같은 규약). 두 계열이 다 성립하면 선택지가 셋이 된다 — 동시에 켜지지는 않는다.
        available = self._available_shimmers(all_hits)
        self._shimmer = None
        if available:
            options = ["없음"] + [f"섬광·{r.value}" for r in available]
            picked = ask_choice("[산드로네] 「섬광·별빛」 상태", options)
            self._shimmer = available[picked - 1] if picked else None

        # A1 「기존의 400%」 — 섬광·별빛이면 어느 계열이든 걸린다.
        # 연산량은 로테이션이 정하는 양이라 엔진이 유도할 수 없다(연산량 모델이 없다).
        self._a1_overload = bool(self._shimmer) and ask_bool(
            "[산드로네 A1] 원소전투 스킬 발동 시 파지오 연산량 50pt 초과 여부"
        )
        # 개선 전술 스택 소모는 **섬광·별 초전도 상태에서 Q를 쏠 때**로 적혀 있다.
        self._a1_stacks = ask_int(
            "[산드로네 A1] 원소폭발 발동 시 제거된 「개선 전술」 스택 수",
            min_val=0, max_val=self._A1_TACTIC_MAX_STACKS,
        ) if self._shimmer is ReactionType.STELLAR_CONDUCT else 0

        # C2 — 「이번 연산 모드에서 발사한 냉각 광선 수」가 곧 스택 수다.
        self._c2_stacks = ask_int(
            "[산드로네 C2] 냉각 광선 치명타 피해 중첩 스택 수",
            min_val=0, max_val=self._C2_MAX_STACKS,
        ) if (self._shimmer and c >= 2) else 0

    def _available_shimmers(self, members) -> list[ReactionType]:
        """이 파티에서 진입할 수 있는 섬광 상태 — 곧 성립하는 별빛 반응 그대로다.

        Stellar 원문은 「극지의 별 영역 내에 있을 때 / 파티원이 별 확산 반응을 발동한 뒤 8초
        동안 각각 섬광·별 초전도 / 섬광·별 확산에 진입한다」이다. 두 진입 조건이 곧 두 반응이
        일어났다는 뜻이므로, 조건을 여기 새로 적지 않고 core.reaction의 성립 판정을 그대로
        읽는다 — 전환 규칙(전환자 + 필요한 두 원소)이 바뀌어도 한 곳만 고치면 따라온다.

        성립한다고 곧바로 진입은 아니다. 반응이 실제로 일어나야 영역·상태가 생기는데 엔진에는
        로테이션 모델이 없으므로, 성립할 때만 유저에게 어느 상태인지 묻는다.
        """
        return [reaction for reaction, _element, _candidates in stellar_conditions(members)]

    # ── 파티 버프 4.5: 스탯을 읽지 않는 크로스 버프 ─────────────────────────
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation
        hits = all_hits[self]

        # C1: 파티 내 모든 캐릭터가 주는 **별빛 반응** 피해 +30% — 두 계열 모두다.
        if c >= 1:
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    for field in self._STELLAR_BONUS_FIELDS:
                        hit.add(field, self._C1_STELLAR_DMG, self, note="C1")

        # C6 승격: 「산드로네가 주는 모든 별빛 반응 피해」 — 자기 히트 전부에 건다.
        # 전 히트에 거는 것이 맞다. elevation_multiplier는 달·별 계열 피해에서만 읽히므로
        # (damage._calc_lunar_*) 평타 같은 히트에 붙어도 숫자에 들어가지 않고, 반대로 파티
        # 별 확산 **반응 피해**는 캐리어 히트(그 캐릭터의 첫 히트)에서 이 필드를 읽는다 —
        # 산드로네는 얼음이라 별 확산 참여자 후보이고, 그 몫도 「그가 주는 별빛 반응 피해」다.
        # 그가 참여할 수 있는 달반응은 없다(달감전은 물·번개, 달결정은 바위·물).
        if c >= 6:
            for hit in hits.values():
                hit.add("elevation_multiplier", self._C6_STELLAR_ELEVATION, self, note="C6 승격")

        # C2: 섬광 상태의 냉각 광선(= 그 계열로 전환된 쪽)의 치명타 피해.
        # 기본 40%는 스택과 무관하게 붙고, 스택은 그 위에 20%씩 얹힌다.
        if self._shimmer and c >= 2:
            crit_dmg = (self._C2_COOLANT_CRIT_DMG
                        + self._C2_COOLANT_CRIT_DMG_PER_STACK * self._c2_stacks)
            self._active(hits, self._HIT_COOLANT).add("crit_dmg", crit_dmg, self,
                                                      note="C2 냉각 광선")

        # A1: 두 번째 프리즘탄이 기존의 400%.
        if self._a1_overload:
            self._amplify_coeff(self._active(hits, self._HIT_PRISM),
                                self._A1_PRISM_SHOT_MULT, "A1 두 번째 프리즘탄")

        # A1: 부성 온도 광선이 기존의 100% + 제거된 스택 수 × 10%.
        # 스택 소모 자체가 섬광·별 초전도 조건이라 _a1_stacks가 그 상태에서만 0이 아니다.
        if self._a1_stacks:
            mult = 1.0 + self._A1_TACTIC_DMG_PER_STACK * self._a1_stacks
            self._amplify_coeff(self._active(hits, self._HIT_SUBZERO), mult, "A1 개선 전술")

    def _active(self, hits: dict[str, SkillHit], base: str) -> SkillHit:
        """지금 켜진 섬광 상태로 전환된 히트. 섬광이 꺼져 있으면 부르지 않는다.

        버프마다 히트 이름을 손으로 짓지 않고 여기 한 곳에서 고른다 — 계열이 둘이라
        「별 초전도 쪽에만 걸리는」 사고가 나기 쉬운 자리다."""
        return hits[self._stellar_hit_name(base, self._shimmer)]

    def _amplify_coeff(self, hit: SkillHit, mult: float, note: str) -> None:
        """계수에 배율을 건다 — **coeff_amp가 아니라 coeff다.**

        별 반응 직접 피해는 damage._calc_lunar_direct를 타는데 그 공식에 coeff_amp 자리가
        없다(계수 × 스탯만 쓴다). coeff_amp에 넣으면 숫자도 안 바뀌고 설명 화면에도 안 뜨는
        조용한 무효가 되므로 계수 자체를 키운다. add로 넣어 원장에 출처가 남는다.
        """
        hit.add("coeff", hit.coeff * (mult - 1.0), self, note=note)

    # ── 파티 버프 5: 최종 스탯을 읽어 스케일하는 버프 (방식 B) ────────────────
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # 산드로네의 최신 공격력 — 값이 아니라 **읽는 함수**로 넘긴다(지연 기여).
        # 같은 단계에서 다른 캐릭터가 그의 공격력을 올릴 수 있으므로 지금 확정하면
        # 파티 멤버 순서가 결과를 바꾼다. 항상 같은 히트(첫 히트)를 읽어 값이 흔들리지 않는다.
        source_hit = next(iter(all_hits[self].values()))
        atk_per_100 = lambda: source_hit.convertible_atk() / 100.0

        # Stellar 별빛 축복: 별 초전도·별 확산 '기본 피해' 증가 — 파티 전원에게 적용된다.
        # 이네파 Moonsign과 같은 모양이고, 반응 계열만 별 쪽으로 갈린다. 콜롬비나가 달반응
        # 세 필드에 같은 값을 넣는 것과 마찬가지로 여기도 두 필드에 같은 값을 넣는다.
        base = lambda: min(atk_per_100() * self._STELLAR_BASE_DMG_PER_100_ATK,
                           self._STELLAR_BASE_DMG_CAP)
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                for field in self._STELLAR_BASE_DMG_FIELDS:
                    hit.add(field, base, self, note="Stellar 별빛 축복")

        # A4 숙녀의 에티켓: 자기 공격력으로 자기 원소 마스터리를 올린다.
        # **상시**다 — 원문에 섬광·별빛 조건이 없다(유저 확인). 파티도 로테이션도 안 본다.
        # 공격력에서 파생된 EM이므로 em_from_flat이 아니라 em_from_pct_share에 넣는다 —
        # EM을 **다시 %로 변환**하는 버프(카즈하류)가 이 지분을 재료로 쓰지 못하게 막는다.
        # 합계(elemental_mastery)는 두 조각의 합이라 본인 반응에는 그대로 들어간다.
        em = lambda: min(atk_per_100() * self._A4_EM_PER_100_ATK, self._A4_EM_CAP)
        for hit in all_hits[self].values():
            hit.add("em_from_pct_share", em, self, note="A4 숙녀의 에티켓")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 파지오 연산량(0~100)·연산 과열 진입/해제 — 피해 계수가 아니라 자원/모드 전환 규칙이다.
    #   엔진에 로테이션 모델이 없어 상태를 굴릴 수 없으므로, 그 상태가 실제로 가르는 값
    #   (A1 400% 여부, 개선 전술 스택 수)만 유저에게 묻는다. 과열 사격과 냉각 광선은 서로
    #   택일이지만 히트는 둘 다 세워 두고, 횟수는 화면을 읽는 쪽이 곱한다.
    # · 티타임용 특수작전 장치의 부유/스태미나, C1의 연산량 증가 속도 -50%, C2·C6의 발동
    #   조건인 「세 번째 냉각 광선」 같은 타이밍 규칙 — 피해식에 들어가지 않는다.
    # · C4의 「4초마다 최대 1회」와 C6의 「최대 4단」 — 발동 횟수 제한은 로테이션 몫이라
    #   히트를 1회/4단으로 세워 두고 실제 횟수는 화면을 읽는 쪽이 곱한다.
