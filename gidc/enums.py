"""게임 전반의 열거형과 상수.

원래 GameData / ArtifactData / WeaponData 세 모듈로 나뉘어 있었으나, 셋 다 순수 열거형이고
StatType처럼 성유물·무기·스탯이 함께 쓰는 타입이 ArtifactData에 갇혀 있어 하나로 합쳤다.
"""
from enum import Enum


# ══════════════════════════════════════════════════════════════════════════
#  전투 일반 (구 GameData)
# ══════════════════════════════════════════════════════════════════════════


class Element(Enum):
    PYRO     = "불"
    HYDRO    = "물"
    CRYO     = "얼음"
    ELECTRO  = "번개"
    ANEMO    = "바람"
    GEO      = "바위"
    DENDRO   = "풀"
    PHYSICAL = "물리"


class CharacterTrait(Enum):
    """캐릭터에 붙는 특성 태그. 파티 파생 상태(PartyState)의 판정 재료가 된다."""
    HEXEREI  = "마도"       # 2명 이상 편성 시 「마도·비밀 의식」 획득
    MOONSIGN = "달빛 징조"   # 파티 달빛 징조 레벨에 기여
    # 파티 전원이 물/얼음이고 물·얼음이 각각 최소 1명이면 파티 전원의 원소전투 스킬 레벨 +1
    MARTIAL_INSTRUCTION = "무예 전수"

    # ── 달반응 전환 ───────────────────────────────────────────────────────
    # 달빛 징조가 켜졌다고 감전·결정이 저절로 전환되는 것이 아니다 — 전환은 특정 캐릭터의
    # 킷 효과이고, 그 캐릭터가 파티에 1명 이상 있어야 한다(core.reaction.lunar_candidates).
    # 보유자를 이름 목록으로 어디에 적어두는 대신 캐릭터가 직접 선언한다 — 아래 미구현
    # 캐릭터를 넣을 때 innate_traits에 이 특성을 함께 적으면 판정이 알아서 따라온다.
    LUNAR_CHARGED_CONVERTER     = "달감전 전환"   # 콜롬비나·이네파·플린스(미구현)
    LUNAR_CRYSTALLIZE_CONVERTER = "달결정 전환"   # 콜롬비나·자백(미구현)·린네아(미구현)

    # ── 별 반응 전환 ──────────────────────────────────────────────────────
    # 달반응과 같은 규약이다 — 전환은 특정 캐릭터의 킷 효과이고, 그 캐릭터가 파티에 1명 이상
    # 있어야 한다(core.reaction.stellar_conditions). 두 별 반응의 보유자가 현재 같지만
    # (산드로네·오데트) 특성을 하나로 합치지 않는다 — 한쪽만 전환하는 캐릭터가 나오면
    # 합쳐 둔 특성은 쪼갤 수 없고, 달반응이 이미 반응별로 나눠 둔 선례가 있다.
    STELLAR_CONDUCT_CONVERTER = "별 초전도 전환"   # 산드로네(미구현)·오데트(미구현)
    STELLAR_SWIRL_CONVERTER   = "별 확산 전환"     # 산드로네(미구현)·오데트(미구현)


class MoonsignLevel(Enum):
    NONE     = "없음"
    CRESCENT = "초승"
    FULL     = "보름"


class ReactionType(Enum):
    NONE              = "없음"
    VAPORIZE          = "증발"
    MELT              = "융해"
    OVERLOADED        = "과부하"
    SUPERCONDUCT      = "초전도"
    ELECTROCHARGED    = "감전"
    SWIRL             = "확산"
    SHATTER           = "쇄빙"
    BURNING           = "연소"
    BLOOM             = "개화"
    HYPERBLOOM        = "만개"
    BURGEON           = "발화"
    AGGRAVATE         = "촉진"
    SPREAD            = "발산"
    LUNAR_CHARGED     = "달감전"
    LUNAR_BLOOM       = "달개화"
    LUNAR_CRYSTALLIZE = "달결정"
    # 별 반응. 확산 계열은 STELLAR_SWIRL이다 — 같은 반응의 별 계열 변종이므로 SWIRL과
    # 같은 어휘를 쓴다. 다른 단어를 들여오면 「무엇이 무엇을 대체하는가」
    # (core.reaction._STELLAR_SUPPRESSES)가 이름만 봐서는 안 보인다.
    STELLAR_CONDUCT   = "별 초전도"
    STELLAR_SWIRL     = "별 확산"


