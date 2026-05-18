import json
from pathlib import Path

from graph_query_service.cluster_metadata.builder import build_manifest_response
from graph_query_service.cluster_metadata.models import GraphQueryRequest


def load_fixture(name: str) -> dict:
    fixture_path = Path(__file__).parent / "fixtures" / name
    return json.loads(fixture_path.read_text())


def test_build_manifest_response_normalizes_cluster_and_dataset_metadata():
    child = load_fixture("cluster_node_listy.json")
    dataset = {
        "properties": {
            "iri": "https://cellxgene.cziscience.com/e/a12ccb9b-4fbe-457d-8590-ac78053259ef.cxg/",
            "title": ["Single-nucleus RNA-seq of the Adult Human Kidney (Version 1.5)"],
            "publication": ["https://doi.org/10.1038/example"],
            "census_dataset_id": ["a12ccb9b-4fbe-457d-8590-ac78053259ef"],
        }
    }
    request = GraphQueryRequest(cell_labels=["Pulmonary neuroendocrine cell"])

    response = build_manifest_response([{"child": child, "dataset": dataset}], request)

    assert response.cluster_count == 1
    entry = response.clusters["http://example.org/341894c8-9547-5d13-a18d-4b6d220d271d"]
    assert entry.cluster_label == "Pulmonary neuroendocrine cell"
    assert entry.author_label_column == "celltype_level3_fullname"
    assert entry.author_label == "Pulmonary neuroendocrine cell"
    assert entry.author_synonym_columns == [
        "celltype_level1",
        "celltype_level2",
        "celltype_level3",
    ]
    assert entry.author_synonym_labels["celltype_level1"] == "PNEC"
    assert entry.dataset_title == "Single-nucleus RNA-seq of the Adult Human Kidney (Version 1.5)"
    assert entry.dataset_publication_doi == "https://doi.org/10.1038/example"
    assert entry.census_dataset_id == "a12ccb9b-4fbe-457d-8590-ac78053259ef"
    assert response.warnings == []
    assert response.query_echo.startswith("cell_labels[1]: Pulmonary neuroendocrine cell")


def test_build_manifest_response_emits_warnings_for_missing_optional_fields():
    child = load_fixture("cluster_node_missing_fields.json")
    request = GraphQueryRequest(cell_labels=["Missing fields cluster"])

    response = build_manifest_response([{"child": child, "dataset": {"properties": {}}}], request)

    assert response.cluster_count == 1
    entry = response.clusters["http://example.org/missing-fields"]
    assert entry.author_label is None
    assert entry.dataset_publication_doi is None
    assert len(response.warnings) == 3
