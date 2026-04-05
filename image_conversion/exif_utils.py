"""Utilities for extracting EXIF metadata from images and videos."""

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from PIL import Image
from config import IST, UTC_STORING_MAKES


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
            "-v",
            "quiet",
            "-print_format",
            "json",
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
            for key in ["com.apple.quicktime.creationdate", "creation_time", "date"]:
                if key in tags:
                    try:
                        # Parse ISO 8601 format (most common)
                        dt_str = tags[key]
                        is_utc = dt_str.endswith("Z")
                        # Remove 'Z' timezone indicator for parsing
                        dt_str = dt_str.replace("Z", "").strip()
                        # Handle different datetime formats
                        for fmt in [
                            "%Y-%m-%dT%H:%M:%S.%f%z",
                            "%Y-%m-%dT%H:%M:%S%z",
                            "%Y-%m-%dT%H:%M:%S.%f",
                            "%Y-%m-%dT%H:%M:%S",
                            "%Y-%m-%d %H:%M:%S",
                        ]:
                            try:
                                dt = datetime.strptime(dt_str, fmt)
                                # If the original string had 'Z', it's UTC time - convert to IST
                                if is_utc:
                                    utc_tz = timezone.utc
                                    dt_utc = dt.replace(tzinfo=utc_tz)
                                    dt = dt_utc.astimezone(IST)
                                # If datetime already has timezone info, convert to IST
                                elif dt.tzinfo is not None:
                                    dt = dt.astimezone(IST)
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
    # Priority order: (datetime_tag_id, offset_tag_id)
    # DateTimeOriginal/Digitized live in ExifIFD (sub-IFD 0x8769), not the main IFD.
    # DateTime (306) is in the main IFD and represents last-modified time — used as fallback only.
    PRIORITY_TAGS = [
        (36867, 36881),  # DateTimeOriginal + OffsetTimeOriginal
        (36868, 36882),  # DateTimeDigitized + OffsetTimeDigitized
        (306, None),     # DateTime (main IFD, last resort)
    ]

    try:
        exif = img.getexif()
        if not exif:
            return None, "Unknown"

        try:
            exif_ifd = exif.get_ifd(0x8769)
        except Exception:
            exif_ifd = {}

        # Some camera makes (e.g. Canon) store DateTimeOriginal in UTC instead of local time.
        # For those, OffsetTimeOriginal represents the local timezone offset to apply.
        make = (exif.get(271) or "").lower()

        for dt_tag, offset_tag in PRIORITY_TAGS:
            dt_str = exif_ifd.get(dt_tag) or exif.get(dt_tag)
            if not dt_str:
                continue

            try:
                dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")

                if offset_tag and make in UTC_STORING_MAKES:
                    offset_str = exif_ifd.get(offset_tag) or exif.get(offset_tag)
                    if offset_str:
                        try:
                            sign = -1 if offset_str.startswith("-") else 1
                            parts = offset_str.lstrip("+-").split(":")
                            offset_td = timedelta(
                                hours=sign * int(parts[0]),
                                minutes=sign * int(parts[1]) if len(parts) > 1 else 0,
                            )
                            dt = dt + offset_td
                        except Exception:
                            pass

                formatted = dt.strftime("%B %d, %Y at %I:%M:%S %p")
                return dt, formatted
            except ValueError:
                continue
    except Exception:
        pass

    return None, "Unknown"


def is_samsung_device(img: Image.Image) -> bool:
    """Check if image is from a Samsung device by examining EXIF make and model tags.

    Args:
        img: PIL Image object

    Returns:
        bool: True if image is from Samsung device, False otherwise
    """
    try:
        exif = img.getexif()
        if exif:
            make = exif.get(271, "")  # Make tag
            model = exif.get(272, "")  # Model tag
            if "samsung" in str(make).lower() or "samsung" in str(model).lower():
                return True
    except Exception:
        pass
    return False
