# 캐릭터 구현 작업 순서

이 문서는 지금까지 구현된 캐릭터(스커크·모나·산드로네·설탕·한운·얀사 …)가 실제로 거쳐 온
순서를 그대로 옮긴 것이다. 새 캐릭터를 넣을 때는 이 순서대로 진행한다.

계산 순서(Phase)의 **단일 출처**는 [`gidc/core/party.py`](../gidc/core/party.py)의
`Party.build_profiles`다. 아래에서 「Phase N」이라고 부르는 이름은 전부 거기서 정의된다.

---

## 0. 이 작업이 건드리는 파일

| 파일 | 언제 |
|---|---|
| `gidc/content/characters/<원소>/<이름>.py` | 항상 — 본체 |
| `gidc/content/characters/<원소>/__init__.py` | 항상 — `from .<이름> import <Class>` |
| `gidc/content/characters/__init__.py` | 항상 — `CHARACTER_REGISTRY`에 한글 이름 |
| `web/engine.zip` | 항상 — `python tools/sync_web.py`로 재생성 |
| `gidc/core/profile.py` | 새 `SkillHit` 필드가 필요할 때만 |
| `gidc/core/party.py` | 새 코어 풀 필드·파티 판정이 생길 때만 |
| `gidc/core/explain.py` | 새 필드를 explain 화면에 태울 때만 |
| `gidc/enums.py` / `gidc/core/reaction.py` | 새 `CharacterTrait`·반응 전환자일 때만 |
| `web/icons.json` | **손대지 않는다** — 로스터 120명이 이미 들어 있다 |

등록 두 곳 중 **하나라도 빠지면** `make_character`가 조용히 `DefaultCharacter`로 대체한다.
예외도 경고도 나지 않으므로 반드시 둘 다 확인한다.

---

## 1단계 — 참고 구현과 코어 계약을 먼저 읽는다

구현을 시작하기 전에 최소 이 넷을 읽는다.

1. `gidc/core/party.py` 상단 docstring — Phase 0~6의 정의.
2. `gidc/core/character.py`의 훅 docstring — `build_hits` / `apply_self_buffs` /
   `contribute_dependent_stats` / `apply_party_buffs` / `apply_dependent_buffs`.
3. `gidc/core/profile.py`의 `SkillHit` 필드 목록과 `add()` 계약(지연 기여).
4. **가장 가까운 동류 캐릭터** 한 명. 서포터면 얀사·한운·설탕, 딜러면 스커크·나비아,
   달·별 반응 전환자면 콜롬비나·산드로네.

> 최신 파일을 그대로 베끼지 말 것. 훅 배치는 **수혜자가 누구냐**로 정해지므로 그 캐릭터에만
> 맞는 배치일 수 있다. 자기 자신만 받는 효과는 유저 입력이 있더라도 `apply_self_buffs`다.

---

## 2단계 — 스켈레톤 (사용자 확인 게이트)

`skeleton_code/Anonymous.py`를 복사해 시작한다. 이 단계에서 **채우는 것**과 **비우는 것**이
정해져 있다.

**채운다**

- 클래스명, `name`(한글), `weapon_type`, `rarity`, `ascension_stat`, `element` 프로퍼티
- `innate_traits` / `unlockable_traits` (해당될 때만)
- 계수 테이블 — 사용자가 준 공식 수치 스크린샷 기준
- 등록 2곳

**비운다**

- 클래스 맨 위 docstring(스킬·특성·명함 설명) — 사용자가 공식 정보로 직접 채운다
- 모든 훅 본문 — `...` + 무엇이 들어갈지 적은 TODO 주석까지만

기억으로 채운 스킬 설명과 계수는 틀리기 쉽고, 틀린 값이 섞이면 계산 결과가 조용히 오염된다.
스켈레톤을 낸 뒤 **사용자가 docstring/수치를 확정할 때까지 본문을 쓰지 않는다.**

---

## 3단계 — 계수 표 전사

스크린샷의 **모든 열**을 옮기고, 필요한 레벨 범위만 남긴다.

- 일반/강/낙하 공격: **L1~L11** (특성 레벨 최대 10 + 보정 여지)
- 원소 스킬 / 원소 폭발: **L1~L13** (명함 +3)
- 스커크 「무예 전수」가 닿지 않는 원소(불·바위 등)는 L14 행이 필요 없다
- 계수는 반드시 소수(`0.4700`)로. 위키의 세 자리 표기(`47.0`)는 잘린 값이라 정밀한 쪽을 쓴다

