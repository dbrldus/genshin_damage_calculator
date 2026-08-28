from gidc.core.character import Character
from gidc.core.party_state import hexerei_rite_for
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import CharacterTrait, Element
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_choice


class Fischl(Character):
    """피슬 (Fischl) | 번개 | 활 | 4성 | 어센션 스탯: 공격력%

    일반 공격 : 활로 최대 5번 공격한다.
    강공격 : 피해가 더 크고 정확한 조준 사격을 한다.
    조준 시 유야정토의 검은 번개 정령이 황녀의 명령을 받아 그녀의 뇌영 화살에 깃든다. 단죄의 번개의 힘이 가득 찬 마법 화살은 강력한 번개 원소 피해를 준다.
    낙하 공격 : 공중에서 화살비를 쏜 후 빠른 속도로 땅에 착지한다. 착지 시 범위 피해를 준다.

    E : 밤을 순찰하는 그림자 날개
    오즈를 소환한다. 암영과 뇌전으로 구성된 레이븐이 속세에 강림할 때 작은 범위 내의 적에게 번개 원소 피해를 준다.
    오즈는 존재하는 동안 번개 에너지 탄을 발사하여 주변의 적을 공격한다.
    홀드하여 오즈의 위치를 조정할 수 있다.
    오즈가 존재하는 동안 다시 한번 짧게 누르면 오즈를 자신의 주변으로 소환할 수 있다.

    Q : 암야의 환
    오즈를 소환해 칠흑으로 엮은 두 날개로 피슬을 보호한다.
    지속하는 동안 아래의 효과를 가진다:
    · 오즈의 형태로 변해 고속 이동한다.
    · 주변의 적에게 번개를 떨어트려 번개 원소 피해를 준다. 적 1명마다 낙뢰 피해를 1번만 받는다.
    · 효과 종료 시 오즈는 필드에 머물러 황녀의 적을 공격한다. 만약 오즈가 필드에 있으면 오즈의 존재 시간이 초기화된다.

    A1 : 별을 삼킨 까마귀
    피슬이 차지 완료된 화살로 오즈를 명중하면 오즈가 주변의 적에게 신성한 번개를 내리고 사격 피해의 152.7%에 달하는 번개 원소 범위 피해를 준다.

    A4 : 단죄의 뇌영
    오즈가 필드에 존재 시 현재 필드 위에 있는 자신의 캐릭터가 적을 공격하여 번개 원소 관련 반응이 발동되었다면 적에게 신성한 번개를 내려 피슬 공격력 80%의 번개 원소 피해를 준다.

    C1 : 그윽한 까마귀 눈
    오즈가 필드에 존재하지 않을 때는 까마귀 눈으로 피슬을 지켜준다. 피슬이 적에게 일반 공격을 가할 시 오즈는 까마귀 눈을 통해 함께 공격해 공격력 22%의 피해를 준다.

    C2 : 신성한 판결의 그림자 깃털
    밤을 순찰하는 그림자 날개 발동 시 추가적으로 공격력 200%의 피해를 주고 영향 범위가 50% 확대된다.

    C3 : 심연색의 검은 날개
    밤을 순찰하는 그림자 날개의 스킬 레벨+3
    최대 Lv.15까지 상승

    C4 : 황녀의 환상 이야기
    암야의 환상 발동 시 주변의 적에게 공격력 222%의 번개 원소 피해를 준다.
    스킬 효과가 사라지면 피슬의 HP를 20% 회복한다.

    C5 : 암야 묵시록
    암야의 환상의 스킬 레벨+3
    최대 Lv.15까지 상승

    C6 : 영야의 금수
    오즈의 존재 시간을 2초 연장한다. 또한 오즈가 현재 필드 위에 있는 자신의 캐릭터와 함께 공격하여 피슬 공격력 30%의 번개 원소 피해를 준다.
    오즈가 협동 공격을 진행한 후, 마녀의 전야제ㆍ유야의 환상곡의 공격력과 원소 마스터리 증가 효과가 100% 증가한다. 지속시간: 10초

    마녀의 전야제 · 유야의 환상곡
    마녀의 과제 · 의외를 완료하면, 피슬이 마도 캐릭터가 된다. 파티에 마도 캐릭터를 2명 이상 편성하면 마도 · 비밀 의식 효과를 획득해 마도 캐릭터가 강화된다.

    마도 · 비밀 의식
    오즈가 필드 위에 있을 시 파티 내 캐릭터가 추가 강화 효과를 획득한다:
    주변에 있는 파티 내 캐릭터가 과부하 반응 발동 후 10초 동안 피슬과 주변에 있는 파티 내 현재 필드 위 다른 캐릭터의 공격력이 22.5% 증가한다.
    주변에 있는 파티 내 캐릭터가 감전 또는 달 감전 반응 발동 후 10초 동안 피슬과 주변에 있는 파티 내 현재 필드 위 다른 캐릭터의 원소 마스터리가 90pt 증가한다.
    """
    name = "피슬"
    weapon_type = WeaponType.BOW

    # 「마녀의 과제 · 의외」를 완료해야 마도 캐릭터가 된다 — 설탕·모나·니콜과 같은 규약으로
    # 빌드 설정에서 unlock_trait()으로 켠다. 켜지 않으면 파티의 마도 정원에도 들어가지 않고
    # 마도·비밀 의식 효과를 내놓지도 받지도 않는다(core/party_state.hexerei_rite_for).
    unlockable_traits = frozenset({CharacterTrait.HEXEREI})

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # ── 일반공격 (L1~L15) ──
    # 일반 공격 — 활로 최대 5번 (물리)
    _NA = [
        [0.441, 0.477, 0.513, 0.564, 0.600, 0.641, 0.698, 0.754, 0.811, 0.872, 0.934, 0.995,  1.06,  1.12,  1.18],
        [0.468, 0.505, 0.544, 0.598, 0.636, 0.680, 0.740, 0.800, 0.860, 0.925, 0.990,  1.06,  1.12,  1.19,  1.25],
        [0.581, 0.629, 0.676, 0.744, 0.791, 0.845, 0.919, 0.994,  1.07,  1.15,  1.23,  1.31,  1.39,  1.47,  1.55],
        [0.577, 0.624, 0.671, 0.738, 0.785, 0.839, 0.913, 0.986,  1.06,  1.14,  1.22,  1.30,  1.38,  1.46,  1.54],
        [0.721, 0.779, 0.838, 0.922, 0.980,  1.05,  1.14,  1.23,  1.32,  1.42,  1.53,  1.63,  1.73,  1.83,  1.93],
    ]
    # 조준 사격 — 미차지는 물리, 풀차지는 번개(활 공통 규칙)
    _AIMED = [
        0.4390, 0.4740, 0.5100, 0.5610, 0.5970,
        0.6380, 0.6940, 0.7500, 0.8060, 0.8670,
        0.9280, 0.9890, 1.0510, 1.1120, 1.1730,
    ]
    _AIMED_FULL = [1.24, 1.33, 1.43, 1.55, 1.64, 1.74, 1.86, 1.98, 2.11, 2.23, 2.36, 2.48, 2.64, 2.79, 2.95]
    _PLUNGE = [
        0.5680, 0.6150, 0.6610, 0.7270, 0.7730,
        0.8260, 0.8990, 0.9710,   1.04, 1.1230,
        1.2030, 1.2820, 1.3610, 1.4410,   1.52,
    ]
    _LOW_PLUNGE = [1.14, 1.23, 1.32, 1.45, 1.55, 1.65, 1.80, 1.94, 2.09, 2.25, 2.40, 2.56, 2.72, 2.88, 3.04]
    _HIGH_PLUNGE = [1.42, 1.53, 1.65, 1.82, 1.93, 2.06, 2.24, 2.43, 2.61, 2.81, 3.00, 3.20, 3.40, 3.60, 3.80]

    # ── 원소스킬 (L1~L15) ──
    # 로테이션에 몇 발이 들어가는지는 화면을 읽는 쪽이 정한다.
    _SKILL_OZ_ATK = [
        0.8880, 0.9550,   1.02,   1.11,   1.18,
          1.24,   1.33,   1.42,   1.51,   1.60,
          1.69,   1.78,   1.89,   2.00,   2.11,
    ]
    # 오즈 강림 순간의 범위 피해
    _SKILL_SUMMON = [1.15, 1.24, 1.33, 1.44, 1.53, 1.62, 1.73, 1.85, 1.96, 2.08, 2.19, 2.31, 2.45, 2.60, 2.74]

    # ── 원소폭발 (L1~L15) ──
    # 적 1명당 1회만 맞는다
    _BURST_LIGHTNING = [
        2.08, 2.24, 2.39, 2.60, 2.76,
        2.91, 3.12, 3.33, 3.54, 3.74,
        3.95, 4.16, 4.42, 4.68, 4.94,
    ]

    # ── 상수 (레벨로 스케일하지 않는 값) ──
    _A1_AIMED_MULT    = 1.527   # A1 별을 삼킨 까마귀 — 사격 피해의 152.7%
    _A4_DMG           = 0.80    # A4 단죄의 뇌영 — 피슬 공격력의 80%
    _C1_DMG           = 0.22    # C1 그윽한 까마귀 눈 — 공격력의 22%
    _C2_DMG           = 2.00    # C2 신성한 판결의 그림자 깃털 — 공격력의 200%
    _C4_DMG           = 2.22    # C4 황녀의 환상 이야기 — 공격력의 222%
    _C6_DMG           = 0.30    # C6 영야의 금수 — 오즈 협동 공격, 공격력의 30%
    _HEXEREI_ATK_PCT  = 0.225   # 과부하 반응 후 10초, 공격력 +22.5%
    _HEXEREI_EM       = 90      # 감전/달감전 반응 후 10초, 원소 마스터리 +90pt
    _C6_HEXEREI_BOOST = 1.00    # C6 — 오즈 협동 공격 후 위 두 효과가 100% 증가
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 3
    BURST_LEVEL_UP_CONSTELLATION = 5
    NA_TABLES = (*_NA, _AIMED, _AIMED_FULL, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_OZ_ATK, _SKILL_SUMMON,)
    BURST_TABLES = (_BURST_LIGHTNING,)

    rarity         = 4
    ascension_stat = StatType.ATK_PCT

    @property
    def element(self) -> Element: return Element.ELECTRO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        c  = self.constellation
        nl = self._na_index()
        sk = self._skill_index()   # C3: 레벨 +3
        bl = self._burst_index()   # C5: 레벨 +3

        hits: list[SkillHit] = []

        # 일반공격
        for i, row in enumerate(self._NA):
            hits.append(SkillHit(f"{i+1}단 공격 피해", SkillType.NORMAL_ATK, row[nl], ScalingStat.ATK))
        hits.append(SkillHit("조준 사격 피해", SkillType.CHARGED_ATK, self._AIMED[nl], ScalingStat.ATK))
        hits.append(SkillHit("풀차지 조준 사격 피해", SkillType.CHARGED_ATK, self._AIMED_FULL[nl], ScalingStat.ATK, Element.ELECTRO))
        hits.append(SkillHit("낙하 기간 피해", SkillType.PLUNGING, self._PLUNGE[nl], ScalingStat.ATK))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl], ScalingStat.ATK))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK))

        # 원소스킬
        hits.append(SkillHit("오즈 공격 피해", SkillType.SKILL, self._SKILL_OZ_ATK[sk], ScalingStat.ATK, Element.ELECTRO))
        hits.append(SkillHit("오즈 소환 피해", SkillType.SKILL, self._SKILL_SUMMON[sk], ScalingStat.ATK, Element.ELECTRO))

        # 원소폭발
        hits.append(SkillHit("낙뢰 피해", SkillType.BURST, self._BURST_LIGHTNING[bl], ScalingStat.ATK, Element.ELECTRO))

        # ── 오즈가 내는 추가 피해 ─────────────────────────────────────────────
        # A1·A4·C1·C6은 전부 **오즈가** 때리는 피해다. 그래서 스킬 타입은 SKILL로 둔다
        # (이네파 A1 「오버클럭 추가 공격」과 같은 규약 — 발동 계기가 일반/강공격이어도
        # 때리는 주체가 스킬 소환물이면 스킬 피해로 센다).
        #
        # A1만 계수가 표에 없다. 「사격 피해의 152.7%」라 **풀차지 조준 사격 표를 읽어**
        # 곱한다. 1.527을 계수 자리에 그냥 적으면 특성 레벨을 따라가지 않는다.
        hits.append(SkillHit("A1 별을 삼킨 까마귀 피해", SkillType.SKILL,
                             self._AIMED_FULL[nl] * self._A1_AIMED_MULT,
                             ScalingStat.ATK, Element.ELECTRO))

        # A4는 오즈가 필드에 있고 필드 위 캐릭터가 번개 반응을 일으켰을 때만 난다.
        # 조건은 로테이션 몫이라 히트는 항상 세워 두고 합산 여부는 화면을 읽는 쪽이 고른다.
        hits.append(SkillHit("A4 단죄의 뇌영 피해", SkillType.SKILL, self._A4_DMG,
                             ScalingStat.ATK, Element.ELECTRO))

        # C1은 **오즈가 없을 때**, C6은 **오즈가 있을 때**다 — 배타적이지만 둘 다 세워 둔다.
        if c >= 1:
            hits.append(SkillHit("C1 까마귀 눈 추가 공격", SkillType.SKILL, self._C1_DMG,
                                 ScalingStat.ATK, Element.ELECTRO))
        if c >= 2:
            hits.append(SkillHit("C2 소환 추가 피해", SkillType.SKILL, self._C2_DMG,
                                 ScalingStat.ATK, Element.ELECTRO))
        if c >= 4:
            # 원소폭발 발동 시 나므로 폭발 피해 보너스를 받는다.
            hits.append(SkillHit("C4 환상 이야기 피해", SkillType.BURST, self._C4_DMG,
                                 ScalingStat.ATK, Element.ELECTRO))
        if c >= 6:
            hits.append(SkillHit("C6 오즈 협동 공격 피해", SkillType.SKILL, self._C6_DMG,
                                 ScalingStat.ATK, Element.ELECTRO))

        return {h.name: h for h in hits}

    # 피슬에게는 자기만 받는 버프가 없다 — 마도 강화는 자신과 필드 위 캐릭터가 함께
    # 받으므로 코어 스탯 기여(Phase 4)로 간다. 추상 메서드라 지우지 못하고 비워 둔다.
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        pass

    # 최종 스탯을 읽어 만드는 버프가 없다(마도 강화는 고정 수치다). 위와 같은 이유로 비워 둔다.
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        pass

    # ── 파티 버프 4: 마도·비밀 의식 (코어 스탯 기여 + 유저 입력 수집) ─────────
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        """마도·비밀 의식 — 오즈가 필드 위에 있을 때 번개 반응이 파티를 강화한다.

        받는 쪽이 **피슬 자신과 「현재 필드 위 다른 캐릭터」 하나**뿐이라 자기 버프가 아니고,
        내놓는 것이 공격력%와 원소 마스터리 고정값이라 코어 스탯 풀 기여다 — 그래서 여기다.
        스탯을 읽지 않으므로 Phase 5로 내릴 것이 없다."""
        c = self.constellation

        # 파티 편성으로 결정되므로 묻지 않는다 (피슬 본인이 마도 + 파티 마도 2명 이상).
        self._hexerei_rite = hexerei_rite_for(self, all_hits)
        if not self._hexerei_rite:
            return

        # 「오즈가 필드 위에 있을 시」가 마도 강화 전체의 문지기다. 로테이션이 정하는 값이라
        # 파티 구성으로 유도할 수 없다 — 묻는다. C1(오즈가 없을 때)과 배타적이라는 것도
        # 문구에 적어 화면에서 바로 읽히게 한다.
        oz_active = ask_bool("[피슬 마도] 오즈가 필드 위 존재?")
        if not oz_active:
            return

        # 두 강화는 트리거도 주는 것도 서로 독립이다 — 나란히 묻고 켜진 만큼 더한다.
        overloaded = ask_bool("[피슬 마도] 과부하 반응 발동 후 10초 이내 (공격력 +22.5%)")
        charged    = ask_bool("[피슬 마도] 감전·달감전 반응 발동 후 10초 이내 (원소 마스터리 +90)")
        if not (overloaded or charged):
            return

        # C6: 오즈가 협동 공격을 한 뒤 위 두 효과가 100% 증가한다. 증가폭이 두 효과에
        # 공통이므로 배수를 한 번만 만들어 둘 다 읽게 한다.
        boost = 1.0
        if c >= 6 and ask_bool("[피슬 C6] 오즈 협동 공격 후 10초 이내 (마도 강화 100% 증가)"):
            boost += self._C6_HEXEREI_BOOST

        # 「피슬과 …… 현재 필드 위 다른 캐릭터」 — 대상은 두 명이다. 파티 전원에게 걸면
        # 부풀려지므로 필드 위 캐릭터를 한 명만 고르게 한다. 그 한 명이 피슬 자신이면
        # 「다른 캐릭터」가 없으므로 피슬만 받는다.
        targets = {self, self._ask_on_field_member(all_hits)}

        for char in targets:
            for hit in all_hits[char].values():
                if overloaded:
                    hit.add("atk_pct", self._HEXEREI_ATK_PCT * boost, self,
                            note="마도 비밀 의식 (과부하)")
                if charged:
                    # 고정 수치라 em_from_pct_share가 아니라 em_from_flat이다 —
                    # 다른 캐릭터 스탯의 %에서 파생된 지분이 아니다(모나 C2와 같은 규약).
                    hit.add("em_from_flat", self._HEXEREI_EM * boost, self,
                            note="마도 비밀 의식 (감전)")

    def _ask_on_field_member(self, all_hits):
        """마도 강화가 걸릴 「현재 필드 위 캐릭터」. 파티원이 1명뿐이면 묻지 않는다."""
        members = list(all_hits.keys())
        if len(members) == 1:
            return members[0]
        options = [
            f"{char.name} ({char.element.value})" + (" ← 피슬" if char is self else "")
            for char in members
        ]
        return members[ask_choice("[피슬] 현재 필드 위 캐릭터", options)]

    # ── 판단이 갈린 자리 ───────────────────────────────────────────────────
    # · A1·A4·C1·C6의 스킬 타입을 SKILL로 두었다. 넷 다 **오즈가** 때리는 피해이고,
    #   이네파 A1 「오버클럭 추가 공격」이 같은 이유로 SKILL이다. 다만 A1은 발동 계기가
    #   풀차지 조준 사격이고 계수도 그 표에서 나오므로 CHARGED_ATK로 볼 여지가 있다 —
    #   그 경우 「사냥꾼의 길」·「나부끼는 첫눈」 같은 강공격 피해 보너스가 A1에 실린다.
    #   자료에 판정이 적혀 있지 않아 소환물 기준으로 통일했다. 실측으로 갈리면 여기만 고친다.
    # · C4는 원소폭발 발동 시 나므로 BURST로 두었다(폭발 피해 보너스를 받는다).
    #
    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 오즈의 존재 시간·재소환·위치 조정(E 홀드)·C6의 존재 시간 +2초 — 시간이지 히트
    #   단가가 아니다. 오즈 공격이 로테이션에 몇 발 들어가는지는 화면을 읽는 쪽이 정한다.
    # · Q 「암야의 환」의 이동 형태 변환·보호 효과 — 피해식에 들어갈 항이 없다.
    # · C4의 HP 20% 회복 — 치유다. 이 엔진은 치유를 히트로 만들지 않는다.
    # · C2의 영향 범위 +50% — 범위지 배율이 아니다.
    # · A1·A4·C1·C6의 발동 빈도와 내부 쿨다운 — 로테이션 몫이라 히트를 세워 두고
    #   합산 여부만 유저가 고른다.
    # · 「마도 · 비밀 의식」 원문 중 「유야의 칠중주」 서술 — 넘겨받은 자료에 그 항의
    #   수치가 없다. 공격력 +22.5%와 원소 마스터리 +90pt 두 줄만 구현했다.
