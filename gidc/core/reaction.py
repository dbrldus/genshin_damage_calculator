"""히트 원소와 파티 원소 구성에서 「어떤 반응이 가능한가」를 유도한다.

유저에게 묻지 않는다 — 불 히트에 증발이 붙으려면 파티에 물이 있어야 하고, 그건 편성만
보면 안다. 반대로 전역 스위치로 반응을 켜면 얼음 히트에 증발 2.0배가 붙는 식으로 조용히
틀린다(profile._reaction_multiplier는 트리거 원소로 배율을 가른다). 그래서 화면이 내놓는
**후보 자체**를 여기서 좁힌다.

배율은 여기 두지 않는다 — profile._reaction_multiplier(달반응까지)와 core.stellar(별 반응)가
이미 갖고 있고, 같은 표가 두 군데 있으면 갈라진다. 이 모듈은 「무엇이 가능한가」에만 답한다.
core.stellar에서 가져오는 것도 계수가 아니라 「이 반응이 반응 피해를 내는가」 하나뿐이다.

party_state와 같은 급의 leaf 모듈이다. Character도 SkillHit도 import하지 않는다 — 받는 것은
Element이거나, element·traits 속성만 있으면 되는 파티원 시퀀스다(달·별 반응 후보 유도).
그래서 파티원 리스트든 all_hits 딕셔너리든 히트든 부르는 쪽이 그대로 넘길 수 있다.
"""
from gidc.enums import CharacterTrait, Element, ReactionType
from gidc.core.party_state import count_trait
from gidc.core.stellar import stellar_has_reaction_damage


# ── 증폭 (증발·융해) : 히트의 base dmg에 **곱해진다** ─────────────────────────
# 트리거 원소 → ((반응, 필요한 오라 원소), …)
_AMPLIFY_RULES: dict[Element, tuple[tuple[ReactionType, Element], ...]] = {
    Element.PYRO:  ((ReactionType.VAPORIZE, Element.HYDRO),
                    (ReactionType.MELT,     Element.CRYO)),
    Element.HYDRO: ((ReactionType.VAPORIZE, Element.PYRO),),
    Element.CRYO:  ((ReactionType.MELT,     Element.PYRO),),
}

# ── 격화 (촉진·발산) : 히트의 base dmg에 **더해진다** ────────────────────────
_CATALYZE_RULES: dict[Element, tuple[tuple[ReactionType, Element], ...]] = {
    Element.ELECTRO: ((ReactionType.AGGRAVATE, Element.DENDRO),),
    Element.DENDRO:  ((ReactionType.SPREAD,    Element.ELECTRO),),
}

# ── 격변 : 히트가 아니라 **별도의 피해 인스턴스** ────────────────────────────
# 트리거 원소 → ((반응, 필요한 오라 원소들, 피해 원소), …)
#
# 피해 원소는 **반응이** 정한다 — 과부하는 번개 캐릭터가 터뜨려도 불 내성을 탄다.
# 확산만 확산된 원소가 곧 피해 원소라 원소별로 한 줄씩 둔다.
#
# 만개는 씨앗(물+풀)을 번개가, 발화는 불이 터뜨린다 — 트리거가 한쪽으로 고정이라 해당
# 원소 캐릭터에만 실린다. 나머지(과부하·초전도·감전·연소·개화)는 두 원소 어느 쪽이든
# 트리거할 수 있으므로 양쪽에 다 실린다. 실제로 둘 다 가능하고, 누가 터뜨렸느냐에 따라
# 쓰이는 EM이 달라지므로 양쪽을 다 보여주는 것이 맞다.
#
# 바위는 없다 — 결정 반응은 보호막이라 피해가 없다.
# 쇄빙도 없다 — 빙결된 적을 물리/양손검/바위로 때려야 하는데 파티 원소만으로는 유도되지
# 않는다(profile._REACTION_MULT_CONST에 배율 3.0은 남아 있다).
_TRANSFORMATIVE_RULES: dict[
    Element, tuple[tuple[ReactionType, frozenset[Element], Element], ...]
] = {
    Element.PYRO: (
        (ReactionType.OVERLOADED, frozenset({Element.ELECTRO}),               Element.PYRO),
        (ReactionType.BURNING,    frozenset({Element.DENDRO}),                Element.PYRO),
        (ReactionType.BURGEON,    frozenset({Element.HYDRO, Element.DENDRO}), Element.DENDRO),
    ),
    Element.HYDRO: (
        (ReactionType.ELECTROCHARGED, frozenset({Element.ELECTRO}), Element.ELECTRO),
        (ReactionType.BLOOM,          frozenset({Element.DENDRO}),  Element.DENDRO),
    ),
    Element.CRYO: (
        (ReactionType.SUPERCONDUCT, frozenset({Element.ELECTRO}), Element.CRYO),
    ),
    Element.ELECTRO: (
        (ReactionType.OVERLOADED,     frozenset({Element.PYRO}),                  Element.PYRO),
        (ReactionType.SUPERCONDUCT,   frozenset({Element.CRYO}),                  Element.CRYO),
        (ReactionType.ELECTROCHARGED, frozenset({Element.HYDRO}),                 Element.ELECTRO),
        (ReactionType.HYPERBLOOM,     frozenset({Element.HYDRO, Element.DENDRO}), Element.DENDRO),
    ),
    Element.DENDRO: (
        (ReactionType.BURNING, frozenset({Element.PYRO}),  Element.PYRO),
        (ReactionType.BLOOM,   frozenset({Element.HYDRO}), Element.DENDRO),
    ),
    # 확산은 확산된 원소가 곧 피해 원소다 — 내성이 원소마다 다르므로 한 줄로 묶을 수 없다.
    Element.ANEMO: tuple(
        (ReactionType.SWIRL, frozenset({e}), e)
        for e in (Element.PYRO, Element.HYDRO, Element.CRYO, Element.ELECTRO)
    ),
}


