"""달·별 반응 **반응 피해**의 파티 단위 집계.

이 반응 피해는 캐릭터 한 명의 것이 아니다. 트리거할 수 있는 파티원들이 **각자 자기 스탯으로**
피해를 넣고, 그 가중합이 파티의 피해다. 그래서 격변처럼 「캐릭터 1명 = 행 1개」로 표현되지
않고, 계산도 캐릭터 루프 안이 아니라 여기서 한 번에 한다.

가중치는 **그 순간 실제로 들어간 피해의 순위**로 정해진다. 그래서 최종 스탯이 확정된 뒤
(Party.build_profiles가 끝난 뒤)에만 계산할 수 있고, 치명타가 누구에게 터졌느냐에 따라 순위가
뒤집히면 가중치도 같이 옮겨간다 — 크리 한 방으로 3등이 1등이 되면 그 사람이 1등 가중치를
받는다. 반면 「누가 트리거하나」는 유저 입력이라 Phase 4에서 미리 모아 둔다
(party._ask_lunar_participants / _ask_stellar_participants). 그 둘을 이어 붙이는 자리가 이 모듈이다.

    참여자 = party.lunar_participants[reaction]        # 유저가 고른 트리거
    후보    = reaction.lunar_candidates(members)        # 전환 캐릭터 + 파티 원소로 유도
    피해    = profile.build_lunar_reaction_context      # 참여자마다 한 번

별 반응은 같은 자리에 stellar_participants / stellar_candidates /
build_stellar_reaction_context가 들어간다.

**달·별 공용이다.** 순위 배수·2^N 기댓값 접기는 어느 반응 계열이냐와 무관하고, 계열마다
다른 것은 컨텍스트를 만드는 방법뿐이다 — 그래서 party_reaction_damage가 build_context를
인자로 받는다. 계열별로 이 파일을 복제하면 기댓값 접기 로직이 두 벌 생겨 갈라진다.
"""
from dataclasses import dataclass

from gidc.core.damage import DamageResult, calculate
from gidc.enums import Element, ReactionType


# 피해 **내림차순** 순위에 붙는 배수. 실측값이다.
#
# 지분(합 1)이 아니라 순위별 배수다 — 1등은 온전히, 2등은 절반, 3·4등은 1/12만 들어간다.
# 그래서 정규화하지 않는다. 참여자가 적으면 뒤 배수는 그냥 안 쓰인다(2명이면 1 + 1/2).
#
# 「지분이 아니라 배수」라는 점이 순위를 매기는 방법을 정한다 — 지분이라면 트리거 빈도라
# 판정 결과와 무관해야 하지만, 배수는 **이번에 들어간 피해 숫자**에 붙는 값이므로 치명타가
# 터져 대소가 역전되면 순위도 따라 바뀐다(_rank_weights).
#
# 규칙이 바뀌면 **이 튜플만** 고친다.
_TRIGGER_WEIGHTS = (1, 1/2, 1/12, 1/12)


@dataclass
class ParticipantShare:
    """참여자 한 명의 몫. result는 가중치를 **곱하기 전** 값이다(그 캐릭터가 혼자 냈을 피해).

    crit_on은 「이 캐릭터의 이번 피해가 치명타로 터졌는가」다 — 참여자마다 따로 굴러가는
    판정이라 파티 단위로 하나로 묶을 수 없다. 유저가 데미지 화면에서 고른다.

    weight는 **지금 고른 치명타 조합에서의** 순위 배수다. 크리를 켜고 끄면 순위가 바뀌어
    이 값도 바뀐다 — 리스트 순서와는 무관하다(리스트는 파티 순서로 고정한다).

    crit_rate는 기댓값을 조합별로 접을 때 쓴다(_expected_over_combos). 화면에는 안 나온다.
    """
    char:      str
    weight:    float
    result:    DamageResult
    crit_rate: float = 0.0
    crit_on:   bool  = False

    @property
    def selected(self) -> float:
        """고른 치명타 상태에서 이 캐릭터가 내는 피해 (가중치 곱하기 전)."""
        return self.result.crit if self.crit_on else self.result.non_crit


@dataclass
class PartyReactionDamage:
    reaction: ReactionType
    element:  Element                    # 피해 원소 — 반응이 정한다
    shares:   list[ParticipantShare]     # 파티 순서 고정. 순위는 각 share의 weight가 말한다
    total:    DamageResult               # non_crit/crit = 양 끝 조합, expected = 조합 전체의 기댓값
    selected: float                      # 지금 고른 치명타 조합의 가중합


def _rank_weights(values: list[float]) -> list[float]:
    """값 내림차순 순위에 _TRIGGER_WEIGHTS를 붙여 **원래 순서로** 돌려준다.

    순위를 「그 순간 실제로 들어간 피해」로 매기는 것이 이 함수의 요점이다. 치명타가 한 명만
    터져 대소가 역전되면 1등 배수도 그 사람에게 간다 — 배수는 트리거 빈도가 아니라 피해
    숫자에 붙는 값이다(_TRIGGER_WEIGHTS 주석).

    동점은 파티 순서를 지킨다(sorted는 안정 정렬) — 같은 파티면 항상 같은 답이 나온다.
    _TRIGGER_WEIGHTS보다 참여자가 많으면 남는 사람은 0이다. 조용히 앞사람에 섞이지 않는다.
    """
    order = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
    weights = [0.0] * len(values)
    for rank, i in enumerate(order):
        if rank < len(_TRIGGER_WEIGHTS):
            weights[i] = _TRIGGER_WEIGHTS[rank]
    return weights


