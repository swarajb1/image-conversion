"""Image conversion and processing logic."""

from pathlib import Path
import shutil
from PIL import Image, ImageOps

from config import DESTINATION_FOLDER, JPEG_QUALITY, JPEG_OPTIMIZE
from exif_utils import get_image_datetime
from filename_utils import FilenameManager


class ImageConverter:
    """Handles image conversion to JPEG with proper orientation and naming."""

    def __init__(self, filename_manager: FilenameManager, samsung_rename_only: bool = False):
        """Initialize the image converter.

        Args:
            filename_manager: FilenameManager instance for handling filenames
            samsung_rename_only: If True, Samsung images are only renamed, not converted
        """
        self.filename_manager = filename_manager
        self.samsung_rename_only = samsung_rename_only

    def convert_to_jpeg(self, source_path: Path, current: int = 0, total: int = 0) -> None:
        """Convert any image format to JPEG with datetime-based filename.

        Args:
            source_path: Path to the source image file
            current: Current file number (for progress display)
            total: Total number of files (for progress display)
        """
        try:
            with Image.open(source_path) as original_img:
                # Get datetime first before any transformations
                dt, datetime_display = get_image_datetime(original_img)

                # Check if image is from Samsung
                is_samsung = False
                try:
                    exif = original_img.getexif()
                    if exif:
                        make = exif.get(271, "")  # Make tag
                        model = exif.get(272, "")  # Model tag
                        if "samsung" in str(make).lower() or "samsung" in str(model).lower():
                            is_samsung = True
                except Exception:
                    pass

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
                # Extract ICC profile from original before any transformation
                icc_profile = original_img.info.get("icc_profile")

                # Preserve EXIF orientation data for correct display
                img = ImageOps.exif_transpose(original_img)
                if img is None:
                    img = original_img

                # If exif_transpose created a new image, ensure ICC profile is still there
                if img is not original_img and icc_profile and "icc_profile" not in img.info:
                    img.info["icc_profile"] = icc_profile

                # Convert to RGB if necessary (images can have different color modes)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                # Save with high quality to preserve visual appearance
                # Use quality=95 and subsampling=0 to minimize visual degradation
                save_kwargs = {
                    "format": "JPEG",
                    "quality": JPEG_QUALITY,
                    "optimize": JPEG_OPTIMIZE,
                    "progressive": True,
                    "subsampling": 0,  # 4:4:4 chroma subsampling (highest quality)
                }
                if icc_profile:
                    save_kwargs["icc_profile"] = icc_profile

                img.save(destination_path, **save_kwargs)

            # Print result
            counter_str = f"[{current}/{total}] " if total > 0 else ""
            if source_path.name != new_filename:
                print(f"{counter_str}✓ Converted {source_path.name} → {new_filename}")
            else:
                print(f"{counter_str}✓ Processed {source_path.name} (already in correct format)")
        except Exception as e:
            counter_str = f"[{current}/{total}] " if total > 0 else ""
            print(f"{counter_str}✗ Failed to convert {source_path.name}: {e}")
