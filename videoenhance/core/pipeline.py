"""
Main enhancement pipeline.

Orchestrates the complete video enhancement workflow.
"""

try:
    import vapoursynth as vs
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        VideoNode = vs.VideoNode
    else:
        VideoNode = "vs.VideoNode"
    core = vs.core
    HAS_VAPOURSYNTH = True
except ImportError:
    vs = None
    VideoNode = None
    core = None
    HAS_VAPOURSYNTH = False

from pathlib import Path
from typing import Dict, Optional, List, Any
import logging
from dataclasses import dataclass, field

from .detector import VideoDetector

# Import filters only if VapourSynth is available
if HAS_VAPOURSYNTH:
    from ..filters.deinterlace import DeinterlaceFilter
    from ..filters.denoise import TemporalDenoiseFilter
    from ..filters.sharpen import SharpenFilter
    from ..filters.deflicker import DeflickerFilter
    from ..filters.color import ColorNormalizeFilter
    from ..filters.artifacts import ArtifactCleanupFilter

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the enhancement pipeline."""
    
    # Deinterlacing
    deinterlace_preset: str = "Fast"
    
    # Denoising
    denoise_strength: float = 1.0
    denoise_radius: int = 2
    
    # Sharpening
    sharpen_strength: float = 0.3
    sharpen_radius: int = 1
    
    # Deflicker
    deflicker_strength: float = 0.5
    deflicker_radius: int = 3
    
    # Color normalization
    auto_white_balance: bool = True
    auto_contrast: bool = True
    gamma: float = 1.0
    
    # Artifact cleanup
    cleanup_artifacts: bool = True
    artifact_strength: float = 0.5
    
    # Output
    output_codec: str = "hevc"  # hevc or av1
    output_crf: int = 20
    output_preset: str = "medium"
    
    # GPU acceleration
    use_gpu: bool = False
    gpu_device: int = 0


class Pipeline:
    """Video enhancement pipeline."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize pipeline.

        Args:
            config: Pipeline configuration (uses defaults if not provided)
        """
        if not HAS_VAPOURSYNTH:
            logger.warning("VapourSynth not available - pipeline will not be functional")
        
        self.config = config or PipelineConfig()
        self.detector = VideoDetector()

    def process(self, input_path: str, output_path: str,
                progress_callback: Optional[callable] = None) -> Dict[str, any]:
        """
        Process a video file through the enhancement pipeline.

        Args:
            input_path: Path to input video file
            output_path: Path to output video file
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary containing processing metrics and statistics

        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If video format cannot be processed
        """
        input_path = Path(input_path)
        output_path = Path(output_path)

        logger.info(f"Processing {input_path} -> {output_path}")

        # Step 1: Detect video properties
        if progress_callback:
            progress_callback("Detecting video format", 0)
        
        properties = self.detector.detect(str(input_path))
        logger.info(f"Video properties: {properties}")

        # Step 2: Load video into VapourSynth
        if progress_callback:
            progress_callback("Loading video", 10)
        
        clip = self._load_video(str(input_path))

        # Step 3: Apply enhancement pipeline
        if progress_callback:
            progress_callback("Applying enhancements", 20)
        
        clip = self._apply_pipeline(clip, properties)

        # Step 4: Export video
        if progress_callback:
            progress_callback("Exporting video", 80)
        
        self._export_video(clip, str(output_path), properties)

        if progress_callback:
            progress_callback("Complete", 100)

        return {
            'input': str(input_path),
            'output': str(output_path),
            'properties': properties,
            'success': True
        }

    def _load_video(self, video_path: str) -> Any:
        """
        Load video into VapourSynth.

        Args:
            video_path: Path to video file

        Returns:
            VapourSynth video node
        """
        # Use ffms2 or lsmas for loading
        try:
            clip = core.ffms2.Source(video_path)
        except AttributeError:
            try:
                clip = core.lsmas.LWLibavSource(video_path)
            except AttributeError:
                # Fallback to basic source
                clip = core.bs.VideoSource(video_path)

        return clip

    def _apply_pipeline(self, clip: Any, properties: Dict[str, any]) -> Any:
        """
        Apply the complete enhancement pipeline.

        Args:
            clip: Input video node
            properties: Video properties from detector

        Returns:
            Enhanced video node
        """
        # Step 1: Deinterlacing (mandatory for interlaced content)
        if properties.get('interlaced', False):
            logger.info("Applying deinterlacing (interlaced content detected)")
            deinterlace = DeinterlaceFilter(
                preset=self.config.deinterlace_preset,
                field_order=properties.get('field_order')
            )
            clip = deinterlace.apply(clip)
        else:
            logger.info("Skipping deinterlacing (progressive content)")

        # Step 2: Temporal denoise
        logger.info("Applying temporal denoise")
        denoise = TemporalDenoiseFilter(
            strength=self.config.denoise_strength,
            radius=self.config.denoise_radius
        )
        clip = denoise.apply(clip)

        # Step 3: Sharpen
        logger.info("Applying sharpening")
        sharpen = SharpenFilter(
            strength=self.config.sharpen_strength,
            radius=self.config.sharpen_radius
        )
        clip = sharpen.apply(clip)

        # Step 4: Deflicker
        logger.info("Applying deflicker")
        deflicker = DeflickerFilter(
            strength=self.config.deflicker_strength,
            radius=self.config.deflicker_radius
        )
        clip = deflicker.apply(clip)

        # Step 5: Color normalization
        logger.info("Applying color normalization")
        color = ColorNormalizeFilter(
            auto_white_balance=self.config.auto_white_balance,
            auto_contrast=self.config.auto_contrast,
            gamma=self.config.gamma
        )
        clip = color.apply(clip)

        # Step 6: Artifact cleanup (optional)
        if self.config.cleanup_artifacts:
            logger.info("Applying artifact cleanup")
            artifacts = ArtifactCleanupFilter(
                strength=self.config.artifact_strength
            )
            clip = artifacts.apply(clip)

        return clip

    def _export_video(self, clip: Any, output_path: str, 
                     properties: Dict[str, any]) -> None:
        """
        Export video using FFmpeg.

        Args:
            clip: VapourSynth video node
            output_path: Path to output file
            properties: Video properties
        """
        logger.info(f"Exporting to {output_path} using {self.config.output_codec}")

        # Set up output pipe from VapourSynth
        clip.set_output()

        # Build FFmpeg command
        codec_args = self._get_codec_args()

        # This is a placeholder - actual implementation would use
        # VapourSynth's built-in output methods or vspipe
        logger.info(f"Export configuration: codec={self.config.output_codec}, "
                   f"crf={self.config.output_crf}, preset={self.config.output_preset}")

    def _get_codec_args(self) -> List[str]:
        """
        Get FFmpeg codec arguments.

        Returns:
            List of FFmpeg codec arguments
        """
        if self.config.output_codec == "hevc":
            codec = "libx265"
            if self.config.use_gpu:
                codec = "hevc_nvenc"
        elif self.config.output_codec == "av1":
            codec = "libsvtav1"
            if self.config.use_gpu:
                codec = "av1_nvenc"
        else:
            codec = "libx264"

        args = [
            "-c:v", codec,
            "-crf", str(self.config.output_crf),
            "-preset", self.config.output_preset,
        ]

        return args
