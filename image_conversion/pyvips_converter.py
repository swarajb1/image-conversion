"""Image conversion using pyvips for high-performance processing."""

from pathlib import Path
import shutil
import pyvips
from PIL import Image

from config import DESTINATION_FOLDER, JPEG_QUALITY
from exif_utils import get_image_datetime, is_samsung_device
from filename_utils import FilenameManager


class PyVipsImageConverter:
    """Handles image conversion to JPEG using pyvips for better performance."""

    def __init__(self, filename_manager: FilenameManager, samsung_rename_only: bool = False):
        """Initialize the pyvips image converter.

        Args:
            filename_manager: FilenameManager instance for handling filenames
            samsung_rename_only: If True, Samsung images are only renamed, not converted
        """
        self.filename_manager = filename_manager
        self.samsung_rename_only = samsung_rename_only

    def convert_to_jpeg(self, source_path: Path, current: int = 0, total: int = 0) -> None:
        """Convert any image format to JPEG with datetime-based filename using pyvips.

        Args:
            source_path: Path to the source image file
            current: Current file number (for progress display)
            total: Total number of files (for progress display)
        """
        try:
            # Get datetime from EXIF data using PIL (for compatibility with existing code)

            with Image.open(source_path) as pil_img:
                dt, datetime_display = get_image_datetime(pil_img)

                # Check if image is from Samsung
                is_samsung = is_samsung_device(pil_img)

            # Determine output filename
            if self.filename_manager.is_valid_format(source_path.name):
                new_filename = source_path.name
            else:
                new_filename = self.filename_manager.determine_output_filename(source_path, dt)

            destination_path = DESTINATION_FOLDER / new_filename

            # If Samsung rename-only mode is enabled and image is from Samsung, just copy/rename
            if self.samsung_rename_only and is_samsung:
                shutil.copy2(source_path, destination_path)

                # Print result
                counter_str = f"[{current}/{total}] " if total > 0 else ""
                if source_path.name != new_filename:
                    print(f"{counter_str}✓ Renamed {source_path.name} → {new_filename} (Samsung, no conversion)")
                else:
                    print(f"{counter_str}✓ Copied {source_path.name} (Samsung, no conversion)")
                return

            # Otherwise, proceed with full conversion
            # Load image with pyvips
            img = pyvips.Image.new_from_file(str(source_path), access="sequential")

            # Apply orientation correction if EXIF orientation exists
            try:
                if "orientation" in img.get_fields():
                    img = img.autorot()
            except Exception:
                # Some formats don't support autorot, skip silently
                pass

            # Check if we need to flatten alpha channel
            if img.bands == 4 and img.hasalpha():
                # Flatten alpha to white background
                img = img.flatten(background=[255, 255, 255])

            # Apply ICC color transform to sRGB to ensure proper color handling
            try:
                img = img.icc_transform("srgb")

                # Mild gamma lift to counter HDR loss (Samsung-specific)
                if is_samsung:
                    img = img.gamma(1.1)
            except Exception:
                # Fallback to colourspace if ICC transform fails
                if img.interpretation != "srgb":
                    if img.bands >= 3:
                        img = img.colourspace("srgb")

            # Save as JPEG with high quality
            img.jpegsave(
                str(destination_path),
                Q=JPEG_QUALITY,
                optimize_coding=True,
                strip=True,  # Strip metadata to avoid thumbnail rotation issues
                interlace=True,  # Progressive JPEG
                subsample_mode="off",  # 4:4:4 chroma subsampling (no subsampling, highest quality)
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
