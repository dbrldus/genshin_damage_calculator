"""무기 자료(스펙 파일) → 무기 클래스 뼈대 + 등록 3곳.

    python tools/new_weapon.py <스펙파일>          # 검사 후 생성
    python tools/new_weapon.py <스펙파일> --check   # 검사만, 파일은 건드리지 않는다
    python tools/new_weapon.py --template          # 빈 스펙 양식 출력

이 스크립트는 **판단하지 않는다.** 패시브를 어느 훅에 어떤 필드로 넣을지는 사람(혹은 AI)이
정하고, 여기서는 손으로 타이핑하면 반드시 어긋나는 것들만 맡는다.

  · 티어 역산 — 게임 화면에 티어는 적혀 있지 않다. Lv.90 기본 공격력과 부옵션에서 각각
    독립으로 되찾고 **둘이 일치하는지 대조한다.** 어긋나면 둘 중 하나를 잘못 옮긴 것이다.
    (등록된 19개 무기 전부에서 양쪽 역산이 티어와 일치하는 것을 확인했다.)
  · 정련 배열 — 5칸인지, 단조인지, 그리고 **그 숫자열이 패시브 설명 원문에 실제로 있는지**.
    설명은 자료에서 그대로 옮겨 오므로, 배열만 고치고 설명을 안 고친 경우가 여기서 잡힌다.
  · 등록 3곳 — content/weapons/<종류>/__init__.py, content/weapons/__init__.py의 import
    묶음과 WEAPON_REGISTRY. 하나라도 빠지면 make_weapon이 DefaultWeapon으로 조용히
    대체하거나 ImportError로 죽는다.

생성한 파일의 apply_passive는 TODO로 남는다 — 관용구 후보를 주석으로 적어 둘 뿐이다.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from gidc.core import weapon_scaling as ws
from gidc.enums import StatType, WeaponType

ROOT     = pathlib.Path(__file__).resolve().parent.parent
WEAPONS  = ROOT / "gidc" / "content" / "weapons"

TEMPLATE = """\
이름: 에슈의 재앙
영문: Calamity of Eshu
종류: SWORD
성급: 4
기본공격력: 565
부옵션: ATK_PCT 27.6
패시브: 자욱한 경계

수치:
  NA_CA_DMG  = 20/25/30/35/40 %
  NA_CA_CRIT = 8/10/12/14/16 %

설명:
- 캐릭터가 보호막의 보호를 받고 있을 시:
  일반 공격과 강공격의 피해 +20/25/30/35/40%,
  일반 공격과 강공격의 치명타 확률 +8/10/12/14/16%
"""

# apply_passive를 채울 때 고를 관용구. 대부분의 무기가 이 넷 중 하나다.
IDIOMS = """\
        # ── 패시브 구현 (TODO) ────────────────────────────────────────────────
        # 아래 관용구 중 하나로 시작한다. 조건이 있으면 ask_bool로 묻되, 질문은
        # 이 메서드(Phase 3) 안에서만 한다.
        #
        # (1) 착용자 스탯 — 가장 흔하다
        #     for hit in all_hits[wearer].values():
        #         hit.add("atk_pct", self._X[r], label, note="패시브명")
        #
        # (2) 스킬 타입별 피해 보너스 — 타입 → 필드 맵을 클래스 속성으로 둔다
        #     field = self._DMG_FIELD.get(hit.skill_type)   # normal_atk_dmg_bonus 등
        #
        # (3) 파티 전원 고정 버프 — 동명의 무기끼리 중첩되지 않으므로 비중첩으로 제출
        #     for char_hits in all_hits.values():
        #         for hit in char_hits.values():
        #             hit.apply_unique_buff(label, "필드명", 값)
        #
        # (4) 착용자의 최종 스탯에 스케일 (방식 B) — 이 메서드가 아니라
        #     apply_passive_dependent(Phase 5)를 재정의하고, current_atk/def/hp()를 읽어
        #     flat_dmg_bonus 등 피해 풀로만 출력한다. 코어 스탯 되먹임 금지."""


class SpecError(Exception):
    pass


