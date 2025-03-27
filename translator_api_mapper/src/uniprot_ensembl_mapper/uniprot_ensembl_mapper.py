import logging
from typing import List

import requests

from translator_api_mapper.src.utils.translator_utils import (
    BATCH_SIZE,
    ENDPOINT_URL,
    ENSEMBL_PREFIX,
    ENSEMBL_SPARQL_QUERY,
    RO_0003000,
    UNIPROT_PREFIX,
    UNIPROT_SPARQL_QUERY,
    get_normalized_curies,
    run_query,
    uri_to_curie,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def insert_triples_in_batch(triples: List[str]):
    """Inserts a batch of RDF triples into the RDF4J repository."""
    endpoint_url = f"{ENDPOINT_URL}/statements"

    headers = {"Content-Type": "application/sparql-update"}
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
            logger.error(
                f"Failed to insert triples. Status Code: {response.status_code}"
            )

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")


def uniprot_ensembl_mapper():
    # Retrieve UniProt and Ensembl terms
    uniprot_terms = run_query(UNIPROT_SPARQL_QUERY)
    uniprot_curie_list = uri_to_curie(uniprot_terms)
    ensembl_terms = run_query(ENSEMBL_SPARQL_QUERY)
    ensembl_curie_list = uri_to_curie(ensembl_terms)

    # Get mappings
    normalized_curie_dict = get_normalized_curies(
        uniprot_curie_list,
        source_field="equivalent_identifiers",
        filter_keyword="ENSEMBL",
    )

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
