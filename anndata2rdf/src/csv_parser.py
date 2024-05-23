import logging
import os

import pandas as pd
import yaml


logging.basicConfig(level=logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_yaml_data(data):
    filtered_df = data[data["Content"].str.lower() == "cell types"]
    grouped_data = filtered_df.groupby("h5ad link")
    _yaml_data = []
    for link, group_df in grouped_data:
        author_cell_type_list = [
            col.strip()
            for col in group_df["Author Category Cell Type Field Name"].tolist()
        ]
        entry = {"CxG_link": link, "author_cell_type_list": author_cell_type_list}
        _yaml_data.append(entry)
    return _yaml_data


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
