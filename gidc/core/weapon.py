from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from gidc.enums import WeaponType
from gidc.core.profile import SkillHit, apply_stat
from gidc.core.stat import GearStat

if TYPE_CHECKING:
    from gidc.core.character import Character


# 무기 부옵션 — 성유물과 같은 규칙으로, 값은 게임에 표시된 그대로 넣는다
# (치명타 피해 66.2% → 66.2). 변환 규칙은 Stat.GearStat 참고.
@dataclass(frozen=True)
class WeaponSubStat(GearStat):
    pass


class Weapon(ABC):
    def __init__(
        self,
        weapon_type: WeaponType,
        base_atk:   int,
        refinement: int,
        sub_stat:   WeaponSubStat | None = None,
    ) -> None:
        if not (1 <= refinement <= 5):
            raise ValueError(f"재련 단계는 1~5여야 합니다. (입력: {refinement})")
        self.weapon_type = weapon_type
        self.base_atk    = base_atk
        self.refinement  = refinement
        self.sub_stat    = sub_stat

    # ── 부옵션을 SkillHit에 누산 (기본 공격력은 build_damage_profile이 atk_base에 합산)
    def apply_raw_stats(self, hit: SkillHit) -> None:
        # %스탯은 scaled가 게임 표기값에 0.01을 곱해 내부 비율로 바꿔 준다.
        if self.sub_stat:
            apply_stat(hit, self.sub_stat.stat_type, self.sub_stat.scaled, "무기 부옵션")

    # ── 무기 패시브 (기여) — 각 무기 서브클래스에서 고유 효과 구현.
    #    self.refinement(1~5)를 읽어 재련 단계별 배율을 적용한다.
    #    apply_primary_buffs(Phase 3)에서 호출된다 — 스탯 확정 전. 고정/flat·% 기여만.
    @abstractmethod
    def apply_passive(self, all_hits: dict[Character, dict[str, SkillHit]], wearer: Character) -> None: ...

    # ── 무기 패시브 (의존/스케일) — 기본 no-op ────────────────────────────────
    #    Phase 5(의존 단계)에서 호출된다 — 모든 코어 스탯 기여가 끝난 뒤.
    #    착용자의 최종 스탯에 스케일하는 방식 B 패시브(예: 바위산을 맴도는 노래의
    #    파티 방어력 기반 효과)만 재정의한다. current_atk/def/hp()로 최신 스탯을 읽고,
    #    결과는 flat_dmg_bonus 등 피해 풀에만 출력한다(코어 스탯 되먹임 금지).
    #    파티 전체에 뿌리는 효과는 동명의 무기끼리 중첩되지 않으므로
    #    SkillHit.apply_unique_buff에 무기 클래스를 소스 키로 넘겨 제출한다.
    def apply_passive_dependent(
        self, all_hits: dict[Character, dict[str, SkillHit]], wearer: Character
    ) -> None:
        pass

    def __repr__(self) -> str:
        sub = f"\n부옵션: {self.sub_stat}" if self.sub_stat else ""
        return (
            f"무기 종류: {self.weapon_type.value}\n"
            f"기본 공격력: {self.base_atk}\n"
            f"재련 단계: {self.refinement}{sub}"
        )
