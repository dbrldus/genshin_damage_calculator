from gidc.core.character import Character, clamp_talent_index
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import CharacterTrait, Element
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_choice, ask_int


class Mavuika(Character):
    """마비카 (Mavuika) | 불 | 양손검 | 5성 | 어센션 스탯: 치명타 피해

    일반 공격 : 검으로 최대 4번 공격한다.
    강공격 : 일정 스태미나를 소모해 전방을 향해 1회의 더 강한 햇볕 베기를 가한다.
    낙하 공격 : 공중에서 땅을 내려찍어 경로상의 적을 공격하고 착지 시 범위 피해를 준다.

    E : 해방의 순간
    「투쟁」의 권능으로 인간신이 계승한 「불꽃 무장」을 소환해, 밤혼 성질의 불 원소 피해를 준다.
    발동 후, 마비카는 밤혼을 최대치까지 회복하고, 밤혼 가호 상태에 진입한다.

    불꽃 무장
    짧은 터치와 홀드에 따라 다른 형태로 불꽃 무장을 개방한다.

    짧은 터치
    「신의 이름 해방」: 불꽃 무장은 불볕 고리 형태로 나타난다. 불볕 고리는 현재 필드 위에 있는 캐릭터를 따라다니며, 간헐적으로 주변에 있는 적을 공격해 밤혼 성질의 불 원소 피해를 준다.

    홀드
    「고대의 이름 해방」: 불꽃 무장은 바이크 형태로 나타난다. 해당 상태에서 마비카는 바이크를 조종해 고속 이동하거나, 바이크의 예비 추진기를 활성화해 짧은 시간 동안 다양한 지형을 통과하거나 공중에서 활강할 수 있다.
    동시에 마비카의 일반 공격, 강공격, 낙하 공격이 다른 원소 부여 효과로 대체될 수 없는 밤혼 성질의 불 원소 피해로 전환된다.
    대시 시, 경로 상의 적에게 밤혼 성질의 불 원소 피해를 준다.

    밤혼 가호 상태에서 원소전투 스킬을 짧게 누르면 불꽃 무장 형태를 전환할 수 있다, 불꽃 무장은 마비카의 밤혼 가호 지속 시간이 종료되면 사라진다.

    밤혼 가호 · 마비카
    불꽃 무장의 형태에 따라 지속적으로 밤혼을 소모한다. 밤혼이 모두 소모되면 마비카의 밤혼 지속 시간이 종료된다.`

    Q : 불타는 하늘
    마비카의 원소폭발은 원소 에너지가 아닌 「전의」에서 나온다.

    전의
    마비카의 전의가 50% 이상 시, 마비카가 모든 전의를 소모해 원소폭발을 발동할 수 있다.
    마비카는 아래의 방식으로 전의를 획득할 수 있다:
    · 전투 상태 시, 주변에 있는 파티 내 캐릭터가 소모한 밤혼이 마비카의 전의로 전환된다.
    · 주변에 있는 파티 내 캐릭터의 일반 공격이 적에게 명중 시, 마비카는 전의 1.5pt를 획득한다, 해당 효과는 0.1초마다 최대 1회 발동된다.

    발동 후 마비카는 밤혼을 10pt 획득하고, 밤혼 가호 상태에 진입한 다음, 바이크를 타고 날아올라
    지면의 적에게 강력한 석양 베기를 1회 발동해 밤혼 성질의 불 원소 범위 피해를 주고, 「삶과 죽음의 용광로」 상태에 진입한다.

    삶과 죽음의 용광로
    지속 시간 동안, 마비카의 행동에도 밤혼이 소모되지 않으며, 마비카의 경직 저항력이 증가한다.
    동시에 발동 순간의 전의에 따라 석양 베기, 바이크 모드에서의 일반 공격과 강공격으로 주는 피해가 증가한다.
    삶과 죽음의 용광로 상태는 마비카가 퇴장하면 사라진다.

    A1 : 타오르는 꽃의 선물
    파티 내 주변에 있는 캐릭터가 「밤혼 발산」 발동 시, 마비카의 공격력이 30% 증가한다. 지속 시간: 10초

    A4 : 「키온고지」
    원소폭발 불타는 하늘 발동 후, 발동 당시의 전의에 따라 1pt당 현재 필드 위 캐릭터가 주는 피해가 0.2% 증가한다.
    해당 방식으로 현재 필드 위 캐릭터가 주는 피해가 최대 40% 증가한다, 지속 시간: 20초. 지속 시간 동안 해당 효과는 0%가 될 때까지 점차 감소한다

    C1 : 밤 주인의 계시
    마비카의 밤혼 최대치가 120pt로 증가하고, 전의 획득 효율이 25% 증가한다.
    또한, 전의 획득 후 마비카의 공격력이 40% 증가한다, 지속 시간: 8초

    C2 : 잿더미의 대가
    밤혼 가호 상태에서 마비카의 기초 공격력이 200pt 증가하고, 불꽃 무장의 형태에 따라 상응하는 효과를 획득한다:
    ·불볕 고리: 주변 적의 방어력이 20% 감소한다.
    ·바이크: 마비카의 일반 공격, 강공격, 원소폭발 불타는 하늘의 석양 베기로 주는 피해가 마비카 공격력의 60%/90%/120%만큼 증가한다

    C3 : 타오르는 태양
    불타는 하늘의 스킬 레벨+3

    C4 : 「지도자」의 각오
    고유 특성 「키온고지」 효과 강화:
    원소폭발 불타는 하늘 발동 후의 피해 증가 효과가 시간에 따라 감소하지 않는다. 또한 추가로 피해 보너스를 10% 획득한다.
    고유 특성 「키온고지」를 해금해야 한다

    C5 : 진정한 의미
    해방의 순간의 스킬 레벨+3

    C6 : 「인간의 이름」 해방
    원소전투 스킬 해방의 순간의 불꽃 무장의 완전 강화:
    ·불볕 고리: 불볕 고리의 공격이 적 명중 시, 바이크 1대가 명중한 적과 부딪혀 공격력의 200%에 해당하는 밤혼 성질의 불 원소 범위 피해를 준다.
    마비카가 바이크 조종 시, 마비카를 따라다니는 「불볕 고리·빛」을 소환해 주변의 적의 방어력을 20% 감소시킨다.
    또한 주변의 적에게 3초마다 공격력의 500%에 해당하는 밤혼 성질의 불 원소 범위 피해를 주고,마비카의 각종 지형 돌파 능력이 향상된다.

    또한 마비카가 비전투 상태에서 바이크 조종 시, 마비카의 밤혼이 5pt로 떨어지면 추가로 밤혼을 80pt 획득한다. 해당 효과는 15초마다 최대 1회 발동된다
    """
    name = "마비카"
    weapon_type = WeaponType.CLAYMORE


    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # 일반 공격 「불로 엮은 삶」 (% ATK, L1~L11) — 양손검이라 물리 피해.
    # 2단은 2타, 3단은 3타로 나뉘어 들어간다(표기: 36.5%*2 / 33.2%*3 @L1).
    _NA_HIT1 = [0.8000, 0.8650, 0.9310, 1.0240, 1.0890, 1.1630, 1.2660, 1.3680, 1.4700, 1.5820, 1.6940]
    _NA_HIT2 = [0.3650, 0.3940, 0.4240, 0.4670, 0.4960, 0.5300, 0.5770, 0.6240, 0.6700, 0.7210, 0.7720]
    _NA_HIT3 = [0.3320, 0.3590, 0.3860, 0.4250, 0.4520, 0.4830, 0.5250, 0.5680, 0.6100, 0.6570, 0.7030]
    _NA_HIT4 = [1.1620, 1.2570, 1.3510, 1.4860, 1.5810, 1.6890, 1.8370, 1.9860, 2.1350, 2.2970, 2.4590]
    # 2단/3단이 한 번의 입력으로 내는 타수 — 로테이션 합산용(단일 히트 계수에는 넣지 않는다).
    _NA_HIT2_COUNT = 2
    _NA_HIT3_COUNT = 3

    # 강공격 종결 피해 (% ATK, L1~L11) — 스태미나 소모 50, 「햇볕 베기」 1회.
    # 양손검이지만 순환 피해가 없고 종결 1타뿐이다.
    _CA = [1.9400, 2.1000, 2.2500, 2.4800, 2.6400, 2.8200, 3.0700, 3.3100, 3.5600, 3.8300, 4.1000]

    # 낙하 공격 — 양손검 전용 표
    _PLUNGE      = [0.7460, 0.8070, 0.8670, 0.9540, 1.0150, 1.0840, 1.1800, 1.2750, 1.3700, 1.4740, 1.5780]
    _LOW_PLUNGE  = [1.4900, 1.6100, 1.7300, 1.9100, 2.0300, 2.1700, 2.3600, 2.5500, 2.7400, 2.9500, 3.1600]
    _HIGH_PLUNGE = [1.8600, 2.0100, 2.1700, 2.3800, 2.5300, 2.7100, 2.9500, 3.1800, 3.4200, 3.6800, 3.9400]

    # ── 원소 스킬 「해방의 순간」 (% ATK, L1~L13, C5 적용 시 최대 L13) ──────────
    # 바이크 모드의 일반/강/낙하 공격과 대시도 **원소 스킬 특성 표**에 실려 있어
    # 스킬 레벨로 스케일한다(피해 종류만 일반/강/낙하로 분류된다).
    _SKILL_ACTIVATION = [   # 가동 피해 — E 발동 시 1회
        0.7440, 0.8000, 0.8560, 0.9300, 0.9860,
        1.0420, 1.1160, 1.1900, 1.2650, 1.3390,
        1.4140, 1.4880, 1.5810,
    ]
    _FLAMESTRIDER_RING = [  # 불볕 고리 피해 — 「신의 이름 해방」(짧은 터치) 형태의 지속 타격
        1.2800, 1.3760, 1.4720, 1.6000, 1.6960,
        1.7920, 1.9200, 2.0480, 2.1760, 2.3040,
        2.4320, 2.5600, 2.7200,
    ]
    _BIKE_NA = [            # 바이크 일반 공격 1~5단 (밤혼 성질 불 원소로 전환)
        [0.5730, 0.6190, 0.6660, 0.7320, 0.7790, 0.8320, 0.9060, 0.9790, 1.0520, 1.1320, 1.2120, 1.2920, 1.3720],
        [0.5910, 0.6390, 0.6880, 0.7560, 0.8040, 0.8590, 0.9350, 1.0110, 1.0860, 1.1690, 1.2510, 1.3340, 1.4160],
        [0.7000, 0.7570, 0.8140, 0.8950, 0.9520, 1.0170, 1.1070, 1.1960, 1.2860, 1.3830, 1.4810, 1.5790, 1.6760],
        [0.6970, 0.7540, 0.8110, 0.8920, 0.9480, 1.0130, 1.1020, 1.1910, 1.2810, 1.3780, 1.4750, 1.5720, 1.6700],
        [0.9100, 0.9840, 1.0580, 1.1640, 1.2380, 1.3230, 1.4390, 1.5560, 1.6720, 1.7990, 1.9260, 2.0530, 2.1800],
    ]
    _BIKE_DASH = [          # 바이크 대시 피해 — 경로상의 적을 친다
        0.8080, 0.8740, 0.9400, 1.0340, 1.1000,
        1.1750, 1.2780, 1.3820, 1.4850, 1.5980,
        1.7110, 1.8240, 1.9360,
    ]
    _BIKE_CA_CYCLIC = [     # 바이크 강공격 순환 피해
        0.9890, 1.0695, 1.1500, 1.2650, 1.3455,
        1.4375, 1.5640, 1.6905, 1.8170, 1.9550,
        2.0930, 2.2310, 2.3690,
    ]
    _BIKE_CA_FINAL = [      # 바이크 강공격 종결 피해
        1.3760, 1.4880, 1.6000, 1.7600, 1.8720,
        2.0000, 2.1760, 2.3520, 2.5280, 2.7200,
        2.9120, 3.1040, 3.2960,
    ]
    _BIKE_PLUNGE = [        # 바이크 낙하 공격 피해
        1.6000, 1.7300, 1.8600, 2.0460, 2.1760,
        2.3250, 2.5300, 2.7340, 2.9390, 3.1620,
        3.3850, 3.6080, 3.8320,
    ]

    # ── 원소 폭발 「불타는 하늘」 (L1~L13, C3 적용 시 최대 L13) ─────────────────
    # 원소 에너지가 아니라 「전의」로 발동한다 — 전의 상한 200, CD 18초.
    _BURST_DMG = [          # 석양 베기 피해 (% ATK)
        4.4480, 4.7820, 5.1150, 5.5600, 5.8940,
        6.2270, 6.6720, 7.1170, 7.5620, 8.0060,
        8.4510, 8.8960, 9.4520,
    ]
    # 「삶과 죽음의 용광로」 — 발동 당시의 전의 1pt당 공격력의 %만큼 피해가 증가한다.
    # 계수가 아니라 피해에 직접 더해지는 몫이라 flat_dmg_bonus로 들어간다.
    _BURST_SPIRIT_ATK = [   # 버스트(석양 베기) 피해 보너스
        0.0160, 0.0170, 0.0180, 0.0200, 0.0210,
        0.0220, 0.0240, 0.0260, 0.0270, 0.0290,
        0.0300, 0.0320, 0.0340,
    ]
    _BIKE_NA_SPIRIT_ATK = [ # 바이크 일반 공격 보너스
        0.0026, 0.0028, 0.0030, 0.0033, 0.0035,
        0.0038, 0.0041, 0.0044, 0.0047, 0.0051,
        0.0055, 0.0058, 0.0062,
    ]
    _BIKE_CA_SPIRIT_ATK = [ # 바이크 강공격 보너스
        0.0052, 0.0056, 0.0060, 0.0066, 0.0070,
        0.0075, 0.0082, 0.0088, 0.0095, 0.0102,
        0.0109, 0.0116, 0.0124,
    ]

    # ── 전의 (Q 자원) ─────────────────────────────────────────────────────────
    # 상한 200pt, 50%(=100pt) 이상이어야 원소폭발을 발동할 수 있다.
    # 획득 경로(밤혼 전환 / 파티원 일반 공격 명중 시 1.5pt)는 자원 모델이 없어 묻는다.
    _SPIRIT_MAX     = 200
    _SPIRIT_Q_MIN   = 100
    _BURST_DURATION = 7.0   # 투신 모드(삶과 죽음의 용광로) 지속 시간(초)

    # ── 고유 특성 / 명함 계수 (히트 아님 — 버프 훅에서 사용) ────────────────────
    # A1 : 파티원 「밤혼 발산」 발동 시 마비카 공격력 증가
    _A1_ATK_PCT = 0.30
    # A4 「키온고지」: 전의 1pt당 필드 위 캐릭터 피해 증가 / 상한 (C4는 여기에 10%를 더한다)
    _A4_PER_SPIRIT_DMG = 0.002
    _A4_DMG_CAP        = 0.40
    _C4_EXTRA_DMG      = 0.10
    # C1 : 전의 획득 후 마비카 공격력 증가 (밤혼 최대치 120pt·전의 획득 효율 +25%는 자원)
    _C1_ATK_PCT = 0.40
    # C2 : 밤혼 가호 상태의 기초 공격력 증가 + 형태별 효과
    _C2_BASE_ATK          = 200
    _C2_RING_DEF_REDUCTION = 0.20   # 불볕 고리 — 주변 적 방어력 감소
    _C2_BIKE_NA_ATK        = 0.60   # 바이크 — 일반 공격 피해 += 공격력의 60%
    _C2_BIKE_CA_ATK        = 0.90   # 바이크 — 강공격 피해 += 공격력의 90%
    _C2_BIKE_BURST_ATK     = 1.20   # 바이크 — 석양 베기 피해 += 공격력의 120%
    # C6 : 형태별 추가 히트 계수(% ATK) + 「불볕 고리·빛」의 방어력 감소
    _C6_RING_BIKE_CRASH_DMG   = 2.00   # 불볕 고리 명중 시 바이크 충돌
    _C6_BIKE_RING_LIGHT_DMG   = 5.00   # 바이크 조종 시 「불볕 고리·빛」, 3초마다 1회
    _C6_BIKE_DEF_REDUCTION    = 0.20
    #endregion

    # ── 히트 이름 (버프 훅이 대상 히트를 고르는 단일 출처) ──────────────────────
    _BIKE_NA_NAMES = (
        "바이크 일반 공격 1단 피해", "바이크 일반 공격 2단 피해", "바이크 일반 공격 3단 피해",
        "바이크 일반 공격 4단 피해", "바이크 일반 공격 5단 피해",
    )
    _BIKE_CA_NAMES = ("바이크 강공격 순환 피해", "바이크 강공격 종결 피해")
    _BURST_NAME    = "석양 베기 피해"

    # ── 불꽃 무장 형태 ────────────────────────────────────────────────────────
    # 밤혼 가호에 들어가야 존재하고, 형태에 따라 C2·C6의 효과가 완전히 갈린다.
    # 파티 구성으로 유도할 수 없는 조작 선택이라 유저에게 한 번 묻는다.
    _FORM_RING = 0
    _FORM_BIKE = 1
    _FORM_NONE = 2
    _FORM_OPTIONS = ["불볕 고리 (짧은 터치)", "바이크 (홀드)", "없음 (밤혼 가호 아님)"]

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 5
    BURST_LEVEL_UP_CONSTELLATION = 3
    NA_TABLES = (_NA_HIT1, _NA_HIT2, _NA_HIT3, _NA_HIT4, _CA, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_ACTIVATION, _FLAMESTRIDER_RING, *_BIKE_NA, _BIKE_DASH,
                    _BIKE_CA_CYCLIC, _BIKE_CA_FINAL, _BIKE_PLUNGE,)
    BURST_TABLES = (_BURST_DMG, _BURST_SPIRIT_ATK, _BIKE_NA_SPIRIT_ATK, _BIKE_CA_SPIRIT_ATK,)

    rarity         = 5
    ascension_stat = StatType.CRIT_DMG

    @property
    def element(self)  -> Element: return Element.PYRO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        c = self.constellation

        # C5: 원소 스킬 레벨 +3 (최대 13)
        sk = self._skill_index()
        # C3: 원소 폭발 레벨 +3 (최대 13)
        bl = self._burst_index()
        nl = self._na_index()

        hits: list[SkillHit] = []

        # 맨몸(불꽃 무장 없음) 일반/강/낙하 공격은 양손검 물리 피해다 (element 미지정 → PHYSICAL).
        # 바이크 모드의 같은 공격들은 아래에 밤혼 성질 불 원소 히트로 따로 들어간다.
        for name, coeff in [
            ("1단 공격 피해", self._NA_HIT1[nl]),
            ("2단 공격 피해", self._NA_HIT2[nl]),
            ("3단 공격 피해", self._NA_HIT3[nl]),
            ("4단 공격 피해", self._NA_HIT4[nl]),
        ]:
            hits.append(SkillHit(name, SkillType.NORMAL_ATK, coeff, ScalingStat.ATK))

        hits.append(SkillHit("강공격 종결 피해", SkillType.CHARGED_ATK, self._CA[nl], ScalingStat.ATK))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK))

        # ── 원소 스킬 ────────────────────────────────────────────────────────
        hits.append(SkillHit("가동 피해",     SkillType.SKILL, self._SKILL_ACTIVATION[sk],  ScalingStat.ATK, Element.PYRO))
        hits.append(SkillHit("불볕 고리 피해", SkillType.SKILL, self._FLAMESTRIDER_RING[sk], ScalingStat.ATK, Element.PYRO))

        # 바이크 모드 — 계수는 원소 스킬 표에서 오지만 피해 종류는 일반/강/낙하 공격이다.
        # 「다른 원소 부여 효과로 대체될 수 없는」 불 원소이므로 element를 못 박아 둔다.
        for name, row in zip(self._BIKE_NA_NAMES, self._BIKE_NA):
            hits.append(SkillHit(name, SkillType.NORMAL_ATK, row[sk], ScalingStat.ATK, Element.PYRO))

        hits.append(SkillHit("바이크 대시 피해", SkillType.SKILL, self._BIKE_DASH[sk], ScalingStat.ATK, Element.PYRO))

        for name, table in zip(self._BIKE_CA_NAMES, (self._BIKE_CA_CYCLIC, self._BIKE_CA_FINAL)):
            hits.append(SkillHit(name, SkillType.CHARGED_ATK, table[sk], ScalingStat.ATK, Element.PYRO))

        hits.append(SkillHit("바이크 낙하 공격 피해", SkillType.PLUNGING, self._BIKE_PLUNGE[sk],
                             ScalingStat.ATK, Element.PYRO))

        # ── 원소 폭발 ────────────────────────────────────────────────────────
        hits.append(SkillHit(self._BURST_NAME, SkillType.BURST, self._BURST_DMG[bl],
                             ScalingStat.ATK, Element.PYRO))

        # ── 명함 추가 히트 ────────────────────────────────────────────────────
        # 조건부 히트도 반드시 build_hits에서 만든다 — apply_self_buffs 이후에 만들면
        # 기초 스탯을 채우는 루프가 이미 끝난 뒤라 공격력이 0으로 남는다.
        # 형태(불볕 고리/바이크)는 Phase 4에서야 정해지므로 C6의 두 히트를 모두 만들어 두고,
        # 실제로 어느 쪽이 나오는지는 형태 선택이 가른다(아래 훅 주석 참고).
        if c >= 6:
            hits.append(SkillHit(
                "C6 바이크 충돌 피해", SkillType.SKILL,
                self._C6_RING_BIKE_CRASH_DMG, ScalingStat.ATK, Element.PYRO,
            ))
            hits.append(SkillHit(
                "C6 불볕 고리·빛 피해", SkillType.SKILL,
                self._C6_BIKE_RING_LIGHT_DMG, ScalingStat.ATK, Element.PYRO,
            ))

        return {h.name: h for h in hits}

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    # 마비카에게만 걸리는 버프는 전부 여기서 묻고 여기서 끝낸다 — 파티를 볼 것이 없다.
    # 불꽃 무장 형태만 예외적으로 파티 대상 효과(C2 불볕 고리·C6)의 재료이기도 해서
    # self에 저장해 두고 뒤 단계가 다시 묻지 않고 재사용한다.
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        c = self.constellation

        # 불꽃 무장의 형태 — 밤혼 가호 여부와 형태를 한 번에 묻는다.
        # 이 답 하나가 C2(기초 공격력·적 방어력·바이크 피해)와 C6(형태별 추가 효과)를
        # 모두 가르므로 가장 먼저 확정한다.
        self._form = ask_choice("[마비카 E] 불꽃 무장 형태", self._FORM_OPTIONS)

        # A1 「타오르는 꽃의 선물」: 파티원의 「밤혼 발산」 발동 → 공격력 +30% (10초).
        # 발동 주체는 파티원이지만 효과를 받는 것은 마비카뿐이라 자기 버프다.
        # 어느 파티원이 언제 밤혼을 발산하는지는 파티 구성만으로 유도할 수 없어 묻는다.
        if ask_bool("[마비카 A1] 파티원 「밤혼 발산」 발동 (공격력 +30%) 여부"):
            for hit in hits.values():
                hit.add("atk_pct", self._A1_ATK_PCT, self, note="A1")

        # C1 「밤 주인의 계시」: 전의 획득 후 공격력 +40% (8초).
        # 밤혼 최대치 120pt·전의 획득 효율 +25%는 자원이라 피해식에 들어갈 항이 없다.
        if c >= 1 and ask_bool("[마비카 C1] 전의 획득 후 공격력 +40% 여부"):
            for hit in hits.values():
                hit.add("atk_pct", self._C1_ATK_PCT, self, note="C1")

        # C2 「잿더미의 대가」 앞부분: 밤혼 가호 상태에서 **기초** 공격력 +200pt.
        # atk_flat이 아니라 atk_base다 — 공격력 %의 곱셈 대상에 들어간다.
        if c >= 2 and self._form != self._FORM_NONE:
            for hit in hits.values():
                hit.add("atk_base", self._C2_BASE_ATK, self, note="C2")

    # ── A4 「키온고지」 피해 보너스의 상한 ─────────────────────────────────────
    # 발동 당시의 전의 1pt당 0.2%, 최대 40%. 감소가 시작되기 전의 최댓값이라
    # C4(감소 없음)의 값이자 C4가 없을 때 유저가 답할 수 있는 상한이기도 하다.
    # 두 소비처가 같은 함수를 읽게 해서 한쪽만 고쳐지는 일을 막는다.
    def _a4_peak_bonus(self) -> float:
        return min(self._spirit * self._A4_PER_SPIRIT_DMG, self._A4_DMG_CAP)

    # ── 파티 버프 4: 유저 입력 수집 ───────────────────────────────────────────
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # 마비카는 파티원의 코어 스탯(atk/def/hp/em)에 기여하지 않는다 — 여기서는
        # Phase 4.5(A4)와 Phase 5(삶과 죽음의 용광로)가 함께 쓸 입력만 한 번 모은다.
        #
        # Q 「불타는 하늘」: 원소 에너지가 아니라 전의로 발동한다. 발동 당시의 전의가
        # A4(필드 위 캐릭터 피해 증가)와 자기 피해 증가의 공통 재료라 여기서 한 번만 묻는다.
        # 50%(=100pt) 미만이면 발동 자체가 불가능하므로 하한을 100으로 둔다.
        self._q_active = ask_bool("[마비카 Q] 불타는 하늘 발동 (삶과 죽음의 용광로) 여부")
        self._spirit   = (
            ask_int("[마비카 Q] 발동 당시의 전의", self._SPIRIT_Q_MIN, self._SPIRIT_MAX)
            if self._q_active else 0
        )

        # ── A4 「키온고지」 대상과 크기 ────────────────────────────────────────
        # 파티 전원이 아니라 「현재 필드 위 캐릭터」 1명에게만 걸린다. 누가 필드에
        # 서는지는 로테이션이 정하는 것이라 파티 구성만으로 유도할 수 없어 묻는다.
        self._a4_target: "Character | None" = None
        self._a4_bonus:  float              = 0.0
        if not self._q_active:
            return

        members = list(all_hits)
        self._a4_target = members[
            ask_choice("[마비카 A4] 「키온고지」를 받을 현재 필드 위 캐릭터",
                       [char.name for char in members])
        ]

        if c >= 4:
            # C4 「지도자」의 각오: 시간에 따른 감소가 사라지므로 값이 상한에 고정된다.
            # 물어볼 것이 없어 전의에서 그대로 유도한다 (전의 200이면 40% + 10% = 50%).
            self._a4_bonus = self._a4_peak_bonus() + self._C4_EXTRA_DMG
        else:
            # C4가 없으면 20초에 걸쳐 0%까지 점차 감소한다 — 이 히트가 그 구간의 어디에서
            # 나오는지는 로테이션이 정하므로 계산기가 고를 수 없다. 상한(전의로 정해지는
            # 발동 직후 값)만 알려 주고 실제로 실린 값을 유저가 답한다.
            self._a4_bonus = ask_int(
                "[마비카 A4] 「키온고지」 피해 보너스 (%)",
                0, round(self._a4_peak_bonus() * 100),
            ) / 100

    # ── 파티 버프 4.5: 스탯을 읽지 않는 크로스 버프 ─────────────────────────
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # A4 「키온고지」: 「현재 필드 위 캐릭터가 주는 피해」가 증가한다 —
        # 파티 전원이 아니라 위에서 고른 그 1명의 히트에만 건다.
        if self._a4_target is not None and self._a4_bonus:
            for hit in all_hits[self._a4_target].values():
                hit.add("all_dmg_bonus", self._a4_bonus, self, note="A4 키온고지")

        # C2 불볕 고리 / C6 「불볕 고리·빛」: 주변 적의 방어력 감소.
        # 적에게 걸리는 효과라 파티 전원의 히트에 넣는다(실로닌 E 내성 감소와 같은 계열).
        # 두 효과는 형태가 서로 배타적이라 실제로 겹치지 않는다.
        if c >= 2 and self._form == self._FORM_RING:
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.add("def_reduction", self._C2_RING_DEF_REDUCTION, self, note="C2 불볕 고리")

        if c >= 6 and self._form == self._FORM_BIKE:
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.add("def_reduction", self._C6_BIKE_DEF_REDUCTION, self, note="C6 불볕 고리·빛")

    # ── 파티 버프 5: 최종 스탯을 읽어 스케일하는 버프 (방식 B) ────────────────
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c    = self.constellation
        hits = all_hits[self]

        # 마비카의 최종 공격력 — 값이 아니라 **읽는 함수**로 넘긴다(지연 기여).
        # 이 공격력에는 다른 캐릭터가 Phase 5에서 주는 몫도 들어오므로, 여기서 미리
        # 확정하면 누가 먼저 실행되느냐가 결과를 바꾼다. 함수로 넘기면 이 필드를 읽는
        # 순간 그때까지의 모든 기여가 확정된 뒤 계산된다.
        # (ATK 코어 풀에 되먹이면 무한 루프이며 정확성 가드가 실패시킨다 → flat_dmg_bonus.)
        source_hit = next(iter(hits.values()))
        atk = lambda: source_hit.current_atk()

        # ── Q 「삶과 죽음의 용광로」 ────────────────────────────────────────────
        # 발동 순간의 전의 1pt당 공격력의 N%만큼 석양 베기 / 바이크 일반 공격 / 바이크
        # 강공격의 피해가 증가한다. 폭발을 쓰면 마비카는 반드시 바이크를 타고 나오므로
        # (「바이크를 타고 날아올라 … 삶과 죽음의 용광로 상태에 진입」) 형태를 따로 보지 않는다.
        if self._q_active:
            bl = self._burst_index()
            spirit = self._spirit
            for name, ratio in (
                (self._BURST_NAME, self._BURST_SPIRIT_ATK[bl]),
                *((n, self._BIKE_NA_SPIRIT_ATK[bl]) for n in self._BIKE_NA_NAMES),
                *((n, self._BIKE_CA_SPIRIT_ATK[bl]) for n in self._BIKE_CA_NAMES),
            ):
                hits[name].add("flat_dmg_bonus",
                               lambda r=ratio: atk() * r * spirit,
                               self, note="Q 삶과 죽음의 용광로")

        # ── C2 바이크 ─────────────────────────────────────────────────────────
        # 「마비카의 일반 공격, 강공격, 석양 베기 피해가 공격력의 60%/90%/120%만큼 증가」.
        # 바이크 형태에서의 효과이므로 여기서 말하는 일반/강공격은 바이크 쪽 히트다.
        if c >= 2 and self._form == self._FORM_BIKE:
            for name, ratio in (
                (self._BURST_NAME, self._C2_BIKE_BURST_ATK),
                *((n, self._C2_BIKE_NA_ATK) for n in self._BIKE_NA_NAMES),
                *((n, self._C2_BIKE_CA_ATK) for n in self._BIKE_CA_NAMES),
            ):
                hits[name].add("flat_dmg_bonus",
                               lambda r=ratio: atk() * r,
                               self, note="C2 바이크")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 밤혼/전의 수지 전반 (E 밤혼 최대 회복, Q 밤혼 10pt 획득, C1 밤혼 최대치 120pt와
    #   전의 획득 효율 +25%, C6 비전투 밤혼 80pt 회복) — 자원 모델이 없어 피해식에 들어갈
    #   항이 없다. 전의는 결과값(보유량)만 유저에게 묻는다.
    # · 「삶과 죽음의 용광로」의 밤혼 무소모·경직 저항, C6의 지형 돌파 — 지속력이지 피해가 아니다.
    # · C6의 두 추가 히트는 형태가 배타적이라 실제 로테이션에서는 한쪽만 나온다 —
    #   히트는 둘 다 만들어 두고 어느 쪽을 합산할지는 사용자가 형태에 맞춰 고른다.
