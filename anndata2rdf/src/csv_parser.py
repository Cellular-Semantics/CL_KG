import logging
import os
import time
from typing import Dict, Optional

import pandas as pd
import requests
import yaml

MAX_RETRIES = 3
RETRY_DELAY = 2

logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DatasetNotFoundException(Exception):
    """Custom exception for missing dataset versions."""

    pass


def generate_yaml_data(data):
    filtered_df = data[data["Content"].str.strip().str.lower() == "cell types"]
    filtered_df.columns = filtered_df.columns.str.lower()  # Normalize to lowercase
    grouped_data = filtered_df.groupby("cxg link")
    _yaml_data = []

    for link, group_df in grouped_data:
        author_cell_type_list = [
            col.strip()
            for col in group_df["author category cell type field name"].tolist()
        ]
        try:
            # Fetch the latest dataset metadata
            latest_cxg_dataset = fetch_latest_cxg_dataset_metadata(link)
            if latest_cxg_dataset:
                _yaml_data.append(
                    {
                        "CxG_link": link,
                        "download_url": latest_cxg_dataset["download_url"],
                        "dataset_id": latest_cxg_dataset["dataset_id"],
                        "dataset_version_id": latest_cxg_dataset["dataset_version_id"],
                        "author_cell_type_list": author_cell_type_list,
                    }
                )
            else:
                raise DatasetNotFoundException(
                    f"Dataset version could not be found for link: {link}"
                )

        except DatasetNotFoundException as e:
            logging.error(e)
        except Exception as e:
            logging.error(f"Unexpected error while processing link {link}: {e}")

    return _yaml_data


def fetch_latest_cxg_dataset_metadata(link: str) -> Optional[Dict[str, str]]:
    """
    Retrieve the latest CXG dataset metadata for the given dataset identifier.

    This method extracts the dataset identifier from the provided URL and sends a GET request
    to the CXG API to fetch dataset versions. It then parses the response to find the
    latest version entry and returns the stable dataset_id, dataset_version_id,
    and URL of the latest H5AD asset.

    Args:
        link (str): The URL containing the dataset identifier to be extracted. That ID is
                    used to query the CXG API for dataset versions.

    Returns:
        Optional[Dict[str, str]]: Metadata for the latest dataset version if successful,
                                  or None if the request fails or the desired dataset is
                                  not found.
    """
    retries = 0
    while retries < MAX_RETRIES:
        try:
            dataset_lookup_id = link.split("/")[-2].split(".")[0]
            request_url = (
                "https://api.cellxgene.cziscience.com/curation/v1/datasets/"
                f"{dataset_lookup_id}/versions"
            )

            response = requests.get(request_url)
            response.raise_for_status()

            data = response.json()
            if not isinstance(data, list) or not data:
                logger.error("Unexpected API response format or empty dataset list.")
                return None

            latest_version = data[0]
            dataset_id = latest_version.get("dataset_id")
            dataset_version_id = latest_version.get("dataset_version_id")

            # Find the latest H5AD dataset link
            for asset in latest_version.get("assets", []):
                if asset.get("filetype") == "H5AD":
                    return {
                        "download_url": asset.get("url"),
                        "dataset_id": dataset_id,
                        "dataset_version_id": dataset_version_id,
                    }

            logger.warning(
                f"No H5AD file found in assets for dataset identifier {dataset_lookup_id}."
            )
            return None

        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            logger.error(f"Error fetching dataset versions using {link}: {e}")

        retries += 1
        if retries < MAX_RETRIES:
            logger.info(
                f"Retrying dataset version retrieval... Attempt {retries + 1} of"
                f" {MAX_RETRIES}"
            )
            time.sleep(RETRY_DELAY)
        else:
            logger.error("Max retries reached. Dataset version retrieval.")
            return None


def write_yaml_file(yaml_data, file_path):
    with open(file_path, "w") as yaml_file:
        yaml.dump(yaml_data, yaml_file)
        logger.info(f"{file_path} written")


def generate_author_cell_type_config(curated_data_folder: str = "curated_data"):
    all_yaml_data = []
    data_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), curated_data_folder
    )
    for file_name in os.listdir(data_folder):
        file_path = os.path.join(data_folder, file_name)

        if file_name.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_name.endswith(".xlsx") or file_name.endswith(".xls"):
            df = pd.read_excel(file_path)
        else:
            logger.info(f"Skipping file '{file_name}' with unsupported format.")
            continue

        yaml_data = generate_yaml_data(df)
        all_yaml_data.extend(yaml_data)
    return all_yaml_data


if __name__ == "__main__":
    config_yaml = generate_author_cell_type_config()
    output_file_path = os.path.join(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "config"),
        "cxg_author_cell_type_v2.yaml",
    )
    write_yaml_file(config_yaml, output_file_path)
