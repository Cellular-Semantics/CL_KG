from typing import Any

from graph_query_service.cluster_metadata.models import (
    ClusterManifestEntry,
    GraphQueryRequest,
    GraphQueryResponse,
)
from graph_query_service.cluster_metadata.normalizer import (
    annotation_value,
    label_value,
    property_map,
    string_value,
    synonym_columns,
)
from graph_query_service.neo4j.query_template import summarize_cell_labels
from graph_query_service.warnings import cluster_warning


def build_manifest_response(
    rows: list[dict[str, Any]], request: GraphQueryRequest
) -> GraphQueryResponse:
    clusters: dict[str, ClusterManifestEntry] = {}
    warnings: list[str] = []

    for row in rows:
        child_props = property_map(row.get("child"))
        dataset_props = property_map(row.get("dataset"))

        node_iri = string_value(child_props, "iri")
        if not node_iri:
            warnings.append(cluster_warning(None, "skipped a cluster result without iri"))
            continue
        if node_iri in clusters:
            continue

        author_label_column = string_value(child_props, "author_label_column")
        author_label = annotation_value(child_props, author_label_column)
        author_synonym_columns = synonym_columns(child_props)
        author_synonym_labels = {
            column: annotation_value(child_props, column) for column in author_synonym_columns
        }

        cluster_label = label_value(child_props)
        dataset_publication_doi = string_value(dataset_props, "publication")
        entry = ClusterManifestEntry(
            node_iri=node_iri,
            cluster_label=cluster_label,
            author_label_column=author_label_column,
            author_label=author_label,
            author_synonym_columns=author_synonym_columns,
            author_synonym_labels=author_synonym_labels,
            dataset_iri=string_value(dataset_props, "iri"),
            dataset_title=string_value(dataset_props, "title"),
            dataset_publication_doi=dataset_publication_doi,
            census_dataset_id=string_value(dataset_props, "census_dataset_id"),
            bitmap_lookup_key=node_iri,
        )
        clusters[node_iri] = entry

        if author_label_column is None:
            warnings.append(cluster_warning(node_iri, "missing author_label_column"))
        elif author_label is None:
            warnings.append(
                cluster_warning(
                    node_iri,
                    f"missing author_label value for column '{author_label_column}'",
                )
            )
        if dataset_publication_doi is None:
            warnings.append(cluster_warning(node_iri, "missing dataset publication DOI"))
        missing_synonyms = [
            column for column, value in author_synonym_labels.items() if value is None
        ]
        for column in missing_synonyms:
            warnings.append(
                cluster_warning(
                    node_iri,
                    f"missing author synonym value for column '{column}'",
                )
            )

    return GraphQueryResponse(
        cluster_count=len(clusters),
        clusters=clusters,
        query_echo=summarize_cell_labels(request.cell_labels),
        warnings=warnings,
    )
