"""Failures are reported in a StepReport and never abort a step or the pipeline."""
import logging

import pytest
import requests

from gene_node_unifier import gene_node_unifier as gnu
from pr_uniprot_id_swapper import pr_uniprot_id_swapper as prs
from uniprot_gene_mapper import uniprot_gene_mapper as ugm
from utils import translator_utils
from utils.reporting import BatchResult, StepReport


class _Response:
    def __init__(self, status_code=204, text=""):
        self.status_code = status_code
        self.text = text


def test_post_sparql_update_reports_rejection(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: _Response(400, "MALFORMED QUERY"))
    assert translator_utils.post_sparql_update("INSERT DATA {}") == "HTTP 400: MALFORMED QUERY"


def test_post_sparql_update_reports_timeout(monkeypatch):
    def timeout(*args, **kwargs):
        raise requests.exceptions.ReadTimeout("read timed out")

    monkeypatch.setattr(requests, "post", timeout)
    assert "read timed out" in translator_utils.post_sparql_update("INSERT DATA {}")


def test_post_sparql_update_sends_timeout(monkeypatch):
    seen = {}

    def fake_post(url, **kwargs):
        seen.update(kwargs)
        return _Response()

    monkeypatch.setattr(requests, "post", fake_post)
    assert translator_utils.post_sparql_update("INSERT DATA {}") is None
    assert seen["timeout"] == translator_utils.REQUEST_TIMEOUT


def test_failed_batch_is_reported_and_later_batches_still_run(monkeypatch):
    statuses = iter([500, 204])
    monkeypatch.setattr(requests, "post", lambda *a, **k: _Response(next(statuses), "boom"))
    monkeypatch.setattr(
        prs, "run_query", lambda q: [{"pr": {"value": f"http://purl.obolibrary.org/obo/PR_{i}"},
                                      "mpr": {"value": f"http://purl.obolibrary.org/obo/PR_{i}"},
                                      "uniprot": {"value": f"UniProtKB:P{i:05d}"}}
                                     for i in range(1000)]
    )

    report = prs.pr_uniprot_id_swapper()

    assert report.failures == ["batch 1: HTTP 500: boom"]
    assert report.batches_ok == 1
    assert not report.ok


def test_query_failure_is_reported_not_raised(monkeypatch):
    def broken(query):
        raise OSError("triplestore down")

    monkeypatch.setattr(gnu, "run_query", broken)
    report = gnu.gene_node_unifier()
    assert report.failures == ["querying Ensembl gene nodes failed: triplestore down"]


def test_normalization_failure_is_reported_not_raised(monkeypatch):
    monkeypatch.setattr(ugm, "run_query", lambda q: [])

    def broken(*args, **kwargs):
        raise requests.exceptions.HTTPError("503 Service Unavailable")

    monkeypatch.setattr(ugm, "get_normalized_curies", broken)
    report = ugm.uniprot_gene_mapper()
    assert report.failures == ["normalizing UniProtKB CURIEs failed: 503 Service Unavailable"]


def test_skipped_items_are_counted(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: _Response())
    result = gnu.update_gene_nodes_batch(
        {"ENSEMBL:ENSG00000141510": ["NCBIGene:7157"], "ENSEMBL:ENSG1": ["UMLS:C1"]}
    )
    assert result == BatchResult(statements=1, skipped=1, error=None)


@pytest.mark.parametrize(
    "report, level",
    [
        (StepReport("s", batches_ok=2, statements_ok=10), logging.INFO),
        (StepReport("s", failures=["batch 3: HTTP 500"]), logging.ERROR),
    ],
)
def test_summary_log_level_reflects_failures(caplog, report, level):
    logger = logging.getLogger("test_summary")
    with caplog.at_level(logging.INFO, logger="test_summary"):
        report.log_summary(logger)
    assert caplog.records[0].levelno == level
