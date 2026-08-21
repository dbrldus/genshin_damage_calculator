from gidc.core.weapon import Weapon
from gidc.core.profile import add_all_lunar_crit_dmg
from gidc.enums import StatType
from gidc.enums import WeaponType
from gidc.prompt import ask_bool


class NocturnesCurtainCall(Weapon):
    """막간의 야상곡 (Nocturne's Curtain Call) | 법구 | 5성
    패시브: 십자로의 여행 노래
    - HP 최대치가 10/12/14/16/18% 증가한다.
    - 장착 캐릭터가 달빛 반응 발동 또는 적에게 달빛 반응 피해를 줄 시, 장착 캐릭터의 원소
      에너지를 14/15/16/17/18pt 회복하고, 12초 동안 지속되는 「풍요로운 바다의 술」 효과를
      획득한다: HP 최대치가 14/16/18/20/22% 더 증가하고, 달빛 반응의 치명타 피해가
      60/80/100/120/140% 증가한다.
      상술한 효과는 10초마다 최대 1회 발동된다. 장착 캐릭터가 대기 상태일 때도 발동한다.
    """

    _HP_PCT        = [0.10, 0.12, 0.14, 0.16, 0.18]
    _TIDE_HP_PCT   = [0.14, 0.16, 0.18, 0.20, 0.22]
    _TIDE_CRIT_DMG = [0.60, 0.80, 1.00, 1.20, 1.40]

    def __init__(self, refinement: int) -> None:
        super().__init__(
            weapon_type   = WeaponType.CATALYST,
            rarity        = 5,
            tier          = 1,
            refinement    = refinement,
            sub_stat_type = StatType.CRIT_DMG,
        )

    def apply_passive(self, all_hits, wearer) -> None:
        r     = self.refinement - 1
        label = "무기: 막간의 야상곡"
        hits  = all_hits[wearer].values()

        # 효과 1: HP 최대치 — 조건이 없고 착용자에게만 붙는다.
        for hit in hits:
            hit.add("hp_pct", self._HP_PCT[r], label, note="십자로의 여행 노래")

        # 효과 2 「풍요로운 바다의 술」. 트리거가 달빛 반응이지만 파티 구성만으로는 유도할 수
        # 없다 — 달반응이 성립하는 파티라도 로테이션에서 착용자가 실제로 트리거했는지는
        # 다른 문제이고, 12초/10초라는 창도 로테이션 몫이다. 그래서 묻는다.
        # 대기 상태에서도 발동하므로 필드 등장 여부는 묻지 않는다.
        if not ask_bool("[막간의 야상곡] 달빛 반응 발동 후 12초 이내 (풍요로운 바다의 술) 여부"):
            return

        for hit in hits:
            hit.add("hp_pct", self._TIDE_HP_PCT[r], label, note="풍요로운 바다의 술")

            # 「달빛 반응의 치명타 피해」 — 반응을 가리지 않으므로 달반응 3종 전부에 넣는다.
            # 히트 전역 crit_dmg가 아니라 반응 전용 필드로 간다. 전역에 더하면 이 캐릭터의
            # 일반/스킬/폭발 치명타 피해까지 올라가고, 반대로 「달반응 히트에만」 넣는 것은
            # 불가능하다 — 달반응 반응 피해는 SkillHit이 아니라 별도 피해 인스턴스이고
            # 캐리어 히트의 스탯을 읽어 갈 뿐이다(core.profile 주석 참고).
            # 달감전 직접 피해(콜롬비나·이네파)에도 붙는다 — 같은 계열의 기존 필드
            # (lunar_*_bonus, lunar_*_base_dmg_bonus)가 직접/반응 양쪽에 붙는 것과 같다.
            add_all_lunar_crit_dmg(hit, self._TIDE_CRIT_DMG[r], label, note="풍요로운 바다의 술")

    # ── 의도적 미구현 ─────────────────────────────────────────────────────
    # · 원소 에너지 14/15/16/17/18pt 회복 — 로테이션 빈도를 정하는 값이지 히트 단가에
    #   들어갈 항이 없다(이 엔진은 에너지를 모델링하지 않는다).
