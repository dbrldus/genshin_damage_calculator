from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class ElegyForTheEnd(Weapon):
    """종말 탄식의 노래 (Elegy for the End) | 활 | 5성
    패시브: 이별의 그리운 노래
    - 바람 속을 유랑하는 「천년의 대악장」의 일부분. 원소 마스터리가 60/75/90/105/120pt
      증가한다. 원소전투 스킬이나 원소폭발이 적에게 명중 시, 캐릭터는 회상의 부적을
      한 장 획득한다. 이는 0.2초마다 한 번 발동되며, 캐릭터가 대기 상태일 때도
      발동된다. 회상의 부적 4장 소유 시, 부적을 모두 소모하여 주변의 파티 내 모든
      캐릭터에게 12초 동안 「천년의 대악장·이별의 노래」 효과를 부여한다: 원소
      마스터리가 100/125/150/175/200pt 증가하고, 공격력이 20/25/30/35/40% 증가한다.
      발동 후 20초 동안은 회상의 부적을 획득할 수 없다. 「천년의 대악장」의 수치 효과
      중 동일 유형의 수치 효과는 중첩될 수 없다
    """

    _BASE_EM       = [60.0, 75.0, 90.0, 105.0, 120.0]
    _PARTY_EM      = [100.0, 125.0, 150.0, 175.0, 200.0]
    _PARTY_ATK_PCT = [0.2, 0.25, 0.3, 0.35, 0.4]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.BOW,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.ENERGY_RECHARGE,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 종말 탄식의 노래"

        # 효과 1: 「천년의 대악장」 조각으로 얻는 상시 원소 마스터리 — 착용자에게만 붙는다.
        for hit in all_hits[wearer].values():
            hit.add("em_from_flat", self._BASE_EM[r], label, note="이별의 그리운 노래")

        # 효과 2 「천년의 대악장·이별의 노래」. 회상의 부적 4장 소모가 트리거인데, 명중
        # 여부(0.2초 1회 제한)와 20초 재발동 제한은 로테이션 몫이라 활성 여부만 묻는다.
        # 대기 상태에서도 부적을 얻을 수 있으므로 필드 등장 여부는 따로 묻지 않는다
        # (오래된 자유의 서약과 같은 판단).
        if not ask_bool(
            "[종말 탄식의 노래] 「천년의 대악장·이별의 노래」 효과 여부"
        ):
            return

        # 파티 전원(착용자 포함) 대상이라 동명 무기 간 비중첩 규약을 지키려면
        # apply_unique_buff로 제출한다. 「천년의 대악장」 발동 효과는 동일 수치의 다른
        # 효과와 중첩되지 않는다는 원문도 같은 방향이다 — 오래된 자유의 서약·송뢰가
        # 울릴 무렵과 같은 「천년의 대악장」 계열이지만, 소스 키(무기명)로 비중첩을
        # 판정하는 이 엔진의 구조상 계열 간 상호 비중첩까지는 반영하지 않는다.
        em_bonus  = self._PARTY_EM[r]
        atk_bonus = self._PARTY_ATK_PCT[r]
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.apply_unique_buff(label, "em_from_flat", em_bonus)
                hit.apply_unique_buff(label, "atk_pct", atk_bonus)

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 회상의 부적 획득(스킬·폭발 명중 시 1장, 0.2초당 1회 제한)과 4장 소모 트리거,
    #   발동 후 20초 부적 획득 정지 — 실제로 「이별의 노래」가 켜져 있는지 결과 상태만
    #   묻는다.
    # · 다른 「천년의 대악장」 계열 무기(오래된 자유의 서약·송뢰가 울릴 무렵)와의 계열
    #   간 비중첩 — 이 엔진은 소스 키(무기명) 단위로만 비중첩을 판정한다. 같은 파티에
    #   두 계열 무기를 동시에 켜면 실제 게임과 달리 중복 합산된다.
