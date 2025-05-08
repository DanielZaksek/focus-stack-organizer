"""Common utilities and classes used across the Focus Stack Organizer."""

from enum import Enum, auto
from typing import Dict, Set

class ImageFormat(Enum):
    """Supported image formats."""
    RAW = auto()
    STANDARD = auto()

    @classmethod
    def extensions(cls) -> Dict[str, Set[str]]:
        """Get supported file extensions for each format."""
        return {
            'RAW': {
                ".orf",  # Olympus
                ".nef",  # Nikon
                ".cr2",  # Canon
                ".arw",  # Sony
                ".rw2",  # Panasonic
                ".raf",  # Fuji
                ".dng"   # Adobe
            },
            'STANDARD': {
                ".jpg",
                ".jpeg",
                ".tiff",
                ".tif",
                ".png"
            },
        }

    @classmethod
    def all_extensions(cls) -> Set[str]:
        """Get all supported file extensions."""
        return {ext.lower() for exts in cls.extensions().values() for ext in exts}

    @classmethod
    def is_supported(cls, filename: str) -> bool:
        """Check if a filename has a supported extension."""
        return any(filename.lower().endswith(ext) for ext in cls.all_extensions())
