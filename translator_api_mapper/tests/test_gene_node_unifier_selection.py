"""Pin how gene_node_unifier picks the primary node from Node Normalization.

These tests document current behaviour (not a design endorsement): the first
equivalent identifier is the primary node and all others become hasDbXref
literals. Response shapes mirror the live API as of 2026-11.
"""
import pytest
import requests
from rdflib import Graph, Literal, URIRef

from gene_node_unifier import gene_node_unifier as gnu
from utils.translator_utils import get_normalized_curies

HAS_DBXREF = URIRef("http://www.geneontology.org/formats/oboInOwl#hasDbXref")
ENSEMBL_IRI = "http://identifiers.org/ensembl/"
NCBIGENE_IRI = "http://identifiers.org/ncbigene/"


def _normalization_response(curie, identifiers):
    class _Response:
        status_code = 200

        @staticmethod
        def raise_for_status():
            pass

        @staticmethod
        def json():
            return {
                curie: {
                    "id": {"identifier": identifiers[0]},
                    "equivalent_identifiers": [{"identifier": i} for i in identifiers],
                }
            }

    return _Response()


@pytest.fixture
def normalize(monkeypatch):
    def _normalize(curie, identifiers):
        monkeypatch.setattr(
            requests, "post", lambda *a, **k: _normalization_response(curie, identifiers)
        )
        return get_normalized_curies([curie], source_field="equivalent_identifiers")

    return _normalize


def _apply(curie, targets):
    """Apply the unify update to a graph holding one Ensembl gene node."""
    gene = URIRef(ENSEMBL_IRI + curie.split(":", 1)[1])
    graph = Graph()
    graph.add((gene, URIRef("http://www.w3.org/2000/01/rdf-schema#label"), Literal("gene")))
    graph.update(gnu.build_gene_unify_statement(curie, targets))
    return graph


def test_ncbigene_first_becomes_primary_and_other_ids_become_xrefs(normalize):
    curie = "ENSEMBL:ENSG00000141510"  # TP53
    ids = ["NCBIGene:7157", curie, "HGNC:11998", "OMIM:191170", "UMLS:C0079419"]
    targets = normalize(curie, ids)[curie]
    assert targets == ids

    graph = _apply(curie, targets)
    primary = URIRef(NCBIGENE_IRI + "7157")
    assert not list(graph.triples((URIRef(ENSEMBL_IRI + "ENSG00000141510"), None, None)))
    assert {str(o) for o in graph.objects(primary, HAS_DBXREF)} == {
        curie,
        "HGNC:11998",
        "OMIM:191170",
        "UMLS:C0079419",
    }


def test_gene_without_ncbigene_mapping_is_rewritten_onto_itself(normalize):
    curie = "ENSEMBL:ENSG00000288588"
    targets = normalize(curie, [curie])[curie]

    graph = _apply(curie, targets)
    gene = URIRef(ENSEMBL_IRI + "ENSG00000288588")
    assert (gene, HAS_DBXREF, Literal(curie)) in graph
    assert all(subject == gene for subject, _, _ in graph)
