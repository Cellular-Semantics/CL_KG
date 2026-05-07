from pathlib import Path

from fastapi.testclient import TestClient
from pyroaring import BitMap

from src.bitmap_store import resolve_bitmap_path
from src.main import app


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
