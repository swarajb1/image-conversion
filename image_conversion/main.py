"""Main entry point for the image and video conversion application."""

import pillow_heif

from config import SOURCE_FOLDER, DESTINATION_FOLDER, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from image_converter import ImageConverter
from video_converter import VideoConverter
from filename_utils import FilenameManager


# Register HEIF opener for pillow
pillow_heif.register_heif_opener()

# Create destination folder if it doesn't exist
DESTINATION_FOLDER.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """Main function to process all image and video files in the source folder."""
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

    total_files = len(image_files) + len(video_files)
    print(f"Found {len(image_files)} image file(s) and {len(video_files)} video file(s) to convert\n")

    filename_manager = FilenameManager()

    # Process images
    if image_files:
        print("=== Processing Images ===")
        image_converter = ImageConverter(filename_manager)
        for idx, source_file in enumerate(image_files, 1):
            image_converter.convert_to_jpeg(source_file, current=idx, total=len(image_files))
        print()

    # Process videos
    if video_files:
        print("=== Processing Videos ===")
        video_converter = VideoConverter(filename_manager)
        for idx, source_file in enumerate(video_files, 1):
            video_converter.convert_to_mp4(source_file, current=idx, total=len(video_files))
        print()

    print(f"Conversion complete!")


if __name__ == "__main__":
    main()
