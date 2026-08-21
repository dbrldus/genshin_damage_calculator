from gidc.core.weapon import Weapon
from gidc.core.party_state import has_hexerei_rite
from gidc.enums import CharacterTrait
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool, ask_choice


def _ask_on_field_member(all_hits, wearer):
    """「선도의 빛」이 대상으로 삼을 현재 필드 위 캐릭터를 고르게 한다.
    파티원이 1명뿐이면 묻지 않는다(하늘의 은총 4세트와 같은 규약)."""
    members = list(all_hits.keys())
    if len(members) == 1:
        return members[0]
    options = [
        f"{char.name} ({char.element.value})"
        + (" ← 장착 캐릭터" if char is wearer else "")
        for char in members
    ]
    return members[ask_choice("[일곱빛 계시] 현재 필드 위 캐릭터", options)]


class AngelosHeptades(Weapon):
    """일곱빛 계시 (Angelos' Heptades) | 법구 | 5성
    패시브: 막내의 왕관
    - 공격력이 12/15/18/21/24% 증가한다.
    - 장착 캐릭터가 보호막 생성 후 20초 동안 「선도의 빛」 효과를 획득한다:
      장착 캐릭터의 공격력에 기반하여, 공격력 1000pt마다 현재 필드 위에 있는 파티 내
      자신의 캐릭터가 주는 피해가 10/13/16/19/22% 증가하여,
      최대 26/34/42/50/58% 증가한다.
    - 지속 시간 동안 현재 필드 위에 있는 파티 내 자신의 캐릭터의 공격이 주변의 적에게
      명중하거나 비전투 상태에서 보물상자 오픈 시, 추가로 「인도자의 만족」 효과를 획득해
      장착 캐릭터가 원소 에너지를 14/15/16/17/18pt 회복한다. 해당 효과는 16초마다 최대
      1회 발동된다. 장착 캐릭터가 대기 상태일 때도 해당 효과가 발동된다.
    - 마도·비밀 의식: 파티 내 자신의 마도 캐릭터가 대기 상태일 때도 「선도의 빛」의
      피해 증가 효과 중 50%를 획득한다
    """

    _ATK_PCT      = [0.12, 0.15, 0.18, 0.21, 0.24]
    _LIGHT_PER_1K = [0.10, 0.13, 0.16, 0.19, 0.22]
    _LIGHT_CAP    = [0.26, 0.34, 0.42, 0.50, 0.58]

    # 마도·비밀 의식이 대기 중인 마도 캐릭터에게 나눠 주는 몫
    _HEXEREI_SHARE = 0.50

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 4,
            refinement    = refinement,
            sub_stat_type = StatType.ATK_PCT,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 일곱빛 계시"

        # 효과 1: 공격력 증가 — 조건이 없고 착용자에게만 붙는다.
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", self._ATK_PCT[r], label, note="막내의 왕관")

        # 효과 2 「선도의 빛」의 조건과 대상. 실제 보너스는 착용자의 **최종** 공격력을
        # 읽어야 하므로 apply_passive_dependent(Phase 5)에서 만든다. 여기서는 유저 입력만
        # 모아 self에 저장한다 — 질문은 반드시 이 단계에서 해야 질문 집합이 흔들리지 않는다.
        self._light = ask_bool("[일곱빛 계시] 보호막 생성 후 20초 이내 (선도의 빛) 여부")
        self._on_field = _ask_on_field_member(all_hits, wearer) if self._light else None

    # ── 「선도의 빛」 — 착용자의 최종 공격력 기반 (방식 B) ────────────────────
    # 공격력을 읽어 **피해 보너스**로 바꾸므로 차원이 달라져 되먹임이 없다.
    # 동명의 무기 효과는 중첩되지 않는다 — 여러 명이 착용하면 공격력이 가장 높은 쪽의
    # 보너스만 남도록 비중첩으로 제출한다.
    def apply_passive_dependent(self, all_hits, wearer) -> None:
        if not self._light:
            return
        r     = self.refinement - 1
        label = "무기: 일곱빛 계시"

        # 착용자의 공격력을 **읽는 함수**로 넘긴다(지연 기여). 이 단계에서 다른 캐릭터가
        # 아직 공격력을 더하는 중일 수 있어, 지금 확정하면 파티 멤버 순서가 결과를 바꾼다.
        # 「1000pt마다」는 바위산을 맴도는 노래와 같이 연속으로 본다(계단이 아니다).
        source_hit = next(iter(all_hits[wearer].values()))
        full = lambda: min(
            (source_hit.convertible_atk() / 1000.0) * self._LIGHT_PER_1K[r],
            self._LIGHT_CAP[r],
        )

        # 현재 필드 위 캐릭터 — 전액.
        for hit in all_hits[self._on_field].values():
            hit.apply_unique_buff(label, "all_dmg_bonus", full)

        # 마도·비밀 의식: 대기 중인 마도 캐릭터도 절반을 받는다.
        # 읽는 것은 has_hexerei_rite(파티에 마도 2명 이상)다 — hexerei_rite_for가 아니다.
        # 이 절은 「착용자가 마도일 것」을 요구하지 않고, 받는 쪽이 마도이기만 하면 된다.
        # 필드 위 캐릭터는 이미 전액을 받았으므로 제외한다(더해지는 것이 아니라 「대기
        # 상태일 때도」 받게 해 주는 절이다).
        if not has_hexerei_rite(all_hits):
            return
        half = lambda: full() * self._HEXEREI_SHARE
        for char, char_hits in all_hits.items():
            if char is self._on_field or not char.has_trait(CharacterTrait.HEXEREI):
                continue
            for hit in char_hits.values():
                hit.apply_unique_buff(label, "all_dmg_bonus", half)

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 「인도자의 만족」 — 원소 에너지 14/15/16/17/18pt 회복. 로테이션 빈도를 정하는 값이지
    #   히트 단가에 들어갈 항이 없다(에너지 회복은 이 엔진이 모델링하지 않는다).
