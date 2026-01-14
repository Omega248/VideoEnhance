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
import subprocess

# Import numpy for video frame processing if available
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

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

# Constants for video export
FFMPEG_BUFFER_SIZE = 10**8  # 100MB buffer for FFmpeg stdin


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
            ImportError: If VapourSynth is not available
        """
        if not HAS_VAPOURSYNTH:
            raise ImportError(
                "VapourSynth is required for video processing. "
                "Please install VapourSynth from http://www.vapoursynth.com/"
            )
        
        input_path = Path(input_path)
        output_path = Path(output_path)

        logger.info(f"Processing {input_path} -> {output_path}")

        # Step 1: Detect video properties
        if progress_callback:
            progress_callback("Detecting video format", 0)
        
        properties = self.detector.detect(str(input_path))
        # Store source path for export
        properties['_source_path'] = str(input_path)
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
        
        self._export_video(clip, str(output_path), properties, progress_callback)

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
        if not HAS_VAPOURSYNTH or core is None:
            raise ImportError("VapourSynth is required for video loading")
        
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
        if not HAS_VAPOURSYNTH:
            raise ImportError("VapourSynth is required for pipeline processing")
        
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
                     properties: Dict[str, any],
                     progress_callback: Optional[callable] = None) -> None:
        """
        Export video using FFmpeg via subprocess.

        Args:
            clip: VapourSynth video node
            output_path: Path to output file
            properties: Video properties
            progress_callback: Optional callback for progress updates
        """
        if not HAS_VAPOURSYNTH or clip is None:
            raise ImportError("VapourSynth is required for video export")
        
        if not HAS_NUMPY:
            raise ImportError("NumPy is required for video export")
        
        logger.info(f"Exporting to {output_path} using {self.config.output_codec}")
        logger.info(f"Export configuration: codec={self.config.output_codec}, "
                   f"crf={self.config.output_crf}, preset={self.config.output_preset}")
        
        # Get clip properties
        num_frames = clip.num_frames
        fps_num = clip.fps.numerator
        fps_den = clip.fps.denominator
        fps = fps_num / fps_den
        width = clip.width
        height = clip.height
        
        logger.info(f"Exporting {num_frames} frames at {width}x{height}, {fps:.2f} fps")
        
        # Build FFmpeg codec arguments
        codec_args = self._get_codec_args()
        
        # Build FFmpeg command to read raw video from stdin
        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'rawvideo',
            '-pix_fmt', 'rgb24',
            '-s', f'{width}x{height}',
            '-r', f'{fps_num}/{fps_den}',
            '-i', 'pipe:0',
            '-y',  # Overwrite output file
        ] + codec_args + [
            '-pix_fmt', 'yuv420p',
            output_path
        ]
        
        logger.debug(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")
        
        try:
            # Start FFmpeg process
            ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=FFMPEG_BUFFER_SIZE
            )
            
            # Process and write each frame
            for frame_num in range(num_frames):
                if frame_num % 100 == 0 and frame_num > 0:
                    percent = (frame_num / num_frames) * 100
                    logger.info(f"Encoding progress: {frame_num}/{num_frames} frames ({percent:.1f}%)")
                    # Update progress callback (map frame progress to 80-100% range)
                    if progress_callback:
                        overall_percent = 80 + (frame_num / num_frames) * 20
                        progress_callback(f"Exporting video ({frame_num}/{num_frames} frames)", overall_percent)
                
                # Get frame from VapourSynth
                frame = clip.get_frame(frame_num)
                
                # Convert frame to RGB24 numpy array
                # Check the frame format and convert accordingly
                if frame.format.color_family == vs.RGB:
                    # RGB format - extract planes
                    planes = []
                    for plane_idx in range(frame.format.num_planes):
                        plane_array = np.asarray(frame[plane_idx])
                        planes.append(plane_array)
                    
                    # Stack RGB planes into single array (H, W, 3)
                    if len(planes) == 3:
                        rgb_array = np.stack(planes, axis=-1)
                    else:
                        # Grayscale - replicate to RGB
                        rgb_array = np.repeat(planes[0][:, :, np.newaxis], 3, axis=2)
                    
                    # Ensure uint8 format
                    if rgb_array.dtype != np.uint8:
                        # Convert from other bit depths
                        if frame.format.sample_type == vs.FLOAT:
                            rgb_array = (np.clip(rgb_array, 0.0, 1.0) * 255).astype(np.uint8)
                        else:
                            # Integer format - scale to 8-bit
                            bit_depth = frame.format.bits_per_sample
                            if bit_depth != 8:
                                rgb_array = (rgb_array >> (bit_depth - 8)).astype(np.uint8)
                
                else:
                    # YUV format - need to convert to RGB
                    # Extract Y, U, V planes
                    y_plane = np.asarray(frame[0])
                    u_plane = np.asarray(frame[1]) if frame.format.num_planes > 1 else None
                    v_plane = np.asarray(frame[2]) if frame.format.num_planes > 2 else None
                    
                    # Convert to 8-bit if necessary
                    bit_depth = frame.format.bits_per_sample
                    if frame.format.sample_type == vs.FLOAT:
                        y = (np.clip(y_plane, 0.0, 1.0) * 255).astype(np.uint8)
                        if u_plane is not None:
                            u = (np.clip(u_plane, 0.0, 1.0) * 255).astype(np.uint8)
                            v = (np.clip(v_plane, 0.0, 1.0) * 255).astype(np.uint8)
                        else:
                            u = np.full_like(y, 128, dtype=np.uint8)
                            v = np.full_like(y, 128, dtype=np.uint8)
                    else:
                        if bit_depth != 8:
                            shift = bit_depth - 8
                            y = (y_plane >> shift).astype(np.uint8)
                            if u_plane is not None:
                                u = (u_plane >> shift).astype(np.uint8)
                                v = (v_plane >> shift).astype(np.uint8)
                            else:
                                u = np.full_like(y, 128, dtype=np.uint8)
                                v = np.full_like(y, 128, dtype=np.uint8)
                        else:
                            y = y_plane.astype(np.uint8)
                            if u_plane is not None:
                                u = u_plane.astype(np.uint8)
                                v = v_plane.astype(np.uint8)
                            else:
                                u = np.full_like(y, 128, dtype=np.uint8)
                                v = np.full_like(y, 128, dtype=np.uint8)
                    
                    # Upsample U and V if subsampled (e.g., 4:2:0 or 4:2:2)
                    if u.shape != y.shape:
                        # Calculate upsampling ratios with validation
                        if u.shape[0] > 0 and u.shape[1] > 0:
                            height_ratio = max(1, y.shape[0] // u.shape[0])
                            width_ratio = max(1, y.shape[1] // u.shape[1])
                            
                            if height_ratio > 1 or width_ratio > 1:
                                # Repeat pixels to match Y plane dimensions
                                u = np.repeat(np.repeat(u, height_ratio, axis=0), 
                                             width_ratio, axis=1)
                                v = np.repeat(np.repeat(v, height_ratio, axis=0),
                                             width_ratio, axis=1)
                                # Trim to exact size if needed
                                u = u[:y.shape[0], :y.shape[1]]
                                v = v[:y.shape[0], :y.shape[1]]
                        else:
                            # Invalid chroma plane size - create neutral chroma
                            u = np.full_like(y, 128, dtype=np.uint8)
                            v = np.full_like(y, 128, dtype=np.uint8)
                    
                    # YUV to RGB conversion (ITU-R BT.601)
                    y_f = y.astype(np.float32)
                    u_f = u.astype(np.float32) - 128
                    v_f = v.astype(np.float32) - 128
                    
                    r = y_f + 1.402 * v_f
                    g = y_f - 0.344136 * u_f - 0.714136 * v_f
                    b = y_f + 1.772 * u_f
                    
                    # Clip and convert to uint8
                    r = np.clip(r, 0, 255).astype(np.uint8)
                    g = np.clip(g, 0, 255).astype(np.uint8)
                    b = np.clip(b, 0, 255).astype(np.uint8)
                    
                    # Stack into RGB array
                    rgb_array = np.stack([r, g, b], axis=-1)
                
                # Write frame data to FFmpeg stdin
                try:
                    ffmpeg_process.stdin.write(rgb_array.tobytes())
                except BrokenPipeError:
                    # FFmpeg process died - get error details
                    logger.error("FFmpeg process died unexpectedly while writing frame")
                    ffmpeg_process.stdin.close()
                    stdout, stderr = ffmpeg_process.communicate()
                    error_msg = stderr.decode('utf-8', errors='ignore')
                    logger.error(f"FFmpeg stderr: {error_msg}")
                    raise RuntimeError(f"FFmpeg process terminated unexpectedly: {error_msg}")
            
            # Close stdin to signal end of input
            ffmpeg_process.stdin.close()
            
            # Wait for FFmpeg to finish and capture output
            stdout, stderr = ffmpeg_process.communicate()
            
            if ffmpeg_process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore')
                logger.error(f"FFmpeg failed with return code {ffmpeg_process.returncode}")
                logger.error(f"FFmpeg stderr: {error_msg}")
                raise RuntimeError(f"Video export failed: {error_msg}")
            
            logger.info(f"Successfully exported video to {output_path}")
            
        except Exception as e:
            logger.error(f"Error during video export: {e}")
            raise

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
