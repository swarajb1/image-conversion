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
IMAGE_EXTENSIONS = ["heic", "heif", "jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp", "dng"]

# Supported video formats
VIDEO_EXTENSIONS = ["mov", "mp4", "avi", "mkv", "flv", "wmv"]

# RAW formats routed through rawpy for white-balance-aware demosaicing
RAW_EXTENSIONS = {".dng"}

# HEIC/HEIF handling
# True  = copy the source bytes unchanged to a .heif name (lossless; a .heic file is
#         already a valid HEIF container, so no decode/encode is needed). Files whose
#         ftyp major brand is not HEIF-compatible fall back to the normal JPEG path.
# False = decode and re-encode to JPEG via the normal pyvips path
HEIC_PASSTHROUGH = True

# DNG handling
# True  = full demosaic written as 10-bit HEIF (keeps the raw tonal headroom that 8-bit
#         JPEG discards); overrides RAW_EXTRACT_PREVIEW below
# False = existing JPEG behaviour, governed by RAW_EXTRACT_PREVIEW
RAW_TO_HEIF = True

# HEIF encoder settings for DNG output (only used when RAW_TO_HEIF is True)
RAW_HEIF_COMPRESSION = "av1"  # "av1" (smaller, modern) or "hevc" (wider device support)
RAW_HEIF_QUALITY = 90  # 1-100; 90 keeps gradients clean without bloating files
RAW_HEIF_BITDEPTH = 10  # 8, 10 or 12 -- 10 is the point of this whole path
RAW_HEIF_EFFORT = 4  # 0-9 CPU effort; higher is slower and slightly smaller
RAW_HEIF_AUTO_BRIGHT = False  # False = faithful exposure; True = auto-lift dark frames

# RAW conversion mode for DNG files -- ignored when RAW_TO_HEIF is True
# True  = extract the embedded camera-processed preview (exact HDR+ colours, lower resolution)
# False = full RAW conversion with histogram-matched colour transfer (full resolution, approximate colours)
RAW_EXTRACT_PREVIEW = True

# JPEG quality settings
JPEG_QUALITY = 93  # Quality level (1-100, recommended: 90 for good quality with compression)
JPEG_OPTIMIZE = True

# Video conversion mode
# True  = try a lossless stream copy (remux) first; only re-encode when the source
#         codecs cannot live in an MP4 container (fast, no quality loss)
# False = always re-encode through FFmpeg (slow, may lose quality)
VIDEO_STREAM_COPY = True

# Video conversion settings (only used when re-encoding)
VIDEO_CODEC = "libx264"  # H.264 codec for MP4
VIDEO_QUALITY = "18"  # CRF value (18 = visually lossless, lower = better quality)
VIDEO_PRESET = "slow"  # Encoding speed preset (slower = better compression)
AUDIO_CODEC = "aac"  # AAC audio codec
AUDIO_BITRATE = "256k"  # High quality audio bitrate

# Filename pattern for valid image names
# Format: IMG_YYYYMMDD_HHMMSS.<ext> or IMG_YYYYMMDD_HHMMSS_noexif.<ext> (with optional -1, -2 suffix)
FILENAME_PATTERN = r"^IMG_\d{8}_\d{6}(_noexif)?(-\d+)?\.(jpg|heif)$"

# Filename pattern for valid video names
# Format: VID_YYYYMMDD_HHMMSS.mp4 or VID_YYYYMMDD_HHMMSS_nometa.mp4 (with optional -1, -2 suffix)
VIDEO_FILENAME_PATTERN = r"^VID_\d{8}_\d{6}(_nometa)?(-\d+)?\.mp4$"

# Pattern for datetime-only filenames (without IMG_ or VID_ prefix)
# Format: YYYYMMDD_HHMMSS.jpg, YYYYMMDD_HHMMSS.heif or YYYYMMDD_HHMMSS.mp4
DATETIME_ONLY_PATTERN = r"^\d{8}_\d{6}\.(jpg|heif|mp4)$"
