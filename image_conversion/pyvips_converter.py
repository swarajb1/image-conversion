"""Image conversion using pyvips for high-performance processing."""

from pathlib import Path
import shutil
import pyvips
import rawpy  # RAW demosaicing for DNG
from PIL import Image

from config import (
    DESTINATION_FOLDER,
    HEIC_PASSTHROUGH,
    JPEG_QUALITY,
    RAW_HEIF_AUTO_BRIGHT,
    RAW_HEIF_BITDEPTH,
    RAW_HEIF_COMPRESSION,
    RAW_HEIF_EFFORT,
    RAW_HEIF_QUALITY,
)
from exif_utils import get_image_datetime
from filename_utils import FilenameManager
from format_utils import HEIF, RAW, detect_kind
from metadata_utils import strip_metadata


class PyVipsImageConverter:
    """Handles image conversion to JPEG using pyvips for better performance."""

    def __init__(self, filename_manager: FilenameManager, max_name_len: int = 0):
        """Initialize the pyvips image converter.

        Args:
            filename_manager: FilenameManager instance for handling filenames
            max_name_len: Max source filename length used to align terminal output columns
        """
        self.filename_manager = filename_manager
        self.max_name_len = max_name_len

    @staticmethod
    def _output_ext(source_path: Path) -> str:
        """Pick the output extension from the file's real format.

        Detection lives here so the chosen filename and the branch that writes it can
        never disagree: a file that is not really HEIF gets a .jpg name and takes the
        normal encode path.
        """
        kind = detect_kind(source_path)
        if HEIC_PASSTHROUGH and kind == HEIF:
            return "heif"
        if kind == RAW:
            return "heif"
        return "jpg"

    def _process_with_pyvips(self, source_path: Path, destination_path: Path, sequential: bool = True) -> None:
        if detect_kind(source_path) == RAW:
            # Full demosaic at 16 bits, encoded to 10-bit HEIF. libvips maps the full
            # ushort 0-65535 range into the target bit depth itself, so the array is
            # handed over unscaled -- shifting it down to 0-1023 first would go black.
            with rawpy.imread(str(source_path)) as raw:
                rgb = raw.postprocess(
                    output_bps=16,
                    use_camera_wb=True,
                    output_color=rawpy.ColorSpace.sRGB,
                    no_auto_bright=not RAW_HEIF_AUTO_BRIGHT,
                )

            h, w, b = rgb.shape
            img = pyvips.Image.new_from_memory(rgb.tobytes(), w, h, b, "ushort")
            img = img.copy(interpretation="rgb16")
            img.heifsave(
                str(destination_path),
                compression=RAW_HEIF_COMPRESSION,
                Q=RAW_HEIF_QUALITY,
                bitdepth=RAW_HEIF_BITDEPTH,
                effort=RAW_HEIF_EFFORT,
                subsample_mode="off",
                strip=True,
                profile="srgb",
            )
            return

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

    def convert_to_jpeg(self, source_path: Path, current: int = 0, total: int = 0) -> tuple[str, str | None]:
        """Convert any image format to JPEG with datetime-based filename using pyvips.

        Args:
            source_path: Path to the source image file
            current: Current file number (for progress display)
            total: Total number of files (for progress display)

        Returns:
            (action, error) where action is the label printed for this file and error is
            the failure message, or None on success
        """
        try:
            # Get datetime from EXIF data using PIL (for compatibility with existing code)

            with Image.open(source_path) as pil_img:
                dt, datetime_display = get_image_datetime(pil_img)

            # Determine output filename
            ext = self._output_ext(source_path)
            if self.filename_manager.is_valid_format(source_path.name):
                new_filename = source_path.name
            else:
                new_filename = self.filename_manager.determine_output_filename(source_path, dt, ext)

            destination_path = DESTINATION_FOLDER / new_filename

            pad = self.max_name_len
            total_w = len(str(total))
            counter_str = f"[{current:>{total_w}}/{total}] " if total > 0 else ""

            # A .heic file is already a valid HEIF container -- copy the bytes and rename,
            # no decode or re-encode. _output_ext has already confirmed the ftyp brand.
            if ext == "heif" and detect_kind(source_path) == HEIF:
                shutil.copy2(source_path, destination_path)
                # There is no encoder on this path to apply strip=True, so the identification
                # metadata every other output drops has to be removed explicitly. The pixels
                # stay byte-identical; only the metadata boxes are rewritten.
                src = source_path.name.ljust(pad)
                if not strip_metadata(destination_path):
                    print(f"{counter_str}✗ Failed    {src} → {new_filename} (HEIF copied; METADATA NOT STRIPPED)")
                    return "Failed", "exiftool could not strip metadata"
                print(f"{counter_str}✓ Passed    {src} → {new_filename} (HEIF, no re-encode)")
                return "Passed", None

            # Otherwise, proceed with full conversion
            if detect_kind(source_path) == RAW:
                # RAW format loaders in libvips don't support sequential access
                self._process_with_pyvips(source_path, destination_path, sequential=False)
            else:
                try:
                    self._process_with_pyvips(source_path, destination_path, sequential=True)
                except pyvips.Error as e:
                    if "out of order" in str(e).lower():
                        # Some JPEGs have non-sequential scan patterns; retry with full load into RAM
                        self._process_with_pyvips(source_path, destination_path, sequential=False)
                    else:
                        raise

            if source_path.name != new_filename:
                src = source_path.name.ljust(pad)
                print(f"{counter_str}✓ Converted {src} → {new_filename}")
                return "Converted", None

            print(f"{counter_str}✓ Processed {source_path.name} (already in correct format)")
            return "Processed", None

        except Exception as e:
            total_w = len(str(total))
            counter_str = f"[{current:>{total_w}}/{total}] " if total > 0 else ""
            print(f"{counter_str}✗ Failed    {source_path.name}: {e}")
            return "Failed", str(e)
