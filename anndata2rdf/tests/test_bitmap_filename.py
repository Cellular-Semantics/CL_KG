import pytest

from bitmap_builder import bitmap_filename, write_roaring_bitmap

# Keep in sync with bitmap_query_service/tests/test_iri_utils.py: this builder
# writes these filenames and the service reads them.
BITMAP_FILENAME_GOLDEN_CASES = [
    (
        "http://example.org/a2cb247f-b3f4-5ed7-b42e-58eb50dcd133",
        "2025-11-08",
        "a2cb247f-b3f4-5ed7-b42e-58eb50dcd133__2025-11-08.bitmap",
    ),
    (
        "http://example.org/A2CB247F-B3F4-5ED7-B42E-58EB50DCD133",
        "stable",
        "a2cb247f-b3f4-5ed7-b42e-58eb50dcd133__stable.bitmap",
    ),
    (
        "http://example.org/cluster/macrophage",
        "2025-11-08",
        "83662b52-7cbb-505e-a469-60b40215e379__2025-11-08.bitmap",
    ),
]


@pytest.mark.parametrize("iri, census_version, expected", BITMAP_FILENAME_GOLDEN_CASES)
def test_bitmap_filename_golden_values(iri, census_version, expected):
    assert bitmap_filename(iri, census_version) == expected


def test_write_roaring_bitmap_uses_bitmap_filename(tmp_path):
    iri, version, expected = BITMAP_FILENAME_GOLDEN_CASES[0]
    path = write_roaring_bitmap(iri, version, [1, 2, 3], str(tmp_path))
    assert path == str(tmp_path / expected)
