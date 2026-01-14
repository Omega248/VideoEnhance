"""
Queue system for batch video processing.
"""

from pathlib import Path
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import threading
from queue import Queue, Empty
import time

from .pipeline import Pipeline, PipelineConfig

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Status of a processing job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingJob:
    """Represents a video processing job."""
    id: str
    input_path: Path
    output_path: Path
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class ProcessingQueue:
    """Queue system for batch processing multiple videos."""

    def __init__(self, config: Optional[PipelineConfig] = None, num_workers: int = 1):
        """
        Initialize processing queue.

        Args:
            config: Pipeline configuration to use for all jobs
            num_workers: Number of concurrent processing workers
        """
        self.config = config or PipelineConfig()
        self.num_workers = num_workers
        self.pipeline = Pipeline(config=self.config)
        
        self.jobs: Dict[str, ProcessingJob] = {}
        self.queue: Queue = Queue()
        self.workers: List[threading.Thread] = []
        self.running = False
        self.job_counter = 0
        
        self._lock = threading.Lock()

    def add_job(self, input_path: str, output_path: str) -> str:
        """
        Add a job to the queue.

        Args:
            input_path: Path to input video
            output_path: Path to output video

        Returns:
            Job ID
        """
        with self._lock:
            job_id = f"job_{self.job_counter:04d}"
            self.job_counter += 1

        job = ProcessingJob(
            id=job_id,
            input_path=Path(input_path),
            output_path=Path(output_path)
        )

        with self._lock:
            self.jobs[job_id] = job
        
        self.queue.put(job_id)
        logger.info(f"Added job {job_id}: {input_path} -> {output_path}")

        return job_id

    def add_directory(self, input_dir: str, output_dir: str, 
                     extensions: Optional[List[str]] = None) -> List[str]:
        """
        Add all videos in a directory to the queue.

        Args:
            input_dir: Input directory path
            output_dir: Output directory path
            extensions: List of file extensions to process (default: common video formats)

        Returns:
            List of job IDs
        """
        if extensions is None:
            extensions = ['.avi', '.mkv', '.mp4', '.mov', '.mpg', '.mpeg', '.m2v', '.vob']

        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        job_ids = []

        for video_file in input_path.iterdir():
            if video_file.is_file() and video_file.suffix.lower() in extensions:
                output_file = output_path / f"{video_file.stem}_enhanced.mp4"
                job_id = self.add_job(str(video_file), str(output_file))
                job_ids.append(job_id)

        logger.info(f"Added {len(job_ids)} jobs from directory {input_dir}")
        return job_ids

    def start(self) -> None:
        """Start processing queue."""
        if self.running:
            logger.warning("Queue is already running")
            return

        self.running = True
        
        for i in range(self.num_workers):
            worker = threading.Thread(target=self._worker, args=(i,), daemon=True)
            worker.start()
            self.workers.append(worker)

        logger.info(f"Started queue with {self.num_workers} workers")

    def stop(self) -> None:
        """Stop processing queue."""
        self.running = False
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5.0)

        self.workers.clear()
        logger.info("Stopped queue")

    def _worker(self, worker_id: int) -> None:
        """
        Worker thread for processing jobs.

        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # Get next job with timeout
                job_id = self.queue.get(timeout=1.0)
                
                with self._lock:
                    if job_id not in self.jobs:
                        continue
                    job = self.jobs[job_id]

                # Process the job
                self._process_job(job, worker_id)

            except Empty:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")

        logger.info(f"Worker {worker_id} stopped")

    def _process_job(self, job: ProcessingJob, worker_id: int) -> None:
        """
        Process a single job.

        Args:
            job: Job to process
            worker_id: Worker identifier
        """
        logger.info(f"Worker {worker_id} processing job {job.id}")

        # Update job status
        with self._lock:
            job.status = JobStatus.PROCESSING
            job.start_time = time.time()

        try:
            # Progress callback
            def progress_callback(message: str, percent: float):
                with self._lock:
                    job.progress = percent
                logger.debug(f"Job {job.id}: {message} ({percent}%)")

            # Process video
            result = self.pipeline.process(
                str(job.input_path),
                str(job.output_path),
                progress_callback=progress_callback
            )

            # Update job status
            with self._lock:
                job.status = JobStatus.COMPLETED
                job.end_time = time.time()
                job.progress = 100.0

            logger.info(f"Job {job.id} completed successfully")

        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}")
            
            with self._lock:
                job.status = JobStatus.FAILED
                job.error = str(e)
                job.end_time = time.time()

    def get_job_status(self, job_id: str) -> Optional[ProcessingJob]:
        """
        Get status of a job.

        Args:
            job_id: Job identifier

        Returns:
            Job object or None if not found
        """
        with self._lock:
            return self.jobs.get(job_id)

    def get_all_jobs(self) -> List[ProcessingJob]:
        """
        Get all jobs.

        Returns:
            List of all jobs
        """
        with self._lock:
            return list(self.jobs.values())

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending job.

        Args:
            job_id: Job identifier

        Returns:
            True if cancelled, False otherwise
        """
        with self._lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                if job.status == JobStatus.PENDING:
                    job.status = JobStatus.CANCELLED
                    return True
        return False
