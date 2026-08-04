from collections import Counter
import math

from gidc.core.character import Character
from gidc.core.profile import SkillHit
from gidc.enums import CharacterTrait, Element, MoonsignLevel
from gidc.core.party_state import moonsign_level, skill_level_bonus
from gidc.prompt import ask_bool, ask_choice, ask_multi_choice


class Party:
    def __init__(self, *characters: Character) -> None:
        if len(characters) > 4:
            raise ValueError(f"파티 인원은 최대 4명입니다. (입력: {len(characters)}명)")
        self.members:  list[Character]                       = list(characters)
        self.all_hits: dict[Character, dict[str, SkillHit]] = {}

    def build_profiles(self) -> dict[Character, dict[str, SkillHit]]:
        # ── Phase 0 : 파티 구성만으로 정해지는 특성 레벨 보정 ────────────────────
        # 계수 자체가 바뀌므로 히트를 만들기 전에 확정해야 한다. 유저 입력도 스탯도
        # 읽지 않아(원소 구성만 봄) 멤버 순서와 무관하다.
        # 현재 출처는 원소전투 스킬(무예 전수)뿐이다 — 평타/폭발 상승 효과가 생기면
        # PartyState에 판정을 추가하고 여기서 같은 방식으로 대입한다.
        skill_bonus = skill_level_bonus(self.members)
        for char in self.members:
            char.na_level_bonus    = 0
            char.skill_level_bonus = skill_bonus
            char.burst_level_bonus = 0

        # Phase 1 : 히트 서술자 생성 (스탯은 기본값)
        self.all_hits = {char: char.build_hits() for char in self.members}

        # Phase 2 : 원소 공명 (원소 종류만 참조 — 스탯 읽기 없음, 선행 적용)
        _apply_elemental_resonance(self.all_hits, self.members)

        # ── Phase 2.5 (개인 버프) : 환상 축복 등 파티 편성만으로 결정되는 캐릭터 개인 버프 ──
        # 원소 공명과 마찬가지로 스탯을 읽지 않고 코어 풀에 가산만 하므로 Phase 3 이전에 둔다.
        _apply_fantastical_blessing(self.all_hits, self.members)

        # Phase 3 : 전체 캐릭터 주 버프 (base + raw + 세트/무기 패시브 + 자신 버프)
        for char in self.members:
            char.apply_primary_buffs(self.all_hits)

        # ── Phase 4 (스탯 기여) : 크로스 캐릭터 코어 스탯 버프 + 유저 입력 수집 ──
        # 가산 연산뿐이라 멤버 순서 무관. 스케일 읽기(다음 단계)가 볼 스탯을 먼저 완성한다.
        # 스탯 확정(finalize)은 스케일 읽기가 current_*()로 라이브 조회하므로 여기서 불필요.
        # 무한 루프 방지 규칙상 스케일러는 스탯을 되먹이지 않으니(방식 A/B), 단일 패스로 충분하다.
        for char in self.members:
            char.contribute_dependent_stats(self.all_hits)

        # ── Phase 4.5 (파티 버프) : 코어 풀도, 최종 스탯 스케일도 아닌 크로스 버프 ──
        # res_reduction, 고정값 all_dmg_bonus, crit 계열 등. 스탯을 읽지 않으므로
        # 순서 무관하며, Phase 5(스케일 읽기)보다 먼저 끝내 두 단계를 명확히 분리한다.
        for char in self.members:
            char.apply_party_buffs(self.all_hits)

        # ── Phase 5 (스탯 스케일 공유) : 버퍼의 current_* 스탯을 읽어 피해 풀에 적용 ──
        #    Phase 4가 모두 끝난 뒤라 멤버 순서와 무관하게 결정적 결과를 낸다.
        core_snapshot = _snapshot_core_pools(self.all_hits)
        for char in self.members:
            char.apply_dependent_buffs(self.all_hits)      # 캐릭터 스케일 버프
            char.apply_dependent_equipment(self.all_hits)  # 무기/성유물 스케일 패시브
        # 파티 공통 스케일 버프 — 특정 캐릭터 킷이 아니라 파티 구성으로 정해지는 방식 B 버프.
        # 캐릭터 스케일 버프가 모두 끝난 뒤라 버퍼의 최신 스탯(current_*)을 읽는다.
        _apply_full_moon_lunar_bonus(self.all_hits, self.members)
        # 정확성 가드: 스케일러는 ATK/DEF/HP 코어 풀을 출력하지 않는다(방식 A는 base, 방식 B는
        # Flat DMG로 차원 변환). 건드렸다면 무한 루프를 유발하는 잘못된 모델이므로, 코어 스탯
        # 기여라면 contribute_dependent_stats로, 스탯을 읽지 않는 고정 버프라면
        # apply_party_buffs로 옮기거나 방식 B(flat_dmg_bonus)로 바꿔야 한다.
        _assert_core_pools_unchanged(self.all_hits, core_snapshot)

        # ── Phase 6 (최종 확정) : 누적된 base/pct/flat을 *_final에 한 번 반영 ──
        #    게임과 동일하게 확정은 마지막에 단 한 번 (다회차 재확정 없음).
        for char_hits in self.all_hits.values():
            for hit in char_hits.values():
                hit.finalize_damage_multipliers()

        return self.all_hits

    def get_hits(self, char: Character) -> dict[str, SkillHit]:
        return self.all_hits[char]


