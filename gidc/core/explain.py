"""히트별 버프 귀속 디버그 — explain_hit.

각 히트가 '어떤 버프로 이 숫자가 나왔는지'를 두 층으로 설명한다:
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

from gidc.core.profile import SkillHit, source_label, build_damage_context
from gidc.core.damage import DamageResult, calculate

_EPS = 1e-9

# ── 렌더링 섹션 구성 ─────────────────────────────────────────────────────────
_STAT_TRIPLES = [("공격력", "atk"), ("HP", "hp"), ("방어력", "def")]

_DMG_POOL_FIELDS = [
    "pyro_dmg_bonus", "hydro_dmg_bonus", "cryo_dmg_bonus", "electro_dmg_bonus",
    "anemo_dmg_bonus", "geo_dmg_bonus", "dendro_dmg_bonus", "physical_dmg_bonus",
    "normal_atk_dmg_bonus", "charged_atk_dmg_bonus", "plunging_dmg_bonus",
    "skill_dmg_bonus", "burst_dmg_bonus", "all_dmg_bonus", "flat_dmg_bonus",
    "lunar_reaction_base_dmg_bonus",
    "vaporize_bonus", "melt_bonus", "overloaded_bonus", "superconduct_bonus",
    "electrocharged_bonus", "swirl_bonus", "shatter_bonus", "burning_bonus",
    "bloom_bonus", "hyperbloom_bonus", "burgeon_bonus", "aggravate_bonus",
    "spread_bonus", "lunar_charged_bonus", "lunar_bloom_bonus", "lunar_crystallize_bonus",
]

# 히트가 만들어질 때 박히는 값 — 버프가 아니라 서술자다(특성 계수 등). 원장에 안 잡히는
# 것이 정상이라 '미계측'으로 셈하면 안 된다. 버프가 얹히기도 한다(스커크 뱀의 계략은
# coeff에 add()로 더한다) — 그때는 기록된 기여 + 선언값으로 갈라 보여야 맞다.
# to_text()는 이 필드들을 아예 안 찍는다. 쓰는 곳은 web_api(브라우저 화면)다.
_DECLARED_FIELDS = ["coeff", "coeff_amp"]

_CRIT_REACTION_FIELDS = [
    "crit_rate", "crit_dmg", "elemental_mastery", "energy_recharge",
    "def_reduction", "def_ignore", "elevation_multiplier",
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


def explain_hit(
    hit: SkillHit,
    *,
    enemy,
    reaction_type=None,
    dmg_type=None,
    char_level: int = 90,
) -> HitExplanation:
    # 1) 필드별 기여 수집: 가산(_ledger) + 비중첩(_unique_buffs)
    parts: dict[str, list] = defaultdict(list)
    for c in hit._ledger:
        parts[c.field].append({"source": c.source, "delta": c.delta, "note": c.note})
    for (src, fld), val in hit._unique_buffs.items():
        if abs(val) > _EPS:
            parts[fld].append({"source": source_label(src), "delta": val, "note": "비중첩"})

    # 2) 공식 트레이스 + 결과
    trace: list = []
    ctx = build_damage_context(
        hit, enemy, reaction_type=reaction_type, dmg_type=dmg_type, char_level=char_level
    )
    result = calculate(ctx, trace)

    # 3) 필드별 브레이크다운 (숫자 필드만, *_final은 파생이라 제외)
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

    return HitExplanation(hit.name, result, fbs, trace)


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
        final = base * (1.0 + pct) + flat
        if abs(final) <= _EPS and hide_zero:
            continue
        L.append(f"  {label}: {final:,.1f} = {base:,.1f} × (1 + {pct:.4f}) + {flat:,.1f}")
        for tag, fb in (("base", base_fb), ("pct", pct_fb), ("flat", flat_fb)):
            if fb and (fb.parts or abs(fb.remainder) > 1e-6):
                L.append(f"    {pre}_{tag} {fb.total:,.4f}")
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
