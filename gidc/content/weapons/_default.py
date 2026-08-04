from gidc.core.weapon import Weapon


class DefaultWeapon(Weapon):
    """특성이 미구현된 무기의 fallback — 특성 효과 없음."""

    def apply_passive(self, all_hits, wearer) -> None:
        pass
