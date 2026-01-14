"""
Logging utilities and progress tracking.
"""

import logging
from pathlib import Path
from typing import Dict, Optional
import json
from datetime import datetime


class ProcessingLogger:
    """Logger for processing metrics and progress."""

    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize processing logger.

        Args:
            log_dir: Directory for log files (default: current directory)
        """
        self.log_dir = Path(log_dir) if log_dir else Path.cwd()
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_job_start(self, job_id: str, input_file: str, output_file: str) -> None:
        """
        Log job start.

        Args:
            job_id: Job identifier
            input_file: Input file path
            output_file: Output file path
        """
        log_entry = {
            'job_id': job_id,
            'timestamp': datetime.now().isoformat(),
            'event': 'start',
            'input': input_file,
            'output': output_file
        }
        self._write_log(job_id, log_entry)

    def log_job_complete(self, job_id: str, metrics: Dict[str, any]) -> None:
        """
        Log job completion.

        Args:
            job_id: Job identifier
            metrics: Processing metrics
        """
        log_entry = {
            'job_id': job_id,
            'timestamp': datetime.now().isoformat(),
            'event': 'complete',
            'metrics': metrics
        }
        self._write_log(job_id, log_entry)

    def log_job_error(self, job_id: str, error: str) -> None:
        """
        Log job error.

        Args:
            job_id: Job identifier
            error: Error message
        """
        log_entry = {
            'job_id': job_id,
            'timestamp': datetime.now().isoformat(),
            'event': 'error',
            'error': error
        }
        self._write_log(job_id, log_entry)

    def _write_log(self, job_id: str, entry: Dict[str, any]) -> None:
        """
        Write log entry to file.

        Args:
            job_id: Job identifier
            entry: Log entry
        """
        log_file = self.log_dir / f"{job_id}.json"
        
        # Read existing logs
        logs = []
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = json.load(f)
        
        # Append new entry
        logs.append(entry)
        
        # Write back
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
