from gidc.core.weapon import Weapon
from gidc.core.reaction import lunar_candidates
from gidc.enums import ReactionType
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool


class BloodsoakedRuins(Weapon):
    """피로 물든 성 (Bloodsoaked Ruins) | 장병기 | 5성
    패시브: 애도가
    - 원소폭발 발동 후 3.5초 동안 장착 캐릭터가 적에게 주는 달 감전 반응 피해가
      36/48/60/72/84% 증가한다.
    - 또한, 장착 캐릭터가 달 감전 반응 발동 후, 「폐허의 만가」를 획득한다:
      치명타 피해가 28/35/42/49/56% 증가한다, 지속 시간: 6초.
    - 장착 캐릭터가 원소 에너지를 12/13/14/15/16pt 회복하며, 해당 방식으로 14초마다
      원소 에너지가 최대 1회 회복된다
    """

    _LUNAR_CHARGED   = [0.36, 0.48, 0.60, 0.72, 0.84]
    _DIRGE_CRIT_DMG  = [0.28, 0.35, 0.42, 0.49, 0.56]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.POLEARM,
            rarity        = 5,
            tier          = 3,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_RATE,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 피로 물든 성"
        hits  = all_hits[wearer].values()

        # 효과 1: 달 감전 반응 피해 증가 — 「기초 피해 증가」가 아니라 반응 보너스 쪽이다.
        # 같은 문구를 쓰는 채굴의 삽·파멸의 빛고리·천둥의 분노 4세트가 모두 이 필드다.
        # (lunar_charged_base_dmg_bonus는 「기초 피해 증가」 문구 전용 — 공식에서 곱해지는
        # 자리가 다르다.)
        if ask_bool("[피로 물든 성] 원소폭발 발동 후 3.5초 이내 여부"):
            for hit in hits:
                hit.add("lunar_charged_bonus", self._LUNAR_CHARGED[r], label, note="애도가")

        # 효과 2 「폐허의 만가」: 한정어 없는 **치명타 피해**다 — 달 감전 반응에만 붙는 것이
        # 아니므로 히트 전역 crit_dmg가 맞고, 히트를 고를 것도 전용 필드도 없다.
        #
        # 다만 트리거가 「**장착 캐릭터가** 달 감전 반응 발동」이라, 켜지려면 두 가지가
        # 모두 성립해야 한다 — 파티에서 달 감전 반응이 일어날 수 있어야 하고, 착용자가
        # 그 반응을 직접 터뜨릴 수 있어야 한다(물이나 번개여야 한다). 둘 다 파티 구성만으로
        # 정해지므로 묻지 않고 걸러 낸다 — 치명타 피해 +56%짜리 전역 버프라 성립하지 않는
        # 파티에서 질문을 띄우면 오적용 여지가 크다.
        # (채굴의 삽이 달빛 징조를 파티에서 유도하는 것과 같은 규약.)
        if not self._wearer_can_trigger_lunar_charged(all_hits, wearer):
            return
        if not ask_bool("[피로 물든 성] 달 감전 반응 발동 후 6초 이내 (폐허의 만가) 여부"):
            return
        for hit in hits:
            hit.add("crit_dmg", self._DIRGE_CRIT_DMG[r], label, note="폐허의 만가")

    @staticmethod
    def _wearer_can_trigger_lunar_charged(all_hits, wearer) -> bool:
        """착용자가 이 파티에서 달 감전 반응을 **직접 터뜨릴 수 있는가**.

        lunar_candidates가 반응마다 (반응, 피해 원소, 트리거 후보 파티원)을 돌려준다.
        후보는 그 반응에 필요한 원소를 가진 파티원이므로, 착용자가 거기 들어 있는지만 보면
        「전환자가 있는가 · 두 원소가 갖춰졌는가 · 착용자가 물이나 번개인가」가 한꺼번에
        걸러진다. 조건을 여기 다시 적으면 규칙이 갈린다."""
        return any(reaction is ReactionType.LUNAR_CHARGED and wearer in triggers
                   for reaction, _element, triggers in lunar_candidates(all_hits))

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 원소 에너지 12/13/14/15/16pt 회복 (14초 1회) — 로테이션 빈도를 정하는 값이지
    #   히트 단가에 들어갈 항이 없다.
