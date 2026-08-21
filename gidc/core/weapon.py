from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from gidc.enums import StatType, WeaponType
from gidc.core import weapon_scaling
from gidc.core.profile import SkillHit, apply_stat
from gidc.core.stat import GearStat

if TYPE_CHECKING:
    from gidc.core.character import Character


# 무기 부옵션 — 성유물과 같은 규칙으로, 값은 게임에 표시된 그대로 넣는다
# (치명타 피해 66.2% → 66.2). 변환 규칙은 Stat.GearStat 참고.
@dataclass(frozen=True)
class WeaponSubStat(GearStat):
    """성유물 부옵션과 달리 값이 레벨 표에서 나오므로 소수가 딸려 온다(원소 마스터리
    220.512). 계산에는 그 소수를 그대로 쓰고, 보여줄 때 게임처럼 반올림하는 규칙은
    GearStat.__str__에 있다."""


class Weapon(ABC):
    """기본 공격력과 부옵션은 **성급·티어·레벨·돌파 단계**로 정해진다(core/weapon_scaling.py).

    그래서 무기가 선언하는 것은 성급·티어·부옵션 종류 셋뿐이고, 542나 66.2 같은 최종
    숫자를 손에 들고 있지 않다 — 들고 있으면 레벨을 바꿀 수 없고 틀려도 드러나지 않는다.

    「티어」는 한 성급 안의 등급(1이 가장 낮은 기본 공격력)이며 부옵션 등급도 겸한다.
    게임 화면에 적혀 있지 않으므로, 새 무기를 쓸 때는 화면에서 읽히는 값으로 되찾는다.

        weapon_scaling.tier_from_substat(5, StatType.ELEMENTAL_MASTERY, 58)   # Lv.1 부옵션
        weapon_scaling.tier_from_base_atk(5, 542)                             # Lv.90 공격력

    표에 없는 커스텀 무기(DefaultWeapon)만 base_atk/sub_stat 프로퍼티를 재정의한다 —
    캐릭터 쪽 DefaultCharacter가 base_hp/atk/def를 재정의하는 것과 같다."""

    def __init__(
        self,
        weapon_type:   WeaponType,
        rarity:        int,
        tier:          int,
        refinement:    int,
        sub_stat_type: StatType | None = None,
    ) -> None:
        if not (1 <= refinement <= 5):
            raise ValueError(f"재련 단계는 1~5여야 합니다. (입력: {refinement})")
        self.weapon_type   = weapon_type
        self.rarity        = rarity
        self.tier          = tier
        self.refinement    = refinement
        self.sub_stat_type = sub_stat_type

        # 레벨과 돌파 단계 — 기본값은 만렙(3~5성이면 Lv.90 6돌파). 캐릭터와 같은 이유로
        # 둘을 따로 둔다: 상한 레벨(20/40/…/80)에서는 돌파 전/후 두 상태가 모두 유효하고
        # 기본 공격력이 다르다. 바꿀 때 짝을 맞추려면 weapon_scaling.resolve_phase를 쓴다.
        self.level:     int = weapon_scaling.max_level(rarity)
        self.ascension: int = weapon_scaling.max_phase(rarity)

        # 성급·티어·부옵션 조합이 표에 있는지 지금 확인한다 — 피해 계산 도중이 아니라
        # 무기를 만드는 순간 실패해야 어디를 잘못 적었는지 드러난다.
        _ = self.base_atk, self.sub_stat

    # ── 레벨로 정해지는 스탯 ──────────────────────────────────────────────
    @property
    def base_atk(self) -> float:
        return weapon_scaling.base_atk(self.rarity, self.tier, self.level, self.ascension)

    @property
    def sub_stat(self) -> WeaponSubStat | None:
        """부옵션. 돌파 단계를 넘기지 않는 것은 부옵션에 돌파 항이 없기 때문이다 —
        같은 레벨이면 돌파 전/후가 같은 값이고, 5레벨마다 한 칸씩 오른다."""
        if self.sub_stat_type is None:
            return None
        return WeaponSubStat(
            self.sub_stat_type,
            weapon_scaling.substat_value(self.sub_stat_type, self.rarity, self.tier, self.level),
        )

    # ── 부옵션을 SkillHit에 누산 (기본 공격력은 build_damage_profile이 atk_base에 합산)
    def apply_raw_stats(self, hit: SkillHit) -> None:
        # %스탯은 scaled가 게임 표기값에 0.01을 곱해 내부 비율로 바꿔 준다.
        if self.sub_stat:
            apply_stat(hit, self.sub_stat.stat_type, self.sub_stat.scaled, "무기 부옵션")

    # ── 무기가 만드는 추가 타격 히트 — 기본 no-op ────────────────────────────
    #    Phase 1(히트 생성)에서 build_hits() 직후에 호출된다. 무기 패시브가 **새 히트**를
    #    만드는 경우(천공 시리즈의 진공의 칼날)만 재정의한다.
    #
    #    왜 Phase 3(apply_passive)이 아니라 여기인가 — Phase 3은 기초 스탯·무기 부옵션·
    #    성유물 옵션·세트 효과가 이미 실린 뒤다(Character.apply_primary_buffs 참고).
    #    그때 히트를 끼워 넣으면 atk_base가 0인 채로 남아 아무것도 곱하지 못한다.
    #    Phase 1에 넣어야 이후 모든 단계가 이 히트를 캐릭터 히트와 똑같이 훑는다.
    #
    #    유저 입력은 여기서 묻지 않는다 — 질문은 종전대로 apply_passive(Phase 3)에 모으고,
    #    조건이 꺼져 있으면 그쪽에서 이 히트를 도로 뺀다.
    def add_hits(self, hits: dict[str, SkillHit], wearer: Character) -> None:
        pass

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
            f"레벨: Lv.{self.level} ({self.ascension}돌파)\n"
            f"기본 공격력: {self.base_atk:.1f}\n"
            f"재련 단계: {self.refinement}{sub}"
        )