def aura_pool(members, trigger) -> frozenset[Element]:
    """트리거 캐릭터 **본인을 제외한** 파티원의 원소 — 오라를 깔 수 있는 쪽.

    본인을 빼는 이유는 자기 원소에 자기가 반응할 수 없기 때문이다. 불 캐릭터 혼자
    있는 파티에서 증발 버튼이 뜨면 안 된다.
    """
    return frozenset(m.element for m in members if m is not trigger)


def hit_candidates(hit_element: Element | None,
                   aura: frozenset[Element]) -> tuple[ReactionType, ...]:
    """이 히트에 붙일 수 있는 **히트 피해를 바꾸는** 반응 (증폭 + 격화).

    원소가 없는 히트는 물리로 계산되므로 반응하지 않는다(스커크 평타 등).
    """
    if hit_element is None:
        return ()
    out: list[ReactionType] = []
    for rules in (_AMPLIFY_RULES, _CATALYZE_RULES):
        for reaction, required in rules.get(hit_element, ()):
            if required in aura:
                out.append(reaction)
    return tuple(out)


def transformative_candidates(
    trigger_element: Element,
    aura: frozenset[Element],
) -> tuple[tuple[ReactionType, Element], ...]:
    """이 캐릭터가 트리거할 수 있는 격변 반응과 그 **피해 원소**.

    반환값의 원소는 내성을 고를 때 쓴다 — 캐리어 히트의 원소가 아니다
    (profile.build_transformative_context 참고).
    """
    return tuple(
        (reaction, dmg_element)
        for reaction, required, dmg_element in _TRANSFORMATIVE_RULES.get(trigger_element, ())
        if required <= aura
    )


# ── 달반응 : 파티 단위 피해 인스턴스 ────────────────────────────────────────────
# 격변과 다른 점이 둘이다.
#   · 트리거 캐릭터 한 명의 것이 아니다 — 트리거할 수 있는 파티원 여럿이 각자 자기 스탯으로
#     피해를 넣고 그 **가중합**이 파티의 달반응 피해다(core.party_reaction).
#   · 달빛 징조만으로는 전환되지 않는다 — 전환을 일으키는 **캐릭터**가 파티에 있어야 한다.
#     (이네파 Moonsign: 「파티 내 캐릭터가 감전 반응 발동 시, 달 감전 반응으로 전환되며…」)
#
# 반응 → (전환 특성, 필요한 파티 원소 = 곧 트리거 후보 원소, 피해 원소)
#
# 피해 원소는 콜롬비나의 달반응 직접 피해 히트 선언과 맞춘다 — 같은 반응이 직접 피해와 반응
# 피해에서 서로 다른 내성을 타면 안 된다.
#
# 달개화는 없다 — profile._LUNAR_MULT의 LUNAR_REACTION 배율이 0.0이라 반응 피해 성분이
# 아예 없다(씨앗이 터지는 직접 피해만 있다).
_LUNAR_RULES: dict[ReactionType, tuple[CharacterTrait, frozenset[Element], Element]] = {
    ReactionType.LUNAR_CHARGED: (
        CharacterTrait.LUNAR_CHARGED_CONVERTER,
        frozenset({Element.HYDRO, Element.ELECTRO}),
        Element.ELECTRO,
    ),
    ReactionType.LUNAR_CRYSTALLIZE: (
        CharacterTrait.LUNAR_CRYSTALLIZE_CONVERTER,
        frozenset({Element.GEO, Element.HYDRO}),
        Element.GEO,
    ),
}

