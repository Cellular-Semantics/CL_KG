import logging
import os
from typing import Dict, List, Optional, Union
import yaml

import cellxgene_census


logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def download_dataset_with_id(dataset_id: str, file_path: Optional[str] = None) -> str:
    """
    Download an AnnData dataset with the specified ID.

    Args:
        dataset_id (str): The ID of the dataset to download.
        file_path (Optional[str], optional): The file path to save the downloaded AnnData. If not provided,
            the dataset_id will be used as the file name. Defaults to None.

    Returns:
        str: The path to the downloaded file
    """
    anndata_file_path = f"{dataset_id}.h5ad" if file_path is None else file_path
    anndata_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        os.path.join("dataset", anndata_file_path),
    )
    if os.path.exists(anndata_file_path):
        logger.info(f"File '{anndata_file_path}' already exists. Skipping download.")
    else:
        logger.info(f"Downloading dataset with ID '{dataset_id} to {anndata_file_path}'...")
        cellxgene_census.download_source_h5ad(dataset_id, to_path=anndata_file_path)
        logger.info(f"Download complete. File saved at '{anndata_file_path}'.")
    return anndata_file_path


def delete_file(file_name):
    try:
        os.remove(file_name)
        logger.info(f"File '{file_name}' deleted successfully.")
    except OSError as e:
        logger.info(f"Error deleting file '{file_name}': {e}")


def get_dataset_dict(input_source: List[Dict]):
    cxg_dataset_dict = {}
    for config in input_source:
        cxg_link = config["CxG_link"]
        cxg_id = get_dataset_id_from_link(cxg_link)
        cxg_dataset_dict.update({cxg_id.split(".")[0]: config["author_cell_type_list"]})
    return cxg_dataset_dict


def get_dataset_id_from_link(cxg_link: str) -> str:
    if cxg_link.endswith("/"):
        return cxg_link.split("/")[-2]
    else:
        return cxg_link.split("/")[-1]


def read_yaml_config(config_file: str):
    with open(config_file, "r") as file:
        return yaml.safe_load(file)


if __name__ == "__main__":
    config_list = read_yaml_config(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            os.path.join("config", "cxg_author_cell_type.yaml"),
        )
    )
    datasets = get_dataset_dict(config_list)
    for dataset in datasets.keys():
        dataset_name = download_dataset_with_id(dataset)
