from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from gidc.enums import DmgType, Element, ReactionType
from gidc.enums import StatType
from gidc.core.damage import DamageContext
from gidc.core.enemy import Enemy
from gidc.core.stellar import stellar_multiplier

# ── 디버그: 버프 기여 원장(explain_hit) ──────────────────────────────────────
# 각 히트 필드에 '누가 얼마를' 넣었는지 기록한다. 평상시엔 꺼져 있어(_RECORD_ENABLED=False)
# add()가 += 와 수치적으로 완전히 동일하다. explain 워크플로에서만 set_recording(True)로 켠다.
_RECORD_ENABLED = False


def set_recording(on: bool) -> None:
    """버프 기여 기록을 켜고 끈다. build_profiles() 호출 전에 켜야 원장이 채워진다."""
    global _RECORD_ENABLED
    _RECORD_ENABLED = on


def is_recording() -> bool:
    return _RECORD_ENABLED


# ── 지연 기여(방식 B) ────────────────────────────────────────────────────────
# 「버퍼의 최종 스탯을 읽어서」 만드는 버프는 값을 당장 알 수 없다 — 그 버퍼의 스탯도
# 다른 캐릭터가 아직 채우는 중일 수 있기 때문이다. 그래서 값 대신 **함수**를 등록하고,
# 그 필드를 실제로 읽는 순간 계산한다(지연 평가). 등록 순서·파티 멤버 순서와 무관하게
# 같은 결과가 나오고, 사슬이 몇 단이든 필요한 만큼 재귀로 풀린다.
#
#     hit.add("em_from_pct_share", lambda: ineffa_hit.current_atk() * 0.06, self)
#     hit.add("flat_dmg_bonus",    lambda: citlali_hit.elemental_mastery * 12, self)
#
# 순환(A가 B를 읽고 B가 A를 읽는 구조)은 값이 정해지지 않으므로 즉시 실패시킨다.
# 단계를 나눠 순서로 통제하던 방식을 대신하는 안전망이다.
#
# _PENDING_COUNT는 「지금 이 프로세스에 미결 기여가 하나라도 있는가」를 O(1)로 알려 준다.
# 대부분의 히트·대부분의 계산에는 지연 기여가 없으므로, 이 값이 0이면 __getattribute__가
# 아무 일도 하지 않고 바로 빠져나간다(핫패스 비용 최소화).
_PENDING_COUNT = 0
# 현재 해결 중인 (히트, 필드) — 순환 탐지용. 히트를 넘나드는 순환도 잡아야 하므로 전역이다.
_RESOLVING: dict[tuple[int, str], str] = {}


class CyclicBuffError(RuntimeError):
    """버프 의존이 순환해 값이 정해지지 않는다."""


@dataclass
class Contribution:
    """한 출처가 한 필드에 더한 가산 기여. explain_hit이 필드별로 모아 보여준다."""
    source: str
    field:  str
    delta:  float
    note:   str = ""


def source_label(source: object) -> str:
    """기여 출처(문자열/캐릭터/성유물 세트 튜플/무기 클래스 등)를 표시용 라벨로 정규화한다."""
    if isinstance(source, str):
        return source
    if isinstance(source, tuple):
        # (ArtifactSet, 4) → "천상의 문 4세트"
        if len(source) == 2 and isinstance(source[1], int):
            return f"{source_label(source[0])} {source[1]}세트"
        return " · ".join(source_label(s) for s in source)
    val = getattr(source, "value", None)      # Enum(ArtifactSet 등)
    if isinstance(val, str):
        return val
    name = getattr(source, "name", None)       # Character 인스턴스
    if isinstance(name, str) and name:
        return name
    if isinstance(source, type):               # 무기 클래스 등
        return source.__name__
    return type(source).__name__


class SkillType(Enum):
    NORMAL_ATK  = "일반 공격"
    CHARGED_ATK = "강공격"
    PLUNGING    = "낙하 공격"
    SKILL       = "원소 스킬"
    BURST       = "원소 폭발"
    # 무기 패시브가 만드는 추가 타격 (천공 시리즈의 진공의 칼날 등).
    # _SKILL_PREFIX에 **일부러 넣지 않는다** — 스킬 타입별 피해 보너스를 받지 않는 것이
    # 이 타입의 정의다. skill_dmg_field가 None을 주고 _skill_dmg_bonus가 0.0으로 접는다.
    # 일반 공격 명중으로 발동하더라도 「일반 공격 피해 보너스」는 붙지 않는다.
    WEAPON      = "무기 추가 타격"


class ScalingStat(Enum):
    ATK = "공격력"
    HP  = "HP"
    DEF = "방어력"
    EM  = "원소 마스터리"