**한 히트가 상태마다 다른 열을 쓰면 숫자가 같아도 열을 합치지 않는다.** 이름이 어느 상태인지
말하게 두고(`_CA_COOLANT_CONDUCT` / `_CA_COOLANT_SWIRL`), 호출부도 열을 각각 짚는다
(`conduct=` / `swirl=`). 한쪽만 바뀌는 날 조용히 어긋나는 것을 막는다.

전사한 표는 **전부** 레벨 메타데이터에 등록한다. 여기 빠진 표는 클램프 경고가 살아나지 않아
계수 누락이 드러나지 않는다.

```python
SKILL_LEVEL_UP_CONSTELLATION = 3
BURST_LEVEL_UP_CONSTELLATION = 5
NA_TABLES    = (*_NA, _CA, _THUNDERQUAKE, _PLUNGE, _LOW_PLUNGE, _HIGH_PLUNGE,)
SKILL_TABLES = (_SKILL_DMG,)
BURST_TABLES = (_BURST_DMG, _MEASURER_ATK_CAP,)
```

계수가 아닌 상수(공격력 보너스 상한, 밤혼 최대치, 명함 계수 …)도 이름 있는 클래스 속성으로
빼 둔다. 레벨 스케일하는 값이라면 표로 만들어 `*_TABLES`에 함께 등록한다.

---

## 4단계 — 등록

```python
# gidc/content/characters/electro/__init__.py
from .iansan import Iansan
```

```python
# gidc/content/characters/__init__.py
CHARACTER_REGISTRY = {
    ...
    "얀사": electro.Iansan,
}
```

---

## 5단계 — 구현 계획 합의

본문을 쓰기 전에 **효과 하나하나를 어느 훅에 어떤 필드로 넣을지** 표로 적어 사용자 확인을
받는다. 이 표가 곧 6~8단계의 작업 목록이 된다.

| 효과 | 수혜자 | 훅(Phase) | 필드 | 유저 입력 |
|---|---|---|---|---|
| A1 표준 동작 공격력 +20% | 얀사 본인 | `apply_self_buffs` (3) | `atk_pct` | 「표준 동작」 여부 |
| C2 필드 위 캐릭터 공격력 +30% | 파티 1명 | `contribute_dependent_stats` (4) | `atk_pct` | 필드 위 캐릭터 |
| C6 주는 피해 +25% | 파티 1명 | `apply_party_buffs` (4.5) | `all_dmg_bonus` | 「극한의 힘」 여부 |
| Q 운동량 측정기 | 파티 1명 | `apply_dependent_buffs` (5) | `atk_flat_derived` (지연) | 밤혼 수치 |

### 훅 고르는 기준

| 이 효과가… | 훅 | Phase |
|---|---|---|
| 자기 자신만 받는다 | `apply_self_buffs` | 3 |
| 남의 ATK/DEF/HP/EM 풀에 **고정값**을 더한다 | `contribute_dependent_stats` | 4 |
| 남에게 주지만 스탯 풀이 아니다(내성 감소, 고정 `all_dmg_bonus`, 치명타 …) | `apply_party_buffs` | 4.5 |
| **버퍼의 최종 스탯을 읽어** 만든다 | `apply_dependent_buffs` | 5 |

훅을 정하는 것은 **수혜자**지 트리거가 아니다. 「낙뢰파 명중 후 얀사의 공격력 +20%」는
트리거가 히트여도 받는 쪽이 얀사뿐이므로 자기 버프다.

---

## 6단계 — `build_hits`

계수·원소·스킬 종류만 세운다. 스탯은 전부 기본값이다.

```python
def build_hits(self) -> dict[str, SkillHit]:
    sk = self._skill_index()   # C3 스킬 +3 반영
    bl = self._burst_index()   # C5 폭발 +3 반영
    nl = self._na_index()

    hits: list[SkillHit] = []
    for i, row in enumerate(self._NA):
        hits.append(SkillHit(f"{i+1}단 공격 피해", SkillType.NORMAL_ATK, row[nl], ScalingStat.ATK))
    hits.append(SkillHit("원소 스킬 피해", SkillType.SKILL, self._SKILL_DMG[sk],
                         ScalingStat.ATK, Element.ELECTRO))
    return {h.name: h for h in hits}
```

