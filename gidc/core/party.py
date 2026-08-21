"""파티 단위 계산 파이프라인.

계산 순서의 **단일 출처**다. 캐릭터·무기·성유물 주석이 「Phase 4」처럼 부르는 이름이
여기서 정의된다.

    Phase 0   특성 레벨 보정      파티 구성만 보고 결정 (스커크 「무예 전수」).
                                  계수 표를 고르는 값이라 히트 생성보다 먼저 확정한다.
    Phase 1   히트 생성           build_hits() + 무기 추가 타격. 스탯은 기본값.
    Phase 2   파티 편성 버프      원소 공명, 환상극 버프. 스탯을 읽지 않는 가산뿐.
    Phase 3   개인 버프           기초/장비 스탯 → 세트·무기 기여 패시브 → apply_self_buffs.
    Phase 4   코어 스탯 기여      contribute_dependent_stats — 크로스 캐릭터 ATK/DEF/HP/EM.
                                  유저 입력(ask_*)도 여기서 한 번에 모은다.
    Phase 4.5 그 밖의 크로스 버프  apply_party_buffs — 내성 감소, 고정 피해 보너스, 치명타 등.
    Phase 5   스탯 스케일 버프     apply_dependent_buffs + 장비의 *_dependent 패시브.
                                  「버퍼의 최종 스탯을 읽어」 만드는 버프(방식 B).
    Phase 5.5 정산               남은 지연 기여를 전부 값으로 확정한다.
    Phase 6   최종 확정           base/pct/flat → *_final. 게임과 동일하게 단 한 번.

**단계는 「누가 먼저 실행되는가」가 아니라 「무엇을 출력하는가」로 나뉜다.**
Phase 2~4.5의 기여는 전부 가산(혹은 최댓값)이라 실행 순서와 무관하고, 순서에 좌우될
수밖에 없는 것 — 남의 최종 스탯을 읽어 만드는 값 — 은 Phase 5에서 **함수로 등록**되어
읽는 순간(늦어도 Phase 5.5)에 계산된다. 그래서 파티 멤버 순서가 결과를 바꾸지 않는다.
자세한 규약은 SkillHit.add(gidc/core/profile.py)와 Character의 각 훅 docstring 참고.
"""
from collections import Counter
import math

from gidc.core.character import Character
from gidc.core.profile import SkillHit
from gidc.enums import CharacterTrait, Element, MoonsignLevel, ReactionType
from gidc.core.party_state import moonsign_level, skill_level_bonus
from gidc.core.reaction import lunar_candidates, stellar_candidates, stellar_conditions
from gidc.prompt import ask_bool, ask_choice, ask_int, ask_multi_choice


