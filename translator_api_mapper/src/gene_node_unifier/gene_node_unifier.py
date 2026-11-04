import logging
from typing import Dict, List

import requests
from utils.sparql_terms import OIO_HAS_DBXREF, InvalidTermError, curie_iri, literal
from utils.reporting import BatchResult, StepReport
from utils.translator_utils import (
    PREFIXES,
    build_sparql_query,
    get_normalized_curies,
    post_sparql_update,
    run_query,
    uri_to_curie,
)

logger = logging.getLogger(__name__)


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


def update_gene_nodes_batch(update_dict: Dict[str, List[str]]) -> BatchResult:
    """
    Combines multiple SPARQL updates into one request.

    Parameters:
      update_dict: A mapping of Ensembl identifiers to lists of NCBIGene identifiers
                          (the first element will be used for the primary update, the rest
                           will be inserted as additional hasDbXref values).
    """
    result = BatchResult()
    update_statements = []
    for ensembl_id, ncbigene_ids in update_dict.items():
        try:
            update_statements.append(build_gene_unify_statement(ensembl_id, ncbigene_ids))
        except InvalidTermError as e:
            logger.warning(f"Skipping gene node {ensembl_id}: {e}")
            result.skipped += 1
    if not update_statements:
        return result

    result.statements = len(update_statements)
    result.error = post_sparql_update(" ;\n".join(update_statements))
    if result.error is None:
        logger.info(f"Successfully updated a batch of {result.statements} updates.")
    return result


def gene_node_unifier() -> StepReport:
    report = StepReport("gene_node_unifier")
    try:
        ensembl_terms = run_query(build_sparql_query(PREFIXES["ensembl"]))
    except Exception as e:
        report.fail(f"querying Ensembl gene nodes failed: {e}")
        return report
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
        try:
            batch_result = get_normalized_curies(
                batch, source_field="equivalent_identifiers"
            )
        except requests.exceptions.RequestException as e:
            report.fail(f"normalizing CURIEs {start}-{start + len(batch) - 1} failed: {e}")
            continue
        normalized_curie_dict.update(batch_result)

    # Batch the SPARQL updates into groups and send them together
    update_batch_size = 1000
    update_items = list(normalized_curie_dict.items())
    for batch_no, i in enumerate(range(0, len(update_items), update_batch_size), 1):
        batch_dict = dict(update_items[i : i + update_batch_size])
        report.add_batch(batch_no, update_gene_nodes_batch(batch_dict))

    logger.info("Gene node unification process completed.")
    return report
