from gidc.core.character import Character, clamp_talent_index
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import Element
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_choice, ask_int


class Iansan(Character):
    """얀사 (Iansan) | 번개 | 장병기 | 4성 | 어센션 스탯: 공격력%

    일반 공격 : 창으로 최대 3번 공격한다.
    강공격 : 일정 스태미나를 소모해 전방으로 돌진하며 경로상의 적에게 피해를 준다.
    낙하 공격 : 공중에서 땅을 내려찍어 경로상의 적을 공격하고 착지 시 범위 피해를 준다.
    밤혼 상태 · 낙뢰파 : 밤혼 가호 상태에서 얀사의 강공격은 호쾌한 「낙뢰파」로 전환되어 일정 스태미나를 소모해 전방을 짓밟아 밤혼 성질의 번개 원소 범위 피해를 준다

    E : 전광석화
    얀사가 전방으로 일정 거리 돌진해 경로상의 적에게 밤혼 성질의 번개 원소 피해를 준다.
    발동 후 얀사는 밤혼을 54pt 회복하고 밤혼 가호 상태에 진입한다.
    돌진 종료 후 5초 내에 일반 공격을 짧게 누를 시, 얀사가 스태미나를 소모하지 않는 「낙뢰파」의 짓밟기 공격을 1회 빠르게 발동한다.

    밤혼 가호 · 얀사
    지속적으로 밤혼을 소모한다. 밤혼을 모두 소모하거나 재발동 시, 얀사의 밤혼 가호가 종료된다. 밤혼 가호 상태는 아래의 특성을 가진다:
    · 얀사의 이동 속도가 증가한다.
    · 대시를 홀드하면 「번개 질주」 모드로 전환되어 짧은 시간 동안 얀사의 이동 속도가 대폭 증가한다.
    해당 상태에서 얀사는 지형 차이를 이용해 도약하거나 밤혼을 추가로 소모해 수면과 액체 열소 위에서 이동할 수 있으며, 액체 열소 피해에 면역된다.

    Q : 힘의 3요소
    「힘」의 이름으로 대지를 짓밟아 밤혼 성질의 번개 원소 범위 피해를 주고 소장했던 한정판 운동량 측정기(헬스용품)를 꺼낸다.
    발동 시, 얀사가 밤혼을 15pt 획득하고 밤혼 가호 상태에 진입한다. 운동량 측정기 퇴장 시, 얀사의 밤혼 가호도 함께 종료된다.

    운동량 측정기
    운동량 측정기는 캐릭터를 따라 움직이며, 얀사의 밤혼 수치에 따라 각기 다른 방식으로 파티 내 자신의 현재 필드 위 캐릭터의 공격력을 증가시킨다.
    · 얀사의 밤혼이 42pt 미만일 경우, 얀사의 밤혼과 공격력에 기반해 공격력 보너스를 획득한다.
    · 얀사의 밤혼이 42pt 이상일 경우, 운동량 측정기가 「뜨거운 응원!」 모드로 전환되어 얀사의 공격력에 기반해 더 높은 공격력 보너스를 획득한다.
    또한 운동량 측정기는 존재 기간 동안 얀사 이외의 파티 내 자신의 현재 필드 위 캐릭터의 이동 거리를 기록하고, 1초마다 이전 1초 동안 기록된 이동 거리를 기반으로 얀사의 밤혼을 회복한다.
    운동량 측정기는 얀사의 밤혼 가호 지속 시간이 종료되면 사라진다. 얀사가 비전투 상태 시, 1초 후에 운동량 측정기가 사라진다.
    운동량 측정기가 존재하는 동안, 얀사가 대기 상태 시에도 밤혼 가호는 종료되지 않는다.

    A1 : 근력 운동
    「낙뢰파」가 적에게 명중 후, 얀사는 15초 동안 지속되는 「표준 동작」 효과를 획득한다.
    지속 시간 동안 얀사의 공격력이 20% 증가하고, 원소폭발 힘의 3요소의 운동량 측정기로 밤혼 회복 시, 추가로 밤혼을 1pt 회복한다.
    또한 파티 내 자신의 현재 필드 위 캐릭터가 밤혼을 소모 또는 회복 후, 얀사가 다음에 운동량 측정기로 밤혼 회복 시, 추가 밤혼 회복량이 4pt까지 증가한다.
    해당 효과는 2.8초마다 최대 1회 발동된다.「표준 동작」 효과는 얀사의 밤혼 가호 종료 시 사라진다

    A4 : 운동량 테스트
    주변에 있는 파티 내 캐릭터가 「밤혼 발산」 발동 시, 얀사가 「준비 운동」을 획득한다. 지속 시간 10초.
    지속 시간 동안 얀사가 밤혼을 최소 1pt 회복 시, 자신의 현재 필드 위 캐릭터의 HP를 얀사 공격력의 60%만큼 회복한다.
    해당 효과는 2.8초마다 최대 1회 발동된다

    C1 : 뭐든 시작이 어려운 법
    전투 중 얀사가 밤혼 가호 상태 시, 밤혼 게이지를 6pt 소모할 때마다 얀사는 자신의 원소 에너지를 15pt 회복한다.
    해당 효과는 18초마다 최대 1회 발동된다

    C2 : 게으름은 운동의 적!
    원소폭발 힘의 3요소 발동 시, 얀사도 고유 특성 「근력 운동」의 「표준 동작」 효과를 획득한다, 지속 시간: 15초.
    또한 「표준 동작」 효과 지속 시간 동안 얀사가 대기 상태일 경우, 파티 내 자신의 현재 필드 위 캐릭터의 공격력이 30% 증가한다.
    해당 효과는 고유 특성 「근력 운동」을 해금해야 한다

    C3 : 과학적인 식단
    원소전투 스킬 전광석화의 스킬 레벨+3

    C4 : 가장 중요한 건 꾸준함
    운동량 측정기 존재 기간 동안, 얀사를 제외한 자신의 파티 내 필드 위 캐릭터가 원소폭발 발동 후, 얀사는 운동량 측정기가 퇴장할 때까지 지속되는 「원기」를 2스택 획득한다.
    운동량 측정기를 소환할 때마다 해당 효과는 최대 1회 발동된다. 얀사가 운동량 측정기를 통해 밤혼 회복 시, 「원기」를 1스택 소모해 얀사의 밤혼을 추가로 4pt 회복한다.
    또한 운동량 측정기의 밤혼 회복량이 밤혼 최대치를 초과하면, 얀사가 다음에 운동량 측정기로 밤혼 회복 시, 초과량의 50%에 해당하는 밤혼을 추가 회복한다

    C5 : 아직 한계가 아니다!
    원소폭발 힘의 3요소의 스킬 레벨+3

    C6 : 「비옥한 터전」의 가르침
    운동량 측정기의 지속 시간이 3초 연장된다. 또한 얀사가 밤혼 회복 효과 발동 시, 밤혼이 최대치를 초과한 경우,
    파티 내 자신의 현재 필드 위 캐릭터의 주는 피해가 25% 증가하는 「극한의 힘」 효과를 획득한다. 지속 시간: 3초
    """
    name = "얀사"
    weapon_type = WeaponType.POLEARM

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # 일반 공격 · 바벨 강타 (% ATK, L1~L11) — 창으로 최대 3번
    _NA = [
        [0.4700, 0.5080, 0.5460, 0.6010, 0.6390, 0.6830, 0.7430, 0.8030, 0.8630, 0.9290, 0.9940],
        [0.4280, 0.4620, 0.4970, 0.5470, 0.5820, 0.6220, 0.6760, 0.7310, 0.7860, 0.8450, 0.9050],
        [0.6440, 0.6960, 0.7490, 0.8240, 0.8760, 0.9360, 1.0180, 1.1010, 1.1830, 1.2730, 1.3630],
    ]

    # 강공격 (% ATK, L1~L11) — 스태미나 소모 25
    _CA = [1.0030, 1.0840, 1.1660, 1.2830, 1.3640, 1.4570, 1.5860, 1.7140, 1.8420, 1.9820, 2.1220]

    # 밤혼 가호 · 「낙뢰파」 (% ATK, L1~L11) — 밤혼 가호 상태에서 강공격을 통째로 대체한다.
    # 스태미나 소모도 강공격과 같은 25pt이고 계수 표도 일반 공격 표에 함께 실려 있어
    # 일반 공격 레벨로 스케일한다. 강공격 자리에 서지만 피해는 밤혼 성질의 번개 원소다.
    _THUNDERQUAKE = [0.8420, 0.9100, 0.9790, 1.0770, 1.1450, 1.2240, 1.3310, 1.4390, 1.5470, 1.6640, 1.7820]

    # 낙하 공격 — 대검을 제외한 무기 공통 표 (이네파·베넷과 같은 값).
    # 위키의 63.9 / 128 / 160 은 아래 값을 세 자리로 자른 것이라 정밀한 쪽이 맞다.
    _PLUNGE      = [0.6393, 0.6914, 0.7434, 0.8177, 0.8698, 0.9292, 1.0110, 1.0928, 1.1746, 1.2638, 1.3530]
    _LOW_PLUNGE  = [1.2784, 1.3824, 1.4865, 1.6351, 1.7392, 1.8581, 2.0216, 2.1851, 2.3486, 2.5270, 2.7054]
    _HIGH_PLUNGE = [1.5968, 1.7267, 1.8567, 2.0424, 2.1723, 2.3209, 2.5251, 2.7293, 2.9336, 3.1564, 3.3792]

    # 원소 스킬 전광석화 (% ATK, L1~L13, C3 적용 시 최대 L13)
    _SKILL_DMG = [
        2.8640, 3.0790, 3.2940, 3.5800, 3.7950,
        4.0100, 4.2960, 4.5820, 4.8690, 5.1550,
        5.4420, 5.7280, 6.0860,
    ]

    # 원소 폭발 힘의 3요소 (% ATK, L1~L13, C5 적용 시 최대 L13)
    _BURST_DMG = [
        4.3040, 4.6270, 4.9500, 5.3800, 5.7030,
        6.0260, 6.4560, 6.8860, 7.3170, 7.7470,
        8.1780, 8.6080, 9.1460,
    ]

    # 운동량 측정기가 줄 수 있는 **최대 공격력 보너스** (실수치, L1~L13).
    # 비율로 계산한 값이 이 값을 넘으면 여기서 잘린다.
    _MEASURER_ATK_CAP = [
        330, 370, 410, 450, 490,
        530, 570, 610, 650, 690,
        730, 770, 810,
    ]

    # ── 밤혼 · 운동량 측정기 상수 ──────────────────────────────────────────────
    _NIGHTSOUL_MAX            = 54     # E 표의 「밤혼 최대치 54.0pt」
    _MEASURER_HOT_THRESHOLD   = 42     # 이 값 이상이면 「뜨거운 응원!」 모드
    _MEASURER_HOT_RATIO       = 0.27   # 뜨거운 응원! — 얀사 공격력의 27%
    _MEASURER_RATIO_PER_POINT = 0.005  # 낮은 밤혼 — 밤혼 1pt당 얀사 공격력의 0.5%

    # ── 특성 계수 ─────────────────────────────────────────────────────────────
    _A1_ATK_PCT          = 0.20   # A1 「표준 동작」 — 얀사 자신의 공격력 +20%
    _C2_ON_FIELD_ATK_PCT = 0.30   # C2 — 얀사가 대기 상태일 때 필드 위 캐릭터 공격력 +30%
    _C6_ALL_DMG_BONUS    = 0.25   # C6 「극한의 힘」 — 필드 위 캐릭터의 주는 피해 +25%
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 3
    BURST_LEVEL_UP_CONSTELLATION = 5
    NA_TABLES = (*_NA, _CA, _THUNDERQUAKE, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_DMG,)
    BURST_TABLES = (_BURST_DMG, _MEASURER_ATK_CAP,)

    rarity         = 4
    ascension_stat = StatType.ATK_PCT

    @property
    def element(self)  -> Element: return Element.ELECTRO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        # C3: 원소 스킬 레벨 +3 (최대 13)
        sk = self._skill_index()
        # C5: 원소 폭발 레벨 +3 (최대 13)
        bl = self._burst_index()
        nl = self._na_index()

        hits: list[SkillHit] = []

        # 창 캐릭터라 일반/강/낙하 공격은 물리 피해(element 미지정 → PHYSICAL)
        for i, row in enumerate(self._NA):
            hits.append(SkillHit(f"{i+1}단 공격 피해", SkillType.NORMAL_ATK, row[nl], ScalingStat.ATK))

        hits.append(SkillHit("강공격 피해", SkillType.CHARGED_ATK, self._CA[nl], ScalingStat.ATK))

        # 「낙뢰파」는 강공격을 통째로 대체하므로 강공격 피해 보너스를 받고, 원소는 번개다.
        # 강공격과 배타적이라 실제 로테이션에서는 한쪽만 나온다 — 둘 다 세워 두고 어느 쪽을
        # 합산할지는 화면을 읽는 쪽이 고른다(산드로네·한운과 같은 규약).
        hits.append(SkillHit("낙뢰파 피해", SkillType.CHARGED_ATK, self._THUNDERQUAKE[nl],
                             ScalingStat.ATK, Element.ELECTRO))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK))

        hits.append(SkillHit("원소 스킬 피해", SkillType.SKILL, self._SKILL_DMG[sk], ScalingStat.ATK, Element.ELECTRO))
        hits.append(SkillHit("원소 폭발 피해", SkillType.BURST, self._BURST_DMG[bl], ScalingStat.ATK, Element.ELECTRO))

        return {h.name: h for h in hits}

    # ── 운동량 측정기 (모드 판정의 단일 출처) ─────────────────────────────────
    # 밤혼 수치 하나가 두 모드를 가른다. 「얼마나 주는가」를 여러 군데 적지 않도록 비율과
    # 최종 보너스를 각각 함수로 두고, 소비처는 이 둘만 읽는다.
    def _measurer_ratio(self, nightsoul: int) -> float:
        """운동량 측정기가 얀사의 공격력에 곱하는 비율.

        42pt 이상이면 「뜨거운 응원!」으로 전환되어 27% 고정이고, 미만이면 밤혼 1pt당 0.5%다.
        밤혼 최대치가 54pt라 두 식의 상한은 27%로 같지만, 문턱에서 21% → 27%로 튀는 구간이
        있어 하나로 접을 수 없다."""
        if nightsoul >= self._MEASURER_HOT_THRESHOLD:
            return self._MEASURER_HOT_RATIO
        return nightsoul * self._MEASURER_RATIO_PER_POINT

    def _measurer_atk_bonus(self, atk: float) -> float:
        """운동량 측정기가 필드 위 캐릭터에게 주는 공격력 보너스(실수치, 상한 적용)."""
        cap = self._MEASURER_ATK_CAP[self._burst_index()]
        return min(atk * self._measurer_ratio(self._nightsoul), cap)

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        c = self.constellation

        # Q 발동 여부는 자기 효과(C2의 「표준 동작」 자동 획득)와 파티 효과(운동량 측정기)를
        # 동시에 가르므로 여기서 한 번만 묻고 self에 저장해 뒤 단계가 재사용한다.
        self._q_active = ask_bool("[얀사 Q] 힘의 3요소 발동 (운동량 측정기) 여부")

        # A1 「표준 동작」: 「낙뢰파」 명중 후 15초 동안 얀사의 공격력 +20%.
        # 받는 쪽이 얀사뿐이라 트리거가 무엇이든 자기 버프다. C2가 있으면 원소 폭발 발동만으로도
        # 얻으므로, 그 경우엔 묻지 않고 Q 발동 여부에서 유도한다.
        self._standard_form = (c >= 2 and self._q_active) or ask_bool(
            "[얀사 A1] 「표준 동작」 (공격력 +20%) 여부"
        )
        if self._standard_form:
            for hit in hits.values():
                hit.add("atk_pct", self._A1_ATK_PCT, self, note="A1 표준 동작")

    # ── 파티 버프 4: 코어 스탯(atk_pct) 기여 + 유저 입력 수집 ─────────────────
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # 운동량 측정기의 모드를 가르는 밤혼 수치. 시간에 따라 오르내리는 값이라 파티 구성만으로
        # 유도할 수 없다 — 실제로 실린 수치를 묻고 상한만 E의 밤혼 최대치에서 얻는다.
        self._nightsoul = (
            ask_int("[얀사 Q] 운동량 측정기 적용 시점의 밤혼 수치 (pt)", 0, self._NIGHTSOUL_MAX)
            if self._q_active else 0
        )

        # C6 「극한의 힘」: 밤혼 회복량이 최대치를 넘길 때만 붙는다 — 로테이션 몫이라 묻는다.
        self._c6_surge = (c >= 6) and ask_bool("[얀사 C6] 「극한의 힘」 (주는 피해 +25%) 여부")

        # 「현재 필드 위 캐릭터」 — 운동량 측정기·C2·C6이 모두 같은 1명을 대상으로 하므로
        # 한 번만 고르게 하고 셋이 그 답을 나눠 쓴다. 파티 전원에게 걸면 부풀려진다.
        self._c2_standby = (c >= 2) and self._standard_form
        self._on_field = (
            self._ask_on_field_member(all_hits)
            if (self._q_active or self._c2_standby or self._c6_surge) else None
        )

        # C2 뒷문장: 「표준 동작」 지속 중 **얀사가 대기 상태일 때** 필드 위 캐릭터 공격력 +30%.
        # 대기 상태가 조건이므로 얀사 자신을 필드 위로 고른 경우에는 걸리지 않는다.
        if self._c2_standby and self._on_field is not None and self._on_field is not self:
            for hit in all_hits[self._on_field].values():
                hit.add("atk_pct", self._C2_ON_FIELD_ATK_PCT, self, note="C2 대기 상태")

    def _ask_on_field_member(self, all_hits):
        """운동량 측정기·C2·C6이 대상으로 삼을 현재 필드 위 캐릭터를 고르게 한다.
        파티원이 1명뿐이면 묻지 않는다."""
        members = list(all_hits.keys())
        if len(members) == 1:
            return members[0]
        options = [
            f"{char.name} ({char.element.value})" + (" ← 얀사" if char is self else "")
            for char in members
        ]
        return members[ask_choice("[얀사] 현재 필드 위 캐릭터", options)]

    # ── 파티 버프 4.5: 스탯을 읽지 않는 크로스 버프 ───────────────────────────
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # C6 「극한의 힘」: 필드 위 캐릭터의 주는 피해 +25% — 고정값이라 여기서 끝난다.
        if self._c6_surge and self._on_field is not None:
            for hit in all_hits[self._on_field].values():
                hit.add("all_dmg_bonus", self._C6_ALL_DMG_BONUS, self, note="C6 극한의 힘")

    # ── 파티 버프 5: 최종 스탯을 읽어 스케일하는 버프 (방식 B) ────────────────
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        if not self._q_active or self._on_field is None:
            return

        # 얀사의 최신 공격력 — 값이 아니라 **읽는 함수**로 넘긴다(지연 기여). 이 공격력에는
        # 다른 캐릭터가 Phase 5에서 주는 몫도 들어오므로 여기서 확정하면 누가 먼저 실행되느냐가
        # 결과를 바꾼다. 항상 같은 히트(첫 히트)를 읽으므로 언제 계산되든 값은 하나다.
        #
        # 읽는 쪽은 current_atk()가 아니라 convertible_atk()다 — 측정기가 만든 공격력은
        # 재료에서 빠져야 한다. 게임은 수정자를 순서대로 접어 자기 출력이 자기 입력에 섞이지
        # 않지만, 이 엔진은 순서를 버리고 지연 평가로 값을 정하므로 같은 슬롯을 읽고 쓰면
        # 값이 정해지지 않는다(얀사 자신을 필드 위로 고르면 바로 그 경우다). 그래서 출력은
        # 꼬리표 달린 별도 슬롯 atk_from_pct_share로 간다 — 최종 공격력에는 그대로 들어가므로
        # 스탯 시트도, 얀사 공격력을 다시 읽는 세트·무기(제사의 여운 등)도 정상적으로 본다.
        source_hit = next(iter(all_hits[self].values()))
        bonus = lambda: self._measurer_atk_bonus(source_hit.convertible_atk())

        for hit in all_hits[self._on_field].values():
            hit.add("atk_from_pct_share", bonus, self, note="Q 운동량 측정기")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 밤혼 수지 전반 (E 54pt 회복, Q 15pt 획득, A1의 추가 회복 1pt/4pt, C4 「원기」와 초과량
    #   50% 재회복, C6 지속 시간 3초 연장) — 자원 모델이 없어 피해식에 들어갈 항이 없다.
    #   결과값인 밤혼 수치만 유저에게 묻는다.
    # · A4 「운동량 테스트」 — 치유(얀사 공격력의 60%)뿐이다. 이 엔진은 치유를 히트로 만들지
    #   않는다(에스코피에·한운과 같은 취급).
    # · C1 「뭐든 시작이 어려운 법」 — 원소 에너지 15pt 회복. 로테이션 빈도지 히트 단가가 아니다.
    # · 밤혼 가호의 이동 속도·「번개 질주」·액체 열소 면역 — 이동이지 피해가 아니다.
