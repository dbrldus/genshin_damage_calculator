from gidc.core.weapon import Weapon
from gidc.core.profile import SkillHit, SkillType
from gidc.enums import Element, WeaponType
from gidc.enums import StatType
from gidc.prompt import ask_bool


class SkywardPride(Weapon):
    """천공의 긍지 (Skyward Pride) | 양손검 | 5성
    패시브: 맑은 하늘을 가르는 용의 척추
    - 주는 피해가 8/10/12/14/16% 증가한다.
    - 원소폭발 발동 후: 일반 공격과 강공격 명중 시 진공의 칼날이 발사되어 경로상의 적에게
      공격력 80/100/120/140/160%의 피해를 준다. 지속 시간: 20초, 또는 진공의 칼날 8번
      발사할 때까지.
    """

    _ALL_DMG            = [0.08, 0.1, 0.12, 0.14, 0.16]
    _VACUUM_BLADE_COEFF = [0.8, 1, 1.2, 1.4, 1.6]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CLAYMORE,
            rarity        = 5,
            tier          = 3,
            refinement    = refinement,
            sub_stat_type = StatType.ENERGY_RECHARGE,
        )

    # 추가 타격 히트 이름 — add_hits(Phase 1)가 만들고 apply_passive(Phase 3)가 도로 뺄 수
    # 있어야 하므로 양쪽이 같은 문자열을 봐야 한다.
    _VACUUM_BLADE_HIT = "진공의 칼날 피해"

    def add_hits(self, hits, wearer) -> None:
        """Phase 1 — 진공의 칼날을 착용자의 히트로 만든다.

        일단 **무조건** 만든다. 활성 여부는 유저 입력이고 질문은 Phase 3에 모으는 것이
        이 저장소의 규약이라, 여기서는 물을 수 없기 때문이다. 꺼져 있으면 apply_passive가
        도로 뺀다 — 한 번 만들어 둬야 기초 스탯·부옵션·성유물·세트가 정상적으로 실린다.

        skill_type이 WEAPON인 것이 요점이다. 일반/강공격 명중으로 발동하지만 그 자신은
        일반 공격이 아니라서 「일반 공격 피해 보너스」를 받지 않는다(_SKILL_PREFIX에 없어
        스킬 타입 보너스가 0으로 접힌다).
        """
        hits[self._VACUUM_BLADE_HIT] = SkillHit(
            name       = self._VACUUM_BLADE_HIT,
            skill_type = SkillType.WEAPON,
            coeff      = self._VACUUM_BLADE_COEFF[self.refinement - 1],
            element    = Element.PHYSICAL,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 천공의 긍지"

        # 효과 1: 상시 주는 피해 증가 (착용자) — 조건 없이 항상 붙는다.
        for hit in all_hits[wearer].values():
            hit.add("all_dmg_bonus", self._ALL_DMG[r], label)

        # 효과 2: 원소폭발 발동 후에만 진공의 칼날이 나간다 — 로테이션이 정하므로 묻는다.
        # 꺼져 있으면 Phase 1에서 만들어 둔 히트를 뺀다. 0 계수로 남겨 두면 피해 0짜리
        # 줄이 화면에 남아 「발동했는데 0인가」로 읽힌다.
        if not ask_bool("[천공의 긍지] 진공의 칼날 활성화 여부 (원소폭발 발동 후)"):
            all_hits[wearer].pop(self._VACUUM_BLADE_HIT, None)

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 지속 시간 20초·최대 8회 발사 제한 — 히트 1개가 칼날 1발이다. 몇 발이 로테이션에
    #   들어가는지는 유저가 판단한다(천공의 마루의 확률·쿨 처리와 같은 방침).
