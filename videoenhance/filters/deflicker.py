"""
Deflicker filter for stabilizing luminance fluctuations.

Designed for tape sources with temporal luminance variations.
"""

import vapoursynth as vs
import logging

logger = logging.getLogger(__name__)

core = vs.core


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

    def apply(self, clip: vs.VideoNode) -> vs.VideoNode:
        """
        Apply deflicker filter.

        Args:
            clip: Input VapourSynth video node

        Returns:
            Deflickered video node
        """
        logger.info(f"Applying deflicker: strength={self.strength}, radius={self.radius}")

        # Calculate temporal average of luma
        deflickered = self._temporal_luma_stabilize(clip)
        
        # Blend with original based on strength
        result = core.std.Merge(clip, deflickered, weight=self.strength)
        
        return result

    def _temporal_luma_stabilize(self, clip: vs.VideoNode) -> vs.VideoNode:
        """
        Stabilize luminance using temporal averaging.

        Args:
            clip: Input video node

        Returns:
            Luminance-stabilized video node
        """
        # Extract luma plane
        luma = core.std.ShufflePlanes(clip, planes=0, colorfamily=vs.GRAY)
        
        # Calculate temporal average of luma
        averaged_luma = core.std.AverageFrames(
            luma,
            weights=[1] * (2 * self.radius + 1),
            scenechange=True
        )
        
        # Calculate luma adjustment factor
        # target_luma / current_luma for each frame
        
        # Apply adjustment to all planes
        # This is simplified - in production would need per-frame adjustment
        adjusted = core.std.Expr(
            [clip, averaged_luma],
            expr=[f"x y / {self.strength} * 1 {self.strength} - + *"]
        )
        
        return adjusted


def deflicker(clip: vs.VideoNode, strength: float = 0.5, radius: int = 3) -> vs.VideoNode:
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
