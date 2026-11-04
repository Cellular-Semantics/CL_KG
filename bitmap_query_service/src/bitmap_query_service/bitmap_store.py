from pathlib import Path

from pyroaring import BitMap

from bitmap_query_service.errors import BitmapNotFoundError, BitmapReadError
from bitmap_query_service.iri_utils import bitmap_filename

__all__ = ["BitmapNotFoundError", "BitmapReadError", "load_bitmap", "resolve_bitmap_path"]


def resolve_bitmap_path(bitmap_dir: str, node_iri: str, census_version: str) -> Path:
    return Path(bitmap_dir) / bitmap_filename(node_iri, census_version)


def load_bitmap(bitmap_dir: str, node_iri: str, census_version: str) -> BitMap:
    """Load the roaring bitmap stored for a cluster IRI and census version.

    Raises:
        BitmapNotFoundError: no bitmap file exists for this IRI and version.
        BitmapReadError: the file exists but cannot be read or is not a valid bitmap.
    """
    bitmap_path = resolve_bitmap_path(bitmap_dir, node_iri, census_version)
    try:
        data = bitmap_path.read_bytes()
    except (FileNotFoundError, IsADirectoryError) as exc:
        raise BitmapNotFoundError(bitmap_path) from exc
    except OSError as exc:
        raise BitmapReadError(bitmap_path, "file could not be read") from exc

    try:
        return BitMap.deserialize(data)
    except (ValueError, IndexError) as exc:  # pyroaring's errors for corrupt/empty data
        raise BitmapReadError(bitmap_path, "file is not a valid roaring bitmap") from exc
