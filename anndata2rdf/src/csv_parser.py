import logging
import os
import time
from typing import Optional

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
            # Fetch the latest dataset link
            latest_cxg_dataset = fetch_latest_cxg_dataset_link(link)
            if latest_cxg_dataset:
                _yaml_data.append(
                    {
                        "CxG_link": latest_cxg_dataset,
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


def fetch_latest_cxg_dataset_link(link: str) -> Optional[str]:
    """
    Retrieve the latest CXG dataset download link for the given matrix_id.

    This method extracts the `matrix_id` from the provided URL and sends a GET request
    to the CXG API to fetch dataset versions. It then parses the response to find the
    URL of the latest dataset file with the file type "H5AD".

    Args:
        link (str): The URL containing the matrix_id to be extracted. The matrix_id is
                    used to query the CXG API for dataset versions.

    Returns:
        Optional[str]: The URL of the latest H5AD dataset file if successful, or None if
                       the request fails or the desired dataset is not found.
    """
    retries = 0
    while retries < MAX_RETRIES:
        try:
            matrix_id = link.split("/")[-2].split(".")[0]
            request_url = f"https://api.cellxgene.cziscience.com/curation/v1/datasets/{matrix_id}/versions"

            response = requests.get(request_url)
            response.raise_for_status()

            data = response.json()
            if not isinstance(data, list) or not data:
                logger.error("Unexpected API response format or empty dataset list.")
                return None

            # Find the latest H5AD dataset link
            for asset in data[0].get("assets", []):
                if asset.get("filetype") == "H5AD":
                    return asset.get("url")

            logger.warning(f"No H5AD file found in assets for matrix_id {matrix_id}.")
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
        "cxg_author_cell_type.yaml",
    )
    write_yaml_file(config_yaml, output_file_path)