@dataclass
class SkillHit:
    # ── 히트 서술자 (모두 기본값 — SkillHit()로 빈 객체 생성 가능) ──────────
    name:         str            = ""
    skill_type:   SkillType      = SkillType.NORMAL_ATK
    coeff:        float          = 0.0
    scaling_stat: ScalingStat    = ScalingStat.ATK
    element:      Element | None = None

    # ── 내재 반응 ────────────────────────────────────────────────────────────
    # 히트 자체가 반응 피해 인스턴스일 때 선언한다 (달감전 피해, 만개 피해, 확산 피해 등).
    # 팀 구성에 따라 붙었다 말았다 하는 '상황적' 반응(증발 평타 등)은 여기 넣지 말고
    # build_damage_context(reaction_type=...) 인자로 넘긴다 — 아래 resolve_reaction 참고.
    #
    # dmg_type이 None이면 reaction_type에서 유도한다(_REACTION_DMG_TYPE).
    # 달반응만 유도가 불가능하므로(직접 피해/반응 피해 두 자리 모두 유효) 반드시 명시해야 한다.
    reaction_type: ReactionType   = ReactionType.NONE
    dmg_type:      DmgType | None = None

    coeff_amp:    float          = 1.0
    stat_fn:      Callable[["SkillHit"], float] | None = field(default=None, repr=False)

    # ── 기본 스탯 ────────────────────────────────────────────────────────────
    #region
    hp_base:  float = 0.0
    atk_base: float = 0.0
    def_base: float = 0.0
    #endregion

    # ── % 보너스 (additive pool) ─────────────────────────────────────────────
    #region
    hp_pct:  float = 0.0
    atk_pct: float = 0.0
    def_pct: float = 0.0
    #endregion

    # ── 고정 추가치 ──────────────────────────────────────────────────────────
    #region
    hp_flat:  float = 0.0
    atk_flat: float = 0.0
    def_flat: float = 0.0
    # 「공격력에서 파생된 공격력」 지분 (자기 참조 차단용 꼬리표).
    # 최종 공격력에는 그대로 들어가지만(current_atk), 공격력을 읽어 **다시 공격력을 만드는**
    # 버프의 재료에서는 빠진다(convertible_atk). 얀사 운동량 측정기가 자기 자신을 필드 위
    # 캐릭터로 삼는 경우가 이쪽이다 — 같은 슬롯을 읽고 쓰면 값이 정해지지 않기 때문이다.
    # 뺄셈이 아니라 **별도 필드**여야 한다: 재료 쪽이 atk_flat을 읽는 순간 자기 몫의
    # 미결 지연 기여가 확정을 요구해 다시 순환이 된다. EM 쪽(em_from_flat /
    # em_from_pct_share)도 같은 이유로 같은 모양이다.
    atk_flat_derived: float = 0.0
    #endregion

    # ── 전투 스탯 ────────────────────────────────────────────────────────────
    #region
    # 원소 마스터리는 **유래별로 두 조각에 저장**하고 합계(elemental_mastery)는 파생시킨다.
    # 나누는 기준은 「무엇에서 왔는가」다 — 값의 단위가 아니다(게임에 원소 마스터리 %
    # 옵션이 없어 둘 다 실수치다).
    #
    #   em_from_flat      고정 수치로 부여된 EM. 장비·돌파·원소 공명·고정 버프.
    #   em_from_pct_share 다른 스탯의 %에서 파생된 EM 지분. 설탕 A4(EM%), 이네파·산드로네
    #                     A4(ATK%), 콜롬비나 C2·성현의 열쇠(HP%).
    #
    # 나누는 이유는 둘이다.
    #  1) 무한 루프 방지 — %-변환 버프(EM→EM, EM→피해%, EM→ATK)는 em_from_flat만 재료로
    #     읽는다. 파생 지분까지 재료로 쓰면 설탕 둘이 서로를 부풀리는 고리가 된다.
    #  2) 순환 오탐 방지 — 합계에서 지분을 빼는 방식이었을 때는 재료 쪽이 합계 필드를
    #     읽어야 했고, 그 읽기가 지분의 미결 지연 기여를 확정시켜 **값으로는 정확히
    #     상쇄되는** 관계까지 CyclicBuffError로 잡혔다(이네파 A4 + 적색 사막의 지팡이).
    #     조각을 나누면 재료 쪽이 지분 필드를 아예 건드리지 않아 간선 자체가 없다.
    # atk_flat / atk_flat_derived가 같은 이유로 이미 같은 모양이다.
    em_from_flat: float = 0.0
    em_from_pct_share: float = 0.0
    energy_recharge:   float = 1.0
    crit_rate:         float = 0.05
    crit_dmg:          float = 0.50
    healing_bonus:     float = 0.0
    #endregion

    # ── 원소별 피해 보너스 ───────────────────────────────────────────────────
    #region
    pyro_dmg_bonus:     float = 0.0
    hydro_dmg_bonus:    float = 0.0
    cryo_dmg_bonus:     float = 0.0
    electro_dmg_bonus:  float = 0.0
    anemo_dmg_bonus:    float = 0.0
    geo_dmg_bonus:      float = 0.0
    dendro_dmg_bonus:   float = 0.0
    physical_dmg_bonus: float = 0.0
    #endregion

    # ── 스킬 타입별 피해 보너스 ─────────────────────────────────────────────
    #region
    normal_atk_dmg_bonus:  float = 0.0
    charged_atk_dmg_bonus: float = 0.0
    plunging_dmg_bonus:    float = 0.0
    skill_dmg_bonus:       float = 0.0
    burst_dmg_bonus:       float = 0.0
    #endregion

    # ── 범용 피해 보너스 ────────────────────────────────────────────────────
    #region
    all_dmg_bonus:  float = 0.0
    flat_dmg_bonus: float = 0.0
    #endregion


    # 달,별 반응 기본 피해 증가
    lunar_charged_base_dmg_bonus:     float = 0.0
    lunar_bloom_base_dmg_bonus:       float = 0.0
    lunar_crystallize_base_dmg_bonus: float = 0.0
    stellar_conduct_base_dmg_bonus:   float = 0.0
    stellar_swirl_base_dmg_bonus:     float = 0.0

    # 별 반응 계수의 재료. 계수 자체는 여기 두지 않는다 — core.stellar의 함수가 만든다
    # (결과값을 담아 두면 재료가 바뀌었는데 값이 안 따라온다).
    # 파티 단위 유저 입력이며 party._ask_stellar_state가 모든 히트에 실어 준다.
    # elevation_multiplier와 같은 성격 — 버프가 아니라 로테이션 서술자다.
    stellar_recorded_hits: float = 0.0   # 기록된 얼음·번개 히트 수 (별 초전도)
    stellar_gust_level:    float = 0.0   # 별빛 돌풍 레벨 0/1/2 (별 확산)

    # ── 반응별 피해 보너스 ───────────────────────────────────────────────────
    #region
    vaporize_bonus:          float = 0.0
    melt_bonus:              float = 0.0
    overloaded_bonus:        float = 0.0
    superconduct_bonus:      float = 0.0
    electrocharged_bonus:    float = 0.0
    swirl_bonus:             float = 0.0
    shatter_bonus:           float = 0.0
    burning_bonus:           float = 0.0
    bloom_bonus:             float = 0.0
    hyperbloom_bonus:        float = 0.0
    burgeon_bonus:           float = 0.0
    aggravate_bonus:         float = 0.0
    spread_bonus:            float = 0.0
    lunar_charged_bonus:     float = 0.0
    lunar_bloom_bonus:       float = 0.0
    lunar_crystallize_bonus: float = 0.0
    stellar_conduct_bonus:   float = 0.0
    stellar_swirl_bonus:     float = 0.0
    #endregion

    # ── 반응별 치명타 스탯 ─────────────────────────────────────────────────
    #region
    vaporize_crit_rate:          float = 0.0
    vaporize_crit_dmg:           float = 0.0
    melt_crit_rate:              float = 0.0
    melt_crit_dmg:               float = 0.0
    overloaded_crit_rate:        float = 0.0
    overloaded_crit_dmg:         float = 0.0
    superconduct_crit_rate:      float = 0.0
    superconduct_crit_dmg:       float = 0.0
    electrocharged_crit_rate:    float = 0.0
    electrocharged_crit_dmg:     float = 0.0
    swirl_crit_rate:             float = 0.0
    swirl_crit_dmg:              float = 0.0
    shatter_crit_rate:           float = 0.0
    shatter_crit_dmg:            float = 0.0
    burning_crit_rate:           float = 0.0
    burning_crit_dmg:            float = 0.0
    bloom_crit_rate:             float = 0.0
    bloom_crit_dmg:              float = 0.0
    hyperbloom_crit_rate:        float = 0.0
    hyperbloom_crit_dmg:         float = 0.0
    burgeon_crit_rate:           float = 0.0
    burgeon_crit_dmg:            float = 0.0
    aggravate_crit_rate:         float = 0.0
    aggravate_crit_dmg:          float = 0.0
    spread_crit_rate:            float = 0.0
    spread_crit_dmg:             float = 0.0
    # 달반응은 캐릭터 본인의 crit_rate/crit_dmg로 치명타 판정한다. 다만 「달빛 반응의 치명타
    # 피해」만 따로 올리는 옵션이 있어(막간의 야상곡), 그 몫은 전용 필드에 담고 달반응 컨텍스트를
    # 만들 때 캐릭터 치명타 피해에 더한다(build_lunar_reaction_context).
    #
    # 히트 전역인 crit_dmg에 바로 더하면 그 캐릭터의 직접 피해(일반/스킬/폭발)까지 오염된다.
    # 반대로 「달반응 히트에만 넣기」도 불가능하다 — 달반응 반응 피해는 SkillHit이 아니라 별도
    # 피해 인스턴스이고 캐리어 히트의 스탯을 읽어 갈 뿐이다. 그래서 격변 반응과 같은 규약
    # ({접두}_crit_dmg)으로 나눠 두고 읽는 자리에서 합산한다 — _reaction_crit_dmg가 접두사
    # 표(_REACTION_PREFIX)로 골라 읽으므로 필드를 선언하는 것만으로 연결된다.
    #
    # 별 반응과 치명타 **확률** 쪽은 아직 그런 옵션을 가진 장비가 없지만, 계산식이 달반응과
    # 같아 언제든 나올 수 있는 자리다. 격변 반응이 확률/피해 짝으로 선언돼 있는 것과 맞춰
    # 미리 대칭으로 세워 둔다 — 값이 0이면 어느 경로에도 영향이 없다.
    lunar_charged_crit_rate:     float = 0.0
    lunar_charged_crit_dmg:      float = 0.0
    lunar_bloom_crit_rate:       float = 0.0
    lunar_bloom_crit_dmg:        float = 0.0
    lunar_crystallize_crit_rate: float = 0.0
    lunar_crystallize_crit_dmg:  float = 0.0
    stellar_conduct_crit_rate:   float = 0.0
    stellar_conduct_crit_dmg:    float = 0.0
    stellar_swirl_crit_rate:     float = 0.0
    stellar_swirl_crit_dmg:      float = 0.0
    #endregion

    # ── 방어력 감소 / 무시 / 배율 ──────────────────────────────────────────
    #region
    def_reduction:        float = 0.0
    def_ignore:           float = 0.0
    elevation_multiplier: float = 1.0
    #endregion

    # ── 적 원소별 내성 감소 효과 ───────────────────────────────────────────────────────
    #region
    pyro_res_reduction:     float = 0.0
    hydro_res_reduction:    float = 0.0
    cryo_res_reduction:     float = 0.0
    electro_res_reduction:  float = 0.0
    anemo_res_reduction:    float = 0.0
    geo_res_reduction:      float = 0.0
    dendro_res_reduction:   float = 0.0
    physical_res_reduction: float = 0.0
    #endregion

    # ── 비중첩 버프 장부 ────────────────────────────────────────────────────
    # 동명의 소스(성유물 세트 / 무기)가 만든 버프는 중첩되지 않는다.
    # 키: (소스 식별자, 필드명) → 그 소스가 현재 이 히트에 반영해 둔 값.
    # apply_unique_buff()가 관리하며, 히트가 새로 만들어질 때마다 자동으로 비워진다.
    _unique_buffs: dict[tuple, float] = field(
        default_factory=dict, init=False, repr=False, compare=False
    )

    # ── 기여 원장 (explain_hit 디버그용) ────────────────────────────────────
    # 가산(add())으로 들어온 기여를 (출처, 필드, delta)로 순서대로 쌓는다.
    # 기록이 켜졌을 때만 채워지며, 데미지 계산에는 전혀 관여하지 않는다.
    # (비중첩 버프의 출처는 위 _unique_buffs가 이미 갖고 있어 explain_hit이 병합해 읽는다.)
    _ledger: list = field(default_factory=list, init=False, repr=False, compare=False)

    # ── 미결 지연 기여 ──────────────────────────────────────────────────────
    # 필드명 → [(값을 계산하는 함수, 출처, note)]. 그 필드를 읽는 순간(또는 settle()에서)
    # 계산되어 평범한 가산 기여로 바뀌고 여기서 사라진다. 위쪽 「지연 기여」 주석 참고.
    _pending: dict[str, list] = field(
        default_factory=dict, init=False, repr=False, compare=False
    )
    # 비중첩 지연 기여 — 필드명 → [(값을 계산하는 함수, 출처)].
    # 확정 시점에 후보를 모두 계산한 뒤 apply_unique_buff로 넘겨 최댓값 하나만 남긴다.
    _pending_unique: dict[str, list] = field(
        default_factory=dict, init=False, repr=False, compare=False
    )
    # 지연 기여가 확정되며 값이 바뀐 필드. 정확성 가드(party.py)가 이 필드는 건너뛴다 —
    # 지연 기여는 순서 무관이 보장되므로 코어 풀에 써도 안전하기 때문이다.
    _lazy_written: set = field(
        default_factory=set, init=False, repr=False, compare=False
    )

    # ── 최종 스탯 (finalize() 이후 유효) ────────────────────────────────────
    hp_final:  float = field(default=0.0, init=False)
    atk_final: float = field(default=0.0, init=False)
    def_final: float = field(default=0.0, init=False)

    # ── 라이브 스탯 (finalize 타이밍과 무관하게 현재 누적값을 즉석 계산) ──────
    # 방식 B 버프는 *_final 대신 이 헬퍼로 읽는다 — *_final은 Phase 6에서야 채워지는데
    # 지연 기여는 그보다 앞선 Phase 5.5에 계산되기 때문이다. *_final은 히트 자신이
    # 피해를 계산할 때 쓰는 값이고, 이쪽은 '지금까지 누적된 스탯'을 즉석에서 구한다.
    def current_hp(self)  -> float: return self.hp_base  * (1.0 + self.hp_pct)  + self.hp_flat
    def current_atk(self) -> float: return self.atk_base * (1.0 + self.atk_pct) + self.atk_flat + self.atk_flat_derived
    def current_def(self) -> float: return self.def_base * (1.0 + self.def_pct) + self.def_flat

    @property
    def elemental_mastery(self) -> float:
        """캐릭터가 실제로 들고 있는 원소 마스터리 — 저장 조각 둘의 합.

        반응 계산·EM 스케일 히트·「EM의 N%를 피해에 직접 더하는」 버프가 읽는 값이다.

        **세터가 없다.** add("elemental_mastery", ...)는 AttributeError로 죽는다 — 새 기여는
        고정 수치면 em_from_flat, 다른 스탯의 %에서 파생됐으면 em_from_pct_share로
        **골라서** 넣어야 한다. 고르지 않고 합계에 넣을 수 있으면 꼬리표 규약이 새기
        때문에, 틀린 쪽을 조용히 허용하느니 컴파일하듯 막는다.

        %-변환 버프(EM→EM·EM→피해%·EM→ATK)의 재료는 이 합계가 아니라 em_from_flat이다.
        반대로 EM에 비례한 몫을 **피해에 직접 더하는** 효과(시틀라리 A4/C1, 잎을 가르는
        빛)는 재변환이 아니므로 이 합계를 그대로 읽는다.
        """
        return self.em_from_flat + self.em_from_pct_share

    def convertible_atk(self) -> float:
        """**공격력 → 공격력** 변환 버프만 읽는 공격력. 파생 지분(atk_flat_derived)은 뺀다.

        게임의 스탯은 수정자를 순서대로 접은 결과라 i번째 수정자가 i-1까지의 값만 보고,
        자기 출력이 자기 입력에 섞이지 않는다. 이 엔진은 순서 대신 지연 평가로 값을 정하므로
        (party.py 첫머리) 같은 슬롯을 읽고 쓰면 해가 없는 순환이 된다 — 그 자리를 이 접근자가
        대신한다. 얀사 운동량 측정기(자기 공격력 27% → 필드 위 캐릭터의 공격력)가 유일한 소비처다.

        공격력을 읽어 **다른** 필드에 쓰는 버프(마비카·한운·제사의 여운 등)는 순환이 아니므로
        current_atk()를 그대로 읽는다 — 실제로 들고 있는 공격력은 출처와 무관하게 전부 재료다.
        em_from_flat이 %-재변환만 막고 EM→피해는 막지 않는 것과 같은 규약이다.

        변환기가 둘 이상이면 서로의 파생 지분을 못 본다. 게임은 순서대로라면 뒤쪽이 앞쪽을
        볼 테니 근사이지만, 순서 독립성을 지키려면 이쪽이 맞다(em_from_pct_share와 같은 교환).
        현재 이 계열은 얀사 하나뿐이라 실제로 갈라지는 조합이 없다.
        """
        return self.atk_base * (1.0 + self.atk_pct) + self.atk_flat

    # ── 가산 기여 (출처 기록) ────────────────────────────────────────────────
    def add(
        self,
        field_name: str,
        value:      float | Callable[[], float],
        source:     object,
        *,
        note: str = "",
    ) -> None:
        """`hit.<field> += value` 와 수치적으로 동일하되, 기록이 켜져 있으면 출처를 원장에
        남긴다. 모든 가산 버프(캐릭터/세트/무기/공명)를 이 메서드로 통일하면 explain_hit이
        각 필드에 누가 얼마를 넣었는지 그대로 복원할 수 있다. 비중첩 버프는 apply_unique_buff
        (출처를 _unique_buffs에 이미 보관)를 그대로 쓴다.

        value에 **함수**를 넘기면 지연 기여가 된다 — 값을 지금 정하지 않고, 그 필드를 읽는
        순간 함수를 실행해 정한다. 「버퍼의 최종 스탯을 읽어서」 만드는 버프(방식 B)는 값이
        등록 시점에 확정되지 않으므로 반드시 이쪽을 쓴다. 그러면 등록 순서·파티 멤버 순서와
        무관하게 같은 결과가 나온다. 확정된 뒤에는 평범한 가산 기여와 완전히 같다(원장 포함).
        """
        if callable(value):
            global _PENDING_COUNT
            pending = object.__getattribute__(self, "_pending")
            pending.setdefault(field_name, []).append((value, source, note))
            _PENDING_COUNT += 1
            return

        # 가로채기(__getattribute__)를 우회한다 — 여기서 일반 getattr을 쓰면 지연 기여를
        # 확정하는 도중에 같은 필드를 다시 읽어 순환으로 오인된다.
        current = object.__getattribute__(self, field_name)
        object.__setattr__(self, field_name, current + value)
        if _RECORD_ENABLED and value:
            self._ledger.append(Contribution(source_label(source), field_name, value, note))

    # ── 지연 기여 확정 ──────────────────────────────────────────────────────
    def _force(self, field_name: str) -> None:
        """이 필드의 미결 지연 기여를 지금 계산해 반영한다.

        계산 도중 같은 (히트, 필드)를 다시 읽으면 값이 정해질 수 없는 순환이므로 즉시
        실패시킨다 — 단계를 나눠 순서로 통제하던 방식을 대신하는 안전망이다."""
        global _PENDING_COUNT
        pending  = object.__getattribute__(self, "_pending")
        uniques  = object.__getattribute__(self, "_pending_unique")
        entries  = pending.get(field_name)
        u_entries = uniques.get(field_name)
        if not entries and not u_entries:
            return

        key   = (id(self), field_name)
        label = f"{object.__getattribute__(self, 'name')}.{field_name}"
        if key in _RESOLVING:
            chain = " → ".join([*_RESOLVING.values(), label])
            raise CyclicBuffError(
                f"버프 의존이 순환합니다: {chain}\n"
                f"지연 기여(add에 함수 전달)는 서로의 값을 읽을 수 없습니다 — 한쪽을 "
                f"기초 스탯(방식 A)이나 고정값으로 바꾸거나, 출력 필드를 피해 쪽"
                f"(flat_dmg_bonus 등)으로 옮겨 고리를 끊으세요."
            )

        _RESOLVING[key] = label
        try:
            # 평가 도중 같은 필드에 새 지연 기여가 붙을 수도 있어 리스트가 빌 때까지 돈다.
            while entries:
                fn, source, note = entries[0]
                # 평가가 끝난 **뒤에** 목록에서 뺀다 — 평가 도중 이 필드를 다시 읽으면
                # _pending이 비어 있지 않아야 _force가 다시 불려 순환으로 잡힌다.
                value = float(fn())
                entries.pop(0)
                _PENDING_COUNT -= 1
                self.add(field_name, value, source, note=note)
                object.__getattribute__(self, "_lazy_written").add(field_name)

            # 비중첩 후보는 값을 모두 구한 뒤에 제출한다 — 최댓값 비교가 쪼개지지 않게
            # 출처별로 합산해서 한 번씩 넘긴다(apply_unique_buff의 계약).
            while u_entries:
                fn, source = u_entries[0]
                value = float(fn())
                u_entries.pop(0)
                _PENDING_COUNT -= 1
                self.apply_unique_buff(source, field_name, value)
                object.__getattribute__(self, "_lazy_written").add(field_name)
        finally:
            del _RESOLVING[key]
            if not entries:
                pending.pop(field_name, None)
            if not u_entries:
                uniques.pop(field_name, None)

    def settle(self) -> None:
        """남아 있는 미결 지연 기여를 전부 확정한다.

        읽히지 않은 필드(피해 보너스 등)에도 지연 기여가 있을 수 있으므로, 스탯 확정
        (finalize) 직전에 파티가 한 번 호출해 준다."""
        pending = object.__getattribute__(self, "_pending")
        uniques = object.__getattribute__(self, "_pending_unique")
        while pending or uniques:
            self._force(next(iter(pending or uniques)))

    # ── 읽기 가로채기 ───────────────────────────────────────────────────────
    # 미결 지연 기여가 있는 필드를 읽으면 그 자리에서 확정한다. 이것이 「단계」를 대신한다 —
    # 값이 필요해진 순간 계산되므로 누가 먼저 실행됐는지가 결과를 바꾸지 않는다.
    #
    # 지연 기여가 하나도 없으면(_PENDING_COUNT == 0) 전역 하나만 보고 즉시 빠져나간다.
    # 내부 필드(_로 시작)는 지연 대상이 아니므로 검사에서 제외해 재귀를 막는다.
    def __getattribute__(self, name: str):
        if _PENDING_COUNT and name[0] != "_":
            d = object.__getattribute__(self, "__dict__")
            pending = d.get("_pending")
            uniques = d.get("_pending_unique")
            if (pending and name in pending) or (uniques and name in uniques):
                object.__getattribute__(self, "_force")(name)
        return object.__getattribute__(self, name)

    # ── 비중첩 버프 (동명 소스는 중첩되지 않음) ─────────────────────────────
    def apply_unique_buff(
        self,
        source:     object,
        field_name: str,
        value:      float | Callable[[], float],
    ) -> None:
        """동명의 소스가 만드는 버프를 누산한다 — 필드별로 **최댓값 하나만** 남는다.

        같은 성유물 세트/무기를 여러 명이 착용해도 파티 전체 버프는 중첩되지 않는 게임
        사양을 구현한다. 세트 인스턴스 단위로 두 번째 착용자를 통째로 무시하면 안 된다
        (예: 잿더미성 두루마리는 착용자마다 반응 참여 원소가 다르므로, 원소 필드별로
        따로 최댓값을 잡아야 불/얼음/바위가 각각 올바르게 들어간다).

        기여자마다 값을 그대로 제출하면 되고, 이미 반영된 값과의 차액만 필드에 누산하므로
        제출 순서와 무관하게 결과가 같다. 착용자 본인에게만 들어가는 효과(대부분의 2세트,
        자기 버프)는 정상적으로 중첩되므로 그냥 `+=`를 쓴다.

        source에는 버프를 만든 주체를 넣는다 — 성유물은 (ArtifactSet, 세트 수),
        무기는 무기 클래스 등. 한 필드에 같은 source로 여러 번 나눠 제출하면 최댓값
        비교가 쪼개지므로, 조건부 증가분까지 합산한 **최종 값을 한 번에** 제출한다.
        내성 감소처럼 음수로 표현되는 효과도 지원한다(같은 키에 부호를 섞지는 말 것).

        value에 **함수**를 넘기면 지연 기여가 된다(add와 동일). 최댓값 비교는 값이 있어야
        하므로, 후보들을 모아 두었다가 그 필드를 읽는 순간 전부 계산한 뒤 비교한다 —
        스탯에서 파생되는 비중첩 버프(바위산을 맴도는 노래의 파티 원소 피해)가 이쪽이다.
        """
        if callable(value):
            global _PENDING_COUNT
            uniques = object.__getattribute__(self, "_pending_unique")
            uniques.setdefault(field_name, []).append((value, source))
            _PENDING_COUNT += 1
            return

        slot = (source, field_name)
        prev = self._unique_buffs.get(slot, 0.0)
        if abs(value) <= abs(prev):
            return
        # add()와 같은 이유로 가로채기를 우회한다 — 차액을 누산할 뿐이라 미결 지연 기여를
        # 여기서 확정할 이유가 없다(그쪽은 자기 시점에 따로 더해진다).
        current = object.__getattribute__(self, field_name)
        object.__setattr__(self, field_name, current + (value - prev))
        self._unique_buffs[slot] = value

    def buff_value(self, source: object, field_name: str) -> float:
        """해당 소스가 이 필드에 이미 반영해 둔 비중첩 버프 값. 미적용이면 0.0.
        고정값 효과의 중복 질문을 생략할 때 쓴다."""
        return self._unique_buffs.get((source, field_name), 0.0)

    def finalize_core_stats(self) -> None:
        self.hp_final  = self.current_hp()
        self.atk_final = self.current_atk()
        self.def_final = self.current_def()

    def finalize_damage_multipliers(self) -> None:
        # Phase 6: 모든 기여(Phase 2~5.5)가 끝난 뒤 코어 스탯을 단 한 번 확정한다.
        self.finalize_core_stats()


