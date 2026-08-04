from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from gidc.enums import DmgType, Element, ReactionType
from gidc.enums import StatType
from gidc.core.damage import DamageContext
from gidc.core.enemy import Enemy

# ── 디버그: 버프 기여 원장(explain_hit) ──────────────────────────────────────
# 각 히트 필드에 '누가 얼마를' 넣었는지 기록한다. 평상시엔 꺼져 있어(_RECORD_ENABLED=False)
# add()가 += 와 수치적으로 완전히 동일하다. explain 워크플로에서만 set_recording(True)로 켠다.
_RECORD_ENABLED = False


def set_recording(on: bool) -> None:
    """버프 기여 기록을 켜고 끈다. build_profiles() 호출 전에 켜야 원장이 채워진다."""
    global _RECORD_ENABLED
    _RECORD_ENABLED = on


def is_recording() -> bool:
    return _RECORD_ENABLED


@dataclass
class Contribution:
    """한 출처가 한 필드에 더한 가산 기여. explain_hit이 필드별로 모아 보여준다."""
    source: str
    field:  str
    delta:  float
    note:   str = ""


def source_label(source: object) -> str:
    """기여 출처(문자열/캐릭터/성유물 세트 튜플/무기 클래스 등)를 표시용 라벨로 정규화한다."""
    if isinstance(source, str):
        return source
    if isinstance(source, tuple):
        # (ArtifactSet, 4) → "천상의 문 4세트"
        if len(source) == 2 and isinstance(source[1], int):
            return f"{source_label(source[0])} {source[1]}세트"
        return " · ".join(source_label(s) for s in source)
    val = getattr(source, "value", None)      # Enum(ArtifactSet 등)
    if isinstance(val, str):
        return val
    name = getattr(source, "name", None)       # Character 인스턴스
    if isinstance(name, str) and name:
        return name
    if isinstance(source, type):               # 무기 클래스 등
        return source.__name__
    return type(source).__name__


class SkillType(Enum):
    NORMAL_ATK  = "일반 공격"
    CHARGED_ATK = "강공격"
    PLUNGING    = "낙하 공격"
    SKILL       = "원소 스킬"
    BURST       = "원소 폭발"


class ScalingStat(Enum):
    ATK = "공격력"
    HP  = "HP"
    DEF = "방어력"
    EM  = "원소 마스터리"


