import logging
from typing import List

import requests
from utils.translator_utils import (
    BATCH_SIZE,
    ENDPOINT_URL,
    PREFIXES,
    RO_0003000,
    build_sparql_query,
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
    PREFIX ensembl: <{PREFIXES['ensembl']}>
    PREFIX uniprot: <{PREFIXES['uniprot']}>

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


def uniprot_gene_mapper():
    # Retrieve UniProt and Ensembl terms
    uniprot_terms = run_query(build_sparql_query(PREFIXES["uniprot"]))
    uniprot_curie_list = uri_to_curie(uniprot_terms)
    ensembl_terms = run_query(build_sparql_query(PREFIXES["ensembl"]))
    ncbigene_terms = run_query(build_sparql_query(PREFIXES["ncbigene"]))
    gene_curie_list = uri_to_curie(ensembl_terms) + uri_to_curie(ncbigene_terms)

    # Get mappings
    normalized_curie_dict = get_normalized_curies(
        uniprot_curie_list,
        source_field="equivalent_identifiers",
        filter_keywords=["NCBIGene", "ENSEMBL"],
    )

    triples_batch = []
    ensembl_count = 0
    ncbigene_count = 0
    ensembl_missing_count = 0
    ncbigene_missing_count = 0

    for uni, gene_list in normalized_curie_dict.items():
        for gene_curie in gene_list:
            # Convert the CURIE back to a full URI using the prefix variables
            if gene_curie.startswith("ENSEMBL:"):
                gene_uri = gene_curie.replace("ENSEMBL:", PREFIXES["ensembl"])
                ensembl_count += 1
            elif gene_curie.startswith("NCBIGene:"):
                gene_uri = gene_curie.replace("NCBIGene:", PREFIXES["ncbigene"])
                ncbigene_count += 1
            uniprot_uri = uni.replace("UniProtKB:", PREFIXES["uniprot"])

            if gene_curie in gene_curie_list:
                triple = f"<{gene_uri}> <{RO_0003000}> <{uniprot_uri}> ."
                triples_batch.append(triple)

                # Insert in batches
                if len(triples_batch) >= BATCH_SIZE:
                    insert_triples_in_batch(triples_batch)
                    triples_batch = []

            elif "ENSG" in gene_curie:
                ensembl_missing_count += 1
            elif "NCBIGene" in gene_curie:
                ncbigene_missing_count += 1

    # Insert remaining triples (if any)
    if triples_batch:
        insert_triples_in_batch(triples_batch)

    logger.info(f"Out of {ensembl_count} ENSEMBL IDs, {ensembl_missing_count} are missing")
    logger.info(f"Out of {ncbigene_count} NCBIGene IDs, {ncbigene_missing_count} are missing")


if __name__ == "__main__":
    uniprot_gene_mapper()
