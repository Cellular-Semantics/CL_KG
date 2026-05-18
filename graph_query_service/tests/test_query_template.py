from graph_query_service.neo4j.query_template import build_query, summarize_cell_labels


def test_build_query_uses_parameterized_cell_labels():
    query = build_query()

    assert "WITH $cell_labels AS cell_labels" in query
    assert "MATCH (n:Cell)-[:composed_primarily_of]-(child:Cell_cluster)" in query
    assert "OPTIONAL MATCH (child)-[:has_source]->(dataset:Dataset)" in query


def test_summarize_cell_labels_includes_count():
    summary = summarize_cell_labels(["a", "b"])

    assert summary == "cell_labels[2]: a, b"
