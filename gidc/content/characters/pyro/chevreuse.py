from gidc.core.character import Character
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import Element
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_int


class Chevreuse(Character):
    """슈브르즈 (Chevreuse) | 불 | 장병기 | 4성 | 어센션 스탯: HP%

    일반 공격 : 창으로 최대 4번 공격한다.
    강공격 : 일정 스태미나를 소모해 전방으로 돌진하며 경로상의 적에게 피해를 준다.
    낙하 공격 : 공중에서 땅을 내려찍어 경로상의 적을 공격하고 착지 시 범위 피해를 준다

    E : 신속 차단 사격술
    슈브르즈가 화승총으로 빠르게 견착 사격을 해 불 원소 범위 피해를 준다.
    슈브르즈가 사격한 후 일정 시간 동안 지속적으로 현재 필드 위에 있는 캐릭터의 HP를 회복시킨다.
    회복량은 슈브르즈 HP 최대치의 영향을 받는다.
    홀드 시 다른 방식으로 발동한다.

    홀드
    조준 상태에 진입해 조준점 안에 있는 적 1기를 타깃하고 더 정밀한 차단 사격을 한다.
    만약 슈브르즈가 「초강력 탄두」를 보유하고 있으면 「초강력 탄두」를 발사하는 것으로 전환되고 범위와 피해가 더 큰 불 원소 피해를 준다.
    주변에 있는 파티 내 캐릭터가 과부하 반응을 발동 시 슈브르즈는 「초강력 탄두」를 1개 획득한다. 「초강력 탄두」는 동시에 최대 1개만 보유할 수 있다.

    아르케의 힘: 우시아
    일정 시간마다 슈브르즈의 「신속 차단 사격술」 명중 시, 솟구치는 칼날을 소환해 우시아 성질의 불 원소 피해를 준다.

    Q : 원형 유탄 사격술
    슈브르즈가 화승총으로 적에게 폭파 유탄을 발사해 불 원소 범위 피해를 준다. 폭파 유탄은 명중 후, 수많은 이중 파열탄으로 분열한다.
    이중 파열탄은 짧은 시간이 지난 후 폭발하며 주변의 적에게 불 원소 피해를 준다.

    A1 : 선봉 협동 전술
    파티 내 모든 캐릭터의 원소 타입이 불 원소와 번개 원소이며 불 원소 캐릭터와 번개 원소 캐릭터가 각각 최소 1명씩 있을 경우:
    슈브르즈가 주변에 있는 파티 내 캐릭터에게 「협동 전술」을 부여한다: 캐릭터가 과부하 반응 발동 후,
    해당 반응의 영향을 받은 적의 불 원소와 번개 원소 내성이 40% 감소한다. 지속 시간: 6초.
    파티 내 캐릭터의 원소 타입이 고유 특성의 조건을 만족하지 못할 시, 협동 전술 효과가 사라진다

    A4 : 종대 통솔자
    슈브르즈가 신속 차단 사격술의 「초강력 탄두」를 발사한 후, 슈브르즈의 HP 최대치에 기반해
    HP 최대치의 1000pt당 주변에 있는 파티 내 모든 불 원소와 번개 원소 캐릭터의 공격력이 1% 증가한다.
    해당 방식으로 공격력이 최대 40% 증가한다. 지속 시간: 30초

    C1 : 전선을 굳히는 패기
    「협동 전술」 상태의 현재 필드 위 캐릭터(슈브르즈 자신 제외)가 과부하 반응 발동 시 원소 에너지를 6pt 회복한다.
    해당 효과는 10초마다 최대 1회 발동된다. 고유 특성 「선봉 협동 전술」을 해금해야 한다

    C2 : 유폭을 노리는 저격
    홀드로 신속 차단 사격술을 발동해 명중 시, 명중한 위치 주변에 연쇄 유폭을 2회 일으킨다. 유폭 1회당 슈브르즈 공격력의 120%에 해당하는 불 원소 피해를 준다.
    해당 효과는 10초마다 최대 1회 발동되며 해당 방식으로 주는 피해는 원소전투 스킬 피해로 간주한다

    C3 : 숙련된 재장전 솜씨
    신속 차단 사격술의 스킬 레벨+3

    C4 : 다중 속사의 비결
    원형 유탄 사격술 발동 후, 슈브르즈가 홀드로 발동하는 신속 차단 사격술이 재사용 대기시간에 진입하지 않는다.
    해당 효과는 홀드로 신속 차단 사격술 2회 발동 후 사라진다. 최대 지속 시간: 6초

    C5 : 화력을 증강한 파괴
    원형 유탄 사격술의 스킬 레벨+3

    C6 : 죄악을 끝내는 추격
    신속 차단 사격술의 치유 효과가 12초 동안 지속된 후, 주변에 있는 파티 내 모든 캐릭터의 HP를 슈브르즈 HP 최대치의 10%만큼 1회 회복시킨다.
    파티 내 캐릭터는 「신속 차단 사격술」의 치유를 받은 후 불 원소 피해 보너스와 번개 원소 피해 보너스를 20% 획득한다.
    지속 시간: 8초, 최대 중첩수: 3스택. 스택마다 지속 시간은 독립적으로 계산된다
    """
    name = "슈브르즈"
    weapon_type = WeaponType.POLEARM


    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # 일반 공격 (% ATK, L1~L11) — 장병기라 물리 피해. 3단은 2타로 나뉜다(27.6%+32.5% @L1).
    _NA_HIT1   = [0.5310, 0.5750, 0.6180, 0.6800, 0.7230, 0.7720, 0.8400, 0.9080, 0.9760, 1.0500, 1.1240]
    _NA_HIT2   = [0.4930, 0.5330, 0.5730, 0.6310, 0.6710, 0.7170, 0.7800, 0.8430, 0.9060, 0.9750, 1.0440]
    _NA_HIT3_1 = [0.2760, 0.2990, 0.3210, 0.3540, 0.3760, 0.4020, 0.4370, 0.4730, 0.5080, 0.5460, 0.5850]
    _NA_HIT3_2 = [0.3250, 0.3510, 0.3770, 0.4150, 0.4420, 0.4720, 0.5130, 0.5550, 0.5960, 0.6420, 0.6870]
    _NA_HIT4   = [0.7730, 0.8360, 0.8980, 0.9880, 1.0510, 1.1230, 1.2220, 1.3210, 1.4190, 1.5270, 1.6350]

    # 강공격 (% ATK, L1~L11) — 스태미나 소모 25pt, 전방 돌진 1회
    _CA = [1.2170, 1.3160, 1.4150, 1.5560, 1.6560, 1.7690, 1.9240, 2.0800, 2.2360, 2.4050, 2.5750]

    # 낙하 공격 (% ATK, L1~L11) — 장병기 전용 표(한손검과 공유)
    _PLUNGE      = [0.6393, 0.6914, 0.7434, 0.8177, 0.8698, 0.9292, 1.0110, 1.0928, 1.1746, 1.2638, 1.3530]
    _LOW_PLUNGE  = [1.2784, 1.3824, 1.4865, 1.6351, 1.7392, 1.8581, 2.0216, 2.1851, 2.3486, 2.5270, 2.7054]
    _HIGH_PLUNGE = [1.5968, 1.7267, 1.8567, 2.0424, 2.1723, 2.3209, 2.5251, 2.7293, 2.9336, 3.1564, 3.3792]

    # ── 원소 스킬 「신속 차단 사격술」 (% ATK, L1~L13, C3 적용 시 최대 L13) ──────
    # 치유 지속 12.0초 / 솟구치는 칼날 간격 10.0초 / CD 15.0초.
    # 불 원소라 스커크 「무예 전수」(물·얼음 전용)가 닿지 않는다 → L14 행이 필요 없다.
    _SKILL_PRESS = [       # 짧은 터치 피해 — 빠른 견착 사격
        1.1520, 1.2380, 1.3250, 1.4400, 1.5260,
        1.6130, 1.7280, 1.8430, 1.9580, 2.0740,
        2.1890, 2.3040, 2.4480,
    ]
    _SKILL_HOLD = [        # 홀드 피해 — 조준해 적 1기를 타깃하는 정밀 차단 사격
        1.7280, 1.8580, 1.9870, 2.1600, 2.2900,
        2.4190, 2.5920, 2.7650, 2.9380, 3.1100,
        3.2830, 3.4560, 3.6720,
    ]
    _SKILL_OVERCHARGED = [ # 「초강력 탄두」 피해 — 파티원의 과부하로 얻어 홀드가 전환된다
        2.8240, 3.0360, 3.2480, 3.5300, 3.7420,
        3.9540, 4.2360, 4.5180, 4.8010, 5.0830,
        5.3660, 5.6480, 6.0010,
    ]
    _SKILL_SURGING_BLADE = [  # 솟구치는 칼날 — 아르케 「우시아」, 발동 간격 10초
        0.2880, 0.3100, 0.3310, 0.3600, 0.3820,
        0.4030, 0.4320, 0.4610, 0.4900, 0.5180,
        0.5470, 0.5760, 0.6120,
    ]
    # 지속 치유량 = HP 최대치의 % + 고정값. 치유는 피해가 아니라 SkillHit을 만들지 않는다 —
    # C6의 발동 조건(치유를 받음)을 서술하는 계수라 표만 보관한다.
    _SKILL_HEAL_HP_PCT = [
        0.0267, 0.0287, 0.0307, 0.0333, 0.0353,
        0.0373, 0.0400, 0.0427, 0.0453, 0.0480,
        0.0507, 0.0533, 0.0567,
    ]
    _SKILL_HEAL_FLAT = [
        257, 282, 310, 340, 372,
        407, 443, 482, 522, 565,
        610, 657, 706,
    ]

    # ── 원소 폭발 「원형 유탄 사격술」 (% ATK, L1~L13, C5 적용 시 최대 L13) ──────
    # CD 15.0초, 원소 에너지 60pt.
    _BURST_SHELL = [       # 폭파 유탄 피해 — 명중 후 이중 파열탄으로 분열한다
        3.6820, 3.9580, 4.2340, 4.6020, 4.8780,
        5.1540, 5.5220, 5.8910, 6.2590, 6.6270,
        6.9950, 7.3630, 7.8230,
    ]
    _BURST_FRAGMENT = [    # 이중 파열탄 피해 — 짧은 시간 후 폭발하는 분열탄 1발분
        0.4910, 0.5280, 0.5650, 0.6140, 0.6500,
        0.6870, 0.7360, 0.7850, 0.8340, 0.8840,
        0.9330, 0.9820, 1.0430,
    ]

    # ── 고유 특성 / 명함 계수 (히트 아님 — 버프 훅에서 사용) ────────────────────
    # A1 「선봉 협동 전술」: 과부하 반응의 영향을 받은 적의 불·번개 내성 감소 (6초)
    _A1_RES_REDUCTION = 0.40
    # A4 「종대 통솔자」: HP 최대치 1000pt당 불·번개 캐릭터 공격력 +1%, 최대 +40%
    _A4_HP_UNIT        = 1000.0
    _A4_ATK_PER_UNIT   = 0.01
    _A4_ATK_CAP        = 0.40
    # C2 「유폭을 노리는 저격」: 홀드 명중 시 연쇄 유폭 2회, 1회당 공격력의 120%
    _C2_CHAIN_BLAST_ATK   = 1.20
    _C2_CHAIN_BLAST_COUNT = 2
    # C6 「죄악을 끝내는 추격」: 치유를 받은 캐릭터의 불·번개 피해 보너스 (스택당, 최대 3스택)
    _C6_ELEM_DMG_PER_STACK = 0.20
    _C6_MAX_STACKS         = 3
    _C6_FINAL_HEAL_HP_PCT  = 0.10   # 12초 후 파티 전원 1회 회복 (치유라 히트 아님)
    #endregion

    # ── 고유 특성이 보는 원소 집합 (판정 함수들의 단일 출처) ────────────────────
    # A1은 파티가 이 두 원소로만 이뤄져야 하고, A4는 이 두 원소인 파티원만 버프한다.
    _COORDINATED_ELEMENTS = frozenset({Element.PYRO, Element.ELECTRO})

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 3
    BURST_LEVEL_UP_CONSTELLATION = 5
    NA_TABLES = (_NA_HIT1, _NA_HIT2, _NA_HIT3_1, _NA_HIT3_2, _NA_HIT4,
                 _CA, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_PRESS, _SKILL_HOLD, _SKILL_OVERCHARGED, _SKILL_SURGING_BLADE,
                    _SKILL_HEAL_HP_PCT, _SKILL_HEAL_FLAT,)
    BURST_TABLES = (_BURST_SHELL, _BURST_FRAGMENT,)

    rarity         = 4
    ascension_stat = StatType.HP_PCT

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

        # 장병기 일반/강/낙하 공격은 물리 피해다 (element 미지정 → PHYSICAL).
        for name, coeff in [
            ("1단 공격 피해",    self._NA_HIT1[nl]),
            ("2단 공격 피해",    self._NA_HIT2[nl]),
            ("3단 공격 1타 피해", self._NA_HIT3_1[nl]),
            ("3단 공격 2타 피해", self._NA_HIT3_2[nl]),
            ("4단 공격 피해",    self._NA_HIT4[nl]),
        ]:
            hits.append(SkillHit(name, SkillType.NORMAL_ATK, coeff, ScalingStat.ATK))

        hits.append(SkillHit("강공격 피해", SkillType.CHARGED_ATK, self._CA[nl], ScalingStat.ATK))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK))

        # ── 원소 스킬 ────────────────────────────────────────────────────────
        # 짧은 터치 / 홀드 / 「초강력 탄두」는 서로 배타적인 발동 방식이다(홀드는 탄두를
        # 보유하고 있으면 탄두 발사로 전환된다). 히트는 셋 다 만들어 두고 어느 것이
        # 로테이션에 실리는지는 사용자가 고른다 — 베넷의 누르기/차지와 같은 방침.
        hits.append(SkillHit("짧은 터치 피해",      SkillType.SKILL, self._SKILL_PRESS[sk],
                             ScalingStat.ATK, Element.PYRO))
        hits.append(SkillHit("홀드 피해",           SkillType.SKILL, self._SKILL_HOLD[sk],
                             ScalingStat.ATK, Element.PYRO))
        hits.append(SkillHit("「초강력 탄두」 피해", SkillType.SKILL, self._SKILL_OVERCHARGED[sk],
                             ScalingStat.ATK, Element.PYRO))
        hits.append(SkillHit("솟구치는 칼날 피해",   SkillType.SKILL, self._SKILL_SURGING_BLADE[sk],
                             ScalingStat.ATK, Element.PYRO))

        # ── 원소 폭발 ────────────────────────────────────────────────────────
        hits.append(SkillHit("폭파 유탄 피해",   SkillType.BURST, self._BURST_SHELL[bl],
                             ScalingStat.ATK, Element.PYRO))
        hits.append(SkillHit("이중 파열탄 피해", SkillType.BURST, self._BURST_FRAGMENT[bl],
                             ScalingStat.ATK, Element.PYRO))

        # ── 명함 추가 히트 ────────────────────────────────────────────────────
        # 조건부 히트도 반드시 build_hits에서 만든다 — apply_self_buffs 이후에 만들면
        # 기초 스탯을 채우는 루프가 이미 끝난 뒤라 공격력이 0으로 남는다.
        #
        # C2 「유폭을 노리는 저격」: 홀드 명중 시 연쇄 유폭 2회, 1회당 공격력의 120%.
        # 특성 레벨이 아니라 고정 계수이고 「원소전투 스킬 피해로 간주한다」고 못 박혀 있다.
        # 2회는 히트 단가가 아니라 발동 횟수라 단일 히트 계수에는 넣지 않는다.
        if c >= 2:
            hits.append(SkillHit(
                "C2 연쇄 유폭 피해", SkillType.SKILL,
                self._C2_CHAIN_BLAST_ATK, ScalingStat.ATK, Element.PYRO,
            ))

        return {h.name: h for h in hits}

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        # 슈브르즈에게만 걸리는 버프는 없다 — 고유 특성·명함이 모두 파티 대상이거나
        # (A1/A4/C6) 자원·치유(C1/C4/C6 앞부분)라 여기서 할 일이 없다.
        # A4는 슈브르즈 자신도 불 원소라 수혜자에 포함되지만, 파티 전체를 훑어야
        # 대상을 고를 수 있고 자기 HP를 읽는 스케일 버프라 apply_dependent_buffs에 있다.
        pass

    # ── 「협동 전술」 성립 여부 (A1의 메커니즘) ──────────────────────────────────
    # 「파티 내 모든 캐릭터의 원소 타입이 불·번개이며 불과 번개가 각각 최소 1명씩」.
    # 파티 원소 구성만으로 정해지므로 유저에게 묻지 않는다 — 스커크 「무예 전수」
    # (core/party_state.skill_level_bonus)와 같은 꼴의 판정이다.
    def _coordinated_tactics(self, all_hits: dict["Character", dict[str, SkillHit]]) -> bool:
        elements = {char.element for char in all_hits}
        return (elements <= self._COORDINATED_ELEMENTS
                and self._COORDINATED_ELEMENTS <= elements)

    # ── 과부하 발동 가능 여부 (A4 「초강력 탄두」 획득의 전제) ────────────────────
    # 슈브르즈가 불을 붙이므로 파티에 번개가 있으면 과부하가 성립한다.
    # 성립할 수 없는 파티에서는 「초강력 탄두」를 얻을 수 없으므로 질문 자체를 만들지 않는다.
    def _can_overload(self, all_hits: dict["Character", dict[str, SkillHit]]) -> bool:
        return any(char.element is Element.ELECTRO for char in all_hits)

    # ── 파티 버프 5a ── 유저 입력 수집 (코어 스탯 기여는 없다) ──────────────────
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # A1 「선봉 협동 전술」: 파티 원소 구성으로 「협동 전술」이 성립하는지는 유도하고,
        # 그 상태에서 실제로 과부하를 터뜨렸는지만 묻는다(내성 감소는 반응의 영향을 받은
        # 적에게 6초만 걸린다). 성립하지 않는 파티에는 묻지 않는다.
        self._a1_active = (
            self._coordinated_tactics(all_hits)
            and ask_bool("[슈브르즈 A1] 과부하 반응 발동 (적 불·번개 내성 -40%) 여부")
        )

        # A4 「종대 통솔자」: 「초강력 탄두」를 발사해야 시작된다. 탄두는 파티원의 과부하로만
        # 얻으므로 번개 파티원이 없으면 발사 자체가 불가능하다 → 그때는 묻지 않는다.
        self._a4_active = (
            self._can_overload(all_hits)
            and ask_bool("[슈브르즈 A4] 「초강력 탄두」 발사 (불·번개 캐릭터 공격력 증가) 여부")
        )

        # C6 「죄악을 끝내는 추격」: 치유를 받을 때마다 1스택, 최대 3스택.
        # 스택마다 지속 시간(8초)이 독립적이라 몇 스택이 실려 있는지는 로테이션이 정한다.
        self._c6_stacks = (
            ask_int("[슈브르즈 C6] 치유 후 획득한 불·번개 피해 보너스 스택",
                    0, self._C6_MAX_STACKS)
            if c >= 6 else 0
        )

    # ── 파티 버프 5a.5 ── 스탯을 읽지 않는 크로스 버프 ──────────────────────────
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # A1: 과부하 반응의 영향을 받은 적의 불·번개 내성 -40% (6초).
        # 내성 감소는 적에게 걸리는 효과라 파티 전원의 히트에 넣는다(시틀라리 A1과 동일).
        if self._a1_active:
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.add("pyro_res_reduction",    -self._A1_RES_REDUCTION, self, note="A1")
                    hit.add("electro_res_reduction", -self._A1_RES_REDUCTION, self, note="A1")

        # C6: 「신속 차단 사격술」의 치유를 받은 캐릭터가 불·번개 피해 보너스 +20% (스택당).
        # E의 지속 치유는 「현재 필드 위 캐릭터」만 받지만, C6 자신이 12초 후 파티 전원의 HP를
        # 1회 회복시키므로 파티 내 캐릭터가 모두 치유를 받는다 → 전원에게 건다.
        # 고정값이라 스탯을 읽지 않는다 → 이 단계가 제자리다.
        if self._c6_stacks:
            bonus = self._C6_ELEM_DMG_PER_STACK * self._c6_stacks
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.add("pyro_dmg_bonus",    bonus, self, note="C6")
                    hit.add("electro_dmg_bonus", bonus, self, note="C6")

    # ── 파티 버프 5b ── 최종 스탯을 읽어 스케일하는 버프 (방식 B) ────────────────
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        if not self._a4_active:
            return

        # A4 「종대 통솔자」: 슈브르즈 HP 최대치 1000pt당 파티 내 불·번개 캐릭터 공격력 +1%,
        # 최대 +40%. 슈브르즈 자신도 불 원소라 수혜자에 포함된다.
        #
        # 슈브르즈의 최종 HP는 값이 아니라 **읽는 함수**로 넘긴다(지연 기여). 이 HP에는
        # 다른 캐릭터가 Phase 5에서 주는 몫도 들어오므로, 여기서 미리 확정하면 누가 먼저
        # 실행되느냐가 결과를 바꾼다. 함수로 넘기면 그 필드를 읽는 순간(늦어도 Phase 5.5)
        # 그때까지의 모든 기여가 확정된 뒤 계산된다.
        #
        # 출력이 atk_pct(코어 풀)인데도 정확성 가드에 걸리지 않는 이유: 지연 기여로 바뀐
        # 필드는 순서 무관이 보장돼 가드가 봐준다(party._assert_core_pools_unchanged).
        # HP는 공격력을 재료로 삼지 않으므로 순환도 없다.
        source_hit = next(iter(all_hits[self].values()))

        def atk_bonus() -> float:
            raw = (source_hit.current_hp() / self._A4_HP_UNIT) * self._A4_ATK_PER_UNIT
            return min(raw, self._A4_ATK_CAP)

        for char, char_hits in all_hits.items():
            if char.element not in self._COORDINATED_ELEMENTS:
                continue
            for hit in char_hits.values():
                hit.add("atk_pct", atk_bonus, self, note="A4 종대 통솔자")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · E 지속 치유(HP 최대치의 %+고정)와 C6의 12초 후 파티 전원 1회 회복 — 치유는 피해가
    #   아니다. 계수 표만 보관한다(_SKILL_HEAL_HP_PCT / _SKILL_HEAL_FLAT / _C6_FINAL_HEAL_HP_PCT).
    # · C1 「전선을 굳히는 패기」: 과부하 발동 시 원소 에너지 6pt 회복 — 자원 모델이 없어
    #   피해식에 들어갈 항이 없다.
    # · C4 「다중 속사의 비결」: 홀드 E가 재사용 대기시간에 진입하지 않는다 — 발동 횟수만
    #   바뀌고 히트당 피해는 그대로다.
    # · 「초강력 탄두」 보유 수지(과부하마다 1개 획득, 동시 최대 1개) — 발사 여부만 묻는다.
