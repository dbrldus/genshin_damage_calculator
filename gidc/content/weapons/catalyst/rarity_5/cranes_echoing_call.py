from gidc.core.weapon import Weapon
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class CranesEchoingCall(Weapon):
    """학의 여음 (Crane's Echoing Call) | 법구 | 5성 | 한운 전용 무기
    패시브: 운급 강림 비법
    - 장착 캐릭터의 낙하 공격이 적에게 명중 후, 주변에 있는 파티 내 모든 캐릭터의
      낙하 공격이 주는 피해가 28/41/54/67/80% 증가한다. 지속 시간: 20초.
    - 주변 파티원의 낙하 공격 명중 시 장착 캐릭터의 원소 에너지를
      2.5/2.75/3/3.25/3.5pt 회복 (0.7초에 최대 1회) — 자원 모델이 없어 피해식에
      들어갈 항이 아니다. 재련 단계별 값만 _ENERGY_RESTORE로 남긴다
      (페보니우스 검·위대한 사막 현자의 대답과 같은 계열).

    「파티 내 모든 캐릭터」이고 제외 문구가 없으므로 착용자도 포함된다.
    「주변」은 사거리 조건이라 항상 참으로 본다.
    파티 전체에 뿌리는 효과이므로 동명의 무기끼리는 중첩되지 않는다.

    낙하 공격 피해 보너스는 히트 종류로 걸러지므로(plunging_dmg_bonus) 전 히트에
    넣어도 낙하 공격에만 실린다 — 한운의 충격파처럼 「낙하 공격 피해로 간주」되는
    히트도 SkillType.PLUNGING이라 그대로 받는다.
    """

    _PLUNGE_DMG     = [0.28, 0.41, 0.54, 0.67, 0.80]
    _ENERGY_RESTORE = [2.5, 2.75, 3.0, 3.25, 3.5]

    _SOURCE = "무기: 학의 여음"

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 4,
            refinement    = refinement,
            sub_stat_type = StatType.ATK_PCT,
        )

    # 고정값 피해 보너스라 스탯을 읽지 않는다 → Phase 3에서 넣어도 순서와 무관하다.
    def apply_passive(self, all_hits, wearer) -> None:
        if not ask_bool("[학의 여음] 착용자의 낙하 공격 명중으로 「운급 강림 비법」 발동 중인지 여부"):
            return

        bonus = self._PLUNGE_DMG[self.refinement - 1]
        for char_hits in all_hits.values():
            for hit in char_hits.values():
                hit.apply_unique_buff(self._SOURCE, "plunging_dmg_bonus", bonus)
