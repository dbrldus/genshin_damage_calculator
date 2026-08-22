from gidc.core.artifact import Artifact, SubStat
from gidc.enums import ArtifactSet, ArtifactSlot, StatType

from ._default import DefaultArtifact

# ── 4~5성 세트 (최신순) ───────────────────────────────────────────────────────
from .scarlet_proof import ScarletProof
from .disenchantment_in_deep_shadow import DisenchantmentInDeepShadow
from .celestial_gift import CelestialGift
from .a_day_carved_from_rising_winds import ADayCarvedFromRisingWinds
from .aubade_of_morningstar_and_moon import AubadeOfMorningstarAndMoon
from .silken_moons_serenade import SilkenMoonsSerenade
from .night_of_the_skys_unveiling import NightOfTheSkysUnveiling
from .finale_of_the_deep_galleries import FinaleOfTheDeepGalleries
from .long_nights_oath import LongNightsOath
from .obsidian_codex import ObsidianCodex
from .scroll_of_the_hero_of_cinder_city import ScrollOfTheHeroOfCinderCity
from .unfinished_reverie import UnfinishedReverie
from .fragment_of_harmonic_whimsy import FragmentOfHarmonicWhimsy
from .nighttime_whispers_in_the_echoing_woods import NighttimeWhispersInTheEchoingWoods
from .song_of_days_past import SongOfDaysPast
from .golden_troupe import GoldenTroupe
from .marechaussee_hunter import MarechausseeHunter
from .vourkashas_glow import VourkashasGlow
from .nymphs_dream import NymphsDream
from .flower_of_paradise_lost import FlowerOfParadiseLost
from .desert_pavilion_chronicle import DesertPavilionChronicle
from .gilded_dreams import GildedDreams
from .deepwood_memories import DeepwoodMemories
from .echoes_of_an_offering import EchoesOfAnOffering
from .vermillion_hereafter import VermillionHereafter
from .husk_of_opulent_dreams import HuskOfOpulentDreams
from .ocean_hued_clam import OceanHuedClam
from .emblem_of_severed_fate import EmblemOfSeveredFate
from .shimenawas_reminiscence import ShimenawasReminiscence
from .pale_flame import PaleFlame
from .tenacity_of_the_millelith import TenacityOfTheMillelith
from .heart_of_depth import HeartOfDepth
from .blizzard_strayer import BlizzardStrayer
from .noblesse_oblige import NoblesseOblige
from .bloodstained_chivalry import BloodstainedChivalry
from .lavawalker import Lavawalker
from .crimson_witch_of_flames import CrimsonWitchOfFlames
from .retracing_bolide import RetracingBolide
from .archaic_petra import ArchaicPetra
from .maiden_beloved import MaidenBeloved
from .viridescent_venerer import ViridescentVenerer
from .thundersoother import Thundersoother
from .thundering_fury import ThunderingFury
from .wanderers_troupe import WanderersTroupe
from .gladiators_finale import GladiatorsFinale

# ── 3~4성 세트 (기도) ─────────────────────────────────────────────────────────
from .prayers_to_springtime import PrayersToSpringtime
from .prayers_for_illumination import PrayersForIllumination
from .prayers_for_destiny import PrayersForDestiny
from .prayers_for_wisdom import PrayersForWisdom

# ── 3~4성 세트 (일반) ─────────────────────────────────────────────────────────
from .scholar import Scholar
from .gambler import Gambler
from .martial_artist import MartialArtist
from .brave_heart import BraveHeart
from .defenders_will import DefendersWill
from .the_exile import TheExile
from .instructor import Instructor
from .berserker import Berserker
from .tiny_miracle import TinyMiracle
from .resolution_of_sojourner import ResolutionOfSojourner

# ── 1~3성 세트 (일반) ─────────────────────────────────────────────────────────
from .traveling_doctor import TravelingDoctor
from .lucky_dog import LuckyDog
from .adventurer import Adventurer

