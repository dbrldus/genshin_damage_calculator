from gidc.core.weapon import Weapon, WeaponSubStat
from gidc.enums import WeaponType


class DefaultWeapon(Weapon):
    """특성이 미구현된 무기의 fallback — 특성 효과 없음.

    스케일링 표를 타지 않고 기본 공격력·부옵션을 통째로 받는다. 표에는 (성급, 티어)
    조합만 있고 「어느 무기가 어느 티어인가」는 무기 파일이 들고 있으므로, 미등록 무기는
    티어를 알 길이 없기 때문이다. 캐릭터 쪽 DefaultCharacter가 base_hp/atk/def를
    재정의하는 것과 같은 자리다.

    레벨을 바꿔도 값이 따라 움직이지 않는다 — 넘겨받은 값이 곧 최종값이다. 레벨을 쓰고
    싶으면 무기를 정식으로 등록하는 편이 맞다."""

    def __init__(
        self,
        weapon_type: WeaponType,
        base_atk:    int,
        refinement:  int,
        sub_stat:    WeaponSubStat | None = None,
    ) -> None:
        self._base_atk = base_atk
        self._sub_stat = sub_stat
        # 성급·티어는 스케일링 표를 지나치므로 쓰이지 않는다. 표에 있는 조합이어야
        # 부모의 검증을 통과하므로 가장 흔한 5성 Tier 1을 자리 표시로 둔다.
        super().__init__(weapon_type, rarity=5, tier=1, refinement=refinement)

    @property
    def base_atk(self) -> int:
        return self._base_atk

    @property
    def sub_stat(self) -> WeaponSubStat | None:
        return self._sub_stat

    def apply_passive(self, all_hits, wearer) -> None:
        pass
