import logging
from typing import List, Tuple

import requests
from SPARQLWrapper import JSON, SPARQLWrapper
from utils.sparql_terms import OIO_HAS_DBXREF, InvalidTermError, curie_iri, iri, literal
from utils.translator_utils import ENDPOINT_URL

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

UBERGRAPH_ENDPOINT = "https://ubergraph.apps.renci.org/sparql"

FIRST_QUERY = """
PREFIX obo: <http://purl.obolibrary.org/obo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?pr ?mpr (STR(?mxref) AS ?uniprot)
WHERE {
  GRAPH <http://reasoner.renci.org/ontology> {
    ?pr rdfs:isDefinedBy obo:pr.owl .
    ?cell rdfs:isDefinedBy obo:cl.owl .
  }
  GRAPH <http://reasoner.renci.org/nonredundant> {
    ?cell ?r ?pr .
    ?mpr rdfs:subClassOf ?pr .
  }
  GRAPH <http://reasoner.renci.org/redundant> {
    { ?mpr obo:RO_0002160 obo:NCBITaxon_9606 }  # Human
    UNION
    { ?mpr obo:RO_0002160 obo:NCBITaxon_10090 } # Mouse
  }
  GRAPH <http://reasoner.renci.org/ontology> {
    ?mpr <http://www.geneontology.org/formats/oboInOwl#hasDbXref> ?mxref .
    FILTER(STRSTARTS(STR(?mxref), "UniProtKB:"))
  }
}
ORDER BY ?pr ?mpr
"""

SECOND_QUERY = """
PREFIX obo: <http://purl.obolibrary.org/obo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?pr (STR(?xref) AS ?uniprot)
WHERE {
  ?pr rdfs:isDefinedBy obo:pr.owl .
  ?cell rdfs:isDefinedBy obo:cl.owl .
  ?cell ?r ?pr .
  ?pr <http://www.geneontology.org/formats/oboInOwl#hasDbXref> ?xref .
  FILTER(STRSTARTS(STR(?xref), "UniProtKB"))
}
ORDER BY ?pr
"""


def run_query(query: str):
    sparql = SPARQLWrapper(UBERGRAPH_ENDPOINT)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    response = sparql.query().convert()
    return response["results"]["bindings"]


def extract_tuples(bindings, key_pr="pr", key_uniprot="uniprot"):
    """
    From a list of SPARQL bindings, extract (pr, uniprot) pairs.
    """
    return [
        (b[key_pr]["value"], b[key_uniprot]["value"])
        for b in bindings
        if key_pr in b and key_uniprot in b
    ]


def generate_rename_query(pr_iri: str, xref_curie: str) -> str:
    """
    Generates a SPARQL UPDATE that:
      - deletes all triples for <pr_iri>
      - reinserts them under the new UniProtKB IRI
    Raises InvalidTermError for unusable values.
    """
    pr = iri(pr_iri)
    uniprot = curie_iri(xref_curie)
    return f"""DELETE {{
    {pr} ?p ?o .
}}
INSERT {{
    {uniprot} ?p ?o .
}}
WHERE {{
    {pr} ?p ?o .
}}"""


def generate_xref_update_query(pr_iri: str, xref_curie: str) -> str:
    """
    Generates a SPARQL UPDATE that:
      - deletes the old oio:hasDbXref "<xref_curie>"
      - reinserts it as oio:hasDbXref "PR:<suffix>"
    Raises InvalidTermError for unusable values.
    """
    uniprot = curie_iri(xref_curie)
    old_xref = literal(xref_curie)
    new_xref = literal(f"PR:{pr_iri.rsplit('_', 1)[-1]}")
    return f"""DELETE {{
    {uniprot} {OIO_HAS_DBXREF} {old_xref} .
}}
INSERT {{
    {uniprot} {OIO_HAS_DBXREF} {new_xref} .
}}
WHERE {{
    {uniprot} {OIO_HAS_DBXREF} {old_xref} .
}}"""


def update_triples_batch(pairs: List[Tuple[str, str]]):
    """
    Renames PR nodes to their UniProtKB IRIs and rewrites the matching xref.
    Pairs with unusable values are skipped individually.
    """
    endpoint_url = f"{ENDPOINT_URL}/statements"
    headers = {"Content-Type": "application/sparql-update"}

    update_statements = []
    for pr_iri, xref_curie in pairs:
        try:
            statements = [
                generate_rename_query(pr_iri, xref_curie),
                generate_xref_update_query(pr_iri, xref_curie),
            ]
        except InvalidTermError as e:
            logger.warning(f"Skipping {pr_iri} -> {xref_curie}: {e}")
            continue
        update_statements.extend(statements)
    if not update_statements:
        return

    full_query = " ;\n".join(update_statements)
    try:
        response = requests.post(endpoint_url, data=full_query, headers=headers)
        if response.status_code == 204:
            logger.info(f"Successfully updated a batch of {len(update_statements) // 2} updates.")
        else:
            logger.error(
                f"Batch update failed. Status Code: {response.status_code} - {response.text}"
            )
    except requests.exceptions.RequestException as e:
        logger.error(f"Batch update request failed: {e}")


def pr_uniprot_id_swapper():
    first = extract_tuples(run_query(FIRST_QUERY), key_pr="mpr")
    second = extract_tuples(run_query(SECOND_QUERY))
    all_tuples = first + second

    update_batch_size = 1000
    for i in range(0, len(all_tuples), update_batch_size):
        batch_list = all_tuples[i : i + update_batch_size]
        update_triples_batch(batch_list)


if __name__ == "__main__":
    pr_uniprot_id_swapper()
