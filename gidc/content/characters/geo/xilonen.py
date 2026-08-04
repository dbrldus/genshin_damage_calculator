from gidc.core.character import Character, clamp_talent_index
from gidc.enums import WeaponType
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import Element
from gidc.prompt import ask_bool


class Xilonen(Character):
    """
    실로닌 (Xilonen) | 바위 | 한손검 | 5성 | 어센션 스탯: 방어력 백분율

    A1 : 「네토틸리즈틀리」
    실로닌이 밤혼 가호 상태에서 「음원 샘플」 타입에 따라 실로닌의 일반 공격과 낙하 공격이 상응하는 강화 효과를 받는다:
    · 원소 전환이 발생한 「음원 샘플」 최소 2개 이상 보유: 적에게 명중 시, 밤혼을 35pt 획득한다. 해당 효과는 0.1초마다 최대 1회 발동된다.
    · 원소 전환이 발생한 「음원 샘플」 2개 미만 보유: 주는 피해가 30% 증가한다.

    A4 : 「휴대용 갑옷」
    밤혼 가호 상태에서 실로닌의 밤혼이 최대치 도달 시, 「밤혼 발산」과 동일한 효과를 1회 발동한다. 해당 효과는 14초마다 최대 1회 발동된다.
    또한 파티 내 주변에 있는 캐릭터가 「밤혼 발산」 발동 시, 실로닌의 방어력이 20% 증가한다. 지속 시간: 15초.

    C1 : 「잠에 바치는 휴일」
    실로닌의 밤혼 가호 상태가 소모하는 밤혼과 열소가 30% 감소하고 밤혼의 제한 시간이 45% 연장된다.
    또한 실로닌의 「음원 샘플」이 활성화 시, 주변에 있는 파티 내 현재 필드 위 캐릭터의 경직 저항력이 증가한다.

    C2 : 「불타는 들판에 바치는 오중주」
    실로닌이 휴대한 바위 원소 「음원 샘플」이 활성화 상태를 계속 유지한다. 또한 실로닌의 「음원 샘플」 활성화 시, 「음원 샘플」의 원소 타입에 따라 주변에 있는 파티 내 모든 동일 원소 타입의 캐릭터가 상응하는 효과를 획득한다:
    · 바위 원소: 주는 피해 50% 증가.
    · 불 원소: 공격력 45% 증가.
    · 물 원소: HP 최대치 45% 증가.
    · 얼음 원소: 치명타 피해 60% 증가.
    · 번개 원소: 원소 에너지 25pt 회복 및 원소폭발의 재사용 대기시간 6초 감소.

    C3 : 「태양에 바치는 순환」
    음악 단조의 스킬 레벨+3
    최대 Lv.15까지 상승

    C4 : 「오후에 바치는 꽃의 꿈」
    실로닌이 음악 단조 발동 후, 주변에 있는 파티 내 모든 캐릭터에게 「영광의 꽃 축복」 효과를 부여한다. 지속 시간: 15초.
    「영광의 꽃 축복」을 보유한 캐릭터가 일반 공격, 강공격, 낙하 공격으로 주는 피해가 실로닌의 방어력의 65%만큼 증가한다. 해당 효과는 6회 적용 또는 지속 시간 종료 시 사라진다.
    동시에 여러 기의 적에게 명중 시, 명중한 적의 수에 따라 효과 발동 횟수가 소모된다. 파티 내에 「영광의 꽃 축복」을 보유한 캐릭터가 있으면, 해당 캐릭터의 효과 발동 횟수는 단독으로 계산한다.

    C5 : 「석양에 바치는 변화」
    야생의 리듬! 의 스킬 레벨+3
    최대 Lv.15까지 상승

    C6 : 「영원한 밤에 바치는 춤」
    밤혼 가호 상태에서 실로닌이 대시, 도약, 일반 공격, 낙하 공격 시, 「영원한 밤 축복」을 획득한다. 밤혼 가호 상태의 제한을 무시하고 일반 공격과 낙하 공격으로 주는 피해가 증가한다. 지속 시간: 5초.
    지속 시간 동안 실로닌의 밤혼 제한 시간 카운트가 멈추고, 실로닌의 밤혼, 열소, 스테미너가 감소하지 않는다. 또한 밤혼이 최대치에 도달해도 실로닌의 밤혼 가호 상태가 종료되지 않는다.
    실로닌이 밤혼 가호 상태에서 일반 공격과 낙하 공격으로 주는 피해가 실로닌의 방어력의 300%만큼 증가한다. 1.5초마다 주변에 있는 파티 내 모든 캐릭터의 HP를 회복한다. 회복량은 실로닌 방어력의 120%에 해당한다.
    「영원한 밤 축복」 효과는 15초마다 최대 1회 획득할 수 있다.
    """
    name = "실로닌"
    weapon_type = WeaponType.SWORD

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # 일반 공격 (% ATK, L1~L11)
    _NA = [
        [0.5179, 0.5601, 0.6022, 0.6625, 0.7046, 0.7528, 0.8190, 0.8853, 0.9515, 1.0238, 1.0961],
        [0.2737, 0.2960, 0.3183, 0.3501, 0.3724, 0.3979, 0.4329, 0.4679, 0.5029, 0.5411, 0.5793],
        [0.2737, 0.2960, 0.3183, 0.3501, 0.3724, 0.3979, 0.4329, 0.4679, 0.5029, 0.5411, 0.5793],
        [0.7295, 0.7889, 0.8482, 0.9331, 0.9925, 1.0603, 1.1536, 1.2469, 1.3402, 1.4420, 1.5438],
    ]

    _CA          = [0.9133, 0.9877, 1.0620, 1.1682, 1.2425, 1.3275, 1.4443, 1.5611, 1.6780, 1.8054, 1.9328]
    _PLUNGE      = [0.6393, 0.6914, 0.7434, 0.8177, 0.8698, 0.9292, 1.0110, 1.0928, 1.1746, 1.2638, 1.3530]
    _LOW_PLUNGE  = [1.2784, 1.3824, 1.4865, 1.6351, 1.7392, 1.8581, 2.0216, 2.1851, 2.3486, 2.5270, 2.7054]
    _HIGH_PLUNGE = [1.5968, 1.7267, 1.8567, 2.0424, 2.1723, 2.3209, 2.5251, 2.7293, 2.9336, 3.1564, 3.3792]

    # 칼날바퀴 수렵 모드 1~4단 공격 (% DEF, L1~L11, 일반 공격 레벨 적용)
    _BLADE_WHEEL_NA = [
        [0.5602, 0.6058, 0.6514, 0.7166, 0.7622, 0.8143, 0.8859, 0.9576, 1.0292, 1.1074, 1.1856],
        [0.5505, 0.5953, 0.6401, 0.7041, 0.7489, 0.8001, 0.8705, 0.9409, 1.0113, 1.0882, 1.1650],
        [0.6582, 0.7117, 0.7653, 0.8418, 0.8954, 0.9566, 1.0408, 1.1250, 1.2092, 1.3010, 1.3928],
        [0.8603, 0.9303, 1.0003, 1.1004, 1.1704, 1.2504, 1.3604, 1.4705, 1.5805, 1.7005, 1.8206],
    ]

    # 원소 스킬 — 돌진 피해 (% DEF, L1~L13, C3 적용 시 최대 L13)
    _SKILL_DASH = [
        1.7920, 1.9264, 2.0608, 2.2400, 2.3744,
        2.5088, 2.6880, 2.8672, 3.0464, 3.2256,
        3.4048, 3.5840, 3.8080,
    ]

    # 원소 스킬 — 음원 샘플 원소 내성 감소 (%, L1~L13, C3 적용 시 최대 L13)
    _RES_REDUCTION = [
        0.09, 0.12, 0.15, 0.18, 0.21,
        0.24, 0.27, 0.30, 0.33, 0.36,
        0.39, 0.42, 0.45,
    ]

    # 원소 폭발 — 야생의 리듬! (% DEF, L1~L13, C5 적용 시 최대 L13)
    _BURST_DMG = [
        2.8128, 3.0238, 3.2347, 3.5160, 3.7270,
        3.9379, 4.2192, 4.5005, 4.7818, 5.0630,
        5.3443, 5.6256, 5.9772,
    ]
    _FOLLOW_UP_BEAT_DMG = [
        2.8128, 3.0238, 3.2347, 3.5160, 3.7270,
        3.9379, 4.2192, 4.5005, 4.7818, 5.0630,
        5.3443, 5.6256, 5.9772,
    ]
    _BURST_HEAL_DEF  = [1.040, 1.118, 1.196, 1.300, 1.378, 1.456, 1.560, 1.664, 1.768, 1.872, 1.976, 2.080, 2.210]
    _BURST_HEAL_FLAT = [501,   551,   605,   664,   726,   793,   864,   939,   1018,  1102,  1189,  1281,  1377 ]
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 3
    BURST_LEVEL_UP_CONSTELLATION = 5
    NA_TABLES = (*_NA, *_BLADE_WHEEL_NA, _CA, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_DASH, _RES_REDUCTION,)
    BURST_TABLES = (_BURST_DMG, _FOLLOW_UP_BEAT_DMG, _BURST_HEAL_DEF, _BURST_HEAL_FLAT,)

    rarity = 5

    @property
    def element(self)  -> Element: return Element.GEO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        c = self.constellation

        # C3: 원소 스킬 레벨 +3 (최대 13)
        sk = self._skill_index()
        # C5: 원소 폭발 레벨 +3 (최대 13)
        bl = self._burst_index()
        nl = self._na_index()

        hits: list[SkillHit] = []

        for name, row in zip(["1단 공격", "2단 공격 1타", "2단 공격 2타", "3단 공격"], self._NA):
            hits.append(SkillHit(f"{name} 피해", SkillType.NORMAL_ATK, row[nl], ScalingStat.ATK))

        hits.append(SkillHit("강공격 피해", SkillType.CHARGED_ATK, self._CA[nl], ScalingStat.ATK))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.DEF))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.DEF))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.DEF))

        for name, row in zip(["1단 공격", "2단 공격", "3단 공격", "4단 공격"], self._BLADE_WHEEL_NA):
            hits.append(SkillHit(f"칼날 바퀴 수렵 {name} 피해", SkillType.NORMAL_ATK, row[nl], ScalingStat.DEF, Element.GEO))

        hits.append(SkillHit("원소 스킬 돌진 피해", SkillType.SKILL, self._SKILL_DASH[sk], ScalingStat.DEF, Element.GEO))

        hits.append(SkillHit("원소 폭발 피해", SkillType.BURST, self._BURST_DMG[bl],        ScalingStat.DEF, Element.GEO))
        hits.append(SkillHit("추가 박자 피해", SkillType.BURST, self._FOLLOW_UP_BEAT_DMG[bl], ScalingStat.DEF, Element.GEO))

        return {h.name: h for h in hits}

    # ── 「음원 샘플」 (E 내성 감소와 A1 판정의 단일 출처) ─────────────────────
    # 샘플 3개는 초기에 모두 바위 원소이며, 파티 내 불/물/얼음/번개 캐릭터가 1명 있을 때마다
    # 바위 샘플 1개가 그 원소로 바뀐다. 실로닌 자신은 바위라 전환을 일으키지 않는다.
    _SAMPLE_SLOTS = 3
    _SAMPLE_CONVERTING_ELEMENTS = (Element.PYRO, Element.HYDRO, Element.CRYO, Element.ELECTRO)

    # 전환된 샘플이 이 수에 못 미치면(= 바위로 유지되는 칸이 2개 이상이면) 전환된 샘플이
    # 내성을 감소시키지 못하고, 대신 A1이 일반/낙하 피해 증가를 준다. 같은 문턱의 양면이다.
    _SHRED_MIN_CONVERTED = 2

    def _sample_elements(self, all_hits: dict["Character", dict[str, SkillHit]]) -> list[Element]:
        """샘플 3칸의 최종 원소 구성 (전환된 칸 먼저, 나머지는 바위).

        유저 입력도 스탯도 보지 않고 파티 원소 구성만으로 정해지므로 묻지 않는다.
        전환은 캐릭터 1명당 1칸이라 같은 원소가 2명이면 2칸이 같은 원소로 바뀐다 —
        내성 감소는 중복돼도 한 번만 걸리지만(_active_sample_elements) 문턱 판정이 세는
        「전환이 발생한 샘플 수」는 칸 기준이므로 여기서는 중복을 남긴다."""
        converted = [
            char.element for char in all_hits
            if char.element in self._SAMPLE_CONVERTING_ELEMENTS
        ][:self._SAMPLE_SLOTS]
        return converted + [Element.GEO] * (self._SAMPLE_SLOTS - len(converted))

    def _converted_sample_elements(self, all_hits: dict["Character", dict[str, SkillHit]]) -> list[Element]:
        """원소 전환이 발생한 샘플의 원소 (칸 단위, 중복 포함)."""
        return [e for e in self._sample_elements(all_hits) if e is not Element.GEO]

    def _active_sample_elements(self, all_hits: dict["Character", dict[str, SkillHit]]) -> list[Element]:
        """내성 감소가 실제로 걸리는 샘플 원소 (중복 제거).

        전환된 샘플이 2개 미만이면 — 즉 바위로 유지되는 칸이 2개 이상이면 — 전환된 샘플은
        내성을 깎지 못한다. 전환되지 않고 남은 바위 샘플은 C2에서만 활성 상태를 유지하며,
        이쪽은 위 문턱과 무관하게 걸린다."""
        converted = self._converted_sample_elements(all_hits)
        kept_geo  = self._SAMPLE_SLOTS - len(converted)

        active = converted if len(converted) >= self._SHRED_MIN_CONVERTED else []
        if kept_geo and self.constellation >= 2:
            active = [*active, Element.GEO]
        return list(dict.fromkeys(active))

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        c = self.constellation

        # A4: 밤혼 발산 발동 → 방어력 +20% (15초)
        if ask_bool("[실로닌 A4] 방어력 +20% 활성 여부"):
            for hit in hits.values():
                hit.add("def_pct", 0.20, self, note="A4")

        # C6: 영원한 밤 축복 — 밤혼 가호 상태 일반/낙하 피해 +DEF 300%
        if c >= 6 and ask_bool("[실로닌 C6] 영원한 밤 축복 여부"):
            # finalize() 전이므로 라이브 스탯으로 현재 방어력을 읽는다
            def_est = next(iter(hits.values())).current_def()
            for hit in hits.values():
                if hit.skill_type in (SkillType.NORMAL_ATK, SkillType.PLUNGING):
                    hit.add("flat_dmg_bonus", def_est * 3.0, self, note="C6 영원한 밤 축복")

    # ── 파티 버프 5a: C2 코어 스탯(atk_pct/hp_pct) 기여 + C4 입력 수집 ─────────
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        self._e_active = ask_bool("[실로닌 E] 음악 단조 활성 여부")
        if self._e_active:
            sk = self._skill_index()
            self._reduction = self._RES_REDUCTION[sk]

            # C2: 음원 샘플 활성 시 동일 원소 파티원 버프 중 코어 스탯(atk_pct/hp_pct)만 여기서
            if c >= 2:
                for char, char_hits in all_hits.items():
                    for hit in char_hits.values():
                        match char.element:
                            case Element.PYRO:  hit.add("atk_pct", 0.45, self, note="C2 음원 샘플")
                            case Element.HYDRO: hit.add("hp_pct",  0.45, self, note="C2 음원 샘플")

        # C4 활성 여부만 수집 — 실제 flat_dmg는 5b에서 current_def()로 적용
        self._c4_active = (c >= 4 and ask_bool("[실로닌 C4] 영광의 꽃 축복 여부"))

    # ── 파티 버프 5a.5: 내성 감소 + C2 all_dmg_bonus/crit_dmg (코어/스케일 아님) ──
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # A1: 원소 전환이 발생한 「음원 샘플」 2개 미만 → 일반/낙하 피해 +30%
        # (2개 이상이면 피해 증가 대신 밤혼 35pt 획득이라 피해 계산에 들어갈 항이 없다.)
        # 파티 원소 구성만으로 판정되므로 여기(파티 단계)에서 처리한다.
        if len(self._converted_sample_elements(all_hits)) < self._SHRED_MIN_CONVERTED:
            for hit in all_hits[self].values():
                if hit.skill_type in (SkillType.NORMAL_ATK, SkillType.PLUNGING):
                    hit.add("normal_atk_dmg_bonus", 0.30, self, note="A1")
                    hit.add("plunging_dmg_bonus",   0.30, self, note="A1")

        if not self._e_active:
            return

        # 샘플이 가질 수 있는 원소는 바위(초기값)와 전환 대상 4종뿐이다 —
        # 바람/풀 파티원은 샘플을 전환하지 않으므로 실로닌은 두 원소를 깎지 못한다.
        for element in self._active_sample_elements(all_hits):
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    match element:
                        case Element.PYRO:    hit.add("pyro_res_reduction",    -self._reduction, self, note="E 내성 감소")
                        case Element.HYDRO:   hit.add("hydro_res_reduction",   -self._reduction, self, note="E 내성 감소")
                        case Element.CRYO:    hit.add("cryo_res_reduction",    -self._reduction, self, note="E 내성 감소")
                        case Element.ELECTRO: hit.add("electro_res_reduction", -self._reduction, self, note="E 내성 감소")
                        case Element.GEO:     hit.add("geo_res_reduction",     -self._reduction, self, note="E 내성 감소")

        # C2: 음원 샘플 활성 시 동일 원소 파티원 버프 중 코어 아닌 것만 여기서
        if c >= 2:
            for char, char_hits in all_hits.items():
                for hit in char_hits.values():
                    match char.element:
                        case Element.GEO:  hit.add("all_dmg_bonus", 0.50, self, note="C2 음원 샘플")
                        case Element.CRYO: hit.add("crit_dmg",      0.60, self, note="C2 음원 샘플")

    # ── 파티 버프 5b: Xilonen 최신 DEF 기반 스케일 (C4) ───────────────────────
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # C4: 음악 단조 발동 후 파티 전원에게 영광의 꽃 축복 → 일반/강/낙하 +DEF 65%
        if not getattr(self, "_c4_active", False):
            return
        def_val = next(iter(all_hits[self].values())).current_def()
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                if hit.skill_type in (SkillType.NORMAL_ATK, SkillType.CHARGED_ATK, SkillType.PLUNGING):
                    hit.add("flat_dmg_bonus", def_val * 0.65, self, note="C4 영광의 꽃")
