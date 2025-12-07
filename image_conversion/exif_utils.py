"""Utilities for extracting EXIF metadata from images and videos."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS


def get_video_datetime(video_path: Path) -> tuple[datetime | None, str]:
    """Extract the datetime when the video was recorded from metadata.

    Args:
        video_path: Path to the video file

    Returns:
        tuple: (datetime object or None, formatted string for display)
    """
    try:
        command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        metadata = json.loads(result.stdout.decode())

        # Try to get creation time from format tags
        if "format" in metadata and "tags" in metadata["format"]:
            tags = metadata["format"]["tags"]
            # Common metadata fields for creation time
            for key in ["creation_time", "com.apple.quicktime.creationdate", "date"]:
                if key in tags:
                    try:
                        # Parse ISO 8601 format (most common)
                        dt_str = tags[key]
                        # Handle different datetime formats
                        for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"]:
                            try:
                                dt = datetime.strptime(dt_str.split(".")[0].replace("Z", ""), fmt.replace(".%f", "").replace("Z", ""))
                                formatted = dt.strftime("%B %d, %Y at %I:%M:%S %p")
                                return dt, formatted
                            except ValueError:
                                continue
                    except Exception:
                        continue
    except Exception:
        pass
    return None, "Unknown"


def get_image_datetime(img: Image.Image) -> tuple[datetime | None, str]:
    """Extract the datetime when the image was taken from EXIF data.

    Args:
        img: PIL Image object

    Returns:
        tuple: (datetime object or None, formatted string for display)
    """
    try:
        exif_data = img.getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name in ("DateTime", "DateTimeOriginal", "DateTimeDigitized"):
                    # Parse the datetime string (format: "YYYY:MM:DD HH:MM:SS")
                    dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                    formatted = dt.strftime("%B %d, %Y at %I:%M:%S %p")
                    return dt, formatted
    except Exception:
        pass
    return None, "Unknown"
