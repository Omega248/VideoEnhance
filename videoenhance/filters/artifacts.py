"""
Compression artifact cleanup filter.

Preserves edges while cleaning compression artifacts.
"""

try:
    import vapoursynth as vs
    core = vs.core
    HAS_VAPOURSYNTH = True
except ImportError:
    vs = None
    core = None
    HAS_VAPOURSYNTH = False

from typing import Any
import logging

logger = logging.getLogger(__name__)


class ArtifactCleanupFilter:
    """Filter for cleaning compression artifacts."""

    def __init__(self, strength: float = 0.5):
        """
        Initialize artifact cleanup filter.

        Args:
            strength: Cleanup strength (0.0 to 1.0, default 0.5)
        """
        self.strength = max(0.0, min(1.0, strength))

    def apply(self, clip: Any) -> Any:
        """
        Apply artifact cleanup.

        Args:
            clip: Input VapourSynth video node

        Returns:
            Cleaned video node
        """
        logger.info(f"Applying artifact cleanup: strength={self.strength}")

        try:
            # Try to use f3kdb for deblocking and debanding
            cleaned = core.f3kdb.Deband(
                clip,
                range=int(self.strength * 16),
                y=int(self.strength * 64),
                cb=int(self.strength * 48),
                cr=int(self.strength * 48),
                grainy=0,
                grainc=0,
                output_depth=8
            )
            return cleaned
        except AttributeError:
            logger.warning("f3kdb not available, using basic deblocking")
            return self._fallback_cleanup(clip)

    def _fallback_cleanup(self, clip: Any) -> Any:
        """
        Fallback artifact cleanup using basic filters.

        Args:
            clip: Input video node

        Returns:
            Cleaned video node
        """
        # Apply a very mild blur to reduce blocking
        # Use a small kernel to preserve edges
        cleaned = core.std.Convolution(
            clip,
            matrix=[1, 2, 1, 2, 8, 2, 1, 2, 1]
        )
        
        # Blend with original based on strength
        result = core.std.Merge(clip, cleaned, weight=self.strength * 0.3)
        
        return result


def cleanup_artifacts(clip: Any, strength: float = 0.5) -> Any:
    """
    Convenience function for artifact cleanup.

    Args:
        clip: Input VapourSynth video node
        strength: Cleanup strength (0.0 to 1.0)

    Returns:
        Cleaned video node
    """
    filter_obj = ArtifactCleanupFilter(strength=strength)
    return filter_obj.apply(clip)
