"""상황 입력 — 계산 도중 유저에게 묻는 질문.

계산 도중 111곳에서 ask_* 를 호출한다. 이 함수들의 이름과 시그니처는 고정이며,
**답변을 어디서 얻을지만** AnswerSource가 결정한다:

    ConsoleSource   stdin 에서 직접 (CLI, bench.py)
    MappingSource   미리 받아둔 답변 맵에서 (웹)

질문 집합은 답변에 따라 달라지므로(푸리나 카니발 체크 해제 -> 뒤 질문 소멸,
나비아 결정 파편 답 -> 다음 질문의 max_val) 웹에서는 미리 다 열거할 수 없다.
MappingSource는 모르는 질문에 중립 기본값을 쓰고 pending에 기록한 뒤 끝까지 실행해서,
이번 라운드에 보일 질문을 한 번에 모은다. 답을 채워 다시 실행하면 새 질문이 드러난다.

질문 ID는 문구가 아니라 **(호출 지점, 같은 지점 반복 횟수)** 로 만든다.
같은 문구가 착용자마다(성유물 4세트), 루프마다(콜롬비나 C6) 반복되고,
푸리나는 같은 문구를 max 400/300 두 번 묻기 때문이다.
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class Question:
    """UI가 위젯 하나를 그리는 데 필요한 전부."""
    id:      str
    kind:    str                      # bool | int | choice | multi | step
    prompt:  str
    options: tuple[str, ...] = ()
    min_val: float = 0
    max_val: float = 999
    step:    float = 1               # step 전용 — 값이 오르내리는 간격
    owner:   str = ""                 # 이 질문을 낳은 장비의 착용자 (asking_for 참고)

    @property
    def display_prompt(self) -> str:
        """착용자를 앞머리 대괄호 **안에** 끼운다 — 「[스커크·진사 왕생록 4세트] …」.

        문구는 관례상 [출처]로 시작하므로(성유물 세트·무기·캐릭터 전부) 그 안에 넣으면
        「누구의 무엇」이 한 덩이로 읽힌다. 밖에 따로 붙이면 대괄호가 두 개 나란히 서서
        어디까지가 출처인지 되레 흐려진다.

        관례를 벗어난 문구(대괄호 없이 시작)는 앞에 [착용자]를 따로 세운다 — 문구를
        건드리는 것보다 낫다. 조립을 여기서 하는 이유는, 이 관례를 아는 것이 문구를
        가진 쪽(엔진)이지 화면이 아니기 때문이다."""
        if not self.owner:
            return self.prompt
        if self.prompt.startswith("["):
            return f"[{self.owner}·{self.prompt[1:]}"
        return f"[{self.owner}] {self.prompt}"

    def to_dict(self) -> dict:
        # prompt 는 착용자가 이미 접힌 표시용 문구다 — 화면이 다시 붙이지 않게
        # owner 를 따로 내보내지 않는다.
        return {
            "id": self.id, "kind": self.kind, "prompt": self.display_prompt,
            "options": list(self.options), "min": self.min_val, "max": self.max_val,
            "step": self.step,
        }


class AnswerSource:
    def ask(self, q: Question):
        raise NotImplementedError


# ══════════════════════════════════════════════════════════════════════════
#  CLI — 기존 동작을 그대로 보존한다 (회귀 기준선이 이 출력에 묶여 있다)
# ══════════════════════════════════════════════════════════════════════════
class ConsoleSource(AnswerSource):
    def ask(self, q: Question):
        return getattr(self, f"_{q.kind}")(q)

    def _bool(self, q: Question) -> bool:
        return input(f"{q.prompt} (y/n): ").strip().lower() == 'y'

    def _int(self, q: Question) -> int:
        while True:
            try:
                v = int(input(f"{q.prompt} ({q.min_val}~{q.max_val}): ").strip())
                if q.min_val <= v <= q.max_val:
                    return v
            except ValueError:
                pass
            print(f"  {q.min_val}~{q.max_val} 사이의 정수를 입력하세요.")

    def _choice(self, q: Question) -> int:
        print(q.prompt)
        for i, opt in enumerate(q.options, 1):
            print(f"  {i}) {opt}")
        while True:
            sel = input("선택: ").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(q.options):
                return int(sel) - 1
            print(f"  1~{len(q.options)} 사이를 입력하세요.")

    def _step(self, q: Question) -> float:
        """min_val~max_val 사이를, step 간격으로만 값을 받는 숫자 질문.

        4.8%처럼 배율 자체가 간격인 값을 「몇 단계」가 아니라 **실수치**로 직접
        받고 싶을 때 ask_int 대신 쓴다 — 화면에 뜨는 숫자가 곧 정련별 실수치라
        스펙과 바로 대조된다."""
        n_steps = round((q.max_val - q.min_val) / q.step)
        while True:
            try:
                v = float(input(f"{q.prompt} ({q.min_val}~{q.max_val}, {q.step} 간격): ").strip())
            except ValueError:
                print(f"  {q.min_val}~{q.max_val} 사이를 {q.step} 간격으로 입력하세요.")
                continue
            idx = round((v - q.min_val) / q.step)
            if 0 <= idx <= n_steps:
                return q.min_val + idx * q.step
            print(f"  {q.min_val}~{q.max_val} 사이를 {q.step} 간격으로 입력하세요.")

    def _multi(self, q: Question) -> list[int]:
        print(q.prompt)
        for i, opt in enumerate(q.options, 1):
            print(f"  {i}) {opt}")
        while True:
            sel = input("선택 (쉼표로 구분, 없으면 Enter): ").strip()
            if not sel:
                return []
            parts = sel.replace(",", " ").split()
            if all(p.isdigit() and 1 <= int(p) <= len(q.options) for p in parts):
                result: list[int] = []
                for p in parts:
                    idx = int(p) - 1
                    if idx not in result:
                        result.append(idx)
                return result
            print(f"  1~{len(q.options)} 사이의 번호를 쉼표로 구분해 입력하세요 (없으면 Enter).")


# ══════════════════════════════════════════════════════════════════════════
#  웹 — 답변 맵 조회 + 미답 질문 수집
# ══════════════════════════════════════════════════════════════════════════
class MappingSource(AnswerSource):
    """답이 있으면 쓰고, 없으면 중립 기본값으로 계속 진행하며 질문을 모은다.

    답변이 범위를 벗어나면(나비아처럼 앞선 답이 max_val을 바꾸는 경우) 잘라서 쓰고
    stale에 기록한다 — UI가 '값이 조정됨'을 표시할 수 있다."""

    def __init__(self, answers: dict | None = None):
        self.answers: dict             = dict(answers or {})
        self.asked:   list[Question]   = []   # 이번 실행에 등장한 질문 전부(순서대로)
        self.pending: list[Question]   = []   # 그중 아직 답이 없는 것
        self.stale:   list[str]        = []   # 범위를 벗어나 조정된 답변의 id

    def ask(self, q: Question):
        self.asked.append(q)
        if q.id not in self.answers:
            self.pending.append(q)
            return self._default(q)
        return self._coerce(q, self.answers[q.id])

    @staticmethod
    def _default(q: Question):
        return {"bool": False, "int": q.min_val, "choice": 0, "multi": [], "step": q.min_val}[q.kind]

    def _coerce(self, q: Question, raw):
        """UI에서 온 값을 엔진이 기대하는 타입·범위로 맞춘다."""
        if q.kind == "bool":
            return bool(raw)

        if q.kind == "int":
            want = int(raw)
            got  = max(q.min_val, min(want, q.max_val))
            if got != want:
                self.stale.append(q.id)
            return got

        if q.kind == "step":
            want = float(raw)
            n_steps = round((q.max_val - q.min_val) / q.step)
            idx = max(0, min(round((want - q.min_val) / q.step), n_steps))
            got = q.min_val + idx * q.step
            if abs(got - want) > 1e-9:
                self.stale.append(q.id)
            return got

        if q.kind == "choice":
            want = int(raw)
            if not 0 <= want < len(q.options):
                self.stale.append(q.id)
                return 0
            return want

        picked: list[int] = []
        for i in raw or []:
            i = int(i)
            if 0 <= i < len(q.options) and i not in picked:
                picked.append(i)
        if len(picked) != len(raw or []):
            self.stale.append(q.id)
        return picked


# ══════════════════════════════════════════════════════════════════════════
#  활성 소스 / 질문 ID
# ══════════════════════════════════════════════════════════════════════════
_CONSOLE = ConsoleSource()
_source:  ContextVar[AnswerSource]   = ContextVar("_source")
_counter: ContextVar[dict[str, int]] = ContextVar("_counter")
_owner:   ContextVar[str]            = ContextVar("_owner", default="")
_fallback_counter: dict[str, int] = {}


@contextmanager
def using(source: AnswerSource):
    """이 블록 안의 ask_* 를 주어진 소스로 처리한다. 질문 ID 카운터도 함께 초기화된다."""
    t_src = _source.set(source)
    t_cnt = _counter.set({})
    try:
        yield source
    finally:
        _source.reset(t_src)
        _counter.reset(t_cnt)


@contextmanager
def asking_for(name: str):
    """이 블록 안에서 나오는 질문에 「누구 것인가」를 달아 둔다.

    성유물 세트 효과의 문구는 세트 이름만 갖고 있어서(「[진사 왕생록 4세트] …」),
    같은 세트를 두 명이 끼고 있으면 화면에 똑같은 질문이 두 개 뜨고 어느 쪽이
    누구 것인지 알 수 없다. 문구를 착용자마다 다르게 만들 수는 없다 — 문구는
    100여 개 세트 파일에 흩어져 있고, 질문 ID도 문구가 아니라 호출 지점으로 만든다.
    그래서 문구는 그대로 두고 착용자만 Question.owner 로 얹어 UI가 붙여 그린다.

    ID는 (호출 지점, 반복 횟수)라 여기에 영향받지 않는다 — 착용자가 바뀌어도
    답변은 그대로 붙어 있다."""
    token = _owner.set(name)
    try:
        yield
    finally:
        _owner.reset(token)


def _next_id() -> str:
    """호출 지점(module:lineno) + 같은 지점 반복 횟수. 파티가 같으면 결정적이다."""
    frame = sys._getframe(2)                  # ask_* 를 부른 쪽
    key = f"{frame.f_globals.get('__name__', '?')}:{frame.f_lineno}"
    try:
        counter = _counter.get()
    except LookupError:
        counter = _fallback_counter           # CLI 경로 — ID를 쓰지 않는다
    n = counter.get(key, 0)
    counter[key] = n + 1
    return f"{key}#{n}"


def _ask(q: Question):
    try:
        source = _source.get()
    except LookupError:
        source = _CONSOLE
    return source.ask(q)


# ══════════════════════════════════════════════════════════════════════════
#  호출부가 쓰는 API — 시그니처 고정 (111곳이 이 이름을 부른다)
# ══════════════════════════════════════════════════════════════════════════
def ask_int(prompt: str, min_val: int = 0, max_val: int = 999) -> int:
    return _ask(Question(_next_id(), "int", prompt,
                         min_val=min_val, max_val=max_val, owner=_owner.get()))


def ask_bool(prompt: str) -> bool:
    return _ask(Question(_next_id(), "bool", prompt, owner=_owner.get()))


def ask_step(prompt: str, min_val: float, max_val: float, step: float) -> float:
    """min_val~max_val 사이를 step 간격으로만 오르내리는 숫자 질문.

    ask_int처럼 숫자 입력 위젯을 쓰되, 값이 임의의 정수가 아니라 **step의 배수**로만
    움직인다. 버프량 자체가 고정 간격으로만 실리는 효과(예: 4.8%씩 쌓이는 스택)에
    쓴다 — ask_choice로 각 단계를 문자열 선택지로 늘어놓는 대신, 화면에 실수치가
    직접 찍히는 숫자 입력으로 받는다."""
    return _ask(Question(_next_id(), "step", prompt,
                         min_val=min_val, max_val=max_val, step=step, owner=_owner.get()))


def ask_choice(prompt: str, options: list[str]) -> int:
    """선택한 항목의 인덱스(0-based)를 반환."""
    return _ask(Question(_next_id(), "choice", prompt,
                         options=tuple(options), owner=_owner.get()))


def ask_multi_choice(prompt: str, options: list[str]) -> list[int]:
    """여러 항목을 선택해 인덱스(0-based) 리스트를 반환한다. 없으면 빈 리스트.

    한 번의 조작으로 셋 이상을 고를 수 있어야 하는 효과(잿더미 세트처럼 반응 참여 원소가
    2개를 넘을 수 있는 경우)에 쓴다."""
    return _ask(Question(_next_id(), "multi", prompt,
                         options=tuple(options), owner=_owner.get()))
