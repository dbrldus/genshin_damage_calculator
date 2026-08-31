from gidc.core.character import Character
from gidc.core.party_state import moonsign_level
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import CharacterTrait, DmgType, Element, MoonsignLevel, ReactionType
from gidc.enums import StatType
from gidc.enums import WeaponType


class Flins(Character):
    """플린스 (Flins) | 번개 | 장병기 | 5성 | 어센션 스탯: 치명타 피해

    일반 공격
    창으로 최대 5번 공격한다.

    강공격
    일정 스태미나를 소모해 전방을 향해 창을 던져 공격한다.

    낙하 공격
    공중에서 땅을 내려찍어 경로상의 적을 공격하고 착지 시 범위 피해를 준다.

    E : 고대 율법 · 등불의 신비
    플린스가 등불 속 고대의 힘을 소환해 푸른불 모드로 전환한다. 해당 모드는 아래의 특성을 가진다:
    · 플린스의 일반 공격과 강공격이 다른 원소 부여 효과로 대체될 수 없는 번개 원소 피해로 전환되고 낙하 공격을 할 수 없게 된다.
    · 플린스의 경직 저항력이 증가한다.
    · 원소전투 스킬 고대 율법 · 등불의 신비가 특수 원소전투 스킬 북국의 장창으로 대체된다.

    북국의 장창
    플린스가 전방에 장창을 소환해 번개 원소 범위 피해를 주고, 그 후 6초 동안 플린스의 원소폭발 고대 예법 · 밤의 손님이 특수 원소폭발 낙뢰 교향곡으로 대체된다.
    북국의 장창의 기본 재사용 대기시간은 6초이며, 해당 재사용 대기시간은 다른 효과의 영향을 받지 않는다

    Q : 고대 예법 · 밤의 손님
    플린스가 등불 속 진정한 힘을 해방해 번개 원소 범위 피해를 주고 짧은 시간 후, 2회의 중간 타격과 1회의 마지막 타격으로 달 감전 반응 피해로 간주하는 번개 원소 범위 피해를 중간 단계 공격으로 2회, 마무리 단계 공격으로 1회 준다.
    달빛 징조 · 보름: 스킬이 강화된다: 주변에 번개구름이 존재할 경우, 추가로 달 감전 반응 피해로 간주하는 번개 원소 범위 피해를 중간 단계 공격으로 2회 준다.

    특수 원소전투 스킬 북국의 장창 발동 후 6초 동안, 플린스의 원소폭발 고대 예법 · 밤의 손님이 특수 원소폭발 낙뢰 교향곡으로 전환된다.

    낙뢰 교향곡
    원소 에너지를 덜 소모하는 특수 원소폭발을 발동할 수 있다. 플린스가 달 감전 반응 피해로 간주하는 번개 원소 범위 피해를 1회 준다.
    달빛 징조 · 보름: 스킬이 강화된다: 주변에 번개 구름이 존재할 경우 달 감전 반응 피해로 간주하는 번개 원소 범위 피해를 추가로 1회 준다

    A1 : 한겨울 교향곡
    파티의 달빛 징조에 따라 플린스가 상응하는 강화 효과를 획득한다.

    달빛 징조 · 보름: 플린스가 발동한 달 감전 반응으로 주는 피해가 20% 증가한다

    A4 : 푸른불의 속삭임
    플린스의 원소 마스터리가 플린스 공격력의 8%만큼 증가한다. 해당 방식으로 플린스의 원소 마스터리는 최대 160pt 증가한다

    C1 : 걷힌 눈의 장막
    특수 원소전투 스킬 북국의 장창의 기본 재사용 대기시간이 4초로 감소한다.
    또한 파티 내 캐릭터가 달 감전 반응 발동 시, 플린스가 원소 에너지를 8pt 회복한다. 해당 효과는 5.5초마다 최대 1회 발동한다

    C2 : 넘어선 악령의 벽
    특수 원소전투 스킬 북국의 장창 발동 후 6초 동안 플린스의 다음 일반 공격이 적에게 명중 시, 추가로 플린스 공격력의 50%에 해당하는 번개 원소 범위 피해를 준다. 해당 피해는 달 감전 반응 피해로 간주한다.
    달빛 징조 · 보름: 필드 위에 있는 플린스가 번개 원소 타입 공격으로 적 명중 후, 해당 적의 번개 원소 내성이 25% 감소한다. 지속 시간: 7초

    C3 : 습지를 방문한 손님
    원소폭발 고대 예법 · 밤의 손님의 스킬 레벨+3
    최대 Lv.15까지 상승

    C4 : 밤에 포효하는 산
    플린스의 공격력이 20% 증가한다.
    돌파 특성 「푸른불의 속삭임」이 강화된다: 플린스의 원소 마스터리가 플린스 공격력의 10%만큼 증가한다. 해당 방식을 통해 플린스의 원소 마스터리는 최대 220pt까지 증가한다

    C5 : 속세를 떠난 그림자
    원소전투 스킬 고대 율법 · 등불의 신비의 스킬 레벨+3
    최대 Lv.15까지 상승

    C6 : 노래와 망자의 춤
    플린스가 적에게 주는 달 감전 반응 피해가 35% 승격한다.
    달빛 징조 · 보름: 주변에 있는 파티 내 모든 캐릭터가 주는 달 감전 반응 피해가 10% 승격한다

    달빛 징조의 축복 · 구시대의 비밀
    파티 내 캐릭터가 감전 반응 발동 시, 달 감전 반응 발동으로 전환되며, 플린스의 공격력에 기반해 달 감전 반응 기본 피해가 증가한다: 공격력 100pt마다 기본 피해가 0.7% 증가하며, 해당 방식으로 피해는 최대 14% 증가한다.

    플린스가 파티에 있을 경우 파티의 달빛 징조가 1레벨 상승한다
    """
    name = "플린스"
    weapon_type = WeaponType.POLEARM
    innate_traits = frozenset({CharacterTrait.MOONSIGN, CharacterTrait.LUNAR_CHARGED_CONVERTER})

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # ── 일반공격 (L1~L11) ──
    _NA1 = [0.447, 0.484,  0.52, 0.572, 0.608,  0.65, 0.707, 0.765, 0.822, 0.884, 0.947]
    _NA2 = [0.451, 0.488, 0.525, 0.577, 0.614, 0.656, 0.714, 0.772, 0.829, 0.892, 0.955]
    _NA3 = [0.559, 0.605,  0.65, 0.715, 0.761, 0.813, 0.884, 0.956, 1.027, 1.105, 1.183]
    # 4단은 같은 계수로 2타 — 히트는 build_hits에서 두 개 세운다.
    _NA4 = [ 0.32, 0.346, 0.373,  0.41, 0.436, 0.466, 0.507, 0.548, 0.589, 0.633, 0.678]
    _NA5 = [0.768,  0.83, 0.893, 0.982, 1.045, 1.116, 1.214, 1.313, 1.411, 1.518, 1.625]
    _CA = [ 1.03, 1.114, 1.198, 1.318, 1.402, 1.498, 1.629, 1.761, 1.893, 2.037,  2.18]
    # 대검을 제외한 무기 공통 낙하 공격 표 (자료의 3자리 표기 대신 정밀값을 쓴다)
    _PLUNGE = [0.6393, 0.6914, 0.7434, 0.8177, 0.8698, 0.9292, 1.0110, 1.0928, 1.1746, 1.2638, 1.3530]
    _LOW_PLUNGE = [1.2784, 1.3824, 1.4865, 1.6351, 1.7392, 1.8581, 2.0216, 2.1851, 2.3486, 2.5270, 2.7054]
    _HIGH_PLUNGE = [1.5968, 1.7267, 1.8567, 2.0424, 2.1723, 2.3209, 2.5251, 2.7293, 2.9336, 3.1564, 3.3792]

    # ── 원소스킬 (L1~L13) ──
    _BLUE_NA1 = [0.582, 0.626,  0.67, 0.728, 0.772, 0.815, 0.874, 0.932,  0.99, 1.048, 1.107, 1.165, 1.238]
    _BLUE_NA2 = [0.588, 0.632, 0.676, 0.735, 0.779, 0.823, 0.882, 0.941,  1.00, 1.058, 1.117, 1.176, 1.249]
    _BLUE_NA3 = [0.728, 0.783, 0.837,  0.91, 0.965,  1.02, 1.092, 1.165, 1.238, 1.311, 1.384, 1.457, 1.548]
    # 4단은 같은 계수로 2타 — 히트는 build_hits에서 두 개 세운다.
    _BLUE_NA4 = [0.417, 0.449,  0.48, 0.522, 0.553, 0.584, 0.626, 0.668, 0.709, 0.751, 0.793, 0.835, 0.887]
    _BLUE_NA5 = [ 1.00, 1.075,  1.15,  1.25, 1.325,  1.40,  1.50,  1.60,  1.70,  1.80,  1.90,  2.00, 2.125]
    _BLUE_CA = [ 1.15, 1.236, 1.322, 1.437, 1.523, 1.609, 1.724, 1.839, 1.954, 2.069, 2.184, 2.299, 2.443]
    # 특수 원소전투 스킬 「북국의 장창」 — 푸른불 모드에서 E를 대체한다. CD 6초(C1: 4초).
    _NORTHERN_LANCE_DMG = [
        1.784, 1.918, 2.052,  2.23, 2.364,
        2.498, 2.676, 2.854, 3.033, 3.211,
         3.39, 3.568, 3.791,
    ]

    # ── 원소폭발 (L1~L13) ──
    _BURST_INITIAL_DMG = [
        2.598, 2.793, 2.988, 3.248, 3.443,
        3.638, 3.898, 4.157, 4.417, 4.677,
        4.937, 5.197, 5.522,
    ]
    # 중간 단계 — 기본 2회, 달빛 징조 · 보름 + 주변 번개구름이면 2회 더
    _BURST_MID_LUNAR_DMG = [
        0.162, 0.175, 0.187, 0.203, 0.215,
        0.227, 0.244,  0.26, 0.276, 0.292,
        0.309, 0.325, 0.345,
    ]
    # 마무리 단계 — 1회
    _BURST_FINAL_LUNAR_DMG = [
        1.169, 1.257, 1.345, 1.462, 1.549,
        1.637, 1.754, 1.871, 1.988, 2.105,
        2.222, 2.339, 2.485,
    ]
    # 특수 원소폭발 「낙뢰 교향곡」 — 북국의 장창 발동 후 6초 동안 Q를 대체한다. 1회.
    _SYMPHONY_LUNAR_DMG = [
        0.715, 0.768, 0.822, 0.893, 0.947,
         1.00, 1.072, 1.143, 1.215, 1.286,
        1.358, 1.429, 1.518,
    ]
    # 낙뢰 교향곡 · 달빛 징조 · 보름 + 주변 번개구름이면 추가 1회
    _SYMPHONY_EXTRA_LUNAR_DMG = [
        1.039, 1.117, 1.195, 1.299, 1.377,
        1.455, 1.559, 1.663, 1.767, 1.871,
        1.975, 2.079, 2.209,
    ]

    # ── 상수 (레벨로 스케일하지 않는 값) ──
    _BURST_MID_HITS                    = 2       # 중간 단계 달 감전 타격 횟수 — 기본 2회, 보름 + 번개구름이면 2회 추가
    _BURST_MID_FULLMOON_HITS           = 2
    _A1_FULLMOON_LUNAR_CHARGED_BONUS   = 0.20    # A1 한겨울 교향곡 (보름) — 플린스가 발동한 달 감전 반응 피해 증가
    _A4_EM_FROM_ATK                    = 0.08    # A4 푸른불의 속삭임 — 플린스 공격력의 8%만큼 원소 마스터리 증가, 최대 160pt
    _A4_EM_CAP                         = 160
    _C2_EXTRA_ATK_RATIO                = 0.50    # 다음 일반 공격 명중 시 공격력 50% 추가타 (달 감전 피해로 간주)
    _C2_FULLMOON_ELECTRO_RES_REDUCTION = 0.25    # 보름 — 번개 원소 공격으로 명중한 적의 번개 원소 내성 감소 (7초). **양수로 적고 쓸 때 부호를 뒤집는다**
    _C4_ATK_PCT                        = 0.20    # C4 밤에 포효하는 산 — 공격력 +20%, A4 강화(10% · 최대 220pt)
    _C4_EM_FROM_ATK                    = 0.10
    _C4_EM_CAP                         = 220
    _C6_LUNAR_CHARGED_ELEVATION        = 0.35    # 플린스 자신
    _C6_FULLMOON_PARTY_LUNAR_ELEVATION = 0.10    # 보름 — 주변 파티 전원
    _MOONSIGN_BASE_DMG_PER_100_ATK     = 0.007   # 달빛 징조의 축복 · 구시대의 비밀 — 공격력 100pt마다 달감전 '기본 피해' +0.7%, 최대 +14%
    _MOONSIGN_BASE_DMG_CAP             = 0.14
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 5
    BURST_LEVEL_UP_CONSTELLATION = 3
    NA_TABLES = (_NA1, _NA2, _NA3, _NA4, _NA5, _CA, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_BLUE_NA1, _BLUE_NA2, _BLUE_NA3, _BLUE_NA4, _BLUE_NA5, _BLUE_CA, _NORTHERN_LANCE_DMG,)
    BURST_TABLES = (_BURST_INITIAL_DMG, _BURST_MID_LUNAR_DMG, _BURST_FINAL_LUNAR_DMG, _SYMPHONY_LUNAR_DMG, _SYMPHONY_EXTRA_LUNAR_DMG,)

    rarity         = 5
    ascension_stat = StatType.CRIT_DMG

    @property
    def element(self) -> Element: return Element.ELECTRO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        c = self.constellation

        nl = self._na_index()
        sk = self._skill_index()   # C5: 레벨 +3
        bl = self._burst_index()   # C3: 레벨 +3

        hits: list[SkillHit] = []

        # 일반공격
        hits.append(SkillHit("1단 공격 피해", SkillType.NORMAL_ATK, self._NA1[nl], ScalingStat.ATK))
        hits.append(SkillHit("2단 공격 피해", SkillType.NORMAL_ATK, self._NA2[nl], ScalingStat.ATK))
        hits.append(SkillHit("3단 공격 피해", SkillType.NORMAL_ATK, self._NA3[nl], ScalingStat.ATK))
        for i in (1, 2):
            hits.append(SkillHit(f"4단 공격 피해 {i}타", SkillType.NORMAL_ATK, self._NA4[nl], ScalingStat.ATK))
        hits.append(SkillHit("5단 공격 피해", SkillType.NORMAL_ATK, self._NA5[nl], ScalingStat.ATK))
        hits.append(SkillHit("강공격 피해", SkillType.CHARGED_ATK, self._CA[nl], ScalingStat.ATK))
        hits.append(SkillHit("낙하 기간 피해", SkillType.PLUNGING, self._PLUNGE[nl], ScalingStat.ATK))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl], ScalingStat.ATK))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK))

        # 원소스킬
        hits.append(SkillHit("푸른불 1단 공격 피해", SkillType.NORMAL_ATK, self._BLUE_NA1[sk], ScalingStat.ATK, Element.ELECTRO))
        hits.append(SkillHit("푸른불 2단 공격 피해", SkillType.NORMAL_ATK, self._BLUE_NA2[sk], ScalingStat.ATK, Element.ELECTRO))
        hits.append(SkillHit("푸른불 3단 공격 피해", SkillType.NORMAL_ATK, self._BLUE_NA3[sk], ScalingStat.ATK, Element.ELECTRO))
        for i in (1, 2):
            hits.append(SkillHit(f"푸른불 4단 공격 피해 {i}타", SkillType.NORMAL_ATK,
                                 self._BLUE_NA4[sk], ScalingStat.ATK, Element.ELECTRO))
        hits.append(SkillHit("푸른불 5단 공격 피해", SkillType.NORMAL_ATK, self._BLUE_NA5[sk], ScalingStat.ATK, Element.ELECTRO))
        hits.append(SkillHit("푸른불 강공격 피해", SkillType.CHARGED_ATK, self._BLUE_CA[sk], ScalingStat.ATK, Element.ELECTRO))
        hits.append(SkillHit("북국의 장창 피해", SkillType.SKILL, self._NORTHERN_LANCE_DMG[sk], ScalingStat.ATK, Element.ELECTRO))

        # 원소폭발
        hits.append(SkillHit("원소 폭발 초기 피해", SkillType.BURST, self._BURST_INITIAL_DMG[bl], ScalingStat.ATK, Element.ELECTRO))

        # ── 달감전 '직접 피해' 히트 ─────────────────────────────────────────
        # 「달 감전 반응 피해로 간주」되는 것들. reaction_type=LUNAR_CHARGED +
        # dmg_type=LUNAR_DIRECT 조합이 _calc_lunar_direct를 타며 RM 3.0이 계수에 곱해진다.
        # 대신 방어력 계수와 원소/스킬 피해 보너스는 붙지 않는다(반응 피해 계열).
        # coeff_amp가 아니라 coeff를 쓴다 — 공식에 coeff_amp 자리가 없어 조용히 무효가 된다.
        #
        # 보름 + 「주변 번개구름」으로만 붙는 타격은 여기서 **함께** 세운다. 붙는 조건이
        # 파티 달빛 징조와 로테이션 둘 다에 걸려 있어 히트 생성(Phase 1)에서는 알 수 없고,
        # 배타적인 두 갈래를 모두 세워 두고 화면을 읽는 쪽이 고르는 것이 이 엔진의 규약이다.
        for i in range(1, self._BURST_MID_HITS + 1):
            hits.append(SkillHit(
                f"중간 단계 달 감전 피해 {i}타", SkillType.BURST, self._BURST_MID_LUNAR_DMG[bl],
                ScalingStat.ATK, Element.ELECTRO,
                reaction_type=ReactionType.LUNAR_CHARGED, dmg_type=DmgType.LUNAR_DIRECT,
            ))
        for i in range(1, self._BURST_MID_FULLMOON_HITS + 1):
            hits.append(SkillHit(
                f"중간 단계 달 감전 피해 (보름) {i}타", SkillType.BURST, self._BURST_MID_LUNAR_DMG[bl],
                ScalingStat.ATK, Element.ELECTRO,
                reaction_type=ReactionType.LUNAR_CHARGED, dmg_type=DmgType.LUNAR_DIRECT,
            ))
        hits.append(SkillHit(
            "마무리 단계 달 감전 피해", SkillType.BURST, self._BURST_FINAL_LUNAR_DMG[bl],
            ScalingStat.ATK, Element.ELECTRO,
            reaction_type=ReactionType.LUNAR_CHARGED, dmg_type=DmgType.LUNAR_DIRECT,
        ))

        # 특수 원소폭발 「낙뢰 교향곡」 — Q와 배타적이라 둘 다 세워 둔다.
        hits.append(SkillHit(
            "낙뢰 교향곡 피해", SkillType.BURST, self._SYMPHONY_LUNAR_DMG[bl],
            ScalingStat.ATK, Element.ELECTRO,
            reaction_type=ReactionType.LUNAR_CHARGED, dmg_type=DmgType.LUNAR_DIRECT,
        ))
        hits.append(SkillHit(
            "낙뢰 교향곡 추가 피해 (보름)", SkillType.BURST, self._SYMPHONY_EXTRA_LUNAR_DMG[bl],
            ScalingStat.ATK, Element.ELECTRO,
            reaction_type=ReactionType.LUNAR_CHARGED, dmg_type=DmgType.LUNAR_DIRECT,
        ))

        # C2 넘어선 악령의 벽 — 북국의 장창 후 다음 일반 공격 명중 시 공격력 50% 추가타.
        # 트리거가 일반 공격이라 SkillType.NORMAL_ATK로 둔다(달감전 직접 피해라 스킬 타입별
        # 피해 보너스는 어차피 붙지 않지만, 무엇이 이 타격을 만들었는지는 남겨 둔다).
        if c >= 2:
            hits.append(SkillHit(
                "C2 추가 피해", SkillType.NORMAL_ATK, self._C2_EXTRA_ATK_RATIO,
                ScalingStat.ATK, Element.ELECTRO,
                reaction_type=ReactionType.LUNAR_CHARGED, dmg_type=DmgType.LUNAR_DIRECT,
            ))

        return {h.name: h for h in hits}

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        c = self.constellation

        # C4 밤에 포효하는 산 — 조건 없는 자기 공격력 증가.
        # Phase 3에 두는 것이 중요하다: A4/C4의 EM 변환과 달빛 징조의 축복이 모두
        # 플린스의 **최종 공격력**을 읽으므로(Phase 5), 이 증가분이 그 재료에 들어가야 한다.
        if c >= 4:
            for hit in hits.values():
                hit.add("atk_pct", self._C4_ATK_PCT, self, note="C4 밤에 포효하는 산")

        # C6 노래와 망자의 춤 — 「플린스가 적에게 주는」 달감전 피해 35% **승격**.
        # 원문이 '증가'가 아니라 '승격'이라 lunar_charged_bonus가 아니라 elevation이다
        # (공식의 Elevation 자리는 1 + 이 값). 받는 쪽이 플린스뿐이라 자기 버프다.
        if c >= 6:
            for hit in hits.values():
                hit.add("lunar_charged_elevation", self._C6_LUNAR_CHARGED_ELEVATION,
                        self, note="C6 노래와 망자의 춤")

    # ── 파티 버프 4.5: 스탯을 읽지 않는 크로스 버프 ─────────────────────────
    # 달빛 징조 판정이 필요한 효과는 전부 여기 모인다 — apply_self_buffs는 파티를 보지
    # 못하므로(hits만 받는다), 받는 쪽이 플린스뿐인 A1도 이 훅에서 자기 히트에만 건다.
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation
        if moonsign_level(all_hits) is not MoonsignLevel.FULL:
            return

        # A1 한겨울 교향곡 (보름) — 「플린스가 발동한」 달감전 피해 20% **증가**.
        # 발동자가 플린스인 경우로 한정되므로 플린스 자신의 히트에만 건다.
        for hit in all_hits[self].values():
            hit.add("lunar_charged_bonus", self._A1_FULLMOON_LUNAR_CHARGED_BONUS,
                    self, note="A1 한겨울 교향곡")

        # C2 (보름) — 플린스의 번개 원소 공격에 맞은 적의 번개 내성 감소.
        # 적에게 붙는 디버프라 파티 전원의 번개 피해에 걸린다.
        # **음수**로 넣는다 — 이 필드는 적 내성에 그대로 더해진다(profile._enemy_resistance).
        if c >= 2:
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.add("electro_res_reduction", -self._C2_FULLMOON_ELECTRO_RES_REDUCTION,
                            self, note="C2 넘어선 악령의 벽")

        # C6 (보름) — 주변 파티원의 달감전 피해 10% 승격.
        # 플린스 자신은 제외한다: 본인은 C6 앞줄의 35% 승격을 이미 받고 있고, 원문의
        # 「모든 캐릭터」에 본인까지 넣어 45%로 겹쳐 읽지 않기로 했다(사용자 판단).
        if c >= 6:
            for char, char_hits in all_hits.items():
                if char is self:
                    continue
                for hit in char_hits.values():
                    hit.add("lunar_charged_elevation", self._C6_FULLMOON_PARTY_LUNAR_ELEVATION,
                            self, note="C6 보름")

    # ── 파티 버프 5: 최종 스탯을 읽어 스케일하는 버프 (방식 B) ────────────────
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # 플린스의 최신 공격력 — 값이 아니라 **읽는 함수**로 넘긴다(지연 기여).
        # 같은 단계에서 다른 캐릭터가 플린스의 공격력을 올릴 수 있어(얀사 Q 등) 여기서
        # 확정하면 파티 멤버 순서가 결과를 바꾼다. 항상 같은 히트(첫 히트)를 읽는다.
        source_hit = next(iter(all_hits[self].values()))

        # A4 푸른불의 속삭임 (C4로 강화) — 플린스 공격력의 8%(C4: 10%)만큼 자신의 EM 증가,
        # 최대 160pt(C4: 220pt). 두 경로가 같은 식을 읽도록 비율·상한만 갈라 둔다.
        ratio, cap = ((self._C4_EM_FROM_ATK, self._C4_EM_CAP)
                      if self.constellation >= 4 else
                      (self._A4_EM_FROM_ATK, self._A4_EM_CAP))
        # 공격력 %에서 파생된 EM 지분이므로 em_from_flat이 아니라 em_from_pct_share에 넣는다
        # — 카즈하처럼 EM을 **다시 %로 변환**하는 버프가 이 지분을 재료로 쓰지 못하게 막는다.
        # 합계(elemental_mastery)는 두 조각의 합이라 플린스 본인 반응에는 그대로 들어간다.
        em = lambda: min(source_hit.convertible_atk() * ratio, cap)
        for hit in all_hits[self].values():
            hit.add("em_from_pct_share", em, self, note="A4 푸른불의 속삭임")

        # 달빛 징조의 축복 · 구시대의 비밀 — 달감전 '기본 피해' 증가. 파티 전원에게 걸린다.
        # 이네파 Moonsign과 같은 식·같은 필드다(달감전에만 걸리고 달개화·달결정에는 안 걸린다).
        # 파티에 플린스와 이네파가 함께 있으면 둘 다 기여하며, 가산이라 각자의 상한이 따로 걸린다.
        base = lambda: min(
            source_hit.convertible_atk() / 100.0 * self._MOONSIGN_BASE_DMG_PER_100_ATK,
            self._MOONSIGN_BASE_DMG_CAP,
        )
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.add("lunar_charged_base_dmg_bonus", base, self, note="Moonsign 구시대의 비밀")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · E 「고대 율법 · 등불의 신비」 자체 — 피해가 없다. 푸른불 모드 전환과 경직 저항력
    #   증가뿐이고, 모드가 바꾸는 것(평타·강공격의 번개 전환, 낙하 공격 불가, E→북국의 장창)은
    #   전부 히트로 이미 세워 두었다. 「푸른불」 접두가 붙은 히트가 그 모드의 것이다.
    # · 북국의 장창 CD 6초와 C1의 4초 감소 — 쿨다운이다. 로테이션 빈도지 히트 단가가 아니다.
    # · C1 에너지 회복 8pt (5.5초당 1회) — 원소 에너지. 자원 모델이 없다.
    # · 「주변 번개구름 존재」 판정 — 감전/달감전이 만드는 필드 오브젝트라 이 엔진에 자리가
    #   없다. 번개구름이 조건인 보름 추가 타격은 히트를 따로 세워 두고(「(보름)」 표시)
    #   합산 여부를 화면 쪽에 맡긴다.
    # · Q의 원소 에너지 소모와 낙뢰 교향곡의 「덜 소모」 — 같은 이유로 에너지다.
    # · 경직 저항력 — 피해식에 들어갈 항이 없다.
