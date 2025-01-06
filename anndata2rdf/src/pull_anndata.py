import logging
import os
import glob
import time
from typing import Dict, List, Optional

import requests
from tqdm import tqdm
import yaml

CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB per chunk
MAX_RETRIES = 3
RETRY_DELAY = 2

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
        logger.info(
            f"Downloading dataset with ID '{dataset_id} to {anndata_file_path}'..."
        )
        cellxgene_census.download_source_h5ad(dataset_id, to_path=anndata_file_path)
        logger.info(f"Download complete. File saved at '{anndata_file_path}'.")
    return anndata_file_path


def download_dataset_with_url(
    matrix_id: str, dataset_download_url: str, file_path: Optional[str] = None
) -> Optional[str]:
    """
    Download an AnnData dataset from the specified URL in chunks with retry logic.

    This function downloads large AnnData datasets in 8 MB chunks to avoid memory overflow issues.
    If the download is interrupted, the function retries up to a maximum number of attempts.
    Incomplete files are deleted before retrying to ensure data integrity. If a file path is not specified,
    the dataset ID is used as the file name, and the file saved in the 'dataset' directory.
    The function checks if a file with the same prefix already exists in the 'graph' directory. If an older version is
    found, it is deleted and replaced with the new download.

    Args:
        matrix_id: A unique identifier for the matrix associated with the dataset.
        dataset_download_url: The URL from which the dataset will be downloaded.
        file_path: The file path to save the downloaded AnnData.
            If not provided, the dataset ID will be used as the file name. Defaults to None.

    Returns:
        The path to the downloaded file if successful, or None if the
            download failed after the maximum number of retries.
    """
    download_id = get_dataset_id_from_link(dataset_download_url)
    anndata_file_path = (
        f"{matrix_id}__{download_id}.h5ad" if file_path is None else file_path
    )
    anndata_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        os.path.join("dataset", anndata_file_path),
    )
    directory = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "graph",
    )

    # Check if any owl file with the prefix exists
    matching_files = check_file_exists_based_on_prefix(directory, matrix_id)

    if matching_files:
        rdf_graph_path = matching_files[0]
        if download_id in matching_files[0]:
            logger.info(
                f"File with prefix '{matrix_id}' already exists: {matching_files[0]}. Skipping download."
            )
            return rdf_graph_path
        os.remove(rdf_graph_path)
        logger.info(
            f"Dataset with ID {matrix_id} has a new version. "
            f"The previous RDF graph at {rdf_graph_path} has been removed and will be "
            f"replaced with the latest version."
        )

    # Download the file in chunks
    logger.info(
        f"Downloading dataset from URL '{dataset_download_url}' to '{anndata_file_path}'..."
    )

    retries = 0
    while retries < MAX_RETRIES:
        try:
            with requests.get(dataset_download_url, stream=True) as response:
                if response.status_code == 200:
                    total_size = int(response.headers.get("content-length", 0))
                    logger.info(f"Total file size: {total_size / (1024 ** 3):.2f} GB")

                    with tqdm(
                        total=total_size,
                        unit="B",
                        unit_scale=True,
                        unit_divisor=1024,
                        desc="Downloading",
                    ) as progress_bar, open(anndata_file_path, "wb") as file:
                        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                            if chunk:  # filter out keep-alive new chunks
                                file.write(chunk)
                                progress_bar.update(len(chunk))

                    logger.info(
                        f"Download complete. File saved at '{anndata_file_path}'."
                    )
                    return anndata_file_path
                else:
                    logger.error(
                        f"Failed to download the dataset. Status code: {response.status_code}"
                    )
                    break
        except Exception as e:
            logger.error(
                f"Error occurred while downloading the dataset: {e}. Retrying..."
            )
            # Delete the incomplete file if an exception occurs
            if os.path.exists(anndata_file_path):
                logger.warning(f"Deleting incomplete file: {anndata_file_path}")
                os.remove(anndata_file_path)

        retries += 1
        if retries < MAX_RETRIES:
            logger.info(f"Retrying download... Attempt {retries + 1} of {MAX_RETRIES}")
            time.sleep(RETRY_DELAY)
        else:
            logger.error("Max retries reached. Download failed.")
            return None


def check_file_exists_based_on_prefix(directory, prefix):
    # Construct a search pattern for files that start with the prefix
    pattern = os.path.join(directory, f"{prefix}__*.owl")
    return glob.glob(pattern)  # Returns a list of matching files


def get_dataset_id_from_h5ad_link(dataset_url):
    return dataset_url.split("/")[-1].split(".")[0]


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
        matrix_id = get_dataset_id_from_link(cxg_link)
        if cxg_link.endswith(".cxg"):
            cxg_id = matrix_id
            cxg_dataset_dict.update(
                {cxg_id.split(".")[0]: config["author_cell_type_list"]}
            )
        else:
            cxg_dataset_dict.update(
                {
                    matrix_id: {
                        "author_cell_type_list": config["author_cell_type_list"],
                        "download_url": config["download_url"],
                    }
                }
            )
    return cxg_dataset_dict


def get_dataset_id_from_link(cxg_link: str) -> str:
    if cxg_link.endswith("/"):
        return cxg_link.split("/")[-2][:-4]
    else:
        return cxg_link.split("/")[-1][:-5]


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
    for dataset in datasets.items():
        dataset_name = download_dataset_with_url(dataset)
