"""파티 구성에서 유도되는 상태.

캐릭터에 붙은 CharacterTrait를 세어 파티 단위 효과를 판정한다.
유저에게 묻지 않고 계산하므로 성유물·캐릭터가 어디서 읽든 항상 같은 값이 나온다.

Character를 import하지 않는 leaf 모듈이다(순환 참조 방지). 파티원은 traits와 element
속성만 가지면 되므로 리스트든 all_hits 딕셔너리든 그대로 넘길 수 있다.
"""
from gidc.enums import CharacterTrait, Element, MoonsignLevel

# 「마도·비밀 의식」 획득에 필요한 마도 캐릭터 수
_HEXEREI_RITE_MIN = 2

# 달빛 징조 캐릭터 수 → 달빛 징조 레벨 (경계값은 내림차순으로 판정)
_MOONSIGN_THRESHOLDS = [
    (2, MoonsignLevel.FULL),      # 2명 이상 → 보름
    (1, MoonsignLevel.CRESCENT),  # 1명      → 초승
]

# 레벨 사다리 — 「달빛 징조 상승」 보유자가 이 순서로 한 칸씩 올린다.
# MoonsignLevel의 선언 순서를 그대로 믿지 않고 여기 다시 적는 이유는, 레벨이 늘어날 때
# 「어느 쪽이 위인가」를 열거형 선언 순서에 맡기면 조용히 뒤집히기 때문이다.
_MOONSIGN_LADDER = (MoonsignLevel.NONE, MoonsignLevel.CRESCENT, MoonsignLevel.FULL)


def count_trait(members, trait: CharacterTrait) -> int:
    """해당 특성을 보유한 파티원 수."""
    return sum(1 for char in members if trait in char.traits)


def has_hexerei_rite(members) -> bool:
    """파티가 「마도·비밀 의식」 효과를 보유하는가 (마도 캐릭터 2명 이상)."""
    return count_trait(members, CharacterTrait.HEXEREI) >= _HEXEREI_RITE_MIN


def hexerei_rite_for(char, members) -> bool:
    """이 캐릭터가 「마도·비밀 의식」을 획득했는가 — 자기 킷의 마도 효과를 켜는 조건.

    마도 효과는 캐릭터 자신의 마도 특성(「마녀의 전야제」 등)이 내놓는다. 마녀의 과제를
    완료하지 않았으면 그 특성 자체가 없으므로, 파티에 마도가 몇 명이든 내놓을 효과가 없다
    — 정원(2명)은 그다음 조건이다. 그래서 파티 상태만 묻는 has_hexerei_rite와 갈린다.

    같은 특성이 두 곳을 정한다는 점이 요점이다: 해제되지 않은 캐릭터는 count_trait의
    정원에도 들어가지 않고(has_hexerei_rite), 효과를 받지도 내놓지도 않는다(이 함수).
    자기 킷의 마도 분기는 반드시 이쪽을 읽는다 — has_hexerei_rite만 보면 「나 말고 둘」인
    파티에서 마도가 아닌 캐릭터의 마도 강화가 조용히 켜진다.
    """
    return CharacterTrait.HEXEREI in char.traits and has_hexerei_rite(members)


def skill_level_bonus(members) -> int:
    """파티 전원이 받는 원소전투 스킬 레벨 상승분.

    현재 출처는 스커크의 고유 특성 「무예 전수」뿐이다 — 보유자가 파티에 있고, 파티 내
    모든 캐릭터가 물/얼음이며 물과 얼음이 각각 최소 1명이면 파티 전원 +1.

    유저 입력도 스탯도 보지 않고 파티 원소 구성만으로 정해지므로 히트를 만들기 전
    (Party.build_profiles의 Phase 0)에 확정해 각 캐릭터의 skill_level_bonus에 넣는다.
    """
    if not count_trait(members, CharacterTrait.MARTIAL_INSTRUCTION):
        return 0

    elements = {char.element for char in members}
    if not elements <= {Element.HYDRO, Element.CRYO}:
        return 0
    if not {Element.HYDRO, Element.CRYO} <= elements:
        return 0
    return 1


def moonsign_level(members) -> MoonsignLevel:
    """파티의 달빛 징조 레벨.

    인원수로 기본 레벨을 정한 뒤, 「달빛 징조 상승」 보유자 수만큼 사다리를 올린다
    (린네아 「서식지 조사」 — "린네아가 파티에 있을 경우 파티의 달빛 징조가 1레벨 상승한다").

    달빛 징조 캐릭터가 하나도 없으면 없음에 머문다. 상승 특성 보유자는 달빛 징조 캐릭터
    이기도 해서 실제로는 닿지 않는 자리지만, 「없음 + 상승 = 초승」이 되는 사고를 막아 둔다.
    """
    count = count_trait(members, CharacterTrait.MOONSIGN)
    if not count:
        return MoonsignLevel.NONE

    level = next(lv for threshold, lv in _MOONSIGN_THRESHOLDS if count >= threshold)
    index = (_MOONSIGN_LADDER.index(level)
             + count_trait(members, CharacterTrait.MOONSIGN_ELEVATION))
    return _MOONSIGN_LADDER[min(index, len(_MOONSIGN_LADDER) - 1)]