# ── 스펙 파싱 ────────────────────────────────────────────────────────────────
def parse_spec(text: str) -> dict:
    """`키: 값` 줄 + `수치:` / `설명:` 블록. 블록은 다음 최상위 키까지 이어진다."""
    spec: dict = {"수치": {}, "설명": ""}
    block = None
    body: list[str] = []

    for line in text.splitlines():
        head = re.match(r"^(이름|영문|클래스|종류|성급|기본공격력|부옵션|패시브|수치|설명)\s*:(.*)$", line)
        if head:
            key, rest = head.group(1), head.group(2).strip()
            if block:
                spec[block] = body
                body = []
            if key in ("수치", "설명"):
                block = key
                continue
            block = None
            spec[key] = rest
            continue
        if block:
            body.append(line)
    if block:
        spec[block] = body

    for key in ("이름", "영문", "종류", "성급", "기본공격력", "부옵션"):
        if not spec.get(key):
            raise SpecError(f"스펙에 '{key}' 항목이 없습니다.")

    spec["설명"] = "\n".join(spec["설명"]).strip("\n") if isinstance(spec["설명"], list) else ""
    spec["수치"] = _parse_values(spec["수치"] if isinstance(spec["수치"], list) else [])
    return spec


def _parse_values(lines: list[str]) -> dict[str, tuple[list[float], str, bool]]:
    """`이름 = 20/25/30/35/40 %` → (값 5개, 원문 숫자열, 퍼센트 여부)."""
    out = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([0-9./\s]+?)\s*(%?)$", line)
        if not m:
            raise SpecError(f"수치 줄을 읽을 수 없습니다: {line!r}\n  꼴: NAME = 20/25/30/35/40 %")
        name, raw, pct = m.group(1), m.group(2).strip(), m.group(3) == "%"
        nums = [float(x) for x in raw.split("/")]
        out[name] = (nums, raw, pct)
    return out


# ── 검증 ─────────────────────────────────────────────────────────────────────
def resolve_tier(rarity: int, base_atk: float, stat: StatType, sub_value: float) -> tuple[int, list[str]]:
    """Lv.90 기본 공격력과 부옵션에서 각각 티어를 되찾고 대조한다."""
    notes = []
    t_atk = ws.tier_from_base_atk(rarity, base_atk)
    t_sub = ws.tier_from_substat(rarity, stat, sub_value, level=90)

    exact_atk = ws.base_atk(rarity, t_atk, 90, ws.max_phase(rarity))
    exact_sub = ws.substat_value(stat, rarity, t_sub, 90)
    notes.append(f"기본 공격력 {base_atk:g} → Tier {t_atk} (표: {exact_atk:.1f})")
    notes.append(f"부옵션 {stat.name} {sub_value:g} → Tier {t_sub} (표: {exact_sub:.1f})")

    if t_atk != t_sub:
        raise SpecError(
            f"티어 역산이 어긋납니다 — 공격력은 Tier {t_atk}, 부옵션은 Tier {t_sub}를 가리킵니다.\n"
            f"  {notes[0]}\n  {notes[1]}\n"
            f"  둘 중 하나를 잘못 옮겼거나, Lv.90 값이 아닌 값을 넣었습니다."
        )
    for label, given, exact in (("기본 공격력", base_atk, exact_atk), ("부옵션", sub_value, exact_sub)):
        if abs(given - exact) > 1.0:
            notes.append(f"경고: {label} 입력 {given:g}이 표의 {exact:.1f}과 {abs(given-exact):.1f} 차이납니다.")
    return t_atk, notes


