"""Shared metadata stripping helpers."""

import subprocess
from pathlib import Path

# Identification metadata fields passed to ExifTool for files that skip re-encoding.
# Mirrors the list in main_1.py.
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


def strip_metadata(path: Path) -> bool:
    """Strip all identification fields from *path* using ExifTool. Returns True on success."""
    cmd = ["exiftool", "-overwrite_original"] + [f"-{field}=" for field in IDENTIFICATION_FIELDS] + [str(path)]
    return subprocess.run(cmd, capture_output=True).returncode == 0
