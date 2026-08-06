"""빌드 프리셋 — 캐릭터 하나를 완성된 상태로 만들어 주는 build() 팩토리 모음.

**개발용이다. 엔진(gidc/)의 일부가 아니고 web/engine.zip 에도 실리지 않는다.**
웹에서는 빈 파티로 시작해 [+ 캐릭터 추가]로 맨몸 캐릭터를 넣고 직접 빌드를 짠다.
프리셋은 사람이 쓰는 출발점이 아니라 **검사용 고정 표본**으로만 남았다.

    · bench.py            회귀 기준선(_baseline/)을 만드는 파티
    · tools/sync_web.py   번들 굽기 전 엔진을 한 바퀴 돌리는 검사 파티

무기·성유물·명함이 다 박힌 캐릭터라서, 맨몸 캐릭터로는 건드리지 못하는 무기 패시브·
성유물 세트 효과·버프 상호작용까지 지난다. 그래서 웹이 안 쓰게 된 뒤에도 지우지 않는다.

각 프리셋은 import 시점에 객체를 만들지 않는다. build()를 부를 때마다 새 Character를
만들어 반환한다 — 캐릭터가 계산 도중 self._e_active 같은 per-run 상태를 저장하므로
같은 객체를 두 번 계산에 넣으면 결과가 오염되기 때문이다.
"""
from .skirk_party import escoffier, furina, mona, skirk
from .solo import bennett, columbina, ineffa, navia, xilonen
from .solo import furina as solo_furina
from .solo import skirk as solo_skirk

# 프리셋 이름 -> build() 팩토리
PRESET_REGISTRY = {
    "skirk_party/skirk":     skirk.build,
    "skirk_party/furina":    furina.build,
    "skirk_party/escoffier": escoffier.build,
    "skirk_party/mona":      mona.build,
    "solo/bennett":          bennett.build,
    "solo/columbina":        columbina.build,
    "solo/furina":           solo_furina.build,
    "solo/ineffa":           ineffa.build,
    "solo/navia":            navia.build,
    "solo/skirk":            solo_skirk.build,
    "solo/xilonen":          xilonen.build,
}


def build_preset(name: str):
    """프리셋 이름으로 새 캐릭터를 만든다."""
    try:
        return PRESET_REGISTRY[name]()
    except KeyError:
        raise ValueError(
            f"알 수 없는 프리셋 '{name}'. 사용 가능: {sorted(PRESET_REGISTRY)}"
        ) from None
