# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
poetry install

# Run conversion (standard mode)
poetry run python -m image_conversion.main

# Run conversion (Samsung rename-only mode)
poetry run python -m image_conversion.main --samsung-rename

# Lint / format check
poetry run pre-commit run --all-files
```

There is no automated test suite. Manual testing is done via `image_conversion/test.ipynb`.

## Architecture

The project is a batch converter for images and videos. Files are read from `files/to_convert/` and written to `files/converted/`.

**Processing pipeline:**
1. `main.py` — discovers files, parses CLI args, orchestrates batch conversion
2. `config.py` — single source of truth for input/output paths, supported formats, JPEG quality, timezone (IST, UTC+5:30), and filename patterns
3. `exif_utils.py` — extracts creation datetime from EXIF (images) or container metadata (videos); detects Samsung devices
4. `filename_utils.py` — `FilenameManager` class: generates standardized filenames (`IMG_YYYYMMDD_HHMMSS.jpg`, `VID_YYYYMMDD_HHMMSS.mp4`), handles deduplication with numeric suffixes, and `_noexif`/`_nometa` fallbacks
5. Converters:
   - `pyvips_converter.py` — preferred high-performance path using `pyvips`; applies Samsung gamma adjustment (1.1 lift) to compensate for HDR loss
   - `image_converter.py` — PIL/Pillow fallback; handles EXIF orientation correction and ICC color profile preservation
   - `video_converter.py` — FFmpeg-based; extracts duration for progress tracking, strips metadata, enables fast-start for web streaming

## Key Design Notes

- **Dual image converter strategy**: `pyvips` is the preferred converter for performance; PIL is the fallback. Both produce progressive JPEG with 4:4:4 chroma subsampling.
- **Samsung mode** (`--samsung-rename`): skips pixel conversion entirely and only renames files detected as coming from Samsung devices.
- **Timezone handling**: all timestamps are converted from UTC to IST (UTC+5:30) before generating filenames.
- **System dependencies**: FFmpeg and libvips must be installed separately; they are not managed by Poetry.
- **Line length**: 119 characters (Black enforced via pre-commit).
