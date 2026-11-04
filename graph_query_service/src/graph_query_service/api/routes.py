from fastapi import APIRouter, Depends, Request

from graph_query_service.cluster_metadata.models import (
    GraphQueryRequest,
    GraphQueryResponse,
)
from graph_query_service.neo4j.client import GraphQueryServiceProtocol

router = APIRouter()


def get_graph_service(request: Request) -> GraphQueryServiceProtocol:
    return request.app.state.graph_service


@router.get("/health")
def health(request: Request):
    settings = request.app.state.settings
    return {
        "status": "ok",
        "neo4j_uri": settings.neo4j_uri,
        "neo4j_database": settings.neo4j_database,
    }


@router.post("/graph/query", response_model=GraphQueryResponse)
def query_graph(
    request: GraphQueryRequest,
    graph_service: GraphQueryServiceProtocol = Depends(get_graph_service),
):
    # Errors are mapped to HTTP responses by the handlers registered in main.py.
    return graph_service.query_manifest(request)