- 레벨 인덱스는 **직접 계산하지 말고** `_na_index()` / `_skill_index()` / `_burst_index()`를
  쓴다. 명함 상승·파티 상승·클램프가 전부 그 안에 들어 있다.
- `element`를 주지 않으면 물리 피해다. 무기 종류가 정하는 일반/강/낙하는 보통 물리이고,
  원소 성질을 띠는 변형 공격(「낙뢰파」 등)만 명시한다.
- 서로 배타적인 히트(강공격 ↔ 대체 강공격)는 **둘 다 세워 둔다.** 어느 쪽을 합산할지는
  화면을 읽는 쪽이 고른다.
- 달·별 반응 직접 피해 히트는 `coeff_amp`가 아니라 `coeff`를 쓴다. 공식에 `coeff_amp`
  자리가 없어 조용히 무효가 된다.
- 파티로 유도되지 않는 히트 원소(흡수 등)는 자리표로 두고 Phase 4에서 확정하거나 히트를
  지운다.

---

## 7단계 — 유저 입력 설계

### 어디서 묻는가

`ask_*`는 **Phase 3(`apply_self_buffs`) 또는 Phase 4(`contribute_dependent_stats`)에서만**
부른다. 질문 ID가 (호출 지점, 반복 횟수)라 실행 시점이 밀리면 질문 집합이 흔들린다.
**지연 기여 함수(람다) 안에서는 절대 묻지 않는다.**

한 답이 여러 효과를 가르면 **한 번만 묻고 `self`에 저장**해 뒤 단계가 재사용한다.

```python
self._q_active = ask_bool("[얀사 Q] 힘의 3요소 발동 (운동량 측정기) 여부")
```

### 무엇을 묻는가

- 값이 시간에 따라 변하거나(감쇠 버프) 로테이션이 정하는 양이면 **실제 실린 값을 묻는다.**
- 다만 **상한은 다른 답에서 유도해** `ask_int`의 `max_val`을 좁힌다
  (전의 120 → A4 보너스 최대 24%).
- 감쇠를 없애는 명함이 있으면 그 경우엔 묻지 않고 같은 식으로 유도한다.
  상한 계산은 함수 하나로 빼서 두 경로가 같은 식을 읽게 한다.
- 파티 구성만으로 정해지는 판정은 **묻지 않고 유도한다.** 다만 결과값이 아니라
  **메커니즘을 함수로** 만들어 모든 소비처가 같은 함수를 읽게 한다.
- 「현재 필드 위 캐릭터」는 `ask_choice`로 **1명**만 고르게 한다. 파티 전원에게 걸면
  부풀려진다. 파티원이 1명뿐이면 묻지 않는다.

### `party.py`에 질문을 추가할 때

저장된 답변(`_baseline/answers.txt`, 웹 빌드)이 질문 ID에 묶여 있다. **줄 수가 변하지 않게**
교체하고, 새 질문은 **맨 아래에 추가**하며, 새 import는 **아래쪽에** 넣는다.

---

## 8단계 — 훅 본문

### `apply_self_buffs` — Phase 3

자기 히트에만 붙는 버프. 모든 가산은 `hit.add(field, value, self, note="A1 표준 동작")`으로
넣는다. 직접 `+=` 하면 explain 원장에 출처가 남지 않는다.

### `contribute_dependent_stats` — Phase 4

남의 ATK/DEF/HP/EM 풀에 **고정값**을 더한다. 유저 입력도 여기서 모은다.
남의 최종 스탯을 읽어 만드는 값이라면 여기서도 `add`에 **함수**를 넘긴다 — 같은 단계의
다른 기여를 놓치지 않기 위해서다(콜롬비나 C2가 읽는 HP를 실로닌 C2가 같은 단계에서 올린다).

EM %-공유(설탕·나히다)는 `elemental_mastery`와 `em_from_pct_share`에 **동시에** 태그해
「EM을 다시 %로 변환하는」 버프가 그 지분을 재료로 쓰지 못하게 막는다.

### `apply_party_buffs` — Phase 4.5

