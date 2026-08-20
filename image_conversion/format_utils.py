"""Content-based format detection. File extensions are a claim, not a fact.

Tools like Picasa rewrite a DNG as JPEG while keeping the .dng filename, so routing
on the suffix sends such a file to rawpy, which correctly refuses it. Every routing
decision in the pipeline reads the leading bytes instead.
"""

from pathlib import Path

from config import RAW_EXTENSIONS

# ftyp major brands that make a file a readable HEIF container
HEIF_FTYP_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1", b"heim", b"heis"}

# TIFF byte-order marks -- DNG is a TIFF variant
TIFF_MAGIC = (b"II*\x00", b"MM\x00*")

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

JPEG = "jpeg"
HEIF = "heif"
PNG = "png"
RAW = "raw"
OTHER = "other"


def content_ext(path: Path) -> str:
    """Extension matching the file's real format, falling back to its own suffix.

    ExifTool refuses to touch a file whose extension contradicts its bytes ("Not a valid
    JPG (looks more like a PNG)"), so even a copy that is never re-encoded has to be named
    for what it actually is. RAW and OTHER keep the source suffix: there is no single
    extension they map to.
    """
    return {JPEG: "jpg", HEIF: "heif", PNG: "png"}.get(detect_kind(path), path.suffix.lower().lstrip("."))


def detect_kind(path: Path) -> str:
    """Identify a file from its leading bytes, ignoring its extension.

    Returns one of JPEG, HEIF, PNG, RAW or OTHER. OTHER is the safe default: it routes
    to the general pyvips encoder, which handles anything libvips can open.
    """
    try:
        with path.open("rb") as handle:
            header = handle.read(12)
    except OSError:
        return OTHER

    if header[:3] == b"\xff\xd8\xff":
        return JPEG
    if len(header) == 12 and header[4:8] == b"ftyp" and header[8:12] in HEIF_FTYP_BRANDS:
        return HEIF
    if header[:8] == PNG_MAGIC:
        return PNG
    if header[:4] in TIFF_MAGIC and path.suffix.lower() in RAW_EXTENSIONS:
        # ponytail: DNG and plain TIFF share magic bytes, so the extension picks the
        # flavour once the content has confirmed the TIFF family. Telling them apart
        # properly means parsing IFD tags for DNGVersion -- more code than this earns.
        return RAW
    return OTHER


if __name__ == "__main__":
    # Self-check: poetry run python image_conversion/format_utils.py
    #
    # Header bytes only -- no sample library needed, so this runs in any clone. The
    # cases that matter are the ones where the name and the bytes disagree, because
    # trusting the name is the failure this module exists to prevent.
    import tempfile

    CASES = [
        ("shot.dng", b"\xff\xd8\xff\xe0" + b"\x00" * 8, JPEG),  # JPEG wearing a .dng name
        ("shot.jpg", b"\xff\xd8\xff\xdb" + b"\x00" * 8, JPEG),
        ("shot.jpg", PNG_MAGIC + b"\x00" * 4, PNG),  # PNG wearing a .jpg name
        ("shot.heic", b"\x00\x00\x00\x18ftypheic", HEIF),
        ("shot.heic", b"\x00\x00\x00\x18ftypqt  ", OTHER),  # ftyp, but not a HEIF brand
        ("shot.dng", b"II*\x00" + b"\x00" * 8, RAW),
        ("scan.tif", b"II*\x00" + b"\x00" * 8, OTHER),  # TIFF magic, but not a RAW extension
        ("clip.mp4", b"\x00\x00\x00\x18ftypmp42", OTHER),
        ("empty.jpg", b"", OTHER),
    ]

    with tempfile.TemporaryDirectory() as tmp:
        for name, header, expected in CASES:
            path = Path(tmp) / name
            path.write_bytes(header)
            got = detect_kind(path)
            assert got == expected, f"{name} ({header[:8]!r}): expected {expected}, got {got}"

        # A name that contradicts the bytes is renamed for the bytes; anything the
        # detector cannot name keeps its own suffix.
        assert content_ext(Path(tmp) / "shot.jpg") == "png"
        assert content_ext(Path(tmp) / "shot.dng") == "dng"
        assert content_ext(Path(tmp) / "clip.mp4") == "mp4"

    assert detect_kind(Path(tmp) / "gone.jpg") == OTHER  # unreadable path falls back safely
    print(f"ok  detect_kind agrees with the bytes on {len(CASES)} cases")
