"""
Mild sharpening filter.

Low-radius, low-strength, no halos.
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


class SharpenFilter:
    """Mild sharpening filter without halos."""

    def __init__(self, strength: float = 0.3, radius: int = 1):
        """
        Initialize sharpening filter.

        Args:
            strength: Sharpening strength (0.0 to 1.0, default 0.3)
            radius: Sharpening radius (1-2, default 1)
        """
        self.strength = max(0.0, min(1.0, strength))
        self.radius = max(1, min(2, radius))

    def apply(self, clip: Any) -> Any:
        """
        Apply mild sharpening.

        Args:
            clip: Input VapourSynth video node

        Returns:
            Sharpened video node
        """
        logger.info(f"Applying sharpening: strength={self.strength}, radius={self.radius}")

        try:
            # Try to use LSFmod for high-quality sharpening
            sharpened = core.lsf.LimitedSharpenFaster(
                clip,
                ss_x=1.0,
                ss_y=1.0,
                strength=int(self.strength * 100),
                overshoot=1
            )
            return sharpened
        except AttributeError:
            logger.warning("LSFmod not available, using unsharp mask")
            return self._fallback_sharpen(clip)

    def _fallback_sharpen(self, clip: Any) -> Any:
        """
        Fallback sharpening using unsharp mask.

        Args:
            clip: Input video node

        Returns:
            Sharpened video node
        """
        # Create blurred version
        blurred = core.std.Convolution(
            clip,
            matrix=[1, 2, 1, 2, 4, 2, 1, 2, 1]
        )

        # Create unsharp mask
        # Formula: original + strength * (original - blurred)
        diff = core.std.MakeDiff(clip, blurred)
        
        # Apply limited strength
        sharpened = core.std.MergeDiff(clip, diff, weight=self.strength)
        
        return sharpened


def sharpen(clip: Any, strength: float = 0.3, radius: int = 1) -> Any:
    """
    Convenience function for sharpening.

    Args:
        clip: Input VapourSynth video node
        strength: Sharpening strength (0.0 to 1.0)
        radius: Sharpening radius (1-2)

    Returns:
        Sharpened video node
    """
    filter_obj = SharpenFilter(strength=strength, radius=radius)
    return filter_obj.apply(clip)
