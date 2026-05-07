import uuid

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