class Party:
    def __init__(self, *characters: Character) -> None:
        if len(characters) > 4:
            raise ValueError(f"파티 인원은 최대 4명입니다. (입력: {len(characters)}명)")
        self.members:  list[Character]                       = list(characters)
        self.all_hits: dict[Character, dict[str, SkillHit]] = {}
        # 달·별 반응 피해를 트리거하는 파티원 (반응별). build_profiles의 Phase 4에서 채운다 —
        # 피해 계산은 최종 스탯이 확정된 뒤라야 하므로 core.party_reaction이 나중에 읽는다.
        self.lunar_participants: dict[ReactionType, list[Character]] = {}

    def build_profiles(self) -> dict[Character, dict[str, SkillHit]]:
        # ── Phase 0 : 파티 구성만으로 정해지는 특성 레벨 보정 ────────────────────
        skill_bonus = skill_level_bonus(self.members)
        for char in self.members:
            char.na_level_bonus    = 0
            char.skill_level_bonus = skill_bonus
            char.burst_level_bonus = 0

        # Phase 1 : 히트 서술자 생성 (스탯은 기본값)
        self.all_hits = {char: char.build_hits_with_weapon() for char in self.members}

        # Phase 2 : 원소 공명 & 환상극 버프
        _apply_elemental_resonance(self.all_hits, self.members)
        _apply_fantastical_blessing(self.all_hits, self.members)

        # Phase 3 : 전체 캐릭터 주 버프 (base + raw + 세트/무기 패시브 + 자신 버프)
        for char in self.members:
            char.apply_primary_buffs(self.all_hits)

        # ── Phase 4 : 크로스 캐릭터 코어 스탯(ATK/DEF/HP/EM) 기여 + 유저 입력 수집 ──
        # 가산뿐이라 멤버 순서 무관. 뒤 단계가 읽을 스탯을 여기서 완성한다.
        # ask_*는 반드시 이 단계에 모은다 — 질문 ID가 (호출 지점, 반복 횟수)라
        # 실행 시점이 밀리면 질문 집합이 흔들린다(지연 기여 함수 안에서 묻지 말 것).
        for char in self.members:
            char.contribute_dependent_stats(self.all_hits)
        # 달·별 반응의 트리거 참여자와 별 반응 계수 재료도 유저 입력이라 이 단계에서 묻는다.
        # 피해 자체는 가중치가 순위로 정해져 Phase 6 뒤에야 계산한다(core.party_reaction).
        self.lunar_participants, self.stellar_participants = _ask_celestial_inputs(self.all_hits, self.members)

        # ── Phase 4.5 : 코어 풀도 스탯 스케일도 아닌 크로스 버프 ──────────────────
        # 내성 감소, 고정값 all_dmg_bonus, 치명타 계열 등. 스탯을 읽지 않아 순서 무관.
        for char in self.members:
            char.apply_party_buffs(self.all_hits)

        # ── Phase 5 : 「버퍼의 최종 스탯을 읽어」 만드는 버프 (방식 B) ─────────────
        # 여기서 등록되는 것은 값이 아니라 **함수**다. 실제 계산은 그 필드를 읽는
        # 순간(늦어도 Phase 5.5)에 일어나므로, 아래 루프의 멤버 순서는 결과와 무관하다.
        core_snapshot = _snapshot_core_pools(self.all_hits)
        for char in self.members:
            char.apply_dependent_buffs(self.all_hits)      # 캐릭터 스케일 버프
            char.apply_dependent_equipment(self.all_hits)  # 무기/성유물 스케일 패시브
        # 파티 구성으로 정해지는 방식 B 버프 — 특정 캐릭터 킷이 아니라서 여기 따로 있다.
        _apply_full_moon_lunar_bonus(self.all_hits, self.members)
        # 정확성 가드 — 이 단계에서 코어 풀을 **즉시 값으로** 바꾸지 않았는지 본다.
        # (지연 기여로 바뀐 몫은 순서 무관이 보장되므로 봐준다. _assert_core_pools_unchanged 참고.)
        _assert_core_pools_unchanged(self.all_hits, core_snapshot)

        # ── Phase 5.5 (정산) : 남은 지연 기여를 전부 값으로 확정한다 ───────────────
        # 지연 기여는 그 필드를 읽는 순간 계산되지만, 피해 보너스처럼 여기까지 아무도
        # 읽지 않는 필드도 있다. 모든 등록이 끝난 지금 훑어야 어느 것도 놓치지 않는다.
        for char_hits in self.all_hits.values():
            for hit in char_hits.values():
                hit.settle()

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
    "hp_flat", "hp_pct", "atk_flat", "atk_flat_derived", "atk_pct", "def_flat", "def_pct",
)


def _read_core_pools(hit: SkillHit) -> tuple:
    """가드 전용 raw 읽기 — 지연 기여를 **확정시키지 않는다**.

    평범한 getattr은 미결 지연 기여가 있으면 그 자리에서 확정해 버린다(SkillHit의 읽기
    가로채기). 가드는 감시자일 뿐 소비자가 아니므로, 값을 보러 왔다가 확정 시점을
    Phase 5.5보다 앞당기면 안 된다 — 그러면 아직 등록되지 않은 기여를 놓친 채 굳는다."""
    return tuple(object.__getattribute__(hit, f) for f in _CORE_POOL_FIELDS)


