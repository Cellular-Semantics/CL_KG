import os
import logging
import requests
from SPARQLWrapper import SPARQLWrapper, JSON, POST
from typing import Dict, List

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Node Normalization Endpoint
NODE_NORMALIZATION_URL = "https://nodenormalization-sri.renci.org/get_normalized_nodes"
# RDF4J local endpoint configuration
ENDPOINT_URL = os.getenv("ENDPOINT_URL", "http://triplestore:8080/rdf4j-server/repositories/obask")

# RO Relation: Gene produces Protein
RO_0003000 = "http://purl.obolibrary.org/obo/RO_0003000"

UNIPROT_PREFIX = "https://identifiers.org/uniprot/"
ENSEMBL_PREFIX = "http://identifiers.org/ensembl/"
BATCH_SIZE = 1000

UNIPROT_SPARQL_QUERY = f"""
SELECT DISTINCT ?s
WHERE {{ 
  ?s a ?o. FILTER(contains(str(?s), "{UNIPROT_PREFIX}"))
}}
"""
ENSEMBL_SPARQL_QUERY = f"""
SELECT DISTINCT ?s
WHERE {{ 
  ?s a ?o. FILTER(contains(str(?s), "{ENSEMBL_PREFIX}"))
}}
"""

# Configure the SPARQL query endpoint
sparql_query = SPARQLWrapper(ENDPOINT_URL)
sparql_query.setReturnFormat(JSON)
# Configure the SPARQL update endpoint
sparql_update = SPARQLWrapper(ENDPOINT_URL)
sparql_update.setMethod(POST)


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


def get_normalized_curies(curie_list: List[str]) -> Dict[str, List[str]]:
    """Retrieves normalized equivalent CURIEs for given UniProt CURIEs."""
    normalized_curies = {}
    logger.info(curie_list)
    result = requests.post(NODE_NORMALIZATION_URL, json={"curies": curie_list})
    if result.status_code == 200:
        result_json = result.json()
        for curie in curie_list:
            if result_json.get(curie):
                for identifier in result_json.get(curie).get("equivalent_identifiers"):
                    if "ENSEMBL" in identifier["identifier"]:
                        if curie not in normalized_curies:
                            normalized_curies[curie] = [identifier["identifier"]]
                        else:
                            normalized_curies[curie].append(identifier["identifier"])
    else:
        logger.error(f"Error fetching normalized CURIEs. Status code: {result.status_code}")
    return normalized_curies


def insert_triples_in_batch(triples: List[str]):
    """Inserts a batch of RDF triples into the RDF4J repository."""
    endpoint_url = f"{ENDPOINT_URL}/statements"

    headers = {
        "Content-Type": "application/sparql-update"
    }
    if not triples:
        return

    # Use the prefix variables in the SPARQL INSERT query
    insert_query = f"""
    PREFIX RO: <http://purl.obolibrary.org/obo/RO_>
    PREFIX ensembl: <{ENSEMBL_PREFIX}>
    PREFIX uniprot: <{UNIPROT_PREFIX}>

    INSERT DATA {{
        {' '.join(triples)}
    }}
    """

    try:
        response = requests.post(endpoint_url, data=insert_query, headers=headers)

        if response.status_code == 204:
            logger.info(f"Successfully inserted {len(triples)} triples.")
        else:
            logger.error(f"Failed to insert triples. Status Code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")


def uniprot_ensembl_mapper():
    # Retrieve UniProt and Ensembl terms
    uniprot_terms = run_query(UNIPROT_SPARQL_QUERY)
    uniprot_curie_list = uri_to_curie(uniprot_terms)
    ensembl_terms = run_query(ENSEMBL_SPARQL_QUERY)
    ensembl_curie_list = uri_to_curie(ensembl_terms)

    # Get mappings
    normalized_curie_dict = get_normalized_curies(uniprot_curie_list)

    triples_batch = []
    count = 0
    missing_count = 0

    for uni, ensembl_list in normalized_curie_dict.items():
        for ensembl_id in ensembl_list:
            count += 1
            # Convert the CURIE back to a full URI using the prefix variables
            ensembl_uri = ensembl_id.replace("ENSEMBL:", ENSEMBL_PREFIX)
            uniprot_uri = uni.replace("UniProtKB:", UNIPROT_PREFIX)

            if ensembl_id in ensembl_curie_list:
                triple = f"<{ensembl_uri}> <{RO_0003000}> <{uniprot_uri}> ."
                triples_batch.append(triple)

                # Insert in batches
                if len(triples_batch) >= BATCH_SIZE:
                    insert_triples_in_batch(triples_batch)
                    triples_batch = []

            else:
                missing_count += 1

    # Insert remaining triples (if any)
    if triples_batch:
        insert_triples_in_batch(triples_batch)

    logger.info(f"Out of {count} ENSEMBL IDs, {missing_count} are missing")


if __name__ == "__main__":
    uniprot_ensembl_mapper()
