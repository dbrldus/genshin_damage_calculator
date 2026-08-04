from gidc.core.artifact import Artifact


class DefaultArtifact(Artifact):
    """미구현 세트의 fallback — 세트 효과 없음."""

    def apply_2set(self, all_hits, wearer) -> None:
        pass

    def apply_4set(self, all_hits, wearer) -> None:
        pass
