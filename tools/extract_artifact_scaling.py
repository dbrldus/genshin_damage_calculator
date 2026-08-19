"""성유물 주옵션 레벨 스케일링 자료를 엑셀에서 뽑아 CSV로 굽는다.

    python tools/extract_artifact_scaling.py [엑셀경로]

무기 쪽(tools/extract_weapon_scaling.py)과 같은 역할이지만 하는 일이 훨씬 적다.
무기는 「기초값 × 레벨 배율 + 돌파 보너스」라는 곱셈 규칙이 있어 표를 셋으로 쪼개
두었지만, **성유물 주옵션에는 그런 규칙이 없다** — 엑셀에 (성급, 스탯, 강화 레벨)마다
게임 화면의 값이 그대로 적혀 있고, 그 값들은 이미 반올림된 표시값이다. 곡선을 되찾아
곱셈으로 복원하면 화면과 어긋나므로, 표를 **있는 그대로** 한 장으로 옮긴다.

    main_stat_value.csv    (스탯, 성급, 강화 레벨) → 주옵션 값 (게임 표기 단위)

엑셀 시트는 성급마다 한 장이고(1 star ~ 5 stars), 행이 스탯·열이 강화 레벨이다.
강화 레벨은 게임의 +N 그대로 0부터 시작하며 상한이 성급마다 다르다(5성 +20, 4성 +16,
3성 +12, 1·2성 +4).

「Elemental DMG%」 행 하나는 일곱 원소가 나눠 쓴다. CSV에는 원소별로 펴서 적는다 —
엔진이 (스탯, 성급, 레벨)로 바로 찾게 하려는 것이고, 「원소 피해 보너스는 원소가 달라도
값이 같다」는 규칙을 코드가 다시 들고 있지 않게 하려는 것이다(무기 쪽 부옵션 시트를
스탯별로 펴서 적는 것과 같은 이유다).
"""
from __future__ import annotations

import csv
import pathlib
import sys

import openpyxl

ROOT   = pathlib.Path(__file__).resolve().parent.parent
XLSX   = ROOT / "Artifact Level Scaling.xlsx"
OUTDIR = ROOT / "gidc" / "core" / "data" / "artifact_level_scaling"

# 시트의 행 머리글 → 그 행을 쓰는 StatType 이름들. 머리글은 시트마다 대소문자가
# 흔들리므로(5성은 "Crit Rate%", 1·2성은 "CRIT Rate%") 소문자로 맞춰 찾는다.
_STAT_ROWS: dict[str, tuple[str, ...]] = {
    "hp":                ("HP",),
    "atk":               ("ATK",),
    "hp%":               ("HP_PCT",),
    "atk%":              ("ATK_PCT",),
    "def%":              ("DEF_PCT",),
    "physical dmg%":     ("PHYSICAL_DMG",),
    "elemental dmg%":    ("PYRO_DMG", "HYDRO_DMG", "CRYO_DMG", "ELECTRO_DMG",
                          "ANEMO_DMG", "GEO_DMG", "DENDRO_DMG"),
    "elemental mastery": ("ELEMENTAL_MASTERY",),
    "energy recharge%":  ("ENERGY_RECHARGE",),
    "crit rate%":        ("CRIT_RATE",),
    "crit dmg%":         ("CRIT_DMG",),
    "healing bonus%":    ("HEALING_BONUS",),
}


def _rows(ws) -> list[tuple]:
    """빈 줄을 걸러 낸 시트 전체. 엑셀 아래쪽의 빈 서식 행이 섞여 들어온다."""
    return [row for row in ws.iter_rows(values_only=True) if any(v is not None for v in row)]


def _rarity(title: str) -> int:
    """시트 이름 → 성급. '5 stars' / '1 star' 처럼 숫자가 앞에 있다."""
    head = title.split()[0]
    if not head.isdigit():
        raise ValueError(f"시트 이름에서 성급을 읽지 못했습니다: {title!r}")
    return int(head)