@dataclass
class SkillHit:
    # ── 히트 서술자 (모두 기본값 — SkillHit()로 빈 객체 생성 가능) ──────────
    name:         str            = ""
    skill_type:   SkillType      = SkillType.NORMAL_ATK
    coeff:        float          = 0.0
    scaling_stat: ScalingStat    = ScalingStat.ATK
    element:      Element | None = None

    # ── 내재 반응 ────────────────────────────────────────────────────────────
    # 히트 자체가 반응 피해 인스턴스일 때 선언한다 (달감전 피해, 만개 피해, 확산 피해 등).
    # 팀 구성에 따라 붙었다 말았다 하는 '상황적' 반응(증발 평타 등)은 여기 넣지 말고
    # build_damage_context(reaction_type=...) 인자로 넘긴다 — 아래 resolve_reaction 참고.
    #
    # dmg_type이 None이면 reaction_type에서 유도한다(_REACTION_DMG_TYPE).
    # 달반응만 유도가 불가능하므로(직접 피해/반응 피해 두 자리 모두 유효) 반드시 명시해야 한다.
    reaction_type: ReactionType   = ReactionType.NONE
    dmg_type:      DmgType | None = None

    coeff_amp:    float          = 1.0
    stat_fn:      Callable[["SkillHit"], float] | None = field(default=None, repr=False)

    # ── 기본 스탯 ────────────────────────────────────────────────────────────
    #region
    hp_base:  float = 0.0
    atk_base: float = 0.0
    def_base: float = 0.0
    #endregion

    # ── % 보너스 (additive pool) ─────────────────────────────────────────────
    #region
    hp_pct:  float = 0.0
    atk_pct: float = 0.0
    def_pct: float = 0.0
    #endregion

    # ── 고정 추가치 ──────────────────────────────────────────────────────────
    #region
    hp_flat:  float = 0.0
    atk_flat: float = 0.0
    def_flat: float = 0.0
    #endregion

    # ── 전투 스탯 ────────────────────────────────────────────────────────────
    #region
    elemental_mastery: float = 0.0
    # '다른 캐릭터 스탯의 %'로 받은 EM 지분 (무한 루프 방지 꼬리표).
    # 본인 반응엔 반영되나(elemental_mastery에 포함), 다른 %-변환의 재료로는 쓸 수 없다.
    em_from_pct_share: float = 0.0
    energy_recharge:   float = 1.0
    crit_rate:         float = 0.05
    crit_dmg:          float = 0.50
    healing_bonus:     float = 0.0
    #endregion

    # ── 원소별 피해 보너스 ───────────────────────────────────────────────────
    #region
    pyro_dmg_bonus:     float = 0.0
    hydro_dmg_bonus:    float = 0.0
    cryo_dmg_bonus:     float = 0.0
    electro_dmg_bonus:  float = 0.0
    anemo_dmg_bonus:    float = 0.0
    geo_dmg_bonus:      float = 0.0
    dendro_dmg_bonus:   float = 0.0
    physical_dmg_bonus: float = 0.0
    #endregion

    # ── 스킬 타입별 피해 보너스 ─────────────────────────────────────────────
    #region
    normal_atk_dmg_bonus:  float = 0.0
    charged_atk_dmg_bonus: float = 0.0
    plunging_dmg_bonus:    float = 0.0
    skill_dmg_bonus:       float = 0.0
    burst_dmg_bonus:       float = 0.0
    #endregion

    # ── 범용 피해 보너스 ────────────────────────────────────────────────────
    #region
    all_dmg_bonus:  float = 0.0
    flat_dmg_bonus: float = 0.0
    #endregion


    lunar_reaction_base_dmg_bonus: float = 0.0
    
    # ── 반응별 피해 보너스 ───────────────────────────────────────────────────
    #region
    vaporize_bonus:          float = 0.0
    melt_bonus:              float = 0.0
    overloaded_bonus:        float = 0.0
    superconduct_bonus:      float = 0.0
    electrocharged_bonus:    float = 0.0
    swirl_bonus:             float = 0.0
    shatter_bonus:           float = 0.0
    burning_bonus:           float = 0.0
    bloom_bonus:             float = 0.0
    hyperbloom_bonus:        float = 0.0
    burgeon_bonus:           float = 0.0
    aggravate_bonus:         float = 0.0
    spread_bonus:            float = 0.0
    lunar_charged_bonus:     float = 0.0
    lunar_bloom_bonus:       float = 0.0
    lunar_crystallize_bonus: float = 0.0
    #endregion

    # ── 반응별 치명타 스탯 ─────────────────────────────────────────────────
    #region
    vaporize_crit_rate:          float = 0.0
    vaporize_crit_dmg:           float = 0.0
    melt_crit_rate:              float = 0.0
    melt_crit_dmg:               float = 0.0
    overloaded_crit_rate:        float = 0.0
    overloaded_crit_dmg:         float = 0.0
    superconduct_crit_rate:      float = 0.0
    superconduct_crit_dmg:       float = 0.0
    electrocharged_crit_rate:    float = 0.0
    electrocharged_crit_dmg:     float = 0.0
    swirl_crit_rate:             float = 0.0
    swirl_crit_dmg:              float = 0.0
    shatter_crit_rate:           float = 0.0
    shatter_crit_dmg:            float = 0.0
    burning_crit_rate:           float = 0.0
    burning_crit_dmg:            float = 0.0
    bloom_crit_rate:             float = 0.0
    bloom_crit_dmg:              float = 0.0
    hyperbloom_crit_rate:        float = 0.0
    hyperbloom_crit_dmg:         float = 0.0
    burgeon_crit_rate:           float = 0.0
    burgeon_crit_dmg:            float = 0.0
    aggravate_crit_rate:         float = 0.0
    aggravate_crit_dmg:          float = 0.0
    spread_crit_rate:            float = 0.0
    spread_crit_dmg:             float = 0.0
    # 달반응(달감전/달개화/달결정)에는 반응 전용 추가 치명타 옵션이 게임에 존재하지 않는다.
    # 달반응 피해는 캐릭터 본인의 crit_rate/crit_dmg로 치명타 판정하므로 전용 필드를 두지 않는다.
    #endregion

    # ── 방어력 감소 / 무시 / 배율 ──────────────────────────────────────────
    #region
    def_reduction:        float = 0.0
    def_ignore:           float = 0.0
    elevation_multiplier: float = 1.0
    #endregion

    # ── 적 원소별 내성 감소 효과 ───────────────────────────────────────────────────────
    #region
    pyro_res_reduction:     float = 0.0
    hydro_res_reduction:    float = 0.0
    cryo_res_reduction:     float = 0.0
    electro_res_reduction:  float = 0.0
    anemo_res_reduction:    float = 0.0
    geo_res_reduction:      float = 0.0
    dendro_res_reduction:   float = 0.0
    physical_res_reduction: float = 0.0
    #endregion

    # ── 비중첩 버프 장부 ────────────────────────────────────────────────────
    # 동명의 소스(성유물 세트 / 무기)가 만든 버프는 중첩되지 않는다.
    # 키: (소스 식별자, 필드명) → 그 소스가 현재 이 히트에 반영해 둔 값.
    # apply_unique_buff()가 관리하며, 히트가 새로 만들어질 때마다 자동으로 비워진다.
    _unique_buffs: dict[tuple, float] = field(
        default_factory=dict, init=False, repr=False, compare=False
    )

    # ── 기여 원장 (explain_hit 디버그용) ────────────────────────────────────
    # 가산(add())으로 들어온 기여를 (출처, 필드, delta)로 순서대로 쌓는다.
    # 기록이 켜졌을 때만 채워지며, 데미지 계산에는 전혀 관여하지 않는다.
    # (비중첩 버프의 출처는 위 _unique_buffs가 이미 갖고 있어 explain_hit이 병합해 읽는다.)
    _ledger: list = field(default_factory=list, init=False, repr=False, compare=False)

    # ── 최종 스탯 (finalize() 이후 유효) ────────────────────────────────────
    hp_final:  float = field(default=0.0, init=False)
    atk_final: float = field(default=0.0, init=False)
    def_final: float = field(default=0.0, init=False)

    # ── 라이브 스탯 (finalize 타이밍과 무관하게 현재 누적값을 즉석 계산) ──────
    # 버퍼 스탯 스케일 버프는 *_final 대신 이 헬퍼로 읽어, 앞선 기여(Phase 5a)를
    # 모두 반영한 최신 스탯을 얻는다. *_final은 히트 자신의 데미지 스케일용.
    def current_hp(self)  -> float: return self.hp_base  * (1.0 + self.hp_pct)  + self.hp_flat
    def current_atk(self) -> float: return self.atk_base * (1.0 + self.atk_pct) + self.atk_flat
    def current_def(self) -> float: return self.def_base * (1.0 + self.def_pct) + self.def_flat

    def convertible_em(self) -> float:
        # %-변환 버프(EM→피해 / EM→EM)가 읽어야 하는 EM. 꼬리표 달린 지분은 제외한다.
        # (예: 설탕이 준 EM은 카즈하의 EM→원소피해 변환 계산에 들어가지 않는다.)
        return self.elemental_mastery - self.em_from_pct_share

    # ── 가산 기여 (출처 기록) ────────────────────────────────────────────────
    def add(self, field_name: str, value: float, source: object, *, note: str = "") -> None:
        """`hit.<field> += value` 와 수치적으로 동일하되, 기록이 켜져 있으면 출처를 원장에
        남긴다. 모든 가산 버프(캐릭터/세트/무기/공명)를 이 메서드로 통일하면 explain_hit이
        각 필드에 누가 얼마를 넣었는지 그대로 복원할 수 있다. 비중첩 버프는 apply_unique_buff
        (출처를 _unique_buffs에 이미 보관)를 그대로 쓴다."""
        setattr(self, field_name, getattr(self, field_name) + value)
        if _RECORD_ENABLED and value:
            self._ledger.append(Contribution(source_label(source), field_name, value, note))

    # ── 비중첩 버프 (동명 소스는 중첩되지 않음) ─────────────────────────────
    def apply_unique_buff(self, source: object, field_name: str, value: float) -> None:
        """동명의 소스가 만드는 버프를 누산한다 — 필드별로 **최댓값 하나만** 남는다.

        같은 성유물 세트/무기를 여러 명이 착용해도 파티 전체 버프는 중첩되지 않는 게임
        사양을 구현한다. 세트 인스턴스 단위로 두 번째 착용자를 통째로 무시하면 안 된다
        (예: 잿더미성 두루마리는 착용자마다 반응 참여 원소가 다르므로, 원소 필드별로
        따로 최댓값을 잡아야 불/얼음/바위가 각각 올바르게 들어간다).

        기여자마다 값을 그대로 제출하면 되고, 이미 반영된 값과의 차액만 필드에 누산하므로
        제출 순서와 무관하게 결과가 같다. 착용자 본인에게만 들어가는 효과(대부분의 2세트,
        자기 버프)는 정상적으로 중첩되므로 그냥 `+=`를 쓴다.

        source에는 버프를 만든 주체를 넣는다 — 성유물은 (ArtifactSet, 세트 수),
        무기는 무기 클래스 등. 한 필드에 같은 source로 여러 번 나눠 제출하면 최댓값
        비교가 쪼개지므로, 조건부 증가분까지 합산한 **최종 값을 한 번에** 제출한다.
        내성 감소처럼 음수로 표현되는 효과도 지원한다(같은 키에 부호를 섞지는 말 것).
        """
        slot = (source, field_name)
        prev = self._unique_buffs.get(slot, 0.0)
        if abs(value) <= abs(prev):
            return
        setattr(self, field_name, getattr(self, field_name) + (value - prev))
        self._unique_buffs[slot] = value

    def buff_value(self, source: object, field_name: str) -> float:
        """해당 소스가 이 필드에 이미 반영해 둔 비중첩 버프 값. 미적용이면 0.0.
        고정값 효과의 중복 질문을 생략할 때 쓴다."""
        return self._unique_buffs.get((source, field_name), 0.0)

    def finalize_core_stats(self) -> None:
        self.hp_final  = self.current_hp()
        self.atk_final = self.current_atk()
        self.def_final = self.current_def()

    def finalize_damage_multipliers(self) -> None:
        # Phase 7: 의존 버프(Phase 5)가 flat/pct 풀에 추가한 값을 *_final에
        # 반영하기 위해 코어 스탯을 다시 확정한다. (현재 Phase 4와 동일 연산)
        self.finalize_core_stats()


