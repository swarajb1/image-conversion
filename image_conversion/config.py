"""Configuration settings for image conversion."""

from pathlib import Path

# Source and destination folders
SOURCE_FOLDER = Path("files/to_convert")
DESTINATION_FOLDER = Path("files/converted")

# Supported image formats
IMAGE_EXTENSIONS = ["heic", "jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"]

# JPEG quality settings
JPEG_QUALITY = 95
JPEG_OPTIMIZE = True

# Filename pattern for valid image names
# Format: IMG_YYYYMMDD_HHMMSS.jpg (with optional -1, -2 suffix)
FILENAME_PATTERN = r"^IMG_\d{8}_\d{6}(-\d+)?\.jpg$"
