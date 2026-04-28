import logging
import os
import re
import uuid
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple
from urllib.parse import unquote

import cellxgene_census
import pandas as pd
from pyroaring import BitMap
from rdflib import RDF, RDFS, URIRef

logger = logging.getLogger(__name__)

CELL_CLUSTER_CLASS = URIRef("http://purl.obolibrary.org/obo/PCL_0010001")
UUID_PATTERN = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


@dataclass(frozen=True)
class ClusterBitmapRecord:
    node_iri: str
    cluster_label: str
    author_label_column: str
    author_label_value: str
    census_dataset_id: str
    census_version: str


def build_cluster_bitmaps(aea, gg, output_dir: str) -> int:
    os.makedirs(output_dir, exist_ok=True)

    obs = _get_anndata_obs(aea)
    if "observation_joinid" not in obs.columns:
        logger.warning("Skipping bitmap build: 'observation_joinid' missing from AnnData obs.")
        return 0

    graph = _get_rdf_graph(gg)
    records = list(iter_cluster_bitmap_records(graph))
    if not records:
        logger.warning("Skipping bitmap build: no cluster bitmap records found in RDF graph.")
        return 0

    joinid_map_cache: Dict[Tuple[str, str], pd.Series] = {}
    bitmap_count = 0

    for record in records:
        if record.author_label_column not in obs.columns:
            logger.warning(
                "Skipping bitmap for %s: obs column '%s' not present.",
                record.node_iri,
                record.author_label_column,
            )
            continue

        cluster_joinids = resolve_cluster_observation_joinids(
            obs,
            record.author_label_column,
            record.author_label_value,
        )
        if cluster_joinids.empty:
            logger.warning(
                "Skipping bitmap for %s: no matching observation_joinid values.",
                record.node_iri,
            )
            continue

        cache_key = (record.census_dataset_id, record.census_version)
        if cache_key not in joinid_map_cache:
            joinid_map_cache[cache_key] = resolve_soma_joinids(
                record.census_dataset_id, record.census_version
            )

        joinid_map = joinid_map_cache[cache_key]
        matched_joinids = cluster_joinids[cluster_joinids.isin(joinid_map.index)]
        if matched_joinids.empty:
            logger.warning(
                "Skipping bitmap for %s: no Census soma_joinid matches found.",
                record.node_iri,
            )
            continue

        soma_joinids = joinid_map.loc[matched_joinids].astype("int64").tolist()
        write_roaring_bitmap(
            record.node_iri,
            record.census_version,
            soma_joinids,
            output_dir,
        )
        bitmap_count += 1
        logger.info(
            "Wrote bitmap for %s (%s cells).",
            record.cluster_label,
            len(soma_joinids),
        )

    logger.info("Bitmap build completed: %s bitmap(s) written.", bitmap_count)
    return bitmap_count


def iter_cluster_bitmap_records(graph) -> Iterable[ClusterBitmapRecord]:
    for cluster_node in graph.subjects(RDF.type, CELL_CLUSTER_CLASS):
        author_label_column = _get_first_literal(graph, cluster_node, "author_label_column")
        if not author_label_column:
            continue

        dataset_node = _get_first_related_node(
            graph, cluster_node, "has_source", "source"
        )
        if dataset_node is None:
            continue

        census_dataset_id = _get_first_literal(graph, dataset_node, "census_dataset_id")
        if not census_dataset_id:
            continue

        census_version = (
            _get_first_literal(graph, dataset_node, "census_version_cached") or "stable"
        )
        cluster_label = _get_cluster_label(graph, cluster_node)
        author_label_value = _get_cluster_author_value(
            graph, cluster_node, author_label_column, cluster_label
        )
        if not cluster_label or not author_label_value:
            continue

        yield ClusterBitmapRecord(
            node_iri=str(cluster_node),
            cluster_label=cluster_label,
            author_label_column=author_label_column,
            author_label_value=author_label_value,
            census_dataset_id=census_dataset_id,
            census_version=census_version,
        )