# 물리를 제외한 7원소 피해 보너스 필드 (아래 두 접근자의 단일 출처)
_ALL_ELEMENTAL_DMG_FIELDS = (
    "pyro_dmg_bonus", "hydro_dmg_bonus", "cryo_dmg_bonus", "electro_dmg_bonus",
    "anemo_dmg_bonus", "geo_dmg_bonus", "dendro_dmg_bonus",
)


def add_all_elemental_dmg_bonus(hit: SkillHit, value: float, source: object = "(미계측)") -> None:
    """7원소 피해 보너스를 모두 동일하게 증가시킨다 (물리 제외)."""
    for name in _ALL_ELEMENTAL_DMG_FIELDS:
        hit.add(name, value, source)


def add_all_elemental_dmg_bonus_unique(hit: SkillHit, source: object, value: float) -> None:
    """7원소 피해 보너스를 비중첩으로 증가시킨다 (물리 제외).
    동명의 소스가 여러 번 제출해도 원소별로 최댓값 하나만 남는다 — SkillHit.apply_unique_buff 참고."""
    for name in _ALL_ELEMENTAL_DMG_FIELDS:
        hit.apply_unique_buff(source, name, value)


# ── enum → SkillHit 필드 접두사 매핑 (아래 접근자들의 단일 출처) ──────────
# 새 원소/반응/스킬타입 추가 시 이 표만 갱신하면 관련 접근자가 모두 따라온다.
_ELEMENT_PREFIX: dict[Element, str] = {
    Element.PYRO:     "pyro",
    Element.HYDRO:    "hydro",
    Element.CRYO:     "cryo",
    Element.ELECTRO:  "electro",
    Element.ANEMO:    "anemo",
    Element.GEO:      "geo",
    Element.DENDRO:   "dendro",
    Element.PHYSICAL: "physical",
}

