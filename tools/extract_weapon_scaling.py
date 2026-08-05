"""무기 레벨 스케일링 자료를 엑셀에서 뽑아 CSV로 굽는다.

    python tools/extract_weapon_scaling.py [엑셀경로]

캐릭터 쪽(tools/extract_level_scaling.py)과 같은 역할이다 — 원본 엑셀은 저장소 밖에서도
바뀔 수 있고 openpyxl 없이는 못 읽는다. 엔진이 읽는 것은 여기서 만든
gidc/core/data/weapon_level_scaling/*.csv 다섯 장뿐이다.

무기는 **기본 공격력과 부옵션이 서로 다른 규칙**을 따른다. 표를 나눠 두는 이유다.

    기본 공격력 = 기초값(성급·티어) × 레벨 배율(성급·티어·레벨) + 돌파 보너스(성급·단계)
    부옵션      = 기초값(스탯·성급·티어) × 레벨 배율(레벨)

  · 기본 공격력은 **매 레벨** 오르고 돌파 보너스를 따로 받는다.
  · 부옵션은 **5레벨마다** 오르고 돌파 보너스가 없다 — 그래서 배율 표가 19행뿐이고,
    성급·티어·스탯 종류와 무관하게 열이 하나다.

엑셀 시트 열 중 넷을 그대로 쓰고, 부옵션 시트 여섯 장은 **Lv.1 행만** 쓴다. 나머지 행은
「Lv.1 × 배율」로 재생성되므로 옮겨 적을 이유가 없고, 오히려 원소 마스터리 시트는 소수
1자리로 반올림돼 있어 계산하는 쪽이 정확하다. 그래도 버리기 전에 전부 대조한다
(_check_secondary_sheets).

「티어」는 엑셀이 부옵션 시트에서 t-38, t-44b 같은 이름으로 부르는 열이다. 이름만 다를 뿐
기본 공격력 표의 (성급, 티어)와 같은 축이며, 한 성급 안에서 부옵션 기초값이 정확히
4:3:2:1 비율을 이룬다. 그 가정은 _SECONDARY_COLUMNS 아래에서 매번 검사한다.
"""
from __future__ import annotations

import csv
import pathlib
import sys

import openpyxl

ROOT   = pathlib.Path(__file__).resolve().parent.parent
XLSX   = ROOT / "Weapon level scaling.xlsx"
OUTDIR = ROOT / "gidc" / "core" / "data" / "weapon_level_scaling"

MAX_LEVEL = 90

# 기본 공격력 레벨 배율 시트의 블록 → 그 곡선을 쓰는 성급들.
# 엑셀은 1~3성을 한 블록으로 묶어 두었다(곡선이 같고 기초값만 다르다).
_MAIN_BLOCKS: dict[str, tuple[int, ...]] = {
    "1-3star": (1, 2, 3),
    "4star":   (4,),
    "5star":   (5,),
}

# 부옵션 시트의 열 이름 → (성급, 티어). 열 11개가 3성 3티어 + 4성 4티어 + 5성 4티어로
# 정확히 나뉜다. 1·2성 무기는 부옵션이 없어 열이 없다.
_SECONDARY_COLUMNS: dict[str, tuple[int, int]] = {
    "t-38": (3, 1), "t-39(b)": (3, 2), "t-40": (3, 3),
    "t-41": (4, 1), "t-42": (4, 2), "t-44": (4, 3), "t-45": (4, 4),
    "t-44b": (5, 1), "t-46": (5, 2), "t-48": (5, 3), "t-49": (5, 4),
}

# 부옵션 시트 → 그 표를 쓰는 스탯들. 시트가 둘씩 묶어 둔 것은 값이 같기 때문이다.
# CSV에는 스탯별로 펴서 적는다 — 엔진이 (스탯, 성급, 티어)로 바로 찾게 하려는 것이고,
# 「HP%와 공격력%가 같은 표를 쓴다」는 규칙을 코드가 다시 들고 있지 않게 하려는 것이다.
_SECONDARY_SHEETS: dict[str, tuple[str, ...]] = {
    "HP%, ATK%":                ("HP_PCT", "ATK_PCT"),
    "DEF%, Physical DMG Bonus": ("DEF_PCT", "PHYSICAL_DMG"),
    "Energy Recharge":          ("ENERGY_RECHARGE",),
    "CRIT Rate":                ("CRIT_RATE",),
    "CRIT DMG":                 ("CRIT_DMG",),
    "Elemental Mastery":        ("ELEMENTAL_MASTERY",),
}

