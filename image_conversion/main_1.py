"""Metadata stripper — renames files by capture date and removes identification metadata.

Copies files to the destination folder with standardised date-based filenames,
then strips all identification metadata using ExifTool.

File formats are preserved exactly (HEIC stays HEIC, MP4 stays MP4).
Original files in the source folder are never modified.
"""

import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pillow_heif
from PIL import Image

from config import DESTINATION_FOLDER, IMAGE_EXTENSIONS, SOURCE_FOLDER, VIDEO_EXTENSIONS
from exif_utils import get_image_datetime, get_video_datetime

# Register HEIF opener for pillow
pillow_heif.register_heif_opener()

# Identification metadata fields to strip from every output file.
# ExifTool clears a tag across all groups (EXIF, XMP, IPTC, QuickTime, etc.)
# when the bare tag name is used with no value.
IDENTIFICATION_FIELDS = [
    # --- Location ---
    "GPSLatitude",
    "GPSLongitude",
    "GPSAltitude",
    "GPSImgDirection",
    "GPSSpeed",
    "GPSTrack",
    "GPSDateStamp",
    "GPSTimeStamp",
    "GPSDestLatitude",
    "GPSDestLongitude",
    "LocationCreated",
    "City",
    "Province-State",
    "Country",
    "Sub-location",
    # --- Device identity ---
    "Make",
    "Model",
    "SerialNumber",
    "LensSerialNumber",
    "LensMake",
    "LensModel",
    "OwnerName",
    "CameraOwnerName",
    # --- Timestamps ---
    "DateTimeOriginal",
    "CreateDate",
    "ModifyDate",
    "MediaCreateDate",
    "MediaModifyDate",
    "TrackCreateDate",
    "TrackModifyDate",
    "CreationTime",
    # --- Person / identity ---
    "Artist",
    "Creator",
    "Copyright",
    "PersonInImage",
    "By-line",
    "Contact",
    # --- Software trail ---
    "Software",
    "ProcessingSoftware",
    "CreatorTool",
    # --- Document lineage ---
    "DocumentID",
    "OriginalDocumentID",
    "InstanceID",
    "DerivedFrom",
    # --- Device pairing ---
    "MediaGroupUUID",
    "ContentIdentifier",
    "ImageUniqueID",
]

# Matches filenames that are already in YYYYMMDD_HHMMSS format (any extension)
_DATETIME_ONLY_RE = re.compile(r"^\d{8}_\d{6}\.")


def check_exiftool() -> None:
    """Verify ExifTool is installed and on PATH."""
    try:
        subprocess.run(["exiftool", "-ver"], capture_output=True, check=True)
    except FileNotFoundError:
        print("Error: exiftool is not installed or not on PATH.")
        print("  macOS:  brew install exiftool")
        print("  Linux:  sudo apt install libimage-exiftool-perl")
        sys.exit(1)


def collect_files(extensions: list[str]) -> list[Path]:
    """Glob SOURCE_FOLDER for files matching the given extensions (case-insensitive)."""
    files: list[Path] = []
    for ext in extensions:
        pattern = f"*.[{ext[0].lower()}{ext[0].upper()}]" + "".join(
            f"[{c.lower()}{c.upper()}]" for c in ext[1:]
        )
        files.extend(SOURCE_FOLDER.glob(pattern))
    return sorted(files, key=lambda f: f.name)


def _make_image_filename(dt: datetime | None, ext: str, used: set[str]) -> str:
    """Return a deduplicated IMG_YYYYMMDD_HHMMSS<ext> filename."""
    if dt:
        base = f"IMG_{dt.strftime('%Y%m%d_%H%M%S')}"
    else:
        base = f"IMG_{datetime.now().strftime('%Y%m%d_%H%M%S')}_noexif"

    filename = f"{base}{ext}"
    if filename not in used:
        used.add(filename)
        return filename

    counter = 1
    while f"{base}-{counter}{ext}" in used:
        counter += 1
    filename = f"{base}-{counter}{ext}"
    used.add(filename)
    return filename


