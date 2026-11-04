from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pyroaring import BitMap

from bitmap_query_service.bitmap_store import resolve_bitmap_path
from bitmap_query_service.main import app


def test_health_reports_bitmap_dir(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("BITMAP_DIR", str(tmp_path))
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["bitmap_dir"] == str(tmp_path)


def test_lookup_returns_count_and_serialized_bitmap(tmp_path: Path, monkeypatch):
    iri = "http://example.org/cluster/11111111-1111-1111-1111-111111111111"
    bitmap_path = resolve_bitmap_path(str(tmp_path), iri, "stable")
    bitmap_path.write_bytes(BitMap([1, 2, 3, 10]).serialize())

    monkeypatch.setenv("BITMAP_DIR", str(tmp_path))
    with TestClient(app) as client:
        response = client.post(
            "/bitmap/query",
            json={
                "census_version": "stable",
                "operation": "lookup",
                "clusters": [iri],
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["operation"] == "lookup"
    assert payload["cluster_iris"] == [iri]
    assert payload["census_version"] == "stable"
    assert payload["count"] == 4
    assert payload["bitmap_base64"]


def _lookup(client, census_version):
    return client.post(
        "/bitmap/query",
        json={
            "census_version": census_version,
            "operation": "lookup",
            "clusters": ["http://example.org/cluster/11111111-1111-1111-1111-111111111111"],
        },
    )


@pytest.mark.parametrize("census_version", ["2025-11-08", "stable", "latest", "v1.2_rc"])
def test_version_like_census_versions_are_accepted(tmp_path: Path, monkeypatch, census_version):
    monkeypatch.setenv("BITMAP_DIR", str(tmp_path))
    with TestClient(app) as client:
        assert _lookup(client, census_version).status_code == 404  # valid, just no file


@pytest.mark.parametrize(
    "census_version", ["../x", "a/b", "a\\b", "", ".hidden", "2025 11 08", "x" * 65]
)
def test_path_like_census_versions_are_rejected(tmp_path: Path, monkeypatch, census_version):
    monkeypatch.setenv("BITMAP_DIR", str(tmp_path))
    with TestClient(app) as client:
        assert _lookup(client, census_version).status_code == 422
