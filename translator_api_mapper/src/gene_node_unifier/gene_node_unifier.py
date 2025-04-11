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


def update_gene_nodes_batch(update_dict):
    """
    Combines multiple SPARQL updates into one request.
    
    Parameters:
      update_dict (dict): A mapping of Ensembl identifiers to lists of NCBIGene identifiers 
                          (the first element will be used for the update).
    """
    endpoint_url = f"{ENDPOINT_URL}/statements"
    headers = {"Content-Type": "application/sparql-update"}

    # Build the common prefix section
    prefixes = f"""
    PREFIX ENSEMBL: <{ENSEMBL_PREFIX}>
    PREFIX NCBIGene: <{NCBIGene_PREFIX}>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX oio: <http://www.geneontology.org/formats/oboInOwl#>

    DELETE {{
      {ensembl_id} ?p ?o .
      ?s2 ?p2 {ensembl_id} .
    }}
    INSERT {{
      {ncbigene_id} ?p ?o .
      ?s2 ?p2 {ncbigene_id} .
      {ncbigene_id} oio:hasDbXref {ensembl_id} .
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

    update_statements = []
    for ensembl_id, ncbigene_ids in update_dict.items():
        # Use the first NCBIGene id from the list
        ncbigene_id = ncbigene_ids[0]
        update_statement = f"""
        DELETE {{
          {ensembl_id} ?p ?o .
          ?s2 ?p2 {ensembl_id} .
        }}
        INSERT {{
          {ncbigene_id} ?p ?o .
          ?s2 ?p2 {ncbigene_id} .
          {ncbigene_id} oio:hasDbXref "{ensembl_id}" .
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
        update_statements.append(update_statement.strip())

    # Combine all updates with semicolon separators
    full_query = prefixes + "\n" + " ;\n".join(update_statements)
    
    try:
        response = requests.post(endpoint_url, data=full_query, headers=headers)
        if response.status_code == 204:
            logger.info(f"Successfully updated a batch of {len(update_dict)} updates.")
        else:
            logger.error(f"Batch update failed. Status Code: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Batch update request failed: {e}")


def gene_node_unifier():
    ensembl_terms = run_query(ENSEMBL_SPARQL_QUERY)
    ensembl_curie_list = uri_to_curie(ensembl_terms)

    # Process the curies in batches to avoid API limitations
    normalized_curie_dict = {}
    batch_size = 20000
    for start in range(0, len(ensembl_curie_list), batch_size):
        batch = ensembl_curie_list[start : start + batch_size]
        batch_result = get_normalized_curies(batch, source_field="id", filter_keyword="NCBIGene")
        normalized_curie_dict.update(batch_result)

    # Batch the SPARQL updates into groups and send them together
    update_batch_size = 1000  # Adjust this batch size as needed
    update_items = list(normalized_curie_dict.items())
    for i in range(0, len(update_items), update_batch_size):
        batch_dict = dict(update_items[i : i + update_batch_size])
        update_gene_nodes_batch(batch_dict)

    logger.info("Gene node unification process completed.")
    return normalized_curie_dict


if __name__ == "__main__":
    gene_node_unifier()