def _combo_total(values: list[float]) -> float:
    """한 치명타 조합의 가중합. 순위도 그 조합의 값으로 다시 매긴다."""
    return sum(w * v for w, v in zip(_rank_weights(values), values))


def _expected_over_combos(shares: list[ParticipantShare]) -> float:
    """총합의 **참** 기댓값 — 치명타 조합 2^N개를 확률로 접는다.

    Σ(가중치 × 개인 기댓값)으로 대신할 수 없다. 개인 기댓값을 쓰려면 가중치가 고정이어야
    하는데, 가중치는 조합마다 순위가 달라 고정이 아니다(_rank_weights). 실제로 한 명만
    크리가 터져 순위가 뒤집히는 조합에서는 배수가 다른 사람에게 가므로, 고정 가중치로 계산한
    값은 참값과 어긋난다.

    파티는 최대 4명이라 조합은 16개 이하다 — 전부 세어도 값싸다.
    """
    n = len(shares)
    total = 0.0
    for mask in range(1 << n):
        prob = 1.0
        values = []
        for i, s in enumerate(shares):
            crit = bool(mask >> i & 1)
            prob *= s.crit_rate if crit else 1.0 - s.crit_rate
            values.append(s.result.crit if crit else s.result.non_crit)
        if prob:
            total += prob * _combo_total(values)
    return total


def _weighted_total(shares: list[ParticipantShare]) -> DamageResult:
    """양 끝 조합(전원 비크리 / 전원 크리)과 조합 전체의 기댓값.

    셋 다 **각자의 순위**로 가중치를 다시 매긴다 — 전원 비크리일 때의 순위와 전원 크리일 때의
    순위가 다를 수 있다(치명타 피해가 사람마다 다르므로). 한 순위를 셋에 돌려 쓰면 양 끝값이
    실제로 나올 수 없는 숫자가 된다.

    base_dmg는 합산하지 않는다 — 서로 다른 캐릭터의 기초 피해를 더한 값은 어떤 공식에도
    나오지 않는 수라서, 화면에 흘러가면 곱해도 되는 것처럼 읽힌다.
    """
    return DamageResult(
        base_dmg = 0.0,
        non_crit = _combo_total([s.result.non_crit for s in shares]),
        crit     = _combo_total([s.result.crit     for s in shares]),
        expected = _expected_over_combos(shares),
    )


def party_reaction_damage(
    all_hits,
    enemy,
    *,
    reaction:     ReactionType,
    element:      Element,
    participants,
    build_context,
    crit_chars    = (),
) -> PartyReactionDamage | None:
    """참여자별 반응 피해를 계산해 가중합한다. 참여자가 없으면 None(행을 내지 않는다).

    participants는 Character 시퀀스다 — 유저가 고른 트리거이며, 후보(lunar_candidates 또는
    stellar_candidates)의 부분집합이어야 한다. 여기서 다시 검증하지 않는 이유는 후보 유도와
    선택이 이미 한 쌍으로 묶여 있기 때문이다(party._ask_lunar_participants).

    build_context가 **계열을 가르는 유일한 인자**다 — profile.build_lunar_reaction_context 또는
    build_stellar_reaction_context. 두 함수의 시그니처가 같으므로 아래 로직은 계열을 모른다.

    crit_chars는 「이번에 치명타가 터진」 참여자의 **이름** 모음이다. 치명타는 참여자마다 따로
    굴러가므로 파티 단위 스위치로 묶을 수 없다 — 화면에서 사람별로 켠다.

    캐리어 히트는 참여자의 첫 히트다 — 이 반응 피해는 계수도 스킬 종류도 안 타므로
    어느 히트를 잡아도 같은 값이 나온다(build_*_reaction_context와 같은 규약).
    """
    shares: list[ParticipantShare] = []
    for char in participants:
        hits = all_hits.get(char)
        if not hits:
            continue
        carrier = next(iter(hits.values()))
        ctx = build_context(
            carrier, enemy,
            reaction=reaction, element=element, char_level=char.level,
        )
        # 가중치는 순위가 정해진 뒤에 붙는다 — 일단 0으로 담고 아래에서 덮어쓴다.
        # 치명타 확률은 damage.py가 쓰는 것과 같게 잘라 둔다(_to_result).
        shares.append(ParticipantShare(
            char      = char.name,
            weight    = 0.0,
            result    = calculate(ctx),
            crit_rate = max(0.0, min(ctx.crit_rate, 1.0)),
        ))

    if not shares:
        return None

    # 순서: 치명타를 먼저 확정하고 → 그 결과로 순위를 매긴다. 거꾸로 하면(순위를 먼저 굳히면)
    # 크리로 대소가 역전돼도 원래 순위의 배수가 그대로 들어간다.
    crit_chars = set(crit_chars)
    for share in shares:
        share.crit_on = share.char in crit_chars

    # 리스트는 파티 순서로 **그대로 둔다** — 순위는 weight가 말한다. 정렬해서 내보내면
    # 크리 버튼을 누를 때마다 화면의 버튼 자리가 옮겨 다닌다.
    for share, weight in zip(shares, _rank_weights([s.selected for s in shares])):
        share.weight = weight

    return PartyReactionDamage(
        reaction = reaction,
        element  = element,
        shares   = shares,
        total    = _weighted_total(shares),
        selected = sum(s.weight * s.selected for s in shares),
    )