def check_values(values: dict, passive_text: str) -> list[str]:
    notes = []
    for name, (nums, raw, pct) in values.items():
        if len(nums) != 5:
            raise SpecError(f"'{name}'의 정련 값이 {len(nums)}개입니다 — 5개여야 합니다: {raw}")
        # 정련이 오를수록 커지는 값이 대부분이지만 **줄어드는** 값도 있다 — 페보니우스
        # 계열의 발동 간격 12/10.5/9/7.5/6이 그렇다. 방향은 가리지 않고, 오르내림이 섞인
        # 것만 막는다. 그건 옮겨 적다 틀린 것이다.
        steps_up   = all(b >= a for a, b in zip(nums, nums[1:]))
        steps_down = all(b <= a for a, b in zip(nums, nums[1:]))
        if not (steps_up or steps_down):
            raise SpecError(f"'{name}'이 단조 수열이 아닙니다 — 오르내림이 섞였습니다: {raw}")
        # 원문은 `12%/15%/18%/21%/24%`처럼 퍼센트가 사이사이에 낀다. 자료를 고치지 않고
        # 비교하려면 양쪽에서 기호를 걷어 내고 숫자열만 남긴다.
        flat = passive_text.replace("%", "").replace(" ", "").replace(",", "")
        if raw.replace(" ", "") not in flat:
            raise SpecError(
                f"'{name}'의 숫자열 {raw}이 패시브 설명 원문에 없습니다.\n"
                f"  배열만 고치고 설명을 안 고쳤거나, 그 반대입니다."
            )
        steps = {round(b - a, 6) for a, b in zip(nums, nums[1:])}
        if len(steps) > 1:
            notes.append(f"참고: '{name}'은 등차가 아닙니다 (증가폭 {sorted(steps)}). 자료를 한 번 더 확인하세요.")
    return notes


# ── 코드 생성 ────────────────────────────────────────────────────────────────
def camel(english: str) -> str:
    return "".join(w[:1].upper() + w[1:] for w in re.split(r"[^A-Za-z0-9]+", english) if w)