# 엑셀은 %스탯을 비율(0.12)로 적어 두었지만, 엔진의 장비 옵션(core/stat.py)은 게임에
# 표시된 값(12.0)을 받는 것이 규칙이다. 여기서 한 번 맞춰 두면 무기 쪽에서 변환이 없다.
_FLAT_STATS = frozenset({"ELEMENTAL_MASTERY"})
_PERCENT_SCALE = 100


def _rows(ws) -> list[tuple]:
    """빈 줄을 걸러 낸 시트 전체. 엑셀 아래쪽의 빈 서식 행이 섞여 들어온다."""
    return [row for row in ws.iter_rows(values_only=True) if any(v is not None for v in row)]


def _number(value) -> float | None:
    """엑셀의 빈 칸. 1·2성 돌파 표의 5·6차처럼 문자열 'None'으로 들어오는 칸도 있다."""
    if value is None or value == "None":
        return None
    return float(value)


# ══════════════════════════════════════════════════════════════════════════
#  기본 공격력
# ══════════════════════════════════════════════════════════════════════════
def _main_base_value(ws) -> dict[tuple[int, int], float]:
    """(성급, 티어) → Lv.1 기본 공격력."""
    out: dict[tuple[int, int], float] = {}
    for rarity, value, tier in _rows(ws)[1:]:
        key = (int(str(rarity)[0]), int(str(tier).split()[1]))
        if key in out:
            raise ValueError(f"기본 공격력 기초값에 {key}가 두 번 나옵니다.")
        out[key] = float(value)
    return out


def _main_ascension(ws) -> dict[int, tuple[float, ...]]:
    """성급 → 돌파 단계별 추가 공격력. 0단계(0)를 앞에 붙여 단계와 인덱스를 맞춘다.

    돌파 보너스가 무기마다가 아니라 **성급 하나로** 정해진다. 1·2성만 4단계에서 끝난다."""
    out: dict[int, tuple[float, ...]] = {}
    for row in _rows(ws)[1:]:
        values = [v for v in (_number(c) for c in row[1:]) if v is not None]
        if any(a >= b for a, b in zip(values, values[1:])):
            raise ValueError(f"돌파 보너스는 단계마다 커져야 합니다. {row[0]}: {values}")
        out[int(str(row[0])[0])] = (0.0, *values)
    return out


def _main_level_multiplier(ws) -> tuple[dict[str, list[int]], dict[tuple[str, int], dict[int, float]]]:
    """블록(1-3star/4star/5star) × 티어 → 레벨별 배율.

    시트는 세 블록이 옆으로 나란히 붙어 있고 각 블록이 'Level' 머리글로 시작한다.
    열 번호를 손으로 세지 않고 그 머리글을 찾아 블록 경계를 잡는다."""
    rows   = _rows(ws)
    header = rows[1]
    starts = [i for i, cell in enumerate(header) if cell == "Level"]
    if len(starts) != len(_MAIN_BLOCKS):
        raise ValueError(f"레벨 배율 시트의 블록이 {len(_MAIN_BLOCKS)}개가 아닙니다. {starts}")

    tiers: dict[str, list[int]] = {}
    out:   dict[tuple[str, int], dict[int, float]] = {}
    for block, start in zip(_MAIN_BLOCKS, starts):
        end = next((s for s in starts if s > start), len(header))
        tiers[block] = [int(str(h).split()[1]) for h in header[start + 1:end] if h]
        for row in rows[2:]:
            level = row[start]
            if level is None:
                continue
            for offset, tier in enumerate(tiers[block], start=1):
                out.setdefault((block, tier), {})[int(level)] = float(row[start + offset])

    for key, by_level in out.items():
        if by_level.get(1) != 1.0:
            raise ValueError(f"{key}의 Lv.1 배율이 1.0이 아닙니다. ({by_level.get(1)})")
        missing = [lv for lv in range(1, MAX_LEVEL + 1) if lv not in by_level]
        if missing:
            raise ValueError(f"{key}의 레벨 배율에 빠진 레벨이 있습니다: {missing}")
        series = [by_level[lv] for lv in range(1, MAX_LEVEL + 1)]
        if any(a >= b for a, b in zip(series, series[1:])):
            raise ValueError(f"{key}의 레벨 배율이 단조 증가가 아닙니다.")
    return tiers, out


