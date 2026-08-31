from gidc.core.character import Character
from gidc.core.party_state import moonsign_level
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import CharacterTrait, Element, MoonsignLevel
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_choice


class Aino(Character):
    """아이노 (Aino) | 물 | 양손검 | 4성 | 어센션 스탯: 원소 마스터리

    일반 공격
    대검으로 최대 3번 공격한다.

    강공격
    스태미나를 지속적으로 소모해 대검을 휘둘러 주변의 적을 공격한다.
    회전 종료 시 추가로 한 번 더 강력하게 휘두른다.

    낙하 공격
    공중에서 땅을 내려찍어 경로상의 적을 공격하고 착지 시 범위 피해를 준다.

    E : 아이디어 집게
    전방으로 「아이디어 집게」를 던져 물 원소 피해를 주고, 자신을 앞으로 끌어당긴다. 이동 종료 시, 주변의 적에게 물 원소 범위 피해를 준다.
    홀드 시 다른 방식으로 발동한다.

    홀드
    조준 상태에 진입해 「아이디어 집게」의 방향을 결정한다

    Q : 정밀 냉수기
    특제 슈퍼 분사 장치 「찬물 오리」를 발사해 냉수 구역을 펼친다.
    지속 시간 동안 「찬물 오리」는 간헐적으로 주변의 적에게 물폭탄을 발사해 물 원소 피해를 준다

    A1 : 모듈화 전략
    파티의 달빛 징조에 따라 아이노가 상응하는 강화 효과를 획득한다.

    달빛 징조 · 보름: 원소폭발 정밀 냉수기가 강화되어 「찬물 오리」의 물폭탄 발사 간격이 감소하고, 범위가 더 큰 물 원소 범위 피해를 준다.

    A4 : 출력 강화 시스템
    아이노의 원소폭발로 주는 피해가 아이노 원소 마스터리의 50%만큼 증가한다

    C1 : 먼지와 역장의 평행이론
    아이노가 아이디어 집게 또는 원소폭발 정밀 냉수기 발동 후, 아이노 자신의 원소 마스터리가 80pt 증가하고 주변의 현재 필드 위 다른 캐릭터의 원소 마스터리가 80pt 증가한다, 지속 시간: 15초.

    해당 운명의 자리로 획득한 원소 마스터리 증가 효과는 중첩되지 않는다

    C2 : 톱니바퀴 차분기관의 계산 원리
    원소폭발 정밀 냉수기의 냉수 구역 지속 시간 동안 아이노가 대기 상태일 경우: 현재 필드 위에 있는 파티 내 자신의 캐릭터의 공격이 주변에 있는 적에게 명중 시, 「찬물 오리」가 해당 적에게 추가로 물폭탄을 1개 발사해 아이노 공격력의 25%와 원소 마스터리의 100%에 해당하는 물 원소 범위 피해를 준다. 해당 효과는 5초마다 최대 1회 발동되고, 주는 피해는 원소폭발 피해로 간주한다

    C3 : 케이크와 장치 수리의 예술
    원소폭발 정밀 냉수기의 스킬 레벨+3
    최대 Lv.15까지 상승

    C4 : 버터와 고양이의 에너지 법칙
    원소전투 스킬 아이디어 집게가 적에게 명중 시, 아이노의 원소 에너지가 10pt 회복된다. 해당 방식으로 원소 에너지를 10초마다 최대 1회 회복할 수 있다

    C5 : 금속과 빛의 영구 터빈
    원소전투 스킬 아이디어 집게의 스킬 레벨+3
    최대 Lv.15까지 상승

    C6 : 발명은 천재의 의무
    원소폭발 정밀 냉수기 발동 후 15초 동안 주변에 있는 현재 필드 위 캐릭터가 발동한 감전, 개화, 달 감전, 달 개화, 달 결정 반응으로 주는 피해가 15% 증가한다.
    달빛 징조 · 보름: 상술한 반응으로 주는 피해가 추가로 20% 증가한다

    달빛 징조의 축복 · 전력 연산
    아이노가 파티에 있을 경우 파티의 달빛 징조가 1레벨 상승한다
    """
    name = "아이노"
    weapon_type = WeaponType.CLAYMORE
    innate_traits = frozenset({CharacterTrait.MOONSIGN})

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # ── 일반공격 (L1~L11) ──
    # 대검 3단. 3단은 같은 계수로 2타 — 히트는 build_hits에서 두 개 세운다.
    _NA1 = [0.665, 0.719, 0.773, 0.851, 0.905, 0.967, 1.052, 1.137, 1.222, 1.315, 1.407]
    _NA2 = [0.662, 0.716,  0.77, 0.847, 0.901, 0.962, 1.047, 1.131, 1.216, 1.308, 1.401]
    _NA3 = [0.492, 0.532, 0.572,  0.63,  0.67, 0.715, 0.778, 0.841, 0.904, 0.973, 1.042]
    _CA_SPIN = [0.6252, 0.6761, 0.7270, 0.7997, 0.8506, 0.9087, 0.9887, 1.0687, 1.1487, 1.2359, 1.3231]
    _CA_ENDING = [1.1309, 1.2229, 1.3150, 1.4465, 1.5386, 1.6437, 1.7884, 1.9331, 2.0777, 2.2355, 2.3933]
    _PLUNGE = [0.7459, 0.8066, 0.8673, 0.9540, 1.0147, 1.0841, 1.1795, 1.2749, 1.3703, 1.4744, 1.5785]
    _LOW_PLUNGE = [1.4914, 1.6128, 1.7342, 1.9077, 2.0291, 2.1678, 2.3586, 2.5493, 2.7401, 2.9482, 3.1563]
    _HIGH_PLUNGE = [1.8629, 2.0145, 2.1662, 2.3828, 2.5344, 2.7077, 2.9460, 3.1842, 3.4225, 3.6825, 3.9424]

    # ── 원소스킬 (L1~L13) ──
    # 던지는 순간의 피해
    _SKILL_THROW_DMG = [
        0.656, 0.705, 0.754,  0.82, 0.869,
        0.918, 0.984,  1.05, 1.115, 1.181,
        1.246, 1.312, 1.394,
    ]
    # 끌어당겨 이동을 마칠 때의 범위 피해
    _SKILL_LANDING_DMG = [
        1.888,  2.03, 2.171,  2.36, 2.502,
        2.643, 2.832, 3.021,  3.21, 3.398,
        3.587, 3.776, 4.012,
    ]

    # ── 원소폭발 (L1~L13) ──
    # 「찬물 오리」가 간헐적으로 쏘는 물폭탄 1발
    _BURST_WATERBOMB_DMG = [
        0.201, 0.216, 0.231, 0.251, 0.266,
        0.282, 0.302, 0.322, 0.342, 0.362,
        0.382, 0.402, 0.427,
    ]

    # ── 상수 (레벨로 스케일하지 않는 값) ──
    _A4_BURST_DMG_FROM_EM    = 0.50   # A4 출력 강화 시스템 — 아이노의 원소폭발 피해가 아이노 원소 마스터리의 50%만큼 증가
    _C1_EM_FLAT              = 80     # C1 먼지와 역장의 평행이론 — 아이노 자신 + 현재 필드 위 다른 캐릭터의 원소 마스터리 (비중첩)
    _C2_ATK_RATIO            = 0.25   # C2 톱니바퀴 차분기관의 계산 원리 — 추가 물폭탄 1발 (5초당 최대 1회, 원소폭발 피해로 간주)
    _C2_EM_RATIO             = 1.00
    _C6_REACTION_BONUS       = 0.15   # C6 발명은 천재의 의무 — 감전·개화·달감전·달개화·달결정 피해 증가
    _C6_FULLMOON_EXTRA_BONUS = 0.20
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 5
    BURST_LEVEL_UP_CONSTELLATION = 3
    NA_TABLES = (_NA1, _NA2, _NA3, _CA_SPIN, _CA_ENDING, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_THROW_DMG, _SKILL_LANDING_DMG,)
    BURST_TABLES = (_BURST_WATERBOMB_DMG,)

    rarity         = 4
    ascension_stat = StatType.ELEMENTAL_MASTERY

    @property
    def element(self) -> Element: return Element.HYDRO

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
        for i in (1, 2):
            hits.append(SkillHit(f"3단 공격 피해 {i}타", SkillType.NORMAL_ATK, self._NA3[nl], ScalingStat.ATK))
        hits.append(SkillHit("강공격 순환 피해", SkillType.CHARGED_ATK, self._CA_SPIN[nl], ScalingStat.ATK))
        hits.append(SkillHit("강공격 종결 피해", SkillType.CHARGED_ATK, self._CA_ENDING[nl], ScalingStat.ATK))
        hits.append(SkillHit("낙하 기간 피해", SkillType.PLUNGING, self._PLUNGE[nl], ScalingStat.ATK))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl], ScalingStat.ATK))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK))

        # 원소스킬
        hits.append(SkillHit("원소 스킬 1단 피해", SkillType.SKILL, self._SKILL_THROW_DMG[sk], ScalingStat.ATK, Element.HYDRO))
        hits.append(SkillHit("원소 스킬 2단 피해", SkillType.SKILL, self._SKILL_LANDING_DMG[sk], ScalingStat.ATK, Element.HYDRO))

        # 원소폭발
        hits.append(SkillHit("물폭탄 피해", SkillType.BURST, self._BURST_WATERBOMB_DMG[bl], ScalingStat.ATK, Element.HYDRO))

        # C2 : 필드 위 캐릭터의 공격이 명중할 때 「찬물 오리」가 쏘는 추가 물폭탄 (5초당 1회).
        # 「아이노 공격력의 25%와 원소 마스터리의 100%」 — 스케일 스탯이 둘이라 계수를
        # 스탯 쪽(stat_fn)에 담고 coeff=1.0으로 둔다. 히트를 둘로 쪼개지 않는 이유는
        # 치명타가 히트 단위로 굴러가기 때문이다(쪼개면 한쪽만 크리가 터진다).
        # 「주는 피해는 원소폭발 피해로 간주」되므로 SkillType.BURST — A4도 여기에 걸린다.
        # 계수가 특성 레벨로 스케일하지 않는 상수라 표가 아니다.
        if c >= 2:
            hits.append(SkillHit(
                "C2 추가 물폭탄 피해", SkillType.BURST, 1.0, ScalingStat.ATK, Element.HYDRO,
                stat_fn=self._c2_waterbomb_stat,
            ))

        return {h.name: h for h in hits}

    def _c2_waterbomb_stat(self, hit: SkillHit) -> float:
        """C2 물폭탄의 스탯 자리 — 아이노 공격력 25% + 원소 마스터리 100%."""
        return (hit.current_atk() * self._C2_ATK_RATIO
                + hit.elemental_mastery * self._C2_EM_RATIO)

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        # C1 먼지와 역장의 평행이론 — 아이노 자신의 원소 마스터리 +80.
        # 트리거(E 또는 Q)를 묻는 것은 여기서 한 번뿐이고, 「필드 위 다른 캐릭터」 몫은
        # 파티를 봐야 해서 Phase 4에서 같은 답을 재사용한다.
        # 고정 수치로 부여된 EM이라 em_from_pct_share가 아니라 em_from_flat이다 —
        # EM을 다시 %로 변환하는 버프(카즈하 등)가 이 몫을 재료로 쓰는 것이 맞다.
        self._c1_active = (
            self.constellation >= 1
            and ask_bool("[아이노 C1] 아이디어 집게 또는 원소폭발 발동 여부")
        )
        if self._c1_active:
            for hit in hits.values():
                hit.add("em_from_flat", self._C1_EM_FLAT, self, note="C1 평행이론")

    # ── 파티 버프 4: 코어 스탯 기여 + 유저 입력 수집 ─────────────────────────
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # C6은 냉수 구역(= 원소폭발)이 조건이다. C1은 E로도 켜지므로 답을 공유하지 않는다.
        self._burst_active = (c >= 6) and ask_bool("[아이노 Q] 냉수 구역 전개 여부 (C6)")

        # 「현재 필드 위 캐릭터」는 C1과 C6이 함께 쓴다 — 한 번만 묻는다.
        # 파티 전원에게 걸면 부풀려지므로 1명만 고르게 한다.
        self._on_field = (
            self._ask_on_field_member(all_hits)
            if (self._c1_active or self._burst_active) else None
        )

        # C1의 「현재 필드 위 **다른** 캐릭터」 몫. 필드 위가 아이노 자신이면 대상이 없다
        # (자기 몫은 Phase 3에서 이미 넣었고, 「중첩되지 않는다」는 문구대로 두 번 넣지 않는다).
        if self._c1_active and self._on_field is not None and self._on_field is not self:
            for hit in all_hits[self._on_field].values():
                hit.add("em_from_flat", self._C1_EM_FLAT, self, note="C1 평행이론")

    def _ask_on_field_member(self, all_hits):
        """C1·C6이 함께 쓰는 현재 필드 위 캐릭터. 파티원이 1명뿐이면 묻지 않는다."""
        members = list(all_hits.keys())
        if len(members) == 1:
            return members[0]
        options = [
            f"{char.name} ({char.element.value})" + (" ← 아이노" if char is self else "")
            for char in members
        ]
        return members[ask_choice("[아이노] 현재 필드 위 캐릭터", options)]

    # ── 파티 버프 4.5: 스탯을 읽지 않는 크로스 버프 ─────────────────────────
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # C6 발명은 천재의 의무 — 필드 위 캐릭터가 발동한 반응 5종의 피해 증가.
        # 반응을 발동하는 것은 필드 위 캐릭터 1명이므로 그 사람의 히트에만 건다.
        if not self._burst_active or self._on_field is None:
            return

        bonus = self._C6_REACTION_BONUS
        if moonsign_level(all_hits) is MoonsignLevel.FULL:
            bonus += self._C6_FULLMOON_EXTRA_BONUS

        # 원문이 반응 5종을 이름으로 꼽으므로 다섯 자리에 각각 적는다. 계열 공통 슬롯은
        # 없다 — 반응별로 나뉘어 있어야 「달 결정만」 올리는 버프가 새지 않는다.
        for field in ("electrocharged_bonus", "bloom_bonus",
                      "lunar_charged_bonus", "lunar_bloom_bonus", "lunar_crystallize_bonus"):
            for hit in all_hits[self._on_field].values():
                hit.add(field, bonus, self, note="C6 발명은 천재의 의무")

    # ── 파티 버프 5: 최종 스탯을 읽어 스케일하는 버프 (방식 B) ────────────────
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # A4 출력 강화 시스템 — 아이노의 원소폭발 피해가 자기 원소 마스터리의 50%만큼 증가.
        # EM을 **피해 차원으로** 바꿔 내보내므로 flat_dmg_bonus다. EM 슬롯으로 되먹이면
        # 자기 참조 순환이 된다.
        #
        # 값이 아니라 **읽는 함수**로 넘긴다(지연 기여) — 같은 단계에서 다른 캐릭터가
        # 아이노의 EM을 올릴 수 있어(시틀라리·설탕) 지금 확정하면 파티 멤버 순서가
        # 결과를 바꾼다. 항상 같은 히트(첫 히트)를 읽으므로 언제 계산되든 값은 같다.
        #
        # 재료로 elemental_mastery(합계)를 읽는다 — EM을 다시 %로 변환하는 버프가 아니라
        # 피해에 직접 더하는 고정값이라 파생 지분까지 재료가 되는 것이 맞다.
        source_hit = next(iter(all_hits[self].values()))
        bonus = lambda: source_hit.elemental_mastery * self._A4_BURST_DMG_FROM_EM
        for hit in all_hits[self].values():
            if hit.skill_type is SkillType.BURST:
                hit.add("flat_dmg_bonus", bonus, self, note="A4 출력 강화 시스템")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · A1 「모듈화 전략」 보름 — 물폭탄 **발사 간격 감소**와 **범위 확대**뿐이다. 계수가
    #   바뀌지 않아 히트 단가에 들어갈 항이 없다(발사 횟수는 로테이션 빈도다).
    # · C2의 「5초마다 최대 1회」와 「아이노가 대기 상태」 조건 — 빈도·필드 배치라 히트를
    #   세워 두기만 하고 몇 번 터지는지는 화면을 읽는 쪽에 맡긴다.
    # · C4 원소 에너지 10pt (10초당 1회) — 자원 모델이 없다.
    # · E 홀드(조준) — 방향만 정하고 계수가 짧은 터치와 같다. 별도 히트를 세우지 않는다.
    # · Q 냉수 구역의 지속 시간·물폭탄 발사 횟수 — 로테이션 서술이지 히트 단가가 아니다.
