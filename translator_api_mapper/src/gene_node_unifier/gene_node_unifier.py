import logging

import requests

from utils.translator_utils import (
    ENDPOINT_URL,
    ENSEMBL_PREFIX,
    ENSEMBL_SPARQL_QUERY,
    NCBIGene_PREFIX,
    get_normalized_curies,
    run_query,
    uri_to_curie,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def update_gene_nodes(ensembl_id: str, ncbigene_id: str):
    """
    Updates all triples containing the specified Ensembl identifier by replacing it with the given NCBIGene identifier,
    regardless of whether it appears as the subject or the object. Additionally, an owl:sameAs triple is inserted
    to record the equivalence between the two identifiers.

    Parameters:
      ensembl_id (str): The Ensembl identifier to replace (e.g., "ensembl:ENSG00000163586").
      ncbigene_id (str): The NCBIGene identifier to use (e.g., "NCBIGene:2168").
    """
    endpoint_url = f"{ENDPOINT_URL}/statements"
    headers = {"Content-Type": "application/sparql-update"}

    update_query = f"""
    PREFIX ENSEMBL: <{ENSEMBL_PREFIX}>
    PREFIX NCBIGene: <{NCBIGene_PREFIX}>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>

    DELETE {{
      {ensembl_id} ?p ?o .
      ?s2 ?p2 {ensembl_id} .
    }}
    INSERT {{
      {ncbigene_id} ?p ?o .
      ?s2 ?p2 {ncbigene_id} .
      {ncbigene_id} owl:equivalentClass {ensembl_id} .
    }}
    WHERE {{
      {{
        {ensembl_id} ?p ?o .
      }}
      UNION
      {{
        ?s2 ?p2 {ensembl_id} .
      }}
    }}
    """

    try:
        response = requests.post(endpoint_url, data=update_query, headers=headers)
        if response.status_code == 204:
            logger.info(
                f"Successfully updated identifier {ensembl_id} to {ncbigene_id}."
            )
        else:
            logger.error(
                f"Failed to update identifier. Status Code: {response.status_code}"
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")


def gene_node_unifier():
    ensembl_terms = run_query(ENSEMBL_SPARQL_QUERY)
    ensembl_curie_list = uri_to_curie(ensembl_terms)

    # Process the curies in batches of 20,000 to avoid API limitations.
    normalized_curie_dict = {}
    batch_size = 20000
    for start in range(0, len(ensembl_curie_list), batch_size):
        batch = ensembl_curie_list[start : start + batch_size]
        batch_result = get_normalized_curies(
            batch, source_field="id", filter_keyword="NCBIGene"
        )
        normalized_curie_dict.update(batch_result)

    triples_batch = []

    for ensembl_node_id, nbcigene_node_id in normalized_curie_dict.items():
        update_gene_nodes(ensembl_node_id, nbcigene_node_id[0])

    logger.info(f"")
    # Continue with further processing of normalized_curie_dict
    return normalized_curie_dict


if __name__ == "__main__":
    gene_node_unifier()
