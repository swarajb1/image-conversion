# Image & Video Conversion Tool

A production-ready Python batch converter for images and videos with intelligent metadata extraction, timezone handling, and standardized filename generation based on capture timestamps.

## 📋 Features

### Image Processing
- **Format Support**: HEIC, PNG, GIF, BMP, TIFF, WebP, JPG/JPEG conversion to high-quality JPEG
- **EXIF Extraction**: Automatically reads creation timestamps from image metadata
- **Orientation Correction**: Auto-corrects image rotation based on EXIF orientation tags
- **Metadata Stripping**: Removes all metadata for privacy and reduced file size
- **Progressive JPEG**: Uses progressive encoding for better compression
- **Duplicate Handling**: Automatically appends suffixes for files with identical timestamps

### Video Processing
- **Format Support**: MOV, AVI, MKV, FLV, WMV → MP4 (H.264 with AAC audio)
- **Metadata Extraction**: Extracts creation timestamps from video metadata (supports multiple formats)
- **Real-time Progress**: Live progress bars with time estimates during conversion
- **Metadata Stripping**: Removes all metadata for privacy
- **Streaming Optimization**: Fast-start enabled for web streaming
- **High-Quality Output**: CRF 18 visually lossless encoding with 320k audio

### Timezone Support
- **IST Conversion**: Automatic conversion from UTC (Z indicator) to Indian Standard Time (UTC+5:30)
- **Flexible Format Support**: Handles ISO 8601 formats with various timezone indicators:
  - `2025-12-01T17:33:23Z` (UTC with Z)
  - `2025-11-29T13:56:48+0530` (with timezone offset)
  - `2025-12-01T17:33:23.000000Z` (with microseconds)

### Filename Generation
- **Standardized Format**:
  - Images: `IMG_YYYYMMDD_HHMMSS.jpg`
  - Videos: `VID_YYYYMMDD_HHMMSS.mp4`
- **Smart Naming**: Uses actual capture time from metadata (converted to IST if needed)
- **Fallback Handling**: Uses current timestamp with `_noexif` or `_nometa` suffix if metadata unavailable
- **Duplicate Prevention**: Appends `-1`, `-2`, etc. for files with identical timestamps

## 🛠️ Prerequisites

### Required
- **Python**: 3.11 or higher
- **Poetry**: For dependency management
- **FFmpeg**: Required for video conversion (with ffprobe)

### Optional
- **macOS**: Recommended for best HEIF/HEIC support

### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH, or use:
```bash
choco install ffmpeg
```

