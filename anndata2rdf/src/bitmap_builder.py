import logging
import os
import re
import uuid
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

import cellxgene_census
import pandas as pd
from pandasaurus_cxg.graph_generator.graph_generator_utils import ncname_safe
from pyroaring import BitMap
from rdflib import DCTERMS, RDF, RDFS, Namespace, URIRef

logger = logging.getLogger(__name__)

CELL_CLUSTER_CLASS = URIRef("http://purl.obolibrary.org/obo/PCL_0010001")
# Namespace pandasaurus_cxg's GraphGenerator uses for obs-column and dataset predicates.
DEFAULT_GRAPH_NS = Namespace("http://example.org/")
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
    ns = getattr(gg, "ns", DEFAULT_GRAPH_NS)
    records = list(iter_cluster_bitmap_records(graph, ns))
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


def iter_cluster_bitmap_records(
    graph, ns: Namespace = DEFAULT_GRAPH_NS
) -> Iterable[ClusterBitmapRecord]:
    """Yield one record per cell cluster node that has everything needed for a bitmap.

    Predicates are matched by exact IRI, mirroring how pandasaurus_cxg's GraphGenerator
    writes them: obs columns as ns[ncname_safe(column)], dataset link as dcterms:source,
    cluster label as rdfs:label.
    """
    for cluster_node in graph.subjects(RDF.type, CELL_CLUSTER_CLASS):
        author_label_column = _get_literal(graph, cluster_node, ns.author_label_column)
        if not author_label_column:
            continue

        dataset_node = graph.value(cluster_node, DCTERMS.source)
        if not isinstance(dataset_node, URIRef):
            continue

        census_dataset_id = _get_literal(graph, dataset_node, ns.census_dataset_id)
        if not census_dataset_id:
            continue

        census_version = (
            _get_literal(graph, dataset_node, ns.census_version_cached) or "stable"
        )
        cluster_label = _get_literal(graph, cluster_node, RDFS.label)
        author_label_value = (
            _get_literal(graph, cluster_node, ns[ncname_safe(author_label_column)])
            or cluster_label
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
    bitmap_path = os.path.join(output_dir, bitmap_filename(node_iri, census_version))
    with open(bitmap_path, "wb") as bitmap_file:
        bitmap_file.write(bitmap.serialize())
    return bitmap_path


# The bitmap filename is the contract between this builder (writer) and
# bitmap_query_service (reader). iri_storage_id and bitmap_filename MUST stay
# identical to bitmap_query_service/src/iri_utils.py; both test suites pin the
# same golden values (see BITMAP_FILENAME_GOLDEN_CASES in their tests).
def bitmap_filename(node_iri: str, census_version: str) -> str:
    return f"{iri_storage_id(node_iri)}__{census_version}.bitmap"


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


def _get_literal(graph, subject, predicate: URIRef) -> Optional[str]:
    value = graph.value(subject, predicate)
    return None if value is None else str(value)