class DmgType(Enum):
    NONE           = "none"
    AMPLIFY        = "amplify"
    CATALYZE       = "catalyze"
    TRANSFORMATIVE = "transformative"
    LUNAR_DIRECT   = "lunar_direct"
    LUNAR_REACTION = "lunar_reaction"
    # 별 반응도 직접 피해/반응 피해 두 자리가 있고 **공식은 달반응과 같다**
    # (damage._DISPATCH가 같은 _calc_lunar_* 함수로 보낸다). 그래도 DmgType을 따로 두는
    # 이유는 반응 배율과 기초 피해 증가 필드가 계열마다 다르기 때문이다.
    STELLAR_DIRECT   = "stellar_direct"
    STELLAR_REACTION = "stellar_reaction"


# ══════════════════════════════════════════════════════════════════════════
#  성유물·스탯 (구 ArtifactData)
# ══════════════════════════════════════════════════════════════════════════


class ArtifactSet(Enum):
    # ── 5성 세트 (최신순) ──────────────────────────────────────────
    DISENCHANTMENT_IN_DEEP_SHADOW           = "그림자 속 산산조각 난 꿈"
    CELESTIAL_GIFT                          = "하늘의 은총"
    A_DAY_CARVED_FROM_RISING_WINDS          = "바람이 시작되는 날"
    AUBADE_OF_MORNINGSTAR_AND_MOON          = "샛별과 달의 여명"
    SILKEN_MOONS_SERENADE                   = "달을 엮는 밤노래"
    NIGHT_OF_THE_SKYS_UNVEILING             = "하늘 경계가 드러난 밤"
    FINALE_OF_THE_DEEP_GALLERIES            = "깊은 회랑의 피날레"
    LONG_NIGHTS_OATH                        = "긴 밤의 맹세"
    OBSIDIAN_CODEX                          = "흑요석 비전"
    SCROLL_OF_THE_HERO_OF_CINDER_CITY       = "잿더미성 용사의 두루마리"
    UNFINISHED_REVERIE                      = "미완의 몽상"
    FRAGMENT_OF_HARMONIC_WHIMSY             = "조화로운 공상의 단편"
    NIGHTTIME_WHISPERS_IN_THE_ECHOING_WOODS = "메아리숲의 야화"
    SONG_OF_DAYS_PAST                       = "지난날의 노래"
    GOLDEN_TROUPE                           = "황금 극단"
    MARECHAUSSEE_HUNTER                     = "그림자 사냥꾼"
    VOURKASHAS_GLOW                         = "감로빛 꽃바다"
    NYMPHS_DREAM                            = "님프의 꿈"
    FLOWER_OF_PARADISE_LOST                 = "잃어버린 낙원의 꽃"
    DESERT_PAVILION_CHRONICLE               = "모래 위 누각의 역사"
    GILDED_DREAMS                           = "도금된 꿈"
    DEEPWOOD_MEMORIES                       = "숲의 기억"
    ECHOES_OF_AN_OFFERING                   = "제사의 여운"
    VERMILLION_HEREAFTER                    = "진사 왕생록"
    HUSK_OF_OPULENT_DREAMS                  = "풍요로운 꿈의 껍데기"
    OCEAN_HUED_CLAM                         = "바다에 물든 거대 조개"
    EMBLEM_OF_SEVERED_FATE                  = "절연의 기치"
    SHIMENAWAS_REMINISCENCE                 = "추억의 시메나와"
    PALE_FLAME                              = "창백의 화염"
    TENACITY_OF_THE_MILLELITH               = "견고한 천암"
    HEART_OF_DEPTH                          = "몰락한 마음"
    BLIZZARD_STRAYER                        = "얼음바람 속에서 길잃은 용사"
    NOBLESSE_OBLIGE                         = "옛 왕실의 의식"
    BLOODSTAINED_CHIVALRY                   = "피에 물든 기사도"
    LAVAWALKER                              = "불 위를 걷는 현인"
    CRIMSON_WITCH_OF_FLAMES                 = "불타오르는 화염의 마녀"
    RETRACING_BOLIDE                        = "날아오르는 유성"
    ARCHAIC_PETRA                           = "유구한 반암"
    MAIDEN_BELOVED                          = "사랑받는 소녀"
    VIRIDESCENT_VENERER                     = "청록색 그림자"
    THUNDERSOOTHER                          = "뇌명을 평정한 존자"
    THUNDERING_FURY                         = "번개 같은 분노"
    WANDERERS_TROUPE                        = "대지를 유랑하는 악단"
    GLADIATORS_FINALE                       = "검투사의 피날레"
    # ── 4성 세트 (기도) ────────────────────────────────────────────
    PRAYERS_TO_SPRINGTIME                   = "얼음을 모시는 자"
    PRAYERS_FOR_ILLUMINATION                = "불을 모시는 자"
    PRAYERS_FOR_DESTINY                     = "물을 모시는 자"
    PRAYERS_FOR_WISDOM                      = "뇌명을 모시는 자"
    # ── 4성 세트 (일반) ────────────────────────────────────────────
    SCHOLAR                                 = "학사"
    GAMBLER                                 = "노름꾼"
    MARTIAL_ARTIST                          = "무인"
    BRAVE_HEART                             = "용사의 마음"
    DEFENDERS_WILL                          = "수호자의 마음"
    THE_EXILE                               = "유배자"
    INSTRUCTOR                              = "교관"
    BERSERKER                               = "전투광"
    TINY_MIRACLE                            = "기적"
    RESOLUTION_OF_SOJOURNER                 = "행자의 마음"
    # ── 3성 세트 (일반) ────────────────────────────────────────────
    TRAVELING_DOCTOR                        = "떠돌이 의사"
    LUCKY_DOG                               = "행운아"
    ADVENTURER                              = "모험가"