def resolve_cluster_observation_joinids(
    obs: pd.DataFrame, author_label_column: str, author_label_value: str
) -> pd.Series:
    author_labels = obs[author_label_column].astype(str)
    observation_joinids = obs["observation_joinid"].astype(str)
    mask = author_labels == str(author_label_value)
    return observation_joinids[mask]


def resolve_soma_joinids(census_dataset_id: str, census_version: str) -> pd.Series:
    with cellxgene_census.open_soma(census_version=census_version) as census:
        for organism in ("homo_sapiens", "mus_musculus"):
            obs_df = cellxgene_census.get_obs(
                census,
                organism,
                value_filter=f"dataset_id == '{census_dataset_id}'",
                column_names=["soma_joinid", "observation_joinid"],
            )
            if len(obs_df):
                return obs_df.set_index(
                    obs_df["observation_joinid"].astype(str)
                )["soma_joinid"]

    logger.warning(
        "Dataset %s was not found in Census version %s.",
        census_dataset_id,
        census_version,
    )
    return pd.Series(dtype="int64")


def write_roaring_bitmap(
    node_iri: str, census_version: str, soma_joinids: Iterable[int], output_dir: str
) -> str:
    bitmap = BitMap(soma_joinids)
    bitmap_path = os.path.join(
        output_dir,
        f"{iri_storage_id(node_iri)}__{census_version}.bitmap",
    )
    with open(bitmap_path, "wb") as bitmap_file:
        bitmap_file.write(bitmap.serialize())
    return bitmap_path


def iri_storage_id(node_iri: str) -> str:
    match = UUID_PATTERN.search(node_iri)
    if match:
        return match.group(0).lower()
    return str(uuid.uuid5(uuid.NAMESPACE_URL, node_iri))


def _get_anndata_obs(aea) -> pd.DataFrame:
    anndata = aea.enricher_manager.anndata
    return anndata.obs.copy()


def _get_rdf_graph(gg):
    for attr_name in ("rdf_graph", "graph"):
        graph = getattr(gg, attr_name, None)
        if graph is not None:
            return graph
    raise AttributeError("GraphGenerator does not expose an RDF graph via 'rdf_graph' or 'graph'.")


def _get_cluster_label(graph, cluster_node) -> Optional[str]:
    label = _get_first_literal(graph, cluster_node, "label")
    if label:
        return label
    for obj in graph.objects(cluster_node, RDFS.label):
        return str(obj)
    label_rdfs = _get_first_literal(graph, cluster_node, "label_rdfs")
    if label_rdfs:
        return label_rdfs
    return None


def _get_cluster_author_value(
    graph, cluster_node, author_label_column: str, fallback_label: Optional[str]
) -> Optional[str]:
    author_value = _get_first_literal(graph, cluster_node, author_label_column)
    return author_value or fallback_label


def _get_first_related_node(graph, subject, *predicate_names: str):
    for predicate, obj in graph.predicate_objects(subject):
        if any(
            _predicate_matches(predicate, predicate_name)
            for predicate_name in predicate_names
        ) and isinstance(obj, URIRef):
            return obj
    return None


def _get_first_literal(graph, subject, predicate_name: str) -> Optional[str]:
    for predicate, obj in graph.predicate_objects(subject):
        if _predicate_matches(predicate, predicate_name):
            return str(obj)
    return None


def _predicate_matches(predicate: URIRef, predicate_name: str) -> bool:
    predicate_text = unquote(str(predicate))
    predicate_key = _predicate_key(predicate_text)
    target_key = _predicate_key(predicate_name)
    return predicate_key == target_key or predicate_text.endswith(predicate_name)


def _predicate_key(value: str) -> str:
    return value.rsplit("#", 1)[-1].rsplit("/", 1)[-1]
