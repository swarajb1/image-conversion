# Image & Video Conversion Tool

A production-ready Python batch converter for images and videos with intelligent metadata extraction, timezone handling, and standardized filename generation based on capture timestamps.

## 📋 Features

### Image Processing
- **Format Support**: GIF, BMP, TIFF, WebP → JPEG; DNG → 10-bit HEIF; JPG, HEIC and PNG renamed in-place, never re-encoded
- **EXIF Extraction**: Automatically reads creation timestamps from image metadata
- **Orientation Correction**: Auto-corrects image rotation based on EXIF orientation tags
- **ICC Profile Preservation**: Maintains color space information for accurate color reproduction
- **High-Quality Chroma**: 4:4:4 chroma subsampling (no subsampling) for maximum quality
- **Metadata Handling**: Identification metadata stripped via ExifTool (JPG) or PyVips `strip=True` (others)
- **Progressive JPEG**: Uses progressive encoding for better compression
- **Duplicate Handling**: Automatically appends suffixes for files with identical timestamps

### Video Processing
- **Format Support**: MOV, AVI, MKV, FLV, WMV → MP4 (H.264 with AAC audio); MP4 renamed in-place
- **Metadata Extraction**: Extracts creation timestamps from video metadata (supports multiple formats)
- **Real-time Progress**: Live progress bars with time estimates during conversion
- **Metadata Stripping**: All identification metadata removed — via ExifTool for MP4, FFmpeg `-map_metadata -1` for others
- **Streaming Optimization**: Fast-start enabled for web streaming
- **High-Quality Output**: CRF 18 visually lossless encoding with 256k audio

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
- **libvips**: Required for high-performance image processing (PyVips)
- **ExifTool**: Required for metadata stripping on JPG and MP4 files

### Optional
- **macOS**: Recommended for best HEIF/HEIC support

### Installing Dependencies

**macOS:**
```bash
brew install ffmpeg vips exiftool
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg libvips libimage-exiftool-perl
```

**Windows:**
Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH, or use:
```bash
choco install ffmpeg
```

