"""Utilities for filename validation and generation."""

import re
from datetime import datetime
from pathlib import Path

from config import DESTINATION_FOLDER, FILENAME_PATTERN


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

    def generate_filename(self, dt: datetime | None, source_name: str) -> str:
        """Generate filename in format IMG_<yyyymmdd>_<hhmmss>.jpg with deduplication.

        Args:
            dt: datetime object from EXIF data, or None
            source_name: original filename for fallback

        Returns:
            str: Generated filename
        """
        if dt:
            base_name = f"IMG_{dt.strftime('%Y%m%d_%H%M%S')}"
        else:
            # Fallback to timestamp-based name if no EXIF data
            base_name = f"IMG_{datetime.now().strftime('%Y%m%d_%H%M%S')}_noexif"

        filename = f"{base_name}.jpg"

        # Handle duplicates by checking the set of already-used filenames for this run
        if filename in self.used_filenames:
            counter = 1
            while f"{base_name}-{counter}.jpg" in self.used_filenames:
                counter += 1
            filename = f"{base_name}-{counter}.jpg"

        # Record filename as used for this run
        self.used_filenames.add(filename)
        return filename

    def determine_output_filename(self, source_path: Path, dt: datetime | None) -> str:
        """Determine the appropriate output filename based on source and format rules.

        Args:
            source_path: Path to the source image file
            dt: datetime object from EXIF data, or None

        Returns:
            str: The output filename to use
        """
        source_lower = source_path.name.lower()

        # Check if filename follows the required format (handles both .jpg and .jpeg)
        if self.is_valid_format(source_path.name):
            # Already follows format, keep the name
            return source_path.name
        elif source_lower.endswith(".jpeg") and self.is_valid_format(source_path.stem + ".jpg"):
            # It's .jpeg but would be valid as .jpg, convert extension
            return source_path.stem + ".jpg"
        else:
            # Doesn't follow format, generate new filename
            return self.generate_filename(dt, source_path.name)
