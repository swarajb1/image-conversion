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

JPEG = "jpeg"
HEIF = "heif"
RAW = "raw"
OTHER = "other"


def detect_kind(path: Path) -> str:
    """Identify a file from its leading bytes, ignoring its extension.

    Returns one of JPEG, HEIF, RAW or OTHER. OTHER is the safe default: it routes to
    the general pyvips encoder, which handles anything libvips can open.
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
    if header[:4] in TIFF_MAGIC and path.suffix.lower() in RAW_EXTENSIONS:
        # ponytail: DNG and plain TIFF share magic bytes, so the extension picks the
        # flavour once the content has confirmed the TIFF family. Telling them apart
        # properly means parsing IFD tags for DNGVersion -- more code than this earns.
        return RAW
    return OTHER


if __name__ == "__main__":
    # Self-check against the real samples: poetry run python image_conversion/format_utils.py
    # The .dng entry expects JPEG because these particular samples were rewritten by
    # Picasa. Add a genuine DNG and this assertion must be updated.
    expected = {".heic": HEIF, ".jpg": JPEG, ".dng": JPEG}

    checked = 0
    for sample in sorted(Path("files/to_convert").glob("*")):
        want = expected.get(sample.suffix.lower())
        if want is None:
            continue
        got = detect_kind(sample)
        assert got == want, f"{sample.name}: expected {want}, got {got}"
        print(f"ok  {sample.name:<28} -> {got}")
        checked += 1

    assert checked, "no sample files found -- run from the repository root"
    print(f"all {checked} format detections correct")