# ── 정확성 가드: 스케일 단계(Phase 5)가 출력하면 안 되는 코어 스탯 풀 ──────────
# 무한 루프 방지 규칙상 스케일러는 ATK/DEF/HP를 절대 출력하지 않는다(방식 A=base 읽기,
# 방식 B=Flat DMG 변환). 반면 EM은 꼬리표(em_from_pct_share) 달린 Flat으로 출력될 수 있으므로
# (설탕·나히다) 감시 대상에서 제외한다.
_CORE_POOL_FIELDS = (
    "hp_flat", "hp_pct", "atk_flat", "atk_pct", "def_flat", "def_pct",
)


def _snapshot_core_pools(all_hits: dict[Character, dict[str, SkillHit]]) -> dict[int, tuple]:
    snap: dict[int, tuple] = {}
    for char_hits in all_hits.values():
        for hit in char_hits.values():
            snap[id(hit)] = tuple(getattr(hit, f) for f in _CORE_POOL_FIELDS)
    return snap


def _assert_core_pools_unchanged(
    all_hits: dict[Character, dict[str, SkillHit]],
    snapshot: dict[int, tuple],
) -> None:
    for char, char_hits in all_hits.items():
        for hit in char_hits.values():
            before = snapshot.get(id(hit))
            if before is None:
                continue
            after = tuple(getattr(hit, f) for f in _CORE_POOL_FIELDS)
            if before != after:
                changed = [f for f, b, a in zip(_CORE_POOL_FIELDS, before, after) if b != a]
                raise AssertionError(
                    f"[정확성 가드] apply_dependent_buffs(스케일 단계)가 ATK/DEF/HP 코어 풀을 "
                    f"변경했습니다: {char.__class__.__name__} / '{hit.name}' → {changed}. "
                    f"무한 루프 방지 규칙상 스케일러는 코어 스탯을 출력하지 않는다. 코어 스탯 "
                    f"기여라면 contribute_dependent_stats로, 스탯을 읽지 않는 고정 버프라면 "
                    f"apply_party_buffs로 옮기고, 최종 스탯 기반이라면 방식 B"
                    f"(flat_dmg_bonus로 차원 변환)를 사용하세요."
                )


