from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from gidc.enums import ArtifactSet, ArtifactSlot, StatType
from gidc.core import artifact_scaling
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


# 성유물 부옵션 — 값은 게임에 표시된 그대로 넣는다 (치명타 확률 12.4% → 12.4,
# HP 실수치 4780 → 4780). 변환 규칙은 Stat.GearStat 참고.
# 주옵션(MainStat)은 값을 받지 않는다 — 성급·강화 레벨로 정해지므로 Artifact가 표에서
# 꺼내 만든다(core/artifact_scaling.py).
@dataclass(frozen=True)
class MainStat(GearStat):
    pass


@dataclass(frozen=True)
class SubStat(GearStat):
    pass


class Artifact(ABC):
    """성유물 하나. **세트 · 부위 · 성급 · 강화 레벨 · 주옵션 종류 · 부옵션**을 받는다.

    주옵션 값은 받지 않는다 — 성급과 강화 레벨로 정해지므로(core/artifact_scaling.py)
    손에 들고 있으면 레벨을 바꿀 수 없고 틀려도 드러나지 않는다. 무기가 기본 공격력·
    부옵션을 성급·티어·레벨에서 꺼내 쓰는 것과 같다.

    부옵션은 반대다. 강화할 때마다 무작위로 붙는 값이라 레벨로 정해지지 않으므로
    지금도 화면에서 읽어 적는다."""

    # 부옵션은 4줄이 상한일 뿐 하한이 아니다 — 4성 이하나 강화 전 성유물은 3줄 이하다.
    MAX_SUB_STATS = 4

    # 이 세트가 존재하는 성급. 게임의 성유물 세트는 저마다 성급 범위가 정해져 있어
    # 「검투사의 피날레 3성」이나 「모험가 5성」 같은 것은 없다. 세트마다 다르므로
    # **세트 파일이 직접 선언한다** — 무기 파일이 성급·티어를 직접 적는 것과 같다.
    # 여기 기본값은 표 밖의 커스텀 세트(DefaultArtifact)를 위한 것으로, 가장 흔한
    # 4~5성이다. 세트 파일에서 빠뜨리면 이 값이 조용히 쓰이므로 새 세트를 쓸 때 꼭 적는다.
    RARITIES: tuple[int, ...] = (4, 5)

    # 이 세트에 있는 부위. 거의 모든 세트가 다섯 부위를 다 갖지만 그렇지 않은 세트가 있다
    # (기도 4종은 관 하나뿐이다). 성급과 같이 세트마다 다르므로 세트 파일이 선언하고,
    # 기본값은 **모든 부위 허용**이다 — 예외인 세트만 적으면 된다.
    SLOTS: tuple[ArtifactSlot, ...] = tuple(ArtifactSlot)

    def __init__(
        self,
        artifact_set: ArtifactSet,
        slot: ArtifactSlot,
        main_stat_type: StatType,
        sub_stats: list[SubStat],
        rarity: int | None = None,     # None이면 그 세트의 최고 성급
        level: int | None = None,      # None이면 그 성급의 만강화(5성 +20)
    ) -> None:
        rarity = max(self.RARITIES) if rarity is None else rarity
        self._validate_rarity(artifact_set, rarity)
        self._validate_slot(artifact_set, slot)
        self._validate_main_stat(slot, main_stat_type)
        self._validate_sub_stats(sub_stats)

        self.artifact_set = artifact_set
        self.slot = slot
        self.rarity = rarity
        self.main_stat_type = main_stat_type
        self.sub_stats = sub_stats
        self.level = artifact_scaling.max_level(rarity) if level is None else level

        # 성급·주옵션·레벨 조합이 표에 있는지 지금 확인한다 — 피해 계산 도중이 아니라
        # 성유물을 만드는 순간 실패해야 어디를 잘못 적었는지 드러난다.
        _ = self.main_stat

    # ── 성급·레벨로 정해지는 주옵션 ───────────────────────────────────────
    @property
    def main_stat(self) -> MainStat:
        return MainStat(
            self.main_stat_type,
            artifact_scaling.main_stat_value(self.main_stat_type, self.rarity, self.level),
        )

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
    @classmethod
    def _validate_rarity(cls, artifact_set: ArtifactSet, rarity: int) -> None:
        if rarity not in cls.RARITIES:
            raise ValueError(
                f"'{artifact_set.value}' 세트는 {list(cls.RARITIES)}성만 있습니다. "
                f"(입력: {rarity}성)"
            )

    @classmethod
    def _validate_slot(cls, artifact_set: ArtifactSet, slot: ArtifactSlot) -> None:
        if slot not in cls.SLOTS:
            raise ValueError(
                f"'{artifact_set.value}' 세트에는 {[s.value for s in cls.SLOTS]} 부위만 "
                f"있습니다. (입력: {slot.value})"
            )

    @staticmethod
    def _validate_main_stat(slot: ArtifactSlot, stat_type: StatType) -> None:
        if stat_type not in _VALID_MAIN_STATS[slot]:
            raise ValueError(
                f"[{slot.value}] 부위에 '{stat_type.value}'는 주옵션으로 사용할 수 없습니다."
            )

    @staticmethod
    def _validate_sub_stats(sub_stats: list[SubStat]) -> None:
        if len(sub_stats) > Artifact.MAX_SUB_STATS:
            raise ValueError(
                f"부옵션은 최대 {Artifact.MAX_SUB_STATS}개입니다. (현재 {len(sub_stats)}개)"
            )

        stat_types = [s.stat_type for s in sub_stats]
        if len(stat_types) != len(set(stat_types)):
            raise ValueError("부옵션에 중복된 스탯이 있습니다.")

        for sub_stat in sub_stats:
            if sub_stat.stat_type in _INVALID_SUB_STATS:
                raise ValueError(
                    f"'{sub_stat.stat_type.value}'는 부옵션으로 등장할 수 없는 스탯입니다."
                )

    def __repr__(self) -> str:
        sub_lines = "\n    ".join(str(s) for s in self.sub_stats) or "(없음)"
        return (
            f"세트  : {self.artifact_set.value} ({self.rarity}성 +{self.level})\n"
            f"부위  : {self.slot.value}\n"
            f"주옵션: {self.main_stat}\n"
            f"부옵션:\n    {sub_lines}"
        )
