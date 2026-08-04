from gidc.core.character import Character
from gidc.core.profile import SkillHit
from gidc.enums import CharacterTrait, Element
from gidc.enums import WeaponType


class DefaultCharacter(Character):
    def __init__(self, hp: int = 0, atk: int = 0, def_: int = 0, element: Element = Element.PYRO,
                 name: str = "", weapon_type: WeaponType | None = None,
                 traits: frozenset[CharacterTrait] | None = None,
                 unlockable_traits: frozenset[CharacterTrait] | None = None) -> None:
        super().__init__()
        self.name              = name or self.name
        self.weapon_type       = weapon_type   # None이면 무기 종류 제한 없음
        self.innate_traits     = frozenset(traits) if traits else frozenset()
        self.unlockable_traits = frozenset(unlockable_traits) if unlockable_traits else frozenset()
        self._hp      = hp
        self._atk     = atk
        self._def     = def_
        self._element = element
        self._custom_hits: list[SkillHit] = []

    @property
    def base_hp(self)  -> int:     return self._hp
    @property
    def base_atk(self) -> int:     return self._atk
    @property
    def base_def(self) -> int:     return self._def
    @property
    def element(self)  -> Element: return self._element

    def build_hits(self) -> dict[str, SkillHit]:
        return {h.name: h for h in self._custom_hits}

    def apply_self_buffs(self, hits: dict[str, SkillHit]) -> None:
        pass

    def apply_dependent_buffs(self, all_hits: dict["Character", dict[str, SkillHit]]) -> None:
        pass
