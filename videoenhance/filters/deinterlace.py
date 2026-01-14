"""
VapourSynth deinterlacing filter using QTGMC.

Mandatory first step in the enhancement pipeline.
"""

import vapoursynth as vs
from typing import Optional
import logging

logger = logging.getLogger(__name__)

core = vs.core


class DeinterlaceFilter:
    """Deinterlacing filter using QTGMC Fast preset."""

    def __init__(self, preset: str = "Fast", field_order: Optional[str] = None):
        """
        Initialize deinterlacing filter.

        Args:
            preset: QTGMC preset (Fast, Medium, Slow, etc.)
            field_order: Field order - 'tff' (top field first) or 'bff' (bottom field first)
        """
        self.preset = preset
        self.field_order = field_order

    def apply(self, clip: vs.VideoNode) -> vs.VideoNode:
        """
        Apply QTGMC deinterlacing.

        Args:
            clip: Input VapourSynth video node

        Returns:
            Deinterlaced video node
        """
        try:
            # Import QTGMC (requires havsfunc or similar)
            from havsfunc import QTGMC

            logger.info(f"Applying QTGMC deinterlacing with preset: {self.preset}")
            
            # Set field order if specified
            if self.field_order == 'bff':
                clip = core.std.SetFieldBased(clip, 0)  # Bottom field first
            elif self.field_order == 'tff':
                clip = core.std.SetFieldBased(clip, 1)  # Top field first
            
            # Apply QTGMC
            deinterlaced = QTGMC(
                clip,
                Preset=self.preset,
                TFF=self.field_order != 'bff',
                FPSDivisor=1  # Keep original framerate (double for progressive)
            )

            return deinterlaced

        except ImportError:
            logger.warning("QTGMC not available, using built-in deinterlacing")
            # Fallback to simple bob deinterlacing
            return self._fallback_deinterlace(clip)

    def _fallback_deinterlace(self, clip: vs.VideoNode) -> vs.VideoNode:
        """
        Fallback deinterlacing using VapourSynth built-in filters.

        Args:
            clip: Input video node

        Returns:
            Deinterlaced video node using simple bob method
        """
        # Separate fields and double framerate
        clip = core.std.SeparateFields(clip, tff=self.field_order != 'bff')
        
        # Interpolate missing lines (bob)
        clip = core.resize.Spline36(clip, clip.width, clip.height)
        
        return clip


def deinterlace(clip: vs.VideoNode, preset: str = "Fast", field_order: Optional[str] = None) -> vs.VideoNode:
    """
    Convenience function for deinterlacing.

    Args:
        clip: Input VapourSynth video node
        preset: QTGMC preset
        field_order: Field order ('tff' or 'bff')

    Returns:
        Deinterlaced video node
    """
    filter_obj = DeinterlaceFilter(preset=preset, field_order=field_order)
    return filter_obj.apply(clip)