ARTIFACT_REGISTRY: dict[ArtifactSet, type[Artifact]] = {
    # ── 4~5성 세트 (최신순) ───────────────────────────────────────────────────
    ArtifactSet.SCARLET_PROOF:                           ScarletProof,
    ArtifactSet.DISENCHANTMENT_IN_DEEP_SHADOW:           DisenchantmentInDeepShadow,
    ArtifactSet.CELESTIAL_GIFT:                          CelestialGift,
    ArtifactSet.A_DAY_CARVED_FROM_RISING_WINDS:          ADayCarvedFromRisingWinds,
    ArtifactSet.AUBADE_OF_MORNINGSTAR_AND_MOON:          AubadeOfMorningstarAndMoon,
    ArtifactSet.SILKEN_MOONS_SERENADE:                   SilkenMoonsSerenade,
    ArtifactSet.NIGHT_OF_THE_SKYS_UNVEILING:             NightOfTheSkysUnveiling,
    ArtifactSet.FINALE_OF_THE_DEEP_GALLERIES:            FinaleOfTheDeepGalleries,
    ArtifactSet.LONG_NIGHTS_OATH:                        LongNightsOath,
    ArtifactSet.OBSIDIAN_CODEX:                          ObsidianCodex,
    ArtifactSet.SCROLL_OF_THE_HERO_OF_CINDER_CITY:       ScrollOfTheHeroOfCinderCity,
    ArtifactSet.UNFINISHED_REVERIE:                      UnfinishedReverie,
    ArtifactSet.FRAGMENT_OF_HARMONIC_WHIMSY:             FragmentOfHarmonicWhimsy,
    ArtifactSet.NIGHTTIME_WHISPERS_IN_THE_ECHOING_WOODS: NighttimeWhispersInTheEchoingWoods,
    ArtifactSet.SONG_OF_DAYS_PAST:                       SongOfDaysPast,
    ArtifactSet.GOLDEN_TROUPE:                           GoldenTroupe,
    ArtifactSet.MARECHAUSSEE_HUNTER:                     MarechausseeHunter,
    ArtifactSet.VOURKASHAS_GLOW:                         VourkashasGlow,
    ArtifactSet.NYMPHS_DREAM:                            NymphsDream,
    ArtifactSet.FLOWER_OF_PARADISE_LOST:                 FlowerOfParadiseLost,
    ArtifactSet.DESERT_PAVILION_CHRONICLE:               DesertPavilionChronicle,
    ArtifactSet.GILDED_DREAMS:                           GildedDreams,
    ArtifactSet.DEEPWOOD_MEMORIES:                       DeepwoodMemories,
    ArtifactSet.ECHOES_OF_AN_OFFERING:                   EchoesOfAnOffering,
    ArtifactSet.VERMILLION_HEREAFTER:                    VermillionHereafter,
    ArtifactSet.HUSK_OF_OPULENT_DREAMS:                  HuskOfOpulentDreams,
    ArtifactSet.OCEAN_HUED_CLAM:                         OceanHuedClam,
    ArtifactSet.EMBLEM_OF_SEVERED_FATE:                  EmblemOfSeveredFate,
    ArtifactSet.SHIMENAWAS_REMINISCENCE:                 ShimenawasReminiscence,
    ArtifactSet.PALE_FLAME:                              PaleFlame,
    ArtifactSet.TENACITY_OF_THE_MILLELITH:               TenacityOfTheMillelith,
    ArtifactSet.HEART_OF_DEPTH:                          HeartOfDepth,
    ArtifactSet.BLIZZARD_STRAYER:                        BlizzardStrayer,
    ArtifactSet.NOBLESSE_OBLIGE:                         NoblesseOblige,
    ArtifactSet.BLOODSTAINED_CHIVALRY:                   BloodstainedChivalry,
    ArtifactSet.LAVAWALKER:                              Lavawalker,
    ArtifactSet.CRIMSON_WITCH_OF_FLAMES:                 CrimsonWitchOfFlames,
    ArtifactSet.RETRACING_BOLIDE:                        RetracingBolide,
    ArtifactSet.ARCHAIC_PETRA:                           ArchaicPetra,
    ArtifactSet.MAIDEN_BELOVED:                          MaidenBeloved,
    ArtifactSet.VIRIDESCENT_VENERER:                     ViridescentVenerer,
    ArtifactSet.THUNDERSOOTHER:                          Thundersoother,
    ArtifactSet.THUNDERING_FURY:                         ThunderingFury,
    ArtifactSet.WANDERERS_TROUPE:                        WanderersTroupe,
    ArtifactSet.GLADIATORS_FINALE:                       GladiatorsFinale,
    # ── 3~4성 세트 (기도) ─────────────────────────────────────────────────────
    ArtifactSet.PRAYERS_TO_SPRINGTIME:                   PrayersToSpringtime,
    ArtifactSet.PRAYERS_FOR_ILLUMINATION:                PrayersForIllumination,
    ArtifactSet.PRAYERS_FOR_DESTINY:                     PrayersForDestiny,
    ArtifactSet.PRAYERS_FOR_WISDOM:                      PrayersForWisdom,
    # ── 3~4성 세트 (일반) ─────────────────────────────────────────────────────
    ArtifactSet.SCHOLAR:                                 Scholar,
    ArtifactSet.GAMBLER:                                 Gambler,
    ArtifactSet.MARTIAL_ARTIST:                          MartialArtist,
    ArtifactSet.BRAVE_HEART:                             BraveHeart,
    ArtifactSet.DEFENDERS_WILL:                          DefendersWill,
    ArtifactSet.THE_EXILE:                               TheExile,
    ArtifactSet.INSTRUCTOR:                              Instructor,
    ArtifactSet.BERSERKER:                               Berserker,
    ArtifactSet.TINY_MIRACLE:                            TinyMiracle,
    ArtifactSet.RESOLUTION_OF_SOJOURNER:                 ResolutionOfSojourner,
    # ── 1~3성 세트 (일반) ─────────────────────────────────────────────────────
    ArtifactSet.TRAVELING_DOCTOR:                        TravelingDoctor,
    ArtifactSet.LUCKY_DOG:                               LuckyDog,
    ArtifactSet.ADVENTURER:                              Adventurer,
}


def artifact_class(artifact_set: ArtifactSet) -> type[Artifact]:
    """세트 → 구현 클래스. 세트가 선언한 것(허용 성급 등)을 만들기 전에 읽어야 할 때 쓴다."""
    return ARTIFACT_REGISTRY.get(artifact_set, DefaultArtifact)


def make_artifact(
    artifact_set: ArtifactSet,
    slot: ArtifactSlot,
    main_stat_type: StatType,
    sub_stats: list[SubStat],
    rarity: int | None = None,
    level: int | None = None,
) -> Artifact:
    return artifact_class(artifact_set)(
        artifact_set, slot, main_stat_type, sub_stats, rarity, level
    )