def _apply_elemental_resonance(
    all_hits: dict[Character, dict[str, SkillHit]],
    members:  list[Character],
) -> None:
    elem_counts = Counter(char.element for char in members)

    def _all(fn):
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                fn(hit)

    # ── 열정의 불 (불 2명) ─────────────────────────────────────────────────
    # 공격력 +25%
    if elem_counts[Element.PYRO] >= 2:
        _all(lambda h: h.add("atk_pct", 0.25, "원소 공명: 열정의 불"))

    # ── 치유의 물 (물 2명) ─────────────────────────────────────────────────
    # HP 최대치 +25%
    if elem_counts[Element.HYDRO] >= 2:
        _all(lambda h: h.add("hp_pct", 0.25, "원소 공명: 치유의 물"))

    # ── 분쇄의 얼음 (얼음 2명) ────────────────────────────────────────────
    # 빙결 또는 얼음 부착 적 공격 시 치명타 확률 +15%
    if elem_counts[Element.CRYO] >= 2:
        if ask_bool("[원소 공명: 분쇄의 얼음] 적이 빙결 상태 또는 얼음 원소 부착 여부"):
            _all(lambda h: h.add("crit_rate", 0.15, "원소 공명: 분쇄의 얼음"))

    # ── 만생의 풀 (풀 2명) ─────────────────────────────────────────────────
    # 원소 마스터리 +50 (고정)
    # 연소·활성·개화 반응 후 전원 EM +30 (6s), 촉진·발산·만개·발화 반응 후 전원 EM +20 (6s)
    if elem_counts[Element.DENDRO] >= 2:
        _all(lambda h: h.add("elemental_mastery", 50, "원소 공명: 만생의 풀"))
        if ask_bool("[원소 공명: 만생의 풀] 연소·활성·개화 반응 후 EM +30 활성 여부"):
            _all(lambda h: h.add("elemental_mastery", 30, "원소 공명: 만생의 풀", note="연소/활성/개화"))
        if ask_bool("[원소 공명: 만생의 풀] 촉진·발산·만개·발화 반응 후 EM +20 활성 여부"):
            _all(lambda h: h.add("elemental_mastery", 20, "원소 공명: 만생의 풀", note="촉진/발산/만개/발화"))

    # ── 부동의 바위 (바위 2명) ────────────────────────────────────────────
    # 보호막 강화 +15% (피해 스탯 없음), 보호막 보유 시: 피해 +15% + 적 바위 내성 -20%
    if elem_counts[Element.GEO] >= 2:
        if ask_bool("[원소 공명: 부동의 바위] 보호막 보유 여부"):
            _all(lambda h: (
                h.add("all_dmg_bonus", 0.15, "원소 공명: 부동의 바위"),
                h.add("geo_res_reduction", -0.20, "원소 공명: 부동의 바위"),
            ))


# ── 환상 축복 (기간 한정 이벤트) : 지정 캐릭터를 파티에 편성하면 HP/공격력/방어력 +20% ───
# 대상 명단이 이벤트마다 바뀌므로(현재는 야란·아이노·플린스·올로룬·스커크·레일라) 하드코딩
# 하지 않고, 파티원 중 현재 활성 명단에 해당하는 인원을 유저가 다중 선택으로 고른다.
# 캐릭터 개인 버프(그 캐릭터 자신의 스탯만 증가)이며 스탯을 읽지 않고 코어 풀에 가산만
# 하므로 원소 공명과 동급으로 Phase 2.5에서 처리한다.
_ILLUSORY_BLESSING_PCT = 0.20


def _apply_fantastical_blessing(
    all_hits: dict[Character, dict[str, SkillHit]],
    members:  list[Character],
) -> None:
    if not members:
        return
    options = [char.name for char in members]
    selected = ask_multi_choice(
        "[현실 속 환상극 버프] 현재 활성 명단에 해당하는 파티원 선택 (해당 없으면 Enter)", options
    )
    for idx in selected:
        char = members[idx]
        for hit in all_hits[char].values():
            hit.add("hp_pct", _ILLUSORY_BLESSING_PCT, "환상 축복")
            hit.add("atk_pct", _ILLUSORY_BLESSING_PCT, "환상 축복")
            hit.add("def_pct", _ILLUSORY_BLESSING_PCT, "환상 축복")


