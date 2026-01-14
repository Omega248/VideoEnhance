"""
Example usage of VideoEnhance library.
"""

from videoenhance import Pipeline, VideoDetector
from videoenhance.core.pipeline import PipelineConfig

# Example 1: Basic usage with defaults
def example_basic():
    """Process a video with default settings."""
    pipeline = Pipeline()
    result = pipeline.process(
        "input.avi",
        "output.mp4"
    )
    print(f"Processed: {result}")

# Example 2: Custom configuration
def example_custom():
    """Process a video with custom settings."""
    config = PipelineConfig(
        denoise_strength=1.5,
        sharpen_strength=0.4,
        output_codec="hevc",
        output_crf=18,
        use_gpu=True
    )
    
    pipeline = Pipeline(config=config)
    result = pipeline.process(
        "input.avi",
        "output.mp4"
    )
    print(f"Processed: {result}")

# Example 3: Detect video properties
def example_detect():
    """Detect video properties."""
    detector = VideoDetector()
    properties = detector.detect("input.avi")
    
    print(f"Resolution: {properties['width']}x{properties['height']}")
    print(f"FPS: {properties['fps']}")
    print(f"Interlaced: {properties['interlaced']}")
    print(f"Codec: {properties['codec']}")

# Example 4: Batch processing with queue
def example_batch():
    """Process multiple videos using queue."""
    from videoenhance.core.queue import ProcessingQueue
    
    config = PipelineConfig(output_codec="hevc", output_crf=20)
    queue = ProcessingQueue(config=config, num_workers=2)
    
    # Add jobs
    job_ids = queue.add_directory(
        "/path/to/input/videos",
        "/path/to/output/videos"
    )
    
    # Start processing
    queue.start()
    
    # Monitor progress
    import time
    while True:
        all_done = True
        for job_id in job_ids:
            job = queue.get_job_status(job_id)
            if job and job.status.value in ["pending", "processing"]:
                all_done = False
                print(f"{job_id}: {job.progress}%")
        
        if all_done:
            break
        
        time.sleep(2)
    
    queue.stop()
    print("All jobs completed!")


if __name__ == "__main__":
    # Uncomment the example you want to run
    # example_basic()
    # example_custom()
    # example_detect()
    # example_batch()
    pass