_SKILL_PREFIX: dict[SkillType, str] = {
    SkillType.NORMAL_ATK:  "normal_atk",
    SkillType.CHARGED_ATK: "charged_atk",
    SkillType.PLUNGING:    "plunging",
    SkillType.SKILL:       "skill",
    SkillType.BURST:       "burst",
}

_REACTION_PREFIX: dict[ReactionType, str] = {
    ReactionType.VAPORIZE:          "vaporize",
    ReactionType.MELT:              "melt",
    ReactionType.OVERLOADED:        "overloaded",
    ReactionType.SUPERCONDUCT:      "superconduct",
    ReactionType.ELECTROCHARGED:    "electrocharged",
    ReactionType.SWIRL:             "swirl",
    ReactionType.SHATTER:           "shatter",
    ReactionType.BURNING:           "burning",
    ReactionType.BLOOM:             "bloom",
    ReactionType.HYPERBLOOM:        "hyperbloom",
    ReactionType.BURGEON:           "burgeon",
    ReactionType.AGGRAVATE:         "aggravate",
    ReactionType.SPREAD:            "spread",
    ReactionType.LUNAR_CHARGED:     "lunar_charged",
    ReactionType.LUNAR_BLOOM:       "lunar_bloom",
    ReactionType.LUNAR_CRYSTALLIZE: "lunar_crystallize",
}

