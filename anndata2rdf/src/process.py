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

PIPELINE_LOGGERS = (
    "csv_parser",
    "pull_anndata",
    "generate_rdf",
    "bitmap_builder",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
CURATED_DATA_DIR = os.path.join(BASE_DIR, "curated_data")
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
GRAPH_DIR = os.path.join(BASE_DIR, "graph")
BITMAP_DIR = os.path.join(BASE_DIR, "bitmaps")

CXG_AUTHOR_CELL_TYPE_CONFIG = "cxg_author_cell_type.yaml"

def configure_logging() -> None:
    """Configure logging once for the whole pipeline.

    Third-party libraries stay at WARNING; this package's modules log at INFO.
    """
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    for name in (__name__, *PIPELINE_LOGGERS):
        logging.getLogger(name).setLevel(logging.INFO)


def main():
    configure_logging()
    cxg_author_cell_type_yaml = generate_author_cell_type_config(CURATED_DATA_DIR)
    write_yaml_file(
        cxg_author_cell_type_yaml, os.path.join(CONFIG_DIR, CXG_AUTHOR_CELL_TYPE_CONFIG)
    )
    datasets = get_dataset_dict(cxg_author_cell_type_yaml)
    for dataset in datasets.items():
        matrix_id = dataset[0]
        dataset_url = dataset[1].get("download_url")
        author_cell_types = dataset[1].get("author_cell_type_list")
        dataset_metadata = {
            "dataset_id": dataset[1].get("dataset_id"),
            "dataset_version_id": dataset[1].get("dataset_version_id"),
        }
        download_id = get_dataset_id_from_link(dataset_url)

        rdf_output_path = os.path.join(GRAPH_DIR, f"{matrix_id}__{download_id}")
        logger.info(rdf_output_path)
        if os.path.exists(rdf_output_path + ".owl"):
            logger.info(f"RDF graph '{rdf_output_path}' already exists. Skipping process.")
        else:
            dataset_path = download_dataset_with_url(
                matrix_id, dataset_url, DATASET_DIR, GRAPH_DIR
            )
            if dataset_path is None:
                logger.error(
                    f"Failed to download dataset '{matrix_id}'. Skipping this dataset."
                )
                continue
            generate_rdf_graph(
                dataset_path,
                author_cell_types,
                rdf_output_path,
                dataset_metadata,
                BITMAP_DIR,
            )
            delete_file(dataset_path)


if __name__ == "__main__":
    main()
