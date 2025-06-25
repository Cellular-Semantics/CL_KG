import logging
from typing import List, Tuple
import requests

from SPARQLWrapper import SPARQLWrapper, JSON

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
      (filtering out the old hasDbXref)
    """
    return f"""
DELETE {{
  <{pr_iri}> ?p ?o .
}}
INSERT {{
  {xref_curie} ?p ?o .
}}
WHERE {{
  <{pr_iri}> ?p ?o .
}}"""


def generate_xref_update_query(pr_iri: str, xref_curie: str) -> str:
    """
    Generates a SPARQL UPDATE that:
      - deletes the old oio:hasDbXref "<xref_curie>"
      - reinserts it as oio:hasDbXref "PR:<suffix>"
    """
    pr_id = pr_iri.rsplit("_", 1)[-1]
    new_xref = f"PR:{pr_id}"
    return f"""
DELETE {{
  {xref_curie} oio:hasDbXref "{xref_curie}" .
}}
INSERT {{
  {xref_curie} oio:hasDbXref "{new_xref}" .
}}
WHERE {{
  {xref_curie} oio:hasDbXref "{xref_curie}" .
}}"""


def update_triples_batch(pairs: List[Tuple[str, str]]):
    """
    Updates triples
    """
    endpoint_url = f"{ENDPOINT_URL}/statements"
    headers = {"Content-Type": "application/sparql-update"}

    prefixes = f"""
    PREFIX PR: <http://purl.obolibrary.org/obo/PR_>
    PREFIX UniProtKB: <https://identifiers.org/uniprot/>
    PREFIX oio: <http://www.geneontology.org/formats/oboInOwl#>
    """
    update_statements = []
    for pr_iri, xref_curie in pairs:
        update_statements.append(generate_rename_query(pr_iri, xref_curie).strip())
        update_statements.append(generate_xref_update_query(pr_iri, xref_curie).strip())

    full_query = prefixes + "\n" + " ;\n".join(update_statements)
    try:
        response = requests.post(endpoint_url, data=full_query, headers=headers)
        if response.status_code == 204:
            logger.info(f"Successfully updated a batch of {len(pairs)} updates.")
        else:
            logger.error(f"Batch update failed. Status Code: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Batch update request failed: {e}")


def pr_uniprot_id_swapper():
    first = extract_tuples(run_query(FIRST_QUERY), key_pr="mpr")
    second = extract_tuples(run_query(SECOND_QUERY))
    all_tuples = first + second

    update_batch_size = 1000
    for i in range(0, len(all_tuples), update_batch_size):
        batch_list = all_tuples[i:i + update_batch_size]
        update_triples_batch(batch_list)


if __name__ == "__main__":
    pr_uniprot_id_swapper()