# 물리를 제외한 7원소 피해 보너스 필드 (아래 두 접근자의 단일 출처)
_ALL_ELEMENTAL_DMG_FIELDS = (
    "pyro_dmg_bonus", "hydro_dmg_bonus", "cryo_dmg_bonus", "electro_dmg_bonus",
    "anemo_dmg_bonus", "geo_dmg_bonus", "dendro_dmg_bonus",
)


def add_all_elemental_dmg_bonus(hit: SkillHit, value: float, source: object = "(미계측)") -> None:
    """7원소 피해 보너스를 모두 동일하게 증가시킨다 (물리 제외)."""
    for name in _ALL_ELEMENTAL_DMG_FIELDS:
        hit.add(name, value, source)


def add_all_elemental_dmg_bonus_unique(
    hit: SkillHit, source: object, value: float | Callable[[], float]
) -> None:
    """7원소 피해 보너스를 비중첩으로 증가시킨다 (물리 제외).
    동명의 소스가 여러 번 제출해도 원소별로 최댓값 하나만 남는다 — SkillHit.apply_unique_buff 참고.
    value에 함수를 넘기면 지연 기여가 된다(스탯에서 파생되는 비중첩 버프)."""
    for name in _ALL_ELEMENTAL_DMG_FIELDS:
        hit.apply_unique_buff(source, name, value)


