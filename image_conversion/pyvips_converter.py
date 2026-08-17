"""Image conversion using pyvips for high-performance processing."""

from pathlib import Path
import shutil
import numpy as np
import pyvips
import rawpy  # RAW demosaicing and embedded preview extraction for DNG colour reference
from PIL import Image

from config import (
    DESTINATION_FOLDER,
    HEIC_PASSTHROUGH,
    JPEG_QUALITY,
    RAW_EXTRACT_PREVIEW,
    RAW_HEIF_AUTO_BRIGHT,
    RAW_HEIF_BITDEPTH,
    RAW_HEIF_COMPRESSION,
    RAW_HEIF_EFFORT,
    RAW_HEIF_QUALITY,
    RAW_TO_HEIF,
)
from exif_utils import get_image_datetime, is_samsung_device
from filename_utils import FilenameManager

# RAW formats that use rawpy for proper white-balance-aware processing
RAW_EXTENSIONS = {".dng"}

# Extensions carrying an ISO/IEC 23008-12 (HEIF) container
HEIF_EXTENSIONS = {".heic", ".heif"}

# ftyp major brands that make a file a readable HEIF container. A .heic file is already
# valid HEIF, so renaming one of these needs no decode -- but a few exotic files carry a
# brand outside this set and would be rejected by some readers if simply renamed.
HEIF_FTYP_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1", b"heim", b"heis"}


def _is_heif_container(path: Path) -> bool:
    """Return True when the file's ftyp major brand marks it as HEIF-compatible."""
    try:
        with path.open("rb") as handle:
            header = handle.read(12)
    except OSError:
        return False
    return len(header) == 12 and header[4:8] == b"ftyp" and header[8:12] in HEIF_FTYP_BRANDS


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

    @staticmethod
    def _build_hist_lut(src_band: pyvips.Image, ref_band: pyvips.Image) -> np.ndarray:
        """Build a uint8 LUT that maps src histogram to match ref histogram."""
        src_data = np.frombuffer(src_band.write_to_memory(), dtype=np.uint8)
        ref_data = np.frombuffer(ref_band.write_to_memory(), dtype=np.uint8)

        src_hist, _ = np.histogram(src_data, bins=256, range=(0, 256))
        ref_hist, _ = np.histogram(ref_data, bins=256, range=(0, 256))

        src_cdf = np.cumsum(src_hist, dtype=np.float64)
        ref_cdf = np.cumsum(ref_hist, dtype=np.float64)
        src_cdf /= src_cdf[-1]
        ref_cdf /= ref_cdf[-1]

        return np.searchsorted(ref_cdf, src_cdf).clip(0, 255).astype(np.uint8)

    @staticmethod
    def _output_ext(source_path: Path) -> str:
        """Pick the output extension for a source file.

        The brand check lives here so the chosen filename and the branch that writes it
        can never disagree: a .heic that fails the check gets a .jpg name and takes the
        normal encode path.
        """
        suffix = source_path.suffix.lower()
        if HEIC_PASSTHROUGH and suffix in HEIF_EXTENSIONS and _is_heif_container(source_path):
            return "heif"
        if RAW_TO_HEIF and suffix in RAW_EXTENSIONS:
            return "heif"
        return "jpg"

    def _process_with_pyvips(
        self, source_path: Path, is_samsung: bool, destination_path: Path, sequential: bool = True
    ) -> None:
        is_raw = source_path.suffix.lower() in RAW_EXTENSIONS

        if is_raw and RAW_TO_HEIF:
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

        if is_raw:
            with rawpy.imread(str(source_path)) as raw:
                try:
                    thumb = raw.extract_thumb()
                except Exception:
                    thumb = None

                if RAW_EXTRACT_PREVIEW and thumb is not None:
                    # Write the embedded camera-processed JPEG directly --
                    # exact HDR+ colours, no re-encoding needed.
                    destination_path.write_bytes(bytes(thumb.data))
                    return

                # Full RAW conversion: demosaic with camera white balance,
                # then histogram-match colours to the embedded preview.
                rgb = raw.postprocess(
                    use_camera_wb=True,
                    output_color=rawpy.ColorSpace.sRGB,
                    no_auto_bright=False,
                )

            h, w, b = rgb.shape
            full = pyvips.Image.new_from_memory(rgb.tobytes(), w, h, b, "uchar")
            full = full.copy(interpretation="srgb")

            if thumb is None:
                img = full
            else:
                prev = pyvips.Image.new_from_buffer(bytes(thumb.data), "")

                corrected = []
                for ch in range(3):
                    src_ch = full.extract_band(ch)
                    ref_ch = prev.extract_band(ch)
                    lut = self._build_hist_lut(src_ch, ref_ch)
                    lut_img = pyvips.Image.new_from_memory(lut.tobytes(), 256, 1, 1, "uchar")
                    corrected.append(src_ch.maplut(lut_img))

                img = corrected[0].bandjoin(corrected[1:])
                img = img.copy(interpretation="srgb")
        else:
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

        # Use maximum quality for RAW-derived images to avoid re-compression artefacts
        # on top of what is already a lossy embedded JPEG.
        quality = 100 if is_raw else JPEG_QUALITY
        img.jpegsave(
            str(destination_path),
            Q=quality,
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
            ext = self._output_ext(source_path)
            if self.filename_manager.is_valid_format(source_path.name):
                new_filename = source_path.name
            else:
                new_filename = self.filename_manager.determine_output_filename(source_path, dt, ext)

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

            # A .heic file is already a valid HEIF container -- copy the bytes and rename,
            # no decode or re-encode. _output_ext has already confirmed the ftyp brand.
            if ext == "heif" and source_path.suffix.lower() in HEIF_EXTENSIONS:
                shutil.copy2(source_path, destination_path)
                src = source_path.name.ljust(pad)
                print(f"{counter_str}✓ Passed    {src} → {new_filename} (HEIF, no re-encode)")
                return

            # Otherwise, proceed with full conversion
            if source_path.suffix.lower() in RAW_EXTENSIONS:
                # RAW format loaders in libvips don't support sequential access
                self._process_with_pyvips(source_path, is_samsung, destination_path, sequential=False)
            else:
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
