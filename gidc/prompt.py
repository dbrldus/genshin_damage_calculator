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
    kind:    str                      # bool | int | choice | multi
    prompt:  str
    options: tuple[str, ...] = ()
    min_val: int = 0
    max_val: int = 999

    def to_dict(self) -> dict:
        return {
            "id": self.id, "kind": self.kind, "prompt": self.prompt,
            "options": list(self.options), "min": self.min_val, "max": self.max_val,
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
        return {"bool": False, "int": q.min_val, "choice": 0, "multi": []}[q.kind]

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
    return _ask(Question(_next_id(), "int", prompt, min_val=min_val, max_val=max_val))


def ask_bool(prompt: str) -> bool:
    return _ask(Question(_next_id(), "bool", prompt))


def ask_choice(prompt: str, options: list[str]) -> int:
    """선택한 항목의 인덱스(0-based)를 반환."""
    return _ask(Question(_next_id(), "choice", prompt, options=tuple(options)))


def ask_multi_choice(prompt: str, options: list[str]) -> list[int]:
    """여러 항목을 선택해 인덱스(0-based) 리스트를 반환한다. 없으면 빈 리스트.

    한 번의 조작으로 셋 이상을 고를 수 있어야 하는 효과(잿더미 세트처럼 반응 참여 원소가
    2개를 넘을 수 있는 경우)에 쓴다."""
    return _ask(Question(_next_id(), "multi", prompt, options=tuple(options)))