# ── enum → SkillHit 필드 접두사 매핑 (아래 접근자들의 단일 출처) ──────────
# 새 원소/반응/스킬타입 추가 시 이 표만 갱신하면 관련 접근자가 모두 따라온다.
_ELEMENT_PREFIX: dict[Element, str] = {
    Element.PYRO:     "pyro",
    Element.HYDRO:    "hydro",
    Element.CRYO:     "cryo",
    Element.ELECTRO:  "electro",
    Element.ANEMO:    "anemo",
    Element.GEO:      "geo",
    Element.DENDRO:   "dendro",
    Element.PHYSICAL: "physical",
}

_SKILL_PREFIX: dict[SkillType, str] = {
    SkillType.NORMAL_ATK:  "normal_atk",
    SkillType.CHARGED_ATK: "charged_atk",
    SkillType.PLUNGING:    "plunging",
    SkillType.SKILL:       "skill",
    SkillType.BURST:       "burst",
}

_REACTION_PREFIX: dict[ReactionType, str] = {
    ReactionType.VAPORIZE:          "vaporize",
    ReactionType.MELT:              "melt",
    ReactionType.OVERLOADED:        "overloaded",
    ReactionType.SUPERCONDUCT:      "superconduct",
    ReactionType.ELECTROCHARGED:    "electrocharged",
    ReactionType.SWIRL:             "swirl",
    ReactionType.SHATTER:           "shatter",
    ReactionType.BURNING:           "burning",
    ReactionType.BLOOM:             "bloom",
    ReactionType.HYPERBLOOM:        "hyperbloom",
    ReactionType.BURGEON:           "burgeon",
    ReactionType.AGGRAVATE:         "aggravate",
    ReactionType.SPREAD:            "spread",
    ReactionType.LUNAR_CHARGED:     "lunar_charged",
    ReactionType.LUNAR_BLOOM:       "lunar_bloom",
    ReactionType.LUNAR_CRYSTALLIZE: "lunar_crystallize",
    ReactionType.STELLAR_CONDUCT:   "stellar_conduct",
    ReactionType.STELLAR_SWIRL:     "stellar_swirl",
}

# StatType → 누산 대상 SkillHit 필드명
_STAT_FIELD: dict[StatType, str] = {
    StatType.HP:                "hp_flat",
    StatType.ATK:               "atk_flat",
    StatType.DEF:               "def_flat",
    StatType.HP_PCT:            "hp_pct",
    StatType.ATK_PCT:           "atk_pct",
    StatType.DEF_PCT:           "def_pct",
    # 장비·돌파가 주는 실수치 EM은 전부 '변환 재료가 되는' 쪽이다.
    StatType.ELEMENTAL_MASTERY: "em_from_flat",
    StatType.ENERGY_RECHARGE:   "energy_recharge",
    StatType.CRIT_RATE:         "crit_rate",
    StatType.CRIT_DMG:          "crit_dmg",
    StatType.HEALING_BONUS:     "healing_bonus",
    StatType.PYRO_DMG:          "pyro_dmg_bonus",
    StatType.HYDRO_DMG:         "hydro_dmg_bonus",
    StatType.CRYO_DMG:          "cryo_dmg_bonus",
    StatType.ELECTRO_DMG:       "electro_dmg_bonus",
    StatType.ANEMO_DMG:         "anemo_dmg_bonus",
    StatType.GEO_DMG:           "geo_dmg_bonus",
    StatType.DENDRO_DMG:        "dendro_dmg_bonus",
    StatType.PHYSICAL_DMG:      "physical_dmg_bonus",
}


def apply_stat(hit: SkillHit, stat_type: StatType, value: float, source: object = "(미계측)",
               *, note: str = "") -> None:
    """StatType 하나를 SkillHit의 적절한 필드에 누산한다. Artifact와 Weapon이 공유."""
    attr = _STAT_FIELD.get(stat_type)
    if attr is not None:
        hit.add(attr, value, source, note=note)


# ── 어떤 필드를 읽을지 고르는 규칙 ───────────────────────────────────────────
# 히트마다 실제로 계산에 들어가는 필드는 한 줌뿐이다 — 냉기 히트는 cryo_dmg_bonus만,
# 폭발이면 burst_dmg_bonus만 읽는다. 그 규칙에 이름을 붙여 두면 계산(_element_dmg_bonus
# 등)과 설명(damage_input_fields)이 같은 것을 읽는다. 화면이 규칙을 베껴 들고 있으면
# 원소나 스킬 종류가 늘 때마다 조용히 어긋난다.
def element_dmg_field(element: Element) -> str | None:
    prefix = _ELEMENT_PREFIX.get(element)
    return f"{prefix}_dmg_bonus" if prefix else None


