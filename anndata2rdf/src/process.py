import logging
import os
import sys

from csv_parser import generate_author_cell_type_config, write_yaml_file
from pull_anndata import (
    get_dataset_dict,
    delete_file,
    download_dataset_with_url,
    get_dataset_id_from_h5ad_link,
)
from generate_rdf import generate_rdf_graph

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)
logger.setLevel(logging.INFO)

CONFIG_DIRECTORY = "config"
CURATED_DATA_DIRECTORY = "curated_data"
DATASET_DIRECTORY = "dataset"
GRAPH_DIRECTORY = "graph"

CXG_AUTHOR_CELL_TYPE_CONFIG = "cxg_author_cell_type.yaml"
GENERATE_RDF_CONFIG = "generate_rdf_config.yaml"

cxg_author_cell_type_yaml = generate_author_cell_type_config()
output_file_path = os.path.join(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_DIRECTORY),
    CXG_AUTHOR_CELL_TYPE_CONFIG,
)
write_yaml_file(cxg_author_cell_type_yaml, output_file_path)
datasets = get_dataset_dict(cxg_author_cell_type_yaml)
for dataset, author_cell_types in datasets.items():
    rdf_output_path = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), GRAPH_DIRECTORY),get_dataset_id_from_h5ad_link(dataset),)
    logger.info(rdf_output_path)
    if os.path.exists(rdf_output_path + ".owl"):
        logger.info(f"RDF graph '{rdf_output_path}' already exists. Skipping process.")
    else:
        dataset_path = download_dataset_with_url(dataset)
        generate_rdf_graph(
            dataset_path,
            author_cell_types,
            rdf_output_path,
        )
        delete_file(dataset_path)
