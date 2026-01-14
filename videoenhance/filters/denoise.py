"""
Temporal-only denoising filter.

No spatial blur, no detail smearing - temporal processing only.
"""

try:
    import vapoursynth as vs
    core = vs.core
    HAS_VAPOURSYNTH = True
except ImportError:
    vs = None
    core = None
    HAS_VAPOURSYNTH = False

from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class TemporalDenoiseFilter:
    """Temporal-only denoising filter."""

    def __init__(self, strength: float = 1.0, radius: int = 2):
        """
        Initialize temporal denoise filter.

        Args:
            strength: Denoising strength (0.0 to 3.0, default 1.0)
            radius: Temporal radius in frames (1-3, default 2)
        """
        self.strength = max(0.0, min(3.0, strength))
        self.radius = max(1, min(3, radius))

    def apply(self, clip: Any) -> Any:
        """
        Apply temporal denoising.

        Args:
            clip: Input VapourSynth video node

        Returns:
            Denoised video node
        """
        if not HAS_VAPOURSYNTH or core is None:
            raise ImportError("VapourSynth is required for denoising")
        
        logger.info(f"Applying temporal denoise: strength={self.strength}, radius={self.radius}")

        try:
            # Try to use TTempSmooth for temporal-only denoising
            denoised = core.ttmpsm.TTempSmooth(
                clip,
                maxr=self.radius,
                thresh=int(self.strength * 4),
                mdiff=int(self.strength * 2),
                strength=int(self.strength)
            )
            return denoised
        except AttributeError:
            logger.warning("TTempSmooth not available, using AverageFrames")
            # Fallback to AverageFrames
            return self._fallback_denoise(clip)

    def _fallback_denoise(self, clip: Any) -> Any:
        """
        Fallback temporal denoising using built-in filters.

        Args:
            clip: Input video node

        Returns:
            Denoised video node
        """
        if not HAS_VAPOURSYNTH or core is None:
            raise ImportError("VapourSynth is required for denoising")
        
        # Use built-in AverageFrames for temporal denoising
        # Create weights array centered on current frame
        # Strength controls the denoising amount (0.0-3.0):
        #   - strength=0.0: center_weight=4, weights=[1,1,4,1,1] → 50% center (minimal denoising)
        #   - strength=1.0: center_weight=3, weights=[1,1,3,1,1] → 43% center (moderate denoising)
        #   - strength=3.0: center_weight=1, weights=[1,1,1,1,1] → 20% center (strong denoising)
        # Higher strength = less weight on current frame = more temporal smoothing
        center_weight = max(1, int(4 - self.strength))
        neighbor_weight = 1
        weights = [neighbor_weight] * self.radius + [center_weight] + [neighbor_weight] * self.radius
        
        denoised = core.std.AverageFrames(
            clip,
            weights=weights,
            scale=sum(weights),
            scenechange=True
        )
        return denoised


def temporal_denoise(clip: Any, strength: float = 1.0, radius: int = 2) -> Any:
    """
    Convenience function for temporal denoising.

    Args:
        clip: Input VapourSynth video node
        strength: Denoising strength (0.0 to 3.0)
        radius: Temporal radius in frames (1-3)

    Returns:
        Denoised video node
    """
    filter_obj = TemporalDenoiseFilter(strength=strength, radius=radius)
    return filter_obj.apply(clip)
