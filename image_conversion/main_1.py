"""Metadata stripper — renames files by capture date and removes identification metadata.

Copies files to the destination folder with standardised date-based filenames,
then strips all identification metadata using ExifTool.

File formats are preserved exactly (HEIC stays HEIC, MP4 stays MP4).
Original files in the source folder are never modified.
"""

import re
import shutil
import sys
from pathlib import Path

import pillow_heif
from PIL import Image

from config import DESTINATION_FOLDER, IMAGE_EXTENSIONS, SOURCE_FOLDER, VIDEO_EXTENSIONS
from exif_utils import get_image_datetime, get_video_datetime
from filename_utils import FilenameManager, collect_files
from metadata_utils import check_exiftool, strip_metadata

# Register HEIF opener for pillow
pillow_heif.register_heif_opener()

# Matches filenames that are already in YYYYMMDD_HHMMSS format. This mode keeps the
# source extension whatever it is, so it cannot use FilenameManager's own
# datetime-only check, which is limited to the formats the converters emit.
_DATETIME_ONLY_RE = re.compile(r"^\d{8}_\d{6}\.")


def _copy_and_strip(source: Path, output_name: str, counter: str, name_col: str) -> None:
    """Copy *source* to the destination under *output_name*, then strip its metadata."""
    dest = DESTINATION_FOLDER / output_name
    try:
        shutil.copy2(source, dest)
    except OSError as e:
        print(f"{counter} ✗ Failed    {name_col} → {output_name}: {e}")
        return

    if strip_metadata(dest):
        print(f"{counter} ✓ Stripped  {name_col} → {output_name}")
    else:
        print(f"{counter} ✗ Failed    {name_col} → {output_name}")


def process_images(files: list[Path], fm: FilenameManager, max_name_len: int) -> None:
    total = len(files)
    total_w = len(str(total))

    for idx, source in enumerate(files, 1):
        ext = source.suffix.lower()

        # If already in YYYYMMDD_HHMMSS format, just add IMG_ prefix
        if _DATETIME_ONLY_RE.match(source.name):
            output_name = f"IMG_{source.stem}{ext}"
            fm.used_filenames.add(output_name)
        else:
            try:
                with Image.open(source) as img:
                    dt, _ = get_image_datetime(img)
            except Exception:
                dt = None
            output_name = fm.generate_filename(dt, source.name, ext.lstrip("."))

        counter = f"[{idx:>{total_w}}/{total}]"
        _copy_and_strip(source, output_name, counter, source.name.ljust(max_name_len))


def process_videos(files: list[Path], fm: FilenameManager, max_name_len: int) -> None:
    total = len(files)
    total_w = len(str(total))

    for idx, source in enumerate(files, 1):
        ext = source.suffix.lower()

        # If already in YYYYMMDD_HHMMSS format, just add VID_ prefix
        if _DATETIME_ONLY_RE.match(source.name):
            output_name = f"VID_{source.stem}{ext}"
            fm.used_filenames.add(output_name)
        else:
            dt, _ = get_video_datetime(source)
            output_name = fm.generate_video_filename(dt, source.name, ext.lstrip("."))

        counter = f"[{idx:>{total_w}}/{total}]"
        _copy_and_strip(source, output_name, counter, source.name.ljust(max_name_len))


def main() -> None:
    check_exiftool()

    if not SOURCE_FOLDER.exists():
        print(f"Error: Source folder '{SOURCE_FOLDER}' does not exist")
        sys.exit(1)

    DESTINATION_FOLDER.mkdir(parents=True, exist_ok=True)

    image_files = collect_files(IMAGE_EXTENSIONS)
    video_files = collect_files(VIDEO_EXTENSIONS)

    if not image_files and not video_files:
        print(f"No image or video files found in '{SOURCE_FOLDER}'")
        return

    print(f"Found {len(image_files)} image(s) and {len(video_files)} video(s)\n")

    max_name_len = max((len(f.name) for f in image_files + video_files), default=0)
    filename_manager = FilenameManager()

    if image_files:
        print("=== Processing Images ===")
        process_images(image_files, filename_manager, max_name_len)
        print()

    if video_files:
        print("=== Processing Videos ===")
        process_videos(video_files, filename_manager, max_name_len)
        print()

    print("Done.")


if __name__ == "__main__":
    main()
