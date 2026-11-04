import logging
from typing import List

import requests
from utils.sparql_terms import InvalidTermError, curie_iri, iri
from utils.reporting import BatchResult, StepReport
from utils.translator_utils import (
    BATCH_SIZE,
    PREFIXES,
    RO_0003000,
    build_sparql_query,
    get_normalized_curies,
    post_sparql_update,
    run_query,
    uri_to_curie,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def build_gene_protein_triple(gene_curie: str, uniprot_curie: str) -> str:
    """Return '<gene> RO:0003000 <protein> .' (gene produces protein) with safe IRIs."""
    return f"{curie_iri(gene_curie)} {iri(RO_0003000)} {curie_iri(uniprot_curie)} ."


def insert_triples_in_batch(triples: List[str]) -> BatchResult:
    """Inserts a batch of RDF triples into the RDF4J repository."""
    result = BatchResult(statements=len(triples))
    if not triples:
        return result
    result.error = post_sparql_update(f"""INSERT DATA {{
    {' '.join(triples)}
}}""")
    if result.error is None:
        logger.info(f"Successfully inserted {len(triples)} triples.")
    return result


def uniprot_gene_mapper() -> StepReport:
    report = StepReport("uniprot_gene_mapper")
    try:
        uniprot_terms = run_query(build_sparql_query(PREFIXES["uniprot"]))
        ensembl_terms = run_query(build_sparql_query(PREFIXES["ensembl"]))
        ncbigene_terms = run_query(build_sparql_query(PREFIXES["ncbigene"]))
    except Exception as e:
        report.fail(f"querying protein/gene nodes failed: {e}")
        return report
    uniprot_curie_list = uri_to_curie(uniprot_terms)
    # A set: membership is checked for every gene ID of every protein.
    known_gene_curies = set(uri_to_curie(ensembl_terms) + uri_to_curie(ncbigene_terms))

    # Get mappings
    try:
        normalized_curie_dict = get_normalized_curies(
            uniprot_curie_list,
            source_field="equivalent_identifiers",
            filter_keywords=["NCBIGene", "ENSEMBL"],
        )
    except requests.exceptions.RequestException as e:
        report.fail(f"normalizing UniProtKB CURIEs failed: {e}")
        return report

    triples_batch = []
    batch_no = 0
    ensembl_count = 0
    ncbigene_count = 0
    ensembl_missing_count = 0
    ncbigene_missing_count = 0

    for uni, gene_list in normalized_curie_dict.items():
        for gene_curie in gene_list:
            if gene_curie.startswith("ENSEMBL:"):
                ensembl_count += 1
            elif gene_curie.startswith("NCBIGene:"):
                ncbigene_count += 1

            if gene_curie in known_gene_curies:
                try:
                    triple = build_gene_protein_triple(gene_curie, uni)
                except InvalidTermError as e:
                    logger.warning(f"Skipping {gene_curie} -> {uni}: {e}")
                    report.skipped += 1
                    continue
                triples_batch.append(triple)

                # Insert in batches
                if len(triples_batch) >= BATCH_SIZE:
                    batch_no += 1
                    report.add_batch(batch_no, insert_triples_in_batch(triples_batch))
                    triples_batch = []

            elif gene_curie.startswith("ENSEMBL:"):
                ensembl_missing_count += 1
            elif gene_curie.startswith("NCBIGene:"):
                ncbigene_missing_count += 1

    # Insert remaining triples (if any)
    if triples_batch:
        batch_no += 1
        report.add_batch(batch_no, insert_triples_in_batch(triples_batch))

    logger.info(f"Out of {ensembl_count} ENSEMBL IDs, {ensembl_missing_count} are missing")
    logger.info(f"Out of {ncbigene_count} NCBIGene IDs, {ncbigene_missing_count} are missing")
    return report


if __name__ == "__main__":
    uniprot_gene_mapper().log_summary(logger)