# StatType → 누산 대상 SkillHit 필드명
_STAT_FIELD: dict[StatType, str] = {
    StatType.HP:                "hp_flat",
    StatType.ATK:               "atk_flat",
    StatType.DEF:               "def_flat",
    StatType.HP_PCT:            "hp_pct",
    StatType.ATK_PCT:           "atk_pct",
    StatType.DEF_PCT:           "def_pct",
    StatType.ELEMENTAL_MASTERY: "elemental_mastery",
    StatType.ENERGY_RECHARGE:   "energy_recharge",
    StatType.CRIT_RATE:         "crit_rate",
    StatType.CRIT_DMG:          "crit_dmg",
    StatType.HEALING_BONUS:     "healing_bonus",
    StatType.PYRO_DMG:          "pyro_dmg_bonus",
    StatType.HYDRO_DMG:         "hydro_dmg_bonus",
    StatType.CRYO_DMG:          "cryo_dmg_bonus",
    StatType.ELECTRO_DMG:       "electro_dmg_bonus",
    StatType.ANEMO_DMG:         "anemo_dmg_bonus",
    StatType.GEO_DMG:           "geo_dmg_bonus",
    StatType.DENDRO_DMG:        "dendro_dmg_bonus",
    StatType.PHYSICAL_DMG:      "physical_dmg_bonus",
}


def apply_stat(hit: SkillHit, stat_type: StatType, value: float, source: object = "(미계측)",
               *, note: str = "") -> None:
    """StatType 하나를 SkillHit의 적절한 필드에 누산한다. Artifact와 Weapon이 공유."""
    attr = _STAT_FIELD.get(stat_type)
    if attr is not None:
        hit.add(attr, value, source, note=note)


# ── 어떤 필드를 읽을지 고르는 규칙 ───────────────────────────────────────────
# 히트마다 실제로 계산에 들어가는 필드는 한 줌뿐이다 — 냉기 히트는 cryo_dmg_bonus만,
# 폭발이면 burst_dmg_bonus만 읽는다. 그 규칙에 이름을 붙여 두면 계산(_element_dmg_bonus
# 등)과 설명(damage_input_fields)이 같은 것을 읽는다. 화면이 규칙을 베껴 들고 있으면
# 원소나 스킬 종류가 늘 때마다 조용히 어긋난다.
def element_dmg_field(element: Element) -> str | None:
    prefix = _ELEMENT_PREFIX.get(element)
    return f"{prefix}_dmg_bonus" if prefix else None


def skill_dmg_field(skill_type: SkillType) -> str | None:
    prefix = _SKILL_PREFIX.get(skill_type)
    return f"{prefix}_dmg_bonus" if prefix else None


def reaction_bonus_field(reaction_type: ReactionType) -> str | None:
    prefix = _REACTION_PREFIX.get(reaction_type)
    return f"{prefix}_bonus" if prefix else None


def element_res_reduction_field(element: Element) -> str:
    return f"{_ELEMENT_PREFIX.get(element, 'physical')}_res_reduction"


def _element_dmg_bonus(hit: SkillHit, element: Element) -> float:
    field = element_dmg_field(element)
    return getattr(hit, field) if field else 0.0


def _skill_dmg_bonus(hit: SkillHit, skill_type: SkillType) -> float:
    field = skill_dmg_field(skill_type)
    return getattr(hit, field) if field else 0.0


def _enemy_resistance(hit: SkillHit, enemy: Enemy, element: Element) -> float:
    prefix = _ELEMENT_PREFIX.get(element, "physical")
    return getattr(enemy, f"{prefix}_res") + getattr(hit, f"{prefix}_res_reduction")


def _reaction_bonus(hit: SkillHit, reaction_type: ReactionType) -> float:
    field = reaction_bonus_field(reaction_type)
    return getattr(hit, field) if field else 0.0


