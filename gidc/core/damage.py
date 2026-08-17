from dataclasses import dataclass

from gidc.enums import DmgType
from gidc.core.level_multiplier import LEVEL_MULTIPLIER


@dataclass
class DamageContext:

    # ── 스탯 ─────────────────────────────────────────────────────────
    stat_value: float            # 최종 스탯 (공격력 / HP / 방어력 등)
    coeff: float                 # 스킬 계수  (예: 2.5 → 250%)

    dmg_type: DmgType = DmgType.NONE
    coeff_amp: float = 1.0       # 계수 증폭
    flat_dmg_bonus: float = 0.0  # 합산 피해 증가

    # ── 피해 보너스 ──────────────────────────────────────────────────
    dmg_bonus: float = 0.0       # 원소/물리 피해 보너스 합계

    # ── 치명타 ───────────────────────────────────────────────────────
    crit_rate: float = 0.05
    crit_dmg: float = 0.50

    # ── 레벨 ─────────────────────────────────────────────────────────
    char_level: int = 90
    
    enemy_level: int = 90

    # ── 적 내성 ──────────────────────────────────────────────────────
    enemy_resistance: float = 0.10  # 내성 합산

    # ── 적 방어 ──────────────────────────────────────────────────────
    def_reduction: float = 0.0      # 방어 감소율
    def_ignore: float = 0.0         # 방어 무시율

    # ── 원소 반응 ────────────────────────────────────────────────────
    elemental_mastery: float = 0.0

    # Reaction Multiplier — dmg_type별 의미:
    #   amplify       : RM (1.5 or 2.0)
    #   catalyze      : 1.15 (Aggravate) or 1.25 (Spread)
    #   transformative: 0.25/0.6/1.5/2.0/2.75/3.0 (반응별 고정값)
    #   lunar_reaction: 1.8/0.96 for Lunar charged, crystallize
    #   lunar_direct  : 3/1/1.8 for Lunar charged, bloom, crystallize
    #   none
    reaction_multiplier: float = 1.0

    reaction_bonus: float = 0.0  # %Reaction Bonus (세트, 특성 등)

    # ── 달반응 / 별 반응 ──────────────────────────────────────────────
    # %Celestial Base DMG Bonus — 공식: × (1 + %)
    #
    # 달·별 **공용 슬롯**이다. SkillHit 쪽은 반응마다 필드가 따로 있지만
    # (lunar_charged/lunar_bloom/lunar_crystallize/stellar_conduct/stellar_swirl_base_dmg_bonus)
    # 공식에 들어가는 자리는 하나이고, 어느 필드를 여기 담을지는 이 컨텍스트를 만드는
    # profile.build_*_context가 이미 알고 있다(profile.celestial_base_dmg_bonus_field).
    #
    # 웹의 공식 트레이스 라벨은 "1+lunar_base" 그대로다 — 이 필드 이름과 묶여 있지 않은
    # 별개의 문자열이고(web_api._FORMULA_LABELS의 키), 바꾸면 저장된 화면 순서가 흔들린다.
    celestial_base_dmg_bonus: float = 0.0
    # Elevation Multiplier
    elevation_multiplier: float = 1.0

    # ── 반응 고유 치명타 (Transformative / Lunar Reaction) ──────────────
    # 기본 0.0 = 치명타 없음; 캐릭터 crit와 별도로 반응에 부여된 치명타
    reaction_crit_rate: float = 0.0
    reaction_crit_dmg: float = 0.0


@dataclass
class DamageResult:
    base_dmg: float
    non_crit: float
    crit: float
    expected: float


# ── 공통 보조 함수 ────────────────────────────────────────────────────

def resistance_mult(res: float) -> float:
    if res < 0:
        return 1.0 - res / 2.0
    elif res < 0.75:
        return 1.0 - res
    else:
        return 1.0 / (4.0 * res + 1.0)


def defense_mult(
    char_level: int,
    enemy_level: int,
    def_reduction: float = 0.0,
    def_ignore: float = 0.0,
) -> float:
    char_factor  = char_level + 100
    enemy_factor = (enemy_level + 100) * (1.0 - def_reduction) * (1.0 - def_ignore)
    return char_factor / (char_factor + enemy_factor)


