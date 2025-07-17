import logging
import os
from typing import Dict, List, Optional

import requests
from SPARQLWrapper import JSON, SPARQLWrapper

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PREFIXES = {
    "uniprot": "https://identifiers.org/uniprot/",
    "ensembl": "http://identifiers.org/ensembl/",
    "ncbigene": "http://identifiers.org/ncbigene/",
}
# Node Normalization Endpoint
NODE_NORMALIZATION_URL = "https://nodenormalization-sri.renci.org/get_normalized_nodes"
# RDF4J local endpoint configuration
# ENDPOINT_URL = os.getenv(
#     "ENDPOINT_URL", "http://triplestore:8080/rdf4j-server/repositories/obask"
# )
ENDPOINT_URL = os.getenv(
    "ENDPOINT_URL", "http://localhost:8081/rdf4j-server/repositories/obask"
)
# RO Relation: Gene produces Protein
RO_0003000 = "http://purl.obolibrary.org/obo/RO_0003000"

BATCH_SIZE = 1000

# Configure the SPARQL query endpoint
sparql_query = SPARQLWrapper(ENDPOINT_URL)
sparql_query.setReturnFormat(JSON)


def build_sparql_query(prefix: str) -> str:
    return f"""
    SELECT DISTINCT ?s
    WHERE {{ 
      ?s a ?o. FILTER(contains(str(?s), "{prefix}"))
    }}
    """


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
        if uri.startswith(PREFIXES["uniprot"]):
            curie_list.append(f"UniProtKB:{uri.replace(PREFIXES['uniprot'], '')}")
        elif uri.startswith(PREFIXES["ensembl"]):
            curie_list.append(f"ENSEMBL:{uri.replace(PREFIXES['ensembl'], '')}")
        elif uri.startswith(PREFIXES["ncbigene"]):
            curie_list.append(f"NCBIGene:{uri.replace(PREFIXES['ncbigene'], '')}")
    return curie_list


def get_normalized_curies(
    curie_list: List[str],
    source_field: str,
    filter_keywords: Optional[List[str]] = None,
) -> Dict[str, List[str]]:
    """
    Retrieves normalized CURIEs for a given list of CURIEs using a specified field in the API response,
    and (optionally) filters them by any of the provided keywords.

    Parameters:
      curie_list: List of CURIEs to normalize.
      source_field: The key from the API response to extract identifiers from
                    (e.g., 'id' for a single identifier or 'equivalent_identifiers' for a list).
      filter_keywords: Optional list of substrings to filter the identifier values.
                       For example:
                         ['ENSEMBL', 'HGNC', 'UMLS', 'OMIM', 'UniProtKB', 'PR']
                       If None or empty, no filtering is applied.

    Returns:
      A dictionary mapping each input CURIE to a list of normalized identifier strings
      that contain *any* of the filter_keywords (or all identifiers if no keywords given).
    """
    normalized_curies: Dict[str, List[str]] = {}
    response = requests.post(NODE_NORMALIZATION_URL, json={"curies": curie_list})

    if response.status_code != 200:
        logger.error(
            f"Error fetching normalized CURIEs. Status code: {response.status_code}"
        )
        return normalized_curies

    result_json = response.json()

    def identifier_allowed(identifier: str) -> bool:
        # If no filter list provided, accept everything
        if not filter_keywords:
            return True
        # Otherwise keep if any keyword matches
        return any(kw in identifier for kw in filter_keywords)

    for curie in curie_list:
        info = result_json.get(curie, {})
        if info is None or source_field not in info:
            continue

        data = info[source_field]

        if isinstance(data, dict):
            ident = data.get("identifier", "")
            if identifier_allowed(ident):
                normalized_curies[curie] = [ident]
        elif isinstance(data, list):
            for id_dict in data:
                ident = id_dict.get("identifier", "")
                if identifier_allowed(ident):
                    normalized_curies.setdefault(curie, []).append(ident)

    return normalized_curies
