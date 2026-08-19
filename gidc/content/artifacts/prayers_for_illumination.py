from gidc.core.artifact import Artifact
from gidc.enums import ArtifactSlot


class PrayersForIllumination(Artifact):
    """불을 모시는 자
    1세트: 불 원소 영향을 받는 지속 시간 40% 감소

    관(冠) 한 부위뿐인 세트라 2·4세트 효과가 없고, 1세트 효과도 원소 부착 지속 시간이라
    피해식에 들어가지 않는다. 그래도 파일을 두는 것은 **성급과 부위를 선언할 자리**가
    필요해서다.
    """

    RARITIES = (3, 4)
    SLOTS    = (ArtifactSlot.CIRCLET,)

    def apply_2set(self, all_hits, wearer) -> None:
        pass

    def apply_4set(self, all_hits, wearer) -> None:
        pass
