import warnings
from abc import ABC, abstractmethod
from collections import Counter
from typing import Optional

from gidc.core import ascension
from gidc.core import base_stats as stat_table
from gidc.core.artifact import Artifact
from gidc.core.weapon import Weapon
from gidc.core.profile import SkillHit, apply_stat
from gidc.enums import ArtifactSet
from gidc.enums import CharacterTrait, Element
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import asking_for


def clamp_talent_index(index: int, *tables: list) -> int:
    """레벨 인덱스가 계수 표를 넘지 않도록 자른다.

    파티발 레벨 상승 버프(무예 전수 등)를 받았는데 해당 레벨의 계수가 아직 표에 없으면
    IndexError로 죽거나 조용히 틀린 값을 쓰는 대신, 표의 마지막 레벨에서 멈추고 경고를
    남긴다 — 계수 표에 그 레벨 행을 채우면 경고가 사라진다."""
    limit = min(len(t) for t in tables) - 1
    if index <= limit:
        return index
    warnings.warn(
        f"레벨 인덱스 {index}에 해당하는 계수가 표에 없어 L{limit + 1}로 제한합니다. "
        f"해당 레벨 행을 계수 표에 추가하세요.",
        stacklevel=2,
    )
    return limit


class Character(ABC):
    # 표시용 이름 — 서브클래스에서 한글 이름으로 재정의한다.
    # 비워두면 클래스명으로 대체된다.
    name: str = ""

    # 장착 가능한 무기 종류 — 서브클래스에서 지정한다.
    # None이면 종류 제한 없음(미등록 캐릭터용).
    weapon_type: WeaponType | None = None

    # 항상 보유하는 특성 — 서브클래스에서 선언한다.
    innate_traits: frozenset[CharacterTrait] = frozenset()

    # 빌드 설정으로 획득할 수 있는 특성 — 서브클래스에서 선언한다.
    # 예) 니콜은 「마녀의 과제」를 완료하면 마도 캐릭터가 된다.
    #     선언하지 않은 캐릭터는 해당 특성을 획득할 수 없다.
    unlockable_traits: frozenset[CharacterTrait] = frozenset()

    # 레벨 스케일링 표(core/base_stats.py)의 열쇠. 비워 두면 클래스명을 쓴다 —
    # 등록된 캐릭터의 클래스명은 그 표의 영문 이름과 같다(Skirk, Xilonen, …).
    stat_key: str = ""

    # ── 어센션 보너스 스탯 (서브클래스에서 선언) ──────────────────────────
    # 돌파할 때마다 오르는 고유 스탯. 무엇이 붙는지와 성급만 선언하면 값은
    # core/ascension.py가 계산한다 — 0.384 같은 최종 숫자를 캐릭터가 들고 있으면
    # 돌파 단계를 바꿀 수 없고 틀려도 드러나지 않는다.
    # None이면 아직 그 캐릭터의 어센션 스탯 자료가 없다는 뜻이다(보너스 없음).
    #
    # rarity는 기초 스탯의 성장 곡선도 고른다. 4성 캐릭터가 선언을 빠뜨리면 5성 곡선으로
    # 조용히 부풀려지므로 등록된 캐릭터는 전부 명시한다.
    rarity:         int = 5
    ascension_stat: StatType | None = None

    # ── 특성 레벨 (서브클래스에서 선언) ────────────────────────────────────
    # 손으로 올릴 수 있는 특성 레벨의 상한. 명함·고유 특성·파티발 상승은 이 위에
    # 얹히므로 실효 레벨은 이보다 높을 수 있다(예: Lv.10 + 명함 +3 = 13).
    MAX_TALENT_LEVEL: int = 10
    # 해당 특성의 레벨을 올리는 명함 번호. 0이면 명함으로 오르지 않는다.
    # 예) 모나는 C5가 원소전투 스킬을, C3가 원소폭발을 올린다.
    NA_LEVEL_UP_CONSTELLATION:    int = 0
    SKILL_LEVEL_UP_CONSTELLATION: int = 0
    BURST_LEVEL_UP_CONSTELLATION: int = 0
    # 명함 1개가 올리는 폭 — 게임 전체 공통으로 +3이다.
    CONSTELLATION_LEVEL_UP: int = 3

    # 고유 특성으로 **상시** 오르는 레벨.
    # 예) 타르탈리아 「끝없는 흐름」: 일반 공격 레벨 +1 → NA_PASSIVE_LEVEL_UP = 1
    NA_PASSIVE_LEVEL_UP:    int = 0
    SKILL_PASSIVE_LEVEL_UP: int = 0
    BURST_PASSIVE_LEVEL_UP: int = 0

    # 각 특성 레벨로 스케일하는 계수 표 — 레벨 인덱스가 표를 넘지 않게 자르는 데 쓴다.
    # 계수 표를 모두 정의한 뒤 클래스 본문에서 튜플로 선언한다. 표가 2차원(단수별 행
    # 묶음)이면 `(*_NA, ...)`처럼 행을 펼쳐 넣는다 — 바깥 길이가 아니라 행 길이가 레벨 수다.
    NA_TABLES:    tuple = ()
    SKILL_TABLES: tuple = ()
    BURST_TABLES: tuple = ()

    def __init__(self) -> None:
        self.name:          str = self.name or self.__class__.__name__
        self.stat_key:      str = self.stat_key or self.__class__.__name__
        self.level:         int = 90
        # 돌파 단계 0~6. level과 따로 두는 이유는 상한 레벨(20/40/…/80)에서 두 상태가
        # 모두 유효하기 때문이다 — Lv.20/20 과 Lv.20/40 은 다른 캐릭터다.
        # level을 바꿀 때 짝을 맞추려면 ascension.resolve_phase(level, phase)를 쓴다.
        # 기본값은 Lv.90의 6돌파.
        self.ascension:     int = ascension.MAX_PHASE
        self.constellation: int = 0
        self.na_level:      int = 1
        self.skill_level:   int = 1
        self.burst_level:   int = 1

        # 파티 구성으로 정해지는 특성 레벨 상승분(스커크 「무예 전수」 등).
        # Party.build_profiles가 히트 생성 **전에** 채워 넣는다. 파티 없이 쓰면 0이다.
        # 캐릭터 자신의 고유 특성 상승분은 NA/SKILL/BURST_PASSIVE_LEVEL_UP으로 선언한다.
        self.na_level_bonus:    int = 0
        self.skill_level_bonus: int = 0
        self.burst_level_bonus: int = 0

        # 획득한 특성 — 전투 중 토글되지 않는 빌드 설정이라
        # constellation처럼 템플릿에서 unlock_trait()으로 지정한다.
        self._unlocked_traits: set[CharacterTrait] = set()

        self._weapon: Weapon | None = None

        self.flower:  Optional[Artifact] = None
        self.feather: Optional[Artifact] = None
        self.sands:   Optional[Artifact] = None
        self.goblet:  Optional[Artifact] = None
        self.circlet: Optional[Artifact] = None

    # ── 특성 계수 표의 레벨 인덱스 (0-based) ──────────────────────────────
    # 기본 레벨(최대 10) + 명함 상승 + 고유 특성 상승 + 파티발 상승을 더하고,
    # 그 레벨의 계수가 표에 없으면 마지막 레벨로 자른다.
    # 서브클래스는 계산식을 다시 쓰지 말고 이 세 메서드를 쓴다.
    def _talent_index(
        self,
        level:            int,
        party_bonus:      int,
        passive_bonus:    int,
        up_constellation: int,
        tables:           tuple,
    ) -> int:
        index = min(level, self.MAX_TALENT_LEVEL) - 1 + party_bonus + passive_bonus
        if up_constellation and self.constellation >= up_constellation:
            index += self.CONSTELLATION_LEVEL_UP
        return clamp_talent_index(index, *tables) if tables else index

    def _na_index(self) -> int:
        return self._talent_index(self.na_level, self.na_level_bonus,
                                  self.NA_PASSIVE_LEVEL_UP,
                                  self.NA_LEVEL_UP_CONSTELLATION, self.NA_TABLES)

    def _skill_index(self) -> int:
        return self._talent_index(self.skill_level, self.skill_level_bonus,
                                  self.SKILL_PASSIVE_LEVEL_UP,
                                  self.SKILL_LEVEL_UP_CONSTELLATION, self.SKILL_TABLES)

    def _burst_index(self) -> int:
        return self._talent_index(self.burst_level, self.burst_level_bonus,
                                  self.BURST_PASSIVE_LEVEL_UP,
                                  self.BURST_LEVEL_UP_CONSTELLATION, self.BURST_TABLES)

    # ── 특성 ──────────────────────────────────────────────────────────────
    @property
    def traits(self) -> frozenset[CharacterTrait]:
        """빌드 설정을 반영한 최종 특성.
        파티 파생 상태(gidc.core.party_state)가 이 값을 세어 판정한다."""
        return self.innate_traits | frozenset(self._unlocked_traits)

    def has_trait(self, trait: CharacterTrait) -> bool:
        return trait in self.traits

    def unlock_trait(self, trait: CharacterTrait) -> None:
        """빌드 설정으로 특성을 획득시킨다. unlockable_traits에 없으면 거부한다."""
        if trait not in self.unlockable_traits:
            raise ValueError(
                f"[{self.name}]은(는) '{trait.value}' 특성을 획득할 수 없습니다. "
                f"(획득 가능: {[t.value for t in self.unlockable_traits] or '없음'})"
            )
        self._unlocked_traits.add(trait)

    # ── 무기 장착 (종류 검증) ──────────────────────────────────────────────
    @property
    def weapon(self) -> Weapon | None:
        return self._weapon

    @weapon.setter
    def weapon(self, weapon: Weapon | None) -> None:
        self._validate_weapon_type(weapon)
        self._weapon = weapon

    def _validate_weapon_type(self, weapon: Weapon | None) -> None:
        # weapon_type이 None인 캐릭터(미등록/커스텀)는 종류를 제한하지 않는다.
        if weapon is None or self.weapon_type is None:
            return
        if weapon.weapon_type is not self.weapon_type:
            raise ValueError(
                f"[{self.name}]은(는) '{self.weapon_type.value}'만 장착할 수 있습니다. "
                f"(입력한 무기 종류: '{weapon.weapon_type.value}')"
            )

    # ── 기초 스탯 ──────────────────────────────────────────────────────────
    # 전 캐릭터가 같은 공식을 따른다.
    #
    #     스탯 = 기초값 × 레벨 배율 + 최대 어센션 값 × 어센션 배율
    #
    # 그래서 캐릭터는 이름(stat_key)과 성급만 알려주면 되고 Lv.90 숫자를 손에 들고 있을
    # 필요가 없다. 표에 없는 캐릭터(DefaultCharacter 같은 커스텀)만 이 셋을 재정의한다.
    @property
    def base_stats(self) -> stat_table.BaseStats:
        return stat_table.base_stats(self.stat_key, self.rarity, self.level, self.ascension)

    @property
    def base_hp(self) -> float:
        return self.base_stats.hp

    @property
    def base_atk(self) -> float:
        return self.base_stats.atk

    @property
    def base_def(self) -> float:
        return self.base_stats.defense

    # ── 추상 프로퍼티 ──────────────────────────────────────────────────────
    @property
    @abstractmethod
    def element(self) -> Element: ...

    # ── 추상 메서드 ────────────────────────────────────────────────────────
    @abstractmethod
    def build_hits(self) -> dict[str, SkillHit]:
        """히트 서술자만 설정하고 스탯은 기본값으로 반환한다."""
        ...

    @abstractmethod
    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        """자신의 모든 히트에 global + hit-specific 버프를 적용한다.
        유저 입력(ask_int/ask_bool)은 여기서 1번만 수집한다."""
        ...

    def contribute_dependent_stats(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        """Phase 4 — 코어 스탯 풀(atk/def/hp/em)에**만** 기여하는 크로스 버프 + 유저 입력 수집.

        여기 넣는 값은 **고정값이어야 한다.** 남의 최종 스탯을 읽어 만드는 값이라면
        지연 기여로(`add`에 함수 전달) 넘겨야 같은 단계의 다른 기여를 놓치지 않는다
        — 콜롬비나 C2가 자기 HP를 읽는데 실로닌 C2가 같은 단계에서 그 HP를 올리는 식의
        얽힘이 실제로 있다.

        유저 입력(ask_*)은 이 단계에 모은다 — 질문 ID가 (호출 지점, 반복 횟수)라 실행
        시점이 밀리면 질문 집합이 흔들린다. 재사용할 상태는 self에 저장. 기본값: no-op.

        EM %-공유(설탕/나히다)는 elemental_mastery와 em_from_pct_share에 동시에 태그해
        「EM을 다시 %로 변환하는」 버프가 그 지분을 재료로 쓰지 못하게 막는다."""
        pass

    def apply_party_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        """Phase 4.5 — 코어 풀도 최종 스탯 스케일도 아닌 크로스 버프(res_reduction,
        고정 all_dmg_bonus, crit_rate/crit_dmg, def_ignore 등).

        스탯을 읽지 않으므로 순서 무관이다. contribute_dependent_stats(Phase 4)에서
        저장해둔 상태를 재사용해 같은 입력을 두 번 묻지 않는다. 기본값: no-op."""
        pass

    @abstractmethod
    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        """버퍼의 **최종 스탯을 읽어서** 스케일하는 크로스 버프만 넣는다 — 읽지 않는 버프는
        apply_party_buffs로. 방식 A(atk_base 등 기초 스탯)는 그대로 읽고, 방식 B(최종 스탯,
        신학/한운/실로닌)는 current_atk/def/hp()를 flat_dmg_bonus로 차원 변환해 적용한다.

        **값이 아니라 함수를 넘긴다.** 이 단계에서 읽는 스탯은 다른 캐릭터가 같은 단계에서
        더하는 중일 수 있으므로, 지금 계산해 버리면 파티 멤버 순서가 결과를 바꾼다.
        `hit.add(field, lambda: 버퍼히트.current_atk() * 2.4, self)`처럼 넘기면 그 필드를
        읽는 순간(늦어도 Phase 5.5 정산에서) 계산되어 순서와 무관해진다. 사슬이 몇 단이든
        필요한 만큼 재귀로 풀리고, 순환이면 CyclicBuffError로 즉시 실패한다.
        (람다가 루프 변수를 잡으면 `lambda h=hit: ...`로 묶을 것 — 늦은 바인딩 주의.)

        ATK/DEF/HP 코어 풀에 **즉시 값으로** 되먹이면 무한 루프이며 정확성 가드가 실패시킨다.
        EM을 **다시 %로 변환**하는 버프(EM→EM, EM→피해 보너스 %; 카즈하)는 elemental_mastery
        대신 convertible_em()을 읽어 꼬리표 달린 지분을 재료에서 뺀다. 반대로 EM에 비례한
        몫을 피해에 직접 더하는 버프(시틀라리 A4/C1)는 재변환이 아니므로 elemental_mastery를
        그대로 읽는다 — 실제로 들고 있는 EM은 출처와 무관하게 전부 재료가 된다."""
        ...

    # ── 스탯 빌드 ─────────────────────────────────────────────────────────
    def apply_ascension_bonus(self, hits: dict[str, SkillHit]) -> None:
        """돌파로 늘어난 고유 스탯을 모든 히트에 더한다.

        값은 스탯·성급·돌파 단계로만 정해지므로 히트마다 다시 구할 것이 없다.
        캐릭터 고유 치명타 확률 5%처럼 SkillHit이 이미 기본값으로 들고 있는 몫은
        포함되지 않는다 — 여기서 더하는 것은 증가분뿐이다."""
        if self.ascension_stat is None:
            return
        bonus = ascension.bonus_value(self.rarity, self.ascension_stat, self.ascension)
        if not bonus:
            return
        for hit in hits.values():
            apply_stat(hit, self.ascension_stat, bonus, self, note="어센션")

    def apply_primary_buffs(
        self,
        all_hits: dict["Character", dict[str, SkillHit]],
    ) -> None:
        """Phase 3: base + raw 스탯 → 세트/무기 패시브(기여) → 자신 버프.
        여기서는 무기/성유물의 **기여** 패시브(apply_passive/apply_2set/apply_4set)만
        호출한다. 스탯 스케일(의존) 패시브는 apply_dependent_equipment(Phase 5)로 분리."""
        weapon = self.weapon
        hits   = all_hits[self]

        # 히트마다 표를 다시 읽을 이유가 없다. 프로퍼티로 받는 것은 커스텀 캐릭터가
        # 셋을 각자 재정의하기 때문이다(base_stats를 바로 부르면 그 재정의를 지나친다).
        base_hp, base_atk, base_def = float(self.base_hp), float(self.base_atk), float(self.base_def)

        for hit in hits.values():
            # 기록을 위해 0에서 add()로 쌓는다 — 순수 대입과 최종값은 동일하다.
            hit.hp_base = hit.atk_base = hit.def_base = 0.0
            hit.add("hp_base",  base_hp,  "기초 스탯", note="캐릭터 기본")
            hit.add("atk_base", base_atk, "기초 스탯", note="캐릭터 기본")
            hit.add("def_base", base_def, "기초 스탯", note="캐릭터 기본")
            if weapon:
                hit.add("atk_base", float(weapon.base_atk), "무기 기본 공격력")

        for hit in hits.values():
            if weapon:
                weapon.apply_raw_stats(hit)
            for art in self._iter_artifacts():
                art.apply_raw_stats(hit)

        # 세트 효과가 묻는 질문에 착용자를 달아 둔다 — 같은 세트를 두 명이 끼면
        # 문구가 똑같아 화면에서 구분되지 않는다 (prompt.asking_for 참고).
        active_sets = self._get_active_sets()
        reps = self._get_set_representatives()
        with asking_for(self.name):
            for artifact_set, tier in active_sets.items():
                rep = reps[artifact_set]
                rep.apply_2set(all_hits, self)
                if tier == 4:
                    rep.apply_4set(all_hits, self)
        if weapon:
            weapon.apply_passive(all_hits, self)

        self.apply_ascension_bonus(hits)
        self.apply_self_buffs(hits)

    def apply_dependent_equipment(
        self,
        all_hits: dict["Character", dict[str, SkillHit]],
    ) -> None:
        """Phase 5(의존): 무기/성유물 세트의 스탯 스케일(방식 B) 패시브를 적용한다.
        모든 코어 스탯 기여가 끝난 뒤에 호출되어 current_*()로 최신 스탯을 읽는다.
        기본 훅은 no-op이라 대부분 장비는 아무것도 하지 않는다."""
        weapon = self.weapon
        if weapon:
            weapon.apply_passive_dependent(all_hits, self)

        active_sets = self._get_active_sets()
        reps = self._get_set_representatives()
        with asking_for(self.name):
            for artifact_set, tier in active_sets.items():
                rep = reps[artifact_set]
                rep.apply_2set_dependent(all_hits, self)
                if tier == 4:
                    rep.apply_4set_dependent(all_hits, self)

    def build_damage_profile(
        self,
        all_hits: dict["Character", dict[str, SkillHit]],
    ) -> None:
        """하위 호환 래퍼 — Party 없이 단일 캐릭터 테스트 시 사용."""
        self.apply_primary_buffs(all_hits)
        self.contribute_dependent_stats(all_hits)
        self.apply_party_buffs(all_hits)
        self.apply_dependent_buffs(all_hits)
        self.apply_dependent_equipment(all_hits)

    def build_stat_sheet(self) -> dict[str, SkillHit]:
        """솔로 경로 편의 메서드 — Party 없이 단일 캐릭터 계산 시 사용."""
        all_hits = {self: self.build_hits()}
        self.apply_primary_buffs(all_hits)
        self.contribute_dependent_stats(all_hits)   # 코어 스탯(atk/def/hp/em) 기여
        self.apply_party_buffs(all_hits)             # 코어/스케일 아닌 크로스 버프
        self.apply_dependent_buffs(all_hits)         # 스탯 스케일 읽기 (current_* 라이브 조회)
        self.apply_dependent_equipment(all_hits)     # 무기/세트 스케일 패시브
        for hit in all_hits[self].values():          # 남은 지연 기여 정산 → 확정
            hit.settle()
            hit.finalize_damage_multipliers()
        return all_hits[self]

    # ── 내부 유틸 ──────────────────────────────────────────────────────────
    def _get_active_sets(self) -> dict[ArtifactSet, int]:
        counts = Counter(art.artifact_set for art in self._iter_artifacts())
        return {s: (4 if c >= 4 else 2) for s, c in counts.items() if c >= 2}

    def _iter_artifacts(self):
        for art in (self.flower, self.feather, self.sands, self.goblet, self.circlet):
            if art is not None:
                yield art

    def _get_set_representatives(self) -> dict[ArtifactSet, Artifact]:
        seen: dict[ArtifactSet, Artifact] = {}
        for art in self._iter_artifacts():
            seen.setdefault(art.artifact_set, art)
        return seen
