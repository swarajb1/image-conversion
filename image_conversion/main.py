"""Main entry point for the image and video conversion application."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import pillow_heif
from PIL import Image

from config import DESTINATION_FOLDER, IMAGE_EXTENSIONS, SOURCE_FOLDER, VIDEO_EXTENSIONS
from exif_utils import get_image_datetime, get_video_datetime
from filename_utils import FilenameManager
from metadata_utils import strip_metadata
from pyvips_converter import PyVipsImageConverter

# from image_converter import ImageConverter
from video_converter import VideoConverter


# Register HEIF opener for pillow
pillow_heif.register_heif_opener()

# Create destination folder if it doesn't exist
DESTINATION_FOLDER.mkdir(parents=True, exist_ok=True)


def check_exiftool() -> None:
    """Verify ExifTool is installed and on PATH."""
    try:
        subprocess.run(["exiftool", "-ver"], capture_output=True, check=True)
    except FileNotFoundError:
        print("Error: exiftool is not installed or not on PATH.")
        print("  macOS:  brew install exiftool")
        print("  Linux:  sudo apt install libimage-exiftool-perl")
        sys.exit(1)


def _handle_existing_jpg(source: Path, current: int, total: int, fm: FilenameManager, max_name_len: int) -> None:
    """Rename a source JPG by capture date and strip its identification metadata."""
    try:
        with Image.open(source) as img:
            dt, _ = get_image_datetime(img)
    except Exception:
        dt = None

    output_name = fm.determine_output_filename(source, dt)
    dest = DESTINATION_FOLDER / output_name
    shutil.copy2(source, dest)

    total_w = len(str(total))
    counter = f"[{current:>{total_w}}/{total}]"
    src_col = source.name.ljust(max_name_len)

    if strip_metadata(dest):
        print(f"{counter} ✓ Stripped  {src_col} → {output_name}")
    else:
        print(f"{counter} ✗ Failed    {src_col} → {output_name}")


def _handle_existing_mp4(source: Path, current: int, total: int, fm: FilenameManager, max_name_len: int) -> None:
    """Rename a source MP4 by capture date and strip its identification metadata."""
    dt, _ = get_video_datetime(source)
    output_name = fm.determine_video_output_filename(source, dt)
    dest = DESTINATION_FOLDER / output_name
    shutil.copy2(source, dest)

    total_w = len(str(total))
    counter = f"[{current:>{total_w}}/{total}]"
    src_col = source.name.ljust(max_name_len)

    if strip_metadata(dest):
        print(f"{counter} ✓ Stripped  {src_col} → {output_name}")
    else:
        print(f"{counter} ✗ Failed    {src_col} → {output_name}")


def parse_arguments() -> argparse.Namespace:
    """Parse and validate command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments with validated values.

    Raises:
        SystemExit: If arguments are invalid (argparse handles this automatically).
    """
    parser = argparse.ArgumentParser(
        prog="image-conversion",
        description="Convert image and video files to JPEG and MP4 formats with optional Samsung image renaming.",
        epilog="Example usage:\n  python main.py                      # Convert all files\n  python main.py --samsung-rename     # Rename Samsung images only\n  python main.py --help               # Show this help message",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--samsung-rename",
        action="store_true",
        help="Rename Samsung images only without performing conversion (useful for organizing Samsung JPEG files)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
        help="Show program version",
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

    samsung_rename_only = args.samsung_rename
    if samsung_rename_only:
        print("Mode: Samsung images will be renamed only (no conversion)\n")

    if not SOURCE_FOLDER.exists():
        print(f"Error: Source folder '{SOURCE_FOLDER}' does not exist")
        return

    # Collect all common image formats
    image_files = []
    for ext in IMAGE_EXTENSIONS:
        # Case-insensitive pattern matching
        image_files.extend(
            SOURCE_FOLDER.glob(
                f"*.[{ext[0].lower()}{ext[0].upper()}]" + "".join(f"[{c.lower()}{c.upper()}]" for c in ext[1:])
            )
        )

    # Collect all video formats
    video_files = []
    for ext in VIDEO_EXTENSIONS:
        # Case-insensitive pattern matching
        video_files.extend(
            SOURCE_FOLDER.glob(
                f"*.[{ext[0].lower()}{ext[0].upper()}]" + "".join(f"[{c.lower()}{c.upper()}]" for c in ext[1:])
            )
        )

    if not image_files and not video_files:
        print(f"No image or video files found in '{SOURCE_FOLDER}'")
        return

    # Sort files by name
    image_files.sort(key=lambda x: x.name)
    video_files.sort(key=lambda x: x.name)

    print(f"Found {len(image_files)} image file(s) and {len(video_files)} video file(s) to convert\n")

    filename_manager = FilenameManager()
    max_name_len = max((len(f.name) for f in image_files + video_files), default=0)

    # Process images
    if image_files:
        print("=== Processing Images ===")
        image_converter = PyVipsImageConverter(
            filename_manager, samsung_rename_only=samsung_rename_only, max_name_len=max_name_len
        )
        for idx, source_file in enumerate(image_files, 1):
            if source_file.suffix.lower() in (".jpg", ".jpeg"):
                _handle_existing_jpg(source_file, idx, len(image_files), filename_manager, max_name_len)
            else:
                image_converter.convert_to_jpeg(source_file, current=idx, total=len(image_files))
        print()

    # Process videos
    if video_files:
        print("=== Processing Videos ===")
        video_converter = VideoConverter(filename_manager, max_name_len=max_name_len)
        for idx, source_file in enumerate(video_files, 1):
            if source_file.suffix.lower() == ".mp4":
                _handle_existing_mp4(source_file, idx, len(video_files), filename_manager, max_name_len)
            else:
                video_converter.convert_to_mp4(source_file, current=idx, total=len(video_files))
        print()

    print("Conversion complete!")


if __name__ == "__main__":
    main()
