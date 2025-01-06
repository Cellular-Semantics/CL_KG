import logging
import os
import sys

from csv_parser import generate_author_cell_type_config, write_yaml_file
from pull_anndata import (
    get_dataset_dict,
    download_dataset_with_url,
    get_dataset_id_from_link,
    delete_file,
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
for dataset in datasets.items():
    matrix_id = dataset[0]
    dataset_url = dataset[1].get("download_url")
    author_cell_types = dataset[1].get("author_cell_type_list")
    download_id = get_dataset_id_from_link(dataset_url)

    rdf_output_path = os.path.join(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), GRAPH_DIRECTORY),
        f"{matrix_id}__{download_id}",
    )
    h5ad_output_path = os.path.join(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), DATASET_DIRECTORY),
        f"{matrix_id}",
    )
    logger.info(rdf_output_path)
    if os.path.exists(rdf_output_path + ".owl"):
        logger.info(f"RDF graph '{rdf_output_path}' already exists. Skipping process.")
    else:
        dataset_path = download_dataset_with_url(matrix_id, dataset_url)
        if dataset_path is None:
            logger.error(
                f"Failed to download dataset '{matrix_id}'. Skipping this dataset."
            )
            continue
        generate_rdf_graph(
            dataset_path,
            author_cell_types,
            rdf_output_path,
        )
        delete_file(dataset_path)
