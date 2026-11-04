import logging
from typing import Dict, List

import requests
from utils.sparql_terms import OIO_HAS_DBXREF, InvalidTermError, curie_iri, literal
from utils.translator_utils import (
    ENDPOINT_URL,
    PREFIXES,
    build_sparql_query,
    get_normalized_curies,
    run_query,
    uri_to_curie,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def build_gene_unify_statement(ensembl_curie: str, ncbigene_ids: List[str]) -> str:
    """
    Build one SPARQL update that moves all triples of an Ensembl gene node onto
    its primary NCBIGene node and records the old IDs as hasDbXref literals.

    The first element of ncbigene_ids is the primary node; the rest become
    additional hasDbXref values. Raises InvalidTermError for unusable IDs.
    """
    if not ncbigene_ids:
        raise InvalidTermError(f"No target identifiers for {ensembl_curie!r}")
    ensembl = curie_iri(ensembl_curie)
    primary = curie_iri(ncbigene_ids[0])
    xref_triples = "".join(
        f"\n    {primary} {OIO_HAS_DBXREF} {literal(xref)} ."
        for xref in [ensembl_curie, *ncbigene_ids[1:]]
    )
    return f"""DELETE {{
    {ensembl} ?p ?o .
    ?s2 ?p2 {ensembl} .
}}
INSERT {{
    {primary} ?p ?o .
    ?s2 ?p2 {primary} .{xref_triples}
}}
WHERE {{
    {{ {ensembl} ?p ?o . }}
    UNION
    {{ ?s2 ?p2 {ensembl} . }}
}}"""


def update_gene_nodes_batch(update_dict: Dict[str, List[str]]):
    """
    Combines multiple SPARQL updates into one request.

    Parameters:
      update_dict: A mapping of Ensembl identifiers to lists of NCBIGene identifiers
                          (the first element will be used for the primary update, the rest
                           will be inserted as additional hasDbXref values).
    """
    endpoint_url = f"{ENDPOINT_URL}/statements"
    headers = {"Content-Type": "application/sparql-update"}

    update_statements = []
    for ensembl_id, ncbigene_ids in update_dict.items():
        try:
            update_statements.append(build_gene_unify_statement(ensembl_id, ncbigene_ids))
        except InvalidTermError as e:
            logger.warning(f"Skipping gene node {ensembl_id}: {e}")
    if not update_statements:
        return

    full_query = " ;\n".join(update_statements)

    try:
        response = requests.post(endpoint_url, data=full_query, headers=headers)
        if response.status_code == 204:
            logger.info(f"Successfully updated a batch of {len(update_statements)} updates.")
        else:
            logger.error(
                f"Batch update failed. Status Code: {response.status_code} - {response.text}"
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"Batch update request failed: {e}")


def gene_node_unifier():
    ensembl_terms = run_query(build_sparql_query(PREFIXES['ensembl']))
    ensembl_curie_list = uri_to_curie(ensembl_terms)

    # Process the curies in batches to avoid API limitations
    normalized_curie_dict = {}
    batch_size = 20000
    for start in range(0, len(ensembl_curie_list), batch_size):
        batch = ensembl_curie_list[start : start + batch_size]
        # Node Normalization lists equivalent_identifiers with the preferred ID first;
        # for genes that is the NCBIGene ID when a mapping exists, so [0] becomes the
        # primary node and every other equivalent ID (ENSEMBL, HGNC, OMIM, UMLS, ...)
        # is kept as a hasDbXref literal. Genes with no NCBIGene mapping get their own
        # Ensembl ID as [0], which rewrites the node onto itself. Pinned by
        # tests/test_gene_node_unifier_selection.py.
        batch_result = get_normalized_curies(
            batch, source_field="equivalent_identifiers"
        )
        normalized_curie_dict.update(batch_result)
    # Batch the SPARQL updates into groups and send them together
    update_batch_size = 1000
    update_items = list(normalized_curie_dict.items())
    for i in range(0, len(update_items), update_batch_size):
        batch_dict = dict(update_items[i : i + update_batch_size])
        update_gene_nodes_batch(batch_dict)

    logger.info("Gene node unification process completed.")
    return normalized_curie_dict


if __name__ == "__main__":
    gene_node_unifier()
