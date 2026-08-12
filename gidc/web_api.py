"""JS ↔ Python 경계.

브라우저(Pyodide)에서 호출하는 유일한 모듈이다. 엔진은 이 모듈을 모른다.

**반환값은 전부 dict / list / str / float / int / bool / None 뿐이다.**
Pyodide에서 그 밖의 것(클래스 인스턴스, Enum, dataclass, Character를 키로 쓴 dict)은
JS로 넘어갈 때 PyProxy가 되어 수명을 직접 관리해야 한다. 여기서 미리 평탄화해 두면
JS 쪽은 .toJs() 한 번으로 끝난다.

빌드시트 스키마 (party 원소 하나 = 캐릭터 하나):

    { "character": "스커크", "level": 90, "ascension": 6, "constellation": 0,
      "naLevel": 1, "skillLevel": 10, "burstLevel": 8,
      "traits": ["HEXEREI"],
      "weapon": { "name": "에슈의 재앙", "refinement": 5, "level": 90, "ascension": 6 },
      "artifacts": {
        "flower": { "set": "FINALE_OF_THE_DEEP_GALLERIES",
                    "main": { "stat": "HP", "value": 4780 },
                    "subs": [ { "stat": "CRIT_DMG", "value": 19.4 }, ... ] },
        "feather": ..., "sands": ..., "goblet": ..., "circlet": ... } }

슬롯 키는 ArtifactSlot 멤버명의 소문자이고, 그대로 Character의 속성명이기도 하다.

호출 흐름 (답변 수렴 루프):

    answers = {}
    while True:
        out = run_calculation(sheet, answers)
        if not out["pending"]:
            break
        answers = 사용자가_채운다(out["questions"], answers)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from gidc.core.artifact import _INVALID_SUB_STATS, _VALID_MAIN_STATS, MainStat, SubStat
from gidc.core.character import Character
from gidc.core import weapon_scaling
from gidc.core.ascension import MAX_LEVEL, phases_for_level, resolve_phase
from gidc.core.damage import calculate
from gidc.core.enemy import Enemy
from gidc.core.explain import (
    _CRIT_REACTION_FIELDS, _DECLARED_FIELDS, _DEFAULTS, _DMG_POOL_FIELDS, _STAT_TRIPLES,
    explain_hit, explain_transformative,
)
from gidc.core.party import Party
from gidc.core.profile import (
    build_damage_context, build_transformative_context, damage_input_fields,
    set_recording, transformative_input_fields,
)
from gidc.core.reaction import aura_pool, hit_candidates, transformative_candidates
from gidc.enums import (
    ArtifactSet, ArtifactSlot, CharacterTrait, Element, ReactionType, StatType,
)
from gidc.content.artifacts import ARTIFACT_REGISTRY, make_artifact
from gidc.content.characters import CHARACTER_REGISTRY, make_character
from gidc.content.weapons import WEAPON_REGISTRY, make_weapon
from gidc.prompt import MappingSource, using

SLOT_KEYS = [s.name.lower() for s in ArtifactSlot]   # flower feather sands goblet circlet


def _to_py(obj):
    """JS에서 온 값을 파이썬 자료구조로. Pyodide의 JsProxy는 .to_py()를 갖는다."""
    return obj.to_py() if hasattr(obj, "to_py") else obj


def _weapon_names_by_class() -> dict[type, str]:
    return {cls: name for name, cls in WEAPON_REGISTRY.items()}


# ══════════════════════════════════════════════════════════════════════════
#  드롭다운 옵션 — 페이지 로드 시 1회
# ══════════════════════════════════════════════════════════════════════════
def get_registries() -> dict:
    return {
        "characters":   _characters(),
        "weapons":      _weapons(),
        "artifactSets": [{"id": s.name, "label": s.value} for s in ArtifactSet],
        "slots":        [{"key": s.name.lower(), "label": s.value} for s in ArtifactSlot],
        "statTypes":    [{"id": s.name, "label": s.value} for s in StatType],
        # 부위별 허용 주옵션 / 부옵션 — 엔진의 검증 테이블을 그대로 노출한다.
        "validMainStats": {
            slot.name.lower(): sorted(s.name for s in stats)
            for slot, stats in _VALID_MAIN_STATS.items()
        },
        "validSubStats": sorted(s.name for s in StatType if s not in _INVALID_SUB_STATS),
        # 레벨 → 고를 수 있는 돌파 단계. 상한 레벨(20/40/50/60/70/80)만 둘이고
        # 나머지는 하나다. 규칙을 JS가 베껴 쓰지 않도록 표를 통째로 넘긴다.
        "ascensionPhases": {
            str(lv): list(phases_for_level(lv)) for lv in range(1, MAX_LEVEL + 1)
        },
        "maxLevel":     MAX_LEVEL,
        # 손으로 올릴 수 있는 특성 레벨의 상한. 명함 상승분은 이 위에 얹힌다.
        "maxTalentLevel": Character.MAX_TALENT_LEVEL,
        # 무기 레벨 규칙은 성급으로 갈린다(1·2성만 Lv.70/4돌파에서 끝난다). 그래서
        # 캐릭터처럼 표 하나가 아니라 성급별로 나눠 넘긴다.
        "weaponLevels": _weapon_levels(),
        # 반응 목록은 여기서 내보내지 않는다 — 고를 수 있는 반응은 히트 원소와 파티 구성에
        # 따라 다르고, 전체 목록을 주면 불가능한 조합까지 고를 수 있다는 뜻이 된다.
        # 히트별 후보는 run_calculation의 damage[].hits[].candidates로 온다.
        "traits":       [{"id": t.name, "label": t.value} for t in CharacterTrait],
        "counts": {
            "characters":   len(CHARACTER_REGISTRY),
            "weapons":      len(WEAPON_REGISTRY),
            "artifactSets": len(ARTIFACT_REGISTRY),
        },
    }


def _characters() -> list[dict]:
    """캐릭터별 원소·성급·장착 가능 무기 종류와 획득 가능 특성.

    element만 프로퍼티라 인스턴스가 필요하다(_weapons도 같은 이유로 하나 만든다).
    빈 캐릭터를 만드는 것은 값싸고 부작용이 없다 — 패시브는 돌지 않는다."""
    out = []
    for name, cls in sorted(CHARACTER_REGISTRY.items()):
        out.append({
            "name":       name,
            "element":    cls().element.value,
            "rarity":     cls.rarity,
            "weaponType": cls.weapon_type.name if cls.weapon_type else None,
            "unlockableTraits": sorted(t.name for t in cls.unlockable_traits),
            # 어느 명함이 어느 특성을 올리는가(0이면 안 올린다). 캐릭터마다 갈린다 —
            # 모나는 C5가 스킬·C3가 폭발, 나비아는 그 반대다. 화면이 특성 입력 옆에
            # 「+3」을 적으려면 이 표가 필요하고, 규칙을 JS가 베껴 두면 조용히 어긋난다.
            "talentUp": {
                "na":    cls.NA_LEVEL_UP_CONSTELLATION,
                "skill": cls.SKILL_LEVEL_UP_CONSTELLATION,
                "burst": cls.BURST_LEVEL_UP_CONSTELLATION,
                "step":  cls.CONSTELLATION_LEVEL_UP,
            },
        })
    return out


def _weapons() -> list[dict]:
    """무기 종류는 인스턴스 속성이라 재련 1로 한 번 만들어 읽는다(패시브는 돌지 않는다).

    baseAtk는 만렙 기준이고 **고를 때 알아보라고 보여주는 값**이라 게임 화면처럼
    반올림한다 — 계산에 쓰이는 것은 표에서 나온 소수(541.83…)다."""
    out = []
    for name, cls in sorted(WEAPON_REGISTRY.items()):
        w = cls(1)
        out.append({"name": name, "type": w.weapon_type.name,
                    "rarity": w.rarity, "baseAtk": round(w.base_atk)})
    return out


def _weapon_levels() -> dict:
    """성급 → {최대 레벨, 레벨별 고를 수 있는 돌파 단계}.

    무기도 캐릭터와 같이 상한 레벨(20/40/50/60/70/80)에서 돌파 전/후 두 상태가 모두
    유효하고 기본 공격력이 다르다. 다른 점은 1·2성이 Lv.70 4돌파에서 끝난다는 것뿐이라
    표를 성급으로 한 겹 더 나눈다. 규칙을 JS가 베껴 쓰지 않도록 표를 통째로 넘긴다."""
    out = {}
    for rarity in weapon_scaling.rarities():
        top = weapon_scaling.max_level(rarity)
        out[str(rarity)] = {
            "maxLevel": top,
            "phases": {str(lv): list(weapon_scaling.phases_for_level(rarity, lv))
                       for lv in range(1, top + 1)},
        }
    return out


# ══════════════════════════════════════════════════════════════════════════
#  빌드시트 ↔ Character
# ══════════════════════════════════════════════════════════════════════════
def blank_sheet(name: str) -> dict:
    """등록된 캐릭터 하나를 맨몸 빌드시트로 — 무기도 성유물도 없는 출발점.

    화면이 캐릭터를 얻는 유일한 경로다. 파티에 넣을 때도, 슬롯의 캐릭터를 바꿀 때도
    여기서 시작해 사용자가 직접 채운다.

    기본값(레벨·돌파·명함·특성 레벨)을 여기 적지 않고 char_from_spec에 이름만 넘겨
    받아 온다 — 같은 기본값이 두 군데에 적히면 조용히 어긋난다."""
    return char_to_spec(char_from_spec({"character": name}))


def char_to_spec(char) -> dict:
    weapon_names = _weapon_names_by_class()
    w = char.weapon
    return {
        "character":     char.name,
        "level":         char.level,
        "ascension":     char.ascension,
        "constellation": char.constellation,
        "naLevel":       char.na_level,
        "skillLevel":    char.skill_level,
        "burstLevel":    char.burst_level,
        "traits":        sorted(t.name for t in (char.traits - char.innate_traits)),
        "weapon": None if w is None else {
            "name":       weapon_names.get(type(w), ""),
            "refinement": w.refinement,
            "level":      w.level,
            "ascension":  w.ascension,
        },
        "artifacts": {
            key: _artifact_to_spec(getattr(char, key)) for key in SLOT_KEYS
        },
    }


def _artifact_to_spec(art) -> dict | None:
    if art is None:
        return None
    return {
        "set":  art.artifact_set.name,
        "main": {"stat": art.main_stat.stat_type.name, "value": art.main_stat.value},
        "subs": [{"stat": s.stat_type.name, "value": s.value} for s in art.sub_stats],
    }


def char_from_spec(spec: dict):
    """빌드시트 한 명분으로 새 Character를 만든다.

    검증은 엔진이 이미 갖고 있다 — 슬롯별 허용 주옵션, 부옵션 4개·중복 금지
    (core/artifact.py), 무기 종류 (core/character.py). 여기서는 ValueError를
    그대로 올려 보내고 run_calculation이 필드 에러로 바꾼다."""
    # make_character는 미등록 이름을 DefaultCharacter로 폴백한다(커스텀 캐릭터용 경로).
    # 웹에서는 드롭다운으로만 고르므로 그 폴백이 도움이 안 되고, 히트가 0개라
    # 조용히 빈 결과가 나온다. 여기서 명시적으로 막는다.
    if spec["character"] not in CHARACTER_REGISTRY:
        raise ValueError(
            f"등록되지 않은 캐릭터 '{spec['character']}'. "
            f"사용 가능: {sorted(CHARACTER_REGISTRY)}"
        )

    char = make_character(name=spec["character"])
    char.level         = int(spec.get("level", 90))
    # 돌파 단계는 상한 레벨에서만 두 갈래라 레벨만으로는 정해지지 않는다. 값이 없으면
    # 그 레벨의 기본값(돌파한 쪽)을 쓰고, 짝이 안 맞으면 ValueError로 올라간다.
    # 이 필드가 없던 시절의 빌드 JSON도 그대로 읽힌다 — Lv.90이면 예전과 같은 6돌파다.
    asc = spec.get("ascension")
    char.ascension     = resolve_phase(char.level, None if asc is None else int(asc))
    char.constellation = int(spec.get("constellation", 0))
    char.na_level      = int(spec.get("naLevel", 1))
    char.skill_level   = int(spec.get("skillLevel", 1))
    char.burst_level   = int(spec.get("burstLevel", 1))

    for trait_name in spec.get("traits") or []:
        char.unlock_trait(CharacterTrait[trait_name])

    w = spec.get("weapon")
    if w and w.get("name"):
        weapon = make_weapon(name=w["name"], refinement=int(w.get("refinement", 1)))
        # 무기 레벨·돌파도 캐릭터와 같은 규칙이다. 값이 없으면 만렙 그대로 둔다 —
        # 이 필드가 없던 시절의 빌드 JSON이 예전과 똑같이 읽힌다.
        if w.get("level") is not None:
            weapon.level = int(w["level"])
        phase = w.get("ascension")
        weapon.ascension = weapon_scaling.resolve_phase(
            weapon.rarity, weapon.level, None if phase is None else int(phase)
        )
        char.weapon = weapon

    for key, art in (spec.get("artifacts") or {}).items():
        if art:
            setattr(char, key, _artifact_from_spec(key, art))
    return char


def _artifact_from_spec(slot_key: str, spec: dict):
    return make_artifact(
        artifact_set = ArtifactSet[spec["set"]],
        slot         = ArtifactSlot[slot_key.upper()],
        main_stat    = MainStat(StatType[spec["main"]["stat"]], float(spec["main"]["value"])),
        sub_stats    = [SubStat(StatType[s["stat"]], float(s["value"]))
                        for s in spec.get("subs") or []],
    )


# ══════════════════════════════════════════════════════════════════════════
#  빌드 JSON 주고받기 (캐릭터 한 명분)
# ══════════════════════════════════════════════════════════════════════════
# 공유 형식은 위 빌드시트 스키마에 봉투만 씌운 것이다 — 내보내기 전용 스키마를 따로
# 만들면 캐릭터에 필드가 늘 때마다 조용히 어긋난다. 봉투가 하는 일은 둘뿐이다.
# 남의 JSON인지 구분하고(format), 나중에 스키마가 바뀌었을 때 알아채는 것(version).
#
#     { "format": "gidc.build", "version": 1, "scope": "character",
#       "exportedAt": "2026-08-05T12:34:56+00:00",
#       "build": { "character": "스커크", ... } }        ← char_to_spec 그대로
#
# 파티 전체가 아니라 한 명분인 이유: 상황 질문 답변(answers)은 질문 ID가
# (호출 지점, 같은 지점 반복 횟수)라 파티 구성과 엔진 소스 줄 번호에 묶여 있어
# 밖으로 들고 나갈 수 없다. 빌드만 오간다.
BUILD_FORMAT  = "gidc.build"
BUILD_VERSION = 1


def export_build(spec) -> str:
    """캐릭터 한 명의 빌드시트를 공유용 JSON 문자열로.

    내보내기 전에 Character로 한 번 조립했다가 다시 편다(왕복). 그러면 엔진의 검증이
    그대로 걸리고 화면이 들고 있던 군더더기가 떨어져 나가, **내보낸 JSON은 반드시 다시
    읽힌다**. 빌드가 잘못돼 있으면 ValueError가 그대로 올라간다(UI가 보여준다)."""
    return json.dumps(
        {
            "format":     BUILD_FORMAT,
            "version":    BUILD_VERSION,
            "scope":      "character",
            "exportedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "build":      char_to_spec(char_from_spec(_to_py(spec))),
        },
        ensure_ascii=False, indent=2,
    )


def import_build(text: str) -> dict:
    """공유 JSON을 빌드시트 한 명분으로. 실패해도 예외 대신 errors를 채워 돌려준다.

    받아 주는 것 — 손으로 만든 JSON도 웬만하면 읽히게 한다:
      · export_build가 만든 봉투     {"format": …, "build": {…}}
      · 파티 형식                    {"party": [{…}, …]}     → 첫 명만 (나머지는 warning)
      · 빌드시트 하나만 그대로       {"character": "스커크", …}

    돌려주는 build는 export_build와 같은 왕복을 거친 값이라, 받은 쪽에서 곧바로
    party 슬롯에 꽂아도 계산이 된다."""
    warnings: list[str] = []

    try:
        data = json.loads(text)
    except (TypeError, ValueError) as e:
        return _import_failed(f"JSON을 읽지 못했습니다: {e}")
    if not isinstance(data, dict):
        return _import_failed("빌드 JSON은 객체({ … })여야 합니다.")

    fmt = data.get("format")
    if fmt is not None and fmt != BUILD_FORMAT:
        return _import_failed(f"이 계산기의 빌드 JSON이 아닙니다 (format={fmt!r}).")

    version = data.get("version", BUILD_VERSION)
    if isinstance(version, int) and version > BUILD_VERSION:
        return _import_failed(
            f"더 새로운 형식(v{version})의 빌드 JSON입니다 — "
            f"이 계산기는 v{BUILD_VERSION}까지 읽습니다."
        )

    spec = data.get("build")
    if spec is None:
        party = data.get("party")
        if isinstance(party, list) and party:
            spec = party[0]
            if len(party) > 1:
                first = spec.get("character", "첫 번째") if isinstance(spec, dict) else "첫 번째"
                warnings.append(
                    f"파티 {len(party)}명이 들어 있어 {first} 한 명만 가져왔습니다."
                )
        elif "character" in data:
            spec = data
    if not isinstance(spec, dict):
        return _import_failed("빌드 내용을 찾지 못했습니다 (build / party / character 없음).")

    try:
        build = char_to_spec(char_from_spec(spec))
    except (ValueError, KeyError, TypeError) as e:
        return _import_failed(_import_error(e), warnings)

    return {"build": build, "errors": [], "warnings": warnings}


def _import_failed(message: str, warnings: list[str] | None = None) -> dict:
    return {"build": None, "errors": [message], "warnings": warnings or []}


def _import_error(e: Exception) -> str:
    """엔진 예외를 붙여넣은 사람이 고칠 수 있는 문장으로. KeyError는 str()이
    따옴표 친 이름 하나뿐이라 그대로 보여주면 무슨 말인지 알 수 없다."""
    if isinstance(e, KeyError):
        return (f"알 수 없는 이름입니다: {e.args[0]!r} — 캐릭터·무기·성유물 세트·"
                f"스탯 이름을 확인하세요 (표시 라벨이 아니라 영문 코드로 적습니다).")
    if isinstance(e, TypeError):
        return f"값의 형태가 맞지 않습니다: {e}"
    return str(e)


def _members_from_sheet(sheet: dict) -> tuple[list, list[dict]]:
    """파티를 만든다. 캐릭터 하나가 실패해도 나머지 오류를 함께 모아 돌려준다."""
    members, errors = [], []
    for i, entry in enumerate(sheet.get("party") or []):
        # 빌드시트(dict)만 받는다. 예전에는 문자열을 프리셋 이름으로도 받았지만 프리셋은
        # 엔진에서 빠졌다 — 그대로 두면 char_from_spec 안에서 TypeError로 터진다.
        if not isinstance(entry, dict):
            errors.append({"index": i, "character": f"#{i + 1}",
                           "message": "파티 원소는 빌드시트(객체)여야 합니다."})
            continue
        try:
            members.append(char_from_spec(entry))
        except (ValueError, KeyError) as e:
            errors.append({"index": i, "character": entry.get("character", f"#{i + 1}"),
                           "message": str(e)})
    return members, errors


# ══════════════════════════════════════════════════════════════════════════
#  계산
# ══════════════════════════════════════════════════════════════════════════
def run_calculation(sheet, answers=None) -> dict:
    """빌드시트와 답변 맵으로 계산한다.

    pending 이 비어 있지 않아도 stats/damage 는 채워서 돌려준다 — 미답 질문은
    중립 기본값으로 계산되므로 화면을 비워두지 않아도 된다.
    빌드가 잘못되면 예외 대신 errors 를 채워 돌려준다(UI가 폼 에러로 표시).
    """
    sheet   = _to_py(sheet) or {}
    answers = _to_py(answers) or {}

    members, errors = _members_from_sheet(sheet)
    if errors or not members:
        return _empty(errors)

    settings = sheet.get("settings") or {}
    # 히트 설명이든 반응 설명이든 버프 기여 원장이 있어야 한다. 둘 다 아니면 끈다 —
    # 기록은 계산을 느리게 만들고, 화면은 누를 때만 켠다.
    set_recording(bool(settings.get("explain") or settings.get("explainReaction")))

    source = MappingSource(answers)
    try:
        with using(source):
            all_hits = Party(*members).build_profiles()
    except (ValueError, AssertionError) as e:
        return _empty([{"index": -1, "character": "", "message": str(e)}])

    enemy = Enemy(level=int((sheet.get("enemy") or {}).get("level", 90)))
    # 반응은 히트마다 다르다 — {캐릭터: {히트: 반응}}. 전역 스위치는 얼음 히트에 증발
    # 2.0배가 붙는 식으로 조용히 틀리므로 두지 않는다(core.reaction 참고).
    hit_reactions = settings.get("hitReactions") or {}
    targets       = set(settings.get("targets") or [])

    return {
        "stats":   _stats(all_hits),
        "damage":  _damage(all_hits, enemy, members, hit_reactions, targets),
        "explain": _explain(all_hits, enemy, members, hit_reactions, targets,
                            settings.get("explain"), settings.get("explainReaction")),
        "questions": [q.to_dict() for q in source.asked],
        "pending":   [q.id for q in source.pending],
        "stale":     source.stale,
        "errors":    [],
    }


def _empty(errors: list[dict]) -> dict:
    return {"stats": [], "damage": [], "explain": None,
            "questions": [], "pending": [], "stale": [], "errors": errors}


def _stats(all_hits) -> list[dict]:
    """캐릭터별 스탯 시트. Character 키를 이름 문자열로 편다."""
    out = []
    for char, hits in all_hits.items():
        if not hits:
            continue
        h = next(iter(hits.values()))
        out.append({
            "name":           char.name,
            "element":        char.element.value,
            "atk":            h.atk_final,
            "hp":             h.hp_final,
            "def":            h.def_final,
            "critRate":       h.crit_rate,
            "critDmg":        h.crit_dmg,
            "em":             h.elemental_mastery,
            "energyRecharge": h.energy_recharge,
        })
    return out


# 방어력 배율과 반응 레벨 배율은 **때리는 캐릭터 자신의 레벨**로 정해진다. 파티에
# 레벨이 섞여 있으면(Lv.80 시틀라리 + Lv.90 딜러) 한 값으로 뭉뚱그릴 수 없고, Lv.80을
# 90으로 계산하면 방어력 배율이 0.4865 대신 0.5가 되어 피해가 2.78% 부풀려진다.
def _damage(all_hits, enemy, members, hit_reactions, targets) -> list[dict]:
    """캐릭터마다 블록 하나. 히트(직접 피해)와 반응(격변 1회)을 나눠 담는다.

    둘은 열의 의미가 다르다 — 격변은 계수도 스탯도 %피해 보너스도 타지 않고, 반응 전용
    치명타가 없으면 비크리와 크리가 같은 값이 된다. 그래서 한 표에 섞지 않는다.
    """
    out = []
    for char, hits in all_hits.items():
        if targets and char.name not in targets:
            continue
        aura     = aura_pool(members, char)
        selected = hit_reactions.get(char.name) or {}

        hit_rows = []
        for hit in hits.values():
            candidates = _hit_candidates(hit, aura)
            reaction   = _selected_reaction(selected.get(hit.name), candidates)
            ctx = build_damage_context(hit, enemy,
                                       reaction_type=reaction, char_level=char.level)
            r = calculate(ctx)
            hit_rows.append({
                "hit":        hit.name,
                "candidates": [{"id": c.name, "label": c.value} for c in candidates],
                "reaction":   reaction.name,
                "nonCrit":    r.non_crit,
                "crit":       r.crit,
                "expected":   r.expected,
            })

        # 격변은 「평타로 낸 과부하」와 「폭발로 낸 과부하」가 따로 있지 않다 — 트리거
        # 캐릭터의 EM만 걸리므로 히트 루프 바깥에서 캐리어 하나를 잡고 반응만 돈다.
        carrier = next(iter(hits.values()), None)
        reaction_rows = []
        if carrier is not None:
            for reaction, element in transformative_candidates(char.element, aura):
                ctx = build_transformative_context(
                    carrier, enemy,
                    reaction=reaction, element=element, char_level=char.level,
                )
                r = calculate(ctx)
                reaction_rows.append({
                    "reaction": reaction.name,
                    "label":    reaction.value,
                    "element":  element.value,
                    "nonCrit":  r.non_crit,
                    "crit":     r.crit,
                    "expected": r.expected,
                })

        out.append({"char": char.name, "hits": hit_rows, "reactions": reaction_rows})
    return out


def _hit_candidates(hit, aura) -> tuple:
    """이 히트에 유저가 고를 수 있는 반응. 내재 반응을 선언한 히트는 후보가 없다.

    이네파의 달감전 피해처럼 히트가 반응을 내장한 경우 resolve_reaction이 바깥에서 넘긴
    반응을 무시하므로, 버튼을 내면 눌러도 숫자가 안 바뀌어 화면이 거짓말을 하게 된다.
    """
    if hit.reaction_type is not ReactionType.NONE:
        return ()
    return hit_candidates(hit.element, aura)


def _selected_reaction(name, candidates) -> ReactionType:
    """저장된 선택이 **지금도 가능한** 반응일 때만 받아들인다.

    파티를 바꿔 증발이 불가능해졌는데 예전 선택이 남아 있으면 조용히 틀린 숫자가 나온다.
    화면이 선택을 비워 주더라도 정확성은 엔진이 책임진다.
    """
    if not name:
        return ReactionType.NONE
    for c in candidates:
        if c.name == name:
            return c
    return ReactionType.NONE


# 묶음 구성은 explain.py의 텍스트 렌더러가 쓰는 것과 같은 목록이다.
# 선언값(계수)이 맨 앞인 건 공식 트레이스도 coeff부터 시작하기 때문이다.
_EXPLAIN_GROUPS = [
    ("히트 선언값",         _DECLARED_FIELDS),
    ("피해 보너스 풀",      _DMG_POOL_FIELDS),
    ("치명타 / 반응 / 기타", _CRIT_REACTION_FIELDS),
]
_DECLARED    = set(_DECLARED_FIELDS)
_STAT_PARTS  = ("base", "pct", "flat")

# 공식 트레이스를 '사람이 읽는 순서'로 세운다 — 기초 피해 재료(스탯·계수·고정 추가)를
# 모아 base_dmg 를 만들고, 거기에 배율(피해량 증가 → 반응 → 치명타 → 내성 → 방어력)을
# 차례로 곱한다. damage.py의 _t() 호출 순서는 계산 순서라 반응 경로마다 다르다.
# 여기 없는 term은 순서 맨 뒤에 원래 차례대로 붙는다 — 새 term이 조용히 사라지지 않게.
_FORMULA_ORDER = [
    # ── 기초 피해 재료 ──
    ("stat",                     "스탯"),
    ("coeff",                    "계수"),
    ("coeff_amp",                "계수 증폭"),
    ("lv_mult",                  "레벨 배율"),
    ("1+lunar_base",             "달반응 기초 피해 증가"),
    ("additive_flat(촉진/발산)",  "촉진/발산 가산"),
    ("flat_dmg_bonus",           "고정 피해 추가"),
    ("base_dmg",                 "기초 피해"),
    # ── 여기에 곱해지는 배율 ──
    ("1+dmg_bonus",              "피해량 증가"),
    ("reaction_mult",            "반응 배율"),
    ("em_bonus",                 "원소 마스터리 보너스"),
    ("reaction_bonus",           "반응 피해 보너스"),
    ("1+em+reaction",            "원마 + 반응 보너스"),
    ("amplify_mult",             "증폭 배율"),
    ("crit_mult",                "치명타 배율"),
    ("res_mult",                 "내성 배율"),
    ("def_mult",                 "방어력 배율"),
    ("elevation",                "고저차 배율"),
    # ── 결과 ──
    ("non_crit",                 "비크리"),
    ("crit",                     "크리"),
    ("expected",                 "기댓값"),
]
# 격변은 항의 역할이 뒤집힌다 — 반응 배율·레벨 배율·원마 보너스가 기초 피해에 곱해지는
# 배율이 아니라 **기초 피해를 만드는 재료**다(_calc_transformative). 위 순서를 그대로 쓰면
# 「기초 피해 5,349 → 반응 배율 2.75」로 찍혀 곱하면 안 되는 것을 곱하라고 읽힌다.
# 실제로는 2.75 × 1446.85 × (1 + 0.3444) = 5,349 다. 라벨은 위 표를 그대로 쓰므로
# 여기는 term 만 세운다.
_FORMULA_ORDER_TRANSFORMATIVE = [
    # ── 기초 피해 재료 ──
    "reaction_mult", "lv_mult", "em_bonus", "reaction_bonus", "flat_dmg_bonus", "base_dmg",
    # ── 여기에 곱해지는 배율 ──
    "crit_mult", "res_mult",
    # ── 결과 ──
    "non_crit", "crit", "expected",
]

# (1+피해량증가) × 방어 × 내성을 한 번에 곱하려고 코드가 미리 뭉쳐 둔 중간값이다.
# 게임 공식에 있는 항이 아니고, 곱해진 셋이 이미 따로 나오므로 화면에서는 뺀다.
_FORMULA_HIDDEN = {"combined_mult"}
_STAT_FIELDS = {f"{pre}_{tag}" for _, pre in _STAT_TRIPLES for tag in _STAT_PARTS}


def _explain(all_hits, enemy, members, hit_reactions, targets,
             hit_name, reaction_spec) -> dict | None:
    """버프 귀속. Explain은 이미 구조화돼 있어 그대로 편다 (to_text()는 쓰지 않는다).

    화면 구성(스탯 조립 / 보너스 풀 / 치명타·반응 / 공식)까지 여기서 짜 준다.
    어떤 필드가 어느 묶음인지는 explain.py가 이미 알고 있고, JS가 그 목록을
    베껴 들고 있으면 필드가 늘 때마다 조용히 어긋난다.

    설명 대상은 데미지 화면의 두 표에 하나씩 대응한다 — 히트 표는 hit_name(히트 이름),
    반응 표는 reaction_spec({char, reaction, element})이다. 반응 쪽이 원소까지 받는 이유는
    확산이 피해 원소별로 네 행이라 반응 이름만으로는 행이 특정되지 않기 때문이다."""
    if reaction_spec:
        return _explain_reaction(all_hits, enemy, members, targets, reaction_spec)
    if not hit_name:
        return None
    for char, hits in all_hits.items():
        if targets and char.name not in targets:
            continue
        hit = hits.get(hit_name)
        if hit is None:
            continue
        # 표에 보이는 그 숫자를 설명해야 하므로 반응도 _damage와 같은 규칙으로 정한다.
        reaction = _selected_reaction(
            (hit_reactions.get(char.name) or {}).get(hit_name),
            _hit_candidates(hit, aura_pool(members, char)),
        )
        ex = explain_hit(hit, enemy=enemy, reaction_type=reaction, char_level=char.level)
        # 이 히트가 실제로 읽는 필드. 나머지는 값이 붙어 있어도 이 숫자와 무관하다
        # — 화면은 그것을 접어 둔다.
        applied = damage_input_fields(hit, reaction_type=reaction)
        return _explain_payload(
            ex, applied,
            char = char.name,
            kind = "hit",
            # 왜 어떤 보너스가 안 걸리는지는 결국 이 둘이 답이다(원소 없는 평타 = 물리).
            element    = (hit.element or Element.PHYSICAL).value,
            skill_type = hit.skill_type.value,
        )
    return None


def _explain_reaction(all_hits, enemy, members, targets, spec) -> dict | None:
    """격변 반응 1회의 설명. 캐리어 히트 하나를 잡아 explain_transformative에 넘긴다.

    _damage의 reaction_rows와 **같은 재료로 같은 숫자**가 나와야 한다 — 표에 없는 숫자를
    설명하는 창이 제일 나쁘다. 그래서 캐리어도(첫 히트), 후보 유도도(파티 원소) 그쪽과 같다.
    """
    name    = spec.get("char")
    reaction_name = spec.get("reaction")
    element_value = spec.get("element")
    if not (reaction_name and element_value):
        return None

    for char, hits in all_hits.items():
        if targets and char.name not in targets:
            continue
        if name and char.name != name:
            continue
        carrier = next(iter(hits.values()), None)
        if carrier is None:
            continue

        # 지금 이 파티에서 **실제로 가능한** 반응일 때만 설명한다. 히트 쪽
        # _selected_reaction과 같은 이유다 — 파티를 바꿔 불가능해진 선택이 화면에 남아
        # 있으면 조용히 틀린 숫자를 진짜인 양 설명하게 된다.
        aura = aura_pool(members, char)
        for reaction, element in transformative_candidates(char.element, aura):
            if reaction.name != reaction_name or element.value != element_value:
                continue
            ex = explain_transformative(
                carrier, enemy=enemy,
                reaction=reaction, element=element, char_level=char.level,
            )
            applied = transformative_input_fields(reaction, element)
            return _explain_payload(
                ex, applied,
                char = char.name,
                kind = "reaction",
                # 피해 원소는 반응이 정한다 — 캐리어의 원소가 아니다.
                element    = element.value,
                # 격변에 스킬 종류는 없다. 대신 버프 원장을 어느 히트에서 읽었는지 밝힌다
                # — 스탯 시트가 아니라 히트에 걸린 값이라 출처를 감추면 안 된다.
                skill_type = None,
                carrier    = carrier.name,
            )
    return None


def _explain_payload(ex, applied, *, char, kind, element, skill_type,
                     carrier=None) -> dict:
    """히트 설명과 반응 설명이 같은 모양을 내도록 묶는다 — 화면 렌더러가 하나뿐이다."""
    order = _FORMULA_ORDER_TRANSFORMATIVE if kind == "reaction" else None
    return {
        "char":      char,
        "kind":      kind,
        "hit":       ex.name,
        "element":   element,
        "skillType": skill_type,
        "carrier":   carrier,
        "result":  {"nonCrit": ex.result.non_crit, "crit": ex.result.crit,
                    "expected": ex.result.expected},
        "stats":   _explain_stats(ex, applied),
        "groups":  _explain_groups(ex, applied),
        "formula": _explain_formula(ex.formula, order),
    }


def _explain_formula(steps, order=None) -> list[dict]:
    """공식 트레이스를 화면 순서로 세우고 한국어 이름을 붙인다 (원래 term도 같이 보낸다).

    order는 term 목록이며 비우면 직접 피해 순서(_FORMULA_ORDER)를 쓴다. 라벨은 언제나
    _FORMULA_ORDER에서 온다 — 경로마다 순서는 달라도 같은 항은 같은 이름이어야 한다."""
    terms = order if order is not None else [t for t, _ in _FORMULA_ORDER]
    rank  = {term: i for i, term in enumerate(terms)}
    label = dict(_FORMULA_ORDER)
    kept  = [s for s in steps if s["term"] not in _FORMULA_HIDDEN]
    # 안정 정렬이라 모르는 term끼리는 계산 순서를 그대로 지킨 채 맨 뒤로 간다.
    kept.sort(key=lambda s: rank.get(s["term"], len(rank)))
    return [{"term":  s["term"], "label": label.get(s["term"], s["term"]),
             "value": s["value"], "note":  s["note"]} for s in kept]


def _field_breakdown(fb, applied: frozenset[str]) -> dict:
    """declared=True면 기록되지 않은 나머지가 '미계측'이 아니라 히트가 들고 나온 선언값이다.
    applied=False면 값은 붙어 있으나 이 히트의 계산에는 안 들어간다."""
    return {"field": fb.field, "total": fb.total, "baseline": fb.baseline,
            "remainder": fb.remainder, "parts": list(fb.parts),
            "declared": fb.field in _DECLARED,
            "applied":  fb.field in applied}


def _explain_stats(ex, applied: frozenset[str]) -> list[dict]:
    """스탯 조립 — final = base × (1 + pct) + flat.

    세 조각 중 기여가 기록되지 않은 것도 총합은 보여줘야 식이 맞아 떨어진다
    (기초 공격력처럼 원장에 안 잡히는 값). 없는 필드는 데이터클래스 기본값.

    applied는 히트가 실제로 곱하는 스탯 하나뿐이다 — 나머지는 화면이 접는다."""
    out = []
    for label, pre in _STAT_TRIPLES:
        total = {tag: (ex.fields[f"{pre}_{tag}"].total
                       if f"{pre}_{tag}" in ex.fields else _DEFAULTS[f"{pre}_{tag}"])
                 for tag in _STAT_PARTS}
        final = total["base"] * (1.0 + total["pct"]) + total["flat"]
        if abs(final) <= 1e-9:          # 값이 아예 없는 스탯은 접을 것도 없다
            continue
        out.append({
            "label": label, "final": final, **total,
            "applied": f"{pre}_base" in applied,
            "components": [_field_breakdown(ex.fields[f"{pre}_{tag}"], applied)
                           for tag in _STAT_PARTS if f"{pre}_{tag}" in ex.fields],
        })
    return out


def _explain_groups(ex, applied: frozenset[str]) -> list[dict]:
    """스탯 조립에 안 들어간 나머지 필드를 묶음별로. 어느 목록에도 없는 필드는
    마지막 '그 밖의 필드'로 흘려 보낸다 — 조용히 사라지는 편보다 낫다."""
    out, shown = [], set(_STAT_FIELDS)
    for label, names in _EXPLAIN_GROUPS:
        picked = [ex.fields[n] for n in names if n in ex.fields]
        shown.update(fb.field for fb in picked)
        if picked:
            out.append({"label": label,
                        "fields": [_field_breakdown(fb, applied) for fb in picked]})

    rest = [fb for name, fb in ex.fields.items() if name not in shown]
    if rest:
        out.append({"label": "그 밖의 필드",
                    "fields": [_field_breakdown(fb, applied) for fb in rest]})
    return out
