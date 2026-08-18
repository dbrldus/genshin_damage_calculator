from gidc.core.character import Character, clamp_talent_index
from gidc.core.profile import SkillHit, SkillType, ScalingStat
from gidc.enums import CharacterTrait, Element
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_choice, ask_int


class Xianyun(Character):
    """한운 (Xianyun) | 바람 | 법구 | 5성 | 어센션 스탯: 공격력%

    일반 공격 : 회전 천풍으로 최대 4번 공격해 바람 원소 피해를 준다.
    강공격 : 일정 스태미나를 소모해 직선으로 날아가는 청풍의 고리를 날려 경로상의 적에게 바람 원소 피해를 준다.
    낙하 공격 : 바람 원소의 힘을 모아 공중에서 땅을 내려찍어 경로상의 적을 공격하고 착지 시 바람 원소 범위 피해를 준다.

    E : 아침 학구름
    한운이 추락 피해를 받지 않는 학구름 변신 상태로 진입해 하늘다리를 1회 발동한다.
    해당 상태에서 한운의 낙하 공격은 한운 충격파로 전환되어 바람 원소 범위 피해를 주고, 학구름 변신 상태를 종료한다. 해당 피해는 낙하 공격 피해로 간주한다.
    해당 상태에서 하늘다리를 발동할 때마다, 다음 한운 충격파의 피해와 범위가 증가한다.

    하늘다리
    공중에서 발동 가능하며, 한운이 전방으로 도약해 경로상의 적에게 바람 원소 피해를 준다.
    학구름 변신 상태 1회마다 하늘다리를 최대 3번 발동할 수 있고, 하늘다리로 동일 적에게는 최대 1회의 피해만 줄 수 있다.
    짧은 시간 내에 하늘다리를 발동하지 않으면 학구름 변신 상태가 종료된다.

    만약 학구름 변신 상태 기간 동안 한운 충격파를 발동하지 않은 경우 아침 학구름의 재사용 대기시간이 3초 감소한다.

    Q : 밤을 수놓는 대나무별
    선풍을 가볍게 불러와 바람 원소 범위 피해를 주고 주변에 있는 파티 내 모든 캐릭터의 HP를 회복한다. 회복량은 한운의 공격력의 영향을 받는다. 또한 기관 「대나무별」을 소환한다.

    대나무별
    현재 필드 위에 있는 캐릭터를 지속적으로 따라가며 간헐적으로 주변에 있는 파티 내 모든 캐릭터의 HP를 회복한다. 회복량은 한운의 공격력의 영향을 받는다.
    시작 시, 8스택의 선력 추진을 보유한다. 선력 추진 보유 시 주변에 있는 현재 필드 위 캐릭터의 점프력을 증가시킨다.
    현재 필드 위 캐릭터가 낙하 공격 완료 시, 대나무별은 1스택의 선력 추진을 소모해 바람 원소 범위 피해를 준다.
    대나무별은 필드 위에 최대 1개만 존재할 수 있다.

    A1 : 상서로운 흰서리깃 기류
    아침 학구름의 한운 충격파가 1명의 적에게 명중할 때마다, 주변에 있는 파티 내 모든 캐릭터에게 캐릭터의 낙하 공격 치명타 확률이 4%/6%/8%/10% 증가하는 「바람깃」 효과를 부여한다. 최대 중첩수: 4스택, 지속 시간: 20초.
    적에게 명중할 때마다 생성되는 「바람깃」의 지속 시간은 독립적으로 계산된다

    A4 : 동굴 속 선인?
    밤을 수놓는 대나무별의 대나무별이 선력 추진을 보유한 경우, 주변에 있는 현재 필드 위 캐릭터의 낙하 공격의 추락 충격으로 주는 피해가 증가한다.
    증가량은 한운의 공격력의 200%에 해당한다. 해당 방식으로 주변에 있는 필드 위 캐릭터의 낙하 공격의 추락 충격으로 주는 피해가 최대 9000pt 증가한다.
    한 번의 낙하 공격으로 주는 추락 충격 피해는 1명의 적에게만 적용된다. 각 캐릭터는 0.4초마다 최대 1회 발동할 수 있다

    C1 : 속세의 인연을 씻는 차풍
    아침 학구름의 사용 횟수가 1회 증가한다.

    C2 : 외딴곳에서 우는 학
    아침 학구름의 하늘다리 발동 후, 한운의 공격력이 20% 증가한다. 지속 시간: 15초.
    또한 고유 특성 「동굴 속 선인?」의 효과가 증가한다: 밤을 수놓는 대나무별의 대나무별이 선력 추진 보유 시,
    주변에 있는 현재 필드 위 캐릭터의 낙하 공격의 추락 충격으로 주는 피해가 증가한다. 증가량은 한운의 공격력의 400%에 해당한다.
    해당 방식으로 주변에 있는 필드 위 캐릭터의 낙하 공격으로 주는 추락 충격 피해가 최대 18000pt 증가한다.
    한 번의 낙하 공격으로 1명의 적에게만 추락 충격 피해를 줄 수있다. 각 캐릭터는 0.4초마다 최대 1회 발동할 수 있다.
    해당 효과는 고유 특성 「동굴 속 선인?」을 해금해야 한다

    C3 : 별과 달의 조화
    밤을 수놓는 대나무별의 스킬 레벨+3

    C4 : 오묘한 기장쌀 요리
    한 번의 아침 학구름의 학구름 변신 기간 동안 하늘다리를 1/2/3번 발동한 후,
    해당 학구름 변신 기간 동안 한운 충격파가 적에게 명중 시, 주변에 있는 파티 내 모든 캐릭터의 HP를 회복시킨다.
    회복량은 한운 공격력의 50%/80%/150%에 해당한다. 해당 효과는 5초마다 최대 1회 발동된다

    C5 : 꽃구름 누비기
    아침 학구름의 스킬 레벨+3

    C6 : 류운 선인!
    한 번의 아침 학구름의 학구름 변신 기간 동안 하늘다리를 1/2/3번 발동 후, 해당 기간 동안 한운 충격파의 치명타 피해가 15%/35%/70% 증가한다.
    한운이 밤을 수놓는 대나무별 발동 후 16초 동안 아침 학구름은 재사용 대기시간에 진입하지 않는다.
    해당 효과는 한운이 아침 학구름을 8회 발동한 후 사라진다
    """
    name = "한운"
    weapon_type = WeaponType.CATALYST


    #region ── 특성 계수 테이블 ─────────────────────────────────────────────────
    # 일반 공격 (% ATK, L1~L11) — 법구라 4단 모두 바람 원소 피해
    _NA = [
        [0.4030, 0.4330, 0.4630, 0.5040, 0.5340, 0.5640, 0.6050, 0.6450, 0.6850, 0.7250, 0.7660],
        [0.3890, 0.4180, 0.4470, 0.4860, 0.5150, 0.5440, 0.5830, 0.6220, 0.6610, 0.6990, 0.7380],
        [0.4890, 0.5250, 0.5620, 0.6110, 0.6480, 0.6840, 0.7330, 0.7820, 0.8310, 0.8800, 0.9290],
        [0.6490, 0.6980, 0.7470, 0.8110, 0.8600, 0.9090, 0.9740, 1.0390, 1.1040, 1.1690, 1.2330],
    ]

    # 강공격 「청풍의 고리」 (% ATK, L1~L11) — 스태미나 소모 50
    _CA = [1.2310, 1.3240, 1.4160, 1.5390, 1.6310, 1.7240, 1.8470, 1.9700, 2.0930, 2.2160, 2.3390]

    # 낙하 공격 (% ATK, L1~L11) — 법구 전용표 (설탕·모나·시틀라리와 같은 값).
    # 위키 표의 56.8 / 114 / 142 는 이 값을 세 자리로 자른 것이라 정밀한 공용표를 그대로 쓴다.
    _PLUNGE      = [0.5683, 0.6145, 0.6608, 0.7269, 0.7731, 0.8260, 0.8987, 0.9714, 1.0441, 1.1234, 1.2027]
    _LOW_PLUNGE  = [1.1363, 1.2288, 1.3213, 1.4535, 1.5459, 1.6517, 1.7970, 1.9423, 2.0877, 2.2462, 2.4048]
    _HIGH_PLUNGE = [1.4193, 1.5349, 1.6504, 1.8154, 1.9310, 2.0630, 2.2445, 2.4261, 2.6076, 2.8057, 3.0037]

    # 원소 스킬 「아침 학구름」 (% ATK, L1~L13, C5 적용 시 최대 L13) — CD 12초
    _SKILL_SKYLADDER = [    # 하늘다리 — 학구름 변신 상태에서 도약할 때마다 1회
        0.2480, 0.2670, 0.2850, 0.3100, 0.3290,
        0.3470, 0.3720, 0.3970, 0.4220, 0.4460,
        0.4710, 0.4960, 0.5270,
    ]
    # 한운 충격파 — **하늘다리를 몇 번 밟고 터뜨렸는가**로 계수가 갈린다.
    # E 진입 자체가 하늘다리를 1회 발동하므로 1회가 최소값이고, 변신 1회당 최대 3회다.
    # 위키가 116% / 148% / 337.6% 로 한 칸에 적어 둔 세 값이 이 1/2/3회에 대응한다.
    _SKILL_WAVE = (
        [1.1600, 1.2470, 1.3340, 1.4500, 1.5370,
         1.6240, 1.7400, 1.8560, 1.9720, 2.0880,
         2.2040, 2.3200, 2.4650],
        [1.4800, 1.5910, 1.7020, 1.8500, 1.9610,
         2.0720, 2.2200, 2.3680, 2.5160, 2.6640,
         2.8120, 2.9600, 3.1450],
        [3.3760, 3.6290, 3.8820, 4.2200, 4.4730,
         4.7260, 5.0640, 5.4020, 5.7390, 6.0770,
         6.4140, 6.7520, 7.1740],
    )

    # 원소 폭발 「밤을 수놓는 대나무별」 (% ATK, L1~L13, C3 적용 시 최대 L13)
    # 지속 16초, CD 18초, 원소 에너지 70.
    _BURST_DMG = [          # 선풍 — 발동 즉시의 바람 원소 범위 피해
        1.0800, 1.1610, 1.2420, 1.3500, 1.4310,
        1.5120, 1.6200, 1.7280, 1.8360, 1.9440,
        2.0520, 2.1600, 2.2950,
    ]
    _BURST_STARWICKER = [   # 대나무별 — 필드 위 캐릭터가 낙하 공격을 마칠 때 1스택 소모
        0.3920, 0.4210, 0.4510, 0.4900, 0.5190,
        0.5490, 0.5880, 0.6270, 0.6660, 0.7060,
        0.7450, 0.7840, 0.8330,
    ]

    # ── 고유 특성 / 명함 계수 (히트 아님 — 버프 훅에서 사용) ────────────────────
    # A1 「바람깃」 : 스택 1/2/3/4개일 때의 낙하 공격 치명타 확률 **총량**.
    # 스택당 가산이 아니라 스택 수로 값이 통째로 갈리는 표다(4→6→8→10, 스택당 +2가 아니다).
    _A1_PINION_CRIT_RATE = (0.04, 0.06, 0.08, 0.10)
    _A1_MAX_PINIONS      = 4
    # A4 「동굴 속 선인?」 : 추락 충격 피해에 한운 공격력의 200%를 더한다 (상한 9000pt).
    # C2가 같은 효과를 400% / 18000pt로 갈아끼운다 — 더하는 것이 아니라 **교체**다.
    _A4_SHOCKWAVE_ATK = 2.00
    _A4_SHOCKWAVE_CAP = 9000.0
    _C2_SHOCKWAVE_ATK = 4.00
    _C2_SHOCKWAVE_CAP = 18000.0
    # C2 : 하늘다리 발동 후 15초 동안 한운 자신의 공격력 +20%
    _C2_ATK_PCT = 0.20
    # C6 : 하늘다리 1/2/3회 뒤의 한운 충격파 치명타 피해 — 계수 표와 같은 눈금이다.
    _C6_WAVE_CRIT_DMG = (0.15, 0.35, 0.70)
    #endregion

    # ── 특성 레벨 메타데이터 (Character의 _na/_skill/_burst_index가 읽는다) ──
    SKILL_LEVEL_UP_CONSTELLATION = 5
    BURST_LEVEL_UP_CONSTELLATION = 3
    NA_TABLES    = (*_NA, _CA, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
    SKILL_TABLES = (_SKILL_SKYLADDER, *_SKILL_WAVE,)
    BURST_TABLES = (_BURST_DMG, _BURST_STARWICKER,)

    rarity         = 5
    ascension_stat = StatType.ATK_PCT

    # ── 히트 이름 (버프가 특정 히트를 집을 때 쓰는 열쇠) ────────────────────────
    # 충격파는 하늘다리 횟수마다 한 벌씩 서므로 이름도 그만큼 갈린다. 문자열을 build_hits와
    # C6 두 곳에 손으로 적으면 한쪽만 고쳐져 버프가 조용히 아무 히트에도 안 붙는다.
    @staticmethod
    def _wave_hit_name(skyladders: int) -> str:
        return f"한운 충격파 피해 (하늘다리 {skyladders}회)"

    # A4/C2가 집는 것은 낙하 공격 **전체**가 아니라 착지 순간의 「추락 충격」이다
    # (낙하 기간 피해는 대상이 아니다). 이 엔진의 추락 충격 히트는 캐릭터마다
    # 「저공/고공 추락 충격 피해」로 이름이 통일돼 있어(스커크의 섬광 변형 포함)
    # 그 이름 조각으로 고른다. 한운 자신의 충격파는 이름이 갈리므로 따로 집는다
    # (apply_dependent_buffs 참고).
    _SHOCKWAVE_HIT_MARK = "추락 충격"

    @property
    def element(self)  -> Element: return Element.ANEMO

    # ── 히트 생성 ─────────────────────────────────────────────────────────
    def build_hits(self) -> dict[str, SkillHit]:
        c = self.constellation

        # C5: 원소 스킬 레벨 +3 (최대 13)
        sk = self._skill_index()
        # C3: 원소 폭발 레벨 +3 (최대 13)
        bl = self._burst_index()
        nl = self._na_index()

        hits: list[SkillHit] = []

        # 법구 캐릭터라 일반/강/낙하 공격도 모두 바람 원소 피해다 (설탕·모나와 동일)
        for i, row in enumerate(self._NA):
            hits.append(SkillHit(f"{i+1}단 공격 피해", SkillType.NORMAL_ATK, row[nl],
                                 ScalingStat.ATK, Element.ANEMO))

        hits.append(SkillHit("강공격 피해", SkillType.CHARGED_ATK, self._CA[nl],
                             ScalingStat.ATK, Element.ANEMO))

        hits.append(SkillHit("낙하 기간 피해",     SkillType.PLUNGING, self._PLUNGE[nl],      ScalingStat.ATK, Element.ANEMO))
        hits.append(SkillHit("저공 추락 충격 피해", SkillType.PLUNGING, self._LOW_PLUNGE[nl],  ScalingStat.ATK, Element.ANEMO))
        hits.append(SkillHit("고공 추락 충격 피해", SkillType.PLUNGING, self._HIGH_PLUNGE[nl], ScalingStat.ATK, Element.ANEMO))

        hits.append(SkillHit("하늘다리 피해", SkillType.SKILL, self._SKILL_SKYLADDER[sk],
                             ScalingStat.ATK, Element.ANEMO))

        # 한운 충격파 — 계수는 원소 스킬 레벨로 스케일하지만 피해 종류는 **낙하 공격**이다
        # (원문: 「해당 피해는 낙하 공격 피해로 간주한다」). 그래서 낙하 공격 피해 보너스도
        # A1 「바람깃」의 치명타 확률도 그대로 받는다.
        #
        # 세 벌을 다 세워 두는 이유는 하늘다리를 몇 번 밟고 터뜨릴지가 로테이션 몫이라
        # 엔진이 유도할 수 없기 때문이다 — 산드로네가 전환 히트를 계열마다 세워 두는 것과
        # 같은 규약이다. 화면을 읽는 쪽이 자기 로테이션의 단을 골라 읽는다.
        for tier, table in enumerate(self._SKILL_WAVE, start=1):
            hits.append(SkillHit(self._wave_hit_name(tier), SkillType.PLUNGING, table[sk],
                                 ScalingStat.ATK, Element.ANEMO))

        hits.append(SkillHit("원소 폭발 피해", SkillType.BURST, self._BURST_DMG[bl],
                             ScalingStat.ATK, Element.ANEMO))
        hits.append(SkillHit("대나무별 피해", SkillType.BURST, self._BURST_STARWICKER[bl],
                             ScalingStat.ATK, Element.ANEMO))

        return {h.name: h for h in hits}

    # ── 개인 버프 ─────────────────────────────────────────────────────────
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        c = self.constellation

        # C2 「외딴곳에서 우는 학」 앞머리 — 받는 쪽이 한운 자신뿐이라 여기서 묻고 끝낸다.
        # 뒤에 붙은 A4 강화분은 파티원이 받으므로 Phase 5에 따로 있다.
        if c >= 2 and ask_bool("[한운 C2] 하늘다리 발동 후 15초 이내 (공격력 +20%) 여부"):
            for hit in hits.values():
                hit.add("atk_pct", self._C2_ATK_PCT, self, note="C2")

        # C6 「류운 선인!」 — 하늘다리 1/2/3회 뒤의 충격파에 각각 15%/35%/70%.
        # 조건이 곧 히트의 단이라 물을 것이 없다: 각 히트에 자기 단의 값만 얹는다.
        if c >= 6:
            for tier, crit_dmg in enumerate(self._C6_WAVE_CRIT_DMG, start=1):
                hits[self._wave_hit_name(tier)].add("crit_dmg", crit_dmg, self, note="C6")

    # ── 파티 버프 4: 유저 입력 수집 ────────────────────────────────────────
    # 한운은 코어 스탯(ATK/DEF/HP/EM)에 기여하지 않는다 — A1은 치명타 확률이라 Phase 4.5,
    # A4는 자신의 최종 공격력을 읽는 방식 B라 Phase 5다. 여기서는 입력만 한 번 모은다.
    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # A1 「바람깃」 — 충격파가 **적 1명을 명중할 때마다** 1스택이라 스택 수는 적 수와
        # 로테이션이 정한다(엔진에는 적 수 모델이 없다). 0이면 효과 자체가 없다.
        self._pinions = ask_int(
            "[한운 A1] 「바람깃」 스택 수 (파티 낙하 공격 치명타 확률)",
            min_val=0, max_val=self._A1_MAX_PINIONS,
        )

        # A4 — 대나무별의 선력 추진(8스택)이 남아 있어야 걸린다. Q를 켜 뒀는지, 스택을 다
        # 썼는지는 로테이션 몫이다.
        self._assistance = ask_bool("[한운 A4] 대나무별의 「선력 추진」 보유 여부")
        # 수혜자가 「주변에 있는 **현재 필드 위** 캐릭터」 1명이라 파티 전원에게 걸면
        # 실제보다 부풀려진다 — 누구인지 고르게 한다(이네파 A4와 같은 규약).
        self._on_field = self._ask_on_field_member(all_hits) if self._assistance else None

    def _ask_on_field_member(self, all_hits):
        """A4 대상이 될 현재 필드 위 캐릭터를 고르게 한다. 파티원이 1명뿐이면 묻지 않는다."""
        members = list(all_hits.keys())
        if len(members) == 1:
            return members[0]
        options = [
            f"{char.name} ({char.element.value})" + (" ← 한운" if char is self else "")
            for char in members
        ]
        return members[ask_choice("[한운 A4] 현재 필드 위 캐릭터", options)]

    # ── 파티 버프 4.5: 스탯을 읽지 않는 크로스 버프 ─────────────────────────
    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        # A1 「상서로운 흰서리깃 기류」 — 「파티 내 모든 캐릭터」의 낙하 공격 치명타 확률.
        # 한운 자신도 파티원이라 자기 낙하 공격·충격파에도 들어간다.
        if not self._pinions:
            return
        crit_rate = self._A1_PINION_CRIT_RATE[self._pinions - 1]
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                if hit.skill_type is SkillType.PLUNGING:
                    hit.add("crit_rate", crit_rate, self, note="A1 바람깃")

    # ── 파티 버프 5: 최종 스탯을 읽어 스케일하는 버프 (방식 B) ────────────────
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        if not self._assistance:
            return

        # C2는 A4를 **덮어쓴다**(200%/9000 → 400%/18000). 둘을 더하지 않는다.
        c2      = self.constellation >= 2
        per_atk = self._C2_SHOCKWAVE_ATK if c2 else self._A4_SHOCKWAVE_ATK
        cap     = self._C2_SHOCKWAVE_CAP if c2 else self._A4_SHOCKWAVE_CAP
        note    = "A4 (C2 강화)" if c2 else "A4"

        # 한운의 최신 공격력을 값이 아니라 **읽는 함수**로 넘긴다(지연 기여) — C2 자기
        # 공격력 버프뿐 아니라 다른 파티원이 같은 단계에서 얹어 줄 수도 있어, 여기서
        # 확정하면 파티 멤버 순서가 결과를 바꾼다. 상한도 읽는 순간에 걸린다.
        source_hit = next(iter(all_hits[self].values()))
        flat = lambda: min(source_hit.current_atk() * per_atk, cap)

        # ① 고른 필드 위 캐릭터의 추락 충격 — 원문 그대로.
        for hit in all_hits[self._on_field].values():
            if hit.skill_type is SkillType.PLUNGING and self._SHOCKWAVE_HIT_MARK in hit.name:
                hit.add("flat_dmg_bonus", flat, self, note=note)

        # ② 한운 자신의 한운 충격파 — 학구름 변신 중 한운의 낙하 공격이 통째로 바뀐 것이라
        # 이 히트가 나오는 순간의 필드 위 캐릭터는 정의상 한운이다. 그래서 ①의 선택과
        # 무관하게 항상 붙인다 — 둘을 배타로 두면 낙하 딜러를 고른 순간 한운 충격파가
        # 근거 없이 맨몸이 되는데, 실제로는 같은 로테이션의 다른 순간일 뿐이다.
        # ①과 겹치지 않는다: 충격파는 이름에 「추락 충격」이 없어 위 루프가 집지 않는다.
        for tier in range(1, len(self._SKILL_WAVE) + 1):
            all_hits[self][self._wave_hit_name(tier)].add("flat_dmg_bonus", flat, self, note=note)

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · Q 발동 회복량·대나무별 지속 회복, C4(충격파 명중 시 회복) — 이 엔진은 치유를
    #   히트로 만들지 않는다(에스코피에와 같은 취급). 회복량은 피해 계산에 들어갈 항이 없다.
    # · C1(E 사용 횟수 +1), C6 뒷문장(Q 후 16초 동안 E가 재사용 대기시간에 들어가지 않음),
    #   「충격파를 안 쓰면 CD 3초 감소」 — 로테이션 빈도지 히트 단가에 들어갈 항이 없다.
    # · A4의 「0.4초마다 1회 · 적 1명에게만」 — 추락 충격 히트가 이미 1회분 단가다.
    # · A4/C2의 고정 피해는 낙하 공격 중 **추락 충격과 한운 충격파**에만 붙는다.
    #   낙하 기간 피해는 착지 충격이 아니라 대상이 아니다(A1 「바람깃」은 낙하 공격 전체가
    #   대상이라 낙하 기간 피해에도 들어간다 — 두 특성의 범위가 다르다).
