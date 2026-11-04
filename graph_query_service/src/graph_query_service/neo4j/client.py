from dataclasses import dataclass
from typing import Any, Protocol

from neo4j import GraphDatabase
from neo4j.exceptions import DriverError, Neo4jError

from graph_query_service.cluster_metadata.builder import build_manifest_response
from graph_query_service.cluster_metadata.models import (
    GraphQueryRequest,
    GraphQueryResponse,
)
from graph_query_service.config import Settings
from graph_query_service.errors import GraphQueryExecutionError
from graph_query_service.neo4j.query_template import build_query

__all__ = ["GraphQueryExecutionError", "GraphQueryServiceProtocol", "Neo4jGraphQueryService"]


class GraphQueryServiceProtocol(Protocol):
    def query_manifest(self, request: GraphQueryRequest) -> GraphQueryResponse:
        ...


@dataclass
class Neo4jGraphQueryService:
    settings: Settings
    _driver: Any = None

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def query_manifest(self, request: GraphQueryRequest) -> GraphQueryResponse:
        query = build_query()
        rows = self._run_query(query, {"cell_labels": request.cell_labels})
        return build_manifest_response(rows, request)

    def _run_query(self, query: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
        """Run a read query and return its records as dicts.

        Raises:
            GraphQueryExecutionError: the driver could not be created (e.g. malformed
                NEO4J_URI), Neo4j is unreachable, or the server rejected the query.
        """
        try:
            driver = self._get_driver()
            with driver.session(database=self.settings.neo4j_database) as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
        except (DriverError, Neo4jError) as exc:
            raise GraphQueryExecutionError("Failed to execute Neo4j graph query.") from exc

    def _get_driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_user, self.settings.neo4j_password),
            )
        return self._driver