# ══════════════════════════════════════════════════════════════════════════
#  부옵션
# ══════════════════════════════════════════════════════════════════════════
def _secondary_level_multiplier(ws) -> dict[int, float]:
    """레벨 → 배율. 부옵션은 5레벨마다 오르므로 90행이 아니라 19행이다.

    표를 90행으로 펴서 적지 않는 것이 중요하다 — 펴 두면 「5레벨마다」라는 규칙이 자료
    속에 녹아 사라지고, 다음에 보는 사람이 매 레벨 갱신으로 읽는다. 규칙은
    core/weapon_scaling.py의 함수 하나에 둔다."""
    out = {int(level): float(mult) for level, mult, *_ in _rows(ws)[1:]}
    expected = [1, *range(5, MAX_LEVEL + 1, 5)]
    if sorted(out) != expected:
        raise ValueError(f"부옵션 배율은 {expected} 레벨이어야 합니다. (읽은 값: {sorted(out)})")
    if out[1] != 1.0:
        raise ValueError(f"Lv.1 배율이 1.0이 아닙니다. ({out[1]})")
    series = [out[lv] for lv in expected]
    if any(a >= b for a, b in zip(series, series[1:])):
        raise ValueError("부옵션 배율이 단조 증가가 아닙니다.")
    return out


def _secondary_base_value(wb) -> dict[tuple[str, int, int], float]:
    """(스탯, 성급, 티어) → Lv.1 부옵션 값 (게임 표기 단위)."""
    out: dict[tuple[str, int, int], float] = {}
    for sheet, stats in _SECONDARY_SHEETS.items():
        rows    = _rows(wb[sheet])
        columns = [c for c in rows[0][1:] if c]
        level_1 = next(row for row in rows[1:] if int(row[0]) == 1)

        unknown = set(columns) - set(_SECONDARY_COLUMNS)
        if unknown or len(columns) != len(_SECONDARY_COLUMNS):
            raise ValueError(f"'{sheet}'의 티어 열이 예상과 다릅니다: {columns}")

        for stat in stats:
            scale = 1 if stat in _FLAT_STATS else _PERCENT_SCALE
            for offset, column in enumerate(columns, start=1):
                rarity, tier = _SECONDARY_COLUMNS[column]
                # round는 자릿수를 줄이려는 것이 아니라 0.05107×100이 남기는
                # 5.106999999999999 같은 2진 부동소수 잔여를 털어 내려는 것이다.
                out[(stat, rarity, tier)] = round(float(level_1[offset]) * scale, 9)
        _check_tier_ratios(sheet, columns, level_1)
    return out


def _check_tier_ratios(sheet: str, columns: list[str], level_1: tuple) -> None:
    """한 성급 안에서 티어별 부옵션 기초값이 4:3:2:1인지 확인한다.

    _SECONDARY_COLUMNS의 열↔(성급,티어) 대응이 맞다는 근거가 이 비율이다. 엑셀의 열
    이름(t-44b 등)에는 성급도 티어도 적혀 있지 않아서, 이 검사가 없으면 대응이 조용히
    어긋나도 드러나지 않는다."""
    by_rarity: dict[int, list[tuple[int, float]]] = {}
    for offset, column in enumerate(columns, start=1):
        rarity, tier = _SECONDARY_COLUMNS[column]
        by_rarity.setdefault(rarity, []).append((tier, float(level_1[offset])))

    for rarity, entries in by_rarity.items():
        entries.sort()
        top = entries[0][1]
        for tier, value in entries:
            expected = top * (5 - tier) / 4
            if abs(value - expected) > max(expected * 5e-4, 1e-9):
                raise ValueError(
                    f"'{sheet}' {rarity}성 Tier {tier}의 기초값이 4:3:2:1 비율에서 벗어납니다. "
                    f"({value} vs 예상 {expected:.5f}) — _SECONDARY_COLUMNS 대응을 확인하세요."
                )


