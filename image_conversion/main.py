"""Main entry point for the image and video conversion application."""

import argparse
import shutil
import sys
import time
from pathlib import Path

import pillow_heif
from PIL import Image

from config import DESTINATION_FOLDER, IMAGE_EXTENSIONS, SOURCE_FOLDER, VIDEO_EXTENSIONS
from exif_utils import get_image_datetime, get_video_datetime
from filename_utils import FilenameManager, collect_files
from format_utils import JPEG, content_ext, detect_kind
from metadata_utils import check_exiftool, strip_metadata
from pyvips_converter import PyVipsImageConverter
from stats import RunStats

# from image_converter import ImageConverter
from video_converter import VideoConverter


# Register HEIF opener for pillow
pillow_heif.register_heif_opener()

# Create destination folder if it doesn't exist
DESTINATION_FOLDER.mkdir(parents=True, exist_ok=True)


def _image_output_name(source: Path, fm: FilenameManager) -> str:
    """Pick the output name for an image copied out as-is, by capture date.

    An already-standard IMG_<date> name is kept as it is, so a second run over this
    program's own output renames nothing and re-encodes nothing -- but only when the name
    does not lie about the content, because ExifTool will not strip a file whose extension
    contradicts its bytes.
    """
    ext = content_ext(source)
    if fm.is_valid_format(source.name) and source.suffix.lower() == f".{ext}":
        fm.used_filenames.add(source.name)
        return source.name

    try:
        with Image.open(source) as img:
            dt, _ = get_image_datetime(img)
    except Exception:
        dt = None

    return fm.determine_output_filename(source, dt, ext)


def _video_output_name(source: Path, fm: FilenameManager) -> str:
    """Pick the output name for a video copied out as-is, by capture date."""
    ext = content_ext(source)
    if fm.is_valid_video_format(source.name) and source.suffix.lower() == f".{ext}":
        fm.used_filenames.add(source.name)
        return source.name

    dt, _ = get_video_datetime(source)
    return fm.determine_video_output_filename(source, dt, ext)


def _copy_and_strip(
    source: Path, output_name: str, current: int, total: int, max_name_len: int
) -> tuple[str, str | None]:
    """Copy *source* to the destination under *output_name* and strip its metadata."""
    dest = DESTINATION_FOLDER / output_name

    total_w = len(str(total))
    counter = f"[{current:>{total_w}}/{total}]"
    src_col = source.name.ljust(max_name_len)

    # One unreadable file must not abort the batch -- the converters catch broadly for
    # the same reason, so the run reaches its summary.
    try:
        shutil.copy2(source, dest)
    except OSError as e:
        print(f"{counter} ✗ Failed    {src_col} → {output_name}: {e}")
        return "Failed", str(e)

    if strip_metadata(dest):
        print(f"{counter} ✓ Stripped  {src_col} → {output_name}")
        return "Stripped", None

    print(f"{counter} ✗ Failed    {src_col} → {output_name}")
    return "Failed", "exiftool could not strip metadata"


def parse_arguments() -> argparse.Namespace:
    """Parse and validate command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments with validated values.

    Raises:
        SystemExit: If arguments are invalid (argparse handles this automatically).
    """
    parser = argparse.ArgumentParser(
        prog="image-conversion",
        description="Convert image and video files to JPEG and MP4 formats.",
        epilog=(
            "Example usage:\n"
            "  python main.py                      # Convert all files\n"
            "  python main.py --no-convert         # Rename and strip only, keep every container\n"
            "  python main.py --help               # Show this help message"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
        help="Show program version",
    )

    parser.add_argument(
        "--no-convert",
        action="store_true",
        help="Copy every file in its original container (HEIC stays HEIC, MOV stays MOV), renaming and stripping metadata only",
    )

    args = parser.parse_args()
    return args


def main() -> None:
    """Main function to process all image and video files in the source folder."""
    # Parse and validate command-line arguments
    try:
        args = parse_arguments()
    except SystemExit as e:
        if e.code != 0:
            sys.exit(e.code)
        sys.exit(0)

    check_exiftool()

    if not SOURCE_FOLDER.exists():
        print(f"Error: Source folder '{SOURCE_FOLDER}' does not exist")
        return

    image_files = collect_files(IMAGE_EXTENSIONS)
    video_files = collect_files(VIDEO_EXTENSIONS)

    if not image_files and not video_files:
        print(f"No image or video files found in '{SOURCE_FOLDER}'")
        return

    print(f"Found {len(image_files)} image file(s) and {len(video_files)} video file(s) to convert\n")

    filename_manager = FilenameManager()
    max_name_len = max((len(f.name) for f in image_files + video_files), default=0)
    stats = RunStats()
    start = time.monotonic()

    # Process images
    if image_files:
        print("=== Processing Images ===")
        image_converter = PyVipsImageConverter(filename_manager, max_name_len=max_name_len)
        for idx, source_file in enumerate(image_files, 1):
            # Route on what the file is, not what it is named. Tools like Picasa rewrite
            # a DNG as JPEG while keeping the .dng name, which would otherwise reach rawpy.
            if args.no_convert or detect_kind(source_file) == JPEG:
                output_name = _image_output_name(source_file, filename_manager)
                action, error = _copy_and_strip(source_file, output_name, idx, len(image_files), max_name_len)
            else:
                action, error = image_converter.convert_to_jpeg(source_file, current=idx, total=len(image_files))
            stats.record(stats.images, action, source_file.name, error)
        print()

    # Process videos
    if video_files:
        print("=== Processing Videos ===")
        # --no-convert never shells out to ffmpeg, so it must not demand it either.
        video_converter = None if args.no_convert else VideoConverter(filename_manager, max_name_len=max_name_len)
        for idx, source_file in enumerate(video_files, 1):
            if video_converter is None:
                output_name = _video_output_name(source_file, filename_manager)
                action, error = _copy_and_strip(source_file, output_name, idx, len(video_files), max_name_len)
            else:
                # An MP4 source needs no special case: the converter's stream copy remuxes
                # MP4 to MP4 losslessly and wipes the metadata while doing it.
                action, error = video_converter.convert_to_mp4(source_file, current=idx, total=len(video_files))
            stats.record(stats.videos, action, source_file.name, error)
        print()

    stats.print_summary(time.monotonic() - start)


if __name__ == "__main__":
    main()
