"""
Command-line interface for VideoEnhance.
"""

import click
import logging
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.logging import RichHandler
import sys

from .core.pipeline import Pipeline, PipelineConfig
from .core.queue import ProcessingQueue
from .core.detector import VideoDetector

console = Console()


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """VideoEnhance - Automated video enhancement pipeline."""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--codec", type=click.Choice(["hevc", "av1"]), default="hevc", help="Output codec")
@click.option("--crf", type=int, default=20, help="CRF value for encoding (lower = better quality)")
@click.option("--preset", default="medium", help="Encoding preset")
@click.option("--denoise", type=float, default=1.0, help="Denoise strength (0.0-3.0)")
@click.option("--sharpen", type=float, default=0.3, help="Sharpen strength (0.0-1.0)")
@click.option("--deflicker", type=float, default=0.5, help="Deflicker strength (0.0-1.0)")
@click.option("--no-artifacts", is_flag=True, help="Disable artifact cleanup")
@click.option("--gpu", is_flag=True, help="Enable GPU acceleration")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def process(input_file, output, codec, crf, preset, denoise, sharpen, deflicker, 
           no_artifacts, gpu, verbose):
    """Process a single video file."""
    setup_logging(verbose)

    # Determine output path
    if not output:
        input_path = Path(input_file)
        output = str(input_path.parent / f"{input_path.stem}_enhanced.mp4")

    console.print(f"[bold]Processing:[/bold] {input_file}")
    console.print(f"[bold]Output:[/bold] {output}")

    # Create pipeline configuration
    config = PipelineConfig(
        output_codec=codec,
        output_crf=crf,
        output_preset=preset,
        denoise_strength=denoise,
        sharpen_strength=sharpen,
        deflicker_strength=deflicker,
        cleanup_artifacts=not no_artifacts,
        use_gpu=gpu
    )

    # Create pipeline
    pipeline = Pipeline(config=config)

    # Process video with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Processing...", total=100)

        def progress_callback(message, percent):
            progress.update(task, completed=percent, description=message)

        try:
            result = pipeline.process(input_file, output, progress_callback=progress_callback)
            console.print(f"[green]✓[/green] Successfully processed video")
            console.print(f"[bold]Output:[/bold] {result['output']}")
        except Exception as e:
            console.print(f"[red]✗[/red] Error: {e}", style="bold red")
            sys.exit(1)


@cli.command()
@click.argument("input_dir", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
@click.option("--codec", type=click.Choice(["hevc", "av1"]), default="hevc", help="Output codec")
@click.option("--crf", type=int, default=20, help="CRF value for encoding")
@click.option("--workers", type=int, default=1, help="Number of concurrent workers")
@click.option("--gpu", is_flag=True, help="Enable GPU acceleration")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def batch(input_dir, output_dir, codec, crf, workers, gpu, verbose):
    """Process all videos in a directory."""
    setup_logging(verbose)

    console.print(f"[bold]Processing directory:[/bold] {input_dir}")
    console.print(f"[bold]Output directory:[/bold] {output_dir}")

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Create pipeline configuration
    config = PipelineConfig(
        output_codec=codec,
        output_crf=crf,
        use_gpu=gpu
    )

    # Create processing queue
    queue = ProcessingQueue(config=config, num_workers=workers)

    # Add all videos from directory
    job_ids = queue.add_directory(input_dir, output_dir)
    
    if not job_ids:
        console.print("[yellow]No video files found in directory[/yellow]")
        return

    console.print(f"[bold]Added {len(job_ids)} videos to queue[/bold]")

    # Start processing
    queue.start()

    # Monitor progress
    try:
        with Progress(console=console) as progress:
            tasks = {job_id: progress.add_task(f"Job {job_id}", total=100) 
                    for job_id in job_ids}

            while True:
                all_done = True
                for job_id in job_ids:
                    job = queue.get_job_status(job_id)
                    if job:
                        progress.update(tasks[job_id], completed=job.progress)
                        if job.status.value in ["pending", "processing"]:
                            all_done = False

                if all_done:
                    break

                import time
                time.sleep(1.0)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    finally:
        queue.stop()

    # Print summary
    console.print("\n[bold]Processing Summary:[/bold]")
    for job_id in job_ids:
        job = queue.get_job_status(job_id)
        if job:
            status_color = {
                "completed": "green",
                "failed": "red",
                "cancelled": "yellow"
            }.get(job.status.value, "white")
            console.print(f"  {job_id}: [{status_color}]{job.status.value}[/{status_color}]")


@cli.command()
@click.argument("video_file", type=click.Path(exists=True))
def info(video_file):
    """Display information about a video file."""
    setup_logging()

    detector = VideoDetector()
    
    try:
        properties = detector.detect(video_file)
        
        console.print(f"\n[bold]Video Information:[/bold] {video_file}\n")
        console.print(f"  Container:    {properties['container']}")
        console.print(f"  Codec:        {properties['codec']}")
        console.print(f"  Resolution:   {properties['width']}x{properties['height']}")
        console.print(f"  FPS:          {properties['fps']:.2f}")
        console.print(f"  Duration:     {properties['duration']:.2f}s")
        console.print(f"  Interlaced:   {properties['interlaced']}")
        if properties['interlaced']:
            console.print(f"  Field Order:  {properties['field_order']}")
        console.print(f"  Pixel Format: {properties['pixel_format']}")
        
        # Check if SD
        is_sd = detector.is_sd_resolution(properties['width'], properties['height'])
        console.print(f"  SD Resolution: {is_sd}")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        sys.exit(1)


@cli.command()
@click.argument("watch_dir", type=click.Path(exists=True))
@click.argument("output_dir", type=click.Path())
@click.option("--codec", type=click.Choice(["hevc", "av1"]), default="hevc", help="Output codec")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def watch(watch_dir, output_dir, codec, verbose):
    """Watch a directory and automatically process new videos."""
    setup_logging(verbose)

    console.print(f"[bold]Watching directory:[/bold] {watch_dir}")
    console.print(f"[bold]Output directory:[/bold] {output_dir}")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")

    # This is a placeholder for the watch functionality
    # Full implementation would use watchdog library
    console.print("[red]Watch mode not yet fully implemented[/red]")
    console.print("Use 'batch' command to process existing files")


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