def skill_dmg_field(skill_type: SkillType) -> str | None:
    prefix = _SKILL_PREFIX.get(skill_type)
    return f"{prefix}_dmg_bonus" if prefix else None


def reaction_bonus_field(reaction_type: ReactionType) -> str | None:
    prefix = _REACTION_PREFIX.get(reaction_type)
    return f"{prefix}_bonus" if prefix else None


def celestial_base_dmg_bonus_field(reaction_type: ReactionType) -> str | None:
    """달·별 반응의 **기초 피해 증가** 필드 이름. 반응별로 나뉘어 있어 고를 자리가 필요하다.

    그 이름을 여러 곳에 손으로 적으면 한쪽만 고쳐져 「설명 화면에 적용됨으로 떴는데 공식에는
    안 곱해지는」 사고가 난다 — 컨텍스트 빌더 셋과 {lunar,stellar}_reaction_input_fields·
    damage_input_fields가 모두 이 함수를 읽는다.

    달·별이 아닌 반응(증발·격변 등)은 None이다. 그쪽 _calc_*가 이 값을 아예 읽지 않는다.
    """
    if reaction_type not in _CELESTIAL_REACTIONS:
        return None
    return f"{_REACTION_PREFIX[reaction_type]}_base_dmg_bonus"


def _celestial_base_dmg_bonus(hit: SkillHit, reaction_type: ReactionType) -> float:
    """공식의 (1 + %기초 피해 증가) 자리에 들어갈 값. 그 반응 전용 필드를 골라 읽는다."""
    field = celestial_base_dmg_bonus_field(reaction_type)
    return getattr(hit, field) if field else 0.0


def element_res_reduction_field(element: Element) -> str:
    return f"{_ELEMENT_PREFIX.get(element, 'physical')}_res_reduction"


def _element_dmg_bonus(hit: SkillHit, element: Element) -> float:
    field = element_dmg_field(element)
    return getattr(hit, field) if field else 0.0


def _skill_dmg_bonus(hit: SkillHit, skill_type: SkillType) -> float:
    field = skill_dmg_field(skill_type)
    return getattr(hit, field) if field else 0.0


def _enemy_resistance(hit: SkillHit, enemy: Enemy, element: Element) -> float:
    prefix = _ELEMENT_PREFIX.get(element, "physical")
    return getattr(enemy, f"{prefix}_res") + getattr(hit, f"{prefix}_res_reduction")


def _reaction_bonus(hit: SkillHit, reaction_type: ReactionType) -> float:
    field = reaction_bonus_field(reaction_type)
    return getattr(hit, field) if field else 0.0


# 달반응은 반응 전용 치명타 필드가 없다(게임에 해당 옵션이 존재하지 않음) — 기본값 0.0.
def _reaction_crit_rate(hit: SkillHit, reaction_type: ReactionType) -> float:
    prefix = _REACTION_PREFIX.get(reaction_type)
    return getattr(hit, f"{prefix}_crit_rate", 0.0) if prefix else 0.0


def _reaction_crit_dmg(hit: SkillHit, reaction_type: ReactionType) -> float:
    prefix = _REACTION_PREFIX.get(reaction_type)
    return getattr(hit, f"{prefix}_crit_dmg", 0.0) if prefix else 0.0


def _celestial_crit_fields(reaction_type: ReactionType) -> frozenset[str]:
    """그 달·별 반응의 **반응 전용 치명타** 필드 짝. 설명 화면의 '적용됨' 판정용이다.

    이름을 손으로 적는 곳을 만들지 않으려고 접두사 표에서 유도한다 — 컨텍스트 빌더가
    _reaction_crit_rate/_reaction_crit_dmg로 읽는 것과 같은 출처다."""
    prefix = _REACTION_PREFIX.get(reaction_type)
    if not prefix:
        return frozenset()
    return frozenset({f"{prefix}_crit_rate", f"{prefix}_crit_dmg"})


# ── 반응 배율표 ──────────────────────────────────────────────────────────
# 대부분 반응별 고정값. 증발/융해는 트리거 원소, 달반응은 dmg_type에 따라 갈린다.
_REACTION_MULT_CONST: dict[ReactionType, float] = {
    ReactionType.BURNING:        0.25,
    ReactionType.SWIRL:          0.6,
    ReactionType.AGGRAVATE:      1.15,
    ReactionType.SPREAD:         1.25,
    ReactionType.SUPERCONDUCT:   1.5,
    ReactionType.ELECTROCHARGED: 2.0,
    ReactionType.BLOOM:          2.0,
    ReactionType.OVERLOADED:     2.75,
    ReactionType.BURGEON:        3.0,
    ReactionType.HYPERBLOOM:     3.0,
    ReactionType.SHATTER:        3.0,
}

# 달반응: 직접 피해(LUNAR_DIRECT) / 반응 피해(LUNAR_REACTION)에 따라 배율이 다르다.
_LUNAR_MULT: dict[ReactionType, dict[DmgType, float]] = {
    ReactionType.LUNAR_CHARGED:     {DmgType.LUNAR_DIRECT: 3.0, DmgType.LUNAR_REACTION: 1.8},
    ReactionType.LUNAR_BLOOM:       {DmgType.LUNAR_DIRECT: 1.0, DmgType.LUNAR_REACTION: 0.0},
    ReactionType.LUNAR_CRYSTALLIZE: {DmgType.LUNAR_DIRECT: 1.8, DmgType.LUNAR_REACTION: 0.96},
}

# 달반응 3종 — dmg_type이 두 자리(LUNAR_DIRECT/LUNAR_REACTION) 모두 유효한 유일한 반응.
_LUNAR_REACTIONS = frozenset(_LUNAR_MULT)

# 달반응 3종의 「반응 전용 치명타 피해」 필드. 접두사 표에서 유도하므로 이름을 손으로
# 적는 곳이 없다 — 반응이 늘면 여기가 저절로 따라온다.
_ALL_LUNAR_CRIT_DMG_FIELDS: tuple[str, ...] = tuple(
    f"{_REACTION_PREFIX[r]}_crit_dmg" for r in sorted(_LUNAR_REACTIONS, key=lambda r: r.name)
)


def add_all_lunar_crit_dmg(
    hit: SkillHit, value: float, source: object = "(미계측)", *, note: str = ""
) -> None:
    """달반응 3종(달감전·달개화·달결정)의 반응 전용 치명타 피해를 모두 증가시킨다.

    「달빛 반응의 치명타 피해가 증가한다」는 문구가 반응을 가리지 않을 때 쓴다. 특정 달반응
    하나만 올리는 효과는 이 헬퍼가 아니라 그 반응의 필드를 직접 짚는다."""
    for name in _ALL_LUNAR_CRIT_DMG_FIELDS:
        hit.add(name, value, source, note=note)

# 별 반응 2종. 달반응처럼 dmg_type 두 자리(STELLAR_DIRECT/STELLAR_REACTION)가 모두 유효하다.
#
# **배율 상수표가 없다.** 별 반응 계수는 런타임 상태(기록 히트 수·별빛 돌풍 레벨)로 변하므로
# core.stellar의 함수가 유일한 출처다(_reaction_multiplier의 별 반응 분기). 여기에 표를
# 하나 더 두면 같은 계수가 두 군데 적혀 갈라진다.
_STELLAR_REACTIONS = frozenset({
    ReactionType.STELLAR_CONDUCT,
    ReactionType.STELLAR_SWIRL,
})

# 달·별 반응 — dmg_type을 반응 타입만으로 유도할 수 없는 계열. 두 자리가 모두 유효하다.
_CELESTIAL_REACTIONS = _LUNAR_REACTIONS | _STELLAR_REACTIONS

# 계열 → 그 계열에서 유효한 (직접 피해, 반응 피해) dmg_type 짝.
_CELESTIAL_DMG_TYPES: dict[ReactionType, tuple[DmgType, DmgType]] = {
    **{r: (DmgType.LUNAR_DIRECT,   DmgType.LUNAR_REACTION)   for r in _LUNAR_REACTIONS},
    **{r: (DmgType.STELLAR_DIRECT, DmgType.STELLAR_REACTION) for r in _STELLAR_REACTIONS},
}

# reaction_type → dmg_type. 달반응을 제외하면 반응 타입이 계산식을 유일하게 결정한다.
_REACTION_DMG_TYPE: dict[ReactionType, DmgType] = {
    ReactionType.NONE:           DmgType.NONE,
    ReactionType.VAPORIZE:       DmgType.AMPLIFY,
    ReactionType.MELT:           DmgType.AMPLIFY,
    ReactionType.AGGRAVATE:      DmgType.CATALYZE,
    ReactionType.SPREAD:         DmgType.CATALYZE,
    ReactionType.OVERLOADED:     DmgType.TRANSFORMATIVE,
    ReactionType.SUPERCONDUCT:   DmgType.TRANSFORMATIVE,
    ReactionType.ELECTROCHARGED: DmgType.TRANSFORMATIVE,
    ReactionType.SWIRL:          DmgType.TRANSFORMATIVE,
    ReactionType.SHATTER:        DmgType.TRANSFORMATIVE,
    ReactionType.BURNING:        DmgType.TRANSFORMATIVE,
    ReactionType.BLOOM:          DmgType.TRANSFORMATIVE,
    ReactionType.HYPERBLOOM:     DmgType.TRANSFORMATIVE,
    ReactionType.BURGEON:        DmgType.TRANSFORMATIVE,
}


