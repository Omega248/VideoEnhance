# VideoEnhance

An automated video enhancement pipeline designed to process SD interlaced video files (such as legacy TV episodes) through a comprehensive enhancement workflow, producing cleaned progressive output.

## Features

- **Automatic Format Detection**: Detects container, codec, resolution, and interlaced/progressive status
- **Deinterlacing**: Uses QTGMC Fast preset via VapourSynth for high-quality deinterlacing
- **Temporal Denoising**: Reduces noise without spatial blur or detail smearing
- **Sharpening**: Applies mild, low-radius sharpening without halos
- **Deflicker**: Stabilizes luminance fluctuations from tape sources
- **Color Normalization**: Automatic white balance, gamma, and contrast adjustment
- **Compression Artifact Cleanup**: Preserves edges while cleaning artifacts
- **Batch Processing**: Queue system for processing multiple episodes
- **GPU Acceleration**: CUDA/OpenCL support when available
- **Dual Interface**: Both CLI and GUI entry points

## Pipeline Stages

1. **Format Detection**: Automatic analysis of video properties
2. **Deinterlacing** (mandatory first step): QTGMC Fast preset
3. **Temporal Denoise**: Tunable strength, temporal-only
4. **Sharpening**: Low-radius, low-strength, halo-free
5. **Deflicker**: Luminance stabilization
6. **Color Normalization**: White balance, gamma, contrast
7. **Artifact Cleanup**: Optional compression artifact removal
8. **Export**: H.265 or AV1 with proper metadata

## Requirements

- Python 3.8+
- VapourSynth
- FFmpeg
- CUDA/OpenCL (optional, for GPU acceleration)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### CLI Mode

```bash
# Process a single file
python -m videoenhance input.avi --output output.mp4

# Process all files in a directory
python -m videoenhance --watch /path/to/videos --output-dir /path/to/output
```

### GUI Mode

```bash
python -m videoenhance.gui
```

## Configuration

The pipeline can be configured via command-line arguments or configuration file. All processing parameters are tunable.

## Architecture

- **Modular Design**: Each processing stage is independent and swappable
- **Error Handling**: Automatic detection and handling of corrupted files
- **Progress Logging**: Detailed logs and metrics for each processing stage
- **No Upscaling**: Preserves native SD resolution
- **No AI Hallucination**: Uses traditional, predictable enhancement methods

## License

See LICENSE file for details.