def _check_secondary_sheets(wb, base: dict, multiplier: dict[int, float]) -> tuple[float, str]:
    """부옵션 시트의 Lv.1 아닌 행들이 「Lv.1 × 배율」과 맞는지 대조한다.

    CSV에 Lv.1 행만 남기고 나머지를 버리기 전에, 버려도 되는지 확인하는 검사다.
    원소 마스터리 시트는 소수 1자리로 반올림돼 있어 0.2%까지 벌어진다."""
    worst, culprit = 0.0, ""
    for sheet, stats in _SECONDARY_SHEETS.items():
        rows    = _rows(wb[sheet])
        columns = [c for c in rows[0][1:] if c]
        stat    = stats[0]
        scale   = 1 if stat in _FLAT_STATS else _PERCENT_SCALE
        for row in rows[1:]:
            level = int(row[0])
            for offset, column in enumerate(columns, start=1):
                rarity, tier = _SECONDARY_COLUMNS[column]
                actual = float(row[offset]) * scale
                calc   = base[(stat, rarity, tier)] * multiplier[level]
                error  = abs(calc - actual) / actual
                if error > worst:
                    worst, culprit = error, f"{sheet} {column} Lv.{level}"
    if worst > 0.005:
        raise ValueError(f"부옵션 시트가 「Lv.1 × 배율」과 {worst:.2%} 어긋납니다 ({culprit}).")
    return worst, culprit


# ══════════════════════════════════════════════════════════════════════════
def main() -> None:
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else XLSX
    if not path.exists():
        raise SystemExit(f"엑셀을 찾을 수 없습니다: {path}")

    wb = openpyxl.load_workbook(path, data_only=True)
    main_base       = _main_base_value(wb["Base Value(Main)"])
    main_ascension  = _main_ascension(wb["Ascension Value(Main)"])
    block_tiers, main_mult = _main_level_multiplier(wb["Level Multiplier(Main)"])
    sub_mult        = _secondary_level_multiplier(wb["Level Multiplier(Secondary)"])
    sub_base        = _secondary_base_value(wb)
    worst, culprit  = _check_secondary_sheets(wb, sub_base, sub_mult)

    for (rarity, tier) in main_base:
        block = next(b for b, rarities in _MAIN_BLOCKS.items() if rarity in rarities)
        if tier not in block_tiers[block]:
            raise ValueError(f"{rarity}성 Tier {tier}의 레벨 배율 열이 없습니다.")
        if rarity not in main_ascension:
            raise ValueError(f"{rarity}성의 돌파 보너스가 없습니다.")

    columns = [f"{block}_tier{tier}" for block, tiers in block_tiers.items() for tier in tiers]

    OUTDIR.mkdir(parents=True, exist_ok=True)
    written = [
        _write("main_base_value.csv", ["rarity", "tier", "base_atk"],
               [[rarity, tier, value] for (rarity, tier), value in sorted(main_base.items())]),
        _write("main_ascension_value.csv", ["rarity", "phase", "base_atk"],
               [[rarity, phase, value]
                for rarity, values in sorted(main_ascension.items())
                for phase, value in enumerate(values)]),
        _write("main_level_multiplier.csv", ["level", *columns],
               [[level, *(main_mult[(block, tier)][level]
                          for block, tiers in block_tiers.items() for tier in tiers)]
                for level in range(1, MAX_LEVEL + 1)]),
        _write("secondary_base_value.csv", ["stat", "rarity", "tier", "value"],
               [[stat, rarity, tier, value]
                for (stat, rarity, tier), value in sorted(sub_base.items())]),
        _write("secondary_level_multiplier.csv", ["level", "multiplier"],
               [[level, sub_mult[level]] for level in sorted(sub_mult)]),
    ]

    print(f"{OUTDIR.relative_to(ROOT)}")
    for name, rows, size in written:
        print(f"  {name:32s} {rows:4d}행 · {size / 1024:5.1f} KB")
    print(f"  성급·티어 {len(main_base)}조합 · 레벨 1~{MAX_LEVEL} · "
          f"부옵션 {len(sub_base)}조합 (배율 {len(sub_mult)}행)")
    print(f"  부옵션 시트 대조: 최대 상대오차 {worst:.3%} ({culprit})")


def _write(name: str, header: list[str], rows: list[list]) -> tuple[str, int, int]:
    path = OUTDIR / name
    # newline="" 이 없으면 윈도우에서 줄바꿈이 \r\r\n 으로 겹친다(csv 모듈이 이미 \r\n 을 쓴다).
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    return name, len(rows), path.stat().st_size


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure") and not _stream.isatty():
            _stream.reconfigure(encoding="utf-8")
    main()
