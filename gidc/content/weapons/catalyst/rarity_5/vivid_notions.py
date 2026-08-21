from gidc.core.weapon import Weapon
from gidc.core.profile import SkillType
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool


class VividNotions(Weapon):
    """빛나는 마음 (Vivid Notions) | 법구 | 5성
    패시브: 무지개의 소원
    - 공격력이 28/35/42/49/56% 증가한다.
    - 캐릭터가 낙하 공격 시, 「아침놀빛」 효과를 획득한다:
      낙하 공격으로 주는 치명타 피해가 28/35/42/49/56% 증가한다.
    - 원소 전투 스킬 또는 원소폭발 발동 시, 「저녁놀빛」 효과를 획득한다:
      낙하 공격으로 주는 치명타 피해가 40/50/60/70/80% 증가한다.
    - 상술한 2가지 효과는 각각 15초 동안 지속되며, 추락 충격으로 피해를 주면
      0.1초 후에 사라진다
    """

    _ATK_PCT = [0.28, 0.35, 0.42, 0.49, 0.56]
    _DAWN_CD = [0.28, 0.35, 0.42, 0.49, 0.56]   # 아침놀빛
    _DUSK_CD = [0.40, 0.50, 0.60, 0.70, 0.80]   # 저녁놀빛

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 3,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 빛나는 마음"
        hits  = all_hits[wearer].values()

        # 효과 1: 공격력 — 조건이 없고 착용자에게만 붙는다.
        for hit in hits:
            hit.add("atk_pct", self._ATK_PCT[r], label, note="무지개의 소원")

        # 효과 2·3: 「낙하 공격으로 주는 치명타 피해」.
        #
        # 전용 필드를 만들지 않고 **낙하 히트만 골라 crit_dmg에 더한다.** 낙하 공격은
        # 실제 SkillHit이라 skill_type으로 정확히 한정되기 때문이다 — 에슈의 재앙이
        # 일반/강공격 치명타 확률을 넣는 방식과 같다. (달반응 전용 치명타가 전용 필드를
        # 써야 했던 것은 달반응 반응 피해가 히트가 아니라 별도 피해 인스턴스여서,
        # 골라 넣을 히트가 없었기 때문이다 — 여기는 그 문제가 없다.)
        #
        # 덤으로 explain이 그대로 따라온다. crit_dmg는 이미 damage_input_fields에
        # 들어 있어 코어를 고치지 않아도 출처가 원장에 남는다.
        #
        # 두 효과는 「각각 15초」로 따로 도는 별개 효과라 동시에 켜지면 합산한다.
        # 「추락 충격으로 피해를 주면 0.1초 후 소멸」은 그 히트 뒤의 이야기이므로
        # 낙하 히트 자신은 온전히 받는다.
        bonus = 0.0
        if ask_bool("[빛나는 마음] 낙하 공격 후 15초 이내 (아침놀빛) 여부"):
            bonus += self._DAWN_CD[r]
        if ask_bool("[빛나는 마음] 원소 전투 스킬/폭발 발동 후 15초 이내 (저녁놀빛) 여부"):
            bonus += self._DUSK_CD[r]
        if not bonus:
            return

        for hit in hits:
            if hit.skill_type is SkillType.PLUNGING:
                hit.add("crit_dmg", bonus, label, note="아침놀빛/저녁놀빛")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 15초 지속 시간과 「추락 충격 후 0.1초 소멸」 — 로테이션에서 몇 번 실리는지를 정하는
    #   값이지 히트 단가에 들어갈 항이 없다. 실렸는지 여부만 유저에게 묻는다.
