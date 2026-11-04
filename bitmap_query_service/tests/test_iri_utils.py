import uuid

import pytest

from src.iri_utils import bitmap_filename, iri_storage_id


def test_iri_storage_id_uses_embedded_uuid():
    iri = "http://example.org/cluster/11111111-1111-1111-1111-111111111111"
    assert iri_storage_id(iri) == "11111111-1111-1111-1111-111111111111"


def test_iri_storage_id_falls_back_to_uuid5():
    iri = "http://example.org/cluster/macrophage"
    assert iri_storage_id(iri) == str(uuid.uuid5(uuid.NAMESPACE_URL, iri))


def test_bitmap_filename_matches_builder_convention():
    iri = "http://example.org/cluster/11111111-1111-1111-1111-111111111111"
    assert (
        bitmap_filename(iri, "stable")
        == "11111111-1111-1111-1111-111111111111__stable.bitmap"
    )


# Keep in sync with anndata2rdf/tests/test_bitmap_filename.py: the builder writes
# these filenames and this service reads them.
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
