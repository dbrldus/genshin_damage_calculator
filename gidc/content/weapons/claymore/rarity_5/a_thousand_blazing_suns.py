from gidc.core.weapon import Weapon, WeaponSubStat
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class AThousandBlazingSuns(Weapon):
    """타오르는 천 개의 태양 (A Thousand Blazing Suns) | 양손검 | 5성
    패시브: 다시 타오르는 여명
    - 원소전투 스킬 또는 원소폭발 발동 시 「불빛」 획득:
      치명타 피해 +20/25/30/35/40%, 공격력 +28/35/42/49/56%.
      지속 6초, 10초마다 최대 1회 발동
    - 지속 시간 동안 일반 공격 또는 강공격이 원소 피해를 준 후 이번 「불빛」의 지속 시간이
      2초 연장된다. 1초마다 최대 1회, 최대 6초까지 연장
    - 밤혼 가호 상태에서는 「불빛」의 효과가 75% 증가하며, 「불빛」은 장착 캐릭터가
      대기 상태일 시 카운트를 진행하지 않는다
    """

    _CRIT_DMG = [0.20, 0.25, 0.30, 0.35, 0.40]
    _ATK_PCT  = [0.28, 0.35, 0.42, 0.49, 0.56]
    # 밤혼 가호 상태에서 「불빛」의 두 수치가 함께 커지는 비율
    _NIGHTSOUL_BOOST = 0.75

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type = WeaponType.CLAYMORE,
            base_atk    = 741,
            refinement  = refinement,
            sub_stat    = WeaponSubStat(StatType.CRIT_RATE, 11.0),
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r = self.refinement - 1

        # 「불빛」은 착용자에게만 걸리는 고정값 버프라 스탯을 읽을 것이 없다 → Phase 3에서 끝난다.
        if not ask_bool("[타오르는 천 개의 태양] 원소전투 스킬·원소폭발 발동 (「불빛」) 여부"):
            return

        # 밤혼 가호 상태면 치명타 피해와 공격력 증가가 **둘 다** 75% 커진다.
        # 밤혼 가호를 못 얻는 캐릭터도 있지만 그 판정은 캐릭터 특성이 아니라 로테이션
        # 상태라 파티 구성만으로 유도할 수 없다 — 「불빛」이 켜졌을 때만 묻는다.
        boost = (1.0 + self._NIGHTSOUL_BOOST
                 if ask_bool("[타오르는 천 개의 태양] 밤혼 가호 상태 여부")
                 else 1.0)

        crit_dmg = self._CRIT_DMG[r] * boost
        atk_pct  = self._ATK_PCT[r]  * boost

        for hit in all_hits[wearer].values():
            hit.add("crit_dmg", crit_dmg, "무기: 타오르는 천 개의 태양", note="다시 타오르는 여명")
            hit.add("atk_pct",  atk_pct,  "무기: 타오르는 천 개의 태양", note="다시 타오르는 여명")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 일반/강공격의 원소 피해로 「불빛」 지속 시간 2초 연장(최대 6초)과 대기 상태에서
    #   카운트가 멈추는 효과 — 지속 시간만 늘릴 뿐 히트당 피해는 그대로다.
    # · 10초마다 최대 1회라는 재발동 제한 — 발동 횟수는 로테이션의 문제다.
