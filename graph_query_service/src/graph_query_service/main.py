from contextlib import asynccontextmanager

from fastapi import FastAPI

from graph_query_service.api.routes import router
from graph_query_service.config import get_settings
from graph_query_service.neo4j.client import Neo4jGraphQueryService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.graph_service = Neo4jGraphQueryService(settings)
    yield
    app.state.graph_service.close()


app = FastAPI(title="Graph Query Service", lifespan=lifespan)
app.include_router(router)
