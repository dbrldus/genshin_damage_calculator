from gidc.core.character import Character, clamp_talent_index
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import CharacterTrait, Element
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_int


class Skirk(Character):
    """스커크 (Skirk) | 얼음 | 한손검 | 5성 | 어센션 스탯: 치명타 피해

    일반 공격 : 최대 5번 공격한다.
    강공격 : 일정 스태미나를 소모해 회전하는 수정 창을 던져 전방의 적에게 피해를 준다.
    낙하 공격 : 공중에서 땅을 내려찍어 경로상의 적을 공격하고 착지 시 범위 피해를 준다

    E : 극악기 · 섬
        극악 기사의 전투 스타일을 모방하여 짧은 터치 또는 홀드에 따라 각기 다른 효과를 생성한다.

        짧은 터치
        스커크가 뱀의 계략을 45pt 획득하고 일곱빛 섬광 모드로 전환된다.

        홀드
        스커크가 뱀의 계략을 45pt 획득하고 지속적으로 빠르게 이동한다. 해당 상태에서 스커크의 경직 저항력이 증가한다.
        지속 시간 동안 스커크는 방향을 조절하며 빠른 속도로 이동할 수 있고, 수면에서도 이동할 수 있다. 
        다시 스킬을 발동하면 빠른 이동 상태가 조기 종료된다

    Q : 극악기 · 멸
        스커크의 원소폭발은 원소 에너지가 아닌 뱀의 계략에서 나온다.
        스커크가 뱀의 계략을 최소 50pt 보유 시, 스커크는 모든 뱀의 계략을 소모해 원소폭발을 발동할 수 있다. 
        이때 전방의 공간을 찢고 빠른 속도로 연속 참격을 날려 얼음 원소 범위 피해 를 준다. 
        또한 발동 시 스커크가 보유한 뱀의 계략이 50pt를 초과하면, 초과한 뱀의 계략 1pt당 이번 원소폭발로 주는 피해가 증가한다. 
        해당 방식으로 뱀의 계략을 최대 12pt까지 계산한다.

        스커크가 일곱빛 섬광 모드 시, 원소폭발 「극악기·멸」이 「극악기·진」으로 대체된다.

        극악기 · 진
        뱀의 계략을 소모하지 않고 발동할 수 있는 특수 원소폭발.
        발동 후, 스커크가 일곱빛 섬광 모드가 종료될 때까지 지속되는 고갈 효과를 획득한다. 
        고유 특성 이치 너머의 이치를 해금한 후, 스커크가 주변 일정 범위 내의 허계 균열을 흡수한다.
        고갈 효과 지속 시간 동안 0.1초마다 스커크의 일반 공격이 적에게 명중 후, 이번 일반 공격으로 주는 피해가 증가한다. 
        만약 극악기 · 진 발동 시, 허계 균열을 흡수했다면 흡수한 허계 균열 수량에 따라 이번 일반 공격으로 주는 피해가 더 증가한다.
        해당 효과는 10회 발동 후 사라진다

    A1 : 주변에 있는 파티 내 캐릭터가 적에게 빙결, 초전도, 얼음 원소 확산 또는 얼음 원소 결정 반응 발동 시, 적 주변에 허계 균열을 1개 창조한다. 
        해당 효과는 2.5초마다 최대 1회 발동된다. 스커크 자신이 창조한 허계 균열은 필드 위에 최대 3개 존재할 수 있다.

        스커크가 아래 방식으로 주변 일정 범위 내의 허계 균열을 흡수한다:
        · 일곱빛 섬광 모드에서 강공격으로 적 명중 시.
        · 일곱빛 섬광 모드에서 특수 원소폭발 극악기 · 진 발동 시.
        · 홀드로 원소전투 스킬 극악기 · 섬을 발동해 빠른 이동 진행 시.

        허계 균열을 흡수할 때마다 스커크가 뱀의 계략을 8pt 획득한다

    A4 : 파티 내 주변에 있는 물 원소 타입 캐릭터가 물 원소 공격으로 적을 명중하거나,
        파티 내 주변에 있는 다른 얼음 원소 타입 캐릭터가 얼음 원소 공격으로 적 명중 시, 
        스커크가 죽음의 강 효과를 1스택 획득한다. 지속 시간: 20초. 최대 중첩수: 3스택. 
        스택마다 지속 시간은 독립적으로 계산된다.
        각 캐릭터는 해당 방식으로 스커크에게 흐르는 죽음 효과를 최대 1스택 부여할 수 있다.
        죽음의 강 효과 스택마다 스커크가 일곱빛 섬광 모드에서 일반 공격으로 기존의 110%/120%/170%에 해당하는 피해를 주고, 
        원소폭발 극악기 · 멸로 기존의 105%/115%/160%에 해당하는 피해를 준다

    무예 전수
    파티 내 모든 캐릭터의 원소 타입이 물 원소 또는 얼음 원소이며, 
    물 원소와 얼음 원소 캐릭터가 각각 최소 1명씩 있을 경우: 파티 내 자신의 캐릭터 원소전투 스킬 레벨이 Lv.1 증가한다

    C1 : 고유 특성 이치 너머의 이치의 효과가 강화된다: 허계 균열을 1개 흡수할 때마다, 
        수정 칼날 하나를 소환해 주변의 적을 공격하고 스커크 공격력의 500%에 해당하는 얼음 원소 피해를 준다. 
        해당 피해는 강공격 피해로 간주한다.
        고유 특성 「이치 너머의 이치」를 해금해야 한다

    C2 : 원소전투 스킬 극악기 · 섬 발동 후, 스커크가 추가로 뱀의 계략을 10pt 획득한다.
        원소폭발 극악기 · 멸 발동 시, 뱀의 계략을 최대 10pt까지 추가로 계산해 이번 원소폭발로 주는 피해가 증가한다.
        또한, 스커크가 일곱빛 섬광 모드에서 특수 원소폭발 극악기 · 진 발동 후 12.5초간 공격력이 70% 증가한다. \
        해당 효과는 스커크가 일곱빛 섬광 모드에서 퇴장하면 사라진다

    C3 : 원소폭발 극악기 · 멸의 스킬 레벨+3

    C4 : 고유 특성 흐름의 적멸의 효과가 강화된다: 죽음의 강 효과 스택마다 스커크의 공격력이 10%/20%/40% 증가한다.
        고유 특성 「흐름의 적멸」을 해금해야 한다

    C5 : 원소전투 스킬 극악기 · 섬의 스킬 레벨+3
    C6 : 스커크가 고유 특성 이치 너머의 이치의 효과를 통해 허계 균열을 1개 흡수할 때마다 극악기 · 참 효과를 1스택 획득한다, 
        지속 시간: 15초, 최대 중첩수: 3스택. 스택마다 지속 시간은 독립적으로 계산된다.
        고유 특성 「이치 너머의 이치」를 해금해야 한다.

        극악기 · 참
        · 원소폭발 극악기 · 멸 발동 시, 모든 극악기 · 참 스택을 소모하여 협동 공격을 진행한다. 
          극악기 · 참 스택마다 스커크 공격력의 750%에 해당하는 얼음 원소 피해를 준다. 해당 피해는 원소폭발 피해로 간주한다.
        · 스커크가 일곱빛 섬광 모드에서 일반 공격의 세 번째 또는 다섯 번째 공격으로 적 명중 시, 
          극악기 · 참을 1스택 소모해 협동 공격을 3회 진행한다. 협동 공격마다 스커크 공격력의 180%에 해당하는 얼음 원소 피해를 준다. 
          해당 피해는 일반 공격 피해로 간주한다.
        · 스커크가 일곱빛 섬광 모드에서 피해를 받을 시 극악기 · 참을 1스택 소모해 이번 받는 피해를 80% 감소시키고, 
          주변의 적을 3회 공격한다. 공격마다 스커크 공격력의 180%에 해당하는 얼음 원소 피해를 준다. 해당 피해는 강공격 피해로 간주한다
    """
    name = "스커크"
    weapon_type = WeaponType.SWORD
    # 「무예 전수」 보유자 — 파티 원소 구성이 맞으면 파티 전원의 원소전투 스킬 레벨이 +1 된다.
    # 판정은 PartyState.skill_level_bonus가 이 태그를 보고 한다.
    innate_traits = frozenset({CharacterTrait.MARTIAL_INSTRUCTION})

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # ── 일반 공격 「극악기 · 참」 (% ATK, L1~L11) ──────────────────────────────
    # 한손검이라 물리 피해, 최대 5단. 3단은 같은 계수로 2타가 들어간다.
    _NA_HIT1 = [0.5452, 0.5896, 0.6340, 0.6974, 0.7418, 0.7925, 0.8622, 0.9320, 1.0017, 1.0778, 1.1539]
    _NA_HIT2 = [0.4979, 0.5385, 0.5790, 0.6369, 0.6774, 0.7238, 0.7874, 0.8511, 0.9148, 0.9843, 1.0538]
    _NA_HIT3 = [0.3242, 0.3506, 0.3770, 0.4147, 0.4411, 0.4713, 0.5127, 0.5542, 0.5957, 0.6409, 0.6861]
    _NA_HIT4 = [0.6080, 0.6575, 0.7070, 0.7777, 0.8272, 0.8838, 0.9615, 1.0393, 1.1171, 1.2019, 1.2867]
    _NA_HIT5 = [0.8290, 0.8965, 0.9640, 1.0604, 1.1279, 1.2050, 1.3110, 1.4171, 1.5231, 1.6388, 1.7545]
    _NA_HIT3_HITS = 2

    # 강공격 (% ATK, L1~L11) — 스태미나 소모 20, 같은 계수로 2타
    _CA      = [0.6682, 0.7226, 0.7770, 0.8547, 0.9091, 0.9713, 1.0567, 1.1422, 1.2277, 1.3209, 1.4141]
    _CA_HITS = 2

    # 낙하 공격 — 대검을 제외한 무기 공통 표 (베넷/이네파/실로닌과 동일)
    _PLUNGE      = [0.6393, 0.6914, 0.7434, 0.8177, 0.8698, 0.9292, 1.0110, 1.0928, 1.1746, 1.2638, 1.3530]
    _LOW_PLUNGE  = [1.2784, 1.3824, 1.4865, 1.6351, 1.7392, 1.8581, 2.0216, 2.1851, 2.3486, 2.5270, 2.7054]
    _HIGH_PLUNGE = [1.5968, 1.7267, 1.8567, 2.0424, 2.1723, 2.3209, 2.5251, 2.7293, 2.9336, 3.1564, 3.3792]

    # ── 원소 스킬 「극악기 · 섬」 ──────────────────────────────────────────────
    # 스킬 자체는 피해를 주지 않는다 — 뱀의 계략 45pt 획득 + 일곱빛 섬광 모드 전환이 전부다.
    # 따라서 이 스킬의 계수 표는 전부 **일곱빛 섬광 모드의 강화 평타/강공격/낙하** 계수다.
    # 일곱빛 섬광 모드 지속 12.5초, 뱀의 계략 최대 100pt, CD 8초.
    #
    # 레벨 표가 L14까지 있는 이유: 기본 10 + C5(+3) + 고유 특성 「무예 전수」(+1) = 14.
    # (무예 전수 = 파티 전원이 물/얼음이고 물·얼음이 각각 최소 1명 → 원소전투 스킬 레벨 +1)
    _FLASH_NA_HIT1 = [
        1.3282, 1.4364, 1.5445, 1.6989, 1.8070, 1.9306, 2.1005,
        2.2704, 2.4403, 2.6256, 2.8109, 2.9963, 3.1816, 3.3669,
    ]
    _FLASH_NA_HIT2 = [
        1.1980, 1.2955, 1.3930, 1.5323, 1.6298, 1.7413, 1.8945,
        2.0477, 2.2010, 2.3681, 2.5353, 2.7025, 2.8696, 3.0368,
    ]
    _FLASH_NA_HIT3 = [
        0.7572, 0.8189, 0.8805, 0.9686, 1.0302, 1.1006, 1.1975,
        1.2943, 1.3912, 1.4969, 1.6025, 1.7082, 1.8138, 1.9195,
    ]
    _FLASH_NA_HIT4 = [
        0.8054, 0.8709, 0.9365, 1.0301, 1.0957, 1.1706, 1.2736,
        1.3767, 1.4797, 1.5920, 1.7044, 1.8168, 1.9292, 2.0416,
    ]
    _FLASH_NA_HIT5 = [
        1.9662, 2.1263, 2.2863, 2.5150, 2.6750, 2.8579, 3.1094,
        3.3609, 3.6124, 3.8868, 4.1611, 4.4355, 4.7098, 4.9842,
    ]
    _FLASH_NA_HIT3_HITS = 2   # 3단 — 같은 계수로 2타
    _FLASH_NA_HIT4_HITS = 2   # 4단 — 같은 계수로 2타

    # 일곱빛 섬광 강공격 (% ATK, L1~L14) — 스태미나 소모 20, 같은 계수로 3타
    _FLASH_CA      = [
        0.4455, 0.4817, 0.5180, 0.5698, 0.6061, 0.6475, 0.7045,
        0.7615, 0.8184, 0.8806, 0.9428, 1.0049, 1.0671, 1.1292,
    ]
    _FLASH_CA_HITS = 3

    # 일곱빛 섬광 낙하 공격 (% ATK, L1~L14) — 공통 표를 L14까지 연장한 값
    _FLASH_PLUNGE = [
        0.6393, 0.6914, 0.7434, 0.8177, 0.8698, 0.9292, 1.0110,
        1.0928, 1.1746, 1.2638, 1.3530, 1.4422, 1.5314, 1.6206,
    ]
    _FLASH_LOW_PLUNGE = [
        1.2784, 1.3824, 1.4865, 1.6351, 1.7392, 1.8581, 2.0216,
        2.1851, 2.3486, 2.5270, 2.7054, 2.8838, 3.0622, 3.2405,
    ]
    _FLASH_HIGH_PLUNGE = [
        1.5968, 1.7267, 1.8567, 2.0424, 2.1723, 2.3209, 2.5251,
        2.7293, 2.9336, 3.1564, 3.3792, 3.6020, 3.8248, 4.0476,
    ]

    # ── 원소 폭발 「극악기 · 멸」 (% ATK, L1~L13, C3 적용 시 최대 L13) ──────────
    # CD 15초. 원소 에너지가 아니라 뱀의 계략 50pt를 소모해 발동한다.
    _BURST_SLASH_DMG = [
        1.2276, 1.3197, 1.4117, 1.5345, 1.6266,
        1.7186, 1.8414, 1.9642, 2.0869, 2.2097,
        2.3324, 2.4552, 2.6087,
    ]
    _BURST_SLASH_HITS = 5   # 연속 참격 5회
    _BURST_FINAL_SLASH_DMG = [
        2.0460, 2.1995, 2.3529, 2.5575, 2.7109,
        2.8644, 3.0690, 3.2736, 3.4782, 3.6828,
        3.8874, 4.0920, 4.3477,
    ]

    # 뱀의 계략 보너스 — 50pt 초과분 1pt당 폭발 피해 증가 (% ATK/pt, L1~L13).
    # 기본 최대 12pt까지 계산하며, C2가 최대 10pt를 추가로 계산해 준다.
    _BURST_SERPENT_BONUS_PER_PT = [
        0.1932, 0.2077, 0.2222, 0.2415, 0.2560,
        0.2705, 0.2898, 0.3092, 0.3285, 0.3478,
        0.3671, 0.3865, 0.4106,
    ]
    _BURST_SERPENT_MAX_PT    = 12   # 기본 상한
    _BURST_SERPENT_C2_MAX_PT = 10   # C2 추가 상한

    # ── 특수 원소 폭발 「극악기 · 진」의 고갈 효과 (%, L1~L13) ──────────────────
    # 고갈 지속 시간 동안 평타가 명중할 때마다 이번 일반 공격 피해가 증가한다(최대 10회).
    # 흡수한 허계 균열 수(0/1/2/3개)에 따라 1회당 증가폭이 달라진다.
    _VOID_RIFT_NA_DMG_BONUS = [
        (0.035, 0.066, 0.088, 0.11),   # L1
        (0.040, 0.072, 0.096, 0.12),   # L2
        (0.045, 0.078, 0.104, 0.13),   # L3
        (0.050, 0.084, 0.112, 0.14),   # L4
        (0.055, 0.090, 0.120, 0.15),   # L5
        (0.060, 0.096, 0.128, 0.16),   # L6
        (0.065, 0.102, 0.136, 0.17),   # L7
        (0.070, 0.108, 0.144, 0.18),   # L8
        (0.075, 0.114, 0.152, 0.19),   # L9
        (0.080, 0.120, 0.160, 0.20),   # L10
        (0.085, 0.126, 0.168, 0.21),   # L11
        (0.090, 0.132, 0.176, 0.22),   # L12
        (0.095, 0.138, 0.184, 0.23),   # L13
    ]
    _VOID_RIFT_MAX_STACKS = 10

    # ── 고유 특성 / 명함 계수 (히트 아님 — 버프 훅에서 사용) ────────────────────
    # A4 「흐름의 적멸」: 죽음의 강 1/2/3스택 → 일곱빛 섬광 평타 / 극악기·멸 피해 배율
    _A4_FLOW_NA_MULT    = (1.10, 1.20, 1.70)
    _A4_FLOW_BURST_MULT = (1.05, 1.15, 1.60)
    _A4_FLOW_MAX_STACKS = 3
    # C4: 죽음의 강 스택마다 공격력 증가
    _C4_FLOW_ATK_PCT = (0.10, 0.20, 0.40)
    # C2: 극악기·진 발동 후 공격력 +70% (12.5초)
    _C2_BURST_ATK_PCT = 0.70

    # ── 명함 추가 히트 계수 (% ATK) ────────────────────────────────────────────
    _C1_CRYSTAL_BLADE_DMG = 5.00   # C1 수정 칼날 — 「강공격 피해로 간주」, 균열 1개 흡수당 1회
    _C6_COOP_BURST_DMG    = 7.50   # C6 협동 공격 — 「원소폭발 피해로 간주」, 참 스택당 1회
    _C6_COOP_NA_DMG       = 1.80   # C6 협동 공격 — 「일반 공격 피해로 간주」, 3회
    _C6_COOP_CA_DMG       = 1.80   # C6 협동 공격 — 「강공격 피해로 간주」, 3회
    _C6_COOP_HITS         = 3
    _C6_SLASH_MAX_STACKS  = 3
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 5
    BURST_LEVEL_UP_CONSTELLATION = 3
    NA_TABLES = (_NA_HIT1, _NA_HIT2, _NA_HIT3, _NA_HIT4, _NA_HIT5, _CA, _PLUNGE, _LOW_PLUNGE,
        _HIGH_PLUNGE,)
    SKILL_TABLES = (_FLASH_NA_HIT1, _FLASH_NA_HIT2, _FLASH_NA_HIT3, _FLASH_NA_HIT4,
        _FLASH_NA_HIT5, _FLASH_CA, _FLASH_PLUNGE, _FLASH_LOW_PLUNGE, _FLASH_HIGH_PLUNGE,)
    BURST_TABLES = (_BURST_SLASH_DMG, _BURST_FINAL_SLASH_DMG, _BURST_SERPENT_BONUS_PER_PT,
        _VOID_RIFT_NA_DMG_BONUS,)

    rarity         = 5
    ascension_stat = StatType.CRIT_DMG

    @property
    def element(self)  -> Element: return Element.CRYO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        c = self.constellation

        # C5: 원소전투 스킬 레벨 +3 (최대 L13)
        # C3: 원소 폭발 레벨 +3 (최대 L13) — 스커크는 다른 캐릭터와 C3/C5가 반대다.
        # 고유 특성 「무예 전수」의 +1(→L14)은 파티 구성으로 정해지므로 Party가 히트 생성
        # 전에 skill_level_bonus에 넣어 준다 — 스커크 본인도 파티원이라 여기서 함께 받는다.
        sk = self._skill_index()
        bl = self._burst_index()
        nl = self._na_index()

        # 뱀의 계략/고갈 보너스가 재사용한다.
        self._bl = bl

        hits: list[SkillHit] = []

        def flash(name: str, skill_type: SkillType, table: list[float]) -> None:
            hits.append(SkillHit(name, skill_type, table[sk], ScalingStat.ATK, Element.CRYO))

        # ── 기본 평타 — 한손검이라 물리 피해(element 미지정 → PHYSICAL) ─────────
        hits.append(SkillHit("1단 공격 피해", SkillType.NORMAL_ATK, self._NA_HIT1[nl], ScalingStat.ATK))
        hits.append(SkillHit("2단 공격 피해", SkillType.NORMAL_ATK, self._NA_HIT2[nl], ScalingStat.ATK))
        for i in range(self._NA_HIT3_HITS):
            hits.append(SkillHit(f"3단 공격 피해 {i+1}타", SkillType.NORMAL_ATK, self._NA_HIT3[nl], ScalingStat.ATK))
        hits.append(SkillHit("4단 공격 피해", SkillType.NORMAL_ATK, self._NA_HIT4[nl], ScalingStat.ATK))
        hits.append(SkillHit("5단 공격 피해", SkillType.NORMAL_ATK, self._NA_HIT5[nl], ScalingStat.ATK))

        for i in range(self._CA_HITS):
            hits.append(SkillHit(f"강공격 피해 {i+1}타", SkillType.CHARGED_ATK, self._CA[nl], ScalingStat.ATK))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK))

        # ── 일곱빛 섬광 모드 — 강화 평타/강공격/낙하, 전부 얼음 원소 피해 ─────────
        # 원소 스킬 「극악기 · 섬」 자체는 피해가 없어 히트를 만들지 않는다.
        flash("일곱빛 섬광 1단 공격 피해", SkillType.NORMAL_ATK, self._FLASH_NA_HIT1)
        flash("일곱빛 섬광 2단 공격 피해", SkillType.NORMAL_ATK, self._FLASH_NA_HIT2)
        for i in range(self._FLASH_NA_HIT3_HITS):
            flash(f"일곱빛 섬광 3단 공격 피해 {i+1}타", SkillType.NORMAL_ATK, self._FLASH_NA_HIT3)
        for i in range(self._FLASH_NA_HIT4_HITS):
            flash(f"일곱빛 섬광 4단 공격 피해 {i+1}타", SkillType.NORMAL_ATK, self._FLASH_NA_HIT4)
        flash("일곱빛 섬광 5단 공격 피해", SkillType.NORMAL_ATK, self._FLASH_NA_HIT5)

        for i in range(self._FLASH_CA_HITS):
            flash(f"일곱빛 섬광 강공격 피해 {i+1}타", SkillType.CHARGED_ATK, self._FLASH_CA)

        flash("일곱빛 섬광 낙하 기간 피해",     SkillType.PLUNGING, self._FLASH_PLUNGE)
        flash("일곱빛 섬광 저공 추락 충격 피해", SkillType.PLUNGING, self._FLASH_LOW_PLUNGE)
        flash("일곱빛 섬광 고공 추락 충격 피해", SkillType.PLUNGING, self._FLASH_HIGH_PLUNGE)

        # ── 원소 폭발 「극악기 · 멸」 — 연속 참격 5회 + 마지막 참격 ────────────
        for i in range(self._BURST_SLASH_HITS):
            hits.append(SkillHit(f"원소 폭발 참격 피해 {i+1}타", SkillType.BURST, self._BURST_SLASH_DMG[bl], ScalingStat.ATK, Element.CRYO))
        hits.append(SkillHit("원소 폭발 마지막 참격 피해", SkillType.BURST, self._BURST_FINAL_SLASH_DMG[bl], ScalingStat.ATK, Element.CRYO))

        # ── 명함 추가 히트 ────────────────────────────────────────────────────
        # 조건부 히트도 반드시 build_hits에서 만든다 — apply_self_buffs에서 만들면
        # 기초 스탯을 채우는 루프가 이미 끝난 뒤라 공격력이 0으로 남는다.
        if c >= 1:
            hits.append(SkillHit(
                "C1 수정 칼날 피해", SkillType.CHARGED_ATK,
                self._C1_CRYSTAL_BLADE_DMG, ScalingStat.ATK, Element.CRYO,
            ))

        if c >= 6:
            hits.append(SkillHit(
                "C6 협동 공격 피해 (폭발)", SkillType.BURST,
                self._C6_COOP_BURST_DMG, ScalingStat.ATK, Element.CRYO,
            ))
            for i in range(self._C6_COOP_HITS):
                hits.append(SkillHit(
                    f"C6 협동 공격 피해 (일반) {i+1}타", SkillType.NORMAL_ATK,
                    self._C6_COOP_NA_DMG, ScalingStat.ATK, Element.CRYO,
                ))
            # 피격 반격은 협동 공격과 트리거가 다르다(평타 명중이 아니라 피격).
            # 로테이션에 넣을지 여부가 갈리므로 별도 히트로 분리해 둔다.
            for i in range(self._C6_COOP_HITS):
                hits.append(SkillHit(
                    f"C6 피격 반격 피해 {i+1}타", SkillType.CHARGED_ATK,
                    self._C6_COOP_CA_DMG, ScalingStat.ATK, Element.CRYO,
                ))

        return {h.name: h for h in hits}

    # ── 히트 그룹 선택자 ──────────────────────────────────────────────────
    # C6 협동 공격은 「일반 공격 / 원소폭발 피해로 간주」되므로, 평타·폭발에 붙는
    # 강화 효과를 각각 함께 받는다. 그래서 대상 집합이 효과별로 갈리지 않고
    # 「무엇으로 간주되는가」 하나로 정해진다.
    @staticmethod
    def _na_effect_hits(hits: dict[str, SkillHit]) -> list[SkillHit]:
        """일반 공격으로 간주되는 히트 — 일곱빛 섬광 강화 평타 + C6 협동 공격(일반).
        A4 평타 배율과 극악기·진 고갈 효과가 함께 대상으로 삼는다.
        (C6 피격 반격은 강공격 판정이라 제외된다.)"""
        return [h for n, h in hits.items()
                if (n.startswith("일곱빛 섬광") and h.skill_type is SkillType.NORMAL_ATK)
                or n.startswith("C6 협동 공격 피해 (일반)")]

    @staticmethod
    def _burst_effect_hits(hits: dict[str, SkillHit]) -> list[SkillHit]:
        """원소 폭발로 간주되는 히트 — 극악기·멸 본체 + C6 협동 공격(폭발).
        A4 폭발 배율과 뱀의 계략 보너스가 함께 대상으로 삼는다."""
        return [h for n, h in hits.items()
                if n.startswith("원소 폭발") or n == "C6 협동 공격 피해 (폭발)"]

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        c  = self.constellation
        bl = self._bl

        # ── Q 「극악기 · 멸」: 뱀의 계략 50pt 초과분 1pt당 피해 증가 ────────────
        # 값이 「% ATK / pt」라 계수와 차원이 같다 → flat_dmg_bonus가 아니라 coeff에
        # 가산한다. 공식이 (coeff × stat × coeff_amp + flat)이므로, coeff에 넣어야
        # A4의 폭발 배율(coeff_amp)이 이 증가분에도 함께 걸린다.
        max_pt = self._BURST_SERPENT_MAX_PT + (self._BURST_SERPENT_C2_MAX_PT if c >= 2 else 0)
        pts = ask_int("[스커크 Q] 극악기·멸 발동 시 50pt 초과 뱀의 계략", 0, max_pt)
        if pts:
            bonus = self._BURST_SERPENT_BONUS_PER_PT[bl] * pts
            for hit in self._burst_effect_hits(hits):
                hit.add("coeff", bonus, self, note="뱀의 계략")

        # ── Q 「극악기 · 진」: 고갈 효과 + C2 공격력 증가 ──────────────────────
        # 극악기·진은 일곱빛 섬광 모드에서 극악기·멸을 대체하는 특수 폭발이라
        # 한 로테이션에 둘 중 하나만 나간다. 계산기는 두 갈래를 모두 보여주므로
        # 위의 뱀의 계략과 아래 고갈 효과를 동시에 물어본다(콜롬비나 인력 간섭과 동일).
        if ask_bool("[스커크 Q] 특수 원소폭발 극악기·진 발동 여부"):
            rifts  = ask_int("[스커크 Q] 극악기·진 발동 시 흡수한 허계 균열 수", 0, 3)
            per_stack = self._VOID_RIFT_NA_DMG_BONUS[bl][rifts]
            for hit in self._na_effect_hits(hits):
                hit.add("normal_atk_dmg_bonus", per_stack, self, note="극악기·진 고갈")

            # C2: 극악기·진 발동 후 12.5초간 공격력 +70% (섬광 모드 퇴장 시 소멸)
            if c >= 2:
                for hit in hits.values():
                    hit.add("atk_pct", self._C2_BURST_ATK_PCT, self, note="C2")

    # ── 파티 버프 4: 파티 구성 판정 + 코어 스탯 기여 ─────────────────────────
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c       = self.constellation
        hits    = all_hits[self]
        members = list(all_hits)

        n_hydro      = sum(1 for ch in members if ch.element is Element.HYDRO)
        n_other_cryo = sum(1 for ch in members if ch.element is Element.CRYO and ch is not self)

        # 고유 특성 「무예 전수」(원소전투 스킬 레벨 +1)는 파티 **전원**이 받는 효과라
        # 여기서 스커크 히트만 손대면 안 된다. 파티 원소 구성만으로 판정되므로
        # PartyState.skill_level_bonus가 계산해 Party가 히트 생성 전에 각 캐릭터의
        # skill_level_bonus에 넣어 주고, 각자의 build_hits가 계수 표에서 반영한다.

        # ── A4 「흐름의 적멸」: 죽음의 강 스택 수 ────────────────────────────────
        # 「각 캐릭터는 최대 1스택」이라 상한이 파티 구성으로 정해진다 —
        # 물 캐릭터 + (스커크를 제외한) 얼음 캐릭터 수, 최대 3스택.
        cap = min(self._A4_FLOW_MAX_STACKS, n_hydro + n_other_cryo)
        self._flow_stacks = ask_int("[스커크 A4] 죽음의 강 스택 수", 0, cap) if cap else 0

        # C4: 죽음의 강 스택마다 공격력 +10%/20%/40% — 코어 풀 기여라 이 단계가 제자리.
        if c >= 4 and self._flow_stacks:
            atk_pct = self._C4_FLOW_ATK_PCT[self._flow_stacks - 1]
            for hit in hits.values():
                hit.add("atk_pct", atk_pct, self, note="C4")

    # ── 파티 버프 4.5: 스탯을 읽지 않는 버프 ─────────────────────────────────
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # A4: 죽음의 강 스택마다 「기존의 N%에 해당하는 피해」 — 계수 배율이므로
        # coeff_amp에 넣는다. coeff_amp는 1.0에서 시작하니 (배율 - 1.0)을 가산하면
        # 최종값이 그대로 배율이 되고, 원장에도 기여가 남는다.
        if not self._flow_stacks:
            return

        hits  = all_hits[self]
        index = self._flow_stacks - 1

        for hit in self._na_effect_hits(hits):
            hit.add("coeff_amp", self._A4_FLOW_NA_MULT[index] - 1.0, self, note="A4 죽음의 강")
        for hit in self._burst_effect_hits(hits):
            hit.add("coeff_amp", self._A4_FLOW_BURST_MULT[index] - 1.0, self, note="A4 죽음의 강")

    # ── 파티 버프 5: 최종 스탯을 읽어 스케일하는 버프 (방식 B) ────────────────
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # 스커크는 파티에 주는 버프도, 최종 스탯을 읽어 스케일하는 버프도 없다.
        # 자기 버프는 전부 Phase 3/4에서 끝난다 (뱀의 계략은 % ATK라 계수로 처리).
        pass
