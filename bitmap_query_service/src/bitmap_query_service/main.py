import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bitmap_query_service.bitmap_ops import bitmap_count, serialize_bitmap
from bitmap_query_service.bitmap_store import load_bitmap
from bitmap_query_service.config import get_settings
from bitmap_query_service.errors import BitmapNotFoundError, BitmapReadError
from bitmap_query_service.models import BitmapQueryRequest, BitmapQueryResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = get_settings()  # ConfigurationError here stops startup
    yield


app = FastAPI(title="Bitmap Query Service", lifespan=lifespan)


@app.exception_handler(BitmapNotFoundError)
async def bitmap_not_found_handler(request: Request, exc: BitmapNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(BitmapReadError)
async def bitmap_read_error_handler(request: Request, exc: BitmapReadError) -> JSONResponse:
    # Full cause (OS error / corrupt data) goes to the server log, not the client.
    logger.error("Failed to load bitmap %s: %s", exc.path, exc.reason, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Failed to load bitmap file '{exc.path.name}'."},
    )


@app.get("/health")
def health():
    settings = app.state.settings
    return {
        "status": "ok",
        "bitmap_dir": settings.bitmap_dir,
    }


@app.post("/bitmap/query", response_model=BitmapQueryResponse)
def query_bitmap(request: BitmapQueryRequest):
    settings = app.state.settings
    bitmap = load_bitmap(settings.bitmap_dir, request.clusters[0], request.census_version)
    return BitmapQueryResponse(
        operation=request.operation,
        cluster_iris=request.clusters,
        census_version=request.census_version,
        count=bitmap_count(bitmap),
        bitmap_base64=serialize_bitmap(bitmap),
    )