# 달반응은 반응 전용 치명타 필드가 없다(게임에 해당 옵션이 존재하지 않음) — 기본값 0.0.
def _reaction_crit_rate(hit: SkillHit, reaction_type: ReactionType) -> float:
    prefix = _REACTION_PREFIX.get(reaction_type)
    return getattr(hit, f"{prefix}_crit_rate", 0.0) if prefix else 0.0


def _reaction_crit_dmg(hit: SkillHit, reaction_type: ReactionType) -> float:
    prefix = _REACTION_PREFIX.get(reaction_type)
    return getattr(hit, f"{prefix}_crit_dmg", 0.0) if prefix else 0.0


# ── 반응 배율표 ──────────────────────────────────────────────────────────
# 대부분 반응별 고정값. 증발/용해는 트리거 원소, 달반응은 dmg_type에 따라 갈린다.
_REACTION_MULT_CONST: dict[ReactionType, float] = {
    ReactionType.BURNING:        0.25,
    ReactionType.SWIRL:          0.6,
    ReactionType.AGGRAVATE:      1.15,
    ReactionType.SPREAD:         1.25,
    ReactionType.SUPERCONDUCT:   1.5,
    ReactionType.ELECTROCHARGED: 2.0,
    ReactionType.BLOOM:          2.0,
    ReactionType.OVERLOADED:     2.75,
    ReactionType.BURGEON:        3.0,
    ReactionType.HYPERBLOOM:     3.0,
    ReactionType.SHATTER:        3.0,
}

# 달반응: 직접 피해(LUNAR_DIRECT) / 반응 피해(LUNAR_REACTION)에 따라 배율이 다르다.
_LUNAR_MULT: dict[ReactionType, dict[DmgType, float]] = {
    ReactionType.LUNAR_CHARGED:     {DmgType.LUNAR_DIRECT: 3.0, DmgType.LUNAR_REACTION: 1.8},
    ReactionType.LUNAR_BLOOM:       {DmgType.LUNAR_DIRECT: 1.0, DmgType.LUNAR_REACTION: 0.0},
    ReactionType.LUNAR_CRYSTALLIZE: {DmgType.LUNAR_DIRECT: 1.8, DmgType.LUNAR_REACTION: 0.96},
}

# 달반응 3종 — dmg_type이 두 자리(LUNAR_DIRECT/LUNAR_REACTION) 모두 유효한 유일한 반응.
_LUNAR_REACTIONS = frozenset(_LUNAR_MULT)

# reaction_type → dmg_type. 달반응을 제외하면 반응 타입이 계산식을 유일하게 결정한다.
_REACTION_DMG_TYPE: dict[ReactionType, DmgType] = {
    ReactionType.NONE:           DmgType.NONE,
    ReactionType.VAPORIZE:       DmgType.AMPLIFY,
    ReactionType.MELT:           DmgType.AMPLIFY,
    ReactionType.AGGRAVATE:      DmgType.CATALYZE,
    ReactionType.SPREAD:         DmgType.CATALYZE,
    ReactionType.OVERLOADED:     DmgType.TRANSFORMATIVE,
    ReactionType.SUPERCONDUCT:   DmgType.TRANSFORMATIVE,
    ReactionType.ELECTROCHARGED: DmgType.TRANSFORMATIVE,
    ReactionType.SWIRL:          DmgType.TRANSFORMATIVE,
    ReactionType.SHATTER:        DmgType.TRANSFORMATIVE,
    ReactionType.BURNING:        DmgType.TRANSFORMATIVE,
    ReactionType.BLOOM:          DmgType.TRANSFORMATIVE,
    ReactionType.HYPERBLOOM:     DmgType.TRANSFORMATIVE,
    ReactionType.BURGEON:        DmgType.TRANSFORMATIVE,
}


