import logging
import os
from typing import Dict, List

import requests
from SPARQLWrapper import JSON, SPARQLWrapper

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

UNIPROT_PREFIX = "https://identifiers.org/uniprot/"
UNIPROT_SPARQL_QUERY = f"""
SELECT DISTINCT ?s
WHERE {{ 
  ?s a ?o. FILTER(contains(str(?s), "{UNIPROT_PREFIX}"))
}}
"""
ENSEMBL_PREFIX = "http://identifiers.org/ensembl/"
ENSEMBL_SPARQL_QUERY = f"""
SELECT DISTINCT ?s
WHERE {{ 
  ?s a ?o. FILTER(contains(str(?s), "{ENSEMBL_PREFIX}"))
}}
"""
NCBIGene_PREFIX = "http://www.ncbi.nlm.nih.gov/gene/"

# Node Normalization Endpoint
NODE_NORMALIZATION_URL = "https://nodenormalization-sri.renci.org/get_normalized_nodes"
# RDF4J local endpoint configuration
ENDPOINT_URL = os.getenv(
    "ENDPOINT_URL", "http://triplestore:8080/rdf4j-server/repositories/obask"
)
# ENDPOINT_URL = os.getenv(
#     "ENDPOINT_URL", "http://localhost:8081/rdf4j-server/repositories/obask"
# )
# RO Relation: Gene produces Protein
RO_0003000 = "http://purl.obolibrary.org/obo/RO_0003000"

BATCH_SIZE = 1000

# Configure the SPARQL query endpoint
sparql_query = SPARQLWrapper(ENDPOINT_URL)
sparql_query.setReturnFormat(JSON)


def run_query(query: str) -> List[str]:
    """Executes a SPARQL SELECT query and returns the results as a list of URIs."""
    sparql_query.setQuery(query)

    try:
        results = sparql_query.query().convert()
        return [result["s"]["value"] for result in results["results"]["bindings"]]
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return []


def uri_to_curie(uri_list: List[str]) -> List[str]:
    """Converts RDF URIs to CURIEs for use with the Translator API."""
    curie_list = []
    for uri in uri_list:
        if uri.startswith(UNIPROT_PREFIX):
            curie_list.append(f"UniProtKB:{uri.replace(UNIPROT_PREFIX, '')}")
        elif uri.startswith(ENSEMBL_PREFIX):
            curie_list.append(f"ENSEMBL:{uri.replace(ENSEMBL_PREFIX, '')}")
    return curie_list


def get_normalized_curies(
    curie_list: List[str], source_field: str, filter_keyword: str
) -> Dict[str, List[str]]:
    """
    Retrieves normalized CURIEs for a given list of CURIEs using a specified field in the API response.

    Parameters:
      curie_list: List of CURIEs to normalize.
      source_field: The key from the API response to extract identifiers from
                    (e.g., 'id' for a single identifier or 'equivalent_identifiers' for a list).
      filter_keyword: Substring to filter the identifier values (e.g., 'ENSEMBL').

    Returns:
      A dictionary mapping each input CURIE to a list of normalized identifier strings that contain the filter_keyword.
    """
    normalized_curies = {}
    # logger.info(curie_list)
    result = requests.post(NODE_NORMALIZATION_URL, json={"curies": curie_list})
    if result.status_code == 200:
        result_json = result.json()
        for curie in curie_list:
            curie_info = result_json.get(curie)
            if curie_info and source_field in curie_info:
                data = curie_info[source_field]
                # Handle a single identifier (dict) or a list of identifiers.
                if isinstance(data, dict):
                    identifier = data.get("identifier", "")
                    if filter_keyword in identifier:
                        normalized_curies[curie] = [identifier]
                elif isinstance(data, list):
                    for identifier_dict in data:
                        identifier = identifier_dict.get("identifier", "")
                        if filter_keyword in identifier:
                            normalized_curies.setdefault(curie, []).append(identifier)
    else:
        logger.error(
            f"Error fetching normalized CURIEs. Status code: {result.status_code}"
        )
    return normalized_curies