def _make_video_filename(dt: datetime | None, ext: str, used: set[str]) -> str:
    """Return a deduplicated VID_YYYYMMDD_HHMMSS<ext> filename."""
    if dt:
        base = f"VID_{dt.strftime('%Y%m%d_%H%M%S')}"
    else:
        base = f"VID_{datetime.now().strftime('%Y%m%d_%H%M%S')}_nometa"

    filename = f"{base}{ext}"
    if filename not in used:
        used.add(filename)
        return filename

    counter = 1
    while f"{base}-{counter}{ext}" in used:
        counter += 1
    filename = f"{base}-{counter}{ext}"
    used.add(filename)
    return filename


# HEIC files store metadata in both the standard EXIF block and Apple's ItemProperties
# container. Field-by-field clearing only reaches the EXIF block, so HEIC requires
# -all= to strip the ItemProperties copy as well.
_HEIC_EXTENSIONS = {".heic", ".heif"}


def strip_metadata(path: Path) -> bool:
    """Run ExifTool on *path*, clearing all identification fields. Returns True on success.

    HEIC/HEIF files use -all= to also clear Apple ItemProperties metadata that
    field-by-field stripping cannot reach.
    """
    if path.suffix.lower() in _HEIC_EXTENSIONS:
        cmd = ["exiftool", "-overwrite_original", "-all=", str(path)]
    else:
        cmd = (
            ["exiftool", "-overwrite_original"]
            + [f"-{field}=" for field in IDENTIFICATION_FIELDS]
            + [str(path)]
        )
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def process_images(files: list[Path], max_name_len: int) -> None:
    total = len(files)
    total_w = len(str(total))
    used_filenames: set[str] = set()

    for idx, source in enumerate(files, 1):
        ext = source.suffix.lower()

        # If already in YYYYMMDD_HHMMSS format, just add IMG_ prefix
        if _DATETIME_ONLY_RE.match(source.name):
            output_name = f"IMG_{source.stem}{ext}"
            used_filenames.add(output_name)
        else:
            try:
                with Image.open(source) as img:
                    dt, _ = get_image_datetime(img)
            except Exception:
                dt = None
            output_name = _make_image_filename(dt, ext, used_filenames)

        dest = DESTINATION_FOLDER / output_name
        shutil.copy2(source, dest)

        counter = f"[{idx:>{total_w}}/{total}]"
        name_col = source.name.ljust(max_name_len)

        if strip_metadata(dest):
            print(f"{counter} ✓ Stripped  {name_col} → {output_name}")
        else:
            print(f"{counter} ✗ Failed    {name_col} → {output_name}")


def process_videos(files: list[Path], max_name_len: int) -> None:
    total = len(files)
    total_w = len(str(total))
    used_filenames: set[str] = set()

    for idx, source in enumerate(files, 1):
        ext = source.suffix.lower()

        # If already in YYYYMMDD_HHMMSS format, just add VID_ prefix
        if _DATETIME_ONLY_RE.match(source.name):
            output_name = f"VID_{source.stem}{ext}"
            used_filenames.add(output_name)
        else:
            dt, _ = get_video_datetime(source)
            output_name = _make_video_filename(dt, ext, used_filenames)

        dest = DESTINATION_FOLDER / output_name
        shutil.copy2(source, dest)

        counter = f"[{idx:>{total_w}}/{total}]"
        name_col = source.name.ljust(max_name_len)

        if strip_metadata(dest):
            print(f"{counter} ✓ Stripped  {name_col} → {output_name}")
        else:
            print(f"{counter} ✗ Failed    {name_col} → {output_name}")


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

    if image_files:
        print("=== Processing Images ===")
        process_images(image_files, max_name_len)
        print()

    if video_files:
        print("=== Processing Videos ===")
        process_videos(video_files, max_name_len)
        print()

    print("Done.")


if __name__ == "__main__":
    main()
