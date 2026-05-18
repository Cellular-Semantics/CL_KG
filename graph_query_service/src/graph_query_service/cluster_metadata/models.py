from typing import Any

from pydantic import BaseModel, Field


class GraphQueryRequest(BaseModel):
    cell_labels: list[str] = Field(min_length=1)


class ClusterManifestEntry(BaseModel):
    node_iri: str
    cluster_label: str | None = None
    author_label_column: str | None = None
    author_label: Any | None = None
    author_synonym_columns: list[str] = Field(default_factory=list)
    author_synonym_labels: dict[str, Any | None] = Field(default_factory=dict)
    dataset_iri: str | None = None
    dataset_title: str | None = None
    dataset_publication_doi: str | None = None
    census_dataset_id: str | None = None
    bitmap_lookup_key: str


class GraphQueryResponse(BaseModel):
    cluster_count: int
    clusters: dict[str, ClusterManifestEntry]
    query_echo: str
    warnings: list[str] = Field(default_factory=list)
