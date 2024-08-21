import logging
import os
from typing import List
import yaml

from pandasaurus_cxg.enrichment_analysis import AnndataEnrichmentAnalyzer
from pandasaurus_cxg.graph_generator.graph_generator import GraphGenerator

logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_rdf_graph(
        anndata_file_path: str, author_cell_type_list: List[str], output_rdf_path: str
):
    logger.info(f"Generating RDF graph using {anndata_file_path}...")
    aea = AnndataEnrichmentAnalyzer(anndata_file_path, author_cell_type_list)
    aea.analyzer_manager.co_annotation_report()
    gg = GraphGenerator(aea)
    gg.generate_rdf_graph()
    gg.set_label_adding_priority(author_cell_type_list)
    gg.add_label_to_terms()
    metadata_field_list = ["tissue", 'disease', 'development_stage', 'organism']
    for field_name in metadata_field_list:
        if field_name in aea.enricher_manager.anndata.obs.columns:
            continue
        metadata_field_list.remove(field_name)
    gg.add_metadata_nodes(metadata_fields=metadata_field_list)
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
        )