# 달반응으로 전환되면 원래 격변은 더는 일어나지 않는다. 값은 (격변 반응, **피해 원소**) —
# 원소까지 묶는 이유는 suppressed_transformatives의 docstring에 있다.
# 결정은 여기 없다 — 보호막이라 애초에 격변 후보가 아니다(위 _TRANSFORMATIVE_RULES 주석).
# 개화도 없다 — 달개화 반응 피해가 0이라 「대체」하면 화면에서 정보가 그냥 사라진다.
_LUNAR_SUPPRESSES: dict[ReactionType, tuple[ReactionType, Element]] = {
    ReactionType.LUNAR_CHARGED: (ReactionType.ELECTROCHARGED, Element.ELECTRO),
}


def lunar_candidates(members) -> tuple[tuple[ReactionType, Element, tuple], ...]:
    """이 파티에서 일어날 수 있는 달반응과 (반응, 피해 원소, 트리거 후보 파티원).

    세 조건을 모두 만족해야 후보가 선다.
      1. 전환 특성 보유자가 파티에 1명 이상 — 없으면 그냥 감전/결정이다.
      2. 필요한 두 원소가 둘 다 파티에 있음 — 반응 자체가 성립해야 한다.
      3. 후보 = 그 두 원소를 가진 파티원 전원 (파티 순서 유지).

    달빛 징조 레벨은 보지 않는다 — 조건은 「전환 캐릭터가 파티에 있는가」 하나다. 실측으로
    달빛 징조까지 필요하다고 밝혀지면 이 함수만 고치면 된다.

    후보 중 **누가 실제로 트리거하는지**는 여기서 정하지 않는다 — 실측 전이라 유저가 고른다
    (party._ask_lunar_participants).
    """
    members = list(members)
    elements = {m.element for m in members}

    out: list[tuple[ReactionType, Element, tuple]] = []
    for reaction, (trait, required, dmg_element) in _LUNAR_RULES.items():
        if not count_trait(members, trait):
            continue
        if not required <= elements:
            continue
        out.append((reaction, dmg_element,
                    tuple(m for m in members if m.element in required)))
    return tuple(out)


# ── 별 반응 : 달반응과 같은 규약, 계수만 다르다 ──────────────────────────────────
# 성립 조건도 후보 유도도 달반응과 같은 모양이다(전환 캐릭터 + 필요한 두 원소). 다른 것은
# 반응 계수가 상수가 아니라는 점뿐이고, 그건 core.stellar가 갖고 있다.
#
# 반응 → (전환 특성, 필요한 파티 원소 = 곧 트리거 후보 원소, 피해 원소)
#
# 피해 원소는 둘 다 얼음이다 — 별 확산은 확산된 원소가 곧 피해 원소이고(얼음+바람 조합),
# 별 초전도의 피해 원소는 원래 초전도와 같이 얼음이다.
_STELLAR_RULES: dict[ReactionType, tuple[CharacterTrait, frozenset[Element], Element]] = {
    ReactionType.STELLAR_CONDUCT: (
        CharacterTrait.STELLAR_CONDUCT_CONVERTER,
        frozenset({Element.CRYO, Element.ELECTRO}),
        Element.CRYO,
    ),
    ReactionType.STELLAR_SWIRL: (
        CharacterTrait.STELLAR_SWIRL_CONVERTER,
        frozenset({Element.CRYO, Element.ANEMO}),
        Element.CRYO,
    ),
}

