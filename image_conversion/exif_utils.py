"""Utilities for extracting EXIF metadata from images."""

from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS


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
