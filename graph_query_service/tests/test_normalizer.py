import json
from pathlib import Path

from graph_query_service.cluster_metadata.normalizer import (
    annotation_value,
    property_map,
    synonym_columns,
)


def load_fixture(name: str) -> dict:
    fixture_path = Path(__file__).parent / "fixtures" / name
    return json.loads(fixture_path.read_text())


def test_synonym_columns_parses_json_string_list():
    node = load_fixture("cluster_node_listy.json")
    props = property_map(node)

    assert synonym_columns(props) == [
        "celltype_level1",
        "celltype_level2",
        "celltype_level3",
    ]


def test_annotation_value_unwraps_single_item_lists():
    node = load_fixture("cluster_node_listy.json")
    props = property_map(node)

    assert annotation_value(props, "author_label_column") == "celltype_level3_fullname"
    assert annotation_value(props, "celltype_level3_fullname") == "Pulmonary neuroendocrine cell"


def test_synonym_columns_handles_native_scalar_and_list_forms():
    node = load_fixture("cluster_node_scalar.json")
    props = property_map(node)

    assert synonym_columns(props) == ["celltype_level1", "celltype_level2"]
