"""
Tests for video detector module.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from videoenhance.core.detector import VideoDetector


class TestVideoDetector(unittest.TestCase):
    """Test VideoDetector class."""

    def test_is_sd_resolution(self):
        """Test SD resolution detection."""
        # SD resolutions
        self.assertTrue(VideoDetector.is_sd_resolution(720, 480))  # NTSC
        self.assertTrue(VideoDetector.is_sd_resolution(720, 576))  # PAL
        self.assertTrue(VideoDetector.is_sd_resolution(640, 480))
        
        # HD resolutions
        self.assertFalse(VideoDetector.is_sd_resolution(1280, 720))
        self.assertFalse(VideoDetector.is_sd_resolution(1920, 1080))

    @patch('videoenhance.core.detector.HAS_AV', True)
    @patch('videoenhance.core.detector.av')
    def test_validate_file_valid(self, mock_av):
        """Test file validation with valid video."""
        mock_container = MagicMock()
        mock_container.streams.video = [MagicMock()]
        mock_av.open.return_value = mock_container

        result = VideoDetector.validate_file("test.avi")
        
        self.assertTrue(result)
        mock_container.close.assert_called_once()

    @patch('videoenhance.core.detector.HAS_AV', True)
    @patch('videoenhance.core.detector.av')
    def test_validate_file_invalid(self, mock_av):
        """Test file validation with invalid video."""
        mock_av.open.side_effect = Exception("Invalid file")

        result = VideoDetector.validate_file("test.avi")
        
        self.assertFalse(result)

    @patch('videoenhance.core.detector.HAS_AV', True)
    @patch('videoenhance.core.detector.av')
    def test_detect_properties(self, mock_av):
        """Test video property detection."""
        # Setup mock
        mock_stream = MagicMock()
        mock_stream.width = 720
        mock_stream.height = 480
        mock_stream.codec_context.name = "mpeg2video"
        mock_stream.average_rate = 29.97
        mock_stream.pix_fmt = "yuv420p"
        mock_stream.field_order = None
        
        mock_container = MagicMock()
        mock_container.format.name = "avi"
        mock_container.streams.video = [mock_stream]
        mock_container.duration = 1000000
        
        mock_av.open.return_value = mock_container
        mock_av.time_base = 1000000

        # Create temporary file for testing
        with patch('pathlib.Path.exists', return_value=True):
            properties = VideoDetector.detect("test.avi")

        # Verify properties
        self.assertEqual(properties['width'], 720)
        self.assertEqual(properties['height'], 480)
        self.assertEqual(properties['codec'], "mpeg2video")
        self.assertEqual(properties['container'], "avi")
        self.assertFalse(properties['interlaced'])


if __name__ == '__main__':
    unittest.main()
