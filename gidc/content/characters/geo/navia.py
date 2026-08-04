from gidc.core.character import Character, clamp_talent_index
from gidc.enums import WeaponType
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import Element
from gidc.enums import StatType
from gidc.prompt import ask_bool, ask_int


class Navia(Character):
    """
    나비아 (Navia) | 바위 | 양손검 | 5성 | 어센션 스탯: 치명타 피해
    A1 :
    결정 축포 발동 후 4초 동안 나비아의 일반 공격, 강공격, 낙하 공격 피해가 다른 원소 부여 효과로 대체될 수 없는 바위 원소 피해로 전환된다.
    또한 나비아의 일반 공격, 강공격, 낙하 공격이 주는 피해가 40% 증가한다

    A4 :
    파티 내 불 원소, 번개 원소, 얼음 원소, 물 원소 캐릭터가 1명 존재할 때마다 나비아의 공격력이 20% 증가한다.
    최대 중첩수: 2스택

    C1 : 「숙녀의 거리감 수칙」
    결정 축포 발동 시, 「결정 파편」을 1개 소모할 때마다 나비아가 원소 에너지를 3pt 회복한다.
    또한, 창공을 울리는 포성의 재사용 대기시간이 1초 감소한다. 해당 방식으로 원소 에너지를 최대 9pt 회복하며 「창공을 울리는 포성」의 재사용 대기시간이 최대 3초 감소한다

    C2 : 「통솔자의 승승장구」
    결정 축포 발동 시, 「결정 파편」을 1개 소모할 때마다 이번 결정 축포의 치명타 확률이 12% 증가한다.
    해당 방식으로 결정 축포의 치명타 확률은 최대 36% 증가한다.
    또한, 결정 축포 사격이 적에게 명중 시 명중한 적의 주변에 창공을 울리는 포성의 「지원 포격」을 1회 발사한다.
    결정 축포를 발동할 때마다 지원 포격을 최대 1회 발사할 수 있으며, 해당 방식으로 발동한 지원 포격은 원소폭발 피해로 간주한다

    C3 : 「경영자의 넓은 시야」
    결정 축포의 스킬 레벨+3
    최대 Lv.15까지 상승

    C4 : 「맹세자의 엄격함」
    창공을 울리는 포성이 적에게 명중 시, 해당 적의 바위 원소 내성이 20% 감소한다.
    지속 시간: 8초

    C5 : 「협상가의 단호함」
    창공을 울리는 포성의 스킬 레벨+3
    최대 Lv.15까지 상승

    C6 : 「보스의 기민한 수완」
    결정 축포 발동 시, 「결정 파편」을 3개 넘게 소모하면 3개를 초과한 「결정 파편」 1개당 이번 결정 축포의 치명타 피해가 45% 증가한다.
    또한, 3개를 초과한 「결정 파편」은 발동 후 반환된다
    """
    name = "나비아"
    weapon_type = WeaponType.CLAYMORE

    def __init__(self) -> None:
        super().__init__()
        self._shrapnel: int = 0  # 결정 파편 개수 (0~6)

    # ── 특성 계수 테이블 ─────────────────────────────────────────────────────
    # 일반 공격 (% ATK, L1~L11)
    _NA_HIT1 = [0.9352, 1.0113, 1.0874, 1.1962, 1.2723, 1.3593, 1.4789, 1.5985, 1.7181, 1.8486, 1.9791]
    _NA_HIT2 = [0.8651, 0.9355, 1.0059, 1.1065, 1.1769, 1.2574, 1.3680, 1.4787, 1.5893, 1.7100, 1.8307]
    _NA_HIT3 = [0.3489, 0.3773, 0.4056, 0.4462, 0.4746, 0.5071, 0.5517, 0.5963, 0.6409, 0.6896, 0.7383]
    _NA_HIT4 = [1.3343, 1.4429, 1.5515, 1.7067, 1.8153, 1.9394, 2.1101, 2.2807, 2.4514, 2.6376, 2.8238]

    _CA_SPIN   = [0.6252, 0.6761, 0.7270, 0.7997, 0.8506, 0.9087, 0.9887, 1.0687, 1.1487, 1.2359, 1.3231]
    _CA_ENDING = [1.1309, 1.2229, 1.3150, 1.4465, 1.5386, 1.6437, 1.7884, 1.9331, 2.0777, 2.2355, 2.3933]

    _PLUNGE      = [0.7459, 0.8066, 0.8673, 0.9540, 1.0147, 1.0841, 1.1795, 1.2749, 1.3703, 1.4744, 1.5785]
    _LOW_PLUNGE  = [1.4914, 1.6128, 1.7342, 1.9077, 2.0291, 2.1678, 2.3586, 2.5493, 2.7401, 2.9482, 3.1563]
    _HIGH_PLUNGE = [1.8629, 2.0145, 2.1662, 2.3828, 2.5344, 2.7077, 2.9460, 3.1842, 3.4225, 3.6825, 3.9424]

    # 원소 스킬 — 결정 축포 (% ATK, L1~L13, C3 적용 시 최대 L13)
    _SKILL_ROSULA_SHARDSHOT = [3.9480, 4.2441, 4.5402, 4.9350, 5.2311, 5.5272, 5.9220, 6.3168, 6.7116, 7.1064, 7.5012, 7.8960, 8.3895]
    _SKILL_SURGING_BLADE    = [0.3600, 0.3870, 0.4140, 0.4500, 0.4770, 0.5040, 0.5400, 0.5760, 0.6120, 0.6480, 0.6840, 0.7200, 0.7650]
    _SKILL_ROSULA_SHARDSHOT_COEFF_AMP = [0.00, 1.00, 1.05, 1.10, 1.15, 1.20, 1.36, 1.40, 1.60, 1.666, 1.90, 2.00]

    # 원소 폭발 — 창공을 울리는 포성 (% ATK, L1~L13, C5 적용 시 최대 L13)
    _BURST_DMG         = [0.7520, 0.8084, 0.8648, 0.9400, 0.9964, 1.0528, 1.1280, 1.2032, 1.2784, 1.3536, 1.4288, 1.5040, 1.5980]
    _BURST_CANNON_FIRE = [0.4315, 0.4639, 0.4962, 0.5394, 0.5717, 0.6041, 0.6472, 0.6904, 0.7336, 0.7767, 0.8199, 0.8630, 0.9169]

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 3
    BURST_LEVEL_UP_CONSTELLATION = 5
    NA_TABLES = (_NA_HIT1, _NA_HIT2, _NA_HIT3, _NA_HIT4, _CA_SPIN, _CA_ENDING, _PLUNGE,
        _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_ROSULA_SHARDSHOT, _SKILL_SURGING_BLADE,)
    BURST_TABLES = (_BURST_DMG, _BURST_CANNON_FIRE,)

    rarity         = 5
    ascension_stat = StatType.CRIT_DMG

    @property
    def element(self)  -> Element: return Element.GEO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        c = self.constellation

        # C3: 결정 축포 레벨 +3 (최대 13)
        sk = self._skill_index()
        # C5: 창공을 울리는 포성 레벨 +3 (최대 13)
        bl = self._burst_index()
        nl = self._na_index()

        hits: list[SkillHit] = []

        for name, coeff in [
            ("1단 공격 피해",       self._NA_HIT1[nl]),
            ("2단 공격 피해",       self._NA_HIT2[nl]),
            ("3단 공격 피해 1타",   self._NA_HIT3[nl]),
            ("3단 공격 피해 2타",   self._NA_HIT3[nl]),
            ("3단 공격 피해 3타",   self._NA_HIT3[nl]),
            ("4단 공격 피해",       self._NA_HIT4[nl]),
        ]:
            hits.append(SkillHit(name, SkillType.NORMAL_ATK, coeff, ScalingStat.ATK))

        hits.append(SkillHit("강공격 순환 피해", SkillType.CHARGED_ATK, self._CA_SPIN[nl],   ScalingStat.ATK))
        hits.append(SkillHit("강공격 마무리 피해", SkillType.CHARGED_ATK, self._CA_ENDING[nl], ScalingStat.ATK))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK))

        # 결정 축포 장미탄 피해
        hits.append(SkillHit("결정 축포 장미탄 기본 피해", SkillType.SKILL, self._SKILL_ROSULA_SHARDSHOT[sk], ScalingStat.ATK, Element.GEO))
        # 솟구치는 칼날 피해
        hits.append(SkillHit("솟구치는 칼날 피해", SkillType.SKILL, self._SKILL_SURGING_BLADE[sk], ScalingStat.ATK, Element.GEO))

        # 창공을 울리는 포성
        hits.append(SkillHit("창공을 울리는 포성 피해",      SkillType.BURST, self._BURST_DMG[bl],         ScalingStat.ATK, Element.GEO))
        hits.append(SkillHit("창공을 울리는 포성 지원 포격", SkillType.BURST, self._BURST_CANNON_FIRE[bl], ScalingStat.ATK, Element.GEO))

        

        return {h.name: h for h in hits}

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        c = self.constellation

        # C3: 결정 축포 레벨 +3 (최대 13)
        sk = self._skill_index()
        # C5: 창공을 울리는 포성 레벨 +3 (최대 13)
        bl = self._burst_index()

        self._shrapnel = ask_int("[나비아 E] 결정 파편 개수", min_val=0, max_val=6)
        max_rosula_shardshot = max([5,7,9,11][min(self._shrapnel, 3)],11)
        self._rosula_shardshot_hit = ask_int("[나비아 E] 맞은 장미탄 개수", min_val=0, max_val=max_rosula_shardshot)
        hits["결정 축포 장미탄 기본 피해"].coeff_amp = self._SKILL_ROSULA_SHARDSHOT_COEFF_AMP[self._rosula_shardshot_hit]
        
        for hit in hits.values():
            if hit.skill_type == SkillType.SKILL:
                hit.add("all_dmg_bonus", max(0, self._shrapnel - 3) * 0.15, self, note="E 결정 파편")

        # C2: 결정 축포 사격 명중 시 지원 포격 1발 (원소 폭발 피해)
        if c >= 2 and self._shrapnel > 0:
            hit = SkillHit(
                "지원 포격 피해 (C2)",
                SkillType.BURST,
                self._BURST_CANNON_FIRE[bl],
                ScalingStat.ATK,
                Element.GEO,
            )
            hits[hit.name] = hit

        # A1: 결정 축포 발동 후 일반/강/낙하 피해 +40%
        if ask_bool("[나비아 A1] 결정 축포 발동 후 효과 여부"):
            for hit in hits.values():
                if hit.skill_type in (SkillType.NORMAL_ATK, SkillType.CHARGED_ATK, SkillType.PLUNGING):
                    hit.element = Element.GEO
                    hit.add("normal_atk_dmg_bonus",  0.40, self, note="A1")
                    hit.add("charged_atk_dmg_bonus", 0.40, self, note="A1")
                    hit.add("plunging_dmg_bonus",    0.40, self, note="A1")

        # C2: 소모 파편 1개당 결정 축포 치명타 확률 +12% (최대 3파편 → +36%)
        # SKILL 히트에만 정확하게 적용
        if c >= 2:
            bonus_cr = min(self._shrapnel, 3) * 0.12
            for hit in hits.values():
                if hit.skill_type == SkillType.SKILL:
                    hit.add("crit_rate", bonus_cr, self, note="C2 결정 파편")

        # C6: 파편 3개 초과분 1개당 결정 축포 치명타 피해 +45%
        # SKILL 히트에만 정확하게 적용
        if c >= 6:
            bonus_cd = max(0, self._shrapnel - 3) * 0.45
            for hit in hits.values():
                if hit.skill_type == SkillType.SKILL:
                    hit.add("crit_dmg", bonus_cd, self, note="C6 결정 파편")

    # ── 파티 버프 ─────────────────────────────────────────────────────────
    # A4는 자신 atk_pct(코어 스탯) 기여 → contribute_dependent_stats.
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # A4: 파티 내 불/번개/얼음/물 원소 캐릭터 1명당 공격력 +20% (최대 2스택)
        target_elems = {Element.PYRO, Element.ELECTRO, Element.CRYO, Element.HYDRO}
        count = sum(1 for char in all_hits if char is not self and char.element in target_elems)
        bonus = min(count, 2) * 0.20
        if bonus > 0:
            for hit in all_hits[self].values():
                hit.add("atk_pct", bonus, self, note="A4 원소 파티원")

    # C4: geo_res_reduction은 코어 스탯도 스탯 스케일도 아니므로 apply_party_buffs.
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        c = self.constellation

        # C4: 창공을 울리는 포성 명중 시 파티 전원 적 바위 내성 -20%
        if c >= 4 and ask_bool("[나비아 C4] 창공을 울리는 포성 명중 여부"):
            for char_hits in all_hits.values():
                for hit in char_hits.values():
                    hit.add("geo_res_reduction", -0.20, self, note="C4 바위 내성 감소")

    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        pass  # 최종 스탯을 읽어 스케일하는 버프 없음