def resolve_reaction(
    hit:           SkillHit,
    reaction_type: ReactionType | None = None,
    dmg_type:      DmgType | None      = None,
) -> tuple[ReactionType, DmgType]:
    """히트의 내재 반응과 호출자의 상황적 반응을 합쳐 (reaction_type, dmg_type)을 확정한다.

    · 히트가 내재 반응을 선언했으면(달감전 피해 등) 그것을 쓴다 — 전역 스위치로 덮이지 않는다.
    · 선언하지 않은 히트(대부분의 평타/스킬)에만 호출자가 넘긴 상황적 반응이 적용된다.
    · dmg_type이 없으면 _REACTION_DMG_TYPE에서 유도하고, 달·별 반응은 유도 불가라 명시를 요구한다.
    """
    if hit.reaction_type is not ReactionType.NONE:
        rt, dt = hit.reaction_type, hit.dmg_type
    else:
        rt = reaction_type if reaction_type is not None else ReactionType.NONE
        dt = dmg_type

    if dt is None:
        if rt in _CELESTIAL_REACTIONS:
            direct, reaction = _CELESTIAL_DMG_TYPES[rt]
            family = "달반응" if rt in _LUNAR_REACTIONS else "별 반응"
            raise ValueError(
                f"{family}('{rt.value}')은 dmg_type을 유도할 수 없습니다. "
                f"직접 피해는 DmgType.{direct.name}, 반응 피해는 DmgType.{reaction.name}을 "
                f"히트에 명시하세요 (SkillHit(..., reaction_type=..., dmg_type=...))."
            )
        try:
            dt = _REACTION_DMG_TYPE[rt]
        except KeyError:
            raise ValueError(f"dmg_type을 유도할 수 없는 reaction_type입니다: {rt!r}") from None
    else:
        _validate_pair(rt, dt)

    return rt, dt


def _validate_pair(reaction_type: ReactionType, dmg_type: DmgType) -> None:
    """(반응, 계산식) 짝이 유효한지 확인한다 — 잘못된 조합은 조용히 오답을 내므로 즉시 실패시킨다."""
    if reaction_type in _CELESTIAL_REACTIONS:
        allowed = _CELESTIAL_DMG_TYPES[reaction_type]
        if dmg_type not in allowed:
            family = "달반응" if reaction_type in _LUNAR_REACTIONS else "별 반응"
            names = " 또는 ".join(dt.name for dt in allowed)
            raise ValueError(
                f"{family}('{reaction_type.value}')의 dmg_type은 {names}이어야 합니다. "
                f"(입력: {dmg_type!r})"
            )
        return

    expected = _REACTION_DMG_TYPE.get(reaction_type)
    if expected is not None and dmg_type is not expected:
        raise ValueError(
            f"'{reaction_type.value}' 반응의 dmg_type은 {expected!r}여야 합니다. "
            f"(입력: {dmg_type!r})"
        )


# 원소 마스터리의 **원장 필드** — 합계 elemental_mastery는 파생 프로퍼티라 기여가 기록되지
# 않는다. 설명 화면이 「이 피해가 실제로 읽는 필드」를 셀 때는 저장 조각 둘을 넣어야 한다.
_EM_LEDGER_FIELDS = frozenset({"em_from_flat", "em_from_pct_share"})


def _add_stat_field(fields: set[str], attr: str) -> None:
    """설명용 필드 집합에 스탯 하나를 넣는다. 파생 스탯은 원장 필드로 펼친다."""
    if attr == "elemental_mastery":
        fields |= _EM_LEDGER_FIELDS
    else:
        fields.add(attr)


# ScalingStat → 히트에서 읽을 최종 스탯 필드명
_SCALING_STAT_ATTR: dict[ScalingStat, str] = {
    ScalingStat.ATK: "atk_final",
    ScalingStat.HP:  "hp_final",
    ScalingStat.DEF: "def_final",
    ScalingStat.EM:  "elemental_mastery",
}


def _reaction_multiplier(
    hit:           SkillHit,
    reaction_type: ReactionType,
    element:       Element,
    dmg_type:      DmgType,
) -> float:
    """이 (반응, 피해 계열) 조합의 반응 배율.

    hit을 받는 것은 **별 반응 때문**이다 — 별 반응 계수만 상수가 아니라 런타임 상태로
    변하고(기록 히트 수·별빛 돌풍 레벨), 그 재료를 나르는 것이 히트다. 나머지 반응은
    hit을 보지 않는다.
    """
    if reaction_type in _REACTION_MULT_CONST:
        return _REACTION_MULT_CONST[reaction_type]
    if reaction_type == ReactionType.VAPORIZE:
        return 1.5 if element == Element.PYRO else 2.0
    if reaction_type == ReactionType.MELT:
        return 2.0 if element == Element.PYRO else 1.5
    if reaction_type in _LUNAR_MULT:
        return _LUNAR_MULT[reaction_type].get(dmg_type, 1.0)
    if reaction_type in _STELLAR_REACTIONS:
        # 상수표가 아니라 함수다 — core.stellar가 계수의 유일한 출처다.
        return stellar_multiplier(
            reaction_type, dmg_type,
            recorded_hits = hit.stellar_recorded_hits,
            gust_level    = hit.stellar_gust_level,
        )
    return 1.0


def build_damage_context(
    hit:   SkillHit,
    enemy: Enemy,
    *,
    reaction_type: ReactionType | None = None,
    dmg_type:      DmgType | None      = None,
    char_level:    int                 = 90,
) -> DamageContext:
    """reaction_type/dmg_type은 히트가 내재 반응을 선언하지 않은 경우에만 적용되는
    '상황적' 반응이다(증발 평타 등). 확정 규칙은 resolve_reaction 참고."""
    element = hit.element if hit.element is not None else Element.PHYSICAL

    reaction_type, dmg_type = resolve_reaction(hit, reaction_type, dmg_type)

    reaction_multiplier = _reaction_multiplier(hit, reaction_type, element, dmg_type)

    if hit.stat_fn is not None:
        stat_value = hit.stat_fn(hit)
    else:
        stat_value = getattr(hit, _SCALING_STAT_ATTR[hit.scaling_stat])

    total_dmg_bonus = (
        _element_dmg_bonus(hit, element)
        + _skill_dmg_bonus(hit, hit.skill_type)
        + hit.all_dmg_bonus
    )

    return DamageContext(
        stat_value               = stat_value,
        coeff                    = hit.coeff,
        dmg_type                 = dmg_type,
        coeff_amp                = hit.coeff_amp,
        flat_dmg_bonus           = hit.flat_dmg_bonus,
        dmg_bonus                = total_dmg_bonus,
        crit_rate                = hit.crit_rate,
        crit_dmg                 = hit.crit_dmg,
        char_level               = char_level,
        enemy_level              = enemy.level,
        enemy_resistance         = _enemy_resistance(hit, enemy, element),
        def_reduction            = hit.def_reduction,
        def_ignore               = hit.def_ignore,
        elemental_mastery        = hit.elemental_mastery,
        reaction_multiplier      = reaction_multiplier,
        reaction_bonus           = _reaction_bonus(hit, reaction_type),
        # 달·별 공용 슬롯 — 그 반응 전용 필드를 골라 담는다(_celestial_base_dmg_bonus).
        celestial_base_dmg_bonus = _celestial_base_dmg_bonus(hit, reaction_type),
        elevation_multiplier     = hit.elevation_multiplier,
        reaction_crit_rate       = _reaction_crit_rate(hit, reaction_type),
        reaction_crit_dmg        = _reaction_crit_dmg(hit, reaction_type),
    )


def build_transformative_context(
    hit:        SkillHit,
    enemy:      Enemy,
    *,
    reaction:   ReactionType,
    element:    Element,
    char_level: int = 90,
) -> DamageContext:
    """격변 반응 1회의 피해 컨텍스트. hit은 **스탯 캐리어**일 뿐 때리는 히트가 아니다.

    격변은 트리거한 캐릭터의 EM·레벨·반응 보너스만으로 정해지는 별도의 피해 인스턴스다
    — 계수도, 스탯 스케일도, %피해 보너스도, 방어력 배율도 타지 않는다(_calc_transformative).
    그래서 build_damage_context와 달리 캐리어 히트에서 **반응에 관계된 필드만** 골라 읽는다.
    히트마다 부르는 것이 아니라 캐릭터마다 한 번 부르고, 캐리어로는 그 캐릭터의 히트 아무
    것이나 넘기면 된다(EM·반응 보너스는 히트에 걸린 버프가 아니라 캐릭터의 것이다).

    element는 **피해 원소**이며 반응이 정한다 — 과부하는 트리거가 번개든 불이든 불 내성을
    탄다. 캐리어 히트의 원소가 아니다. 확산만 확산된 원소가 그때그때 들어온다.
    후보와 피해 원소는 core.reaction.transformative_candidates가 유도한다.
    """
    return DamageContext(
        # 격변은 계수도 스탯도 읽지 않는다. 0은 '없음'이 아니라 '이 경로가 쓰지 않는
        # 자리'라는 뜻이다 — DamageContext에 기본값이 없어서 채울 뿐이다.
        stat_value = 0.0,
        coeff      = 0.0,
        dmg_type   = DmgType.TRANSFORMATIVE,

        # 캐리어 히트의 flat_dmg_bonus는 **직접 피해용**이라 여기로 넘기면 안 된다.
        # (시틀라리 C1은 다른 캐릭터의 전 히트에 EM×200%를 얹는데 그 효과는 일반/강/낙하/
        #  스킬/폭발 한정이고, 제사의 여운 4세트는 아예 일반 공격 전용이다. 그대로 넘기면
        #  격변 피해가 조용히 부풀려진다.) 격변에 더해지는 고정 피해가 실제로 생기면
        #  그때 전용 필드를 신설한다 — damage_input_fields도 이 0에 맞춰져 있다.
        flat_dmg_bonus = 0.0,

        elemental_mastery   = hit.elemental_mastery,
        reaction_multiplier = _REACTION_MULT_CONST[reaction],
        reaction_bonus      = _reaction_bonus(hit, reaction),
        reaction_crit_rate  = _reaction_crit_rate(hit, reaction),
        reaction_crit_dmg   = _reaction_crit_dmg(hit, reaction),

        char_level = char_level,
        # 적 기본 내성은 enemy에서, 내성 **감소**는 캐리어 히트에서 온다 — 후자는 트리거
        # 캐릭터가 받은 버프라 캐리어에서 읽는 것이 맞다.
        enemy_resistance = _enemy_resistance(hit, enemy, element),
        # enemy_level은 넘기지 않는다 — 격변은 defense_mult를 부르지 않는다(방어력 무시).
        # coeff_amp·dmg_bonus·crit_rate/crit_dmg·def_*·lunar_*·elevation도 같은 이유로 없다.
    )


