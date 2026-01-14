"""
Deflicker filter for stabilizing luminance fluctuations.

Designed for tape sources with temporal luminance variations.
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


class DeflickerFilter:
    """Deflicker filter to stabilize luminance."""

    def __init__(self, strength: float = 0.5, radius: int = 3):
        """
        Initialize deflicker filter.

        Args:
            strength: Deflicker strength (0.0 to 1.0, default 0.5)
            radius: Temporal radius for averaging (1-5, default 3)
        """
        self.strength = max(0.0, min(1.0, strength))
        self.radius = max(1, min(5, radius))

    def apply(self, clip: Any) -> Any:
        """
        Apply deflicker filter.

        Args:
            clip: Input VapourSynth video node

        Returns:
            Deflickered video node
        """
        if not HAS_VAPOURSYNTH or core is None or vs is None:
            raise ImportError("VapourSynth is required for deflicker")
        
        logger.info(f"Applying deflicker: strength={self.strength}, radius={self.radius}")

        # Calculate temporal average of luma
        deflickered = self._temporal_luma_stabilize(clip)
        
        # Blend with original based on strength
        result = core.std.Merge(clip, deflickered, weight=self.strength)
        
        return result

    def _temporal_luma_stabilize(self, clip: Any) -> Any:
        """
        Stabilize luminance using temporal averaging.

        Args:
            clip: Input video node

        Returns:
            Luminance-stabilized video node
        """
        if not HAS_VAPOURSYNTH or core is None or vs is None:
            raise ImportError("VapourSynth is required for deflicker")
        
        # Extract luma plane
        luma = core.std.ShufflePlanes(clip, planes=0, colorfamily=vs.GRAY)
        
        # Calculate temporal average of luma
        averaged_luma = core.std.AverageFrames(
            luma,
            weights=[1] * (2 * self.radius + 1),
            scenechange=True
        )
        
        # Merge temporally-averaged luma with original chroma planes
        if clip.format.num_planes == 1:
            # Grayscale clip, just return averaged luma
            return averaged_luma
        else:
            # Color clip, combine averaged luma (plane 0) with original chroma (planes 1 and 2)
            # ShufflePlanes takes plane 0 from averaged_luma, planes 1 and 2 from original clip
            return core.std.ShufflePlanes(
                [averaged_luma, clip, clip], 
                planes=[0, 1, 2], 
                colorfamily=clip.format.color_family
            )


def deflicker(clip: Any, strength: float = 0.5, radius: int = 3) -> Any:
    """
    Convenience function for deflickering.

    Args:
        clip: Input VapourSynth video node
        strength: Deflicker strength (0.0 to 1.0)
        radius: Temporal radius (1-5)

    Returns:
        Deflickered video node
    """
    filter_obj = DeflickerFilter(strength=strength, radius=radius)
    return filter_obj.apply(clip)
