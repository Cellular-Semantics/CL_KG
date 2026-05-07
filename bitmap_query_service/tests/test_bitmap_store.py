from pathlib import Path

import pytest
from pyroaring import BitMap

from src.bitmap_store import BitmapNotFoundError, load_bitmap, resolve_bitmap_path


def test_resolve_bitmap_path_uses_expected_filename(tmp_path: Path):
    iri = "http://example.org/cluster/11111111-1111-1111-1111-111111111111"
    bitmap_path = resolve_bitmap_path(str(tmp_path), iri, "stable")
    assert bitmap_path.name == "11111111-1111-1111-1111-111111111111__stable.bitmap"


def test_load_bitmap_returns_deserialized_bitmap(tmp_path: Path):
    iri = "http://example.org/cluster/11111111-1111-1111-1111-111111111111"
    bitmap_path = resolve_bitmap_path(str(tmp_path), iri, "stable")
    bitmap_path.write_bytes(BitMap([1, 2, 3]).serialize())

    bitmap = load_bitmap(str(tmp_path), iri, "stable")
    assert list(bitmap) == [1, 2, 3]


def test_load_bitmap_raises_not_found_for_missing_file(tmp_path: Path):
    iri = "http://example.org/cluster/11111111-1111-1111-1111-111111111111"
    with pytest.raises(BitmapNotFoundError):
        load_bitmap(str(tmp_path), iri, "stable")
