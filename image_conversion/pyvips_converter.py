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

    def __init__(self, filename_manager: FilenameManager, samsung_rename_only: bool = False, max_name_len: int = 0):
        """Initialize the pyvips image converter.

        Args:
            filename_manager: FilenameManager instance for handling filenames
            samsung_rename_only: If True, Samsung images are only renamed, not converted
            max_name_len: Max source filename length used to align terminal output columns
        """
        self.filename_manager = filename_manager
        self.samsung_rename_only = samsung_rename_only
        self.max_name_len = max_name_len

    def _process_with_pyvips(
        self, source_path: Path, is_samsung: bool, destination_path: Path, sequential: bool = True
    ) -> None:
        load_kwargs = {"access": "sequential"} if sequential else {}
        img = pyvips.Image.new_from_file(str(source_path), **load_kwargs)

        try:
            if "orientation" in img.get_fields():
                img = img.autorot()
        except Exception:
            pass

        if img.bands == 4 and img.hasalpha():
            img = img.flatten(background=[255, 255, 255])

        try:
            img = img.icc_transform("srgb")
            if is_samsung:
                img = img.gamma(1.1)
        except Exception:
            if img.interpretation != "srgb":
                if img.bands >= 3:
                    img = img.colourspace("srgb")

        img.jpegsave(
            str(destination_path),
            Q=JPEG_QUALITY,
            optimize_coding=True,
            strip=True,
            interlace=True,
            subsample_mode="off",
        )

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

            pad = self.max_name_len
            total_w = len(str(total))
            counter_str = f"[{current:>{total_w}}/{total}] " if total > 0 else ""

            # If Samsung rename-only mode is enabled and image is from Samsung, just copy/rename
            if self.samsung_rename_only and is_samsung:
                shutil.copy2(source_path, destination_path)

                if source_path.name != new_filename:
                    src = source_path.name.ljust(pad)
                    print(f"{counter_str}✓ Renamed   {src} → {new_filename} (Samsung, no conversion)")
                else:
                    print(f"{counter_str}✓ Copied    {source_path.name} (Samsung, no conversion)")
                return

            # Otherwise, proceed with full conversion
            try:
                self._process_with_pyvips(source_path, is_samsung, destination_path, sequential=True)
            except pyvips.Error as e:
                if "out of order" in str(e).lower():
                    # Some JPEGs have non-sequential scan patterns; retry with full load into RAM
                    self._process_with_pyvips(source_path, is_samsung, destination_path, sequential=False)
                else:
                    raise

            if source_path.name != new_filename:
                src = source_path.name.ljust(pad)
                print(f"{counter_str}✓ Converted {src} → {new_filename}")
            else:
                print(f"{counter_str}✓ Processed {source_path.name} (already in correct format)")

        except Exception as e:
            total_w = len(str(total))
            counter_str = f"[{current:>{total_w}}/{total}] " if total > 0 else ""
            print(f"{counter_str}✗ Failed    {source_path.name}: {e}")
