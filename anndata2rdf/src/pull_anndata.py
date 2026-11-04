import logging
import os
import re
import time

import requests
from tqdm import tqdm

CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB per chunk
MAX_RETRIES = 3
RETRY_DELAY = 2
# (connect, read) seconds. The read timeout is the max gap between bytes,
# not a cap on total download time, so large files are unaffected.
REQUEST_TIMEOUT = (10, 60)
UUID_PATTERN = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)

logger = logging.getLogger(__name__)


def download_dataset_with_url(
    matrix_id: str, dataset_download_url: str, dataset_dir: str
) -> str | None:
    """
    Download an AnnData dataset from the specified URL in chunks with retry logic.

    This function downloads large AnnData datasets in 8 MB chunks to avoid memory overflow issues.
    If the download is interrupted, the function retries up to a maximum number of attempts.
    Incomplete files are deleted before retrying to ensure data integrity. The file is saved
    in dataset_dir as '<matrix_id>__<download_id>.h5ad'.

    Args:
        matrix_id: A unique identifier for the matrix associated with the dataset.
        dataset_download_url: The URL from which the dataset will be downloaded.
        dataset_dir: Directory to save the downloaded AnnData file in.

    Returns:
        The path to the downloaded file if successful, or None if the
            download failed after the maximum number of retries.
    """
    download_id = get_dataset_id_from_link(dataset_download_url)
    anndata_file_path = os.path.join(dataset_dir, f"{matrix_id}__{download_id}.h5ad")

    # Download the file in chunks
    logger.info(
        f"Downloading dataset from URL '{dataset_download_url}' to '{anndata_file_path}'..."
    )

    retries = 0
    while retries < MAX_RETRIES:
        try:
            with requests.get(
                dataset_download_url, stream=True, timeout=REQUEST_TIMEOUT
            ) as response:
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
        except (requests.RequestException, OSError) as e:
            # Network errors (incl. timeouts) and local write errors are retried.
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


def delete_file(file_name):
    try:
        os.remove(file_name)
        logger.info(f"File '{file_name}' deleted successfully.")
    except OSError as e:
        logger.info(f"Error deleting file '{file_name}': {e}")


def get_dataset_dict(input_source: list[dict]) -> dict[str, dict]:
    cxg_dataset_dict = {}
    for config in input_source:
        matrix_id = get_dataset_id_from_link(config["CxG_link"])
        cxg_dataset_dict[matrix_id] = {
            "author_cell_type_list": config["author_cell_type_list"],
            "download_url": config["download_url"],
            "dataset_id": config.get("dataset_id"),
            "dataset_version_id": config.get("dataset_version_id"),
        }
    return cxg_dataset_dict


def get_dataset_id_from_link(link: str) -> str:
    """Return the dataset UUID embedded in a CxG explorer link or an h5ad download URL.

    Examples:
        https://cellxgene.cziscience.com/e/<uuid>.cxg/  -> <uuid>
        https://datasets.cellxgene.cziscience.com/<uuid>.h5ad -> <uuid>
    """
    match = UUID_PATTERN.search(link or "")
    if match is None:
        raise ValueError(f"No dataset UUID found in link: {link!r}")
    return match.group(0)