def _snapshot_core_pools(all_hits: dict[Character, dict[str, SkillHit]]) -> dict[int, tuple]:
    snap: dict[int, tuple] = {}
    for char_hits in all_hits.values():
        for hit in char_hits.values():
            snap[id(hit)] = _read_core_pools(hit)
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
            after = _read_core_pools(hit)
            if before != after:
                # 지연 기여로 바뀐 필드는 봐준다 — 값이 등록 순서가 아니라 읽는 시점에
                # 정해지므로 파티 멤버 순서와 무관하고, 순환은 CyclicBuffError가 잡는다.
                # 여기서 막아야 하는 것은 순서에 좌우되는 **즉시** 가산뿐이다.
                lazy = hit._lazy_written
                changed = [f for f, b, a in zip(_CORE_POOL_FIELDS, before, after)
                           if b != a and f not in lazy]
                if not changed:
                    continue
                raise AssertionError(
                    f"[정확성 가드] apply_dependent_buffs(스케일 단계)가 ATK/DEF/HP 코어 풀을 "
                    f"**즉시 값으로** 변경했습니다: {char.__class__.__name__} / '{hit.name}' "
                    f"→ {changed}. 이 단계의 즉시 가산은 파티 멤버 순서에 좌우된다. 코어 스탯 "
                    f"기여라면 contribute_dependent_stats로, 스탯을 읽지 않는 고정 버프라면 "
                    f"apply_party_buffs로 옮기고, 최종 스탯 기반이라면 방식 B"
                    f"(flat_dmg_bonus로 차원 변환)나 지연 기여(add에 함수 전달)를 사용하세요."
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


# ── 달반응 반응 피해의 트리거 참여자 ─────────────────────────────────────────────
# 새 코드는 이 파일 **맨 아래**에 붙인다 — 위에 끼워 넣으면 기존 ask_* 호출 지점의 lineno가
# 밀려 질문 ID가 바뀌고, 웹에 저장된 답변이 조용히 떨어진다(prompt._next_id 참고).
def _ask_lunar_participants(members) -> dict[ReactionType, list]:
    """달반응을 실제로 트리거하는 파티원 — 반응마다 ask_multi_choice 한 번.

    후보는 core.reaction.lunar_candidates가 유도한다(전환 캐릭터가 파티에 있고, 반응에 필요한
    두 원소가 다 있을 때 그 두 원소의 파티원). 그중 누가 실제로 트리거하는지는 실측 전이라
    유저에게 맡긴다 — 후보가 없으면 질문도 없다.

    여기서 묻는 것은 **참여자뿐이다.** 가중치는 피해 순위로 정해져 최종 스탯이 확정된 뒤에만
    계산할 수 있으므로 core.party_reaction이 나중에 붙인다.
    """
    picked: dict[ReactionType, list] = {}
    for reaction, _element, candidates in lunar_candidates(members):
        if not candidates:
            continue
        options = [f"{c.name} ({c.element.value})" for c in candidates]
        idxs = ask_multi_choice(
            f"[{reaction.value}] 이 로테이션에서 {reaction.value}을 트리거하는 파티원", options
        )
        chosen = [candidates[i] for i in idxs]
        if chosen:
            picked[reaction] = chosen
    return picked


# 이 import가 파일 맨 위가 아닌 이유: 위쪽에 한 줄을 더하면 아래 ask_* 호출 지점의 lineno가
# 밀려 질문 ID가 바뀌고 웹에 저장된 답변이 떨어진다(prompt._next_id). 모듈 최상단 import와
# 동작은 같다 — import 문은 모듈을 읽을 때 실행되고, 함수 본문은 호출 시점에 전역을 찾는다.
from gidc.core.stellar import CONDUCT_MAX_HITS, GUST_MAX_LEVEL


# ── 별 반응 : 트리거 참여자 + 반응 계수의 재료 ────────────────────────────────────
# 여기서 **아래로만** 코드를 붙인다. 위 규칙(prompt._next_id)이 그대로 적용된다 — 이 블록을
# _ask_lunar_participants 위에 끼워 넣었다면 달반응 참여자 질문의 ID가 바뀌어 웹에 저장된
# 답변이 떨어졌을 것이다. build_profiles 쪽도 같은 이유로 줄을 늘리지 않고 기존 한 줄을
# _ask_celestial_inputs 호출로 **교체**했다.
def _ask_celestial_inputs(all_hits, members) -> tuple[dict, dict]:
    """달·별 반응의 Phase 4 유저 입력을 한 번에 모아 (달 참여자, 별 참여자)를 돌려준다.

    build_profiles에서 두 줄을 쓰지 않고 이 함수 하나로 접은 이유는 줄 수 때문이다 —
    위 주석 참고. 순서는 달 → 별이며, 달반응 질문의 호출 지점이 위쪽에 그대로 남아 있어야
    기존 답변이 붙어 있는다.
    """
    lunar = _ask_lunar_participants(members)
    _ask_stellar_state(all_hits, members)
    return lunar, _ask_stellar_participants(members)


def _ask_stellar_state(all_hits, members) -> None:
    """별 반응 **반응 계수의 재료**를 묻고 모든 히트에 실어 준다.

    계수 자체는 여기서 만들지 않는다 — core.stellar의 함수가 유일한 출처다. 여기서 하는 일은
    그 함수가 읽을 재료를 히트에 놓아 주는 것뿐이다(profile._reaction_multiplier).

    파티 구성에서 **유도할 수 없는** 값이라 유저에게 묻는다. 엔진에는 히트 카운팅도 로테이션
    모델도 없고, 별빛 돌풍은 오데트(미구현) 킷이 올리는 상태다. 실측으로 파티 구성만으로
    정해진다고 밝혀지면 이 함수만 core.party_state의 유도 함수 호출로 바꾸면 된다.

    조건이 성립하지 않으면 **묻지 않는다** — 후보가 없을 때 질문이 뜨면 안 되고, 회귀
    기준선 파티(전환 캐릭터 없음)의 답변 스트림도 지켜진다.

    버프가 아니라 로테이션 서술자이므로 hit.add가 아니라 직접 대입한다. add로 넣으면 여러
    출처가 더해져 「기록 히트 20회」 같은 값이 만들어지고, 원장에도 버프인 양 찍힌다.
    """
    for reaction, _element, _candidates in stellar_conditions(members):
        if reaction is ReactionType.STELLAR_CONDUCT:
            hits = ask_int(
                f"[{reaction.value}] 기록된 얼음·번개 히트 수",
                0, CONDUCT_MAX_HITS,
            )
            _set_on_all_hits(all_hits, "stellar_recorded_hits", hits)
        elif reaction is ReactionType.STELLAR_SWIRL:
            # 선택지 수와 계수표 길이가 갈라지지 않게 core.stellar의 상한에서 만든다.
            options = ["없음"] + [f"Lv.{lv}" for lv in range(1, GUST_MAX_LEVEL + 1)]
            level = ask_choice(f"[{reaction.value}] 별빛 돌풍 레벨", options)
            _set_on_all_hits(all_hits, "stellar_gust_level", level)


def _set_on_all_hits(all_hits, field: str, value: float) -> None:
    for char_hits in all_hits.values():
        for hit in char_hits.values():
            setattr(hit, field, value)


def _ask_stellar_participants(members) -> dict[ReactionType, list]:
    """별 반응을 실제로 트리거하는 파티원 — _ask_lunar_participants와 같은 규약.

    후보는 stellar_candidates가 유도한다 — **반응 피해를 내는** 별 반응만 남으므로 실제로는
    별 확산 한 번만 묻는다. 별 초전도는 참여자를 물어도 쓸 반응 행이 없다(반응 피해가 없고
    직접 피해는 캐릭터 히트로 들어간다).
    """
    picked: dict[ReactionType, list] = {}
    for reaction, _element, candidates in stellar_candidates(members):
        if not candidates:
            continue
        options = [f"{c.name} ({c.element.value})" for c in candidates]
        idxs = ask_multi_choice(
            f"[{reaction.value}] 이 로테이션에서 {reaction.value}을 트리거하는 파티원", options
        )
        chosen = [candidates[i] for i in idxs]
        if chosen:
            picked[reaction] = chosen
    return picked
