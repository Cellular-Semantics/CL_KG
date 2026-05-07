from pathlib import Path

from pyroaring import BitMap

from src.iri_utils import bitmap_filename


class BitmapNotFoundError(FileNotFoundError):
    pass


class BitmapReadError(RuntimeError):
    pass


def resolve_bitmap_path(bitmap_dir: str, node_iri: str, census_version: str) -> Path:
    return Path(bitmap_dir) / bitmap_filename(node_iri, census_version)


def load_bitmap(bitmap_dir: str, node_iri: str, census_version: str) -> BitMap:
    bitmap_path = resolve_bitmap_path(bitmap_dir, node_iri, census_version)
    if not bitmap_path.is_file():
        raise BitmapNotFoundError(f"Bitmap file not found: {bitmap_path.name}")

    try:
        bitmap_bytes = bitmap_path.read_bytes()
        return BitMap.deserialize(bitmap_bytes)
    except BitmapNotFoundError:
        raise
    except Exception as exc:
        raise BitmapReadError(
            f"Failed to load bitmap file '{bitmap_path.name}'."
        ) from exc
