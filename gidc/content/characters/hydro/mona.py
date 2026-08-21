from gidc.core.character import Character, clamp_talent_index
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import CharacterTrait, Element
from gidc.enums import StatType
from gidc.core.party_state import hexerei_rite_for
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_choice, ask_int


class Mona(Character):
    """모나 (Mona) | 물 | 법구 | 5성 | 어센션 스탯: 원소 충전 효율

    일반 공격 : 물보라로 최대 4번 공격해 물 원소 피해를 준다.
    강공격 : 일정 스태미나를 소모해, 짧은 영창 후 물 원소 범위 피해를 준다.
    낙하 공격 : 공중에서 물의 힘을 모은 후 지면을 강타해 경로상의 적을 공격하고 착지 시 물 원소 범위 피해를 준다.

    E : 수중 환원
        물보라가 모여 만든 운명의 허영.

        허영
        아래의 특성을 가진다:
        · 주변의 적을 도발하여 공격을 유도한다.
        주변의 적에게 지속해서 물 원소 피해를 준다.
        지속 시간이 끝나면 허영이 파열되면서 물 원소 범위 피해를 준다.

        홀드
        물의 흐름을 이용해 빠르게 후퇴하며 허영을 소환한다.

    Q : 별의 운명
        맑고 청아한 물결에 환상의 별하늘을 비춰 넓은 범위 내의 적을 포영 상태로 만든다.

        포영
        점성의 거품으로 적을 감싸고 습기 효과를 부여한다. 약한 적들은 거품 속에 갇혀 움직일 수 없다.
        포영 상태의 적에게 피해를 주면 아래의 효과가 발생한다:
        · 적에게 성이(星異) 피해 보너스를 부여하며 이번에 주는 피해가 증가한다.
        포영 효과가 해제되고 추가로 물 원소 피해를 1번 준다.

        성이(星異)
        지속 시간 동안 받는 피해가 증가한다.

    A1 : 「할망구, 나 잡아 봐라!」
        흐르는 허와 실 상태에 진입한 후 2초 동안 만약 주변에 적이 존재하면 자동으로 허영을 하나 만들어낸다.
        이러한 방식으로 생성된 허영은 2초 동안 지속되며 터지면서 가하는 피해는 수중 환원 피해의 50%이다.

    A4 : 「운명에 맡겨!」
        모나의 물 원소 피해 보너스가 추가로 모나 원소 충전 효율의 20%만큼 상승한다.

    마도 : 마녀의 과제 · 갈망을 완료하면, 모나가 마도 캐릭터가 된다.
          파티에 마도 캐릭터를 2명 이상 편성하면 마도 · 비밀 의식 효과를 획득해 마도 캐릭터가 강화된다.

        마도 · 비밀 의식
        모나의 일반 공격 또는 강공격이 적에게 명중 시, 「수성천의 빛」을 1스택 획득한다. 지속 시간: 8초, 최대 중첩수: 3스택.
        0.1초마다 해당 방식으로 「수성천의 빛」을 최대 1스택 획득할 수 있다.
        파티 내 자신의 다른 캐릭터가 적에게 증발 반응 발동 시, 모든 「수성천의 빛」이 소모되고,
        소모된 1스택당 이번 증발 반응으로 주는 피해가 5% 증가한다.
        또한 모나의 일반 공격 또는 강공격이 적에게 명중 시, 적의 성이 상태가 2초 연장된다.
        해당 효과는 0.5초마다 최대 1회 발동되며, 해당 방식으로 적의 성이 상태를 최대 8초 연장할 수 있다

    C1 : 성월의 연주
        파티 내 자신의 캐릭터가 성이 상태의 적을 명중하면 8초 동안 물 원소 관련 반응의 효과가 상승한다:
        · 감전 반응으로 주는 피해+15%, 달 감전 반응으로 주는 피해+15%,
        증발 반응으로 주는 피해+15%, 물 원소 확산 반응으로 주는 피해+15%
        · 빙결 반응 지속 시간+15%

        마도 강화 후 적용
        또한, 파티 내 대기 상태인 캐릭터가 상술한 효과 발동 시, 피해 증가 효과가 기존의 160%로 증가한다

    C2 : 달의 사슬
        일반 공격 명중 시 20%의 확률로 강공격을 1회 추가 발동한다.

        마도 강화 후 적용
        또한 모나가 원소폭발 별의 운명 발동 후 5초 내에 다음 일반 공격 명중시, 확정으로 강공격을 자동으로 1회 발동한다.
        상술한 자동 발동 강공격은 5초마다 1회 발동한다.
        모나의 강공격이 적에게 명중 시 주변에 있는 파티 내 모든 캐릭터의 원소 마스터리가 80pt 증가한다.

    C3 : 멈추지 않는 천상
        별의 운명의 스킬 레벨+3

    C4 : 망각의 예언
        파티 내 모든 캐릭터가 성이 상태의 적을 공격 시 치명타 확률이 15% 증가한다.

        마도 강화 후 적용
        파티 내 모든 마도 캐릭터가 성이 상태의 적을 공격 시 치명타 피해가 15% 증가한다.

    C5 : 운명의 우롱
        수중 환원의 스킬 레벨+3

    C6 : 악운의 수식
        모나가 현재 필드 위에 있고, 흐르는 허와 실 상태이거나 주변에 성이 상태의 적이 존재 시,
        1초마다 모나의 다음 강공격 피해가 60% 증가한다.
        해당 방식으로 강공격 피해가 최대 180% 획득할 수 있다. 해당 효과는 최대 8초 지속된다.

        마도 강화 후 적용
        또한 성이 상태의 적에게 모나의 강공격은 기존의 200%에 해당하는 피해를 준다
    """
    name = "모나"
    weapon_type = WeaponType.CATALYST
    # 「마녀의 과제 · 갈망」을 완료하면 마도 캐릭터가 된다 (니콜과 동일한 규칙).
    unlockable_traits = frozenset({CharacterTrait.HEXEREI})

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # 일반 공격 범람의 운명 (% ATK, L1~L11) — 물 원소, 최대 4단
    _NA = [
        [0.3760, 0.4042, 0.4324, 0.4700, 0.4982, 0.5264, 0.5640, 0.6016, 0.6392, 0.6768, 0.7144],
        [0.3600, 0.3870, 0.4140, 0.4500, 0.4770, 0.5040, 0.5400, 0.5760, 0.6120, 0.6480, 0.6840],
        [0.4480, 0.4816, 0.5152, 0.5600, 0.5936, 0.6272, 0.6720, 0.7168, 0.7616, 0.8064, 0.8512],
        [0.5616, 0.6037, 0.6458, 0.7020, 0.7441, 0.7862, 0.8424, 0.8986, 0.9547, 1.0109, 1.0670],
    ]

    # 강공격 (% ATK, L1~L11) — 스태미나 소모 50
    _CA = [1.4972, 1.6095, 1.7218, 1.8715, 1.9838, 2.0961, 2.2458, 2.3955, 2.5452, 2.6950, 2.8507]

    # 낙하 공격 (% ATK, L1~L11) — 법구 표준표가 아닌 모나 전용표(콜롬비나와 같은 값)
    _PLUNGE      = [0.5683, 0.6145, 0.6608, 0.7269, 0.7731, 0.8260, 0.8987, 0.9714, 1.0441, 1.1234, 1.2027]
    _LOW_PLUNGE  = [1.1363, 1.2288, 1.3213, 1.4535, 1.5459, 1.6517, 1.7970, 1.9423, 2.0877, 2.2462, 2.4048]
    _HIGH_PLUNGE = [1.4193, 1.5349, 1.6504, 1.8154, 1.9310, 2.0630, 2.2445, 2.4261, 2.6076, 2.8057, 3.0037]

    # ── 원소 스킬 수중 환원 (% ATK, L1~L14, C5 적용 시 최대 L13) ────────────────
    # CD 12초
    _SKILL_DOT = [   # 허영 지속 피해 (1회분)
        0.3200, 0.3440, 0.3680, 0.4000, 0.4240, 0.4480, 0.4800,
        0.5120, 0.5440, 0.5760, 0.6080, 0.6400, 0.6800, 0.7200,
    ]
    _SKILL_EXPLOSION = [  # 지속 시간 종료 시 허영 파열 피해
        1.3280, 1.4276, 1.5272, 1.6600, 1.7596, 1.8592, 1.9920,
        2.1248, 2.2576, 2.3904, 2.5232, 2.6560, 2.8220, 2.9880,
    ]

    # ── 원소 폭발 별의 운명 (% ATK, L1~L14, C3 적용 시 최대 L13) ────────────────
    # 포영 지속 8초, CD 15초, 원소 에너지 60
    _BURST_BUBBLE_EXPLOSION = [  # 포영 파열 피해
        4.4240, 4.7558, 5.0876, 5.5300, 5.8618, 6.1936, 6.6360,
        7.0784, 7.5208, 7.9632, 8.4056, 8.8480, 9.4010, 9.9500,
    ]
    # 「성이」 — 대상이 받는 피해 증가 (L1~L14). 지속 4s / 4.5s / 5s (레벨 구간별)
    _OMEN_DMG_BONUS = [
        0.42, 0.44, 0.46, 0.48, 0.50, 0.52, 0.54,
        0.56, 0.58, 0.60, 0.60, 0.60, 0.60, 0.60,
    ]

    # ── 명함 / 특성 상수 ────────────────────────────────────────────────────
    # A1 : 자동 생성된 허영의 파열 피해는 수중 환원 피해의 50%
    _A1_PHANTOM_DMG_RATIO = 0.50
    # A4 : 원소 충전 효율 → 물 원소 피해 보너스 전환 비율
    _A4_ER_TO_HYDRO_DMG = 0.20
    # 마도·비밀 의식 : 「수성천의 빛」 1스택당 증발 반응 피해 증가 / 최대 스택
    _HEXEREI_VAPORIZE_PER_STACK = 0.05
    _HEXEREI_MAX_STACKS         = 3
    # C1 : 성이 상태의 적 대상 물 관련 반응 강화 / 마도 강화 시 배율
    _C1_REACTION_BONUS   = 0.15
    _C1_HEXEREI_MULT     = 1.60
    # C2 : 마도 강화 후 강공격 명중 시 파티 전원 원소 마스터리 증가
    _C2_HEXEREI_EM       = 80
    # C4 : 성이 상태의 적 공격 시 치명타 확률 / 마도 캐릭터 치명타 피해
    _C4_CRIT_RATE        = 0.15
    _C4_HEXEREI_CRIT_DMG = 0.15
    # C6 : 1초당 강공격 피해 증가 / 상한 / 마도 강화 시 강공격 계수 배율
    _C6_CA_DMG_PER_SEC   = 0.60
    _C6_CA_DMG_CAP       = 1.80
    _C6_MAX_STACKS       = 3      # 60% × 3 = 180% (상한)
    _C6_HEXEREI_CA_MULT  = 2.00
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 5
    BURST_LEVEL_UP_CONSTELLATION = 3
    NA_TABLES = (*_NA, _CA, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_DOT, _SKILL_EXPLOSION,)
    BURST_TABLES = (_BURST_BUBBLE_EXPLOSION, _OMEN_DMG_BONUS,)

    rarity         = 5
    ascension_stat = StatType.ENERGY_RECHARGE

    @property
    def element(self)  -> Element: return Element.HYDRO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        c = self.constellation

        # C5: 원소 스킬 레벨 +3 (최대 13)
        sk = self._skill_index()
        # C3: 원소 폭발 레벨 +3 (최대 13)
        bl = self._burst_index()
        nl = self._na_index()

        hits: list[SkillHit] = []

        # 법구 캐릭터라 일반/강/낙하 공격도 모두 물 원소 피해다 (니콜·콜롬비나와 동일)
        for i, row in enumerate(self._NA):
            hits.append(SkillHit(f"{i+1}단 공격 피해", SkillType.NORMAL_ATK, row[nl],
                                 ScalingStat.ATK, Element.HYDRO))

        hits.append(SkillHit("강공격 피해", SkillType.CHARGED_ATK, self._CA[nl],
                             ScalingStat.ATK, Element.HYDRO))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK, Element.HYDRO))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK, Element.HYDRO))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK, Element.HYDRO))

        hits.append(SkillHit("허영 지속 피해", SkillType.SKILL, self._SKILL_DOT[sk],
                             ScalingStat.ATK, Element.HYDRO))
        hits.append(SkillHit("허영 파열 피해", SkillType.SKILL, self._SKILL_EXPLOSION[sk],
                             ScalingStat.ATK, Element.HYDRO))

        # A1: 흐르는 허와 실 진입 시 자동 생성되는 허영. 파열 피해가 수중 환원의 50%라
        # 같은 계수에 coeff_amp로 비율을 걸어 두 히트의 관계를 드러낸다.
        hits.append(SkillHit("A1 허영 파열 피해", SkillType.SKILL, self._SKILL_EXPLOSION[sk],
                             ScalingStat.ATK, Element.HYDRO,
                             coeff_amp=self._A1_PHANTOM_DMG_RATIO))

        hits.append(SkillHit("포영 파열 피해", SkillType.BURST, self._BURST_BUBBLE_EXPLOSION[bl],
                             ScalingStat.ATK, Element.HYDRO))

        return {h.name: h for h in hits}

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        # C6 「악운의 수식」: 1초마다 다음 강공격 피해 +60%, 최대 180%.
        # 파티 구성과 무관한 자기 버프라 Phase 3에서 처리한다.
        # (마도 강화 분기는 파티 판정이 필요해 apply_party_buffs로 나뉘어 있다.)
        if self.constellation >= 6:
            stacks = ask_int("[모나 C6] 강공격 피해 증가 스택 (1스택=60%)",
                             min_val=0, max_val=self._C6_MAX_STACKS)
            if stacks:
                bonus = min(self._C6_CA_DMG_PER_SEC * stacks, self._C6_CA_DMG_CAP)
                for hit in hits.values():
                    hit.add("charged_atk_dmg_bonus", bonus, self, note="C6 악운의 수식")

        # C2 「달의 사슬」 기본 효과(일반 공격 명중 시 20% 확률로 강공격 1회 추가 발동)와
        # 마도 강화의 자동 강공격은 발동 '횟수'를 바꿀 뿐 히트당 피해를 바꾸지 않는다.
        # 로테이션 모델이 없는 계산기라 콜롬비나 A4와 같은 방침으로 미반영한다.

    # ── 파티 버프 4: 코어 스탯 기여 + 유저 입력 수집 ─────────────────────────
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # 파티 편성으로 결정되므로 묻지 않는다 (모나 본인이 마도 + 파티 마도 2명 이상).
        self._hexerei_rite = hexerei_rite_for(self, all_hits)

        # 성이 활성 여부 — Q·C1·C4·C6 마도 분기가 모두 이 조건에 걸려 있어 한 번만 묻는다.
        self._omen_active = ask_bool("[모나 Q] 「성이」 효과 활성 여부")

        # C1 마도 강화는 '대기 상태인 캐릭터'만 160%를 받으므로 필드 위 캐릭터를 알아야 한다.
        self._on_field = (
            self._ask_on_field_member(all_hits)
            if self._omen_active and self._hexerei_rite and c >= 1 else None
        )

        # 마도·비밀 의식 「수성천의 빛」 — 소모 스택 수만큼 다른 캐릭터의 증발 반응이 강해진다.
        self._starlight_stacks = (
            ask_int("[모나 마도] 소모한 「수성천의 빛」 스택 수",
                    min_val=0, max_val=self._HEXEREI_MAX_STACKS)
            if self._hexerei_rite else 0
        )

        # C2 마도 강화: 강공격 명중 시 파티 전원 원소 마스터리 +80.
        # 고정값 코어 풀 기여라 이 단계(Phase 4)가 제자리다. 다른 캐릭터 스탯의 %가
        # 아니므로 em_from_pct_share 꼬리표는 달지 않는다.
        if (c >= 2 and self._hexerei_rite
                and ask_bool("[모나 C2] 강공격 명중 후 원소 마스터리 증가 유지 여부")):
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.add("em_from_flat", self._C2_HEXEREI_EM, self, note="C2 마도 강화")

    def _ask_on_field_member(self, all_hits):
        """C1 마도 강화 분기에서 '대기 상태'를 가려내기 위한 현재 필드 위 캐릭터.
        파티원이 1명뿐이면 묻지 않는다 (콜롬비나와 동일한 패턴)."""
        members = list(all_hits.keys())
        if len(members) == 1:
            return members[0]
        options = [
            f"{char.name} ({char.element.value})" + (" ← 모나" if char is self else "")
            for char in members
        ]
        return members[ask_choice("[모나 C1] 현재 필드 위 캐릭터", options)]

    # ── 파티 버프 4.5: 스탯을 읽지 않는 크로스 버프 ─────────────────────────
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # 마도·비밀 의식 「수성천의 빛」: 「자신의 **다른** 캐릭터」의 증발 반응만 강화한다.
        # 성이와 무관하게 발동하므로 성이 분기 밖에 둔다.
        if self._starlight_stacks:
            bonus = self._HEXEREI_VAPORIZE_PER_STACK * self._starlight_stacks
            for char, char_hits in all_hits.items():
                if char is self:
                    continue
                for hit in char_hits.values():
                    hit.add("vaporize_bonus", bonus, self, note="마도·비밀 의식")

        if not self._omen_active:
            return

        bl = self._burst_index()
        omen = self._OMEN_DMG_BONUS[bl]

        for char, char_hits in all_hits.items():
            # C1 마도 강화: 대기 상태(= 필드 위가 아닌) 캐릭터는 반응 증가량이 160%가 된다.
            c1_bonus = self._C1_REACTION_BONUS
            if self._hexerei_rite and char is not self._on_field:
                c1_bonus *= self._C1_HEXEREI_MULT

            for hit in char_hits.values():
                # 성이: 받는 피해 증가. 게임에서 다른 피해 보너스와 합산되는 계열이므로
                # all_dmg_bonus에 그대로 가산한다 (근사가 아니라 실제 계산 방식).
                hit.add("all_dmg_bonus", omen, self, note="Q 성이")

                # C1 「성월의 연주」: 물 원소 관련 반응 강화.
                # 빙결 지속 시간 +15%는 피해식에 들어가지 않으므로 미구현.
                if c >= 1:
                    hit.add("electrocharged_bonus", c1_bonus, self, note="C1 성월의 연주")
                    hit.add("lunar_charged_bonus",  c1_bonus, self, note="C1 성월의 연주")
                    hit.add("vaporize_bonus",       c1_bonus, self, note="C1 성월의 연주")
                    hit.add("swirl_bonus",          c1_bonus, self, note="C1 성월의 연주")

                # C4 「망각의 예언」: 파티 전원 치명타 확률 +15%,
                # 마도 강화 후에는 마도 캐릭터에 한해 치명타 피해 +15%가 추가된다.
                if c >= 4:
                    hit.add("crit_rate", self._C4_CRIT_RATE, self, note="C4 망각의 예언")
                    if self._hexerei_rite and char.has_trait(CharacterTrait.HEXEREI):
                        hit.add("crit_dmg", self._C4_HEXEREI_CRIT_DMG, self, note="C4 마도 강화")

        # C6 마도 강화: 성이 상태의 적 대상 모나의 강공격은 기존의 200% 피해.
        # 계수 증폭이라 코어 풀도 스탯 스케일도 아니므로 이 단계에서 처리한다.
        if c >= 6 and self._hexerei_rite:
            all_hits[self]["강공격 피해"].coeff_amp += self._C6_HEXEREI_CA_MULT - 1

    # ── 파티 버프 5: 최종 스탯을 읽어 스케일하는 버프 (방식 B) ────────────────
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # A4 「운명에 맡겨!」: 자신의 원소 충전 효율 20%만큼 물 원소 피해 보너스 증가.
        # 성유물·무기·베넷 C2 등이 모두 반영된 최종 ER을 읽어야 하므로 Phase 5에서 처리한다.
        # 출력이 hydro_dmg_bonus라 코어 풀을 건드리지 않아 정확성 가드에 걸리지 않는다.
        # 값이 아니라 **읽는 함수**로 넘긴다(지연 기여) — 다른 캐릭터가 Phase 5에서
        # 원소 충전 효율을 더해 줄 수도 있어 지금 확정하면 순서에 좌우된다.
        for hit in all_hits[self].values():
            hit.add("hydro_dmg_bonus",
                    lambda h=hit: h.energy_recharge * self._A4_ER_TO_HYDRO_DMG,
                    self, note="A4 운명에 맡겨!")
