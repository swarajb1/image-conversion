"""Shared metadata stripping helpers."""

import subprocess
import sys
from pathlib import Path

# Identification metadata fields passed to ExifTool for files that skip re-encoding.
IDENTIFICATION_FIELDS = [
    # --- Location ---
    "GPSLatitude",
    "GPSLongitude",
    "GPSAltitude",
    "GPSImgDirection",
    "GPSSpeed",
    "GPSTrack",
    "GPSDateStamp",
    "GPSTimeStamp",
    "GPSDestLatitude",
    "GPSDestLongitude",
    # QuickTime keeps its location in com.apple.quicktime.location.ISO6709 / ©xyz, which
    # ExifTool names GPSCoordinates -- the GPSLatitude/GPSLongitude pair never reaches it.
    "GPSCoordinates",
    "GPSPosition",
    "LocationCreated",
    "City",
    "Province-State",
    "Country",
    "Sub-location",
    # --- Device identity ---
    "Make",
    "Model",
    "SerialNumber",
    "LensSerialNumber",
    "LensMake",
    "LensModel",
    "OwnerName",
    "CameraOwnerName",
    # --- Timestamps ---
    "DateTimeOriginal",
    "CreateDate",
    "ModifyDate",
    "MediaCreateDate",
    "MediaModifyDate",
    "TrackCreateDate",
    "TrackModifyDate",
    "CreationTime",
    # --- Person / identity ---
    "Artist",
    "Creator",
    "Copyright",
    "PersonInImage",
    "By-line",
    "Contact",
    # --- Software trail ---
    "Software",
    "ProcessingSoftware",
    "CreatorTool",
    # --- Document lineage ---
    "DocumentID",
    "OriginalDocumentID",
    "InstanceID",
    "DerivedFrom",
    # --- Device pairing ---
    "MediaGroupUUID",
    "ContentIdentifier",
    "ImageUniqueID",
]


# Formats where field-by-field clearing is not enough, so everything goes:
#   HEIC/HEIF -- Apple keeps a second copy of GPS/Make/Model in its ItemProperties
#                container, which named-tag clearing never reaches.
#   PNG       -- metadata lives in free-form tEXt/iTXt/eXIf chunks, so there is no
#                fixed set of tag names to enumerate.
STRIP_ALL_EXTENSIONS = {".heic", ".heif", ".png"}


def check_exiftool() -> None:
    """Verify ExifTool is installed and on PATH."""
    try:
        subprocess.run(["exiftool", "-ver"], capture_output=True)
    except OSError:
        print("Error: exiftool is not installed or not on PATH.")
        print("  macOS:  brew install exiftool")
        print("  Linux:  sudo apt install libimage-exiftool-perl")
        sys.exit(1)


def _strip_command(path: Path) -> list[str]:
    """Build the ExifTool command that clears identification metadata from *path*."""
    if path.suffix.lower() in STRIP_ALL_EXTENSIONS:
        return ["exiftool", "-overwrite_original", "-all=", str(path)]
    return ["exiftool", "-overwrite_original"] + [f"-{field}=" for field in IDENTIFICATION_FIELDS] + [str(path)]


def strip_metadata(path: Path) -> bool:
    """Strip all identification fields from *path* using ExifTool. Returns True on success."""
    return subprocess.run(_strip_command(path), capture_output=True).returncode == 0


if __name__ == "__main__":
    # Self-check: the -all= branch is the one that must not regress -- field-by-field
    # clearing leaves Apple's ItemProperties copy of GPS/Make/Model, and every PNG
    # text chunk, in place.
    for name in ("a.heic", "a.HEIC", "a.heif", "a.png", "a.PNG"):
        assert "-all=" in _strip_command(Path(name)), name

    jpg = _strip_command(Path("a.jpg"))
    assert "-all=" not in jpg
    assert "-GPSLatitude=" in jpg and "-Make=" in jpg

    # Videos take the same field-by-field branch, so the QuickTime location tag has to be
    # in the shared list or an MP4 leaves with its GPS intact.
    assert "-GPSCoordinates=" in _strip_command(Path("a.mp4"))
    print(f"ok  HEIF/PNG use -all=, other formats clear {len(IDENTIFICATION_FIELDS)} named fields")
