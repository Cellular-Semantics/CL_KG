from dataclasses import dataclass
from typing import Any, Protocol

from graph_query_service.cluster_metadata.builder import build_manifest_response
from graph_query_service.cluster_metadata.models import (
    GraphQueryRequest,
    GraphQueryResponse,
)
from graph_query_service.config import Settings
from graph_query_service.neo4j.query_template import build_query


class GraphQueryExecutionError(RuntimeError):
    pass


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
        driver = self._get_driver()
        try:
            with driver.session(database=self.settings.neo4j_database) as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
        except ValueError:
            raise
        except Exception as exc:
            raise GraphQueryExecutionError("Failed to execute Neo4j graph query.") from exc

    def _get_driver(self):
        if self._driver is None:
            from neo4j import GraphDatabase

            self._driver = GraphDatabase.driver(
                self.settings.neo4j_uri,
                auth=(self.settings.neo4j_user, self.settings.neo4j_password),
            )
        return self._driver
