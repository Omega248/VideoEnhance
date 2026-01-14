# Quick Start Guide

This guide will help you get started with VideoEnhance quickly.

## Prerequisites

Before using VideoEnhance, ensure you have:

1. **Python 3.8 or higher**
2. **VapourSynth** - Video processing framework
   - Download from: http://www.vapoursynth.com/
   - Or install via package manager
3. **FFmpeg** - Video encoding
   - Download from: https://ffmpeg.org/
   - Or install via package manager: `apt install ffmpeg` / `brew install ffmpeg`

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/Omega248/VideoEnhance.git
cd VideoEnhance

# Install the package
pip install -e .
```

### Install with GUI Support

```bash
pip install -e ".[gui]"
```

## Basic Usage

### 1. Process a Single Video

The simplest way to enhance a video:

```bash
videoenhance process input.avi --output output.mp4
```

This will apply all enhancement filters with default settings.

### 2. Custom Processing

Adjust enhancement parameters:

```bash
videoenhance process input.avi \
  --output output.mp4 \
  --codec hevc \
  --crf 18 \
  --denoise 1.5 \
  --sharpen 0.4 \
  --deflicker 0.6
```

**Parameters:**
- `--codec`: Video codec (hevc or av1)
- `--crf`: Quality (0-51, lower = better, default: 20)
- `--denoise`: Denoise strength (0.0-3.0, default: 1.0)
- `--sharpen`: Sharpen strength (0.0-1.0, default: 0.3)
- `--deflicker`: Deflicker strength (0.0-1.0, default: 0.5)

### 3. Batch Process Multiple Videos

Process all videos in a directory:

```bash
videoenhance batch /path/to/input/videos /path/to/output/videos
```

With multiple workers (faster):

```bash
videoenhance batch /path/to/input/videos /path/to/output/videos --workers 2
```

### 4. Check Video Information

Before processing, check what you're working with:

```bash
videoenhance info video.avi
```

Output example:
```
Video Information: video.avi

  Container:    avi
  Codec:        mpeg2video
  Resolution:   720x480
  FPS:          29.97
  Duration:     1800.00s
  Interlaced:   True
  Field Order:  tff
  Pixel Format: yuv420p
  SD Resolution: True
```

## Using the Python API

### Simple Processing

```python
from videoenhance import Pipeline

# Create pipeline with defaults
pipeline = Pipeline()

# Process video
result = pipeline.process("input.avi", "output.mp4")

print(f"Success: {result['success']}")
print(f"Output: {result['output']}")
```

### Custom Configuration

```python
from videoenhance import Pipeline
from videoenhance.core.pipeline import PipelineConfig

# Create custom configuration
config = PipelineConfig(
    # Denoising
    denoise_strength=2.0,
    denoise_radius=2,
    
    # Sharpening
    sharpen_strength=0.4,
    sharpen_radius=1,
    
    # Color
    auto_white_balance=True,
    auto_contrast=True,
    gamma=1.0,
    
    # Output
    output_codec="hevc",
    output_crf=18,
    output_preset="slow",
    
    # GPU
    use_gpu=True
)

# Create pipeline with config
pipeline = Pipeline(config=config)

# Process video
result = pipeline.process("input.avi", "output.mp4")
```

### Batch Processing

```python
from videoenhance.core.queue import ProcessingQueue
from videoenhance.core.pipeline import PipelineConfig
import time

# Create configuration
config = PipelineConfig(output_codec="hevc", output_crf=20)

# Create queue with 2 workers
queue = ProcessingQueue(config=config, num_workers=2)

# Add all videos from directory
job_ids = queue.add_directory(
    "/path/to/input/videos",
    "/path/to/output/videos"
)

print(f"Added {len(job_ids)} videos to queue")

# Start processing
queue.start()

# Monitor progress
try:
    while True:
        all_done = True
        for job_id in job_ids:
            job = queue.get_job_status(job_id)
            if job:
                print(f"{job_id}: {job.status.value} ({job.progress}%)")
                if job.status.value in ["pending", "processing"]:
                    all_done = False
        
        if all_done:
            break
        
        time.sleep(2)
finally:
    queue.stop()

print("All processing complete!")
```

## Understanding the Pipeline

VideoEnhance processes videos through these stages:

1. **Format Detection** → Analyzes video properties
2. **Deinterlacing** → Converts interlaced to progressive (if needed)
3. **Temporal Denoise** → Removes noise without blurring
4. **Sharpening** → Enhances details without halos
5. **Deflicker** → Stabilizes brightness fluctuations
6. **Color Normalization** → Adjusts white balance, gamma, contrast
7. **Artifact Cleanup** → Removes compression artifacts (optional)
8. **Export** → Encodes to H.265 or AV1

Each stage can be configured independently!

## Common Use Cases

### Restore Old TV Episodes

```bash
videoenhance process "Star Trek Voyager S01E01.avi" \
  --output "Star Trek Voyager S01E01 Enhanced.mp4" \
  --codec hevc \
  --crf 18 \
  --denoise 1.5 \
  --deflicker 0.7
```

### Clean Up VHS Captures

```bash
videoenhance process vhs_capture.avi \
  --output vhs_cleaned.mp4 \
  --denoise 2.0 \
  --deflicker 0.8 \
  --sharpen 0.2
```

### Batch Process TV Series

```bash
# Process entire season
videoenhance batch "/TV Shows/Star Trek Voyager/Season 01" \
  "/TV Shows/Star Trek Voyager/Season 01 Enhanced" \
  --workers 2 \
  --codec hevc \
  --crf 20
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'vapoursynth'"

**Solution:** Install VapourSynth on your system. It's not a Python package but a system library.
- Windows: Download installer from vapoursynth.com
- Linux: `sudo apt install vapoursynth` or similar
- macOS: `brew install vapoursynth`

### "No video stream found"

**Solution:** The file might be corrupted or not a video file. Check with:
```bash
videoenhance info yourfile.avi
```

### Processing is slow

**Solutions:**
1. Enable GPU acceleration: `--gpu`
2. Use faster preset: `--preset fast`
3. Use multiple workers for batch: `--workers 4`
4. Lower CRF for smaller file (at cost of quality): `--crf 24`

### Video looks over-processed

**Solutions:**
1. Reduce denoise strength: `--denoise 0.5`
2. Reduce sharpen strength: `--sharpen 0.2`
3. Disable artifact cleanup: `--no-artifacts`

## Configuration File

Create `config.yaml` for reusable settings:

```yaml
denoise:
  strength: 1.5
  radius: 2

sharpen:
  strength: 0.4
  radius: 1

deflicker:
  strength: 0.6
  radius: 3

output:
  codec: "hevc"
  crf: 18
  preset: "medium"

gpu:
  enabled: true
```

Then use: `videoenhance process input.avi --config config.yaml`

## Getting Help

```bash
# General help
videoenhance --help

# Command-specific help
videoenhance process --help
videoenhance batch --help
videoenhance info --help
```

## Next Steps

- Read [DEVELOPMENT.md](DEVELOPMENT.md) for advanced usage
- Check [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for feature details
- See [examples.py](examples.py) for more code examples

## Tips for Best Results

1. **Always check video info first** to understand what you're working with
2. **Start with defaults** and adjust from there
3. **Process a short clip first** to test settings
4. **Use consistent settings** for a series to maintain visual consistency
5. **Keep original files** until you're satisfied with results
6. **Monitor disk space** when batch processing

Happy enhancing! 🎬✨
