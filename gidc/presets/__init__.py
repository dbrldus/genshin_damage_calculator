"""빌드 프리셋 — 캐릭터 하나를 완성된 상태로 만들어 주는 build() 팩토리 모음.

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
