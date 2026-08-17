"""별 반응의 **반응 계수**. 달반응과 갈리는 단 하나의 자리다.

별 반응은 계산식이 달반응과 똑같다(damage._calc_lunar_direct / _calc_lunar_reaction을 그대로
탄다). 다른 것은 계수뿐이다 — 달반응의 profile._LUNAR_MULT는 상수표지만, 별 반응 계수는
런타임 상태에 따라 변한다.

    별 초전도 직접 피해 : 기록된 얼음·번개 히트 수로 커진다 (0회면 1.0)
    별 확산 반응 피해   : 별빛 돌풍 레벨로 갈린다 (0.75 / 2 / 3)

그래서 상수표를 두지 않고 **함수**로 둔다. 결과값을 어디에 캐시해 두면 재료가 바뀌었는데
값이 안 따라오는 사고가 나므로, 소비처는 언제나 이 함수를 부른다(profile._reaction_multiplier).

계수 규칙이 바뀌면 **이 모듈만** 고친다.

party_state·reaction과 같은 급의 leaf다 — Character도 SkillHit도 import하지 않는다. 받는 것은
ReactionType·DmgType과 정수 두 개뿐이다.
"""
from gidc.enums import DmgType, ReactionType


# ── 별 초전도 ────────────────────────────────────────────────────────────────
# 반응 피해가 없다 — 반응하면 「극지의 별 영역」을 생성하고, 피해는 그 영역의 직접 피해로
# 들어간다(stellar_has_reaction_damage). 그 직접 피해의 계수가 아래 규칙으로 커진다.
#
# 기록된 히트가 하나도 없으면 1.0이고, 1회 이상이면 자리가 1.4로 **점프한 뒤** 히트당
# 0.05씩 붙는다. 그래서 0회와 1회 사이가 연속이 아니다(1.0 → 1.45) — 실측 확정값이다.
_CONDUCT_NO_HIT   = 1.0
_CONDUCT_BASE     = 1.4
_CONDUCT_STEP     = 0.05
_CONDUCT_MAX_HITS = 12          # 이 수를 넘는 히트는 세지 않는다 (계수 상한 2.0)

# ── 별 확산 ──────────────────────────────────────────────────────────────────
# 직접 피해 계수는 고정 1.0이고, 반응 피해 계수만 별빛 돌풍 레벨로 갈린다.
_SWIRL_DIRECT   = 1.0
_SWIRL_REACTION = (0.75, 2.0, 3.0)      # 별빛 돌풍 레벨 0(없음) / 1 / 2

# 별빛 돌풍 레벨의 상한. 질문의 선택지와 계수표가 갈라지지 않게 표에서 유도한다.
GUST_MAX_LEVEL = len(_SWIRL_REACTION) - 1

# 기록 히트 수의 상한 — 질문(party._ask_stellar_state)이 ask_int의 max_val로 읽는다.
# 계수 규칙과 질문이 같은 숫자를 보게 하려고 내보낸다.
CONDUCT_MAX_HITS = _CONDUCT_MAX_HITS


def conduct_direct_multiplier(recorded_hits: float) -> float:
    """별 초전도 직접 피해의 반응 계수. 0회 → 1.0, n회 → 1.4 + 0.05 × min(n, 12).

    1회 = 1.45, 12회 이상 = 2.00.
    """
    if recorded_hits <= 0:
        return _CONDUCT_NO_HIT
    counted = min(recorded_hits, _CONDUCT_MAX_HITS)
    return _CONDUCT_BASE + _CONDUCT_STEP * counted


def swirl_reaction_multiplier(gust_level: float) -> float:
    """별 확산 반응 피해의 반응 계수. 별빛 돌풍 레벨 0/1/2 → 0.75 / 2 / 3.

    범위를 벗어난 레벨은 잘라서 쓴다 — 답변이 남아 있는 채로 표가 짧아지면(레벨 상한이
    내려가면) 인덱스 에러로 계산 전체가 죽는 것보다 낫다.
    """
    level = int(max(0, min(gust_level, GUST_MAX_LEVEL)))
    return _SWIRL_REACTION[level]


def stellar_has_reaction_damage(reaction: ReactionType) -> bool:
    """이 별 반응이 **반응 피해**를 내는가.

    별 초전도는 내지 않는다 — 반응 시 「극지의 별 영역」을 생성하고 직접 피해만 있다.
    반응 행 후보를 좁히는 데 쓴다(reaction.stellar_candidates).

    **억제와는 무관하다.** 별 초전도는 반응 피해가 없어도 원래 초전도를 대체한다
    (reaction._STELLAR_SUPPRESSES) — 실측 확인. 그래서 이 판정을 억제에 재사용하면 안 된다.
    """
    return reaction is not ReactionType.STELLAR_CONDUCT


def stellar_multiplier(
    reaction: ReactionType,
    dmg_type: DmgType,
    *,
    recorded_hits: float = 0.0,
    gust_level:    float = 0.0,
) -> float:
    """별 반응 하나의 반응 계수. profile._reaction_multiplier가 유일한 소비처다.

    재료(recorded_hits·gust_level)는 히트가 나른다 — 파티 단위 유저 입력이며
    party._ask_stellar_state가 모든 히트에 실어 준다.

    없는 조합(별 초전도의 반응 피해)은 0.0이다. 1.0으로 두면 존재하지 않는 피해가
    「계수 1인 피해」로 화면에 뜬다.
    """
    if reaction is ReactionType.STELLAR_CONDUCT:
        if dmg_type is DmgType.STELLAR_DIRECT:
            return conduct_direct_multiplier(recorded_hits)
        return 0.0                      # 별 초전도는 반응 피해가 없다

    if reaction is ReactionType.STELLAR_SWIRL:
        if dmg_type is DmgType.STELLAR_DIRECT:
            return _SWIRL_DIRECT
        return swirl_reaction_multiplier(gust_level)

    raise ValueError(f"별 반응이 아닙니다: {reaction!r}")
