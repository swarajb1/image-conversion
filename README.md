# Image & Video Conversion Tool

A Python-based batch converter for images and videos that standardizes filenames based on EXIF metadata and converts files to optimized formats (JPEG for images, MP4 for videos).

## 📋 Features

- **Batch Image Conversion**: Convert HEIC, PNG, GIF, BMP, TIFF, WebP, and other formats to high-quality JPEG
- **Batch Video Conversion**: Convert MOV, AVI, MKV, FLV, WMV, and other formats to MP4 with H.264 encoding
- **EXIF Metadata Extraction**: Automatically reads creation date/time from image and video metadata
- **Smart Filename Generation**: Creates standardized filenames in `IMG_YYYYMMDD_HHMMSS.jpg` and `VID_YYYYMMDD_HHMMSS.mp4` formats
- **Duplicate Handling**: Automatically appends suffixes (-1, -2, etc.) for files with identical timestamps
- **EXIF Orientation Correction**: Properly rotates images based on EXIF orientation data
- **Progress Tracking**: Real-time progress bars for video conversions with time estimates
- **Selective Processing**: Skips files with double underscores in their names (preserves special files)
- **High Quality Output**: 
  - Images: 95% JPEG quality with optimization
  - Videos: CRF 18 (visually lossless), 320k AAC audio, fast-start enabled for streaming

## 🛠️ Prerequisites

- **Python**: 3.11 or higher
- **Poetry**: For dependency management
- **FFmpeg**: Required for video conversion

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
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/swarajb1/image-conversion.git
   cd image-conversion
   ```

2. **Install dependencies using Poetry:**
   ```bash
   poetry install
   ```

3. **Activate the virtual environment:**
   ```bash
   poetry shell
   ```

## 🚀 Usage

### Basic Usage

1. Place your images and videos in the `files/to_convert/` directory
2. Run the converter:
   ```bash
   python -m image_conversion.main
   ```
3. Find converted files in `files/converted/`

### File Organization

```
image-conversion/
├── files/
│   ├── to_convert/      # Place source files here
│   └── converted/       # Converted files appear here
├── image_conversion/    # Source code
└── tests/              # Test files
```

### Supported Formats

**Images:**
- HEIC (Apple's High Efficiency Image Format)
- JPEG/JPG
- PNG
- GIF
- BMP
- TIFF
- WebP

**Videos:**
- MOV (QuickTime)
- MP4
- AVI
- MKV (Matroska)
- FLV (Flash Video)
- WMV (Windows Media Video)

## ⚙️ Configuration

Edit `image_conversion/config.py` to customize settings:

### Image Settings

```python
JPEG_QUALITY = 95        # Quality level (1-100, default: 95)
JPEG_OPTIMIZE = True     # Enable JPEG optimization
```

### Video Settings

```python
VIDEO_CODEC = "libx264"     # H.264 codec for MP4
VIDEO_QUALITY = "18"        # CRF value (18 = visually lossless, 0-51)
VIDEO_PRESET = "slow"       # Encoding preset (ultrafast to veryslow)
AUDIO_CODEC = "aac"         # AAC audio codec
AUDIO_BITRATE = "320k"      # Audio bitrate (320k = near CD quality)
```

### Directory Settings

```python
SOURCE_FOLDER = Path("files/to_convert")
DESTINATION_FOLDER = Path("files/converted")
```

## 📝 How It Works

### Image Processing

1. Scans the source folder for supported image formats (case-insensitive)
2. Skips files containing double underscores (`__`) in their names
3. Opens each image and extracts EXIF metadata
4. Corrects image orientation based on EXIF data
5. Extracts creation date/time from EXIF tags (`DateTime`, `DateTimeOriginal`, or `DateTimeDigitized`)
6. Generates filename: `IMG_YYYYMMDD_HHMMSS.jpg`
7. Handles duplicates by appending suffixes: `IMG_YYYYMMDD_HHMMSS-1.jpg`
8. Converts to RGB mode if necessary
9. Saves as optimized JPEG with preserved EXIF data

### Video Processing

1. Checks for FFmpeg availability
2. Scans the source folder for supported video formats
3. Skips files with double underscores in their names
4. Extracts creation time from video metadata using `ffprobe`
5. Generates filename: `VID_YYYYMMDD_HHMMSS.mp4`
6. Converts video using FFmpeg with:
   - H.264 video codec (libx264)
   - AAC audio codec at 320k bitrate
   - CRF 18 quality (visually lossless)
   - Fast-start flag for web streaming
7. Displays real-time progress bar with time estimates

## 🔧 Architecture

### Module Structure

- **`main.py`**: Entry point, orchestrates the conversion process
- **`converter.py`**: Contains `ImageConverter` and `VideoConverter` classes
- **`exif_utils.py`**: EXIF and video metadata extraction utilities
- **`filename_utils.py`**: Filename generation, validation, and duplicate handling
- **`config.py`**: Configuration settings and constants

### Key Classes

- **`FilenameManager`**: Manages filename generation with duplicate tracking
- **`ImageConverter`**: Handles image conversion and EXIF processing
- **`VideoConverter`**: Handles video conversion with FFmpeg integration

## 🎯 Use Cases

- **Photo Library Organization**: Standardize filenames across mixed photo collections
- **HEIC to JPEG Conversion**: Convert Apple HEIC photos for universal compatibility
- **Video Format Standardization**: Convert various video formats to web-friendly MP4
- **Batch Processing**: Process hundreds of files with progress tracking
- **Metadata-Based Sorting**: Organize media by actual capture date/time

## 🐛 Troubleshooting

**FFmpeg not found:**
- Ensure FFmpeg is installed and available in your system PATH
- Run `ffmpeg -version` to verify installation

**No EXIF data found:**
- Files without EXIF data will be named with current timestamp and `_noexif` suffix
- Some file formats don't preserve EXIF data

**Orientation issues:**
- The tool automatically corrects orientation using EXIF data
- If images appear rotated, the source file may have incorrect EXIF orientation tags

**Video conversion fails:**
- Check FFmpeg installation
- Ensure source video is not corrupted
- Verify sufficient disk space for conversion

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Swaraj Bisane**
- Email: bisane.swaraj@gmail.com
- GitHub: [@swarajb1](https://github.com/swarajb1)

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## 📊 Example Output

```
Found 15 image file(s) and 3 video file(s) to convert

=== Processing Images ===
[1/15] ✓ Converted photo.heic → IMG_20231215_143022.jpg
[2/15] ✓ Converted screenshot.png → IMG_20231215_143023.jpg
[3/15] ✓ Converted IMG_20231215_143023.jpg → IMG_20231215_143023-1.jpg
...

=== Processing Videos ===
[1/3] Converting video.mov |████████████████████| 100% [00:45<00:00]
[1/3] ✓ Converted video.mov → VID_20231215_143500.mp4
...

Conversion complete!
```

## 🔄 Version History

- **v0.1.0** (Initial Release)
  - Batch image conversion to JPEG
  - Batch video conversion to MP4
  - EXIF metadata extraction
  - Automatic filename generation
  - Progress tracking for videos
