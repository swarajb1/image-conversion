"""Image conversion and processing logic."""

from pathlib import Path
from PIL import Image, ImageOps

from config import DESTINATION_FOLDER, JPEG_QUALITY, JPEG_OPTIMIZE
from exif_utils import get_image_datetime
from filename_utils import FilenameManager


class ImageConverter:
    """Handles image conversion to JPEG with proper orientation and naming."""

    def __init__(self, filename_manager: FilenameManager):
        """Initialize the image converter.

        Args:
            filename_manager: FilenameManager instance for handling filenames
        """
        self.filename_manager = filename_manager

    def convert_to_jpeg(self, source_path: Path) -> None:
        """Convert any image format to JPEG with datetime-based filename.

        Args:
            source_path: Path to the source image file
        """
        try:
            with Image.open(source_path) as original_img:
                # Preserve EXIF orientation data
                # This ensures the image is displayed in the correct orientation
                img = ImageOps.exif_transpose(original_img)
                if img is None:
                    img = original_img

                # Get datetime and display string
                dt, datetime_display = get_image_datetime(img)

                # Determine output filename
                new_filename = self.filename_manager.determine_output_filename(source_path, dt)
                destination_path = DESTINATION_FOLDER / new_filename

                # Convert to RGB if necessary (images can have different color modes)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                # Save with EXIF data preserved (including orientation)
                img.save(
                    destination_path, format="JPEG", quality=JPEG_QUALITY, optimize=JPEG_OPTIMIZE, exif=img.getexif()
                )

            # Print result
            if source_path.name != new_filename:
                print(f"✓ Converted {source_path.name} → {new_filename}")
            else:
                print(f"✓ Processed {source_path.name} (already in correct format)")
        except Exception as e:
            print(f"✗ Failed to convert {source_path.name}: {e}")
