"""Configuration settings for image conversion."""

from pathlib import Path

# Source and destination folders
SOURCE_FOLDER = Path("files/to_convert")
DESTINATION_FOLDER = Path("files/converted")

# Supported image formats
IMAGE_EXTENSIONS = ["heic", "jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"]

# Supported video formats
VIDEO_EXTENSIONS = ["mov", "avi", "mkv", "flv", "wmv"]

# JPEG quality settings
JPEG_QUALITY = 95
JPEG_OPTIMIZE = True

# Video conversion settings
VIDEO_CODEC = "libx264"  # H.264 codec for MP4
VIDEO_QUALITY = "18"  # CRF value (18 = visually lossless, lower = better quality)
VIDEO_PRESET = "slow"  # Encoding speed preset (slower = better compression)
AUDIO_CODEC = "aac"  # AAC audio codec
AUDIO_BITRATE = "320k"  # High quality audio bitrate (320k = near CD quality)

# Filename pattern for valid image names
# Format: IMG_YYYYMMDD_HHMMSS.jpg (with optional -1, -2 suffix)
FILENAME_PATTERN = r"^IMG_\d{8}_\d{6}(-\d+)?\.jpg$"
