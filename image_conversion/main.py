"""Main entry point for the image conversion application."""

import pillow_heif

from config import SOURCE_FOLDER, DESTINATION_FOLDER, IMAGE_EXTENSIONS
from converter import ImageConverter
from filename_utils import FilenameManager


# Register HEIF opener for pillow
pillow_heif.register_heif_opener()

# Create destination folder if it doesn't exist
DESTINATION_FOLDER.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """Main function to process all image files in the source folder."""
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

    if not image_files:
        print(f"No image files found in '{SOURCE_FOLDER}'")
        return

    # Sort files by name
    image_files.sort(key=lambda x: x.name)

    print(f"Found {len(image_files)} image file(s) to convert\n")

    # Initialize converter with filename manager
    filename_manager = FilenameManager()
    converter = ImageConverter(filename_manager)

    # Process all images
    for source_file in image_files:
        converter.convert_to_jpeg(source_file)

    print(f"\nConversion complete!")


if __name__ == "__main__":
    main()
