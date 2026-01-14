"""
VideoEnhance - Automated video enhancement pipeline
"""

__version__ = "0.1.0"
__author__ = "VideoEnhance Contributors"

from .core.pipeline import Pipeline
from .core.detector import VideoDetector

__all__ = ["Pipeline", "VideoDetector"]