def em_amplifying_bonus(em: float) -> float:
    return 2.78 * em / (em + 1400) if em > 0 else 0.0

def em_transformative_bonus(em: float) -> float:
    return 16.0 * em / (em + 2000) if em > 0 else 0.0

def em_catalyze_bonus(em: float) -> float:
    return 5.0 * em / (em + 1200) if em > 0 else 0.0

def em_lunar_bonus(em: float) -> float:
    return 6.0 * em / (em + 2000) if em > 0 else 0.0



def _to_result(
    base_dmg: float,
    combined_mult: float,
    crit_rate: float,
    crit_dmg: float,
    trace: list | None = None,
) -> DamageResult:
    non_crit = base_dmg * combined_mult
    crit     = base_dmg * combined_mult * (1.0 + crit_dmg)
    crit_rate = max(0, min(crit_rate, 1))
    expected = non_crit * (1.0 - crit_rate) + crit * crit_rate
    if trace is not None:
        _t(trace, "base_dmg",      base_dmg)
        _t(trace, "combined_mult", combined_mult)
        _t(trace, "crit_mult",     1.0 + crit_dmg)
        _t(trace, "non_crit",      non_crit)
        _t(trace, "crit",          crit)
        _t(trace, "expected",      expected, note=f"crit_rate={crit_rate:.3f}")
    return DamageResult(base_dmg=base_dmg, non_crit=non_crit, crit=crit, expected=expected)


def _t(trace: list | None, term: str, value: float, *, note: str = "") -> None:
    """공식 트레이스 스텝을 기록한다(explain_hit Layer 2). trace가 None이면 무시 → 핫패스 무비용."""
    if trace is not None:
        trace.append({"term": term, "value": value, "note": note})


# ── 반응별 계산 함수 ──────────────────────────────────────────────────

def _calc_no_reaction(ctx: DamageContext, trace: list | None = None) -> DamageResult:
    base_dmg = ctx.coeff * ctx.stat_value * ctx.coeff_amp + ctx.flat_dmg_bonus

    def_m = defense_mult(ctx.char_level, ctx.enemy_level, ctx.def_reduction, ctx.def_ignore)
    res_m = resistance_mult(ctx.enemy_resistance)
    combined_mult = (1.0 + ctx.dmg_bonus) * def_m * res_m

    if trace is not None:
        _t(trace, "coeff", ctx.coeff); _t(trace, "stat", ctx.stat_value)
        _t(trace, "coeff_amp", ctx.coeff_amp); _t(trace, "flat_dmg_bonus", ctx.flat_dmg_bonus)
        _t(trace, "1+dmg_bonus", 1.0 + ctx.dmg_bonus)
        _t(trace, "def_mult", def_m); _t(trace, "res_mult", res_m)
    return _to_result(base_dmg, combined_mult, ctx.crit_rate, ctx.crit_dmg, trace)


def _calc_amplifying(ctx: DamageContext, trace: list | None = None) -> DamageResult:
    """AM = Reaction Multiplier × (1 + %EM Bonus + %Reaction Bonus)"""
    base_dmg = ctx.coeff * ctx.stat_value * ctx.coeff_amp + ctx.flat_dmg_bonus

    em_bonus     = em_amplifying_bonus(ctx.elemental_mastery)
    amplify_mult = ctx.reaction_multiplier * (1.0 + em_bonus + ctx.reaction_bonus)

    def_m = defense_mult(ctx.char_level, ctx.enemy_level, ctx.def_reduction, ctx.def_ignore)
    res_m = resistance_mult(ctx.enemy_resistance)
    combined_mult = (1.0 + ctx.dmg_bonus) * def_m * res_m * amplify_mult

    if trace is not None:
        _t(trace, "coeff", ctx.coeff); _t(trace, "stat", ctx.stat_value)
        _t(trace, "coeff_amp", ctx.coeff_amp); _t(trace, "flat_dmg_bonus", ctx.flat_dmg_bonus)
        _t(trace, "1+dmg_bonus", 1.0 + ctx.dmg_bonus)
        _t(trace, "reaction_mult", ctx.reaction_multiplier)
        _t(trace, "em_bonus", em_bonus); _t(trace, "reaction_bonus", ctx.reaction_bonus)
        _t(trace, "amplify_mult", amplify_mult)
        _t(trace, "def_mult", def_m); _t(trace, "res_mult", res_m)
    return _to_result(base_dmg, combined_mult, ctx.crit_rate, ctx.crit_dmg, trace)


