import os
from dataclasses import dataclass

from bitmap_query_service.errors import ConfigurationError


@dataclass(frozen=True)
class Settings:
    bitmap_dir: str
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"


def get_settings() -> Settings:
    """Read settings from the environment.

    Raises:
        ConfigurationError: BITMAP_DIR is not set or PORT is not an integer.
    """
    bitmap_dir = os.environ.get("BITMAP_DIR", "").strip()
    if not bitmap_dir:
        raise ConfigurationError("BITMAP_DIR environment variable must be set.")

    port_text = os.environ.get("PORT", "8000").strip()
    try:
        port = int(port_text)
    except ValueError as exc:
        raise ConfigurationError(f"PORT must be an integer, got {port_text!r}.") from exc

    return Settings(
        bitmap_dir=bitmap_dir,
        host=os.environ.get("HOST", "0.0.0.0").strip() or "0.0.0.0",
        port=port,
        log_level=os.environ.get("LOG_LEVEL", "INFO").strip() or "INFO",
    )