def resolve_reaction(
    hit:           SkillHit,
    reaction_type: ReactionType | None = None,
    dmg_type:      DmgType | None      = None,
) -> tuple[ReactionType, DmgType]:
    """히트의 내재 반응과 호출자의 상황적 반응을 합쳐 (reaction_type, dmg_type)을 확정한다.

    · 히트가 내재 반응을 선언했으면(달감전 피해 등) 그것을 쓴다 — 전역 스위치로 덮이지 않는다.
    · 선언하지 않은 히트(대부분의 평타/스킬)에만 호출자가 넘긴 상황적 반응이 적용된다.
    · dmg_type이 없으면 _REACTION_DMG_TYPE에서 유도하고, 달반응은 유도 불가라 명시를 요구한다.
    """
    if hit.reaction_type is not ReactionType.NONE:
        rt, dt = hit.reaction_type, hit.dmg_type
    else:
        rt = reaction_type if reaction_type is not None else ReactionType.NONE
        dt = dmg_type

    if dt is None:
        if rt in _LUNAR_REACTIONS:
            raise ValueError(
                f"달반응('{rt.value}')은 dmg_type을 유도할 수 없습니다. "
                f"직접 피해는 DmgType.LUNAR_DIRECT, 반응 피해는 DmgType.LUNAR_REACTION을 "
                f"히트에 명시하세요 (SkillHit(..., reaction_type=..., dmg_type=...))."
            )
        try:
            dt = _REACTION_DMG_TYPE[rt]
        except KeyError:
            raise ValueError(f"dmg_type을 유도할 수 없는 reaction_type입니다: {rt!r}") from None
    else:
        _validate_pair(rt, dt)

    return rt, dt


def _validate_pair(reaction_type: ReactionType, dmg_type: DmgType) -> None:
    """(반응, 계산식) 짝이 유효한지 확인한다 — 잘못된 조합은 조용히 오답을 내므로 즉시 실패시킨다."""
    if reaction_type in _LUNAR_REACTIONS:
        if dmg_type not in (DmgType.LUNAR_DIRECT, DmgType.LUNAR_REACTION):
            raise ValueError(
                f"달반응('{reaction_type.value}')의 dmg_type은 LUNAR_DIRECT 또는 "
                f"LUNAR_REACTION이어야 합니다. (입력: {dmg_type!r})"
            )
        return

    expected = _REACTION_DMG_TYPE.get(reaction_type)
    if expected is not None and dmg_type is not expected:
        raise ValueError(
            f"'{reaction_type.value}' 반응의 dmg_type은 {expected!r}여야 합니다. "
            f"(입력: {dmg_type!r})"
        )


# ScalingStat → 히트에서 읽을 최종 스탯 필드명
_SCALING_STAT_ATTR: dict[ScalingStat, str] = {
    ScalingStat.ATK: "atk_final",
    ScalingStat.HP:  "hp_final",
    ScalingStat.DEF: "def_final",
    ScalingStat.EM:  "elemental_mastery",
}


def _reaction_multiplier(
    reaction_type: ReactionType,
    element:       Element,
    dmg_type:      DmgType,
) -> float:
    if reaction_type in _REACTION_MULT_CONST:
        return _REACTION_MULT_CONST[reaction_type]
    if reaction_type == ReactionType.VAPORIZE:
        return 1.5 if element == Element.PYRO else 2.0
    if reaction_type == ReactionType.MELT:
        return 2.0 if element == Element.PYRO else 1.5
    if reaction_type in _LUNAR_MULT:
        return _LUNAR_MULT[reaction_type].get(dmg_type, 1.0)
    return 1.0


def build_damage_context(
    hit:   SkillHit,
    enemy: Enemy,
    *,
    reaction_type: ReactionType | None = None,
    dmg_type:      DmgType | None      = None,
    char_level:    int                 = 90,
) -> DamageContext:
    """reaction_type/dmg_type은 히트가 내재 반응을 선언하지 않은 경우에만 적용되는
    '상황적' 반응이다(증발 평타 등). 확정 규칙은 resolve_reaction 참고."""
    element = hit.element if hit.element is not None else Element.PHYSICAL

    reaction_type, dmg_type = resolve_reaction(hit, reaction_type, dmg_type)

    reaction_multiplier = _reaction_multiplier(reaction_type, element, dmg_type)

    if hit.stat_fn is not None:
        stat_value = hit.stat_fn(hit)
    else:
        stat_value = getattr(hit, _SCALING_STAT_ATTR[hit.scaling_stat])

    total_dmg_bonus = (
        _element_dmg_bonus(hit, element)
        + _skill_dmg_bonus(hit, hit.skill_type)
        + hit.all_dmg_bonus
    )

    return DamageContext(
        stat_value                    = stat_value,
        coeff                         = hit.coeff,
        dmg_type                      = dmg_type,
        coeff_amp                     = hit.coeff_amp,
        flat_dmg_bonus                = hit.flat_dmg_bonus,
        dmg_bonus                     = total_dmg_bonus,
        crit_rate                     = hit.crit_rate,
        crit_dmg                      = hit.crit_dmg,
        char_level                    = char_level,
        enemy_level                   = enemy.level,
        enemy_resistance              = _enemy_resistance(hit, enemy, element),
        def_reduction                 = hit.def_reduction,
        def_ignore                    = hit.def_ignore,
        elemental_mastery             = hit.elemental_mastery,
        reaction_multiplier           = reaction_multiplier,
        reaction_bonus                = _reaction_bonus(hit, reaction_type),
        lunar_reaction_base_dmg_bonus = hit.lunar_reaction_base_dmg_bonus,
        elevation_multiplier          = hit.elevation_multiplier,
        reaction_crit_rate            = _reaction_crit_rate(hit, reaction_type),
        reaction_crit_dmg             = _reaction_crit_dmg(hit, reaction_type),
    )