def _calc_catalyze(ctx: DamageContext, trace: list | None = None) -> DamageResult:
    """Additive Base DMG Bonus = Reaction Multiplier × Level Multiplier × (1 + %EM + %Reaction)"""
    em_bonus      = em_catalyze_bonus(ctx.elemental_mastery)
    lv_mult       = LEVEL_MULTIPLIER[ctx.char_level]
    additive_flat = ctx.reaction_multiplier * lv_mult * (1.0 + em_bonus + ctx.reaction_bonus)

    base_dmg = ctx.coeff * ctx.stat_value * ctx.coeff_amp + ctx.flat_dmg_bonus + additive_flat

    def_m = defense_mult(ctx.char_level, ctx.enemy_level, ctx.def_reduction, ctx.def_ignore)
    res_m = resistance_mult(ctx.enemy_resistance)
    combined_mult = (1.0 + ctx.dmg_bonus) * def_m * res_m

    if trace is not None:
        _t(trace, "coeff", ctx.coeff); _t(trace, "stat", ctx.stat_value)
        _t(trace, "coeff_amp", ctx.coeff_amp); _t(trace, "flat_dmg_bonus", ctx.flat_dmg_bonus)
        _t(trace, "additive_flat(촉진/발산)", additive_flat)
        _t(trace, "em_bonus", em_bonus); _t(trace, "reaction_bonus", ctx.reaction_bonus)
        _t(trace, "1+dmg_bonus", 1.0 + ctx.dmg_bonus)
        _t(trace, "def_mult", def_m); _t(trace, "res_mult", res_m)
    return _to_result(base_dmg, combined_mult, ctx.crit_rate, ctx.crit_dmg, trace)


def _calc_transformative(ctx: DamageContext, trace: list | None = None) -> DamageResult:
    """DMG = (Reaction Multiplier × Level Multiplier × (1 + %EM + %Reaction) + Additive Base) × RES × CRIT"""
    em_bonus = em_transformative_bonus(ctx.elemental_mastery)
    lv_mult  = LEVEL_MULTIPLIER[ctx.char_level]
    base_dmg = (
        ctx.reaction_multiplier * lv_mult * (1.0 + em_bonus + ctx.reaction_bonus)
        + ctx.flat_dmg_bonus
    )

    res_m = resistance_mult(ctx.enemy_resistance)
    if trace is not None:
        _t(trace, "reaction_mult", ctx.reaction_multiplier); _t(trace, "lv_mult", lv_mult)
        _t(trace, "em_bonus", em_bonus); _t(trace, "reaction_bonus", ctx.reaction_bonus)
        _t(trace, "flat_dmg_bonus", ctx.flat_dmg_bonus); _t(trace, "res_mult", res_m)
    return _to_result(base_dmg, res_m, ctx.reaction_crit_rate, ctx.reaction_crit_dmg, trace)


