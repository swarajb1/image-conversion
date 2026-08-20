"""Video conversion and processing logic."""

import subprocess
from pathlib import Path
from tqdm import tqdm

from config import (
    DESTINATION_FOLDER,
    VIDEO_CODEC,
    VIDEO_QUALITY,
    VIDEO_PRESET,
    AUDIO_CODEC,
    AUDIO_BITRATE,
    VIDEO_STREAM_COPY,
)
from exif_utils import get_video_datetime
from filename_utils import FilenameManager
from metadata_utils import strip_metadata


class VideoConverter:
    """Handles video conversion to MP4 format."""

    def __init__(self, filename_manager: FilenameManager, max_name_len: int = 0):
        """Initialize the video converter.

        Args:
            filename_manager: FilenameManager instance for handling filenames
            max_name_len: Max source filename length used to align terminal output columns
        """
        self.filename_manager = filename_manager
        self.max_name_len = max_name_len
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

    def _get_audio_bitrate(self, source_path: Path) -> str:
        """Get the audio bitrate of a video file.

        Args:
            source_path: Path to the video file

        Returns:
            Audio bitrate as a string (e.g., "128000"), or "0" if unable to determine
        """
        try:
            command = [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=bit_rate",
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
            bitrate = result.stdout.decode().strip()
            return bitrate if bitrate else "0"
        except (subprocess.CalledProcessError, ValueError):
            return "0"

    def _get_video_quality(self, source_path: Path) -> str:
        """Get the video quality (resolution) of a video file.

        Args:
            source_path: Path to the video file

        Returns:
            Video quality as a string (e.g., "1920x1080"), or "Unknown" if unable to determine
        """
        try:
            command = [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=p=0",
                str(source_path),
            ]
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            quality = result.stdout.decode().strip()
            return quality if quality else "Unknown"
        except (subprocess.CalledProcessError, ValueError):
            return "Unknown"

    def _try_stream_copy(self, source_path: Path, destination_path: Path) -> bool:
        """Remux the source into MP4 without re-encoding.

        Args:
            source_path: Path to the source video file
            destination_path: Path to write the remuxed MP4 to

        Returns:
            True if the remux succeeded, False if the streams cannot live in an MP4
            container (caller should fall back to a full re-encode)
        """
        command = [
            "ffmpeg",
            "-i",
            str(source_path),
            "-map_metadata",
            "-1",  # Strip all metadata
            "-c",
            "copy",  # Stream copy — no decode/encode
            "-movflags",
            "+faststart",  # Enable streaming
            "-y",  # Overwrite output file if exists
            str(destination_path),
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            # ffmpeg creates the output before it discovers the codec is unmuxable
            destination_path.unlink(missing_ok=True)
            return False
        return True

    def convert_to_mp4(self, source_path: Path, current: int = 0, total: int = 0) -> tuple[str, str | None]:
        """Convert any video format to MP4 with progress bar.

        Args:
            source_path: Path to the source video file
            current: Current file number (for progress display)
            total: Total number of files (for progress display)

        Returns:
            (action, error) where action is the label printed for this file and error is
            the failure message, or None on success
        """
        try:
            # Get video metadata
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

            # Try a lossless remux first — falls through to a re-encode if the codecs
            # cannot be muxed into MP4 (e.g. PCM audio in a .mov, MJPEG in an .avi)
            if VIDEO_STREAM_COPY and self._try_stream_copy(source_path, destination_path):
                strip_metadata(destination_path)

                pad = self.max_name_len
                total_w = len(str(total))
                counter_str = f"[{current:>{total_w}}/{total}] " if total > 0 else ""
                src = source_path.name.ljust(pad)
                print(f"{counter_str}✓ Remuxed   {src} → {output_filename}")
                return "Remuxed", None

            # Get video duration for progress tracking
            duration = self._get_video_duration(source_path)

            # Get audio bitrate from source, use default if not available
            audio_bitrate = self._get_audio_bitrate(source_path)
            if audio_bitrate == "0":
                audio_bitrate = AUDIO_BITRATE

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
                audio_bitrate,
                "-movflags",
                "+faststart",  # Enable streaming
                "-progress",
                "pipe:1",  # Output progress to stdout
                "-y",  # Overwrite output file if exists
                str(destination_path),
            ]

            # Initialize progress bar
            total_w = len(str(total))
            counter_str = f"[{current:>{total_w}}/{total}] " if total > 0 else ""
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

            pad = self.max_name_len
            if process.returncode == 0:
                src = source_path.name.ljust(pad)
                print(f"{counter_str}✓ Converted {src} → {output_filename}")
                return "Converted", None

            # Read any remaining stderr
            if process.stderr:
                stderr = process.stderr.read()
                print(f"{counter_str}✗ Failed    {source_path.name}: {stderr}")
                return "Failed", stderr

            print(f"{counter_str}✗ Failed    {source_path.name}")
            return "Failed", f"ffmpeg exited with code {process.returncode}"

        except subprocess.CalledProcessError as e:
            total_w = len(str(total))
            counter_str = f"[{current:>{total_w}}/{total}] " if total > 0 else ""
            print(f"{counter_str}✗ Failed    {source_path.name}: {e.stderr}")
            return "Failed", str(e.stderr)
        except Exception as e:
            total_w = len(str(total))
            counter_str = f"[{current:>{total_w}}/{total}] " if total > 0 else ""
            print(f"{counter_str}✗ Failed    {source_path.name}: {e}")
            return "Failed", str(e)
