"""반응 피해의 레벨 배율 — 격변·촉진 계열이 캐릭터 레벨로 곱하는 상수.

캐릭터 기초 스탯의 성장 곡선(data/character_level_scaling/level_multiplier.csv)과는
이름만 같고 다른 표다. 그쪽은 core/base_stats.py 가 읽는다.
"""
import json
from pathlib import Path

_path = Path(__file__).parent / "data" / "level_multiplier.json"
with _path.open(encoding="utf-8") as _f:
    LEVEL_MULTIPLIER: dict[int, float] = {int(k): v for k, v in json.load(_f).items()}