# ── 달빛 징조·보름 (2명 편성) : 비-달빛징조 버퍼의 스탯 스케일 달빛 반응 피해 증가 ──────
# 달빛 징조가 아닌 캐릭터가 원소전투 스킬/폭발 발동 후 20초 동안, 자신의 원소 타입 기반으로
# 주변 파티 전원의 달빛 반응 피해를 최대 36%까지 증가시킨다(중첩 불가). 우가/폭발 가동은
# 상시 유지되는 것으로 보고(다른 Moonsign 상시 효과와 동일하게) 파티 구성에서 유도한다.
#
# 「중첩 불가」 → 동시에 활성인 버퍼가 여러 명이면 값이 가장 큰 한 명만 남는다(활성 버퍼 중
# max). 다만 각 버퍼가 실제로 활성인지(원소 스킬/폭발 발동 여부)는 로테이션마다 다르므로
# (예: 실로닌 E 생략 시 실로닌은 비활성), 각 버퍼의 실효 %를 라벨에 보여주고 현재 활성인
# 버퍼를 유저가 고른다 — 활성 버퍼 중 가장 높은 것을 고르면 max가 된다. 활성 버퍼가 없으면
# 「없음」을 고른다. 반응별로 세 필드(달감전/달개화/달결정)에 동일하게 들어간다.
_FULL_MOON_LUNAR_CAP    = 0.36
_FULL_MOON_LUNAR_FIELDS = ("lunar_charged_bonus", "lunar_bloom_bonus", "lunar_crystallize_bonus")


def _full_moon_buffer_bonus(hit: SkillHit, element: Element) -> float:
    """비-달빛징조 버퍼 한 명이 자신의 원소별 스탯으로 만드는 달빛 반응 피해 증가(캡 전)."""
    if element in (Element.PYRO, Element.ELECTRO, Element.CRYO):
        return (hit.current_atk() / 100.0) * 0.009    # 공격력 100pt당 0.9%
    if element == Element.HYDRO:
        return (hit.current_hp() / 1000.0) * 0.006     # HP 최대치 1000pt당 0.6%
    if element == Element.GEO:
        return (hit.current_def() / 100.0) * 0.01      # 방어력 100pt당 1%
    if element in (Element.ANEMO, Element.DENDRO):
        # EM→피해 변환이므로 꼬리표 달린 지분(설탕 등)은 재료에서 제외한다.
        return (hit.convertible_em() / 100.0) * 0.0225  # 원소 마스터리 100pt당 2.25%
    return 0.0


def _apply_full_moon_lunar_bonus(
    all_hits: dict[Character, dict[str, SkillHit]],
    members:  list[Character],
) -> None:
    if moonsign_level(all_hits) is not MoonsignLevel.FULL:
        return

    buffers = [
        m for m in members
        if CharacterTrait.MOONSIGN not in m.traits and all_hits.get(m)
    ]
    if not buffers:
        return  # 전원 달빛 징조면 이 효과의 버퍼가 없다

    def _raw_bonus(b: Character) -> float:
        return _full_moon_buffer_bonus(next(iter(all_hits[b].values())), b.element)

    def _option_label(b: Character) -> str:
        raw = _raw_bonus(b)
        eff = min(raw, _FULL_MOON_LUNAR_CAP)
        cap_note = " (상한 36%)" if raw > _FULL_MOON_LUNAR_CAP else ""
        return f"{b.name} ({b.element.value}) — 달빛 반응 피해 +{eff * 100:.1f}%{cap_note}"

    # 각 버퍼의 실효 %를 라벨에 노출한다. 활성 버퍼가 여럿이면 가장 높은 것을 고르면 max가 되고,
    # 아무도 활성이 아니면(스킬 생략 등) 「없음」을 고른다. 1명이어도 활성 여부를 물어야 한다.
    options = [_option_label(b) for b in buffers] + ["없음 (활성 버퍼 없음)"]
    idx = ask_choice("[달빛 징조·보름] 현재 활성인 달빛 반응 버퍼", options)
    if idx >= len(buffers):
        return  # 없음 — 활성 버퍼 없음

    bonus = min(_raw_bonus(buffers[idx]), _FULL_MOON_LUNAR_CAP)
    if bonus <= 0.0:
        return

    label = f"달빛 징조·보름({buffers[idx].name})"
    for char_hits in all_hits.values():
        for hit in char_hits.values():
            for field in _FULL_MOON_LUNAR_FIELDS:
                hit.add(field, bonus, label)
