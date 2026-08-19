"""버프 귀속 디버그 — explain_hit(직접 피해) / explain_transformative(격변 반응 1회) /
explain_party_reaction(달·별 반응 반응 피해에서 참여자 한 명의 몫).

'어떤 버프로 이 숫자가 나왔는지'를 두 층으로 설명한다:
  Layer 1 (버프 출처): 각 필드에 누가 얼마를 더했는지.
      · 가산 버프 → SkillHit._ledger (add()가 기록)
      · 비중첩 버프 → SkillHit._unique_buffs (apply_unique_buff가 이미 보관)
  Layer 2 (공식 트레이스): 그 최종 필드들이 Damage.py에서 어떻게 곱해져 숫자가 됐는지.

아직 add()로 마이그레이션되지 않은 가산 버프는 원장에 안 잡히므로, 각 필드의
'미계측(기타)' 나머지 = 실제값 - 초기값 - 기록된 기여 로 정직하게 표기한다. 마이그레이션이
진행될수록 이 나머지가 0으로 수렴한다.

사용:
    from gidc.core.profile import set_recording
    set_recording(True)                  # build_profiles() 전에 켠다
    all_hits = party.build_profiles()
    exp = explain_hit(all_hits[char][hit_name], enemy=enemy)
    print(exp.to_text())
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, fields, MISSING, field as dc_field

from gidc.core.profile import (
    SkillHit, source_label, build_damage_context, build_transformative_context,
)
# build_{lunar,stellar}_reaction_context는 여기서 import하지 않는다 —
# explain_party_reaction이 빌더를 인자로 받으므로 어느 계열인지 고르는 쪽은 호출자다.
from gidc.core.damage import DamageResult, calculate

_EPS = 1e-9

# ── 렌더링 섹션 구성 ─────────────────────────────────────────────────────────
_STAT_TRIPLES = [("공격력", "atk"), ("HP", "hp"), ("방어력", "def")]

# 코어 스탯에 더해지지만 이름이 「{접두}_flat」이 아닌 슬롯.
# 최종 스탯 조립식(profile.SkillHit.current_atk 등)에 들어가므로 여기서도 같이 더해야
# 화면의 「공격력 = base × (1+pct) + flat」 줄이 atk_final과 어긋나지 않는다.
# atk_flat_derived는 「공격력에서 파생된 공격력」 꼬리표다 — 최종 공격력에는 들어가되
# 공격력→공격력 변환의 재료에서만 빠진다(profile.convertible_atk 참고).
_EXTRA_FLAT_FIELDS: dict[str, tuple[str, ...]] = {"atk": ("atk_flat_derived",)}

_DMG_POOL_FIELDS = [
    "pyro_dmg_bonus", "hydro_dmg_bonus", "cryo_dmg_bonus", "electro_dmg_bonus",
    "anemo_dmg_bonus", "geo_dmg_bonus", "dendro_dmg_bonus", "physical_dmg_bonus",
    "normal_atk_dmg_bonus", "charged_atk_dmg_bonus", "plunging_dmg_bonus",
    "skill_dmg_bonus", "burst_dmg_bonus", "all_dmg_bonus", "flat_dmg_bonus",
    # 달·별 반응의 기초 피해 증가는 반응별로 나뉘어 있다 — 「달감전만」 올리는 버프(이네파
    # Moonsign)가 달개화·달결정까지 올리면 안 되기 때문이다(profile.celestial_base_dmg_bonus_field).
    "lunar_charged_base_dmg_bonus", "lunar_bloom_base_dmg_bonus",
    "lunar_crystallize_base_dmg_bonus",
    "stellar_conduct_base_dmg_bonus", "stellar_swirl_base_dmg_bonus",
    "vaporize_bonus", "melt_bonus", "overloaded_bonus", "superconduct_bonus",
    "electrocharged_bonus", "swirl_bonus", "shatter_bonus", "burning_bonus",
    "bloom_bonus", "hyperbloom_bonus", "burgeon_bonus", "aggravate_bonus",
    "spread_bonus", "lunar_charged_bonus", "lunar_bloom_bonus", "lunar_crystallize_bonus",
    "stellar_conduct_bonus", "stellar_swirl_bonus",
]

# 히트가 만들어질 때 박히는 값 — 버프가 아니라 서술자다(특성 계수 등). 원장에 안 잡히는
# 것이 정상이라 '미계측'으로 셈하면 안 된다. 버프가 얹히기도 한다(스커크 뱀의 계략은
# coeff에 add()로 더한다) — 그때는 기록된 기여 + 선언값으로 갈라 보여야 맞다.
# to_text()는 이 필드들을 아예 안 찍는다. 쓰는 곳은 web_api(브라우저 화면)다.
_DECLARED_FIELDS = ["coeff", "coeff_amp"]

_CRIT_REACTION_FIELDS = [
    "crit_rate", "crit_dmg", "elemental_mastery", "energy_recharge",
    "def_reduction", "def_ignore", "elevation_multiplier",
    # 별 반응 계수의 재료. 계수를 바꾸는 값이라 「이 숫자가 왜 그런지」에 답하려면 보여야 한다.
    "stellar_recorded_hits", "stellar_gust_level",
    "pyro_res_reduction", "hydro_res_reduction", "cryo_res_reduction",
    "electro_res_reduction", "anemo_res_reduction", "geo_res_reduction",
    "dendro_res_reduction", "physical_res_reduction",
]


@dataclass
class FieldBreakdown:
    field:    str
    total:    float          # 실제 최종값
    baseline: float          # 데이터클래스 기본값 (crit_rate 0.05 등)
    parts:    list           # [{"source", "delta", "note"}]

    @property
    def recorded(self) -> float:
        return sum(p["delta"] for p in self.parts)

    @property
    def remainder(self) -> float:
        return self.total - self.baseline - self.recorded

    def has_content(self) -> bool:
        return bool(self.parts) or abs(self.total - self.baseline) > _EPS


@dataclass
class HitExplanation:
    name:    str
    result:  DamageResult
    fields:  dict            # field_name -> FieldBreakdown
    formula: list            # Layer 2 트레이스 스텝

    def to_text(self, *, hide_zero: bool = True) -> str:
        return _render(self, hide_zero=hide_zero)


# ── 기본값 테이블 (초기값 baseline) ──────────────────────────────────────────
def _skillhit_defaults() -> dict:
    d = {}
    for f in fields(SkillHit):
        if f.default is not MISSING and isinstance(f.default, (int, float)):
            d[f.name] = float(f.default)
        else:
            d[f.name] = 0.0
    return d


_DEFAULTS = _skillhit_defaults()


def _collect_parts(hit: SkillHit) -> dict[str, list]:
    """필드별 기여 수집: 가산(_ledger) + 비중첩(_unique_buffs)."""
    parts: dict[str, list] = defaultdict(list)
    for c in hit._ledger:
        parts[c.field].append({"source": c.source, "delta": c.delta, "note": c.note})
    for (src, fld), val in hit._unique_buffs.items():
        if abs(val) > _EPS:
            parts[fld].append({"source": source_label(src), "delta": val, "note": "비중첩"})
    return parts


def _field_breakdowns(hit: SkillHit, parts: dict[str, list]) -> dict[str, FieldBreakdown]:
    """숫자 필드만 브레이크다운으로. *_final은 파생이라 제외한다."""
    fbs: dict[str, FieldBreakdown] = {}
    for f in fields(SkillHit):
        name = f.name
        if name.startswith("_") or name.endswith("_final"):
            continue
        val = getattr(hit, name)
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            continue
        fb = FieldBreakdown(name, float(val), _DEFAULTS.get(name, 0.0), parts.get(name, []))
        if fb.has_content():
            fbs[name] = fb
    return fbs


def explain_hit(
    hit: SkillHit,
    *,
    enemy,
    reaction_type=None,
    dmg_type=None,
    char_level: int = 90,
) -> HitExplanation:
    parts = _collect_parts(hit)

    trace: list = []
    ctx = build_damage_context(
        hit, enemy, reaction_type=reaction_type, dmg_type=dmg_type, char_level=char_level
    )
    result = calculate(ctx, trace)

    return HitExplanation(hit.name, result, _field_breakdowns(hit, parts), trace)


def explain_transformative(
    carrier: SkillHit,
    *,
    enemy,
    reaction,
    element,
    char_level: int = 90,
) -> HitExplanation:
    """격변 반응 1회의 설명. explain_hit과 같은 모양을 돌려주므로 화면이 그대로 재사용한다.

    carrier는 **스탯·버프 캐리어**일 뿐 때리는 히트가 아니다 — 격변은 트리거한 캐릭터의
    EM·반응 보너스·내성 감소만으로 정해지므로 그 캐릭터의 히트 아무 것이나 넘기면 된다
    (build_transformative_context와 같은 규약). 그래서 Layer 1(버프 출처)은 캐리어의
    원장에서 그대로 읽고, Layer 2(공식)만 격변 경로로 돈다.

    element는 **피해 원소**다 — 반응이 정하며 캐리어의 원소가 아니다.
    어떤 필드가 실제로 이 숫자에 들어가는지는 profile.transformative_input_fields가 답한다.
    """
    parts = _collect_parts(carrier)

    trace: list = []
    ctx = build_transformative_context(
        carrier, enemy, reaction=reaction, element=element, char_level=char_level
    )
    result = calculate(ctx, trace)

    name = f"{reaction.value} ({element.value} 피해)"
    return HitExplanation(name, result, _field_breakdowns(carrier, parts), trace)


def explain_party_reaction(
    carrier: SkillHit,
    *,
    enemy,
    reaction,
    element,
    build_context,
    char_level: int = 90,
) -> HitExplanation:
    """달·별 반응 반응 피해에서 **참여자 한 명의 몫**을 설명한다(가중치를 곱하기 전 값).

    explain_transformative와 같은 규약이다 — carrier는 스탯·버프 캐리어일 뿐 때리는 히트가
    아니고, Layer 1(버프 출처)은 캐리어 원장에서 그대로 읽고 Layer 2(공식)만 이 경로로 돈다.

    build_context가 계열을 가른다 — profile.build_lunar_reaction_context 또는
    build_stellar_reaction_context. core.party_reaction.party_reaction_damage와 같은 규약이며,
    같은 반응 행을 설명하려면 **그쪽과 같은 빌더를 넘겨야** 숫자가 맞는다.
    기본값을 두지 않는 이유가 그것이다 — 빠뜨렸을 때 조용히 다른 계열로 설명하는 대신
    TypeError로 즉시 실패해야 한다.

    파티 가중합은 여기서 다루지 않는다 — 참여자 목록과 가중치는 core.party_reaction이 갖고
    있고, 이 함수는 그중 한 명의 숫자가 왜 그런지에만 답한다.
    어떤 필드가 실제로 들어가는지는 profile.{lunar,stellar}_reaction_input_fields가 답한다.
    """
    parts = _collect_parts(carrier)

    trace: list = []
    ctx = build_context(
        carrier, enemy, reaction=reaction, element=element, char_level=char_level
    )
    result = calculate(ctx, trace)

    name = f"{reaction.value} ({element.value} 피해)"
    return HitExplanation(name, result, _field_breakdowns(carrier, parts), trace)


# ── 텍스트 렌더러 ────────────────────────────────────────────────────────────
def _fmt(v: float) -> str:
    return f"{v:,.4f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def _render_parts(fb: FieldBreakdown, indent: str) -> list[str]:
    lines = []
    for p in sorted(fb.parts, key=lambda x: -abs(x["delta"])):
        note = f"  ({p['note']})" if p["note"] else ""
        lines.append(f"{indent}{p['source']:<22} {p['delta']:+.4f}{note}")
    rem = fb.remainder
    if abs(rem) > 1e-6:
        lines.append(f"{indent}{'미계측(기타)':<22} {rem:+.4f}")
    return lines


def _render(exp: HitExplanation, *, hide_zero: bool) -> str:
    L: list[str] = []
    r = exp.result
    L.append(f"[히트] {exp.name}")
    L.append(f"  non_crit={r.non_crit:,.0f}  crit={r.crit:,.0f}  expected={r.expected:,.0f}")

    # ■ 스탯 조립
    L.append("\n■ 스탯 조립")
    for label, pre in _STAT_TRIPLES:
        base_fb = exp.fields.get(f"{pre}_base")
        pct_fb  = exp.fields.get(f"{pre}_pct")
        flat_fb = exp.fields.get(f"{pre}_flat")
        base = base_fb.total if base_fb else _DEFAULTS[f"{pre}_base"]
        pct  = pct_fb.total  if pct_fb  else _DEFAULTS[f"{pre}_pct"]
        flat = flat_fb.total if flat_fb else _DEFAULTS[f"{pre}_flat"]
        # 이름이 「{접두}_flat」이 아닌 고정 슬롯도 최종 스탯에 들어간다 (_EXTRA_FLAT_FIELDS).
        extras = [(n, exp.fields.get(n)) for n in _EXTRA_FLAT_FIELDS.get(pre, ())]
        flat += sum((fb.total if fb else _DEFAULTS[n]) for n, fb in extras)
        final = base * (1.0 + pct) + flat
        if abs(final) <= _EPS and hide_zero:
            continue
        L.append(f"  {label}: {final:,.1f} = {base:,.1f} × (1 + {pct:.4f}) + {flat:,.1f}")
        for tag, fb in (("base", base_fb), ("pct", pct_fb), ("flat", flat_fb)):
            if fb and (fb.parts or abs(fb.remainder) > 1e-6):
                L.append(f"    {pre}_{tag} {fb.total:,.4f}")
                L.extend(_render_parts(fb, "      "))
        for name, fb in extras:
            if fb and (fb.parts or abs(fb.remainder) > 1e-6):
                L.append(f"    {name} {fb.total:,.4f}")
                L.extend(_render_parts(fb, "      "))

    # ■ 피해 보너스 풀
    pool_lines = []
    for name in _DMG_POOL_FIELDS:
        fb = exp.fields.get(name)
        if fb and fb.has_content():
            pool_lines.append(f"  {name} = {_fmt(fb.total)}")
            pool_lines.extend(_render_parts(fb, "    "))
    if pool_lines:
        L.append("\n■ 피해 보너스 풀")
        L.extend(pool_lines)

    # ■ 치명타 / 반응 / 기타
    cr_lines = []
    for name in _CRIT_REACTION_FIELDS:
        fb = exp.fields.get(name)
        if fb and fb.has_content():
            cr_lines.append(f"  {name} = {_fmt(fb.total)}")
            cr_lines.extend(_render_parts(fb, "    "))
    if cr_lines:
        L.append("\n■ 치명타 / 반응 / 기타")
        L.extend(cr_lines)

    # ■ 공식 (Layer 2)
    if exp.formula:
        L.append("\n■ 공식 (Layer 2)")
        for s in exp.formula:
            note = f"   {s['note']}" if s.get("note") else ""
            L.append(f"  {s['term']:<26} {s['value']:,.4f}{note}")

    return "\n".join(L)
