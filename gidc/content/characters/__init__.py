from gidc.core.character import Character
from gidc.enums import CharacterTrait, Element
from gidc.enums import WeaponType
from ._default import DefaultCharacter
from . import pyro, hydro, cryo, electro, anemo, geo, dendro

CHARACTER_REGISTRY: dict[str, type[Character]] = {
    "베넷":    pyro.Bennett,
    "니콜":    pyro.Nicole,
    "푸리나":  hydro.Furina,
    "콜롬비나": hydro.Columbina,
    "모나":    hydro.Mona,
    "에스코피에": cryo.Escoffier,
    "스커크":    cryo.Skirk,
    "이네파":  electro.Ineffa,
    "실로닌":  geo.Xilonen,
    "나비아":  geo.Navia,
}


def make_character(
    name:        str,
    hp:          int = 0,
    atk:         int = 0,
    def_:        int = 0,
    element:     Element = Element.PYRO,
    weapon_type: WeaponType | None = None,
    traits:      frozenset[CharacterTrait] | None = None,
    unlockable_traits: frozenset[CharacterTrait] | None = None,
) -> Character:
    cls = CHARACTER_REGISTRY.get(name, DefaultCharacter)
    if cls is DefaultCharacter:
        return DefaultCharacter(hp, atk, def_, element, name, weapon_type,
                                traits, unlockable_traits)
    return cls()
