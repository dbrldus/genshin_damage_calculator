from gidc.core.character import Character, clamp_talent_index
from gidc.core.party_state import hexerei_rite_for
from gidc.core.profile import SkillHit, SkillType, ScalingStat, element_dmg_field
from gidc.enums import CharacterTrait, Element
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_choice, ask_multi_choice


class Sucrose(Character):
    """설탕 (Sucrose) | 바람 | 법구 | 4성 | 어센션 스탯: 바람 원소 피해 보너스

    일반 공격 : 풍령으로 최대 4번 공격해 바람 원소 피해를 준다.
    강공격 : 일정 스태미나를 소모해 짧은 영창 후 바람 원소 범위 피해를 준다.
    낙하 공격 : 풍령의 힘을 모은 후 지면을 강타해 경로상의 적을 공격하고 착지 시 바람 원소 범위 피해를 준다.

    E : 풍령 작성 · 육삼공팔
    소형 풍령을 소환해 적과 물체를 풍령이 있는 위치로 끌어당긴 후 공중으로 띄우고 바람 원소 범위 피해를 입힌다.

    Q : 금기 · 풍령 작성 · 칠오 동구 이형
    설탕이 불안정한 플라스크를 던져 대형의 바람 정령을 생성한다.
    존재하는 동안 대형의 바람 정령은 주변의 적과 물체를 지속해서 끌어당긴 후 공중으로 띄우고 바람 원소 범위 피해를 준다.

    원소 전환
    바람 정령 스킬을 시전하는 동안 물 원소/불 원소/얼음 원소/번개 원소에 닿으면 상응하는 원소 속성을 획득하고 추가로 해당 속성 피해를 준다.
    원소 전환은 스킬을 시전하는 동안 1회만 발생한다.

    A1 : 촉매 치환술
    설탕이 원소 확산 반응 발동 후 파티 내 모든 대응하는 원소 유형 캐릭터(설탕 자신을 포함하지 않음)의 원소 마스터리가 50pt 증가한다. 지속 시간: 8초

    A4 : 작은 혜풍
    풍령 작성 · 육삼공팔 혹은 금기 · 풍령 작성 · 칠오 동구 이형이 적을 명중하면 설탕의 원소 마스터리의 20%를 기반으로 파티 내 모든 캐릭터(설탕 자신을 포함하지 않음)에게 원소 마스터리 보너스를 제공한다. 지속 시간: 8초

    마도 : 마녀의 전야제ㆍ일곱 순환의 이치
    마녀의 과제 · 신비한 꽃을 완료하면, 설탕이 마도 캐릭터가 된다. 파티에 마도 캐릭터를 2명 이상 편성하면 마도 · 비밀 의식 효과를 획득해 마도 캐릭터가 강화된다.

    마도 · 비밀 의식
    소형 풍령을 소환한 후 15초 동안 주변에 있는 파티 내 캐릭터가 일반 공격, 강공격, 낙하 공격, 원소전투 스킬과 원소폭발로 주는 피해가 5.71428% 증가한다.
    거대 풍령을 소환한 후 20초 동안 주변에 있는 파티 내 마도 캐릭터의 일반 공격, 강공격, 낙하 공격, 원소전투 스킬과 원소폭발로 주는 피해가 7.14285% 증가한다

    C1 : 쌓아 올린 진공 영역
    풍령 작성 · 육삼공팔의 사용 가능 횟수가 1회 증가한다.

    C2 : 불속박형 베트
    금기 · 풍령 작성 · 칠오 동구 이형의 스킬 지속 시간을 2초 연장한다.

    C3 : 실수하지 않는 소녀
    풍령 작성 · 육삼공팔의 스킬 레벨+3

    C4 : 연금의 편집증
    설탕이 일반 공격 혹은 강공격을 7번 발동할 때마다 풍령 작성 · 육삼공팔의 재사용 대기시간이 랜덤으로 1~7초 감소한다. 0.1초마다 최대 1회 카운트된다

    C5 : 진지한 보통병
    금기 · 풍령 작성 · 칠오 동구 이형의 스킬 레벨+3

    C6 : 혼돈의 엔트로피
    금기 · 풍령 작성 · 칠오 동구 이형에 원소 전환이 발생하면 파티 내 모든 캐릭터는 스킬이 지속되는 동안 대응하는 원소 피해 보너스를 20% 획득한다.
    또한, 파티 내 주변의 마도 캐릭터가 추가로 대응하는 원소 피해 보너스를 8.57142% 획득한다
    """
    name = "설탕"
    weapon_type = WeaponType.CATALYST
    # 「마녀의 과제 · 신비한 꽃」을 완료하면 마도 캐릭터가 된다.
    unlockable_traits = frozenset({CharacterTrait.HEXEREI})


    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # 일반 공격 (% ATK, L1~L11) — 법구라 4단 모두 바람 원소 피해
    _NA = [
        [0.3350, 0.3600, 0.3850, 0.4180, 0.4430, 0.4690, 0.5020, 0.5350, 0.5690, 0.6020, 0.6360],
        [0.3060, 0.3290, 0.3520, 0.3830, 0.4060, 0.4290, 0.4590, 0.4900, 0.5210, 0.5510, 0.5820],
        [0.3840, 0.4130, 0.4420, 0.4810, 0.5090, 0.5380, 0.5770, 0.6150, 0.6540, 0.6920, 0.7310],
        [0.4790, 0.5150, 0.5510, 0.5990, 0.6350, 0.6710, 0.7190, 0.7670, 0.8150, 0.8630, 0.9100],
    ]

    # 강공격 (% ATK, L1~L11) — 스태미나 소모 50
    _CA = [1.2000, 1.2900, 1.3800, 1.5000, 1.5900, 1.6800, 1.8000, 1.9200, 2.0400, 2.1600, 2.2800]

    # 낙하 공격 (% ATK, L1~L11) — 법구 전용표 (모나/시틀라리/콜롬비나와 같은 값).
    # 위키 표의 56.8 / 114 / 142 는 이 값을 세 자리로 자른 것이라 정밀한 공용표를 그대로 쓴다.
    _PLUNGE      = [0.5683, 0.6145, 0.6608, 0.7269, 0.7731, 0.8260, 0.8987, 0.9714, 1.0441, 1.1234, 1.2027]
    _LOW_PLUNGE  = [1.1363, 1.2288, 1.3213, 1.4535, 1.5459, 1.6517, 1.7970, 1.9423, 2.0877, 2.2462, 2.4048]
    _HIGH_PLUNGE = [1.4193, 1.5349, 1.6504, 1.8154, 1.9310, 2.0630, 2.2445, 2.4261, 2.6076, 2.8057, 3.0037]

    # 원소 스킬 「풍령 작성 · 육삼공팔」 (% ATK, L1~L13, C3 적용 시 최대 L13) — CD 15초
    _SKILL_DMG = [
        2.1100, 2.2700, 2.4300, 2.6400, 2.8000,
        2.9600, 3.1700, 3.3800, 3.5900, 3.8000,
        4.0100, 4.2200, 4.4900,
    ]

    # 원소 폭발 「금기 · 풍령 작성 · 칠오 동구 이형」 (% ATK, L1~L13, C5 적용 시 최대 L13)
    # 지속 6초(C2가 +2초), CD 20초, 원소 에너지 80.
    _BURST_DOT = [        # 지속 피해 — 대형 바람 정령이 끌어당기며 주는 바람 원소 피해
        1.4800, 1.5900, 1.7000, 1.8500, 1.9600,
        2.0700, 2.2200, 2.3700, 2.5200, 2.6600,
        2.8100, 2.9600, 3.1500,
    ]
    _BURST_ABSORPTION = [ # 부가 원소 피해 — 원소 전환이 일어났을 때만 발생한다
        0.4400, 0.4730, 0.5060, 0.5500, 0.5830,
        0.6160, 0.6600, 0.7040, 0.7480, 0.7920,
        0.8360, 0.8800, 0.9350,
    ]

    # ── 고유 특성 / 마도 / 명함 계수 (히트 아님 — 버프 훅에서 사용) ─────────────
    _A1_SWIRLED_ELEMENT_EM = 50      # A1 : 확산된 원소 유형 파티원의 원소 마스터리 +50
    _A4_EM_SHARE           = 0.20    # A4 : 설탕 원소 마스터리의 20%를 파티원에게 분배
    # 마도 · 비밀 의식 — 파티에 마도 캐릭터가 2명 이상일 때만 성립한다.
    _RITE_SKILL_DMG_BONUS  = 0.0571428   # 소형 풍령(E) 15초, 파티 전원
    _RITE_BURST_DMG_BONUS  = 0.0714285   # 거대 풍령(Q) 20초, 마도 캐릭터만
    # C6 : 원소 전환 발생 시 대응 원소 피해 보너스 — 파티 전원 / 마도 캐릭터 추가분
    _C6_ELEM_DMG_BONUS      = 0.20
    _C6_HEXEREI_EXTRA_BONUS = 0.0857142
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 3
    BURST_LEVEL_UP_CONSTELLATION = 5
    NA_TABLES    = (*_NA, _CA, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_DMG,)
    BURST_TABLES = (_BURST_DOT, _BURST_ABSORPTION,)

    rarity         = 4
    ascension_stat = StatType.ANEMO_DMG

    # ── 원소 전환 / 확산의 대상 원소 ───────────────────────────────────────
    # 바람이 흡수·확산할 수 있는 네 원소. 순서는 청록색 그림자 4세트·유구한 반암 4세트와
    # 같게 두어 화면의 선택지 순서가 갈리지 않게 한다.
    _ABSORBABLE = (Element.PYRO, Element.HYDRO, Element.CRYO, Element.ELECTRO)

    # 원소 전환이 없으면 통째로 사라지는 히트. 이름을 상수로 둔 이유는 build_hits와
    # contribute_dependent_stats 두 곳이 같은 열쇠를 써야 하기 때문이다.
    _ABSORPTION_HIT = "원소 폭발 부가 원소 피해"

    @property
    def element(self)  -> Element: return Element.ANEMO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        c = self.constellation

        # C3: 원소 스킬 레벨 +3 (최대 13)
        sk = self._skill_index()
        # C5: 원소 폭발 레벨 +3 (최대 13)
        bl = self._burst_index()
        nl = self._na_index()

        hits: list[SkillHit] = []

        # 법구 캐릭터라 일반/강/낙하 공격도 모두 바람 원소 피해다 (모나·니콜과 동일)
        for i, row in enumerate(self._NA):
            hits.append(SkillHit(f"{i+1}단 공격 피해", SkillType.NORMAL_ATK, row[nl],
                                 ScalingStat.ATK, Element.ANEMO))

        hits.append(SkillHit("강공격 피해", SkillType.CHARGED_ATK, self._CA[nl],
                             ScalingStat.ATK, Element.ANEMO))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK, Element.ANEMO))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK, Element.ANEMO))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK, Element.ANEMO))

        hits.append(SkillHit("원소 스킬 피해", SkillType.SKILL, self._SKILL_DMG[sk],
                             ScalingStat.ATK, Element.ANEMO))

        hits.append(SkillHit("원소 폭발 지속 피해", SkillType.BURST, self._BURST_DOT[bl],
                             ScalingStat.ATK, Element.ANEMO))

        # 원소 전환의 부가 피해. **어느 원소인지는 파티 구성만으로 정해지지 않는다** —
        # 적이 깔아 둔 원소에 닿아도 전환되므로 유저 입력이고, 입력은 Phase 4에서만 모을 수
        # 있다(질문 ID가 호출 지점·반복 횟수라 실행 시점이 밀리면 질문 집합이 흔들린다).
        # 그래서 히트는 여기서 만들고 원소만 Phase 4에서 확정한다 — 전환이 없으면 그때
        # 히트를 지운다(contribute_dependent_stats). 여기 적어 둔 바람은 그 전까지의
        # 자리표이며 Phase 4를 지나면 남아 있지 않다.
        hits.append(SkillHit(self._ABSORPTION_HIT, SkillType.BURST, self._BURST_ABSORPTION[bl],
                             ScalingStat.ATK, Element.ANEMO))

        return {h.name: h for h in hits}

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        pass  # 자기 전용 버프가 없다 — 설탕의 고유 특성·마도·명함은 전부 파티 대상이다

    # ── 파티 버프 4: 코어 스탯 기여 + 유저 입력 수집 ─────────────────────────
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # ── 원소 전환 ─────────────────────────────────────────────────────
        # 한 번만 묻고 두 곳이 쓴다: 부가 피해 히트의 원소와 C6의 원소 피해 보너스.
        idx = ask_choice(
            "[설탕 Q] 원소 전환으로 획득한 원소",
            ["없음"] + [e.value for e in self._ABSORBABLE],
        )
        self._absorbed: Element | None = self._ABSORBABLE[idx - 1] if idx else None

        # 전환이 없으면 부가 피해 자체가 발생하지 않는다 — 히트를 남겨 두면 있지도 않은
        # 「바람 속성 부가 피해」 행이 화면에 뜨므로 여기서 지운다.
        hits = all_hits[self]
        if self._absorbed is None:
            hits.pop(self._ABSORPTION_HIT, None)
        else:
            hits[self._ABSORPTION_HIT].element = self._absorbed

        # ── A1 「촉매 치환술」 : 확산된 원소 유형의 파티원 원소 마스터리 +50 ──────
        # 「대응하는 원소 유형 캐릭터」가 대상이라 그 원소의 파티원이 없으면 효과가 갈 곳이
        # 없다 — 선택지를 파티에 실제로 있는 원소로 좁히고, 하나도 없으면 묻지 않는다.
        # 한 로테이션에서 여러 원소를 확산시키는 것이 보통이라(지속 8초) 복수 선택이다.
        targets = {
            elem: [char for char in all_hits if char is not self and char.element is elem]
            for elem in self._ABSORBABLE
        }
        swirlable = [elem for elem in self._ABSORBABLE if targets[elem]]
        if swirlable:
            picked = ask_multi_choice(
                "[설탕 A1] 확산시킨 원소 (해당 원소 파티원 원소 마스터리 +50)",
                [elem.value for elem in swirlable],
            )
            for i in picked:
                for char in targets[swirlable[i]]:
                    for hit in all_hits[char].values():
                        hit.add("em_from_flat", self._A1_SWIRLED_ELEMENT_EM, self, note="A1")

        # ── 뒤 단계에서 쓸 입력 ────────────────────────────────────────────
        # A4는 설탕의 최종 원소 마스터리를 읽어야 하므로 적용은 Phase 5로 넘긴다.
        self._a4_active = ask_bool("[설탕 A4] E·Q가 적을 명중 (파티 원소 마스터리 보너스) 여부")

        # 마도 · 비밀 의식 — 마녀의 과제를 완료하지 않았으면 「마녀의 전야제」 특성 자체가
        # 없어 내놓을 효과가 없다. 대상이 파티 전원이라 「마도 캐릭터만 받는다」로는 설명되지
        # 않는 자리다 — 조건은 받는 쪽이 아니라 **내는 쪽**에 있다(party_state.hexerei_rite_for).
        self._rite = hexerei_rite_for(self, all_hits)
        self._rite_skill = self._rite and ask_bool("[설탕 마도·비밀 의식] 소형 풍령 소환 후 15초 이내 여부")
        self._rite_burst = self._rite and ask_bool("[설탕 마도·비밀 의식] 거대 풍령 소환 후 20초 이내 여부")

    # ── 파티 버프 4.5: 스탯을 읽지 않는 크로스 버프 ─────────────────────────
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # ── 마도 · 비밀 의식 ──────────────────────────────────────────────
        # 「일반 공격, 강공격, 낙하 공격, 원소전투 스킬과 원소폭발로 주는 피해」 — 직접 피해
        # 다섯 종류 전부라 스킬 타입으로 거를 것이 없어 all_dmg_bonus로 넣는다. 이 필드는
        # 직접 피해 공식에만 들어가므로(profile.build_damage_context) 확산 같은 격변 피해가
        # 덩달아 부풀지 않는다 — 문구의 범위와 정확히 같다.
        if self._rite_skill:
            for char_hits in all_hits.values():          # 파티 전원
                for hit in char_hits.values():
                    hit.add("all_dmg_bonus", self._RITE_SKILL_DMG_BONUS, self, note="마도·비밀 의식 E")

        if self._rite_burst:
            for char, char_hits in all_hits.items():
                if not char.has_trait(CharacterTrait.HEXEREI):   # 마도 캐릭터만
                    continue
                for hit in char_hits.values():
                    hit.add("all_dmg_bonus", self._RITE_BURST_DMG_BONUS, self, note="마도·비밀 의식 Q")

        # ── C6 「혼돈의 엔트로피」 ─────────────────────────────────────────
        # 전환된 원소의 피해 보너스를 파티 전원에게, 마도 캐릭터에게는 추가분까지.
        # 필드 이름은 profile.element_dmg_field가 유일한 출처다 — 원소별 표를 여기 또 두면
        # 원소가 늘거나 필드명이 바뀔 때 한쪽만 고쳐진다.
        if self.constellation < 6 or self._absorbed is None:
            return
        field = element_dmg_field(self._absorbed)
        for char, char_hits in all_hits.items():
            bonus = self._C6_ELEM_DMG_BONUS
            if char.has_trait(CharacterTrait.HEXEREI):
                bonus += self._C6_HEXEREI_EXTRA_BONUS
            for hit in char_hits.values():
                hit.add(field, bonus, self, note="C6")

    # ── 파티 버프 5: 최종 스탯을 읽어 스케일하는 버프 (방식 B) ────────────────
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        if not self._a4_active:
            return

        # A4 「작은 혜풍」: 설탕 원소 마스터리의 20%를 파티원(자신 제외)에게 원소 마스터리로 준다.
        #
        # 값이 아니라 **읽는 함수**로 넘긴다(지연 기여) — 설탕의 원소 마스터리는 다른 캐릭터가
        # 같은 단계에서 더해 줄 수 있어(이네파 A4 등), 여기서 미리 확정하면 파티 멤버 순서가
        # 결과를 바꾼다.
        #
        # 재료는 elemental_mastery(합계)가 아니라 em_from_flat이다 — 이쪽은 원소 마스터리를
        # **다시 원소 마스터리로 변환**하는 효과라, 남에게서 %로 받은 지분까지 재료로 쓰면
        # 설탕 둘이 서로를 부풀리는 고리가 된다. 원소 마스터리에 비례한 몫을 피해에 직접
        # 더하는 효과(시틀라리 A4/C1)만 합계 elemental_mastery를 읽는다.
        #
        # 받는 쪽은 em_from_pct_share **한 곳**에만 넣는다. 합계(elemental_mastery)는
        # 두 조각의 합이라 본인 반응에는 자동으로 들어가고, 다음 %-변환(카즈하의 EM→원소
        # 피해 등)이 읽는 em_from_flat에는 애초에 안 쌓인다.
        source_hit = next(iter(all_hits[self].values()))
        share = lambda: source_hit.em_from_flat * self._A4_EM_SHARE

        for char, char_hits in all_hits.items():
            if char is self:      # 「설탕 자신을 포함하지 않음」
                continue
            for hit in char_hits.values():
                hit.add("em_from_pct_share", share, self, note="A4")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · C1(E 사용 횟수 +1), C2(Q 지속 +2초), C4(E 재사용 대기시간 1~7초 감소)
    #   — 로테이션 빈도·지속력이지 히트 단가에 들어갈 항이 없다.
    # · 원소 전환의 「스킬을 시전하는 동안 1회만」 제약 — 부가 피해 히트가 이미 1회분 단가다.
