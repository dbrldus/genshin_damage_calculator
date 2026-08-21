from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class BeaconOfTheReedSea(Weapon):
    """갈대 바다의 등대 (Beacon of the Reed Sea) | 양손검 | 5성
    패시브: 모래바다 파수
    - 원소전투 스킬이 적에게 명중 후 공격력이 20/25/30/35/40% 증가한다. 지속 시간: 8초.
    - 피해를 입은 후 공격력이 20/25/30/35/40% 증가한다. 지속 시간: 8초.
    - 상술한 2가지 효과는 캐릭터가 대기 상태 시에도 발동할 수 있다.
    - 또한 보호막의 보호를 받지 않을 시, HP 최대치가 32/40/48/56/64% 증가한다
    """

    _SKILL_ATK   = [0.2, 0.25, 0.3, 0.35, 0.4]
    _DAMAGED_ATK = [0.2, 0.25, 0.3, 0.35, 0.4]
    _HP_PCT      = [0.32, 0.4, 0.48, 0.56, 0.64]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CLAYMORE,
            rarity        = 5,
            tier          = 2,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 갈대 바다의 등대"
        hits  = all_hits[wearer].values()

        # 앞 두 효과는 트리거가 따로다(E 명중 / 피해를 입음). 서로를 함의하지 않으므로
        # 독립된 ask_bool 둘이고 켜진 만큼 합산된다 — 나른한 새해와 같은 자리다.
        # 둘 다 대기 상태에서 발동하므로 필드 등장 여부는 묻지 않는다.
        # 문구에 증가량을 적어 어느 줄이 얼마인지 화면에서 바로 보이게 한다.
        buffs = (
            ("원소전투 스킬 명중 후 8초 이내", self._SKILL_ATK[r],   "모래바다 파수 E"),
            ("피해를 입은 후 8초 이내",       self._DAMAGED_ATK[r], "모래바다 파수 피격"),
        )
        for question, amount, note in buffs:
            if not ask_bool(f"[갈대 바다의 등대] {question} 여부 (공격력 +{amount:.0%})"):
                continue
            for hit in hits:
                hit.add("atk_pct", amount, label, note=note)

        # 세 번째 효과는 조건이 **부정**이다(보호막을 받지 **않을** 때). 그대로 부정형으로
        # 묻는다 — 「받는 중인지」로 묻고 뒤집으면(에슈의 재앙의 문구) 무응답 기본값 False가
        # 「보호막 없음」이 되어 HP +64%가 저절로 켜진다. 웹은 아직 답하지 않은 질문을
        # 기본값으로 계산하므로, 기본값이 효과 off 쪽에 서야 한다.
        if ask_bool(f"[갈대 바다의 등대] 보호막의 보호를 받지 「않는」 상태?"
                    f"(HP 최대치 +{self._HP_PCT[r]:.0%})"):
            for hit in hits:
                hit.add("hp_pct", self._HP_PCT[r], label, note="모래바다 파수 보호막 없음")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 두 공격력 버프의 지속 시간 8초 — 켜졌는지만 묻고 유지 여부는 유저가 판단한다.
