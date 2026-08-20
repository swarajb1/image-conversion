# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
poetry install

# Run conversion (standard mode)
poetry run python -m image_conversion.main

# Lint / format check
poetry run pre-commit run --all-files
```

There is no automated test suite. Manual testing is done via `image_conversion/test.ipynb`.

> Always run Python using `poetry run python` — never call the interpreter directly.

## Architecture

The project is a batch converter for images and videos. Files are read from `files/to_convert/` and written to `files/converted/`.

**Processing pipeline:**
1. `main.py` — discovers files, parses CLI args, orchestrates batch conversion
2. `config.py` — single source of truth for input/output paths, supported formats, JPEG quality, timezone (IST, UTC+5:30), and filename patterns
3. `exif_utils.py` — extracts creation datetime from EXIF (images) or container metadata (videos)
4. `filename_utils.py` — `FilenameManager` class: generates standardized filenames (`IMG_YYYYMMDD_HHMMSS.jpg`, `VID_YYYYMMDD_HHMMSS.mp4`), handles deduplication with numeric suffixes, and `_noexif`/`_nometa` fallbacks
5. Converters:
   - `pyvips_converter.py` — preferred high-performance path using `pyvips`; passes HEIF and PNG through untouched and renders DNG to 10-bit HEIF
   - `image_converter.py` — PIL/Pillow fallback; handles EXIF orientation correction and ICC color profile preservation
   - `video_converter.py` — FFmpeg-based; extracts duration for progress tracking, strips metadata, enables fast-start for web streaming

## Key Design Notes

- **Dual image converter strategy**: `pyvips` is the preferred converter for performance; PIL is the fallback. Both produce progressive JPEG with 4:4:4 chroma subsampling.
- **No-re-encode fast paths**: files already in an acceptable container (JPEG, HEIF, PNG, MP4) are copied or remuxed rather than re-encoded; because no encoder runs, ExifTool strips the metadata instead of `strip=True` (HEIF and PNG need `-all=`).
- **Timezone handling**: all timestamps are converted from UTC to IST (UTC+5:30) before generating filenames.
- **System dependencies**: FFmpeg and libvips must be installed separately; they are not managed by Poetry.
- **Line length**: 119 characters (Black enforced via pre-commit).
