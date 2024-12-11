import logging
import os
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


def download_dataset_with_url(dataset_url: str, file_path: Optional[str] = None) -> Optional[str]:
    """
    Download an AnnData dataset from the specified URL in chunks with retry logic.

    This function downloads the dataset in 8 MB chunks to handle large files efficiently,
    avoiding memory overflow issues. If a file path is not provided, the dataset ID will
    be used as the file name and stored in the 'dataset' directory. The function includes
    retry logic to handle transient errors such as `IncompleteRead` and network issues,
    ensuring robustness. Incomplete files are deleted before retrying.

    Args:
        dataset_url (str): The URL of the dataset to download.
        file_path (Optional[str], optional): The file path to save the downloaded AnnData.
            If not provided, the dataset ID will be used as the file name. Defaults to None.

    Returns:
        Optional[str]: The path to the downloaded file if successful, or None if the
            download failed after the maximum number of retries.
    """

    anndata_file_path = (
        f"{get_dataset_id_from_h5ad_link(dataset_url)}.h5ad"
        if file_path is None
        else file_path
    )
    anndata_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        os.path.join("dataset", anndata_file_path),
    )

    if os.path.exists(anndata_file_path):
        logger.info(f"File '{anndata_file_path}' already exists. Skipping download.")
        return anndata_file_path

    # Download the file in chunks
    logger.info(
        f"Downloading dataset from URL '{dataset_url}' to '{anndata_file_path}'..."
    )

    retries = 0
    while retries < MAX_RETRIES:
        try:
            with requests.get(dataset_url, stream=True) as response:
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
        if cxg_link.endswith(".cxg"):
            cxg_id = get_dataset_id_from_link(cxg_link)
            cxg_dataset_dict.update(
                {cxg_id.split(".")[0]: config["author_cell_type_list"]}
            )
        else:
            cxg_dataset_dict.update({cxg_link: config["author_cell_type_list"]})
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
            os.path.join("config", "xcxg_author_cell_type.yaml"),
        )
    )
    datasets = get_dataset_dict(config_list)
    for dataset in datasets.keys():
        dataset_name = download_dataset_with_url(dataset)
