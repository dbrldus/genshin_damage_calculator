from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from gidc.enums import ArtifactSet, ArtifactSlot, StatType
from gidc.core.profile import SkillHit, apply_stat
from gidc.core.stat import GearStat

if TYPE_CHECKING:
    from gidc.core.character import Character

# 부위별 허용 주옵션
_VALID_MAIN_STATS: dict[ArtifactSlot, set[StatType]] = {
    ArtifactSlot.FLOWER: {StatType.HP},
    ArtifactSlot.FEATHER: {StatType.ATK},
    ArtifactSlot.SANDS: {
        StatType.HP_PCT, StatType.ATK_PCT, StatType.DEF_PCT,
        StatType.ELEMENTAL_MASTERY, StatType.ENERGY_RECHARGE,
    },
    ArtifactSlot.GOBLET: {
        StatType.HP_PCT, StatType.ATK_PCT, StatType.DEF_PCT,
        StatType.ELEMENTAL_MASTERY,
        StatType.PYRO_DMG, StatType.HYDRO_DMG, StatType.CRYO_DMG,
        StatType.ELECTRO_DMG, StatType.ANEMO_DMG, StatType.GEO_DMG,
        StatType.DENDRO_DMG, StatType.PHYSICAL_DMG,
    },
    ArtifactSlot.CIRCLET: {
        StatType.HP_PCT, StatType.ATK_PCT, StatType.DEF_PCT,
        StatType.ELEMENTAL_MASTERY,
        StatType.CRIT_RATE, StatType.CRIT_DMG, StatType.HEALING_BONUS,
    },
}

# 부옵션으로 등장할 수 없는 스탯
_INVALID_SUB_STATS: set[StatType] = {
    StatType.PYRO_DMG, StatType.HYDRO_DMG, StatType.CRYO_DMG,
    StatType.ELECTRO_DMG, StatType.ANEMO_DMG, StatType.GEO_DMG,
    StatType.DENDRO_DMG, StatType.PHYSICAL_DMG, StatType.HEALING_BONUS,
}


# 성유물 옵션 — 값은 게임에 표시된 그대로 넣는다 (치명타 확률 12.4% → 12.4,
# HP 실수치 4780 → 4780). 변환 규칙은 Stat.GearStat 참고.
@dataclass(frozen=True)
class MainStat(GearStat):
    pass


@dataclass(frozen=True)
class SubStat(GearStat):
    pass


class Artifact(ABC):
    def __init__(
        self,
        artifact_set: ArtifactSet,
        slot: ArtifactSlot,
        main_stat: MainStat,
        sub_stats: list[SubStat],
    ) -> None:
        self._validate_main_stat(slot, main_stat.stat_type)
        self._validate_sub_stats(sub_stats)

        self.artifact_set = artifact_set
        self.slot = slot
        self.main_stat = main_stat
        self.sub_stats = sub_stats

    # ── 주옵션 + 부옵션을 SkillHit에 누산 (공통, 비추상) ─────────────────────
    def apply_raw_stats(self, hit: SkillHit) -> None:
        # %스탯은 scaled가 게임 표기값에 0.01을 곱해 내부 비율로 바꿔 준다.
        slot = self.slot.value
        apply_stat(hit, self.main_stat.stat_type, self.main_stat.scaled, f"성유물 메인({slot})")
        for sub in self.sub_stats:
            apply_stat(hit, sub.stat_type, sub.scaled, f"성유물 부옵션({slot})")

    # ── 세트 효과 (각 서브클래스에서 구현) ───────────────────────────────────
    @abstractmethod
    def apply_2set(self, all_hits: dict[Character, dict[str, SkillHit]], wearer: Character) -> None:
        """2세트 효과를 all_hits[wearer]의 각 히트에 누산한다."""
        ...

    @abstractmethod
    def apply_4set(self, all_hits: dict[Character, dict[str, SkillHit]], wearer: Character) -> None:
        """4세트 효과를 all_hits[wearer]의 각 히트에 누산한다. apply_raw_stats() 이후 호출 보장."""
        ...

    # ── 세트 효과 (의존/스케일) — 기본 no-op ──────────────────────────────────
    #    Phase 5(의존 단계)에서 호출된다 — 모든 코어 스탯 기여가 끝난 뒤.
    #    착용자의 최종 스탯에 스케일하는 방식 B 세트 효과(예: 제사의 여운 4세트의
    #    공격력 기반 피해)만 재정의한다. current_atk/def/hp()로 최신 스탯을 읽고,
    #    결과는 flat_dmg_bonus 등 피해 풀에만 출력한다(코어 스탯 되먹임 금지).
    def apply_2set_dependent(
        self, all_hits: dict[Character, dict[str, SkillHit]], wearer: Character
    ) -> None:
        pass

    def apply_4set_dependent(
        self, all_hits: dict[Character, dict[str, SkillHit]], wearer: Character
    ) -> None:
        pass

    # ── 검증 ─────────────────────────────────────────────────────────────
    @staticmethod
    def _validate_main_stat(slot: ArtifactSlot, stat_type: StatType) -> None:
        if stat_type not in _VALID_MAIN_STATS[slot]:
            raise ValueError(
                f"[{slot.value}] 부위에 '{stat_type.value}'는 주옵션으로 사용할 수 없습니다."
            )

    @staticmethod
    def _validate_sub_stats(sub_stats: list[SubStat]) -> None:
        if len(sub_stats) != 4:
            raise ValueError(f"부옵션은 정확히 4개여야 합니다. (현재 {len(sub_stats)}개)")

        stat_types = [s.stat_type for s in sub_stats]
        if len(stat_types) != len(set(stat_types)):
            raise ValueError("부옵션에 중복된 스탯이 있습니다.")

        for sub_stat in sub_stats:
            if sub_stat.stat_type in _INVALID_SUB_STATS:
                raise ValueError(
                    f"'{sub_stat.stat_type.value}'는 부옵션으로 등장할 수 없는 스탯입니다."
                )

    def __repr__(self) -> str:
        sub_lines = "\n    ".join(str(s) for s in self.sub_stats)
        return (
            f"세트  : {self.artifact_set.value}\n"
            f"부위  : {self.slot.value}\n"
            f"주옵션: {self.main_stat}\n"
            f"부옵션:\n    {sub_lines}"
        )
