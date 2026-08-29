from gidc.core.character import Character
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import CharacterTrait, DmgType, Element, MoonsignLevel, ReactionType
from gidc.enums import StatType
from gidc.core.party_state import moonsign_level
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_choice, ask_int


class Illuga(Character):
    """일루가 (Illuga) | 바위 | 장병기 | 4성 | 어센션 스탯: 원소 마스터리

    일반 공격
    창으로 최대 4번 공격한다.

    강공격
    일정 스태미나를 소모해 전방으로 돌진하며 경로상의 적에게 피해를 준다.

    낙하 공격
    공중에서 땅을 내려찍어 경로상의 적을 공격하고 착지 시 범위 피해를 준다

    E : 새벽을 여는 밤꾀꼬리
    함께 싸우는 전령새 「아에돈」을 소환한다. 짧은 터치 또는 홀드에 따라 각기 다른 효과가 발생한다.

    짧은 터치
    아에돈이 전방의 적을 향해 돌진해 닿은 적에게 바위 원소 피해를 준다.

    홀드
    조준을 진행한다. 아에돈이 조준된 적을 향해 돌진해 닿은 적에게 바위 원소 피해를 준다

    Q : 그림자를 밝히는 등불
    등불을 밝혀 바위 원소 범위 피해를 주고 20초 동안 지속되는 「악몽의 밤꾀꼬리 노래」 효과를 획득한다: 지속 시간 동안 일루가는 「밤꾀꼬리 노래」를 21스택 획득하며, 주변에 있는 파티 내 현재 필드 위 캐릭터의 일반 공격, 강공격, 낙하 공격, 원소전투 스킬 또는 원소폭발이 적에게 바위 원소 피해를 줄 시, 「밤꾀꼬리 노래」를 1스택 소모해 일루가의 원소 마스터리를 기반으로 주는 피해가 증가한다. 해당 피해가 달 결정 반응으로 준 피해일 경우, 주는 피해가 추가로 증가한다.
    상술한 방식으로 준 바위 원소 피해가 동시에 여러 적에게 명중 시, 명중한 적의 수에 따라 「밤꾀꼬리 노래」 스택을 소모한다.

    또한 일루가가 주변에 있는 파티 내 캐릭터가 창조한 바위 원소 창조물이 필드 위에 있는 상태에서 원소폭발을 발동하거나, 「악몽의 밤꾀꼬리 노래」 지속 시간 동안 주변에 있는 파티 내 캐릭터가 바위 원소 창조물을 창조했을 시, 일루가는 필드 위의 바위 원소 창조물 1개당 「밤꾀꼬리의 노래」를 추가로 5스택 획득한다. 매번 원소폭발 발동 후 20초 동안 일루가는 해당 방식으로 「밤꾀꼬리의 노래」를 추가로 최대 15스택 획득할 수 있다.

    「밤꾀꼬리 노래」 스택을 모두 소모하거나 지속 시간이 끝나면 「악몽의 밤꾀꼬리 노래」 효과가 해제된다

    A1 : 등 제작자의 맹약
    원소전투 스킬 새벽을 여는 밤꾀꼬리 또는 원소폭발 그림자를 밝히는 등불 발동 후, 파티 내 주변의 다른 캐릭터가 20초 동안 「등지기의 서약」 효과를 획득한다: 바위 원소 피해의 치명타 확률이 5%, 치명타 피해가 10% 증가한다.

    달빛 징조 · 보름
    「등지기의 서약」 효과의 영향을 받는 캐릭터는 원소 마스터리가 50pt 증가한다

    A4 : 사냥꾼의 황혼
    「밤꾀꼬리 노래」의 효과가 강화된다: 파티 내에 물 원소 또는 바위 원소 캐릭터가 1/2/3명 있을 경우, 「밤꾀꼬리 노래」의 주는 피해 증가 효과가 일루가 원소 마스터리의 7%/14%/24%만큼 추가로 증가한다. 만약 상술한 피해가 달 결정 반응으로 준 피해라면, 일루가 원소 마스터리의 48%/96%/160%만큼 증가한다

    C1 : 경고의 꿩
    일루가가 필드 위에서 바위 원소 관련 반응 발동 후 일루가의 원소 에너지가 12pt 회복되며, 해당 효과는 15초마다 최대 1회 발동된다.

    C2 : 풀을 먹는 사슴
    원소폭발 그림자를 밝히는 등불의 「악몽의 밤꾀꼬리 노래」 효과 지속 시간 동안, 「밤꾀꼬리 노래」를 7스택 소모할 때마다 일루가는 아에돈을 소환해 주변의 적 1기에게 일루가 원소 마스터리의 400%와 방어력의 200%를 기반으로 한 바위 원소 피해를 1회 준다. 해당 피해는 원소폭발 피해로 간주한다

    C3 : 곰의 울음
    원소폭발 그림자를 밝히는 등불의 스킬 레벨+3
    최대 Lv.15까지 상승

    C4 : 태양을 쫓는 늑대
    원소폭발 그림자를 밝히는 등불의 「악몽의 밤꾀꼬리 노래」 효과 지속 시간 동안, 파티 내 주변에 있는 현재 필드 위 캐릭터의 방어력이 200pt 증가한다

    C5 : 바람을 가르는 말
    원소전투 스킬 새벽을 여는 밤꾀꼬리의 스킬 레벨+3
    최대 Lv.15까지 상승

    C6 : 악몽의 밤꾀꼬리
    돌파 특성 등 제작자의 맹약의 「등지기의 서약」 효과가 강화된다: 적에게 주는 바위 원소 피해의 치명타 확률이 10%, 치명타 피해가 30% 증가한다.

    달빛 징조 · 보름
    「등지기의 서약」 효과의 영향을 받는 캐릭터의 원소 마스터리가 80pt 증가한다.
    돌파 특성 등 제작자의 맹약을 해금해야 한다

    달빛 징조의 축복 · 상록수
    일루가가 파티에 있을 경우 파티의 달빛 징조가 1레벨 상승한다
    """
    name = "일루가"
    weapon_type = WeaponType.POLEARM
    # 노드크라이 출신 — 파티 달빛 징조에 기여한다.
    # 「상록수」의 "파티의 달빛 징조가 1레벨 상승"은 이 특성이 곧 그 상승이다 —
    # party_state의 인원수 임계값 표가 이미 그렇게 센다(린네아·자백·이네파와 같은 문구).
    #
    # 달결정 **전환자는 아니다** — 일루가는 달 결정 반응을 일으키는 쪽이 아니라 그 피해를
    # 키우는 쪽이다(Q·A4). 전환은 콜롬비나·린네아·자백이 맡는다.
    innate_traits = frozenset({CharacterTrait.MOONSIGN})

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # ── 일반공격 (L1~L11) ──
    # 일반 공격 — 창 4단, 물리
    _NA_HIT1 = [0.4737, 0.5122, 0.5508, 0.6058, 0.6444, 0.6885, 0.7490, 0.8096, 0.8702, 0.9363, 1.0024]
    _NA_HIT2 = [0.4853, 0.5248, 0.5643, 0.6207, 0.6602, 0.7053, 0.7674, 0.8294, 0.8915, 0.9592, 1.0269]
    # 3단은 같은 계수로 2타 — 히트는 build_hits에서 두 개 세운다.
    _NA_HIT3 = [0.3143, 0.3399, 0.3655, 0.4020, 0.4276, 0.4569, 0.4971, 0.5373, 0.5775, 0.6213, 0.6652]
    _NA_HIT4 = [0.7628, 0.8249, 0.8870, 0.9757, 1.0377, 1.1087, 1.2063, 1.3038, 1.4014, 1.5078, 1.6143]
    _CA = [1.1103, 1.2006, 1.2910, 1.4201, 1.5105, 1.6138, 1.7558, 1.8978, 2.0398, 2.1947, 2.3496]
    _PLUNGE = [0.6393, 0.6914, 0.7434, 0.8177, 0.8698, 0.9292, 1.0110, 1.0928, 1.1746, 1.2638, 1.3530]
    _LOW_PLUNGE = [1.2784, 1.3824, 1.4865, 1.6351, 1.7392, 1.8581, 2.0216, 2.1851, 2.3486, 2.5270, 2.7054]
    _HIGH_PLUNGE = [1.5968, 1.7267, 1.8567, 2.0424, 2.1723, 2.3209, 2.5251, 2.7293, 2.9336, 3.1564, 3.3792]

    # ── 원소스킬 (L1~L13) ──
    # 짧은 터치 — 아에돈이 전방으로 돌진
    _SKILL_TAP_EM = [
         4.8256,  5.1875,  5.5494,  6.0320,  6.3939,
         6.7558,  7.2384,  7.7210,  8.2035,  8.6861,
         9.1686,  9.6512, 10.2544,
    ]
    _SKILL_TAP_DEF = [
        2.4128, 2.5938, 2.7747, 3.0160, 3.1970,
        3.3779, 3.6192, 3.8605, 4.1018, 4.3430,
        4.5843, 4.8256, 5.1272,
    ]
    # 홀드 — 조준한 적을 향해 돌진. 짧은 터치와 배타적이라 히트는 둘 다 세운다.
    _SKILL_HOLD_EM = [
         6.0320,  6.4844,  6.9368,  7.5400,  7.9924,
         8.4448,  9.0480,  9.6512, 10.2544, 10.8576,
        11.4608, 12.0640, 12.8180,
    ]
    _SKILL_HOLD_DEF = [
        3.0160, 3.2422, 3.4684, 3.7700, 3.9962,
        4.2224, 4.5240, 4.8256, 5.1272, 5.4288,
        5.7304, 6.0320, 6.4090,
    ]

    # ── 원소폭발 (L1~L13) ──
    # 등불 발동 순간의 범위 피해
    _BURST_EM = [
          8.272,  8.8924,  9.5128,  10.340, 10.9604,
        11.5808,  12.408, 13.2352, 14.0624, 14.8896,
        15.7168,  16.544,  17.578,
    ]
    _BURST_DEF = [
         4.136, 4.4462, 4.7564,  5.170, 5.4802,
        5.7904,  6.204, 6.6176, 7.0312, 7.4448,
        7.8584,  8.272,  8.789,
    ]
    # 바위 원소 피해일 때
    _BURST_SONG_GEO = [
         0.336, 0.3612, 0.3864,  0.420, 0.4452,
        0.4704,  0.504, 0.5376, 0.5712, 0.6048,
        0.6384,  0.672,  0.714,
    ]
    # 그 피해가 달 결정 반응 피해일 때
    _BURST_SONG_LUNAR = [
        2.2592, 2.4286, 2.5981, 2.8240, 2.9934,
        3.1629, 3.3888, 3.6147, 3.8406, 4.0666,
        4.2925, 4.5184, 4.8008,
    ]

    # ── 상수 (레벨로 스케일하지 않는 값) ──
    _Q_SONG_STACKS        = 21     # Q 「밤꾀꼬리 노래」 스택 수지 — 자원 모델이 없어 피해식에는 안 들어간다.
    _Q_EXTRA_PER_CREATION = 5      # 바위 원소 창조물 1개당
    _Q_EXTRA_STACKS_MAX   = 15
    _A1_GEO_CRIT_RATE     = 0.05   # A1 등지기의 서약 — 파티 내 **다른** 캐릭터의 바위 원소 피해 치명타
    _A1_GEO_CRIT_DMG      = 0.10
    _A1_FULLMOON_EM       = 50
    _C2_STACKS_PER_AEDON  = 7      # C2 풀을 먹는 사슴 — 7스택 소모마다 아에돈 소환 (원소폭발 피해로 간주)
    _C2_AEDON_EM_RATIO    = 4.00
    _C2_AEDON_DEF_RATIO   = 2.00
    _C4_DEF_FLAT          = 200    # C4 태양을 쫓는 늑대 — Q 지속 중 현재 필드 위 캐릭터의 방어력 증가 (실수치)
    _C6_GEO_CRIT_RATE     = 0.10   # C6 악몽의 밤꾀꼬리 — 「등지기의 서약」 강화값 (A1 값을 **대체**한다)
    _C6_GEO_CRIT_DMG      = 0.30
    _C6_FULLMOON_EM       = 80

    # A4 사냥꾼의 황혼 — 파티 내 물/바위 캐릭터 수(1/2/3명)로 인덱싱한다.
    # 특성 레벨 표가 아니므로 *_TABLES에 넣지 않고 NON_TALENT_TABLES로 선언해
    # 점검 도구가 「등록을 빠뜨린 것」과 구별하게 한다.
    _A4_GEO_EM   = (0.07, 0.14, 0.24)   # 바위 원소 피해일 때
    _A4_LUNAR_EM = (0.48, 0.96, 1.60)   # 그 피해가 달 결정 반응 피해일 때
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 5
    BURST_LEVEL_UP_CONSTELLATION = 3
    NON_TALENT_TABLES = (_A4_GEO_EM, _A4_LUNAR_EM,)
    NA_TABLES = (_NA_HIT1, _NA_HIT2, _NA_HIT3, _NA_HIT4, _CA, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_TAP_EM, _SKILL_TAP_DEF, _SKILL_HOLD_EM, _SKILL_HOLD_DEF,)
    BURST_TABLES = (_BURST_EM, _BURST_DEF, _BURST_SONG_GEO, _BURST_SONG_LUNAR,)

    rarity         = 4
    ascension_stat = StatType.ELEMENTAL_MASTERY

    @property
    def element(self) -> Element: return Element.GEO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    @staticmethod
    def _em_def_stat(em_ratio: float, def_ratio: float):
        """「원소 마스터리의 X% + 방어력의 Y%」를 한 히트의 스탯 값으로 접는다.

        SkillHit은 스케일 스탯을 하나만 갖지만 stat_fn(임의 함수)을 받는다. 계수를
        스탯 쪽에 담고 coeff=1.0으로 두면 공식의 `coeff × stat` 자리가 그대로 성립한다.
        히트를 둘로 쪼개지 않는 이유는 치명타가 히트 단위로 굴러가기 때문이다 —
        쪼개면 한쪽만 크리가 터지는, 게임에 없는 상태가 화면에 생긴다.
        """
        return lambda h: h.elemental_mastery * em_ratio + h.current_def() * def_ratio

    def build_hits(self) -> dict[str, SkillHit]:
        nl = self._na_index()
        sk = self._skill_index()   # C5: 레벨 +3
        bl = self._burst_index()   # C3: 레벨 +3

        hits: list[SkillHit] = []

        # ── 일반 공격 (물리, 공격력) ─────────────────────────────────────────
        hits.append(SkillHit("1단 공격 피해", SkillType.NORMAL_ATK, self._NA_HIT1[nl], ScalingStat.ATK))
        hits.append(SkillHit("2단 공격 피해", SkillType.NORMAL_ATK, self._NA_HIT2[nl], ScalingStat.ATK))
        # 3단은 같은 계수로 2타
        for i in (1, 2):
            hits.append(SkillHit(f"3단 공격 피해 {i}타", SkillType.NORMAL_ATK, self._NA_HIT3[nl], ScalingStat.ATK))
        hits.append(SkillHit("4단 공격 피해", SkillType.NORMAL_ATK, self._NA_HIT4[nl], ScalingStat.ATK))
        hits.append(SkillHit("강공격 피해", SkillType.CHARGED_ATK, self._CA[nl], ScalingStat.ATK))

        hits.append(SkillHit("낙하 기간 피해",      SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK))

        # ── E 새벽을 여는 밤꾀꼬리 — 짧은 터치와 홀드는 배타적이라 둘 다 세운다 ──
        # 계수는 스탯 쪽(stat_fn)에 담기므로 coeff는 1.0이다.
        hits.append(SkillHit(
            "원소 스킬 짧은 터치 피해", SkillType.SKILL, 1.0, ScalingStat.DEF, Element.GEO,
            stat_fn=self._em_def_stat(self._SKILL_TAP_EM[sk], self._SKILL_TAP_DEF[sk]),
        ))
        hits.append(SkillHit(
            "원소 스킬 홀드 피해", SkillType.SKILL, 1.0, ScalingStat.DEF, Element.GEO,
            stat_fn=self._em_def_stat(self._SKILL_HOLD_EM[sk], self._SKILL_HOLD_DEF[sk]),
        ))

        # ── Q 그림자를 밝히는 등불 ───────────────────────────────────────────
        hits.append(SkillHit(
            "원소 폭발 피해", SkillType.BURST, 1.0, ScalingStat.DEF, Element.GEO,
            stat_fn=self._em_def_stat(self._BURST_EM[bl], self._BURST_DEF[bl]),
        ))

        # C2 : 「밤꾀꼬리 노래」 7스택 소모마다 아에돈이 1회 때린다.
        # 「해당 피해는 원소폭발 피해로 간주」되므로 SkillType.BURST다.
        # 계수가 특성 레벨로 스케일하지 않는 상수라 표가 아니다.
        if self.constellation >= 2:
            hits.append(SkillHit(
                "C2 아에돈 피해", SkillType.BURST, 1.0, ScalingStat.DEF, Element.GEO,
                stat_fn=self._em_def_stat(self._C2_AEDON_EM_RATIO, self._C2_AEDON_DEF_RATIO),
            ))

        return {h.name: h for h in hits}

    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        # 일루가의 킷에는 「자기만 받는」 효과가 없다 — A1은 **다른** 캐릭터에게,
        # Q 「밤꾀꼬리 노래」와 C4는 현재 필드 위 캐릭터에게 간다(그가 일루가일 수는 있다).
        # 대상을 고르려면 파티를 봐야 하므로 유저 입력도 Phase 4에서 모은다.
        pass

    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # ── 유저 입력 ────────────────────────────────────────────────────────
        # Q 「악몽의 밤꾀꼬리 노래」 지속 여부 — Q 피해 증가와 C4가 함께 쓴다.
        self._q_active = ask_bool("[일루가 Q] 「악몽의 밤꾀꼬리 노래」 지속 중인지 여부")
        # 그 효과가 붙는 대상. 「현재 필드 위 캐릭터」는 1명만 고르게 한다.
        self._on_field = self._ask_on_field_member(all_hits)
        # A1 「등지기의 서약」 — E 또는 Q 발동 후 20초. 로테이션이 정한다.
        self._oath = ask_bool("[일루가 A1] 「등지기의 서약」 효과 보유 여부")

        # ── A4 사냥꾼의 황혼 : 파티의 물/바위 인원수 ─────────────────────────
        # 파티 구성만으로 정해지므로 묻지 않고 센다. 자백 A4와 달리 원문에 「다른」이 없어
        # **일루가 자신도 센다**(사용자 확인) — 바위라 솔로에서도 1단계가 켜진다.
        # Phase 5의 Q 피해 증가가 이 값을 읽으므로 여기서 확정해 둔다.
        self._a4_tier = min(
            3, sum(1 for char in all_hits
                   if char.element in (Element.GEO, Element.HYDRO))
        )

        # ── C4 태양을 쫓는 늑대 : Q 지속 중 필드 위 캐릭터의 방어력 +200 ──────
        # 실수치 가산이라 def_flat이다(다른 스탯의 %에서 파생된 지분이 아니다).
        if c >= 4 and self._q_active:
            for hit in all_hits[self._on_field].values():
                hit.add("def_flat", self._C4_DEF_FLAT, self, note="C4 태양을 쫓는 늑대")

        # ── A1 보름 : 「등지기의 서약」 대상의 원소 마스터리 증가 ──────────────
        # 고정 수치로 부여되는 EM이라 em_from_flat이다. C6이 값을 **대체**한다.
        # 코어 풀에 넣는 고정값이라 Phase 4의 계약에 맞는다.
        if self._oath and moonsign_level(all_hits) is MoonsignLevel.FULL:
            em = self._C6_FULLMOON_EM if c >= 6 else self._A1_FULLMOON_EM
            for char in self._oath_targets(all_hits):
                for hit in all_hits[char].values():
                    hit.add("em_from_flat", em, self, note="A1 보름 등지기의 서약")

    def _ask_on_field_member(self, all_hits):
        """Q·C4가 함께 쓰는 「현재 필드 위 캐릭터」. 파티원이 1명뿐이면 묻지 않는다."""
        members = list(all_hits.keys())
        if len(members) == 1:
            return members[0]
        options = [
            f"{char.name} ({char.element.value})" + (" ← 일루가" if char is self else "")
            for char in members
        ]
        return members[ask_choice("[일루가 Q/C4] 현재 필드 위 캐릭터", options)]

    def _oath_targets(self, all_hits):
        """「등지기의 서약」을 받는 파티원 — 원문이 「파티 내 주변의 **다른** 캐릭터」다.
        일루가 자신은 빠진다. A4의 인원수 판정(자신 포함)과 갈리는 자리다."""
        return [char for char in all_hits if char is not self]

    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # ── A1 등지기의 서약 : 다른 캐릭터의 **바위 원소 피해** 치명타 증가 ───
        # 원소를 가리는 효과라 바위 히트에만 건다 — 히트 전역 crit에 넣으면 그 캐릭터의
        # 물리·타 원소 피해까지 오염된다.
        # C6은 「강화된다」라 값을 **대체**한다(5%/10% → 10%/30%). 더하지 않는다.
        if not self._oath:
            return
        c = self.constellation
        crit_rate = self._C6_GEO_CRIT_RATE if c >= 6 else self._A1_GEO_CRIT_RATE
        crit_dmg  = self._C6_GEO_CRIT_DMG  if c >= 6 else self._A1_GEO_CRIT_DMG

        for char in self._oath_targets(all_hits):
            for hit in all_hits[char].values():
                if hit.element is not Element.GEO:
                    continue
                hit.add("crit_rate", crit_rate, self, note="A1 등지기의 서약")
                hit.add("crit_dmg",  crit_dmg,  self, note="A1 등지기의 서약")

    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # ── Q 「밤꾀꼬리 노래」 : 필드 위 캐릭터의 바위 원소 피해 증가 ──────────
        # 「일루가의 원소 마스터리를 기반으로 주는 피해가 증가한다」 → 피해에 그대로
        # 더하는 고정값이라 flat_dmg_bonus다.
        #
        # 재료는 **합계 elemental_mastery**다 — EM을 다시 %로 변환하는 버프가 아니라
        # 피해 차원으로 내보내는 쪽이므로 유래를 가리지 않는다(실측 확정).
        #
        # 일루가의 EM을 **읽는 함수**로 넘긴다(지연 기여). 어센션·성유물 말고도 다른
        # 캐릭터가 같은 단계에서 EM을 올릴 수 있어, 지금 확정하면 순서가 결과를 바꾼다.
        if not self._q_active:
            return

        source_hit = next(iter(all_hits[self].values()))
        bl = self._burst_index()
        tier = self._a4_tier

        # 「대체」다 — 달 결정 반응 피해는 자기 행만 쓰고 바위 행을 겹쳐 받지 않는다
        # (사용자 확인). A4의 추가분도 같은 방식으로 행마다 따로 붙는다.
        geo_ratio   = self._BURST_SONG_GEO[bl]
        lunar_ratio = self._BURST_SONG_LUNAR[bl]
        if tier:
            geo_ratio   += self._A4_GEO_EM[tier - 1]
            lunar_ratio += self._A4_LUNAR_EM[tier - 1]

        for hit in all_hits[self._on_field].values():
            if not self._song_applies(hit):
                continue
            ratio = lunar_ratio if self._is_lunar_crystallize(hit) else geo_ratio
            hit.add("flat_dmg_bonus",
                    lambda r=ratio: source_hit.elemental_mastery * r,
                    self, note="Q 밤꾀꼬리 노래")

    # 「일반 공격, 강공격, 낙하 공격, 원소전투 스킬 또는 원소폭발」 — 무기 추가 타격
    # (SkillType.WEAPON)만 빠진다. 원문이 나열한 다섯 종류를 그대로 적어 둔다.
    _SONG_SKILL_TYPES = frozenset({
        SkillType.NORMAL_ATK, SkillType.CHARGED_ATK, SkillType.PLUNGING,
        SkillType.SKILL, SkillType.BURST,
    })

    @classmethod
    def _song_applies(cls, hit: SkillHit) -> bool:
        """이 히트가 「밤꾀꼬리 노래」 스택을 소모하는 바위 원소 피해인가."""
        return hit.element is Element.GEO and hit.skill_type in cls._SONG_SKILL_TYPES

    @staticmethod
    def _is_lunar_crystallize(hit: SkillHit) -> bool:
        """달 결정 **직접 피해** 히트인가 — 달결정 행이 붙을 수 있는 자리.

        내재 반응과 dmg_type을 함께 본다. 파티 단위 달결정 **반응 피해**는 SkillHit이
        아니라 별도 피해 인스턴스이고 flat_dmg_bonus를 읽지 않는다
        (damage._calc_lunar_reaction) — 맨 아래 「의도적 미구현」 참고.
        """
        return (hit.reaction_type is ReactionType.LUNAR_CRYSTALLIZE
                and hit.dmg_type is DmgType.LUNAR_DIRECT)

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 「밤꾀꼬리 노래」 스택 수지 전반 — 자원 모델이 없다. 21스택·창조물 1개당 5스택·
    #   추가 최대 15스택(_Q_SONG_STACKS / _Q_EXTRA_PER_CREATION / _Q_EXTRA_STACKS_MAX)과
    #   「여러 적 명중 시 적 수만큼 소모」는 전부 효과가 몇 번 붙느냐를 정할 뿐 히트 단가가
    #   아니다. 화면을 읽는 쪽이 몇 히트를 합산할지 고른다.
    # · 같은 이유로 C2 아에돈의 발동 횟수(7스택마다) — 히트는 세워 두고 횟수는 안 센다.
    # · C1 「경고의 꿩」 — 원소 에너지 회복. 로테이션 빈도지 히트 단가가 아니다.
    # · Q의 「바위 원소 창조물」 판정 — 창조물은 이 엔진의 모델에 없다. 스택 수지에만
    #   쓰이므로 위 항목에 함께 묻힌다.
    # · Q·A4의 피해 증가가 파티 단위 달 결정 **반응 피해 인스턴스**에 붙는 몫 —
    #   damage._calc_lunar_reaction에 고정 피해 가산 자리가 없다(캐리어의 flat_dmg_bonus를
    #   일부러 읽지 않는다). 달결정 **직접 피해 히트**에만 걸었다. 린네아 C1과 같은 자리다.