def _calc_lunar_direct(ctx: DamageContext, trace: list | None = None) -> DamageResult:
    """달반응 직접 피해: RM × 계수 × 스탯 × (1 + %Lunar Base) × (1 + %EM + %Reaction) × RES × Elevation × CRIT

    원소/스킬 피해 보너스(%DMG)는 곱해지지 않는다 — 달반응 직접 피해는 반응 피해 계열이라
    일반 피해 보너스를 받지 않는다.

    **별 반응 직접 피해(STELLAR_DIRECT)도 이 함수를 탄다** — 공식이 같다. 계열마다 다른 것은
    RM과 기초 피해 증가 필드뿐이고, 둘 다 컨텍스트를 만드는 쪽에서 이미 정해져 들어온다.
    공식을 복제하면 한쪽만 고쳐져 갈라지므로 나누지 않는다. 세 번째 계열이 생기는 순간이
    이 함수 이름을 계열 중립으로 바꿀 시점이다."""
    em_bonus = em_lunar_bonus(ctx.elemental_mastery)

    base_dmg = (ctx.reaction_multiplier
                * ctx.coeff * ctx.stat_value
                * (1.0 + ctx.celestial_base_dmg_bonus)
                * (1.0 + em_bonus + ctx.reaction_bonus)
                ) + ctx.flat_dmg_bonus

    res_m = resistance_mult(ctx.enemy_resistance)
    combined_mult = res_m * ctx.elevation_multiplier

    if trace is not None:
        _t(trace, "reaction_mult", ctx.reaction_multiplier)
        _t(trace, "coeff", ctx.coeff); _t(trace, "stat", ctx.stat_value)
        _t(trace, "1+lunar_base", 1.0 + ctx.celestial_base_dmg_bonus)
        _t(trace, "em_bonus", em_bonus); _t(trace, "reaction_bonus", ctx.reaction_bonus)
        _t(trace, "1+em+reaction", 1.0 + em_bonus + ctx.reaction_bonus)
        _t(trace, "flat_dmg_bonus", ctx.flat_dmg_bonus)
        _t(trace, "res_mult", res_m); _t(trace, "elevation", ctx.elevation_multiplier)
    return _to_result(base_dmg, combined_mult, ctx.crit_rate, ctx.crit_dmg, trace)


def _calc_lunar_reaction(ctx: DamageContext, trace: list | None = None) -> DamageResult:
    """DMG = RM_Indirect × LvMult × (1 + %Lunar Base) × (1 + %EM + %Reaction) × Elevation × RES × CRIT

    별 반응 반응 피해(STELLAR_REACTION)도 이 함수를 탄다 — _calc_lunar_direct와 같은 이유다."""
    em_bonus = em_lunar_bonus(ctx.elemental_mastery)
    lv_mult  = LEVEL_MULTIPLIER[ctx.char_level]
    base_dmg = (
        ctx.reaction_multiplier
        * lv_mult
        * (1.0 + ctx.celestial_base_dmg_bonus)
        * (1.0 + em_bonus + ctx.reaction_bonus)
    )

    res_m = resistance_mult(ctx.enemy_resistance)
    combined_mult = res_m * ctx.elevation_multiplier

    if trace is not None:
        _t(trace, "reaction_mult", ctx.reaction_multiplier); _t(trace, "lv_mult", lv_mult)
        _t(trace, "1+lunar_base", 1.0 + ctx.celestial_base_dmg_bonus)
        _t(trace, "em_bonus", em_bonus); _t(trace, "reaction_bonus", ctx.reaction_bonus)
        _t(trace, "res_mult", res_m); _t(trace, "elevation", ctx.elevation_multiplier)
    return _to_result(base_dmg, combined_mult, ctx.crit_rate, ctx.crit_dmg, trace)


# ── 진입점 ────────────────────────────────────────────────────────────

_DISPATCH = {
    DmgType.NONE:           _calc_no_reaction,
    DmgType.AMPLIFY:        _calc_amplifying,
    DmgType.CATALYZE:       _calc_catalyze,
    DmgType.LUNAR_DIRECT:   _calc_lunar_direct,
    DmgType.TRANSFORMATIVE: _calc_transformative,
    DmgType.LUNAR_REACTION: _calc_lunar_reaction,
    # 별 반응은 달반응과 **같은 공식**을 탄다. 계열마다 다른 것은 반응 배율과 기초 피해 증가
    # 필드뿐이고, 둘 다 profile.build_*_context가 컨텍스트에 담아 넘긴다.
    DmgType.STELLAR_DIRECT:   _calc_lunar_direct,
    DmgType.STELLAR_REACTION: _calc_lunar_reaction,
}


def calculate(ctx: DamageContext, trace: list | None = None) -> DamageResult:
    """trace에 리스트를 주면 공식 각 항을 라벨과 함께 append 한다(explain_hit Layer 2).
    기본값 None이면 아무 것도 기록하지 않아 일반 계산 경로에 영향이 없다."""
    calc_fn = _DISPATCH.get(ctx.dmg_type)
    if calc_fn is None:
        raise ValueError(f"알 수 없는 dmg_type: {ctx.dmg_type!r}")
    return calc_fn(ctx, trace)
