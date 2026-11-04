"""Exception hierarchy for the bitmap query service.

Catch BitmapQueryServiceError to handle any error raised by this package.
"""
from pathlib import Path


class BitmapQueryServiceError(Exception):
    """Base class for all errors raised by bitmap_query_service."""


class ConfigurationError(BitmapQueryServiceError):
    """The service environment is missing or has an invalid setting."""


class BitmapNotFoundError(BitmapQueryServiceError):
    """No bitmap file exists for the requested cluster and census version."""

    def __init__(self, path: Path):
        self.path = path
        super().__init__(f"Bitmap file not found: {path.name}")


class BitmapReadError(BitmapQueryServiceError):
    """A bitmap file exists but could not be read or deserialized."""

    def __init__(self, path: Path, reason: str):
        self.path = path
        self.reason = reason
        super().__init__(f"Failed to load bitmap file '{path.name}': {reason}")
