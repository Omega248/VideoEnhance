"""
Tests for processing queue.
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from videoenhance.core.queue import ProcessingQueue, ProcessingJob, JobStatus
from videoenhance.core.pipeline import PipelineConfig


class TestProcessingQueue(unittest.TestCase):
    """Test ProcessingQueue class."""

    def test_queue_initialization(self):
        """Test queue initialization."""
        queue = ProcessingQueue()
        
        self.assertIsNotNone(queue.config)
        self.assertEqual(queue.num_workers, 1)
        self.assertFalse(queue.running)

    def test_add_job(self):
        """Test adding a job to queue."""
        queue = ProcessingQueue()
        
        job_id = queue.add_job("input.avi", "output.mp4")
        
        self.assertIn(job_id, queue.jobs)
        self.assertEqual(queue.jobs[job_id].status, JobStatus.PENDING)
        self.assertEqual(str(queue.jobs[job_id].input_path), "input.avi")

    def test_get_job_status(self):
        """Test getting job status."""
        queue = ProcessingQueue()
        
        job_id = queue.add_job("input.avi", "output.mp4")
        job = queue.get_job_status(job_id)
        
        self.assertIsNotNone(job)
        self.assertEqual(job.status, JobStatus.PENDING)

    def test_cancel_job(self):
        """Test cancelling a pending job."""
        queue = ProcessingQueue()
        
        job_id = queue.add_job("input.avi", "output.mp4")
        result = queue.cancel_job(job_id)
        
        self.assertTrue(result)
        self.assertEqual(queue.jobs[job_id].status, JobStatus.CANCELLED)

    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.mkdir')
    def test_add_directory(self, mock_mkdir, mock_iterdir):
        """Test adding directory of videos."""
        # Mock directory contents
        mock_file1 = MagicMock()
        mock_file1.is_file.return_value = True
        mock_file1.suffix = ".avi"
        mock_file1.stem = "video1"
        
        mock_file2 = MagicMock()
        mock_file2.is_file.return_value = True
        mock_file2.suffix = ".mkv"
        mock_file2.stem = "video2"
        
        mock_iterdir.return_value = [mock_file1, mock_file2]
        
        queue = ProcessingQueue()
        job_ids = queue.add_directory("/input", "/output")
        
        self.assertEqual(len(job_ids), 2)


if __name__ == '__main__':
    unittest.main()
