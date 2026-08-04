from gidc.core.character import Character, clamp_talent_index
from gidc.enums import WeaponType
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import Element
from gidc.prompt import ask_bool, ask_int


class Furina(Character):
    """푸리나 (Furina) | 물 | 한손검 | 5성 | 어센션 스탯: 치명타 확률
    A1 :
    현재 필드 위에 있는 파티 내 캐릭터가 치유를 받을 시, 이 치유가 푸리나 자신이 한 치유가 아닌 동시에 회복량이 초과된 경우,
    이어지는 4초 동안 푸리나가 2초마다 주변에 있는 파티 내 캐릭터의 HP를 1회 회복시킨다. 회복량은 캐릭터 각자 HP 최대치의 2%에 해당한다

    A4 :
    HP 최대치의 1000pt마다, 아르케의 힘 속성에 따른 푸리나의 고고한 살롱이 상응하는 버프 효과를 획득한다:
    「살롱 멤버」가 주는 피해가 0.7% 증가한다. 해당 방식으로 「살롱 멤버」가 주는 피해가 최대 28% 증가한다.
    「물들의 가수」가 근처에 있는 현재 필드 위 캐릭터의 HP를 회복시키는 간격이 0.4% 감소한다.
    해당 방식으로 「물들의 가수」가 주변에 있는 현재 필드 위 캐릭터의 HP를 회복시키는 간격이 최대 16% 감소한다

    C1 : 「사랑은 애걸해도 길들일 수 없는 새」
    성대한 카니발 발동 시, 푸리나가 「무대 열기」를 150pt 획득한다.
    또한, 푸리나의 「무대 열기」 보유 최대치가 100pt 증가한다

    C2 : 「여자의 마음은 흔들리는 부평초」
    성대한 카니발 지속 시간 동안, 푸리나가 주변에 있는 파티 내 캐릭터의 현재 HP 증가 또는 감소하는 방식을 통해 획득하는 「무대 열기」가 250% 증가한다.
    최대치를 초과하는 「무대 열기」 1pt당 푸리나의 HP 최대치가 0.35% 증가한다. 해당 방식으로 푸리나의 HP 최대치는 최대 140%까지 증가한다

    C3 : 「내 이름은 그 누구도 모르리라」
    성대한 카니발의 스킬 레벨+3
    최대 Lv.15까지 상승

    C4 : 「저승에서 느낀 삶의 소중함!」
    고고한 살롱의 「살롱 멤버」가 적을 명중시키거나 「물들의 가수」가 현재 필드 주변에 있는 캐릭터의 HP를 회복시킬 경우,
    푸리나가 원소 에너지를 4pt 획득한다. 해당 효과는 5초마다 최대 1회 발동된다

    C5 : 「난 알았노라, 그대의 이름은…!」
    고고한 살롱의 스킬 레벨+3
    최대 Lv.15까지 상승

    C6 : 「모두 사랑의 축배를 들렴!」
    고고한 살롱 발동 시, 푸리나가 「만인의 주목」을 획득한다. 지속 시간: 10초
    지속 시간 동안 푸리나의 일반 공격, 강공격, 낙하 공격이 다른 원소 부여 효과로 대체될 수 없는 물 원소 피해로 전환되고 주는 피해가 푸리나 HP 최대치의 18%만큼 증가한다.
    지속 시간 동안 0.1초마다, 푸리나의 일반 공격(「아르케의 힘: 성과 속」의 공격 제외), 강공격과 낙하 공격의 추락 충격이 적에게 명중 후, 푸리나의 현재 아르케의 힘 속성에 따라 다른 효과가 생성된다:

    아르케의 힘: 우시아
    1초마다 주변에 있는 파티 내 모든 캐릭터의 HP를 푸리나 HP 최대치의 4%만큼 회복한다.
    지속 시간: 2.9초. 중복 발동 시 지속 시간이 연장된다.
    아르케의 힘: 프뉴마
    이번 일반 공격(「아르케의 힘: 성과 속」의 공격 제외), 강공격과 낙하 공격의 추락 충격으로 주는 피해가 푸리나 HP 최대치의 25%만큼 증가한다.
    상술한 공격이 적에게 명중 시, 주변에 있는 파티 내 모든 캐릭터의 HP를 현재 HP의 1%만큼 소모한다.

    한 번의 「만인의 주목」 지속 시간 동안 상술한 효과는 최대 6회 발동되고, 발동 횟수가 6회에 도달하거나 지속 시간이 종료되면 효과가 사라진다
    """
    name = "푸리나"
    weapon_type = WeaponType.SWORD

    def __init__(self) -> None:
        super().__init__()
        self._salon_coeff_amp: float = 1.0

    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # 일반 공격
    _NA = [
        [0.4839, 0.5232, 0.5626, 0.6189, 0.6583, 0.7033, 0.7652, 0.8271, 0.8890, 0.9565, 1.0240],
        [0.4373, 0.4729, 0.5085, 0.5593, 0.5949, 0.6356, 0.6915, 0.7475, 0.8034, 0.8644, 0.9254],
        [0.5512, 0.5961, 0.6409, 0.7050, 0.7499, 0.8012, 0.8717, 0.9422, 1.0127, 1.0896, 1.1665],
        [0.7330, 0.7926, 0.8523, 0.9375, 0.9972, 1.0654, 1.1591, 1.2529, 1.3466, 1.4489, 1.5512],
    ]

    _CA = [0.7422, 0.8026, 0.8630, 0.9493, 1.0097, 1.0788, 1.1737, 1.2686, 1.3635, 1.4671, 1.5707]

    _PLUNGE      = [0.6393, 0.6914, 0.7434, 0.8177, 0.8698, 0.9293, 1.0110, 1.0928, 1.1746, 1.2638, 1.3530]
    _LOW_PLUNGE  = [1.2784, 1.3824, 1.4865, 1.6351, 1.7392, 1.8581, 2.0216, 2.1851, 2.3486, 2.5270, 2.7054]
    _HIGH_PLUNGE = [1.5968, 1.7267, 1.8567, 2.0424, 2.1723, 2.3209, 2.5251, 2.7293, 2.9336, 3.1564, 3.3792]

    # 아르케의 힘
    _SPRITBREATH_THORN_SURGING_BLADE \
      = [0.0946, 0.1023, 0.1100, 0.1210, 0.1287, 0.1375, 0.1496, 0.1617, 0.1738, 0.1870, 0.2002]

    # 원소 전투 스킬 (% Max HP, L1~L13, C5 적용 시 최대 L13)
    _SKILL_OUSIA_BUBBLE  = [0.0786, 0.0845, 0.0904, 0.0983, 0.1042, 0.1101, 0.1180, 0.1258, 0.1337, 0.1416, 0.1494, 0.1573, 0.1671]
    _SKILL_USHER         = [0.0596, 0.0641, 0.0685, 0.0745, 0.0790, 0.0834, 0.0894, 0.0954, 0.1013, 0.1073, 0.1132, 0.1192, 0.1267]
    _SKILL_CHEVALMARIN   = [0.0323, 0.0347, 0.0372, 0.0404, 0.0428, 0.0452, 0.0485, 0.0517, 0.0549, 0.0582, 0.0614, 0.0646, 0.0687]
    _SKILL_CRABALETTA    = [0.0829, 0.0891, 0.0953, 0.1036, 0.1098, 0.1160, 0.1243, 0.1326, 0.1409, 0.1492, 0.1575, 0.1658, 0.1761]
    _SKILL_SINGER_HEAL   = [
        (0.0480, 462),  (0.0516, 508),  (0.0550, 559),  (0.0600, 612),  (0.0636, 670),
        (0.0672, 732),  (0.0720, 797),  (0.0768, 867),  (0.0816, 940),  (0.0864, 1017),
        (0.0912, 1098), (0.0960, 1183), (0.1020, 1271),
    ]
    _SKILL_USHER_HP_COST       = 0.024
    _SKILL_CHEVALMARIN_HP_COST = 0.016
    _SKILL_CRABALETTA_HP_COST  = 0.036

    # 원소 폭발 — 스킬 피해 (% Max HP, L1~L13, C3 적용 시 최대 L13)
    _BURST_DMG = [0.1141, 0.1226, 0.1312, 0.1426, 0.1511,
                  0.1597, 0.1711, 0.1825, 0.1939, 0.2053,
                  0.2167, 0.2281, 0.2424]

    # 무대 열기 → 피해 보너스 변환 비율 (% per Fanfare point, L1~L13)
    _FANFARE_DMG_INCREASE = [
        0.07, 0.09, 0.11, 0.13, 0.15,
        0.17, 0.19, 0.21, 0.23, 0.25,
        0.27, 0.29, 0.31
    ]
    _FANFARE_HEAL_BONUS = [
        0.01, 0.02, 0.03, 0.04, 0.05,
        0.06, 0.07, 0.08, 0.09, 0.10,
        0.11, 0.12, 0.13
    ]
    #endregion
    
    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 5
    BURST_LEVEL_UP_CONSTELLATION = 3
    NA_TABLES = (*_NA, _CA, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_USHER, _SKILL_CHEVALMARIN, _SKILL_CRABALETTA,)
    BURST_TABLES = (_BURST_DMG, _FANFARE_DMG_INCREASE,)

    rarity = 5

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

        for i, row in enumerate(self._NA):
            hits.append(SkillHit(f"{i+1}단 공격", SkillType.NORMAL_ATK, row[nl], ScalingStat.ATK))

        hits.append(SkillHit("강공격 피해", SkillType.CHARGED_ATK, self._CA[nl], ScalingStat.ATK))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK))

        # coeff_amp는 apply_self_buffs에서 설정되므로 기본값 1.0으로 시작
        hits += [
            SkillHit("어셔 훈작 피해",   SkillType.SKILL, self._SKILL_USHER[sk],       ScalingStat.HP, Element.HYDRO),
            SkillHit("슈벨마 부인 피해", SkillType.SKILL, self._SKILL_CHEVALMARIN[sk], ScalingStat.HP, Element.HYDRO),
            SkillHit("사발레타 씨 피해", SkillType.SKILL, self._SKILL_CRABALETTA[sk],  ScalingStat.HP, Element.HYDRO),
        ]

        hits.append(SkillHit("원소 폭발", SkillType.BURST, self._BURST_DMG[bl], ScalingStat.HP, Element.HYDRO))

        return {h.name: h for h in hits}

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        c = self.constellation

        # 살롱 멤버 coeff_amp 계산 후 해당 히트에 반영
        hp_over_half = ask_int("[푸리나 E] HP 50% 이상 파티원 수", min_val=0, max_val=4)
        self._salon_coeff_amp = 1 + 0.1 * hp_over_half
        for name in ("어셔 훈작 피해", "슈벨마 부인 피해", "사발레타 씨 피해"):
            if name in hits:
                hits[name].coeff_amp = self._salon_coeff_amp

        # A4: 원소 전투 스킬 피해 보너스
        for hit in hits.values():
            hit.add("skill_dmg_bonus", min(0.007 * self.base_hp * 0.001, 0.28), self, note="A4")

        # C2: 무대 열기 초과 → HP 최대치 증가
        if c >= 2:
            fanfare_above_limit = ask_int("[푸리나 C2] 무대 열기 초과량(400에서 최대 버프)", min_val=0, max_val=400)
            for hit in hits.values():
                hit.add("hp_pct", min(fanfare_above_limit * 0.0035, 1.4), self, note="C2 무대 초과")

    # ── 파티 버프 ─────────────────────────────────────────────────────────
    # all_dmg_bonus는 최종 스탯을 읽지 않는 고정 유저 입력 기반 버프이므로 apply_party_buffs.
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        if not ask_bool("[푸리나 Q] 성대한 카니발 사용 여부"):
            return

        c  = self.constellation
        bl = self._burst_index()

        if c >= 1:
            fanfare = ask_int("[푸리나 Q] 무대 열기", min_val=0, max_val=400)
        else:
            fanfare = ask_int("[푸리나 Q] 무대 열기", min_val=0, max_val=300)

        bonus = fanfare * self._FANFARE_DMG_INCREASE[bl] * 0.01
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.add("all_dmg_bonus", bonus, self, note="Q 무대 열기")

    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        pass  # 최종 스탯을 읽어 스케일하는 버프 없음
