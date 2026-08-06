"""히트 원소와 파티 원소 구성에서 「어떤 반응이 가능한가」를 유도한다.

유저에게 묻지 않는다 — 불 히트에 증발이 붙으려면 파티에 물이 있어야 하고, 그건 편성만
보면 안다. 반대로 전역 스위치로 반응을 켜면 얼음 히트에 증발 2.0배가 붙는 식으로 조용히
틀린다(profile._reaction_multiplier는 트리거 원소로 배율을 가른다). 그래서 화면이 내놓는
**후보 자체**를 여기서 좁힌다.

배율은 여기 두지 않는다 — profile._reaction_multiplier가 이미 갖고 있고, 같은 표가 두
군데 있으면 갈라진다. 이 모듈은 「무엇이 가능한가」에만 답한다.

party_state와 같은 leaf 모듈이다. Character도 SkillHit도 import하지 않고 Element만
받으므로, 파티원 리스트든 히트든 부르는 쪽이 원소만 꺼내 넘기면 된다.
"""
from gidc.enums import Element, ReactionType


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