def build_lunar_reaction_context(
    hit:        SkillHit,
    enemy:      Enemy,
    *,
    reaction:   ReactionType,
    element:    Element,
    char_level: int = 90,
) -> DamageContext:
    """달반응 **반응 피해** 1회의 컨텍스트. hit은 격변과 같이 **스탯 캐리어**다.

    build_transformative_context와 형제다 — 히트가 아니라 별도의 피해 인스턴스이고,
    계수도 스탯 스케일도 %피해 보너스도 방어력 배율도 타지 않는다(_calc_lunar_reaction).
    캐릭터마다 한 번 부르고, 캐리어로는 그 캐릭터의 히트 아무 것이나 넘기면 된다.

    격변과 다른 점이 둘이다.
      · 달반응은 반응 전용 치명타가 아니라 **캐릭터 치명타로 크리가 터진다** — 그래서
        crit_rate/crit_dmg를 캐리어에서 읽는다(달반응에는 반응 전용 치명타 옵션이 없다).
      · 기초 피해 증가(그 반응 전용 필드)와 elevation_multiplier를 읽는다.

    호출자는 이 함수를 **파티원마다** 부르고 결과를 가중합한다(core.party_reaction).
    element는 피해 원소이며 반응이 정한다 — core.reaction._LUNAR_RULES가 답을 갖고 있다.
    """
    return DamageContext(
        # 계수도 스탯도 읽지 않는다. 0은 '없음'이 아니라 '이 경로가 쓰지 않는 자리'다.
        stat_value = 0.0,
        coeff      = 0.0,
        dmg_type   = DmgType.LUNAR_REACTION,

        # 캐리어의 flat_dmg_bonus는 직접 피해용이다 — _calc_lunar_reaction도 읽지 않는다
        # (build_transformative_context의 같은 자리와 같은 이유).
        flat_dmg_bonus = 0.0,

        elemental_mastery   = hit.elemental_mastery,
        reaction_multiplier = _LUNAR_MULT[reaction][DmgType.LUNAR_REACTION],
        reaction_bonus      = _reaction_bonus(hit, reaction),

        # 달·별 공용 슬롯에 이 반응 전용 필드를 담는다 — 별 반응 빌더와 같은 규약.
        celestial_base_dmg_bonus = _celestial_base_dmg_bonus(hit, reaction),
        elevation_multiplier     = hit.elevation_multiplier,

        # 달반응은 캐릭터 치명타를 쓴다 — 격변과 갈리는 자리다.
        crit_rate = hit.crit_rate,
        crit_dmg  = hit.crit_dmg,
        # 「달빛 반응의 치명타 피해」처럼 그 반응에만 붙는 몫(막간의 야상곡)은 전용 슬롯으로
        # 따로 넘기고 _calc_lunar_reaction이 캐릭터 치명타에 더한다 — build_damage_context와
        # 같은 규약이다. 반응별 필드라 달감전만 올리는 버프가 달개화에 새지 않는다.
        reaction_crit_rate = _reaction_crit_rate(hit, reaction),
        reaction_crit_dmg  = _reaction_crit_dmg(hit, reaction),

        char_level = char_level,
        # 적 기본 내성은 enemy에서, 내성 **감소**는 캐리어(= 트리거 캐릭터가 받은 버프)에서.
        enemy_resistance = _enemy_resistance(hit, enemy, element),
        # enemy_level·coeff_amp·dmg_bonus·def_*는 없다 — 이 경로가 읽지 않는다.
    )


def lunar_reaction_input_fields(
    reaction: ReactionType,
    element:  Element,
) -> frozenset[str]:
    """달반응 반응 피해 1회가 캐리어 히트에서 **실제로 읽는** 필드.
    build_lunar_reaction_context와 짝이다 — 한쪽만 고치면 화면이 '적용됨'으로 띄운 항목이
    실제로는 안 곱해진다.

    damage_input_fields의 LUNAR_REACTION 분기를 돌려 쓰지 않는다.
    transformative_input_fields가 적어 둔 이유와 같다 — resolve_reaction(hit, ...)을 부르므로
    캐리어의 내재 반응(콜롬비나의 달감전 직접 피해)이 설명하려는 반응을 덮어쓰고, 피해 원소도
    캐리어에서 유도해 내성 필드가 어긋난다.
    """
    # 계수·스탯·coeff_amp·%피해 보너스·flat_dmg_bonus·방어력 필드는 일부러 없다.
    fields = {
        element_res_reduction_field(element),
        *_EM_LEDGER_FIELDS,
        "elevation_multiplier",
        # 격변과 달리 캐릭터 치명타를 쓴다.
        "crit_rate", "crit_dmg",
    }

    # 「달빛 반응의 치명타 피해」 전용 몫 — 반응별 필드라 여기서도 반응으로 골라야
    # 달감전만 올리는 버프가 달개화 설명에 적용됨으로 뜨지 않는다.
    fields |= _celestial_crit_fields(reaction)

    # 기초 피해 증가는 그 반응 전용 필드 하나다 — 이름을 손으로 적으면 「달감전만」 올리는
    # 버프(이네파 Moonsign)가 달개화 설명에 적용됨으로 뜬다.
    base = celestial_base_dmg_bonus_field(reaction)
    if base:
        fields.add(base)

    bonus = reaction_bonus_field(reaction)
    if bonus:
        fields.add(bonus)

    return frozenset(fields)


def build_stellar_reaction_context(
    hit:        SkillHit,
    enemy:      Enemy,
    *,
    reaction:   ReactionType,
    element:    Element,
    char_level: int = 90,
) -> DamageContext:
    """별 반응 **반응 피해** 1회의 컨텍스트. build_lunar_reaction_context의 쌍둥이다.

    공식이 달반응과 같으므로(_calc_lunar_reaction) 이 함수가 다르게 하는 것은 하나뿐이다 —
    반응 배율을 상수표가 아니라 core.stellar의 함수에서 가져온다. 별빛 돌풍 레벨로 변하는
    값이라 표에 적어 둘 수 없다. 기초 피해 증가는 달반응도 반응별 필드라 같은 규칙을 탄다
    (celestial_base_dmg_bonus_field).

    현재 이 경로를 타는 반응은 별 확산뿐이다 — 별 초전도는 반응 피해가 없다
    (stellar.stellar_has_reaction_damage). 그래도 반응을 인자로 받는 이유는, 계수와 필드를
    반응에서 유도하는 구조를 유지해 두면 나중에 반응 피해가 있는 별 반응이 늘어도
    이 함수를 고칠 일이 없기 때문이다.
    """
    return DamageContext(
        # 계수도 스탯도 읽지 않는다 — build_lunar_reaction_context와 같은 규약.
        stat_value = 0.0,
        coeff      = 0.0,
        dmg_type   = DmgType.STELLAR_REACTION,
        flat_dmg_bonus = 0.0,

        elemental_mastery   = hit.elemental_mastery,
        reaction_multiplier = stellar_multiplier(
            reaction, DmgType.STELLAR_REACTION,
            recorded_hits = hit.stellar_recorded_hits,
            gust_level    = hit.stellar_gust_level,
        ),
        reaction_bonus      = _reaction_bonus(hit, reaction),

        # 달·별 공용 슬롯에 이 반응 전용 필드를 담는다 — 달반응 빌더와 같은 규약.
        celestial_base_dmg_bonus = _celestial_base_dmg_bonus(hit, reaction),
        elevation_multiplier     = hit.elevation_multiplier,

        # 별 반응도 캐릭터 치명타를 쓴다. 반응 전용 몫은 달반응과 같은 규약으로 전용 슬롯에
        # 담아 넘긴다 — 아직 별 반응 전용 치명타를 주는 장비는 없어 값은 0이지만, 생기는 날
        # 이 함수를 고칠 일이 없다.
        crit_rate = hit.crit_rate,
        crit_dmg  = hit.crit_dmg,
        reaction_crit_rate = _reaction_crit_rate(hit, reaction),
        reaction_crit_dmg  = _reaction_crit_dmg(hit, reaction),

        char_level = char_level,
        enemy_resistance = _enemy_resistance(hit, enemy, element),
    )


