"""Error handling: exception hierarchy, config errors, Neo4j failures, HTTP mapping."""
import logging

import pytest
from fastapi.testclient import TestClient
from neo4j.exceptions import ServiceUnavailable

from graph_query_service.api.routes import get_graph_service
from graph_query_service.cluster_metadata.models import ClusterManifestEntry
from graph_query_service.config import Settings, get_settings
from graph_query_service.errors import (
    ConfigurationError,
    GraphQueryExecutionError,
    GraphQueryServiceError,
)
from graph_query_service.main import app
from graph_query_service.neo4j.client import Neo4jGraphQueryService

ENV = {"NEO4J_URI": "bolt://example:7687", "NEO4J_USER": "neo4j", "NEO4J_PASSWORD": "secret"}


@pytest.fixture
def env(monkeypatch):
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    return monkeypatch


def _settings(uri: str) -> Settings:
    return Settings(neo4j_uri=uri, neo4j_user="neo4j", neo4j_password="secret")


@pytest.mark.parametrize("error", [ConfigurationError, GraphQueryExecutionError])
def test_all_service_errors_share_one_base_class(error):
    assert issubclass(error, GraphQueryServiceError)


@pytest.mark.parametrize("missing", list(ENV))
def test_missing_neo4j_setting_is_configuration_error(env, missing):
    env.delenv(missing)
    with pytest.raises(ConfigurationError, match=missing):
        get_settings()


def test_non_integer_port_is_configuration_error(env):
    env.setenv("PORT", "eighty")
    with pytest.raises(ConfigurationError, match="PORT must be an integer, got 'eighty'"):
        get_settings()


@pytest.mark.parametrize(
    "uri, cause_name",
    [
        ("not a uri", "ConfigurationError"),  # malformed: raised when creating the driver
        ("bolt://127.0.0.1:1", "ServiceUnavailable"),  # nothing listening
    ],
)
def test_driver_failures_become_execution_error_with_cause(uri, cause_name):
    service = Neo4jGraphQueryService(_settings(uri))
    try:
        with pytest.raises(GraphQueryExecutionError) as exc_info:
            service._run_query("RETURN 1", {})
    finally:
        service.close()
    assert type(exc_info.value.__cause__).__name__ == cause_name


class _FailingService:
    def __init__(self, error: Exception):
        self.error = error

    def query_manifest(self, request):
        raise self.error


def _post(env, error: Exception):
    app.dependency_overrides[get_graph_service] = lambda: _FailingService(error)
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            return client.post("/graph/query", json={"cell_labels": ["T cell"]})
    finally:
        app.dependency_overrides.clear()


def test_execution_error_returns_500_and_logs_cause(env, caplog):
    error = GraphQueryExecutionError("Failed to execute Neo4j graph query.")
    error.__cause__ = ServiceUnavailable("connection refused")
    with caplog.at_level(logging.ERROR):
        response = _post(env, error)
    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to execute Neo4j graph query."}
    assert "connection refused" in caplog.text


def test_server_side_value_error_is_500_not_client_400(env):
    # A pydantic ValidationError is a ValueError; raised while building the
    # response it is our bug, not a bad request.
    try:
        ClusterManifestEntry(node_iri=None, bitmap_lookup_key="x")
    except ValueError as exc:
        validation_error = exc
    assert _post(env, validation_error).status_code == 500


def test_invalid_request_body_is_still_422(env):
    with TestClient(app) as client:
        response = client.post("/graph/query", json={"cell_labels": []})
    assert response.status_code == 422
