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
    # Self-check against the real samples: poetry run python image_conversion/format_utils.py
    #
    # PIL decodes independently of this module, so if it disagrees then detect_kind
    # would route the file to a branch that cannot read it -- which is the whole
    # failure this module exists to prevent. Extensions are deliberately never
    # consulted here: distrusting them is the point.
    from collections import Counter

    import pillow_heif
    from PIL import Image

    pillow_heif.register_heif_opener()

    # RAW is absent because PIL does not decode raw; videos and anything else land
    # in OTHER, which makes no claim worth checking.
    PIL_FORMATS = {JPEG: {"JPEG", "MPO"}, HEIF: {"HEIF"}, PNG: {"PNG"}}

    counts: Counter = Counter()
    for sample in sorted(Path("files/to_convert").glob("*")):
        if not sample.is_file():
            continue
        kind = detect_kind(sample)
        counts[kind] += 1
        expected = PIL_FORMATS.get(kind)
        if expected is None:
            continue
        with Image.open(sample) as img:
            assert img.format in expected, f"{sample.name}: detect_kind said {kind}, PIL says {img.format}"

    assert counts, "no sample files found -- run from the repository root"
    for kind, n in sorted(counts.items()):
        print(f"{kind:<6} {n:>4}")
    print("detect_kind agrees with PIL on every decodable sample")