## 📦 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/swarajb1/image-conversion.git
cd image-conversion
```

### 2. Install Dependencies Using Poetry
```bash
poetry install
```

### 3. Activate Virtual Environment
```bash
poetry shell
```

## 🚀 Usage

### Basic Usage

1. **Place files in source folder:**
   ```bash
   cp your_photos/* files/to_convert/
   ```

2. **Run the converter:**
   ```bash
   python -m image_conversion.main
   ```

3. **Find converted files:**
   ```bash
   ls files/converted/
   ```

### Directory Structure

```
image-conversion/
├── files/
│   ├── to_convert/          # Place source files here
│   └── converted/           # Output directory (auto-created)
├── image_conversion/        # Main package
│   ├── __init__.py
│   ├── config.py           # Configuration & settings
│   ├── main.py             # Entry point
│   ├── image_converter.py  # Image conversion logic
│   ├── video_converter.py  # Video conversion logic
│   ├── exif_utils.py       # Metadata extraction utilities
│   ├── filename_utils.py   # Filename generation & validation
│   └── converter.py        # Compatibility wrapper
├── tests/                  # Test files
├── pyproject.toml          # Poetry configuration
└── README.md              # This file
```

### Supported Formats

#### Images
| Format | Extension | Support |
|--------|-----------|---------|
| HEIC | .heic | ✅ Full support via pillow-heif |
| JPEG | .jpg, .jpeg | ✅ Full support |
| PNG | .png | ✅ Full support |
| GIF | .gif | ✅ Full support (converted to JPEG) |
| BMP | .bmp | ✅ Full support |
| TIFF | .tiff, .tif | ✅ Full support |
| WebP | .webp | ✅ Full support |

#### Videos
| Format | Extension | Codec | Support |
|--------|-----------|-------|---------|
| MOV | .mov | H.264 | ✅ Full support |
| MP4 | .mp4 | H.264 | ✅ Full support |
| AVI | .avi | H.264 | ✅ Full support |
| Matroska | .mkv | H.264 | ✅ Full support |
| Flash Video | .flv | H.264 | ✅ Full support |
| Windows Media | .wmv | H.264 | ✅ Full support |

## ⚙️ Configuration

Edit `image_conversion/config.py` to customize behavior:

### Image Settings
```python
JPEG_QUALITY = 90        # Quality 1-100 (recommended: 85-90)
JPEG_OPTIMIZE = True     # Enable JPEG optimization
# Progressive JPEG is always enabled for better compression
```

### Video Settings
```python
VIDEO_CODEC = "libx264"     # H.264 codec (recommended for compatibility)
VIDEO_QUALITY = "18"        # CRF 0-51 (18 = visually lossless)
VIDEO_PRESET = "slow"       # Speed: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
AUDIO_CODEC = "aac"         # AAC audio codec
AUDIO_BITRATE = "320k"      # Audio quality (320k = near CD quality)
```

### Timezone Settings
```python
IST = timezone(timedelta(hours=5, minutes=30))  # Indian Standard Time (UTC+5:30)
```

### Directory Settings
```python
SOURCE_FOLDER = Path("files/to_convert")
DESTINATION_FOLDER = Path("files/converted")
```

## 🏗️ Architecture

### Module Structure

#### `config.py`
Central configuration file for all settings, patterns, and constants.

#### `main.py`
Application entry point that:
- Scans source folder for images and videos
- Collects and sorts files
- Initializes converters
- Orchestrates batch processing

#### `image_converter.py` (ImageConverter class)
Handles image conversion:
- Opens image files using PIL
- Applies EXIF orientation correction
- Extracts creation timestamps
- Converts to RGB mode if necessary
- Saves as optimized progressive JPEG
- Generates standardized filenames

#### `video_converter.py` (VideoConverter class)
Handles video conversion:
- Validates FFmpeg availability
- Extracts video metadata and creation timestamps
- Manages FFmpeg conversion process
- Parses progress output for real-time progress bars
- Handles errors gracefully

#### `exif_utils.py`
Metadata extraction utilities:
- `get_image_datetime()`: Extracts creation time from image EXIF data
- `get_video_datetime()`: Extracts creation time from video metadata using ffprobe
- Timezone-aware parsing with UTC→IST conversion
- Supports multiple datetime formats and timezone indicators

#### `filename_utils.py` (FilenameManager class)
Filename generation and validation:
- `generate_filename()`: Creates standardized image filenames
- `generate_video_filename()`: Creates standardized video filenames
- `is_valid_format()`: Validates filename format compliance
- `determine_output_filename()`: Intelligent filename selection
- Duplicate tracking and prevention with suffix management

#### `converter.py`
Compatibility wrapper that imports both converters for backward compatibility.

## 📊 Processing Flow

### Image Processing
```
Source Image
    ↓
Open & Extract EXIF
    ↓
Correct Orientation
    ↓
Extract Creation Time (UTC→IST conversion if needed)
    ↓
Generate Standardized Filename
    ↓
Convert to RGB (if needed)
    ↓
Save as Progressive JPEG (Quality 90, Optimized, Metadata Stripped)
    ↓
Output: IMG_YYYYMMDD_HHMMSS.jpg
```

### Video Processing
```
Source Video
    ↓
Check FFmpeg Availability
    ↓
Extract Metadata & Creation Time (UTC→IST conversion if needed)
    ↓
Get Video Duration (for progress calculation)
    ↓
Generate Standardized Filename
    ↓
Run FFmpeg Conversion with Progress Tracking
    ↓
Output: VID_YYYYMMDD_HHMMSS.mp4
```

## 💡 Advanced Usage

### Custom Quality Settings
Modify `JPEG_QUALITY` in `config.py`:
- **95+**: Maximum quality, larger files (5-15 MB for typical photos)
- **85-90**: Excellent quality, balanced (2-5 MB for typical photos) - **recommended**
- **75-85**: Good quality, smaller files (1-3 MB)
- **Below 75**: Noticeable quality loss, very small files

### Video Encoding Presets
Change `VIDEO_PRESET` for speed/quality tradeoff:
- **fast/ultrafast**: Quick encoding, larger files
- **medium**: Balanced (default in most tools)
- **slow/veryslow**: Better compression, takes longer

### Selective File Processing
Skip files with double underscores (`__`) in their names - useful for preserving special files.

## 🔍 Metadata Handling

### Image EXIF Extraction
Checks in order of preference:
1. `DateTimeOriginal` (photo capture time)
2. `DateTimeDigitized` (digitization time)
3. `DateTime` (file modification time)

### Video Metadata Extraction
Checks in order of preference:
1. `com.apple.quicktime.creationdate` (macOS/QuickTime files)
2. `creation_time` (standard ISO format)
3. `date` (fallback field)

Supports timezone formats:
- UTC with Z indicator: `2025-12-01T17:33:23Z`
- Timezone offset: `2025-11-29T13:56:48+0530`
- ISO 8601 with microseconds: `2025-12-01T17:33:23.000000Z`

## 🐛 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "FFmpeg not found" | FFmpeg not installed | Install FFmpeg (see Prerequisites) |
| Large file sizes | Quality too high | Reduce `JPEG_QUALITY` to 85-90 |
| "No EXIF data found" | Missing metadata | File will use current timestamp with `_noexif` suffix |
| Rotated images | EXIF orientation ignored | Check source file EXIF data |
| Video conversion fails | Unsupported codec | Verify source video integrity and format |
| Slow video conversion | Preset too slow | Change `VIDEO_PRESET` to "fast" or "medium" |
| "No files found" | Wrong source folder | Check `SOURCE_FOLDER` path in config.py |

## 📈 Performance

### Typical Benchmarks (on M-series Mac)

**Images:**
- HEIC to JPEG: ~200-500ms per image
- PNG to JPEG: ~100-300ms per image
- Batch of 50 photos: ~2-3 minutes

**Videos:**
- MOV to MP4 (5 mins): ~30-60 seconds (depends on preset)
- Batch of 3 videos (1 hour total): ~15-30 minutes

## 🔐 Privacy & Security

- ✅ **Metadata Stripping**: All EXIF/metadata removed from output files
- ✅ **No External Uploads**: All processing is local
- ✅ **No Logging**: Source filenames logged only to stdout during processing
- ✅ **Python-only**: No compiled binaries or hidden processes

## 📄 File Format Details

### Output JPEG Format
- **Codec**: JPEG with progressive encoding
- **Quality**: 90 (customizable)
- **Optimization**: Enabled for reduced file size
- **Color Mode**: RGB
- **Metadata**: None (stripped for privacy)

### Output MP4 Format
- **Video Codec**: H.264 (libx264)
- **Quality**: CRF 18 (visually lossless)
- **Preset**: slow (best compression)
- **Audio Codec**: AAC
- **Audio Bitrate**: 320k (near CD quality)
- **Streaming**: Fast-start enabled
- **Metadata**: None (stripped for privacy)

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- [ ] Batch size optimization
- [ ] CUDA/GPU acceleration
- [ ] WebP output support
- [ ] Batch rename without conversion
- [ ] GUI interface
- [ ] Configuration wizard

## 📄 License

GNU Affero General Public License v3.0 - See [LICENSE](LICENSE) file for details.

## 👤 Author

**Swaraj Bisane**
- Email: bisane.swaraj@gmail.com
- GitHub: [@swarajb1](https://github.com/swarajb1)

## 🔗 Resources

- [Pillow Documentation](https://python-pillow.org/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [EXIF Standards](https://en.wikipedia.org/wiki/Exif)
- [ISO 8601 DateTime Format](https://en.wikipedia.org/wiki/ISO_8601)

## ⚡ Quick Reference

```bash
# Install
poetry install && poetry shell

# Run
python -m image_conversion.main

# Check config
cat image_conversion/config.py

# Find converted files
ls -lh files/converted/

# Check specific image
file files/converted/IMG_*.jpg

# Get video info
ffprobe files/converted/VID_*.mp4
```

---

**Last Updated**: December 2025 | **Version**: 0.1.0
