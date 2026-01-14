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


if __name__ == '__main__':
    unittest.main()
