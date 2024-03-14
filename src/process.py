import logging
import os

from csv_parser import generate_author_cell_type_config, write_yaml_file
from pull_anndata import download_dataset_with_id, get_dataset_dict, delete_file
from generate_rdf import generate_rdf_graph

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
    dataset_path = download_dataset_with_id(dataset)
    generate_rdf_graph(
        dataset_path,
        author_cell_types,
        os.path.join(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), GRAPH_DIRECTORY),
            dataset,
        ),
    )
    print("Deleted")
