"""Configuration settings for image conversion."""

from pathlib import Path
from datetime import timezone, timedelta

# Source and destination folders
SOURCE_FOLDER = Path("files/to_convert")
DESTINATION_FOLDER = Path("files/converted")

# Timezone settings
IST = timezone(timedelta(hours=5, minutes=30))  # Indian Standard Time (UTC+5:30)

# Camera makes known to store DateTimeOriginal in UTC instead of local time (non-standard).
# For these cameras, OffsetTimeOriginal must be added to get the correct local time.
UTC_STORING_MAKES = {"canon"}

# Supported image formats
IMAGE_EXTENSIONS = ["heic", "jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp", "dng"]

# Supported video formats
VIDEO_EXTENSIONS = ["mov", "mp4", "avi", "mkv", "flv", "wmv"]

# RAW conversion mode for DNG files
# True  = extract the embedded camera-processed preview (exact HDR+ colours, lower resolution)
# False = full RAW conversion with histogram-matched colour transfer (full resolution, approximate colours)
RAW_EXTRACT_PREVIEW = True

# JPEG quality settings
JPEG_QUALITY = 93  # Quality level (1-100, recommended: 90 for good quality with compression)
JPEG_OPTIMIZE = True

# Video conversion settings
VIDEO_CODEC = "libx264"  # H.264 codec for MP4
VIDEO_QUALITY = "18"  # CRF value (18 = visually lossless, lower = better quality)
VIDEO_PRESET = "slow"  # Encoding speed preset (slower = better compression)
AUDIO_CODEC = "aac"  # AAC audio codec
AUDIO_BITRATE = "256k"  # High quality audio bitrate

# Filename pattern for valid image names
# Format: IMG_YYYYMMDD_HHMMSS.jpg or IMG_YYYYMMDD_HHMMSS_noexif.jpg (with optional -1, -2 suffix)
FILENAME_PATTERN = r"^IMG_\d{8}_\d{6}(_noexif)?(-\d+)?\.jpg$"

# Filename pattern for valid video names
# Format: VID_YYYYMMDD_HHMMSS.mp4 or VID_YYYYMMDD_HHMMSS_nometa.mp4 (with optional -1, -2 suffix)
VIDEO_FILENAME_PATTERN = r"^VID_\d{8}_\d{6}(_nometa)?(-\d+)?\.mp4$"

# Pattern for datetime-only filenames (without IMG_ or VID_ prefix)
# Format: YYYYMMDD_HHMMSS.jpg or YYYYMMDD_HHMMSS.mp4
DATETIME_ONLY_PATTERN = r"^\d{8}_\d{6}\.(jpg|mp4)$"
