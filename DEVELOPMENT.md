# VideoEnhance Development Guide

## Project Structure

```
VideoEnhance/
├── videoenhance/           # Main package
│   ├── core/              # Core functionality
│   │   ├── detector.py    # Video format detection
│   │   ├── pipeline.py    # Main enhancement pipeline
│   │   └── queue.py       # Batch processing queue
│   ├── filters/           # Enhancement filters
│   │   ├── deinterlace.py # QTGMC deinterlacing
│   │   ├── denoise.py     # Temporal denoise
│   │   ├── sharpen.py     # Mild sharpening
│   │   ├── deflicker.py   # Luminance stabilization
│   │   ├── color.py       # Color normalization
│   │   └── artifacts.py   # Compression artifact cleanup
│   ├── utils/             # Utilities
│   │   ├── watcher.py     # File watching
│   │   └── logging.py     # Progress logging
│   ├── gui/               # GUI components (placeholder)
│   └── cli.py             # Command-line interface
├── tests/                 # Unit tests
├── examples.py            # Usage examples
├── requirements.txt       # Python dependencies
└── setup.py              # Package setup

## Installation

### Prerequisites

1. **Python 3.8+**
2. **VapourSynth** (video processing framework)
   - Linux: Install from your distribution's package manager
   - Windows: Download from http://www.vapoursynth.com/
   - macOS: Install via Homebrew
3. **FFmpeg** (video encoding)
   - Install from https://ffmpeg.org/ or via package manager

### Install Package

```bash
# Install in development mode
pip install -e .

# Or install normally
pip install .

# Install with GUI support
pip install -e ".[gui]"
```

## Usage

### Command Line Interface

#### Process a Single File

```bash
# Basic usage with defaults
videoenhance process input.avi --output output.mp4

# Custom settings
videoenhance process input.avi \
  --output output.mp4 \
  --codec hevc \
  --crf 18 \
  --denoise 1.5 \
  --sharpen 0.4 \
  --gpu
```

#### Batch Processing

```bash
# Process all videos in a directory
videoenhance batch /path/to/input /path/to/output

# With multiple workers
videoenhance batch /path/to/input /path/to/output --workers 2
```

#### Get Video Information

```bash
videoenhance info video.avi
```

### Python API

#### Basic Processing

```python
from videoenhance import Pipeline

pipeline = Pipeline()
result = pipeline.process("input.avi", "output.mp4")
print(f"Success: {result['success']}")
```

#### Custom Configuration

```python
from videoenhance import Pipeline
from videoenhance.core.pipeline import PipelineConfig

config = PipelineConfig(
    denoise_strength=2.0,
    sharpen_strength=0.4,
    output_codec="hevc",
    output_crf=18,
    use_gpu=True
)

pipeline = Pipeline(config=config)
result = pipeline.process("input.avi", "output.mp4")
```

#### Batch Processing with Queue

```python
from videoenhance.core.queue import ProcessingQueue
from videoenhance.core.pipeline import PipelineConfig

config = PipelineConfig(output_codec="hevc")
queue = ProcessingQueue(config=config, num_workers=2)

# Add multiple jobs
job_ids = queue.add_directory("/input/dir", "/output/dir")

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
```

## Pipeline Configuration

### Deinterlacing
- `deinterlace_preset`: QTGMC preset ("Fast", "Medium", "Slow", etc.)
- Applied automatically for interlaced content

### Denoising
- `denoise_strength`: 0.0 to 3.0 (default: 1.0)
- `denoise_radius`: 1 to 3 frames (default: 2)
- Temporal-only, no spatial blur

### Sharpening
- `sharpen_strength`: 0.0 to 1.0 (default: 0.3)
- `sharpen_radius`: 1 or 2 (default: 1)
- Low-radius, halo-free

### Deflicker
- `deflicker_strength`: 0.0 to 1.0 (default: 0.5)
- `deflicker_radius`: 1 to 5 frames (default: 3)
- Stabilizes luminance fluctuations

### Color Normalization
- `auto_white_balance`: Enable/disable automatic white balance
- `auto_contrast`: Enable/disable automatic contrast
- `gamma`: Gamma correction (default: 1.0)

### Artifact Cleanup
- `cleanup_artifacts`: Enable/disable (default: True)
- `artifact_strength`: 0.0 to 1.0 (default: 0.5)

### Output
- `output_codec`: "hevc" or "av1" (default: "hevc")
- `output_crf`: 0 to 51 (default: 20, lower = better quality)
- `output_preset`: FFmpeg preset (default: "medium")

### GPU Acceleration
- `use_gpu`: Enable/disable GPU acceleration
- `gpu_device`: GPU device ID (default: 0)

## Testing

Run the test suite:

```bash
# Run all tests
python -m unittest discover tests/ -v

# Run specific test module
python -m unittest tests.test_pipeline -v

# Run with pytest (if installed)
pytest tests/ -v
```

## Architecture

### Modular Design

Each enhancement stage is independent and can be:
- Enabled/disabled individually
- Configured with custom parameters
- Swapped with alternative implementations
- Tested in isolation

### Error Handling

- Automatic detection of invalid/corrupted files
- Graceful degradation when optional dependencies are missing
- Detailed error logging for troubleshooting

### Progress Tracking

- Per-job progress callbacks
- Detailed logging of each processing stage
- Output metrics and statistics

## Development

### Adding a New Filter

1. Create a new file in `videoenhance/filters/`
2. Implement a filter class with an `apply()` method
3. Add configuration options to `PipelineConfig`
4. Integrate into `Pipeline._apply_pipeline()`
5. Add tests in `tests/`

Example:

```python
# videoenhance/filters/myfilter.py
import vapoursynth as vs
import logging

logger = logging.getLogger(__name__)
core = vs.core

class MyFilter:
    def __init__(self, strength: float = 1.0):
        self.strength = strength
    
    def apply(self, clip: vs.VideoNode) -> vs.VideoNode:
        logger.info(f"Applying my filter: strength={self.strength}")
        # Process clip
        return clip
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints for function signatures
- Document all public APIs with docstrings
- Keep functions focused and testable

## Troubleshooting

### VapourSynth Import Errors

If you get `ModuleNotFoundError: No module named 'vapoursynth'`:
- Ensure VapourSynth is properly installed on your system
- Check that the Python bindings are available
- Verify your Python version is compatible (3.8+)

### FFmpeg Encoding Errors

If video export fails:
- Verify FFmpeg is installed and in your PATH
- Check that the chosen codec is available (`ffmpeg -codecs`)
- Try a different codec or preset

### GPU Acceleration Issues

If GPU acceleration doesn't work:
- Verify CUDA/OpenCL is installed
- Check GPU driver versions
- Try disabling GPU acceleration (`use_gpu=False`)

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

See LICENSE file for details.
