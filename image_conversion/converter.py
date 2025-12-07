"""Image and video conversion and processing logic."""

import re
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

    def convert_to_jpeg(self, source_path: Path) -> None:
        """Convert any image format to JPEG with datetime-based filename.

        Args:
            source_path: Path to the source image file
        """
        try:
            with Image.open(source_path) as original_img:
                # Preserve EXIF orientation data
                # This ensures the image is displayed in the correct orientation
                img = ImageOps.exif_transpose(original_img)
                if img is None:
                    img = original_img

                # Get datetime and display string
                dt, datetime_display = get_image_datetime(img)

                # Determine output filename
                new_filename = self.filename_manager.determine_output_filename(source_path, dt)
                destination_path = DESTINATION_FOLDER / new_filename

                # Convert to RGB if necessary (images can have different color modes)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                # Save with EXIF data preserved (including orientation)
                img.save(
                    destination_path, format="JPEG", quality=JPEG_QUALITY, optimize=JPEG_OPTIMIZE, exif=img.getexif()
                )

            # Print result
            if source_path.name != new_filename:
                print(f"✓ Converted {source_path.name} → {new_filename}")
            else:
                print(f"✓ Processed {source_path.name} (already in correct format)")
        except Exception as e:
            print(f"✗ Failed to convert {source_path.name}: {e}")


class VideoConverter:
    """Handles video conversion to MP4 format."""

    def __init__(self):
        """Initialize the video converter."""
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

    def convert_to_mp4(self, source_path: Path) -> None:
        """Convert any video format to MP4 with progress bar.

        Args:
            source_path: Path to the source video file
        """
        try:
            # Determine output filename (keep same name but change extension to .mp4)
            output_filename = source_path.stem + ".mp4"
            destination_path = DESTINATION_FOLDER / output_filename

            # Get video duration for progress tracking
            duration = self._get_video_duration(source_path)

            # Run ffmpeg conversion
            command = [
                "ffmpeg",
                "-i",
                str(source_path),
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
            pbar = tqdm(
                total=100,
                desc=f"Converting {source_path.name}",
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
                    # Extract current time in microseconds
                    time_ms = int(line.split("=")[1].strip())
                    current_time = time_ms / 1_000_000  # Convert to seconds

                    if duration > 0:
                        progress = min(100, (current_time / duration) * 100)
                        pbar.n = int(progress)
                        pbar.refresh()

            # Wait for process to complete
            process.wait()
            pbar.n = 100
            pbar.refresh()
            pbar.close()

            if process.returncode == 0:
                print(f"✓ Converted {source_path.name} → {output_filename}")
            else:
                stderr = process.stderr.read()
                print(f"✗ Failed to convert {source_path.name}: {stderr}")

        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to convert {source_path.name}: {e.stderr}")
        except Exception as e:
            print(f"✗ Failed to convert {source_path.name}: {e}")