def stellar_reaction_input_fields(
    reaction: ReactionType,
    element:  Element,
) -> frozenset[str]:
    """별 반응 반응 피해 1회가 캐리어 히트에서 **실제로 읽는** 필드.
    build_stellar_reaction_context와 짝이다 — 한쪽만 고치면 화면이 '적용됨'으로 띄운 항목이
    실제로는 안 곱해진다.

    lunar_reaction_input_fields와 다른 자리는 하나뿐이다 — 계수의 **재료**(stellar_gust_level)도
    넣는다. 이 값이 반응 배율을 바꾸므로 「이 숫자에 실제로 들어가는 것」에 해당한다. 넣지
    않으면 화면이 계수가 왜 그 값인지 답할 수 없다.
    """
    fields = {
        element_res_reduction_field(element),
        *_EM_LEDGER_FIELDS,
        "elevation_multiplier",
        "crit_rate", "crit_dmg",
        # 반응 배율의 재료. 별 초전도는 반응 피해가 없으므로 기록 히트 수는 여기 없다.
        "stellar_gust_level",
    }

    # 반응 전용 치명타 — 달반응 쪽과 같은 규칙이다(_celestial_crit_fields).
    fields |= _celestial_crit_fields(reaction)

    base = celestial_base_dmg_bonus_field(reaction)
    if base:
        fields.add(base)

    bonus = reaction_bonus_field(reaction)
    if bonus:
        fields.add(bonus)

    return frozenset(fields)


def transformative_input_fields(
    reaction: ReactionType,
    element:  Element,
) -> frozenset[str]:
    """격변 피해 1회가 캐리어 히트에서 **실제로 읽는** 필드. build_transformative_context와 짝이다.

    위 함수가 채우는 자리와 하나씩 대응한다 — 한쪽만 고치면 화면이 '적용됨'으로 띄운
    항목이 실제로는 안 곱해진다(damage_input_fields가 build_damage_context와 맺은 관계와 같다).

    damage_input_fields를 격변에 돌려 쓰지 않는 이유가 둘이다.
      · resolve_reaction(hit, ...)을 부르므로 캐리어 히트의 **내재 반응**(이네파의 달감전
        피해 등)이 여기서 설명하려는 격변 반응을 덮어쓴다. 캐리어는 스탯 운반책일 뿐이라
        그 히트가 무슨 반응을 내장했든 격변 피해와는 상관이 없다.
      · element를 캐리어 히트에서 유도한다. 격변의 피해 원소는 **반응이** 정하므로
        (과부하는 번개가 터뜨려도 불 내성) 트리거 원소의 내성 필드가 나와 어긋난다.

    설명 화면에서 '적용되는 것만' 추리는 데 쓴다 — 계산 경로에서는 부르지 않는다.
    """
    # 계수·스탯·coeff_amp·%피해 보너스·flat_dmg_bonus·방어력 필드는 일부러 없다.
    # _calc_transformative가 하나도 읽지 않는다(위 함수가 0으로 못박은 자리들).
    fields = {element_res_reduction_field(element), *_EM_LEDGER_FIELDS}

    bonus = reaction_bonus_field(reaction)
    if bonus:
        fields.add(bonus)

    # 격변은 캐릭터 치명타가 아니라 반응 전용 치명타를 쓴다 (_calc_transformative).
    prefix = _REACTION_PREFIX.get(reaction)
    if prefix:
        fields |= {f"{prefix}_crit_rate", f"{prefix}_crit_dmg"}

    return frozenset(fields)


# 직접 피해 계열 — 계수 증폭·피해 보너스 풀(%DMG)·방어력 배율을 모두 쓰는 경로다.
# 격변과 달반응은 반응 피해라 셋 다 안 받는다. 달반응 직접 피해는 계수×스탯만 쓴다.
# damage.py의 _calc_* 와 어긋나면 화면에 '적용됨'으로 뜬 항목이 실제로는 안 곱해진다.
_DIRECT_DMG_TYPES    = {DmgType.NONE, DmgType.AMPLIFY, DmgType.CATALYZE}
_DMG_TYPES_WITH_STAT = _DIRECT_DMG_TYPES | {DmgType.LUNAR_DIRECT, DmgType.STELLAR_DIRECT}

# 달·별 반응 계열의 dmg_type — (1 + %기초 피해 증가)와 고저차 배율을 읽는 경로.
_CELESTIAL_DMG_TYPE_SET = {
    DmgType.LUNAR_DIRECT,   DmgType.LUNAR_REACTION,
    DmgType.STELLAR_DIRECT, DmgType.STELLAR_REACTION,
}


def damage_input_fields(
    hit:   SkillHit,
    *,
    reaction_type: ReactionType | None = None,
    dmg_type:      DmgType | None      = None,
) -> frozenset[str]:
    """이 히트의 피해에 **실제로 들어가는** SkillHit 필드 이름들.

    build_damage_context가 읽는 것과 같은 규칙이다 — 원소/스킬 종류/반응에 따라
    한 줌만 골라 읽으므로, 나머지는 값이 붙어 있어도 이 히트의 숫자에는 영향이 없다.
    (스커크 평타는 원소가 없어 물리로 계산된다 → 냉기 피해 보너스는 안 걸린다.)

    설명 화면에서 '적용되는 것만' 추리는 데 쓴다. 계산 경로에서는 부르지 않으므로
    핫패스 비용이 없다."""
    reaction_type, dmg_type = resolve_reaction(hit, reaction_type, dmg_type)
    element = hit.element if hit.element is not None else Element.PHYSICAL

    fields = {element_res_reduction_field(element)}

    # 격변만 flat_dmg_bonus를 안 받는다 — build_transformative_context가 0으로 못박기
    # 때문이다(캐리어 히트에 쌓인 값은 직접 피해용이다). 나머지 경로는 damage.py의
    # _calc_* 가 모두 이 필드를 읽는다.
    if dmg_type is not DmgType.TRANSFORMATIVE:
        fields.add("flat_dmg_bonus")

    # 격변은 반응 전용 치명타 **만** 쓴다 (_calc_transformative — 캐릭터 치명타를 안 읽는다).
    # 달·별 직접 피해는 **둘 다** 쓴다 (_calc_lunar_direct가 더한다). 나머지는 평소 치명타뿐.
    prefix = _REACTION_PREFIX.get(reaction_type)
    if dmg_type is DmgType.TRANSFORMATIVE:
        if prefix:
            fields |= {f"{prefix}_crit_rate", f"{prefix}_crit_dmg"}
    else:
        fields |= {"crit_rate", "crit_dmg"}
        if prefix and dmg_type in (DmgType.LUNAR_DIRECT, DmgType.STELLAR_DIRECT):
            fields |= {f"{prefix}_crit_rate", f"{prefix}_crit_dmg"}

    if dmg_type in _DMG_TYPES_WITH_STAT:
        fields.add("coeff")
        if hit.stat_fn is not None:
            # 임의의 함수라 어떤 스탯을 읽는지 알 수 없다 → 전부 후보로 남긴다.
            prefixes = ("hp", "atk", "def")
            fields |= _EM_LEDGER_FIELDS
        else:
            attr = _SCALING_STAT_ATTR[hit.scaling_stat]
            # atk_final 같은 파생값은 base/pct/flat 세 조각에서 나온다.
            prefixes = (attr.removesuffix("_final"),) if attr.endswith("_final") else ()
            if not prefixes:
                _add_stat_field(fields, attr)       # 원소 마스터리 스케일
        for prefix in prefixes:
            fields |= {f"{prefix}_base", f"{prefix}_pct", f"{prefix}_flat"}

    if dmg_type in _DIRECT_DMG_TYPES:
        fields |= {"coeff_amp", "all_dmg_bonus", "def_reduction", "def_ignore"}
        for field in (element_dmg_field(element), skill_dmg_field(hit.skill_type)):
            if field:
                fields.add(field)

    if reaction_type is not ReactionType.NONE:
        fields |= _EM_LEDGER_FIELDS
        bonus = reaction_bonus_field(reaction_type)
        if bonus:
            fields.add(bonus)

    if dmg_type in _CELESTIAL_DMG_TYPE_SET:
        fields.add("elevation_multiplier")
        # 기초 피해 증가는 그 반응 전용 필드 하나만 — build_damage_context가 담는 것과 같다
        # (_celestial_base_dmg_bonus). 여럿 넣으면 안 곱해지는 항목이 '적용됨'으로 뜬다.
        base = celestial_base_dmg_bonus_field(reaction_type)
        if base:
            fields.add(base)

    # 별 반응 계수의 재료. 반응 배율을 바꾸는 값이라 이 숫자에 실제로 들어간다.
    # 반응마다 재료가 다르므로 쓰는 것만 넣는다 — 별 초전도는 기록 히트 수,
    # 별 확산은 별빛 돌풍 레벨이다(core.stellar.stellar_multiplier).
    if reaction_type is ReactionType.STELLAR_CONDUCT:
        fields.add("stellar_recorded_hits")
    elif reaction_type is ReactionType.STELLAR_SWIRL:
        if dmg_type is DmgType.STELLAR_REACTION:
            fields.add("stellar_gust_level")   # 직접 피해 계수는 고정 1.0이라 재료가 없다

    return frozenset(fields)