스탯을 읽지 않는 크로스 버프. 내성 감소, 고정 `all_dmg_bonus`, 치명타, 방어 무시.
Phase 4에서 저장해둔 상태를 재사용해 같은 질문을 두 번 묻지 않는다.

### `apply_dependent_buffs` — Phase 5

**값이 아니라 함수를 넘긴다.**

```python
source_hit = next(iter(all_hits[self].values()))
bonus = lambda: self._measurer_atk_bonus(source_hit.convertible_atk())
for hit in all_hits[self._on_field].values():
    hit.add("atk_flat_derived", bonus, self, note="Q 운동량 측정기")
```

- 지금 계산해 버리면 파티 멤버 순서가 결과를 바꾼다. 함수로 넘기면 그 필드를 읽는
  순간(늦어도 Phase 5.5)에 정해져 순서와 무관해진다. 순환이면 `CyclicBuffError`로 즉시 실패.
- 람다가 루프 변수를 잡으면 `lambda h=hit: ...`로 묶는다(늦은 바인딩).
- 항상 **같은 히트**(보통 첫 히트)를 읽어 값이 하나로 정해지게 한다.
- ATK/DEF/HP 코어 풀에 **즉시 값으로** 되먹이면 정확성 가드
  (`party._assert_core_pools_unchanged`)가 실패시킨다.

### 스탯 변환 시 읽을 필드

| 만드는 것 | 읽는 것 / 내보내는 곳 |
|---|---|
| 공격력 → 공격력 | `convertible_atk()`를 읽고 **`atk_flat_derived`로 출력** |
| EM → EM, EM → 피해 보너스% (재변환) | `convertible_em()` |
| EM → 피해에 직접 더하는 고정값 | `elemental_mastery` (원본 그대로) |
| 최종 스탯 → 피해 (방식 B) | `current_atk/def/hp()` → `flat_dmg_bonus`로 차원 변환 |

같은 슬롯을 읽고 쓰면 지연 평가에서 순환이 된다. 피해 차원으로 바꾸거나 꼬리표 달린
별도 슬롯으로 내보내 사슬을 끊는다.

---

## 9단계 — 「의도적 미구현」 블록

파일 맨 아래에 **무엇을 왜 넣지 않았는지** 적는다. 나중에 「빠뜨린 것」과 「안 넣기로 한 것」을
구분하는 유일한 근거다.

```python
# ── 의도적 미구현 ─────────────────────────────────────────────────────
# · 밤혼 수지 전반 — 자원 모델이 없어 피해식에 들어갈 항이 없다.
# · A4 — 치유뿐이다. 이 엔진은 치유를 히트로 만들지 않는다.
# · C1 — 원소 에너지 회복. 로테이션 빈도지 히트 단가가 아니다.
```

주로 여기 들어가는 것: 에너지 회복, 치유, 쿨다운, 이동 속도, 자원 게이지 수지, 실드 수치.

---

## 10단계 — 코어에 손대야 하는 경우

새 메커니즘이면 캐릭터 파일만으로 끝나지 않는다. 얀사(`atk_flat_derived`)와
산드로네(별 반응)가 그 예다.

- **새 `SkillHit` 필드** → `gidc/core/profile.py`에 필드 추가 + 최종 스탯 조립식
  (`current_atk` 등)에 반영
- **코어 스탯 풀 성격의 필드** → `gidc/core/party.py`의 `_CORE_POOL_FIELDS`에 추가
- **`{접두}_flat`이 아닌 이름의 flat 슬롯** → `gidc/core/explain.py`의 `_EXTRA_FLAT_FIELDS`에
  추가. 안 하면 화면의 「공격력 = base × (1+pct) + flat」 줄이 `atk_final`과 어긋난다
- **새 파티 판정 특성** → `gidc/enums.py`의 `CharacterTrait` + `innate_traits` 선언.
  반응 전환자면 `gidc/core/reaction.py`의 후보 판정도 함께
- **격변 반응 억제** → `ReactionType`만으로 막으면 안 된다. 확산이 원소별 4행이라
  **원소 쌍**으로 막아야 불·물·번개 확산까지 사라지지 않는다

---

## 11단계 — 검증 (세 가지 전부)

### (1) 파생 공식 기반 자체 검증

