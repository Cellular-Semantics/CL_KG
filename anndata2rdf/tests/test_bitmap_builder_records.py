from rdflib import DCTERMS, RDF, RDFS, Graph, Literal, Namespace

from bitmap_builder import CELL_CLUSTER_CLASS, iter_cluster_bitmap_records

NS = Namespace("http://example.org/")


def _graph_with_cluster(cluster_triples, label="Cluster label"):
    """Build a minimal graph shaped like pandasaurus_cxg's GraphGenerator output."""
    g = Graph()
    cluster, dataset = NS["cluster-1"], NS["dataset-1"]
    g.add((dataset, NS.census_dataset_id, Literal("a12ccb9b-4fbe-457d-8590-ac78053259ef")))
    g.add((dataset, NS.census_version_cached, Literal("2025-11-08")))
    g.add((cluster, RDF.type, CELL_CLUSTER_CLASS))
    g.add((cluster, DCTERMS.source, dataset))
    if label is not None:
        g.add((cluster, RDFS.label, Literal(label)))
    for predicate, value in cluster_triples:
        g.add((cluster, predicate, Literal(value)))
    return g


def _single_record(graph):
    records = list(iter_cluster_bitmap_records(graph, NS))
    assert len(records) == 1
    return records[0]


def test_author_value_uses_exact_column_not_suffix_match():
    # 'broad_celltype' and 'fine_celltype' end with 'celltype'; only the exact
    # column may be used, whatever order the graph yields predicates in.
    graph = _graph_with_cluster(
        [
            (NS.author_label_column, "celltype"),
            (NS.broad_celltype, "T cell"),
            (NS.fine_celltype, "CD4 naive T cell"),
            (NS.celltype, "CD4 T cell"),
        ]
    )
    record = _single_record(graph)
    assert record.author_label_column == "celltype"
    assert record.author_label_value == "CD4 T cell"


def test_cluster_label_is_rdfs_label_not_label_suffixed_column():
    graph = _graph_with_cluster(
        [
            (NS.author_label_column, "celltype"),
            (NS.celltype, "CD4 T cell"),
            (NS.author_cell_label, "should not be used"),
        ],
        label="CD4 T cell (rdfs)",
    )
    assert _single_record(graph).cluster_label == "CD4 T cell (rdfs)"


def test_author_column_with_space_uses_ncname_safe_predicate():
    graph = _graph_with_cluster(
        [(NS.author_label_column, "cell type"), (NS.cell_type, "B cell")]
    )
    record = _single_record(graph)
    assert record.author_label_column == "cell type"
    assert record.author_label_value == "B cell"


def test_dataset_fields_are_read_from_source_node():
    graph = _graph_with_cluster(
        [(NS.author_label_column, "celltype"), (NS.celltype, "CD4 T cell")]
    )
    record = _single_record(graph)
    assert record.node_iri == str(NS["cluster-1"])
    assert record.census_dataset_id == "a12ccb9b-4fbe-457d-8590-ac78053259ef"
    assert record.census_version == "2025-11-08"


def test_author_value_falls_back_to_cluster_label():
    graph = _graph_with_cluster([(NS.author_label_column, "celltype")], label="Fallback")
    assert _single_record(graph).author_label_value == "Fallback"


def test_cluster_without_author_label_column_is_skipped():
    graph = _graph_with_cluster([(NS.celltype, "CD4 T cell")])
    assert list(iter_cluster_bitmap_records(graph, NS)) == []
