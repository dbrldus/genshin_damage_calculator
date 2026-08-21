from gidc.core.character import Character, clamp_talent_index
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import CharacterTrait, Element
from gidc.core.party_state import hexerei_rite_for
from gidc.enums import WeaponType
from gidc.prompt import ask_bool


class Nicole(Character):
    """니콜 (Nicole) | 불 | 법구 | 5성 | 어센션 스탯: 공격력%

    A1 : 나눔
    원소전투 스킬 성언 묵시·미현의 빛 발동 후 20초 동안, 니콜은 파티 내 현재 필드에 있는 자신의 다른 캐릭터를 지속적으로 「관측」한다.
    관측 대상 캐릭터가 3초 동안 필드에 머물면, 해당 캐릭터가 보유한 자기 비움의 축복 효과가 축성의 인도(으)로 승급되어 추가로 공격력이 300pt 증가한다.
    만약 관측 대상 캐릭터가 마도 캐릭터일 경우, 자기 비움의 효과가 즉시 축성의 인도로 승급된다.
    니콜을 제외한, 다른 캐릭터가 보유한 축성의 인도는 퇴장 시 자기 비움의 축복로 복원된다.

    A4 :
    주변에 있는 파티 내 현재 필드 위 캐릭터의 원소 타입 피해가 적 명중 후,
    니콜 자신이 보유한 자기 비움의 축복이 축성의 인도로 승급된다. 지속 시간: 8초

    Hexerei :
    마녀의 과제·인도…? 완료하면, 니콜이 마도 캐릭터가 된다. 파티에 마도 캐릭터를 2명 이상 편성하면 마도 · 비밀 의식 효과를 획득해 마도 캐릭터가 강화된다.
    마도·비밀 의식 : 마도 캐릭터의 비밀 환영이 주는 피해가 증가하며, 증가량은 니콜 공격력의 300%에 해당한다.

    C1 : 「두려워 말라 총애받는 인간 아이여」
    파티 내 자신의 현재 필드 위 캐릭터의 공격이 적 명중 시, 추가로 특수한 「비밀 환영 · 합일」을 소환해 적에게 협동 공격을 하고,
    해당 캐릭터의 원소 타입에 따라 상응하는 원소 범위 피해를 준다. 이 피해는 해당 캐릭터 공격력의 600%에 해당하며, 해당 캐릭터가 주는 피해로 간주한다.
    해당 효과는 6초마다 최대 1회 발동된다

    C2 : 「내가 너를 인도하고 훈계하리로다」
    원소전투 스킬 성언 묵시·미현의 빛의 효과가 강화된다: 자기 비움의 축복은 공격력을 추가로 300pt 증가시킨다(해당 효과의 공격력은 보너스 최대치에 포함되지 않는다).
    축성의 인도는 캐릭터의 원소 타입에 따라 주변 적의 해당 원소 내성을 25% 감소시킨다. 동일한 원소 타입의 원소 내성 감소 효과는 중첩되지 않는다.
    또한, 니콜이 원소전투 스킬 성언 묵시·미현의 빛을 발동할 때도 주변의 현재 필드 위 캐릭터에게 광휘 보호막을 부여한다

    C3 : 「나는 네 등불이요 네 곁의 빛이니라」
    원소전투 스킬 성언 묵시 · 미현의 빛의 스킬 레벨+3

    C4 : 「네가 바른길에서 벗어나 방황할 때」
    주변에 있는 파티 내 캐릭터가 보유한 자기 비움의 축복이 축성의 인도로 승급될 때, 니콜이 해당 캐릭터에게 추가로 「인도자의 가호」 효과를 부여한다.
    지속 시간:20초, 각 캐릭터는 16초마다 해당 효과를 최대 1회 획득할 수 있다.
    「인도자의 가호」를 보유한 캐릭터의 일반 공격, 강공격, 낙하 공격, 원소전투 스킬과 원소폭발로 주는 피해가 증가한다.
    증가량은 니콜 공격력의 70%에 해당한다. 해당 효과는 8회 발동되거나 지속 시간이 끝날 때 사라진다.
    동시에 여러 명의 적 명중 시, 명중한 적의 수에 따라 효과 발동 횟수가 소모된다.
    파티 내 「인도자의 가호」를 보유한 캐릭터의 효과 발동 횟수는 독립적으로 계산된다

    C5 : 「나는 네 귀에 들러 이르기를」
    원소폭발 성언 묵시 · 하늘 계단의 스킬 레벨+3

    C6 : 「이것이 바른길이니 행할지어다」
    니콜이 보유한 자기 비움의 축복이 축성의 인도로 승급될 때, 주변에 있는 파티 내 모든 캐릭터가 보유한 자기 비움의 축복도 함께 축성의 인도로 승급된다.
    승급된 모든 축성의 인도는 더 이상 자기 비움의 축복으로 되돌아가지 않는다.
    또한, 축성의 인도를 보유한 캐릭터가 주는 피해는 적의 방어력을 40% 무시한다.
    """
    name = "니콜"
    weapon_type = WeaponType.CATALYST
    # 「마녀의 과제」를 완료하면 마도 캐릭터가 된다.
    unlockable_traits = frozenset({CharacterTrait.HEXEREI})

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # 일반 공격 (% ATK, L1~L11)
    _NA = [
        [0.4019, 0.4344, 0.4670, 0.5137, 0.5463, 0.5789, 0.6302, 0.6814, 0.7327, 0.7886, 0.8445],
        [0.3656, 0.3953, 0.4250, 0.4675, 0.4972, 0.5269, 0.5734, 0.6199, 0.6664, 0.7169, 0.7674],
        [0.4599, 0.4973, 0.5347, 0.5881, 0.6255, 0.6629, 0.7212, 0.7794, 0.8377, 0.9009, 0.9642],
    ]

    _CA = [0.7922, 0.8566, 0.9210, 1.0131, 1.0775, 1.1513, 1.2528, 1.3544, 1.4559, 1.5668, 1.6777]

    _PLUNGE      = [0.6393, 0.6914, 0.7434, 0.8177, 0.8698, 0.9293, 1.0110, 1.0928, 1.1746, 1.2638, 1.3530]
    _LOW_PLUNGE  = [1.2784, 1.3824, 1.4865, 1.6351, 1.7392, 1.8581, 2.0216, 2.1851, 2.3486, 2.5270, 2.7054]
    _HIGH_PLUNGE = [1.5968, 1.7267, 1.8567, 2.0424, 2.1723, 2.3209, 2.5251, 2.7293, 2.9336, 3.1564, 3.3792]

    # 원소 스킬 (L1~L13, C3 적용 시 최대 L13)
    _SKILL_DMG           = [1.568, 1.686, 1.804, 1.960, 2.078, 2.196, 2.352, 2.508, 2.664, 2.820, 2.976, 3.132, 3.328]
    _SKILL_ATK_BONUS     = [  163,   175,   188,   204,   216,   229,   245,   261,   277,   293,   309,   326,   347]
    _SKILL_ATK_BONUS_MAX = [  326,   350,   376,   408,   432,   458,   490,   522,   554,   586,   618,   652,   694]

    # 원소 폭발 (L1~L15, C5 적용 시 최대 L13)
    _BURST_DMG = [
        3.728, 4.008, 4.288, 4.660, 4.940,
        5.220, 5.592, 5.964, 6.336, 6.708,
        7.080, 7.452, 7.916, 8.380, 8.844,
    ]
    _BURST_ARCANE_PROJECTION = [
        0.932, 1.002, 1.072, 1.165, 1.235,
        1.305, 1.398, 1.491, 1.584, 1.677,
        1.770, 1.863, 1.979, 2.095, 2.211,
    ]
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 3
    BURST_LEVEL_UP_CONSTELLATION = 5
    NA_TABLES = (*_NA, _CA, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_DMG, _SKILL_ATK_BONUS, _SKILL_ATK_BONUS_MAX,)
    BURST_TABLES = (_BURST_DMG, _BURST_ARCANE_PROJECTION,)

    rarity = 5

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

        for i, row in enumerate(self._NA):
            hits.append(SkillHit(f"{i+1}단 공격", SkillType.NORMAL_ATK, row[nl], ScalingStat.ATK, Element.PYRO))

        hits.append(SkillHit("강공격 피해", SkillType.CHARGED_ATK, self._CA[nl], ScalingStat.ATK, Element.PYRO))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK, Element.PYRO))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK, Element.PYRO))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK, Element.PYRO))

        hits.append(SkillHit("원소 스킬 피해", SkillType.SKILL, self._SKILL_DMG[sk], ScalingStat.ATK, Element.PYRO))

        hits.append(SkillHit("원소 폭발 피해",     SkillType.BURST, self._BURST_DMG[bl],               ScalingStat.ATK, Element.PYRO))
        hits.append(SkillHit("비밀 환영 비전 피해", SkillType.BURST, self._BURST_ARCANE_PROJECTION[bl], ScalingStat.ATK, Element.PYRO))

        return {h.name: h for h in hits}

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        pass  # 개인 버프 없음 — Hexerei는 Phase 5에서 파티 구성으로 판정한다

    # ── Phase 4: 자기 비움/축성의 인도 ATK 기여 + 입력 수집 ────────────────────
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        self._consecrated: dict = {}   # char -> 축성의 인도 여부 (Phase 4.5/5에서 재사용)
        self._e_active = ask_bool("[니콜 E] 성언 묵시·미현의 빛 활성 여부")
        if not self._e_active:
            return

        sk         = self._skill_index()
        base_bonus = self._SKILL_ATK_BONUS[sk]
        max_bonus  = self._SKILL_ATK_BONUS_MAX[sk]
        c2_extra   = 300 if c >= 2 else 0

        def _apply_blessing(char_hits, is_consecrated):
            # 축성의 인도 시 A1 +300 ATK (캡 제한), 기본은 base_bonus
            atk_bonus = min(base_bonus + 300, max_bonus) if is_consecrated else base_bonus
            for hit in char_hits.values():
                hit.add("atk_flat", atk_bonus + c2_extra, self, note="E 비움의 축복")

        # 자신
        self_has    = ask_bool("[니콜] [Nicole] 자기 비움의 축복 보유 여부")
        self_consec = ask_bool("[니콜] [Nicole] 축성의 인도로 승급 여부") if self_has else False
        self._consecrated[self] = self_consec
        if self_has:
            _apply_blessing(all_hits[self], self_consec)

        # 파티원
        for char, char_hits in all_hits.items():
            if char is self:
                continue
            char_name = char.name
            if not ask_bool(f"[니콜] [{char_name}] 자기 비움의 축복 보유 여부"):
                self._consecrated[char] = False
                continue
            is_consecrated = ask_bool(f"[니콜] [{char_name}] 축성의 인도로 승급 여부")
            self._consecrated[char] = is_consecrated
            _apply_blessing(char_hits, is_consecrated)

    # ── Phase 4.5: 축성의 인도 res_reduction/def_ignore (코어/스케일 아님) ──────
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation
        if not self._e_active:
            return

        for char, char_hits in all_hits.items():
            if not self._consecrated.get(char, False):
                continue

            # C2: 축성의 인도 → 캐릭터 원소 내성 -25%
            if c >= 2:
                for hit in char_hits.values():
                    match char.element:
                        case Element.PYRO:    hit.add("pyro_res_reduction",    -0.25, self, note="C2 축성의 인도")
                        case Element.HYDRO:   hit.add("hydro_res_reduction",   -0.25, self, note="C2 축성의 인도")
                        case Element.CRYO:    hit.add("cryo_res_reduction",    -0.25, self, note="C2 축성의 인도")
                        case Element.ELECTRO: hit.add("electro_res_reduction", -0.25, self, note="C2 축성의 인도")
                        case Element.ANEMO:   hit.add("anemo_res_reduction",   -0.25, self, note="C2 축성의 인도")
                        case Element.GEO:     hit.add("geo_res_reduction",     -0.25, self, note="C2 축성의 인도")
                        case Element.DENDRO:  hit.add("dendro_res_reduction",  -0.25, self, note="C2 축성의 인도")

            # C6: 축성의 인도 — 방어력 40% 무시
            if c >= 6:
                for hit in char_hits.values():
                    hit.add("def_ignore", 0.40, self, note="C6 축성의 인도")

    # ── Phase 5: 니콜 최신 ATK 기반 스케일 (C4 + Hexerei) ──────────────────────
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # 니콜의 최신 ATK를 **읽는 함수**로 넘긴다(지연 기여) — 다른 캐릭터가 같은
        # 단계에서 공격력을 더해 줄 수 있어 지금 확정하면 파티원 순서가 결과를 바꾼다.
        source_hit = next(iter(all_hits[self].values()))

        # Hexerei: 마도·비밀 의식(니콜 본인이 마도 + 2명 이상) — 비밀 환영 피해 + Nicole ATK 300%
        if hexerei_rite_for(self, all_hits):
            all_hits[self]["비밀 환영 비전 피해"].add(
                "flat_dmg_bonus", lambda: source_hit.convertible_atk() * 3.0,
                self, note="마도·비밀 의식")

        if not self._e_active or c < 4:
            return

        # C4: 인도자의 가호 — 모든 피해 + Nicole ATK 70% (flat)
        for char, char_hits in all_hits.items():
            if not self._consecrated.get(char, False):
                continue
            for hit in char_hits.values():
                hit.add("flat_dmg_bonus",
                        lambda: source_hit.convertible_atk() * 0.70,
                        self, note="C4 인도자의 가호")