# 별 반응으로 치환되는 (격변 반응, 피해 원소). **둘 다 대체한다** — 실측 확인이다.
#
# 별 초전도는 반응 피해가 없는데도(반응 시 「극지의 별 영역」 생성) 초전도를 지운다. 위
# _LUNAR_SUPPRESSES가 달개화를 뺀 이유(「대체하면 화면에서 정보가 그냥 사라진다」)와 정반대
# 결론이지만, 이쪽은 실측으로 확인된 사실이므로 실측을 따른다. 사라진 자리는 전환 캐릭터의
# 히트가 채운다 — 산드로네가 냉각 광선·프리즘탄·부성 온도 광선을 별 초전도/별 확산 직접
# 피해로 계열마다 한 벌씩 선언하고 있다(content.characters.cryo.sandrone).
_STELLAR_SUPPRESSES: dict[ReactionType, tuple[ReactionType, Element]] = {
    ReactionType.STELLAR_CONDUCT: (ReactionType.SUPERCONDUCT, Element.CRYO),
    ReactionType.STELLAR_SWIRL:   (ReactionType.SWIRL,        Element.CRYO),
}


def stellar_conditions(members) -> tuple[tuple[ReactionType, Element, tuple], ...]:
    """이 파티에서 **성립하는** 별 반응 전부와 (반응, 피해 원소, 트리거 후보 파티원).

    lunar_candidates와 같은 3조건 게이트다. 다른 것은 반응 피해가 없는 별 초전도도
    여기서는 빠지지 않는다는 점이다 — 억제 판정과 유저 입력 질문 게이트가 「반응 피해가
    있는가」와 무관하게 이 판정을 필요로 한다(_STELLAR_SUPPRESSES 주석).

    반응 행에 쓸 후보는 stellar_candidates가 여기서 다시 걸러낸다.
    """
    members = list(members)
    elements = {m.element for m in members}

    out: list[tuple[ReactionType, Element, tuple]] = []
    for reaction, (trait, required, dmg_element) in _STELLAR_RULES.items():
        if not count_trait(members, trait):
            continue
        if not required <= elements:
            continue
        out.append((reaction, dmg_element,
                    tuple(m for m in members if m.element in required)))
    return tuple(out)


def stellar_candidates(members) -> tuple[tuple[ReactionType, Element, tuple], ...]:
    """그중 **반응 피해를 내는** 별 반응만. 반응 행과 참여자 질문이 이것을 읽는다.

    조건을 다시 적지 않고 stellar_conditions에서 걸러낸다 — 같은 판정이 두 군데 적히면
    한쪽만 고쳐져, 억제는 걸렸는데 표에는 아무것도 안 뜨거나 그 반대가 된다.

    현재 남는 것은 별 확산뿐이다(별 초전도는 반응 피해가 없다).
    """
    return tuple(
        row for row in stellar_conditions(members)
        if stellar_has_reaction_damage(row[0])
    )


def suppressed_transformatives(members) -> frozenset[tuple[ReactionType, Element]]:
    """달·별 반응으로 치환돼 더는 일어나지 않는 격변 반응 — (반응, **피해 원소**) 쌍.

    조건을 다시 쓰지 않고 후보 유도 결과에서 유도한다 — 같은 판정이 두 군데 적히면
    한쪽만 고쳐져, 표에서 반응이 조용히 사라지거나 감전과 달감전이 동시에 뜬다.

    **원소까지 묶어 내는 이유**: 확산은 _TRANSFORMATIVE_RULES에서 확산된 원소마다 한 행씩
    나온다(불·물·얼음·번개). 반응 타입만으로 막으면 별 확산 하나가 불·물·번개 확산까지
    같이 지운다. 초전도는 얼음 트리거·번개 트리거 두 행이 있지만 **둘 다 피해 원소가
    얼음**이라 (초전도, 얼음) 하나로 정확히 둘 다 막힌다. 달감전도 마찬가지로 두 행 모두
    피해 원소가 번개다 — 원소를 붙여도 동작이 달라지지 않는다.

    별 쪽은 stellar_candidates가 아니라 **stellar_conditions**에서 유도한다. 별 초전도는
    반응 행 후보에 없어도 억제는 해야 하기 때문이다(_STELLAR_SUPPRESSES 주석).
    """
    out: set[tuple[ReactionType, Element]] = set()

    for candidates, suppresses in ((lunar_candidates(members),   _LUNAR_SUPPRESSES),
                                   (stellar_conditions(members), _STELLAR_SUPPRESSES)):
        for reaction, _element, _cands in candidates:
            if reaction in suppresses:
                out.add(suppresses[reaction])

    return frozenset(out)
