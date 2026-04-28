import logging
import os
from typing import List, Optional
import yaml

from bitmap_builder import build_cluster_bitmaps
from pandasaurus_cxg.enrichment_analysis import AnndataEnrichmentAnalyzer
from pandasaurus_cxg.graph_generator.graph_generator import GraphGenerator

logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_rdf_graph(
    anndata_file_path: str,
    author_cell_type_list: List[str],
    output_rdf_path: str,
    dataset_metadata: Optional[dict] = None,
    bitmap_output_dir: Optional[str] = None,
):
    logger.info(f"Generating RDF graph using {anndata_file_path}...")
    aea = AnndataEnrichmentAnalyzer(anndata_file_path, author_cell_type_list)
    aea.analyzer_manager.co_annotation_report()
    gg = GraphGenerator(aea, dataset_metadata=dataset_metadata)
    gg.generate_rdf_graph(merge=True)
    gg.set_label_adding_priority(author_cell_type_list)
    gg.add_label_to_terms()
    metadata_field_list = [
        "tissue",
        "disease",
        "development_stage",
        "organism",
        "sex",
        "assay",
        "self_reported_ethnicity",
    ]
    metadata_field_list = [
        field_name
        for field_name in metadata_field_list
        if field_name in aea.enricher_manager.anndata.obs.columns
    ]
    gg.add_metadata_nodes(metadata_fields=metadata_field_list)
    if bitmap_output_dir is not None:
        logger.info(f"Building cluster bitmaps in {bitmap_output_dir}...")
        try:
            build_cluster_bitmaps(aea, gg, bitmap_output_dir)
        except Exception:
            logger.exception("Bitmap build failed; continuing with RDF graph save.")
    gg.save_rdf_graph(file_name=output_rdf_path)
    logger.info(f"RDF graph has been generated for {anndata_file_path}...")


if __name__ == "__main__":
    dirname = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(dirname, "config")
    with open(
        os.path.join(
            config_dir,
            "cxg_author_cell_type.yaml",
        ),
        "r",
    ) as file:
        config_data = yaml.safe_load(file)

    for config in config_data:
        generate_rdf_graph(
            os.path.join(dirname, str(config["anndata_file_path"])),
            config["author_cell_type_list"],
            os.path.join(
                "graph",
                (
                    config["output_rdf_path"]
                    if "output_rdf_path" in config
                    else config["anndata_file_path"].split("/")[-1].split(".")[0]
                ),
            ),
            {
                "dataset_id": config.get("dataset_id"),
                "dataset_version_id": config.get("dataset_version_id"),
            },
            os.path.join(dirname, "bitmaps"),
        )