# 직접 피해 계열 — 계수 증폭·피해 보너스 풀(%DMG)·방어력 배율을 모두 쓰는 경로다.
# 격변과 달반응은 반응 피해라 셋 다 안 받는다. 달반응 직접 피해는 계수×스탯만 쓴다.
# damage.py의 _calc_* 와 어긋나면 화면에 '적용됨'으로 뜬 항목이 실제로는 안 곱해진다.
_DIRECT_DMG_TYPES    = {DmgType.NONE, DmgType.AMPLIFY, DmgType.CATALYZE}
_DMG_TYPES_WITH_STAT = _DIRECT_DMG_TYPES | {DmgType.LUNAR_DIRECT}


def damage_input_fields(
    hit:   SkillHit,
    *,
    reaction_type: ReactionType | None = None,
    dmg_type:      DmgType | None      = None,
) -> frozenset[str]:
    """이 히트의 피해에 **실제로 들어가는** SkillHit 필드 이름들.

    build_damage_context가 읽는 것과 같은 규칙이다 — 원소/스킬 종류/반응에 따라
    한 줌만 골라 읽으므로, 나머지는 값이 붙어 있어도 이 히트의 숫자에는 영향이 없다.
    (스커크 평타는 원소가 없어 물리로 계산된다 → 냉기 피해 보너스는 안 걸린다.)

    설명 화면에서 '적용되는 것만' 추리는 데 쓴다. 계산 경로에서는 부르지 않으므로
    핫패스 비용이 없다."""
    reaction_type, dmg_type = resolve_reaction(hit, reaction_type, dmg_type)
    element = hit.element if hit.element is not None else Element.PHYSICAL

    fields = {"flat_dmg_bonus", element_res_reduction_field(element)}

    # 격변 피해만 반응 전용 치명타 필드를 쓴다 (_calc_transformative). 나머지는 평소 치명타.
    if dmg_type is DmgType.TRANSFORMATIVE:
        prefix = _REACTION_PREFIX.get(reaction_type)
        if prefix:
            fields |= {f"{prefix}_crit_rate", f"{prefix}_crit_dmg"}
    else:
        fields |= {"crit_rate", "crit_dmg"}

    if dmg_type in _DMG_TYPES_WITH_STAT:
        fields.add("coeff")
        if hit.stat_fn is not None:
            # 임의의 함수라 어떤 스탯을 읽는지 알 수 없다 → 전부 후보로 남긴다.
            prefixes = ("hp", "atk", "def")
            fields.add("elemental_mastery")
        else:
            attr = _SCALING_STAT_ATTR[hit.scaling_stat]
            # atk_final 같은 파생값은 base/pct/flat 세 조각에서 나온다.
            prefixes = (attr.removesuffix("_final"),) if attr.endswith("_final") else ()
            if not prefixes:
                fields.add(attr)                    # 원소 마스터리 스케일
        for prefix in prefixes:
            fields |= {f"{prefix}_base", f"{prefix}_pct", f"{prefix}_flat"}

    if dmg_type in _DIRECT_DMG_TYPES:
        fields |= {"coeff_amp", "all_dmg_bonus", "def_reduction", "def_ignore"}
        for field in (element_dmg_field(element), skill_dmg_field(hit.skill_type)):
            if field:
                fields.add(field)

    if reaction_type is not ReactionType.NONE:
        fields.add("elemental_mastery")
        bonus = reaction_bonus_field(reaction_type)
        if bonus:
            fields.add(bonus)

    if dmg_type in (DmgType.LUNAR_DIRECT, DmgType.LUNAR_REACTION):
        fields |= {"lunar_reaction_base_dmg_bonus", "elevation_multiplier"}

    return frozenset(fields)