For Windows libvips, download from [libvips.github.io](https://libvips.github.io/libvips/install.html) or use pre-built Windows binaries.

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
| PNG | .png | ✅ Copied as-is (lossless; alpha preserved) |
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
JPEG_QUALITY = 95        # Quality 1-100 (95 = maximum quality with minimal file size increase)
JPEG_OPTIMIZE = True     # Enable JPEG optimization
# Progressive JPEG is always enabled for better compression
# 4:4:4 Chroma subsampling is always used for highest quality
# ICC profiles are preserved for accurate color reproduction
```

### Video Settings
```python
VIDEO_CODEC = "libx264"     # H.264 codec (recommended for compatibility)
VIDEO_QUALITY = "18"        # CRF 0-51 (18 = visually lossless)
VIDEO_PRESET = "slow"       # Speed: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
AUDIO_CODEC = "aac"         # AAC audio codec
AUDIO_BITRATE = "256k"      # Audio quality (256k = near CD quality)
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
- **JPG sources**: renamed by capture date + identification metadata stripped via ExifTool (no re-encoding)
- **MP4 sources**: renamed by capture date + identification metadata stripped via ExifTool (no re-encoding)
- All other formats: converted via PyVips (images) or FFmpeg (videos)
- Orchestrates batch processing

#### `image_converter.py` (ImageConverter class)
Handles image conversion:
- Opens image files using PIL
- Applies EXIF orientation correction
- Extracts creation timestamps
- Preserves ICC color profiles from original images
- Converts to RGB mode if necessary
- Saves as optimized progressive JPEG with 4:4:4 chroma subsampling
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

#### `pyvips_converter.py` (PyVipsImageConverter class)
High-performance image conversion using pyvips:
- Uses pyvips for faster image processing
- Applies EXIF orientation correction with autorot()
- Handles alpha channel flattening for RGBA images
- Applies ICC color space transformation to sRGB
- Saves as JPEG with 4:4:4 chroma subsampling (highest quality)
- Metadata is stripped for privacy on every path (encoder `strip=True`, or ExifTool when nothing is re-encoded)

## 📊 Processing Flow

### Image Processing (`main.py`)

Routing is by `detect_kind()` — the file's magic bytes, never its extension.

```
                              Source Image
                                   │
                                   ▼
                         ┌───────────────────┐
                         │   detect_kind()   │
                         └─────────┬─────────┘
             ┌───────────────┬─────┴─────┬───────────────────┐
             │               │           │                   │
           JPEG          HEIF / PNG     RAW                other
      (not already      (.heic/.heif   (.dng)         (gif, tiff, bmp,
       IMG_<date>)         / .png)                      webp, JPEG
             │               │           │             already named)
             ▼               ▼           ▼                   ▼
    ┌────────────────┐ ┌───────────┐ ┌──────────┐  ┌────────────────┐
    │ copy bytes     │ │ copy      │ │ rawpy    │  │ pyvips decode  │
    │ ExifTool strip │ │ bytes     │ │ 16-bit   │  │ autorot, sRGB  │
    │ (named fields) │ │ ExifTool  │ │ demosaic │  │ jpegsave       │
    │                │ │ -all=     │ │ heifsave │  │ strip=True     │
    │                │ │           │ │ 10-bit   │  │                │
    └───────┬────────┘ └─────┬─────┘ └────┬─────┘  └───────┬────────┘
         Stripped         Passed      Converted         Converted
            │                │             │                │
            ▼                ▼             ▼                ▼
     IMG_<date>.jpg   IMG_<date>.heif  IMG_<date>.heif  IMG_<date>.jpg
                      IMG_<date>.png
```

Only the two left branches avoid a re-encode. Because neither runs an encoder,
neither gets the encoder's implicit `strip=True`, so ExifTool has to do it — and
HEIF and PNG need `-all=` rather than the named-field list: HEIF because
field-by-field clearing misses Apple's ItemProperties copy of GPS and device
identity, PNG because its metadata lives in free-form text chunks with no fixed
tag names to enumerate.

PNG is passed through rather than converted because it is the one lossless input
format. Re-encoding it to JPEG discards that, flattens any alpha onto white, and
usually *grows* the file, since the PNGs in a photo library are screenshots and
graphics rather than photographs.

### Video Processing (`main.py`)

```
                         Source Video
                              │
             ┌────────────────┴────────────────┐
             │                                 │
  MP4, not already                Other formats
    VID_<date>.mp4
             │                                 │
             ▼                                 ▼
  ┌─────────────────────┐          ┌─────────────────────┐
  │  1. Read date       │          │  FFmpeg stream copy │
  │  2. Copy to dest    │          │  -c copy (remux)    │
  │  3. Rename to VID_  │          │  -map_metadata -1   │
  │  4. ExifTool strip  │          │  + ExifTool strip   │
  └──────────┬──────────┘          └──────────┬──────────┘
             │                        unmuxable│codecs
             │                                 ▼
             │                     ┌─────────────────────┐
             │                     │  FFmpeg: re-encode  │
             │                     │  H.264 / AAC        │
             │                     │  -map_metadata -1   │
             │                     └──────────┬──────────┘
             └─────────────────┬──────────────┘
                               │
                               ▼
                   ┌───────────────────────────┐
                   │  VID_YYYYMMDD_HHMMSS.mp4  │
                   └───────────────────────────┘
```

## 💡 Advanced Usage

### Command-Line Options

### Custom Quality Settings
Modify `JPEG_QUALITY` in `config.py`:
- **95**: Maximum quality, larger files (recommended for archival) - **current default**
- **90**: Excellent quality, balanced (3-6 MB for typical photos)
- **85-90**: Excellent quality, balanced (2-5 MB for typical photos)
- **75-85**: Good quality, smaller files (1-3 MB)
- **Below 75**: Noticeable quality loss, very small files

### ICC Profile Handling
The converter now preserves ICC color profiles:
- Extracts ICC profiles from source images
- Applies ICC transform to sRGB color space during conversion
- Results in more accurate color reproduction in the output JPEG

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
| "exiftool not found" | ExifTool not installed | `brew install exiftool` / `apt install libimage-exiftool-perl` |
| Large file sizes | Quality too high | Reduce `JPEG_QUALITY` to 90 or below |
| Slow conversion | Using PIL (ImageConverter) | Use PyVipsImageConverter for faster processing |
| "No EXIF data found" | Missing metadata | File will use current timestamp with `_noexif` suffix |
| Rotated images | EXIF orientation ignored | Check source file EXIF data |
| Video conversion fails | Unsupported codec | Verify source video integrity and format |
| Slow video conversion | Preset too slow | Change `VIDEO_PRESET` to "fast" or "medium" |
| "No files found" | Wrong source folder | Check `SOURCE_FOLDER` path in config.py |

## 📈 Performance

### Typical Benchmarks (on M-series Mac)

**Images (using PyVipsImageConverter):**
- HEIC to JPEG: ~100-200ms per image (faster than PIL)
- Batch of 50 photos: ~1-2 minutes
- ICC profile processing overhead: negligible

**Images (using ImageConverter - PIL):**
- HEIC to JPEG: ~200-500ms per image
- Batch of 50 photos: ~2-3 minutes

**Videos:**
- MOV to MP4 (5 mins): ~30-60 seconds (depends on preset)
- Batch of 3 videos (1 hour total): ~15-30 minutes

---

## 🔏 Metadata Stripper (format-preserving)

`main_1.py` is an alternative entry point that **renames files by capture date and strips identification
metadata without converting formats**. Every file is copied to `files/converted/` with a standardised
date-based filename and its original format preserved; ExifTool then removes the identifying fields from
the copy. The original in `files/to_convert/` is never modified.

### Prerequisites

Requires **ExifTool** in addition to the standard dependencies:

```bash
# macOS
brew install exiftool

# Linux (Ubuntu/Debian)
sudo apt install libimage-exiftool-perl
```

### Processing Flow (`main_1.py`)

```
                         Source File
                              │
             ┌────────────────┴────────────────┐
             │                                 │
           Image                             Video
             │                                 │
             ▼                                 ▼
  ┌─────────────────────┐          ┌─────────────────────┐
  │  Read EXIF date     │          │  Read date via      │
  │  via PIL            │          │  ffprobe            │
  └──────────┬──────────┘          └──────────┬──────────┘
             │                                 │
             ▼                                 ▼
  ┌─────────────────────┐          ┌─────────────────────┐
  │  Copy + rename to   │          │  Copy + rename to   │
  │  IMG_ filename      │          │  VID_ filename      │
  │  (original ext)     │          │  (original ext)     │
  └──────────┬──────────┘          └──────────┬──────────┘
             └─────────────────┬──────────────┘
                               │
                    ┌──────────┴──────────┐
                    │    HEIC / HEIF ?    │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
             YES                                NO
              │                                 │
              ▼                                 ▼
  ┌─────────────────────┐          ┌─────────────────────┐
  │  ExifTool: -all=    │          │  ExifTool: strip    │
  │  (full strip incl.  │          │  ID fields          │
  │  Apple containers)  │          └──────────┬──────────┘
  └──────────┬──────────┘                     │
             └─────────────────┬──────────────┘
                               │
                               ▼
                   ┌───────────────────────────┐
                   │  Original format kept     │
                   │  No identification        │
                   │  metadata                 │
                   └───────────────────────────┘
```

### Usage

```bash
poetry run python -m image_conversion.main_1
```

### What it strips

| Category | Fields removed |
|----------|---------------|
| Location | `GPSLatitude`, `GPSLongitude`, `GPSAltitude`, `GPSImgDirection`, `GPSSpeed`, `GPSTrack`, `GPSDateStamp`, `GPSTimeStamp`, `GPSDestLatitude`, `GPSDestLongitude`, `LocationCreated`, `City`, `Province-State`, `Country`, `Sub-location` |
| Device identity | `Make`, `Model`, `SerialNumber`, `LensSerialNumber`, `LensMake`, `LensModel`, `OwnerName`, `CameraOwnerName` |
| Timestamps | `DateTimeOriginal`, `CreateDate`, `ModifyDate`, `MediaCreateDate`, `MediaModifyDate`, `TrackCreateDate`, `TrackModifyDate`, `CreationTime` |
| Person / identity | `Artist`, `Creator`, `Copyright`, `PersonInImage`, `By-line`, `Contact` |
| Software trail | `Software`, `ProcessingSoftware`, `CreatorTool` |
| Document lineage | `DocumentID`, `OriginalDocumentID`, `InstanceID`, `DerivedFrom` |
| Device pairing | `MediaGroupUUID`, `ContentIdentifier`, `ImageUniqueID` |

ExifTool clears each field across all metadata groups (EXIF, XMP, IPTC, QuickTime) in a single pass, so
Apple-specific atoms in iPhone videos and proprietary maker-note tags are covered alongside standard EXIF.

### Comparison with `main.py`

| | `main.py` | `main_1.py` |
|---|---|---|
| Output format | JPEG (images) / MP4 (videos) | Original format unchanged |
| Filename | Standardized `IMG_` / `VID_` by date | Standardized `IMG_` / `VID_` by date |
| JPG sources | Renamed + ExifTool strip (no re-encode) | Renamed + ExifTool strip (no re-encode) |
| MP4 sources | Renamed + ExifTool strip (no re-encode) | Renamed + ExifTool strip (no re-encode) |
| HEIC / other images | Converted to JPEG via PyVips | Renamed + ExifTool `-all=` strip |
| MOV / other videos | Re-encoded to MP4 via FFmpeg | Renamed + ExifTool strip |
| DNG / RAW | Converted to JPEG | Stripped in-place |

---

## 🔐 Privacy & Security

- ✅ **Metadata Stripping**: All EXIF/metadata removed from output files
- ✅ **No External Uploads**: All processing is local
- ✅ **No Logging**: Source filenames logged only to stdout during processing
- ✅ **Python-only**: No compiled binaries or hidden processes

## 📄 File Format Details

### Output JPEG Format
- **Codec**: JPEG with progressive encoding
- **Quality**: 95 (customizable, recommended 95 for max quality)
- **Chroma Subsampling**: 4:4:4 (no subsampling - highest quality)
- **Color Mode**: RGB with ICC profile transformation
- **Optimization**: Enabled for reduced file size
- **ICC Profiles**: Preserved during conversion for accurate color reproduction
- **Metadata**: Stripped (except ICC profile) for privacy

### Output MP4 Format
- **Video Codec**: H.264 (libx264)
- **Quality**: CRF 18 (visually lossless)
- **Preset**: slow (best compression)
- **Audio Codec**: AAC
- **Audio Bitrate**: 256k (near CD quality)
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

**Last Updated**: December 2025 | **Version**: 0.2.0

**Recent Changes (v0.2.0):**
- Added PyVipsImageConverter for high-performance image processing
- Implemented ICC profile preservation for accurate color reproduction
- Improved JPEG quality settings (95 default with 4:4:4 chroma subsampling)
- Enhanced color space handling with ICC transform to sRGB
