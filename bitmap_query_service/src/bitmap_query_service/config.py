import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    bitmap_dir: str
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"


def get_settings() -> Settings:
    bitmap_dir = os.environ.get("BITMAP_DIR", "").strip()
    if not bitmap_dir:
        raise RuntimeError("BITMAP_DIR environment variable must be set.")

    port_text = os.environ.get("PORT", "8000").strip()
    return Settings(
        bitmap_dir=bitmap_dir,
        host=os.environ.get("HOST", "0.0.0.0").strip() or "0.0.0.0",
        port=int(port_text),
        log_level=os.environ.get("LOG_LEVEL", "INFO").strip() or "INFO",
    )
