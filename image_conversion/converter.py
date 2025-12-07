"""Image and video conversion and processing logic."""

import re
import shutil
import subprocess
from pathlib import Path
from tqdm import tqdm
from PIL import Image, ImageOps

from config import (
    DESTINATION_FOLDER,
    JPEG_QUALITY,
    JPEG_OPTIMIZE,
    VIDEO_CODEC,
    VIDEO_QUALITY,
    VIDEO_PRESET,
    AUDIO_CODEC,
    AUDIO_BITRATE,
)
from exif_utils import get_image_datetime
from filename_utils import FilenameManager


class ImageConverter:
    """Handles image conversion to JPEG with proper orientation and naming."""

    def __init__(self, filename_manager: FilenameManager):
        """Initialize the image converter.

        Args:
            filename_manager: FilenameManager instance for handling filenames
        """
        self.filename_manager = filename_manager

    def convert_to_jpeg(self, source_path: Path, current: int = 0, total: int = 0) -> None:
        """Convert any image format to JPEG with datetime-based filename.

        Args:
            source_path: Path to the source image file
            current: Current file number (for progress display)
            total: Total number of files (for progress display)
        """
        try:
            # Process files by determining filename based on datetime format
            destination_path = DESTINATION_FOLDER / source_path.name

            with Image.open(source_path) as original_img:
                # Preserve EXIF orientation data for correct display
                img = ImageOps.exif_transpose(original_img)
                if img is None:
                    img = original_img

                # Get datetime and display string
                dt, datetime_display = get_image_datetime(img)

                # Check if source filename already follows the datetime format
                # If it does, keep the same name but strip metadata
                # Otherwise, generate a new filename based on datetime or convert datetime-only format
                source_stem = source_path.stem
                if self.filename_manager.is_valid_format(source_path.name):
                    # Source already has correct format - keep the name, strip metadata
                    new_filename = source_path.name
                else:
                    # Generate new filename based on datetime or convert datetime-only format
                    new_filename = self.filename_manager.determine_output_filename(source_path, dt)
                destination_path = DESTINATION_FOLDER / new_filename

                # Convert to RGB if necessary (images can have different color modes)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                # Save without any metadata (only the image data)
                img.save(destination_path, format="JPEG", quality=JPEG_QUALITY, optimize=JPEG_OPTIMIZE)

            # Print result
            counter_str = f"[{current}/{total}] " if total > 0 else ""
            if source_path.name != new_filename:
                print(f"{counter_str}✓ Converted {source_path.name} → {new_filename}")
            else:
                print(f"{counter_str}✓ Processed {source_path.name} (already in correct format)")
        except Exception as e:
            counter_str = f"[{current}/{total}] " if total > 0 else ""
            print(f"{counter_str}✗ Failed to convert {source_path.name}: {e}")


class VideoConverter:
    """Handles video conversion to MP4 format."""

    def __init__(self, filename_manager: FilenameManager):
        """Initialize the video converter.

        Args:
            filename_manager: FilenameManager instance for handling filenames
        """
        self.filename_manager = filename_manager
        self._check_ffmpeg()

    def _check_ffmpeg(self) -> None:
        """Check if ffmpeg is available in the system."""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Warning: ffmpeg not found. Please install ffmpeg to convert videos.")
            print("Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)")

    def _get_video_duration(self, source_path: Path) -> float:
        """Get the duration of a video file in seconds.

        Args:
            source_path: Path to the video file

        Returns:
            Duration in seconds, or 0 if unable to determine
        """
        try:
            command = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(source_path),
            ]
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            duration = float(result.stdout.decode().strip())
            return duration
        except (subprocess.CalledProcessError, ValueError):
            return 0

    def convert_to_mp4(self, source_path: Path, current: int = 0, total: int = 0) -> None:
        """Convert any video format to MP4 with progress bar.

        Args:
            source_path: Path to the source video file
            current: Current file number (for progress display)
            total: Total number of files (for progress display)
        """
        try:
            # Get video metadata
            from exif_utils import get_video_datetime

            dt, datetime_display = get_video_datetime(source_path)

            # Check if source filename already follows the datetime format
            # If it does, keep the same name but strip metadata
            # Otherwise, generate a new filename based on datetime or convert datetime-only format
            if self.filename_manager.is_valid_video_format(source_path.name):
                # Source already has correct format - keep the name, strip metadata
                output_filename = source_path.name
            else:
                # Generate new filename based on datetime or convert datetime-only format
                output_filename = self.filename_manager.determine_video_output_filename(source_path, dt)
            destination_path = DESTINATION_FOLDER / output_filename

            # Get video duration for progress tracking
            duration = self._get_video_duration(source_path)

            # Run ffmpeg conversion
            command = [
                "ffmpeg",
                "-i",
                str(source_path),
                "-map_metadata",
                "-1",  # Strip all metadata
                "-c:v",
                VIDEO_CODEC,
                "-crf",
                VIDEO_QUALITY,
                "-preset",
                VIDEO_PRESET,
                "-c:a",
                AUDIO_CODEC,
                "-b:a",
                AUDIO_BITRATE,
                "-movflags",
                "+faststart",  # Enable streaming
                "-progress",
                "pipe:1",  # Output progress to stdout
                "-y",  # Overwrite output file if exists
                str(destination_path),
            ]

            # Initialize progress bar
            counter_str = f"[{current}/{total}] " if total > 0 else ""
            pbar = tqdm(
                total=100,
                desc=f"{counter_str}Converting {source_path.name}",
                unit="%",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}% [{elapsed}<{remaining}]",
            )

            # Start ffmpeg process
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            # Parse ffmpeg progress output
            current_time = 0
            for line in process.stdout:
                if line.startswith("out_time_ms="):
                    try:
                        # Extract current time in microseconds
                        time_str = line.split("=")[1].strip()
                        # Skip if value is N/A or not numeric
                        if time_str == "N/A" or not time_str.lstrip("-").isdigit():
                            continue
                        time_ms = int(time_str)
                        current_time = time_ms / 1_000_000  # Convert to seconds

                        if duration > 0:
                            progress = min(100, (current_time / duration) * 100)
                            pbar.n = int(progress)
                            pbar.refresh()
                    except (ValueError, IndexError):
                        # Skip lines with invalid format
                        continue

            # Wait for process to complete
            process.wait()
            pbar.n = 100
            pbar.refresh()
            pbar.close()

            counter_str = f"[{current}/{total}] " if total > 0 else ""
            if process.returncode == 0:
                print(f"{counter_str}✓ Converted {source_path.name} → {output_filename}")
            else:
                # Read any remaining stderr
                if process.stderr:
                    stderr = process.stderr.read()
                    print(f"{counter_str}✗ Failed to convert {source_path.name}: {stderr}")
                else:
                    print(f"{counter_str}✗ Failed to convert {source_path.name}")

        except subprocess.CalledProcessError as e:
            counter_str = f"[{current}/{total}] " if total > 0 else ""
            print(f"{counter_str}✗ Failed to convert {source_path.name}: {e.stderr}")
        except Exception as e:
            counter_str = f"[{current}/{total}] " if total > 0 else ""
            print(f"{counter_str}✗ Failed to convert {source_path.name}: {e}")
