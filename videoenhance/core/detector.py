"""
Video format detection module.

Automatically detects container, codec, resolution, and interlaced/progressive status.
"""

try:
    import av
    HAS_AV = True
except ImportError:
    av = None
    HAS_AV = False

from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class VideoDetector:
    """Detects video format and properties."""

    @staticmethod
    def detect(video_path: str) -> Dict[str, any]:
        """
        Detect video format and properties.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary containing video properties:
                - container: Container format (e.g., 'avi', 'mkv')
                - codec: Video codec (e.g., 'h264', 'mpeg2')
                - width: Video width in pixels
                - height: Video height in pixels
                - fps: Frames per second
                - interlaced: True if interlaced, False if progressive
                - duration: Duration in seconds
                - field_order: Field order if interlaced (tff/bff)

        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If video format cannot be detected
        """
        if not HAS_AV:
            raise ImportError("PyAV library is required for video detection. Install with: pip install av")
        
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        try:
            container = av.open(str(video_path))
            video_stream = container.streams.video[0]

            # Detect interlaced status
            interlaced = False
            field_order = None
            
            # Check if video is interlaced by examining codec context
            if hasattr(video_stream, 'field_order'):
                if video_stream.field_order in ['tt', 'tb', 'bt', 'bb']:
                    interlaced = True
                    field_order = 'tff' if video_stream.field_order in ['tt', 'tb'] else 'bff'

            properties = {
                'container': container.format.name,
                'codec': video_stream.codec_context.name,
                'width': video_stream.width,
                'height': video_stream.height,
                'fps': float(video_stream.average_rate) if video_stream.average_rate else 25.0,
                'interlaced': interlaced,
                'duration': float(container.duration) / av.time_base if container.duration else 0.0,
                'field_order': field_order,
                'pixel_format': video_stream.pix_fmt,
            }

            container.close()

            logger.info(f"Detected video properties: {properties}")
            return properties

        except Exception as e:
            logger.error(f"Failed to detect video format: {e}")
            raise ValueError(f"Cannot detect video format: {e}")

    @staticmethod
    def is_sd_resolution(width: int, height: int) -> bool:
        """
        Check if resolution is SD (Standard Definition).

        Args:
            width: Video width
            height: Video height

        Returns:
            True if SD resolution, False otherwise
        """
        # Common SD resolutions: 720x480 (NTSC), 720x576 (PAL), 640x480, etc.
        return height <= 576 and width <= 720

    @staticmethod
    def validate_file(video_path: str) -> bool:
        """
        Validate that file is a readable video file.

        Args:
            video_path: Path to video file

        Returns:
            True if valid video file, False otherwise
        """
        if not HAS_AV:
            logger.warning("PyAV not available, cannot validate file")
            return False
            
        try:
            container = av.open(str(video_path))
            has_video = len(container.streams.video) > 0
            container.close()
            return has_video
        except Exception as e:
            logger.warning(f"File validation failed for {video_path}: {e}")
            return False
