"""
데미지 계산 벤치 — 아래 「설정」 섹션을 수정하고 실행하세요.

    python bench.py
"""

import sys
import unicodedata

from _presets.skirk_party import skirk, furina, escoffier, mona
from gidc.core.party import Party
from gidc.core.enemy import Enemy
from gidc.enums import DmgType, ReactionType
from gidc.core.profile import build_damage_context, set_recording
from gidc.core.damage import calculate
from gidc.core.explain import explain_hit


# ══════════════════════════════════════════════════════════════════════════
#  설정
# ══════════════════════════════════════════════════════════════════════════
# 프리셋은 build() 팩토리다 — 실행할 때마다 새 캐릭터 객체를 만든다.
# (캐릭터가 self._e_active 같은 per-run 상태를 들고 있어 재사용하면 계산이 오염된다)
PARTY = (skirk.build, furina.build, escoffier.build, mona.build)

# 상황적 반응 — 팀 구성/로테이션에 따라 붙는 반응(증발 평타 등)을 전역으로 켠다.
# 히트가 내재 반응을 선언한 경우(이네파의 달감전 피해 등)에는 적용되지 않는다.
# 비달반응은 DMG_TYPE을 None으로 두면 REACTION에서 자동 유도된다.
REACTION  = ReactionType.NONE
DMG_TYPE  = None
CHAR_LV   = 90
enemy     = Enemy(level=100)

DAMAGE_TARGETS = {"스커크"}   # 데미지 출력할 캐릭터 이름 — 비우면 전원 출력

# 버프 귀속 디버그 — 여기에 히트 이름을 넣으면 '어떤 버프로 이 숫자가 나왔는지' 상세 출력.
# (DAMAGE_TARGETS 안의 캐릭터 히트만 대상. 예: {"A1 오버클럭 추가 공격"})
EXPLAIN = {"원소 폭발 참격 피해 1타"}


# ══════════════════════════════════════════════════════════════════════════
#  출력 헬퍼
# ══════════════════════════════════════════════════════════════════════════
def _display_width(s: str) -> int:
    """한글 등 동아시아 전각 문자를 폭 2로 계산한 표시 폭(터미널 기준)."""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in s)


def _pad_display(s: str, width: int) -> str:
    return s + " " * max(0, width - _display_width(s))


def print_stat_sheets(all_hits) -> None:
    for char, hits in all_hits.items():
        if not hits:
            continue
        first = next(iter(hits.values()))
        print(f"\n[{char.name} 스탯 시트]")
        print(f"  최종 공격력      : {first.atk_final:>10,.1f}")
        print(f"  최종 HP          : {first.hp_final:>10,.1f}")
        print(f"  최종 방어력      : {first.def_final:>10,.1f}")
        print(f"  치명타 확률      : {first.crit_rate       * 100:>9.1f}%")
        print(f"  치명타 피해      : {first.crit_dmg        * 100:>9.1f}%")
        print(f"  원소 충전 효율   : {first.energy_recharge * 100:>9.1f}%")


def print_damage(all_hits) -> None:
    for char, hits in all_hits.items():
        if DAMAGE_TARGETS and char.name not in DAMAGE_TARGETS:
            continue
        print(f"\n[데미지 — {char.name}]")
        name_width = max((_display_width(hit.name) for hit in hits.values()), default=0)
        for hit in hits.values():
            ctx = build_damage_context(
                hit,
                enemy,
                reaction_type = REACTION,
                dmg_type      = DMG_TYPE,
                char_level    = CHAR_LV,
            )
            r = calculate(ctx)
            name = _pad_display(hit.name, name_width)
            print(f"  {name}  non_crit={r.non_crit:>12,.0f}  crit={r.crit:>12,.0f}  expected={r.expected:>12,.0f}")


def print_explain(all_hits) -> None:
    if not EXPLAIN:
        return
    for char, hits in all_hits.items():
        if DAMAGE_TARGETS and char.name not in DAMAGE_TARGETS:
            continue
        for name, hit in hits.items():
            if name in EXPLAIN:
                print()
                print(explain_hit(
                    hit, enemy=enemy, reaction_type=REACTION,
                    dmg_type=DMG_TYPE, char_level=CHAR_LV,
                ).to_text())


# ══════════════════════════════════════════════════════════════════════════
#  실행
# ══════════════════════════════════════════════════════════════════════════
def main() -> None:
    # 버프 기여 기록을 켠다(explain_hit용). 데미지 수치에는 전혀 영향이 없다.
    set_recording(True)
    all_hits = Party(*(build() for build in PARTY)).build_profiles()

    print_stat_sheets(all_hits)
    print_damage(all_hits)
    print_explain(all_hits)


if __name__ == "__main__":
    # 출력을 파일·파이프로 넘기면 Python이 로케일 인코딩(Windows는 cp949)을 쓰는데,
    # cp949는 —(U+2014) 같은 문자를 인코딩하지 못해 UnicodeEncodeError로 죽는다.
    # 콘솔에 그대로 찍을 때는 기존 인코딩을 건드리지 않고, 리다이렉트된 경우에만 UTF-8로 고정한다.
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure") and not _stream.isatty():
            _stream.reconfigure(encoding="utf-8")
    main()
