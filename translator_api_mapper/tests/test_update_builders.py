import pytest
import requests
from rdflib.plugins.sparql.parser import parseUpdate

from gene_node_unifier import gene_node_unifier as gnu
from pr_uniprot_id_swapper import pr_uniprot_id_swapper as prs
from uniprot_gene_mapper import uniprot_gene_mapper as ugm
from utils.sparql_terms import InvalidTermError


class _Response:
    status_code = 204
    text = ""


@pytest.fixture
def sent(monkeypatch):
    """Capture SPARQL update bodies instead of POSTing them."""
    bodies = []

    def fake_post(url, data=None, **kwargs):
        bodies.append(data)
        return _Response()

    monkeypatch.setattr(requests, "post", fake_post)
    return bodies


def test_gene_unify_statement_is_valid_sparql_with_full_iris():
    stmt = gnu.build_gene_unify_statement(
        "ENSEMBL:ENSG00000141510", ["NCBIGene:7157", "NCBIGene:999"]
    )
    parseUpdate(stmt)
    assert "<http://identifiers.org/ensembl/ENSG00000141510>" in stmt
    assert "<http://identifiers.org/ncbigene/7157>" in stmt
    assert '"ENSEMBL:ENSG00000141510"' in stmt
    assert '"NCBIGene:999"' in stmt


@pytest.mark.parametrize("targets", [["HGNC:11998"], [], ["NCBIGene:1 2"]])
def test_gene_unify_statement_rejects_unusable_targets(targets):
    with pytest.raises(InvalidTermError):
        gnu.build_gene_unify_statement("ENSEMBL:ENSG00000141510", targets)


def test_gene_batch_skips_bad_item_and_sends_the_rest(sent):
    gnu.update_gene_nodes_batch(
        {
            "ENSEMBL:ENSG00000141510": ["NCBIGene:7157"],
            "ENSEMBL:ENSG00000000003": ["UMLS:C0079419"],  # unknown prefix
        }
    )
    assert len(sent) == 1
    parseUpdate(sent[0])
    assert "ENSG00000141510" in sent[0]
    assert "ENSG00000000003" not in sent[0]


def test_pr_swap_queries_are_valid_sparql():
    pr_iri, xref = "http://purl.obolibrary.org/obo/PR_P04637", "UniProtKB:P04637"
    parseUpdate(prs.generate_rename_query(pr_iri, xref))
    xref_query = prs.generate_xref_update_query(pr_iri, xref)
    parseUpdate(xref_query)
    assert '"UniProtKB:P04637"' in xref_query
    assert '"PR:P04637"' in xref_query


def test_pr_batch_skips_malformed_pair(sent):
    prs.update_triples_batch(
        [
            ("http://purl.obolibrary.org/obo/PR_P04637", "UniProtKB:P04637"),
            ("http://purl.obolibrary.org/obo/PR_bad>iri", "UniProtKB:P00000"),
        ]
    )
    assert len(sent) == 1
    parseUpdate(sent[0])
    assert "P00000" not in sent[0]


def test_gene_protein_triple_and_insert_are_valid_sparql(sent):
    triple = ugm.build_gene_protein_triple("NCBIGene:7157", "UniProtKB:P04637")
    assert triple == (
        "<http://identifiers.org/ncbigene/7157> "
        "<http://purl.obolibrary.org/obo/RO_0003000> "
        "<https://identifiers.org/uniprot/P04637> ."
    )
    ugm.insert_triples_in_batch([triple])
    parseUpdate(sent[0])
