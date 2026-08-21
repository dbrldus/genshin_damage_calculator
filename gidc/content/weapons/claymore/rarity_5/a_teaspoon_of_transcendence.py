from gidc.core.weapon import Weapon
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_int


class ATeaspoonOfTranscendence(Weapon):
    """초월의 열쇠 (A Teaspoon of Transcendence) | 양손검 | 5성
    패시브: 하얀 여왕의 승급
    - 공격력이 28/35/42/49/56% 증가한다.
    - 또한, 장착 캐릭터의 강공격이 적에게 명중할 때마다 짧은 시간 동안 「초월」을 달성한다:
      장착 캐릭터의 별 초전도와 별 확산 반응 피해가 16/20/24/28/32% 증가한다,
      지속 시간: 5초. 해당 효과는 0.2초마다 최대 1스택 중첩된다, 최대 중첩수: 3스택
    """

    _ATK_PCT     = [0.28, 0.35, 0.42, 0.49, 0.56]
    _STELLAR_DMG = [0.16, 0.20, 0.24, 0.28, 0.32]

    _MAX_STACKS = 3

    # 「별 초전도와 별 확산」 두 계열을 나란히 올린다. 별 초전도는 반응 피해가 없고 극지의
    # 별 영역 직접 피해로 들어가지만(core.stellar), 그 히트도 같은 필드를 읽으므로
    # 계열마다 필드를 갈라 적지 않는다 — 산드로네 C1·그림자 속 산산조각 난 꿈 4세트와 같다.
    _STELLAR_BONUS_FIELDS = ("stellar_conduct_bonus", "stellar_swirl_bonus")

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CLAYMORE,
            rarity        = 5,
            tier          = 3,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 초월의 열쇠"
        hits  = all_hits[wearer].values()

        # 효과 1: 공격력 — 조건이 없고 착용자에게만 붙는다.
        for hit in hits:
            hit.add("atk_pct", self._ATK_PCT[r], label, note="하얀 여왕의 승급")

        # 효과 2 「초월」 스택. 트리거가 착용자의 강공격 명중이라 파티로 유도되지 않는다 —
        # 로테이션에서 강공격을 몇 번 넣었는지는 유저만 안다.
        #
        # 별 반응이 이 파티에서 성립하는지(stellar_conditions)로 질문을 막지는 않는다.
        # 성립하지 않으면 이 필드를 읽는 히트가 아예 없어서 답이 무엇이든 결과가 같고,
        # 막으려면 무기가 파티 판정을 한 벌 더 들고 있어야 한다. 같은 이유로 그림자 속
        # 산산조각 난 꿈 4세트도 별 초전도 몫을 조건 없이 얹는다.
        stacks = ask_int(
            "[초월의 열쇠] 「초월」 스택 수 "
            f"(강공격이 적에게 명중, 최대 {self._MAX_STACKS})",
            0, self._MAX_STACKS,
        )
        if not stacks:
            return

        for hit in hits:
            for field in self._STELLAR_BONUS_FIELDS:
                hit.add(field, stacks * self._STELLAR_DMG[r], label, note="초월 스택")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 5초 지속 시간과 0.2초마다 1스택이라는 누적 속도 — 스택이 몇 개 실려 있는지만 묻고
    #   유지 여부는 유저가 판단한다(등방울꽃의 애가와 같다).
