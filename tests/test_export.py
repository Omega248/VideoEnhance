"""
Tests for video export functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import subprocess

from videoenhance.core.pipeline import Pipeline, PipelineConfig


class TestVideoExport(unittest.TestCase):
    """Test video export functionality."""

    def test_get_codec_args_hevc(self):
        """Test codec arguments for HEVC."""
        config = PipelineConfig(output_codec="hevc", output_crf=18, output_preset="slow")
        pipeline = Pipeline(config=config)
        
        args = pipeline._get_codec_args()
        
        self.assertIn("-c:v", args)
        self.assertIn("libx265", args)
        self.assertIn("-crf", args)
        self.assertIn("18", args)
        self.assertIn("-preset", args)
        self.assertIn("slow", args)

    def test_get_codec_args_av1(self):
        """Test codec arguments for AV1."""
        config = PipelineConfig(output_codec="av1", output_crf=25, output_preset="fast")
        pipeline = Pipeline(config=config)
        
        args = pipeline._get_codec_args()
        
        self.assertIn("-c:v", args)
        self.assertIn("libsvtav1", args)
        self.assertIn("-crf", args)
        self.assertIn("25", args)
        self.assertIn("-preset", args)
        self.assertIn("fast", args)

    def test_get_codec_args_gpu(self):
        """Test codec arguments with GPU acceleration."""
        config = PipelineConfig(output_codec="hevc", use_gpu=True)
        pipeline = Pipeline(config=config)
        
        args = pipeline._get_codec_args()
        
        self.assertIn("-c:v", args)
        self.assertIn("hevc_nvenc", args)

    def test_export_video_requires_vapoursynth(self):
        """Test that export raises error without VapourSynth."""
        # Temporarily disable VapourSynth
        import videoenhance.core.pipeline as pipeline_module
        original_has_vs = pipeline_module.HAS_VAPOURSYNTH
        
        try:
            pipeline_module.HAS_VAPOURSYNTH = False
            
            config = PipelineConfig()
            pipeline = Pipeline(config=config)
            
            # Should raise ImportError
            with self.assertRaises(ImportError) as context:
                pipeline._export_video(None, '/test/output.mp4', {}, None)
            
            self.assertIn('VapourSynth is required', str(context.exception))
        finally:
            pipeline_module.HAS_VAPOURSYNTH = original_has_vs

    def test_export_video_accepts_progress_callback(self):
        """Test that export accepts progress_callback parameter."""
        import videoenhance.core.pipeline as pipeline_module
        original_has_vs = pipeline_module.HAS_VAPOURSYNTH
        
        try:
            # Disable VapourSynth to avoid actual processing
            pipeline_module.HAS_VAPOURSYNTH = False
            
            config = PipelineConfig()
            pipeline = Pipeline(config=config)
            
            # Create a mock progress callback
            progress_callback = Mock()
            
            # Should raise ImportError but accept the callback parameter
            with self.assertRaises(ImportError):
                pipeline._export_video(None, '/test/output.mp4', {}, progress_callback)
                
        finally:
            pipeline_module.HAS_VAPOURSYNTH = original_has_vs

    @patch('subprocess.Popen')
    def test_export_uses_devnull_for_stdout_stderr(self, mock_popen):
        """Test that export uses DEVNULL for stdout/stderr to prevent deadlock."""
        import videoenhance.core.pipeline as pipeline_module
        
        # Skip if VapourSynth is not available
        if not pipeline_module.HAS_VAPOURSYNTH:
            self.skipTest("VapourSynth not available")
        
        # Create mock clip with minimal properties
        mock_clip = Mock()
        mock_clip.num_frames = 10
        mock_clip.width = 640
        mock_clip.height = 480
        mock_clip.fps = Mock(numerator=30, denominator=1)
        
        # Mock get_frame to return a simple frame
        mock_frame = Mock()
        mock_frame.format = Mock(
            color_family=pipeline_module.vs.RGB,
            num_planes=3,
            sample_type=pipeline_module.vs.INTEGER,
            bits_per_sample=8
        )
        
        # Create simple numpy arrays for RGB planes
        import numpy as np
        plane_data = np.zeros((480, 640), dtype=np.uint8)
        mock_frame.__getitem__ = Mock(side_effect=lambda x: plane_data)
        mock_clip.get_frame = Mock(return_value=mock_frame)
        
        # Mock FFmpeg process
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.stdin.write = Mock()
        mock_process.stdin.close = Mock()
        mock_process.wait = Mock(return_value=0)
        mock_popen.return_value = mock_process
        
        # Create pipeline and export
        config = PipelineConfig()
        pipeline = Pipeline(config=config)
        
        # Call export - we're only interested in verifying Popen arguments
        # The export may fail due to mocking limitations, but Popen will be called first
        try:
            pipeline._export_video(mock_clip, '/tmp/test_output.mp4', {}, None)
        except (AttributeError, TypeError, RuntimeError) as e:
            # Expected exceptions due to incomplete mocking
            # AttributeError: mock objects missing expected attributes
            # TypeError: type mismatches in mock setup  
            # RuntimeError: FFmpeg-related errors from incomplete mock
            pass
        
        # Verify that Popen was called with DEVNULL for stdout and stderr
        self.assertTrue(mock_popen.called, "Popen should have been called")
        call_kwargs = mock_popen.call_args[1]
        self.assertEqual(call_kwargs['stdout'], subprocess.DEVNULL,
                        "stdout should be DEVNULL to prevent buffer deadlock")
        self.assertEqual(call_kwargs['stderr'], subprocess.DEVNULL,
                        "stderr should be DEVNULL to prevent buffer deadlock")


if __name__ == '__main__':
    unittest.main()
