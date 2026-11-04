import logging

import requests

from uniprot_gene_mapper import uniprot_gene_mapper as ugm

STORE = {
    "https://identifiers.org/uniprot/": ["https://identifiers.org/uniprot/P04637"],
    "http://identifiers.org/ensembl/": [
        "http://identifiers.org/ensembl/ENSG00000141510",
    ],
    "http://identifiers.org/ncbigene/": ["http://identifiers.org/ncbigene/7157"],
}


class _Response:
    status_code = 204
    text = ""


def _run(monkeypatch, caplog, gene_ids):
    monkeypatch.setattr(
        ugm, "run_query", lambda q: next(v for k, v in STORE.items() if f'"{k}"' in q)
    )
    monkeypatch.setattr(ugm, "get_normalized_curies", lambda *a, **k: {"UniProtKB:P04637": gene_ids})
    sent = []
    monkeypatch.setattr(requests, "post", lambda url, data=None, **k: (sent.append(data), _Response())[1])
    with caplog.at_level(logging.INFO, logger=ugm.logger.name):
        report = ugm.uniprot_gene_mapper()
    return report, sent, caplog.text


def test_links_only_genes_present_in_store(monkeypatch, caplog):
    report, sent, _ = _run(
        monkeypatch,
        caplog,
        ["NCBIGene:7157", "ENSEMBL:ENSG00000141510", "NCBIGene:999", "ENSEMBL:ENSMUSG00000059552"],
    )
    assert report.ok and report.statements_ok == 2
    assert "ncbigene/7157" in sent[0] and "ensembl/ENSG00000141510" in sent[0]
    assert "ncbigene/999" not in sent[0] and "ENSMUSG" not in sent[0]


def test_missing_counts_include_mouse_ensembl_ids(monkeypatch, caplog):
    _, _, log = _run(
        monkeypatch,
        caplog,
        ["ENSEMBL:ENSG00000141510", "ENSEMBL:ENSMUSG00000059552", "NCBIGene:999"],
    )
    assert "Out of 2 ENSEMBL IDs, 1 are missing" in log
    assert "Out of 1 NCBIGene IDs, 1 are missing" in log
