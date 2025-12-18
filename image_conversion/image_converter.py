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

    def convert_to_jpeg(self, source_path: Path, current: int = 0, total: int = 0) -> None:
        """Convert any image format to JPEG with datetime-based filename.

        Args:
            source_path: Path to the source image file
            current: Current file number (for progress display)
            total: Total number of files (for progress display)
        """
        try:
            # Process files by determining filename based on datetime format
            destination_path = DESTINATION_FOLDER / source_path.name

            with Image.open(source_path) as original_img:
                # Preserve EXIF orientation data for correct display
                img = ImageOps.exif_transpose(original_img)
                if img is None:
                    img = original_img

                # Get datetime and display string
                dt, datetime_display = get_image_datetime(img)

                # Check if source filename already follows the datetime format
                # If it does, keep the same name but strip metadata
                # Otherwise, generate a new filename based on datetime or convert datetime-only format
                source_stem = source_path.stem
                if self.filename_manager.is_valid_format(source_path.name):
                    # Source already has correct format - keep the name, strip metadata
                    new_filename = source_path.name
                else:
                    # Generate new filename based on datetime or convert datetime-only format
                    new_filename = self.filename_manager.determine_output_filename(source_path, dt)
                destination_path = DESTINATION_FOLDER / new_filename

                # Convert to RGB if necessary (images can have different color modes)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                # Save with progressive JPEG encoding for better compression
                img.save(
                    destination_path,
                    format="JPEG",
                    quality=JPEG_QUALITY,
                    optimize=JPEG_OPTIMIZE,
                    progressive=True,
                )

            # Print result
            counter_str = f"[{current}/{total}] " if total > 0 else ""
            if source_path.name != new_filename:
                print(f"{counter_str}✓ Converted {source_path.name} → {new_filename}")
            else:
                print(f"{counter_str}✓ Processed {source_path.name} (already in correct format)")
        except Exception as e:
            counter_str = f"[{current}/{total}] " if total > 0 else ""
            print(f"{counter_str}✗ Failed to convert {source_path.name}: {e}")
