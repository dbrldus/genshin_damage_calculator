from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class SongOfBrokenPines(Weapon):
    """송뢰가 울릴 무렵 (Song of Broken Pines) | 양손검 | 5성
    패시브: 깃발을 든 반항의 노래
    - 바람 속을 유랑하는 「천년의 대악장」의 일부분. 공격력이 16/20/24/28/32% 증가한다.
    - 일반 공격 혹은 강공격이 적에게 명중 시, 캐릭터는 속삭임의 부적을 1개 획득하고, 이는
      0.3초마다 한번 발동된다. 속삭임의 부적 4개 소유 시, 부적을 모두 소모하여 주변의 파티 내
      모든 캐릭터에게 12초 동안 「천년의 대악장·깃발의 노래」 효과를 부여한다: 일반 공격 속도가
      12/15/18/21/24% 증가하고, 공격력이 20/25/30/35/40% 증가한다. 발동 후 20초 동안은 속삭임의
      부적을 획득할 수 없다. 「천년의 대악장」의 수치 효과 중 동일 유형의 수치 효과는 중첩될 수
      없다.
    """

    _ATK_PCT       = [0.16, 0.2, 0.24, 0.28, 0.32]
    _PARTY_ATK_PCT = [0.2, 0.25, 0.3, 0.35, 0.4]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CLAYMORE,
            rarity        = 5,
            tier          = 4,
            refinement    = refinement,
            sub_stat_type = StatType.PHYSICAL_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 송뢰가 울릴 무렵"

        # 효과 1: 상시 공격력% (착용자) — 조건 없이 항상 붙는다.
        for hit in all_hits[wearer].values():
            hit.add("atk_pct", self._ATK_PCT[r], label)

        # 효과 2 「천년의 대악장·깃발의 노래」: 부적 4개를 모아 터뜨린 상태인지는 로테이션이
        # 정하므로 묻는다 — 부적 자체(0.3초당 1개, 20초 재획득 제한)는 스택이 아니라 이 버프의
        # 온/오프를 결정하는 트리거일 뿐이라 별도로 묻지 않는다.
        # 파티 전원(장착자 포함, 「주변의」로 범위가 좁혀지지 않음) + 비중첩 — 동명의 무기
        # 두 자루가 각자 발동해도 공격력 보너스는 겹치지 않는다.
        if not ask_bool("[송뢰가 울릴 무렵] 「천년의 대악장·깃발의 노래」 발동? (부적 4개 소모)"):
            return
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.apply_unique_buff(label, "atk_pct", self._PARTY_ATK_PCT[r])

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 일반 공격 속도 +12/15/18/21/24% (「깃발의 노래」 발동 중) — 히트 단가를 바꾸지
    #   않는다. 로테이션에 히트를 몇 개 더 넣느냐의 문제이고, 이 계산기는 히트 목록을 유저가
    #   정한 대로 받는다(천공의 마루·늑대의 무용담과 같다).
    # · 속삭임의 부적 획득 속도(0.3초당 1회)·발동 후 20초 재획득 제한 — 버프가 걸려 있는지만
    #   묻고, 무엇이 그 상태를 만들었는지는 유저가 판단한다.
