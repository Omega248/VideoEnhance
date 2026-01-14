"""
Tests for pipeline configuration and structure.
"""

import unittest
from videoenhance.core.pipeline import Pipeline, PipelineConfig


class TestPipelineConfig(unittest.TestCase):
    """Test PipelineConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PipelineConfig()
        
        self.assertEqual(config.deinterlace_preset, "Fast")
        self.assertEqual(config.denoise_strength, 1.0)
        self.assertEqual(config.sharpen_strength, 0.3)
        self.assertEqual(config.output_codec, "hevc")
        self.assertEqual(config.output_crf, 20)
        self.assertFalse(config.use_gpu)

    def test_custom_config(self):
        """Test custom configuration values."""
        config = PipelineConfig(
            denoise_strength=2.0,
            output_codec="av1",
            use_gpu=True
        )
        
        self.assertEqual(config.denoise_strength, 2.0)
        self.assertEqual(config.output_codec, "av1")
        self.assertTrue(config.use_gpu)


class TestPipeline(unittest.TestCase):
    """Test Pipeline class."""

    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        pipeline = Pipeline()
        
        self.assertIsNotNone(pipeline.config)
        self.assertIsNotNone(pipeline.detector)

    def test_pipeline_with_custom_config(self):
        """Test pipeline with custom configuration."""
        config = PipelineConfig(denoise_strength=2.0)
        pipeline = Pipeline(config=config)
        
        self.assertEqual(pipeline.config.denoise_strength, 2.0)


if __name__ == '__main__':
    unittest.main()
