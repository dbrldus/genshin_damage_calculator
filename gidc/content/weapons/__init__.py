from gidc.enums import WeaponType
from gidc.core.weapon import Weapon, WeaponSubStat

from ._default import DefaultWeapon
from .claymore import AThousandBlazingSuns, Verdict, ATeaspoonOfTranscendence, GestOfTheMightyWolf, FangOfTheMountainKing
from .sword import (
    PeakPatrolSong, SkywardBlade, AquilaFavonia, Azurelight,
    FavoniusSword, CalamityOfEshu,
)
from .polearm import (
    ProspectorsShovel, Deathmatch, DialoguesOfTheDesertSages,
    FracturedHalo, SymphonistOfScents, SkywardSpine,
    BloodsoakedRuins,
    DragonsBane,
    FavoniusLance,
    LumidouceElegy,
    CrimsonMoonsSemblance,
)
from .catalyst import (
    StarcallersWatch, CranesEchoingCall, FavoniusCodex, SacrificialFragments,
    ThrillingTalesOfDragonSlayers,
    AngelosHeptades,
    NocturnesCurtainCall,
    VividNotions,
    NewYearsMorningHibernation,
)

WEAPON_REGISTRY: dict[str, type[Weapon]] = {
    "타오르는 천 개의 태양": AThousandBlazingSuns,
    "판정":               Verdict,
    "바위산을 맴도는 노래": PeakPatrolSong,
    "천공의 검":           SkywardBlade,
    "매의 검":             AquilaFavonia,
    "창백한 섬광":          Azurelight,
    "페보니우스 검":        FavoniusSword,
    "에슈의 재앙":          CalamityOfEshu,
    "채굴의 삽":           ProspectorsShovel,
    "결투의 창":           Deathmatch,
    "위대한 사막 현자의 대답": DialoguesOfTheDesertSages,
    "파멸의 빛고리":        FracturedHalo,
    "맛의 지휘자":          SymphonistOfScents,
    "천공의 마루":          SkywardSpine,
    "별지기의 시선":        StarcallersWatch,
    "학의 여음":           CranesEchoingCall,
    "페보니우스 비전":      FavoniusCodex,
    "제례의 악장":          SacrificialFragments,
    "드래곤 슬레이어 영웅담": ThrillingTalesOfDragonSlayers,
    "일곱빛 계시":           AngelosHeptades,
    "막간의 야상곡":          NocturnesCurtainCall,
    "빛나는 마음":           VividNotions,
    "피로 물든 성":          BloodsoakedRuins,
    "용학살창":             DragonsBane,
    "페보니우스 장창":         FavoniusLance,
    "등방울꽃의 애가":         LumidouceElegy,
    "붉은 달의 형상":         CrimsonMoonsSemblance,
    "나른한 새해":           NewYearsMorningHibernation,
    "초월의 열쇠":           ATeaspoonOfTranscendence,
    "늑대의 무용담":          GestOfTheMightyWolf,
    "산왕의 엄니":           FangOfTheMountainKing,
}


def make_weapon(
    name:        str,
    refinement:  int,
    weapon_type: WeaponType      | None = None,
    base_atk:    int             | None = None,
    sub_stat:    WeaponSubStat   | None = None,
) -> Weapon:
    cls = WEAPON_REGISTRY.get(name)
    if cls is not None:
        return cls(refinement)
    if weapon_type is None or base_atk is None:
        raise ValueError(
            f"'{name}'은 미등록 무기입니다. weapon_type과 base_atk를 직접 지정하세요."
        )
    return DefaultWeapon(weapon_type, base_atk, refinement, sub_stat)
