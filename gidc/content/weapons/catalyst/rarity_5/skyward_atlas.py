from gidc.core.weapon import Weapon
from gidc.core.profile import SkillHit, SkillType, element_dmg_field
from gidc.enums import WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class SkywardAtlas(Weapon):
    """천공의 두루마리 (Skyward Atlas) | 법구 | 5성
    패시브: 사방을 떠다니는 뭉게구름
    - 원소 피해 보너스+12/15/18/21/24%. 일반 공격 명중 시 50%의 확률로 구름의 총애를
      받는다. 15초 내에 주변의 적을 직접 공격하면 공격력 160/200/240/280/320%의 피해를
      준다. 해당 효과는 30초마다 1번 발동한다
    """

    _ELEM_DMG_BONUS = [0.12, 0.15, 0.18, 0.21, 0.24]
    _CLOUD_COEFF    = [1.6, 2, 2.4, 2.8, 3.2]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 3,
            refinement    = refinement,
            sub_stat_type = StatType.ATK_PCT,
        )

    _CLOUD_HIT = "구름의 총애 추가 타격"

    def add_hits(self, hits, wearer) -> None:
        """Phase 1 — 「구름의 총애」 추가 타격을 착용자의 히트로 만든다 (착용자 원소 피해).

        일단 무조건 만들고, 활성화하지 않았다면 apply_passive(Phase 3)가 도로 뺀다 —
        질문은 Phase 3에 모으는 규약이라 여기서 물을 수 없고, 한 번 만들어 둬야 기초
        스탯·부옵션·성유물·세트가 정상적으로 실린다(천공의 검과 같은 꼴). 원소는 착용자의
        원소를 그대로 쓴다 — 천공의 검의 물리 고정과 다른 자리다.
        """
        hits[self._CLOUD_HIT] = SkillHit(
            name       = self._CLOUD_HIT,
            skill_type = SkillType.WEAPON,
            coeff      = self._CLOUD_COEFF[self.refinement - 1],
            element    = wearer.element,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 천공의 두루마리"

        # 효과 1: 원소 피해 보너스 — 「모든 원소」라는 말이 없으므로 착용자 자신의
        # 원소 타입에만 붙는다(안개를 가르는 회광과 같은 구분).
        field = element_dmg_field(wearer.element)
        if field is not None:
            for hit in all_hits[wearer].values():
                hit.add(field, self._ELEM_DMG_BONUS[r], label, note="사방을 떠다니는 뭉게구름")

        # 효과 2: 「구름의 총애」— 일반 공격 명중 시 50% 확률로 얻어 15초 내 적 공격 시
        # 발동, 30초 재발동 제한. 확률·지속 시간·쿨타임 전부 로테이션이 정하므로
        # 발동 여부만 묻는다(천공의 검과 같은 단순화).
        if not ask_bool("[천공의 두루마리] 「구름의 총애」 발동 여부 (일반 공격 명중 50% 확률,"
                        " 15초 내 발동, 30초 재발동 제한)"):
            all_hits[wearer].pop(self._CLOUD_HIT, None)

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # (없음 — 문구 전체가 히트 단가에 반영된다)
