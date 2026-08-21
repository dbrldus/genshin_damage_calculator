from gidc.core.character import Character, clamp_talent_index
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import Element
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_int


class Citlali(Character):
    """시틀라리 (Citlali) | 얼음 | 법구 | 5성 | 어센션 스탯: 원소 마스터리

    일반 공격 : 대대로 전해진 연기 주인의 비밀 의식으로 최대 3번 공격해 얼음 원소 피해를 준다.
    강공격 : 조준 상태에 진입하며 홀드 종료 시, 일정 스태미나를 소모해 조준 방향으로 차가운 별을 1개 날려 경로상의 적에게 얼음 원소 피해를 준다.
    낙하 공격 : 공중에서 원소의 힘을 모은 후 지면을 강타해 경로상의 적을 공격하고 착지 시 얼음 원소 범위 피해를 준다.

    E : 검은 서리별
    연기 주인에서 천 년 동안 전승되어 온 비밀 계약에 따라, 하얀빛 보호막을 펼치고 무시무시(소문)한 「검은빛 치치미틀」이즈파파를 소환해 밤혼 성질의 얼음 원소 범위 피해를 준다.
    하얀빛 보호막의 피해 흡수량은 시틀라리의 원소 마스터리의 영향을 받으며 얼음 원소 피해에 대해 250%의 흡수 효과가 있다.
    발동 후, 시틀라리가 밤혼을 24pt를 획득하고 밤혼 가호 상태에 진입한다.

    밤혼 가호 · 시틀라리
    이즈파파가 퇴장 시, 시틀라리의 밤혼 가호는 종료된다.

    이즈파파
    ·이즈파파는 캐릭터를 따라 행동한다.
    ·시틀라리가 밤혼을 최소 50pt 보유한 경우, 이즈파파가 하얀 불 상태에 진입해 지속적으로 밤혼을 소모하며 캐릭터를 따라다니는 서리운석 폭풍을 일으켜 범위 내의 적을 공격해 밤혼 성질의 얼음 원소 피해를 준다.
    ·밤혼 소진 시, 이즈파파의 하얀 불 상태도 종료된다.

    Q : 반짝이는 칙령
    하늘과 대지의 「맹우」에게 얼음 폭풍으로 전방을 습격하도록 지시하여 밤혼 성질의 얼음 원소 범위 피해를 주고 시틀라리의 밤혼을 일정량 회복하며,
    범위 내 최대 3기의 적 주변에 영혼 해골을 소환한다. 영혼 해골은 일정 시간이 지난 후 폭발해 밤혼 성질의 얼음 원소 피해를 주고 시틀라리의 밤혼을 일정량 회복한다.

    A1 : 다섯 번째 하늘의 서리비
    이즈파파 존재 기간 동안, 주변에 있는 파티 내 캐릭터가 빙결 또는 융해 반응 발동 후, 이번 반응의 영향을 받은 적의 불 원소와 물 원소 내성이 20% 감소한다, 지속 시간: 12초.
    또한 시틀라리가 밤혼을 16pt 회복한다. 해당 방식으로 8초마다 밤혼이 최대 1회 회복된다

    A4 : 하얀 불나비의 별옷
    원소전투 스킬 검은 서리별의 이즈파파가 일으킨 서리운석 폭풍이 주는 피해가 시틀라리 원소 마스터리의 90%만큼 증가한다.
    원소폭발 반짝이는 칙령의 얼음 폭풍이 주는 피해가 시틀라리 원소 마스터리의 1200%만큼 증가한다.
    또한 주변에 있는 파티 내 캐릭터가 「밤혼 발산」 발동 시, 시틀라리는 추가로 밤혼을 4pt 회복한다

    C1 : 사백 개의 별빛
    원소전투 스킬 검은 서리별 발동 시, 시틀라리는 이즈파파가 퇴장 전까지 지속되는 「흰별 치마」 효과를 획득한다: 지속 시간 동안 시틀라리가 「별빛 검」 효과를 10스택 획득한다.
    주변에 있는 시틀라리를 제외한 현재 필드 위 캐릭터가 일반 공격, 강공격, 낙하 공격, 원소전투 스킬 또는 원소폭발로 피해를 줄 시,
    「별빛 검」 1스택을 소모해 주는 피해를 시틀라리 원소 마스터리의 200%만큼 증가시킨다.
    주변에 있는 파티 내 캐릭터가 빙결 또는 융해 반응 발동 후, 시틀라리가 「별빛 검」을 추가로 3스택 획득한다. 해당 효과는 8초마다 최대 1회 발동된다.

    원소전투 스킬 검은 서리별 발동 시, 「별빛 검」의 스택이 갱신된다.
    또한 시틀라리가 도약하거나 공중에서 조준 혹은 강공격 진행 시, 소모되는 열소가 45% 감소한다

    C2 : 심장을 삼키는 자의 순행
    시틀라리의 원소 마스터리가 125pt 증가하고 하얀빛 보호막의 보호를 받고 있거나 이즈파파가 따라다니고 있는 다른 캐릭터의 원소 마스터리가 250pt 증가한다.
    또한 원소전투 스킬 검은 서리별 발동 시, 주변에 있는 현재 필드 위 캐릭터에게 하얀빛 보호막을 부여한다.

    또한 고유 특성 「다섯 번째 하늘의 서리비」 효과가 증가한다:
    이즈파파 존재 기간 동안, 주변에 있는 파티 내 캐릭터가 빙결 또는 융해 반응 발동 후, 이번 반응의 영향을 받은 적의 불 원소와 물 원소 내성이 추가로 20% 감소한다,
    지속 시간: 12초. 해당 효과는 고유 특성 「다섯 번째 하늘의 서리비」를 해금해야 한다

    C3 : 구름뱀의 깃털 왕관
    원소전투 스킬 검은 서리별의 스킬 레벨+3

    C4 : 죽음을 거부하는 자의 영혼 해골
    원소전투 스킬 검은 서리별의 이즈파파가 일으킨 서리운석 폭풍이 적에게 명중 시, 영혼 해골 · 검은별을 추가로 소환한다.
    해당 방식으로 소환한 영혼 해골이 폭발 시, 시틀라리 원소 마스터리의 1800%에 해당하는 밤혼 성질의 얼음 원소 범위 피해를 주고,
    시틀라리의 밤혼을 16pt, 원소에너지를 8pt 회복한다. 해당 효과는 8초마다 최대 1회 발동된다. 해당 피해는 원소폭발 피해로 간주하지 않는다

    C5 : 불길한 닷새의 주술
    원소폭발 반짝이는 칙령의 스킬 레벨+3

    C6 : 아홉 번째 하늘의 계약
    원소전투 스킬 검은 서리별이 소환한 이즈파파가 계속 하얀 불 상태를 유지한다. 밤혼 소진 시에도 이즈파파의 하얀 불 상태가 종료되지 않는다.
    또한 원소전투 스킬 검은 서리별 발동 시, 이즈파파는 모든 밤혼을 소모하고 존재 기간 동안 지속적으로 밤혼을 소모한다. 해당 방식으로 밤혼을 1pt 소모하면, 시틀라리가 「신비의 수」를 1pt 획득한다.
    시틀라리가 보유한 「신비의 수」 1pt 당, 주변에 있는 파티 내 캐릭터가 불 원소, 물 원소 피해 보너스를 1.5% 획득하고 시틀라리가 주는 피해가 2.5% 증가한다. 「신비의 수」최대치: 40pt.
    이즈파파가 퇴장 또는 원소 전투 스킬 재발동 시, 시틀라리가 보유한 「신비의 수」가 사라진다
    """
    name = "시틀라리"
    weapon_type = WeaponType.CATALYST


    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # 일반 공격 「영혼 포착」 (% ATK, L1~L11) — 법구라 3단 모두 얼음 원소 피해
    _NA_HIT1 = [0.4340, 0.4670, 0.4990, 0.5430, 0.5750, 0.6080, 0.6510, 0.6950, 0.7380, 0.7810, 0.8250]
    _NA_HIT2 = [0.3880, 0.4170, 0.4460, 0.4850, 0.5140, 0.5430, 0.5820, 0.6210, 0.6600, 0.6990, 0.7370]
    _NA_HIT3 = [0.5380, 0.5780, 0.6180, 0.6720, 0.7120, 0.7530, 0.8070, 0.8600, 0.9140, 0.9680, 1.0220]

    # 강공격 (% ATK, L1~L11) — 스태미나 소모 50, 조준해 차가운 별 1개를 날린다
    _CA = [0.9920, 1.0660, 1.1410, 1.2400, 1.3140, 1.3890, 1.4880, 1.5870, 1.6860, 1.7860, 1.8850]

    # 낙하 공격 (% ATK, L1~L11) — 법구 전용표 (모나/콜롬비나와 같은 값)
    _PLUNGE      = [0.5683, 0.6145, 0.6608, 0.7269, 0.7731, 0.8260, 0.8987, 0.9714, 1.0441, 1.1234, 1.2027]
    _LOW_PLUNGE  = [1.1363, 1.2288, 1.3213, 1.4535, 1.5459, 1.6517, 1.7970, 1.9423, 2.0877, 2.2462, 2.4048]
    _HIGH_PLUNGE = [1.4193, 1.5349, 1.6504, 1.8154, 1.9310, 2.0630, 2.2445, 2.4261, 2.6076, 2.8057, 3.0037]

    # ── 원소 스킬 「검은 서리별」 (% ATK, L1~L14) ───────────────────────────────
    # 보호막/이즈파파 지속 20초, 하얀 불 밤혼 소모 8.0pt/초, CD 16초.
    #
    # 표가 L14까지 있는 이유: 기본 10 + C3(+3) + 스커크 고유 특성 「무예 전수」(+1) = 14.
    # (무예 전수 = 파티 전원이 물/얼음이고 물·얼음이 각각 최소 1명 → 파티 전원 원소전투
    #  스킬 레벨 +1. 시틀라리는 얼음이라 그 파티에 들어갈 수 있다.)
    _SKILL_TZITZIMITL_DMG = [   # 흑요 치치미틀 피해 — E 발동 시 1회
        0.7300, 0.7840, 0.8390, 0.9120, 0.9670, 1.0210, 1.0940,
        1.1670, 1.2400, 1.3130, 1.3860, 1.4590, 1.5500, 1.6420,
    ]
    _SKILL_METEOR_STORM_DMG = [ # 서리운석 폭풍 피해 — 이즈파파 하얀 불 상태의 지속 타격
        0.1700, 0.1830, 0.1960, 0.2130, 0.2260, 0.2380, 0.2550,
        0.2720, 0.2890, 0.3060, 0.3230, 0.3400, 0.3620, 0.3830,
    ]
    # 하얀빛 보호막 흡수량 (원소 마스터리의 %  + 고정값, L1~L14).
    # 보호막은 피해가 아니라 SkillHit을 만들지 않는다 — 세트/명함 조건 판정용으로 보관한다.
    # (얼음 원소 피해에 대해서는 250% 흡수.)
    _SHIELD_EM   = [
        5.7600, 6.1920, 6.6240, 7.2000, 7.6320, 8.0640, 8.6400,
        9.2160, 9.7920, 10.3680, 10.9440, 11.5200, 12.2400, 12.9600,
    ]
    _SHIELD_FLAT = [   # L3은 원본 표에 「19.6」으로 적혀 있으나 증가 추세상 1674가 맞다.
        1387, 1525, 1676, 1837, 2011, 2196, 2392,
        2600, 2820, 3051, 3294, 3548, 3814, 4091,
    ]
    _SHIELD_CRYO_ABSORB = 2.50

    # ── 원소 폭발 「반짝이는 칙령」 (% ATK, L1~L13, C5 적용 시 최대 L13) ────────
    # 얼음 폭풍 밤혼 획득 24pt / 영혼 해골 밤혼 획득 3pt, CD 15초, 원소 에너지 60.
    _BURST_ICE_STORM_DMG = [   # 얼음 폭풍 피해
        5.3760, 5.7790, 6.1820, 6.7200, 7.1230,
        7.5260, 8.0640, 8.6020, 9.1390, 9.6770,
        10.2140, 10.7520, 11.4240,
    ]
    _BURST_SKULL_DMG = [       # 영혼 해골 피해 — 범위 내 최대 3기까지 소환된다
        1.3440, 1.4450, 1.5460, 1.6800, 1.7810,
        1.8820, 2.0160, 2.1500, 2.2850, 2.4190,
        2.5540, 2.6880, 2.8560,
    ]

    # ── 고유 특성 / 명함 계수 (히트 아님 — 버프 훅에서 사용) ────────────────────
    # A1 : 빙결·융해 반응의 영향을 받은 적의 불·물 내성 감소 (C2가 추가로 20% 더 깎는다)
    _A1_RES_REDUCTION       = 0.20
    _C2_A1_EXTRA_RES_REDUCTION = 0.20
    # A4 : 서리운석 폭풍 / 얼음 폭풍 피해에 더해지는 원소 마스터리 배율
    _A4_METEOR_STORM_EM = 0.90
    _A4_ICE_STORM_EM    = 12.00
    # C1 : 「별빛 검」 1스택 소모 시 다른 캐릭터의 피해 증가 (원소 마스터리 배율) / 스택
    _C1_STARLIGHT_BLADE_EM     = 2.00
    _C1_STARLIGHT_STACKS       = 10
    _C1_STARLIGHT_REACTION_GAIN = 3
    # C2 : 원소 마스터리 증가 — 자신 / 보호막·이즈파파의 보호를 받는 다른 캐릭터
    _C2_SELF_EM  = 125
    _C2_ALLY_EM  = 250
    # C6 : 「신비의 수」 1pt당 파티 불·물 피해 보너스 / 시틀라리 피해 증가, 상한 40pt
    _C6_PER_PT_ELEM_DMG = 0.015
    _C6_PER_PT_SELF_DMG = 0.025
    _C6_MYSTIC_MAX      = 40

    # ── 명함 추가 히트 계수 (% 원소 마스터리) ──────────────────────────────────
    _C4_BLACKSTAR_SKULL_EM = 18.00   # C4 영혼 해골 · 검은별 — 「원소폭발 피해로 간주하지 않는다」
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 3
    BURST_LEVEL_UP_CONSTELLATION = 5
    NA_TABLES = (_NA_HIT1, _NA_HIT2, _NA_HIT3, _CA, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_TZITZIMITL_DMG, _SKILL_METEOR_STORM_DMG, _SHIELD_EM, _SHIELD_FLAT,)
    BURST_TABLES = (_BURST_ICE_STORM_DMG, _BURST_SKULL_DMG,)

    rarity         = 5
    ascension_stat = StatType.ELEMENTAL_MASTERY

    @property
    def element(self)  -> Element: return Element.CRYO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        c = self.constellation

        # C3: 원소 스킬 레벨 +3 (최대 13, 무예 전수까지 받으면 14)
        sk = self._skill_index()
        # C5: 원소 폭발 레벨 +3 (최대 13)
        bl = self._burst_index()
        nl = self._na_index()

        hits: list[SkillHit] = []

        # 법구 캐릭터라 일반/강/낙하 공격도 모두 얼음 원소 피해다 (모나·니콜과 동일)
        for name, coeff in [
            ("1단 공격 피해", self._NA_HIT1[nl]),
            ("2단 공격 피해", self._NA_HIT2[nl]),
            ("3단 공격 피해", self._NA_HIT3[nl]),
        ]:
            hits.append(SkillHit(name, SkillType.NORMAL_ATK, coeff, ScalingStat.ATK, Element.CRYO))

        hits.append(SkillHit("강공격 피해", SkillType.CHARGED_ATK, self._CA[nl],
                             ScalingStat.ATK, Element.CRYO))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK, Element.CRYO))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK, Element.CRYO))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK, Element.CRYO))

        hits.append(SkillHit("흑요 치치미틀 피해", SkillType.SKILL, self._SKILL_TZITZIMITL_DMG[sk],
                             ScalingStat.ATK, Element.CRYO))
        hits.append(SkillHit("서리운석 폭풍 피해", SkillType.SKILL, self._SKILL_METEOR_STORM_DMG[sk],
                             ScalingStat.ATK, Element.CRYO))

        hits.append(SkillHit("얼음 폭풍 피해", SkillType.BURST, self._BURST_ICE_STORM_DMG[bl],
                             ScalingStat.ATK, Element.CRYO))
        hits.append(SkillHit("영혼 해골 피해", SkillType.BURST, self._BURST_SKULL_DMG[bl],
                             ScalingStat.ATK, Element.CRYO))

        # ── 명함 추가 히트 ────────────────────────────────────────────────────
        # 조건부 히트도 반드시 build_hits에서 만든다 — apply_self_buffs에서 만들면
        # 기초 스탯을 채우는 루프가 이미 끝난 뒤라 스탯이 0으로 남는다.
        #
        # C4 「영혼 해골 · 검은별」: 서리운석 폭풍 명중이 트리거이고 「원소폭발 피해로
        # 간주하지 않는다」고 못 박혀 있어 원소 스킬 피해로 둔다. 공격력이 아니라
        # 원소 마스터리로 스케일하는 유일한 히트다(ScalingStat.EM).
        if c >= 4:
            hits.append(SkillHit(
                "C4 영혼 해골 · 검은별 피해", SkillType.SKILL,
                self._C4_BLACKSTAR_SKULL_EM, ScalingStat.EM, Element.CRYO,
            ))

        return {h.name: h for h in hits}

    # ── 빙결·융해 가능 여부 (A1 / C1 스택 충전의 공통 전제) ────────────────────
    # 시틀라리가 얼음을 붙이므로 파티에 물이 있으면 빙결, 불이 있으면 융해가 성립한다.
    # 파티 원소 구성만으로 정해지는 판정이라 유저에게 묻지 않는다 — 둘 다 없는 파티에서는
    # 애초에 발동할 수 없으므로 질문 자체를 만들지 않는다.
    _REACTION_PARTNER_ELEMENTS = (Element.HYDRO, Element.PYRO)

    def _can_freeze_or_melt(self, all_hits: dict["Character", dict[str, SkillHit]]) -> bool:
        return any(char.element in self._REACTION_PARTNER_ELEMENTS for char in all_hits)

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        # C2 「심장을 삼키는 자의 순행」 앞부분: 시틀라리 자신의 원소 마스터리 +125.
        # 조건이 없는 상시 효과라 파티를 볼 것이 없어 여기(Phase 3)서 끝난다.
        # 다른 캐릭터에게 주는 +250은 보호막/이즈파파 조건이 붙어
        # contribute_dependent_stats(Phase 4)로 나뉘어 있다.
        if self.constellation >= 2:
            for hit in hits.values():
                hit.add("em_from_flat", self._C2_SELF_EM, self, note="C2")

    # ── 파티 버프 4: 코어 스탯 기여 + 유저 입력 수집 ─────────────────────────
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # 이즈파파 존재 여부 — A1·C1·C2(타인)·C6가 모두 이 조건에 걸려 있어 한 번만 묻는다.
        self._e_active = ask_bool("[시틀라리 E] 이즈파파 존재 여부")

        # A1 「다섯 번째 하늘의 서리비」: 파티원이 빙결 또는 융해를 발동해야 한다.
        # 어떤 반응이 가능한지는 파티 원소 구성이 정하므로 불가능한 파티에는 묻지 않는다.
        self._a1_active = (
            self._e_active
            and self._can_freeze_or_melt(all_hits)
            and ask_bool("[시틀라리 A1] 빙결·융해 반응 발동 (적 불·물 내성 감소) 여부")
        )

        # C6 「신비의 수」: 이즈파파가 소모한 밤혼 1pt당 1pt 획득, 최대 40pt.
        # 밤혼 수지는 모델에 없으므로 보유량을 그대로 묻는다.
        self._mystic_count = (
            ask_int("[시틀라리 C6] 보유한 「신비의 수」", 0, self._C6_MYSTIC_MAX)
            if c >= 6 and self._e_active else 0
        )

        # C2 뒷부분: 하얀빛 보호막을 받고 있거나 이즈파파가 따라다니는 **다른** 캐릭터의
        # 원소 마스터리 +250. C2 자신이 필드 위 캐릭터에게 보호막을 부여하므로 이즈파파가
        # 나와 있으면 주변 파티원이 모두 조건을 만족한다.
        # 다른 캐릭터 스탯의 %가 아니라 고정값이라 em_from_pct_share 꼬리표는 달지 않는다.
        if c >= 2 and self._e_active:
            for char, char_hits in all_hits.items():
                if char is self:
                    continue
                for hit in char_hits.values():
                    hit.add("em_from_flat", self._C2_ALLY_EM, self, note="C2")

    # ── 파티 버프 4.5: 스탯을 읽지 않는 크로스 버프 ─────────────────────────
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # A1: 반응의 영향을 받은 적의 불·물 내성 -20% (12초).
        # C2가 고유 특성을 강화하면 추가로 -20% (합계 -40%).
        # 내성 감소는 적에게 걸리는 효과라 파티 전원의 히트에 넣는다(에스코피에 A4와 동일).
        if self._a1_active:
            reduction = self._A1_RES_REDUCTION
            if c >= 2:
                reduction += self._C2_A1_EXTRA_RES_REDUCTION
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.add("pyro_res_reduction",  -reduction, self, note="A1")
                    hit.add("hydro_res_reduction", -reduction, self, note="A1")

        # C6 「아홉 번째 하늘의 계약」: 「신비의 수」 1pt당
        #   · 파티 내 캐릭터 불·물 원소 피해 보너스 +1.5%
        #   · 시틀라리가 주는 피해 +2.5%
        # 둘 다 고정값이라 스탯을 읽지 않는다 → 이 단계가 제자리다.
        if self._mystic_count:
            elem_bonus = self._C6_PER_PT_ELEM_DMG * self._mystic_count
            self_bonus = self._C6_PER_PT_SELF_DMG * self._mystic_count
            for char, char_hits in all_hits.items():
                for hit in char_hits.values():
                    hit.add("pyro_dmg_bonus",  elem_bonus, self, note="C6 신비의 수")
                    hit.add("hydro_dmg_bonus", elem_bonus, self, note="C6 신비의 수")
                    if char is self:
                        hit.add("all_dmg_bonus", self_bonus, self, note="C6 신비의 수")

    # ── 파티 버프 5: 최종 스탯을 읽어 스케일하는 버프 (방식 B) ────────────────
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        hits = all_hits[self]

        # 시틀라리의 최종 EM — 값이 아니라 **읽는 함수**로 넘긴다(지연 기여).
        # 이 EM에는 다른 캐릭터가 Phase 5에서 주는 몫(이네파 A4 등)도 들어오므로, 여기서
        # 미리 확정하면 누가 먼저 실행되느냐가 결과를 바꾼다. 함수로 넘기면 이 필드를
        # 읽는 순간 그때까지의 모든 기여가 확정된 뒤 계산된다.
        #
        # em_from_flat이 아니라 elemental_mastery를 **그대로** 읽는 이유:
        # A4와 C1은 원마를 다시 원마나 피해 보너스(%)로 변환하는 효과가 아니라, 원마에
        # 비례한 몫을 피해에 직접 더하는 효과다. 재변환이 없으니 무한 루프도 없고,
        # 시틀라리가 실제로 들고 있는 원마는 출처와 무관하게 전부 재료가 된다
        # (실측: 설탕이 시틀라리에게 원마를 준 쪽이 안 준 쪽보다 피해가 높다).
        # 같은 계열인 C4 「영혼 해골 · 검은별」도 ScalingStat.EM이라 이 필드를 그대로 읽는다.
        source_hit = next(iter(hits.values()))
        em = lambda: source_hit.elemental_mastery

        # A4 「하얀 불나비의 별옷」: 서리운석 폭풍 +EM 90%, 얼음 폭풍 +EM 1200%.
        # 「피해가 EM의 N%만큼 증가」라 계수가 아니라 고정 추가치다 → flat_dmg_bonus로
        # 차원 변환한다 (EM 코어 풀에 되먹이면 순환이며 CyclicBuffError가 잡는다).
        hits["서리운석 폭풍 피해"].add(
            "flat_dmg_bonus", lambda: em() * self._A4_METEOR_STORM_EM, self, note="A4")
        hits["얼음 폭풍 피해"].add(
            "flat_dmg_bonus", lambda: em() * self._A4_ICE_STORM_EM, self, note="A4")

        # C1 「별빛 검」: 시틀라리를 제외한 필드 위 캐릭터가 주는 피해가 EM의 200%만큼 증가.
        # 대상이 「일반 공격, 강공격, 낙하 공격, 원소전투 스킬 또는 원소폭발」 — 다섯 종류
        # 전부라 스킬 타입으로 거를 것이 없다.
        # 스택(기본 10 + 빙결·융해마다 3)은 히트 단가가 아니라 로테이션당 발동 횟수라
        # 단일 히트 표에는 반영하지 않는다 (에스코피에 C2 「냉요리」와 같은 방침).
        if self.constellation >= 1 and self._e_active:
            for char, char_hits in all_hits.items():
                if char is self:      # 「시틀라리를 제외한」
                    continue
                for hit in char_hits.values():
                    hit.add("flat_dmg_bonus",
                            lambda: em() * self._C1_STARLIGHT_BLADE_EM,
                            self, note="C1 별빛 검")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 밤혼 수지 전반 (E 24pt 획득, 하얀 불 8pt/초 소모, A1 16pt·A4 4pt·Q 24/3pt 회복)
    #   과 C4의 원소 에너지 8pt 회복 — 자원 모델이 없어 피해식에 들어갈 항이 없다.
    # · 하얀빛 보호막 흡수량 — 피해가 아니다. 계수 표만 보관한다(_SHIELD_EM/_SHIELD_FLAT).
    # · C1의 열소 소모 45% 감소, C6의 하얀 불 상태 유지 — 지속력이지 피해가 아니다.
