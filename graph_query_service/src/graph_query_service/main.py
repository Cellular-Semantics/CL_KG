import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from graph_query_service.api.routes import router
from graph_query_service.config import get_settings
from graph_query_service.errors import GraphQueryExecutionError
from graph_query_service.neo4j.client import Neo4jGraphQueryService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()  # ConfigurationError here stops startup
    app.state.settings = settings
    app.state.graph_service = Neo4jGraphQueryService(settings)
    yield
    app.state.graph_service.close()


app = FastAPI(title="Graph Query Service", lifespan=lifespan)
app.include_router(router)


@app.exception_handler(GraphQueryExecutionError)
async def graph_query_error_handler(request: Request, exc: GraphQueryExecutionError) -> JSONResponse:
    # The driver/server cause goes to the server log, not the client.
    logger.error("Neo4j graph query failed: %s", exc.__cause__, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": str(exc)})
