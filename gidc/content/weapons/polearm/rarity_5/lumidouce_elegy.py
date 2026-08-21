from gidc.core.weapon import Weapon
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_int


class LumidouceElegy(Weapon):
    """등방울꽃의 애가 (Lumidouce Elegy) | 장병기 | 5성
    패시브: 하얀 새벽의 서곡
    - 공격력이 15/19/23/27/31% 증가한다.
    - 장착 캐릭터가 적에게 연소 반응 발동 또는 연소 상태의 적에게 풀 원소 피해를 준 후,
      주는 피해가 18/23/28/33/38% 증가한다, 해당 효과 지속 시간: 8초, 최대 중첩수: 2스택.
    - 2스택 달성 또는 2스택의 지속 시간 갱신 시, 원소 에너지를 12/13/14/15/16pt 회복한다.
      해당 방식으로 12초마다 원소 에너지를 최대 1번 회복할 수 있다.
    - 상술한 2가지 효과는 캐릭터가 대기 상태일 때도 발동된다
    """

    _ATK_PCT       = [0.15, 0.19, 0.23, 0.27, 0.31]
    _DMG_PER_STACK = [0.18, 0.23, 0.28, 0.33, 0.38]

    _MAX_STACKS = 2

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.POLEARM,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 등방울꽃의 애가"
        hits  = all_hits[wearer].values()

        # 효과 1: 공격력 — 조건이 없고 착용자에게만 붙는다.
        for hit in hits:
            hit.add("atk_pct", self._ATK_PCT[r], label, note="하얀 새벽의 서곡")

        # 효과 2 「주는 피해」 스택. 대기 상태에서도 발동하므로 필드 등장 여부는 묻지 않는다.
        #
        # 파티 구성으로 게이팅하지 않는다. 트리거가 연소 반응인데, 연소는 불과 풀이 둘 다
        # 적에게 붙어야 하고 한쪽은 적이 원래 두르고 있을 수 있다(용학살창과 같은 이유).
        # 게다가 바람 캐릭터가 확산시킨 불도 연소를 일으키므로 착용자 원소로도 막을 수 없다.
        # 달감전처럼 「이 파티에서 가능한가」를 답해 주는 함수가 없는 자리다
        # (transformative_candidates의 aura는 다른 파티원의 원소일 뿐 적 부착을 모른다).
        stacks = ask_int(f"[등방울꽃의 애가] 「하얀 새벽의 서곡」 스택 수 (최대 {self._MAX_STACKS})",
                         0, self._MAX_STACKS)
        if not stacks:
            return

        for hit in hits:
            hit.add("all_dmg_bonus", stacks * self._DMG_PER_STACK[r], label,
                    note="하얀 새벽의 서곡 스택")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 원소 에너지 12~16pt 회복 (2스택 달성/갱신 시, 12초 1회) — 로테이션 빈도를 정하는
    #   값이지 히트 단가에 들어갈 항이 없다.
    # · 8초 지속 시간 — 스택이 몇 개 실려 있는지만 묻고 유지 여부는 유저가 판단한다.
