# Blank Finder icon on a passed-through HEIF

## Symptom

After a run, one `.heif` in the output shows a generic/blank icon in Finder while others show a photo thumbnail.

## Cause

HEIF files are passed through (bytes copied) and stripped in place with ExifTool `-all=`. The file is rewritten after Finder may already have cached its icon, so Finder keeps showing the stale entry.

The file itself is fine — the HEIF thumbnail item survives the strip:

```bash
heif-info IMG_<date>.heif          # lists "thumbnail: 312x416" under the primary image
qlmanage -t -o /tmp IMG_<date>.heif  # renders the thumbnail to /tmp/IMG_<date>.heif.png
```

Seen with a 24 MP iPhone capture (`5712x4284`, `896x640` tiles) next to a 12 MP one (`4032x3024`, `512x512` tiles); both had identical item structure and both rendered via `qlmanage`.

## Fix

```bash
qlmanage -r cache   # reset QuickLook thumbnail cache
qlmanage -r         # reload QuickLook generators
killall Finder      # relaunch Finder so icons regenerate
```

If the icon is still blank, bump the mtime to force regeneration:

```bash
touch IMG_<date>.heif
```

No converter change is needed.
