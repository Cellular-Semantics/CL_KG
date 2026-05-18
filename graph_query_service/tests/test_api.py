from fastapi.testclient import TestClient

from graph_query_service.api.routes import get_graph_service
from graph_query_service.cluster_metadata.models import GraphQueryResponse
from graph_query_service.main import app


class StubGraphService:
    def query_manifest(self, request):
        return GraphQueryResponse(
            cluster_count=1,
            clusters={
                "http://example.org/cluster/1": {
                    "node_iri": "http://example.org/cluster/1",
                    "cluster_label": "Example cluster",
                    "author_label_column": "author_label",
                    "author_label": "Example cluster",
                    "author_synonym_columns": ["synonym_label"],
                    "author_synonym_labels": {"synonym_label": "Example synonym"},
                    "dataset_iri": "http://example.org/dataset/1",
                    "dataset_title": "Dataset 1",
                    "dataset_publication_doi": None,
                    "census_dataset_id": "dataset-1",
                    "bitmap_lookup_key": "http://example.org/cluster/1",
                }
            },
            query_echo=f"cell_labels[{len(request.cell_labels)}]",
            warnings=[],
        )


def test_health_reports_neo4j_settings(monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "bolt://example:7687")
    monkeypatch.setenv("NEO4J_USER", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "secret")
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["neo4j_uri"] == "bolt://example:7687"


def test_query_graph_returns_manifest(monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "bolt://example:7687")
    monkeypatch.setenv("NEO4J_USER", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "secret")
    app.dependency_overrides[get_graph_service] = lambda: StubGraphService()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/graph/query",
                json={
                    "cell_labels": ["Pulmonary neuroendocrine cell"]
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["cluster_count"] == 1
    assert "http://example.org/cluster/1" in payload["clusters"]