class ArtifactSlot(Enum):
    FLOWER  = "꽃"    # 주옵션 고정: HP
    FEATHER = "깃털"  # 주옵션 고정: 공격력
    SANDS   = "시계"  # HP%·공격력%·방어력%·원소 마스터리·원소 충전 효율
    GOBLET  = "성배"  # HP%·공격력%·방어력%·원소 마스터리·원소/물리 피해 보너스
    CIRCLET = "왕관"  # HP%·공격력%·방어력%·원소 마스터리·치명타 확률/피해·치유 보너스


class StatType(Enum):
    # 기본 스탯
    HP               = "HP"
    ATK              = "공격력"
    DEF              = "방어력"
    # 퍼센트 스탯
    HP_PCT           = "HP%"
    ATK_PCT          = "공격력%"
    DEF_PCT          = "방어력%"
    # 전투 스탯
    ELEMENTAL_MASTERY = "원소 마스터리"
    ENERGY_RECHARGE  = "원소 충전 효율"
    CRIT_RATE        = "치명타 확률"
    CRIT_DMG         = "치명타 피해"
    HEALING_BONUS    = "치유 보너스"
    # 원소 피해 보너스
    PYRO_DMG         = "불 원소 피해 보너스"
    HYDRO_DMG        = "물 원소 피해 보너스"
    CRYO_DMG         = "얼음 원소 피해 보너스"
    ELECTRO_DMG      = "번개 원소 피해 보너스"
    ANEMO_DMG        = "바람 원소 피해 보너스"
    GEO_DMG          = "바위 원소 피해 보너스"
    DENDRO_DMG       = "풀 원소 피해 보너스"
    PHYSICAL_DMG     = "물리 피해 보너스"


# 게임에서 %로 표시되는 스탯. 이 스탯의 옵션 값은 게임 표기 그대로(치명타 확률 12.4% → 12.4)
# 넣으면 되고, 내부에서 0.01을 곱해 비율로 바꾼다 — Artifact.MainStat/SubStat.scaled 참고.
# HP·공격력·방어력 실수치와 원소 마스터리는 표기 자체가 실수치라 변환하지 않는다.
PERCENT_STAT_TYPES: frozenset[StatType] = frozenset({
    StatType.HP_PCT, StatType.ATK_PCT, StatType.DEF_PCT,
    StatType.ENERGY_RECHARGE, StatType.CRIT_RATE, StatType.CRIT_DMG,
    StatType.HEALING_BONUS,
    StatType.PYRO_DMG, StatType.HYDRO_DMG, StatType.CRYO_DMG,
    StatType.ELECTRO_DMG, StatType.ANEMO_DMG, StatType.GEO_DMG,
    StatType.DENDRO_DMG, StatType.PHYSICAL_DMG,
})

# 게임 표기(%) → 내부 비율 변환 계수
PERCENT_SCALE = 0.01


# ══════════════════════════════════════════════════════════════════════════
#  무기 (구 WeaponData)
# ══════════════════════════════════════════════════════════════════════════


class WeaponType(Enum):
    SWORD    = "한손검"
    CLAYMORE = "양손검"
    POLEARM  = "장병기"
    CATALYST = "법구"
    BOW      = "활"
