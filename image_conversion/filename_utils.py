"""Utilities for filename validation and generation."""

import re
from datetime import datetime
from pathlib import Path

from config import FILENAME_PATTERN, DATETIME_ONLY_PATTERN, SOURCE_FOLDER


def collect_files(extensions: list[str]) -> list[Path]:
    """Glob SOURCE_FOLDER for files matching the given extensions, case-insensitively."""
    files: list[Path] = []
    for ext in extensions:
        pattern = f"*.[{ext[0].lower()}{ext[0].upper()}]" + "".join(f"[{c.lower()}{c.upper()}]" for c in ext[1:])
        files.extend(SOURCE_FOLDER.glob(pattern))
    return sorted(files, key=lambda f: f.name)


class FilenameManager:
    """Manages filename generation and validation with duplicate tracking."""

    def __init__(self):
        """Initialize the filename manager with an empty set of used filenames."""
        self.used_filenames: set[str] = set()

    def is_valid_format(self, filename: str) -> bool:
        """Check if filename follows IMG_<yyyymmdd>_<hhmmss>.jpg format.

        Args:
            filename: The filename to check (without path)

        Returns:
            bool: True if filename matches the format, False otherwise
        """
        return bool(re.match(FILENAME_PATTERN, filename))

    def is_datetime_only_format(self, filename: str) -> bool:
        """Check if filename follows <yyyymmdd>_<hhmmss>.jpg/mp4 format (without prefix).

        Args:
            filename: The filename to check (without path)

        Returns:
            bool: True if filename matches the datetime-only format, False otherwise
        """
        return bool(re.match(DATETIME_ONLY_PATTERN, filename, re.IGNORECASE))

    def generate_filename(self, dt: datetime | None, source_name: str, ext: str = "jpg") -> str:
        """Generate filename in format IMG_<yyyymmdd>_<hhmmss>.<ext> with deduplication.

        Args:
            dt: datetime object from EXIF data, or None
            source_name: original filename for fallback
            ext: output file extension without the leading dot

        Returns:
            str: Generated filename
        """
        if dt:
            base_name = f"IMG_{dt.strftime('%Y%m%d_%H%M%S')}"
        else:
            # Fallback to timestamp-based name if no EXIF data
            base_name = f"IMG_{datetime.now().strftime('%Y%m%d_%H%M%S')}_noexif"

        filename = f"{base_name}.{ext}"

        # Handle duplicates by checking the set of already-used filenames for this run
        if filename in self.used_filenames:
            counter = 1
            while f"{base_name}-{counter}.{ext}" in self.used_filenames:
                counter += 1
            filename = f"{base_name}-{counter}.{ext}"

        # Record filename as used for this run
        self.used_filenames.add(filename)
        return filename

    def is_valid_video_format(self, filename: str) -> bool:
        """Check if filename follows VID_<yyyymmdd>_<hhmmss>.mp4 format.

        Args:
            filename: The filename to check (without path)

        Returns:
            bool: True if filename matches the format, False otherwise
        """
        from config import VIDEO_FILENAME_PATTERN

        return bool(re.match(VIDEO_FILENAME_PATTERN, filename))

    def generate_video_filename(self, dt: datetime | None, source_name: str, ext: str = "mp4") -> str:
        """Generate filename in format VID_<yyyymmdd>_<hhmmss>.<ext> with deduplication.

        Args:
            dt: datetime object from video metadata, or None
            source_name: original filename for fallback
            ext: output file extension without the leading dot

        Returns:
            str: Generated filename
        """
        if dt:
            base_name = f"VID_{dt.strftime('%Y%m%d_%H%M%S')}"
        else:
            # Fallback to timestamp-based name if no metadata
            base_name = f"VID_{datetime.now().strftime('%Y%m%d_%H%M%S')}_nometa"

        filename = f"{base_name}.{ext}"

        # Handle duplicates by checking the set of already-used filenames for this run
        if filename in self.used_filenames:
            counter = 1
            while f"{base_name}-{counter}.{ext}" in self.used_filenames:
                counter += 1
            filename = f"{base_name}-{counter}.{ext}"

        # Record filename as used for this run
        self.used_filenames.add(filename)
        return filename

    def determine_output_filename(self, source_path: Path, dt: datetime | None, ext: str = "jpg") -> str:
        """Determine the appropriate output filename based on source and format rules.

        Args:
            source_path: Path to the source image file
            dt: datetime object from EXIF data, or None
            ext: output file extension without the leading dot

        Returns:
            str: The output filename to use
        """
        # Check if filename is in datetime-only format (e.g., "20251207_175000.jpg")
        if self.is_datetime_only_format(source_path.name):
            # Add IMG_ prefix to the existing filename
            stem = source_path.stem  # e.g., "20251207_175000"
            new_filename = f"IMG_{stem}.{ext}"
            self.used_filenames.add(new_filename)
            return new_filename

        # Always generate new filename based on datetime metadata
        return self.generate_filename(dt, source_path.name, ext)

    def determine_video_output_filename(self, source_path: Path, dt: datetime | None) -> str:
        """Determine the appropriate output filename for videos.

        Args:
            source_path: Path to the source video file
            dt: datetime object from video metadata, or None

        Returns:
            str: The output filename to use
        """
        # Check if filename is in datetime-only format (e.g., "20251207_175000.mp4")
        if self.is_datetime_only_format(source_path.name):
            # Add VID_ prefix to the existing filename
            stem = source_path.stem  # e.g., "20251207_175000"
            new_filename = f"VID_{stem}.mp4"
            self.used_filenames.add(new_filename)
            return new_filename

        # Always generate new filename based on datetime metadata
        return self.generate_video_filename(dt, source_path.name)