def _sheet(ws) -> dict[str, list[float]]:
    """시트 한 장 → {StatType 이름: 레벨 0..N의 값}.

    검사가 여기 몰려 있다. 표를 그대로 옮기는 자료라 나중에 값을 되짚어 볼 곱셈 규칙이
    없다 — 옮겨 적는 순간 어긋난 것을 잡지 못하면 영영 드러나지 않는다."""
    rows   = _rows(ws)
    header = rows[0]
    if str(header[0]).strip().lower() != "level":
        raise ValueError(f"[{ws.title}] 첫 칸이 'Level'이 아닙니다: {header[0]!r}")

    levels = [int(v) for v in header[1:]]
    if levels != list(range(len(levels))):
        raise ValueError(f"[{ws.title}] 강화 레벨이 0부터 1씩 늘지 않습니다: {levels}")

    out: dict[str, list[float]] = {}
    seen: set[str] = set()
    for row in rows[1:]:
        label = str(row[0]).strip().lower()
        if label not in _STAT_ROWS:
            raise ValueError(f"[{ws.title}] 모르는 스탯 행입니다: {row[0]!r}")
        if label in seen:
            raise ValueError(f"[{ws.title}] '{row[0]}' 행이 두 번 나옵니다.")
        seen.add(label)

        values = [float(v) for v in row[1:len(levels) + 1]]
        if len(values) != len(levels):
            raise ValueError(f"[{ws.title}] '{row[0]}' 행의 칸 수가 머리글과 다릅니다.")
        if any(a >= b for a, b in zip(values, values[1:])):
            raise ValueError(f"[{ws.title}] '{row[0]}' 값이 레벨마다 커지지 않습니다: {values}")

        for stat in _STAT_ROWS[label]:
            out[stat] = values

    missing = set(_STAT_ROWS) - seen
    if missing:
        raise ValueError(f"[{ws.title}] 빠진 스탯 행: {sorted(missing)}")
    return out


def main() -> None:
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else XLSX
    if not path.exists():
        raise SystemExit(f"엑셀을 찾을 수 없습니다: {path}")

    wb = openpyxl.load_workbook(path, data_only=True)
    table: dict[int, dict[str, list[float]]] = {}
    for ws in wb.worksheets:
        rarity = _rarity(ws.title)
        if rarity in table:
            raise ValueError(f"성급 {rarity}의 시트가 둘입니다: {ws.title}")
        table[rarity] = _sheet(ws)

    # 성급이 높을수록 같은 강화 레벨에서 값이 커야 한다. 시트를 통째로 잘못 붙여 넣는
    # 사고(4성 자리에 3성 시트)를 이 한 줄이 잡는다.
    for lower, upper in zip(sorted(table), sorted(table)[1:]):
        for stat, values in table[lower].items():
            if values[0] >= table[upper][stat][0]:
                raise ValueError(
                    f"{upper}성 +0 '{stat}'이 {lower}성보다 크지 않습니다: "
                    f"{table[upper][stat][0]} ≤ {values[0]}"
                )

    rows = [
        [stat, rarity, level, value]
        for rarity, stats in sorted(table.items())
        for stat, values in sorted(stats.items())
        for level, value in enumerate(values)
    ]
    rows.sort(key=lambda r: (r[0], r[1], r[2]))

    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / "main_stat_value.csv"
    # newline="" 이 없으면 윈도우에서 줄바꿈이 \r\r\n 으로 겹친다(csv 모듈이 이미 \r\n 을 쓴다).
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["stat", "rarity", "level", "value"])
        writer.writerows(rows)

    print(f"{OUTDIR.relative_to(ROOT)}")
    print(f"  {out.name:24s} {len(rows):4d}행 · {out.stat().st_size / 1024:5.1f} KB")
    for rarity, stats in sorted(table.items()):
        top = len(next(iter(stats.values()))) - 1
        print(f"  {rarity}성 · 강화 +0~+{top} · 스탯 {len(stats)}종")


if __name__ == "__main__":
    main()