def snake(cls_name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", cls_name).lower()


def render(spec: dict, tier: int) -> str:
    cls = spec["클래스"]
    wt = WeaponType[spec["종류"]]
    stat = StatType[spec["부옵션"].split()[0]]
    rarity = int(spec["성급"])

    const_lines = []
    width = max((len(n) for n in spec["수치"]), default=0)
    for name, (nums, _raw, pct) in spec["수치"].items():
        # 소수 자리를 고정하지 않는다 — `.2f`로 자르면 7.5%가 0.07로 **조용히 틀린다**
        # (7.5/9/10.5/12/15.5 꼴의 무기가 실제로 있다). 반올림 오차가 남지 않게
        # 유효숫자로 찍고, 검사 출력과 생성된 상수가 같은 수를 말하게 둔다.
        vals = ", ".join(f"{round(n / 100, 6):g}" if pct else f"{n:g}" for n in nums)
        const_lines.append(f"    _{name:<{width}} = [{vals}]")
    consts = "\n".join(const_lines) or "    # (정련 스케일 값 없음)"

    desc = "\n".join("    " + ln if ln.strip() else "" for ln in spec["설명"].splitlines())
    passive_name = spec.get("패시브", "").strip()
    passive_line = f"    패시브: {passive_name}\n" if passive_name else ""

    return f'''from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class {cls}(Weapon):
    """{spec["이름"]} ({spec["영문"]}) | {wt.value} | {rarity}성
{passive_line}{desc}
    """

{consts}

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.{wt.name},
            rarity        = {rarity},
            tier          = {tier},
            refinement    = refinement,
            sub_stat_type = StatType.{stat.name},
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: {spec["이름"]}"

{IDIOMS}
        raise NotImplementedError("{spec['이름']} 패시브 미구현")
'''


# ── 등록 3곳 ─────────────────────────────────────────────────────────────────
def register(cls: str, module: str, wt: WeaponType, rarity: int, kr_name: str) -> list[str]:
    done = []
    type_dir = wt.name.lower()

    # (1) content/weapons/<종류>/__init__.py
    p = WEAPONS / type_dir / "__init__.py"
    line = f"from .rarity_{rarity}.{module} import {cls}\n"
    src = p.read_text(encoding="utf-8")
    if line not in src:
        p.write_text(src.rstrip("\n") + "\n" + line if src.strip() else line, encoding="utf-8")
        done.append(f"{p.relative_to(ROOT)}  ← import 추가")

    # (2)(3) content/weapons/__init__.py — import 묶음과 WEAPON_REGISTRY
    p = WEAPONS / "__init__.py"
    src = p.read_text(encoding="utf-8")

    if not re.search(rf"\b{cls}\b", src):
        group = re.search(rf"from \.{type_dir} import \(([^)]*)\)", src)
        if group:
            inner = group.group(1).rstrip()
            sep = "" if inner.endswith(",") else ","
            src = src[:group.start(1)] + inner + sep + f"\n    {cls},\n" + src[group.end(1):]
        else:
            single = re.search(rf"from \.{type_dir} import ([^\n(]+)\n", src)
            if single:
                src = src[:single.end(1)] + f", {cls}" + src[single.end(1):]
            else:
                # 그 종류의 첫 무기 — import 묶음 자체를 만든다. WEAPON_REGISTRY 바로 앞이
                # 마지막 import 자리다(파일 맨 위 블록의 끝).
                anchor = src.index("WEAPON_REGISTRY")
                src = src[:anchor] + f"from .{type_dir} import (\n    {cls},\n)\n\n" + src[anchor:]
                done.append(f"gidc/content/weapons/__init__.py  ← '.{type_dir}' import 묶음 신설")
        if not done or "묶음 신설" not in done[-1]:
            done.append("gidc/content/weapons/__init__.py  ← import 추가")

    if f'"{kr_name}"' not in src:
        m = re.search(r"(WEAPON_REGISTRY[^{]*\{)(.*?)(\n\})", src, re.S)
        if not m:
            raise SpecError("WEAPON_REGISTRY를 찾지 못했습니다.")
        body = m.group(2)
        keys = re.findall(r'\n    "([^"]+)":(\s*)', body)
        pad = max((len(k) + len(sp) for k, sp in keys), default=len(kr_name) + 1)
        entry = f'\n    "{kr_name}":{" " * max(1, pad - len(kr_name))}{cls},'
        src = src[:m.end(2)] + entry + src[m.end(2):]
        done.append("gidc/content/weapons/__init__.py  ← WEAPON_REGISTRY 등록")

    p.write_text(src, encoding="utf-8")
    return done


def main() -> None:
    ap = argparse.ArgumentParser(description="무기 스펙 → 클래스 뼈대 + 등록")
    ap.add_argument("spec", nargs="?", help="스펙 파일 경로")
    ap.add_argument("--check", action="store_true", help="검사만 하고 파일을 쓰지 않는다")
    ap.add_argument("--template", action="store_true", help="빈 스펙 양식을 출력한다")
    args = ap.parse_args()

    if args.template:
        print(TEMPLATE)
        return
    if not args.spec:
        ap.error("스펙 파일 경로가 필요합니다 (양식은 --template).")

    spec = parse_spec(pathlib.Path(args.spec).read_text(encoding="utf-8"))
    if not spec.get("클래스"):
        spec["클래스"] = camel(spec["영문"])

    wt     = WeaponType[spec["종류"]]
    rarity = int(spec["성급"])
    parts  = spec["부옵션"].split()
    stat, sub_value = StatType[parts[0]], float(parts[1])

    tier, notes = resolve_tier(rarity, float(spec["기본공격력"]), stat, sub_value)
    notes += check_values(spec["수치"], spec["설명"])

    print(f"[{spec['이름']}]  {wt.value} · {rarity}성 · Tier {tier}")
    for n in notes:
        print(f"  {n}")
    for name, (nums, _raw, pct) in spec["수치"].items():
        print(f"  _{name} = {[round(n/100, 4) if pct else n for n in nums]}")

    if args.check:
        print("\n검사만 했습니다 (--check). 파일은 그대로입니다.")
        return

    cls    = spec["클래스"]
    module = snake(cls)
    out    = WEAPONS / wt.name.lower() / f"rarity_{rarity}" / f"{module}.py"
    if out.exists():
        raise SpecError(f"이미 있습니다: {out.relative_to(ROOT)}")
    out.write_text(render(spec, tier), encoding="utf-8")
    print(f"\n{out.relative_to(ROOT)}  ← 생성")
    for line in register(cls, module, wt, rarity, spec["이름"]):
        print(line)
    print("\n다음: apply_passive를 채우고 `python tools/sync_web.py`로 웹에 반영하세요.")


if __name__ == "__main__":
    try:
        main()
    except SpecError as e:
        sys.exit(f"오류: {e}")
