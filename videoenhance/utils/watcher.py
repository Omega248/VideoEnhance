"""
File watcher utility for automatic video processing.
"""

from pathlib import Path
from typing import Callable, List, Optional
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

logger = logging.getLogger(__name__)


class VideoFileHandler(FileSystemEventHandler):
    """Handler for new video file events."""

    def __init__(self, callback: Callable[[str], None], 
                 extensions: Optional[List[str]] = None):
        """
        Initialize file handler.

        Args:
            callback: Function to call when new video is detected
            extensions: List of video file extensions to watch
        """
        self.callback = callback
        self.extensions = extensions or [
            '.avi', '.mkv', '.mp4', '.mov', '.mpg', '.mpeg', '.m2v', '.vob'
        ]

    def on_created(self, event: FileCreatedEvent):
        """
        Handle file creation event.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix.lower() in self.extensions:
            logger.info(f"New video file detected: {file_path}")
            self.callback(str(file_path))


class FileWatcher:
    """Watches a directory for new video files."""

    def __init__(self, watch_dir: str, callback: Callable[[str], None],
                 extensions: Optional[List[str]] = None):
        """
        Initialize file watcher.

        Args:
            watch_dir: Directory to watch
            callback: Function to call when new video is detected
            extensions: List of video file extensions to watch
        """
        self.watch_dir = Path(watch_dir)
        self.callback = callback
        self.extensions = extensions

        self.observer = Observer()
        self.handler = VideoFileHandler(callback, extensions)

    def start(self):
        """Start watching directory."""
        self.observer.schedule(self.handler, str(self.watch_dir), recursive=False)
        self.observer.start()
        logger.info(f"Started watching directory: {self.watch_dir}")

    def stop(self):
        """Stop watching directory."""
        self.observer.stop()
        self.observer.join()
        logger.info("Stopped watching directory")