기댓값을 **손으로 타이핑하지 말고** `m.base_atk` 등에서 식으로 유도해 비교한다. 눈으로 옮겨
적은 상수는 자릿수 때문에 가짜 MISMATCH를 낸다.

돌려야 하는 경로: **명함 0 / 최대**, **조건 분기 on/off**, **질문 미응답 기본값**.

검증 스크립트는 `_presets/solo/<이름>.py` 꼴로 빌드를 하나 만들어 `Party(char)`를 돌리는
방식이 가장 짧다.

### (2) 계수 표 누락 — 클램프 경고를 실패로 승격

```python
import warnings
warnings.simplefilter("error")   # character.clamp_talent_index의 경고를 예외로
# 무예 전수(물·얼음 파티) 포함 여러 조합으로 build_profiles를 돌린다
```

### (3) 회귀 기준선 diff

```bash
python bench.py < _baseline/answers.txt > /tmp/out.txt 2>&1
```

```bash
diff _baseline/baseline.txt /tmp/out.txt
```

**신규 캐릭터는 bench 파티에 없으므로 diff가 비어야 정상이다.** 비어 있지 않다면 코어를
건드린 부분이 기존 계산을 바꾼 것이므로, 의도한 변화인지 눈으로 확인하기 전에는 기준선을
덮어쓰지 않는다.

---

## 12단계 — 웹 반영

```bash
python tools/sync_web.py
```

검사(`gidc.web_api` 임포트 → 레지스트리 → 빌드시트 → `run_calculation` 한 바퀴) → `engine.zip`
번들 → `app.js` 캐시 버전 갱신을 한 번에 한다. 검사에 실패하면 번들을 건드리지 않으므로
`web/`은 마지막으로 성공한 상태에 남는다.

`web/icons.json`은 전체 로스터 120명이 이미 들어 있어 **손대지 않는다.**

---

## 13단계 — 커밋과 보고

커밋 범위: 캐릭터 파일 + 등록 2곳 + `web/engine.zip` (+ 필요했다면 코어 변경).

**보고는 Phase별이 아니라 특성별로 쓴다** — E / Q / A1 / A4 / C1~C6 각각이 어디에 구현됐는지.
여기에 반드시 포함한다.

1. 검증 결과 (표 형태 — 기댓값 유도식과 실제값)
2. 기준선 diff 결과
3. **의도적으로 미구현한 항목**

---

## 부록 A — Phase 요약

| Phase | 하는 일 | 캐릭터 훅 |
|---|---|---|
| 0 | 파티 구성만으로 정해지는 특성 레벨 보정 | — |
| 1 | 히트 생성 (계수/원소/종류만) | `build_hits` |
| 2 | 원소 공명 · 환상극 | — |
| 3 | 기초/장비 스탯 → 세트·무기 패시브 → 자기 버프 | `apply_self_buffs` |
| 4 | 크로스 캐릭터 코어 스탯 기여 **+ 유저 입력 수집** | `contribute_dependent_stats` |
| 4.5 | 스탯을 읽지 않는 크로스 버프 | `apply_party_buffs` |
| 5 | 최종 스탯을 읽어 만드는 버프 (방식 B, 지연 기여) | `apply_dependent_buffs` |
| 5.5 | 남은 지연 기여를 전부 값으로 정산 | — |
| 6 | base/pct/flat → `*_final` 최종 확정 (단 한 번) | — |

단계는 「누가 먼저 실행되는가」가 아니라 「무엇을 출력하는가」로 나뉜다.

## 부록 B — 자주 하는 실수

- 등록 2곳 중 하나 누락 → `DefaultCharacter`로 조용히 대체. 경고 없음
- `*_TABLES`에 표 등록 누락 → 클램프 경고가 죽어 계수 누락이 드러나지 않음
- 지연 기여 함수 안에서 `ask_*` 호출 → 질문 집합이 흔들림
- Phase 5에서 코어 풀에 즉시 값 가산 → 정확성 가드 실패(순서 의존)
- 공격력→공격력을 `atk_flat`으로 출력 → 자기 참조 순환
- 달·별 히트에 `coeff_amp` 사용 → 공식에 자리가 없어 조용히 무효
- 「현재 필드 위 캐릭터」 효과를 파티 전원에게 적용 → 과대 계산
- `hit.field += x` 직접 가산 → explain 원장에 출처가 남지 않음
