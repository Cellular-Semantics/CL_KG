from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from src.bitmap_ops import bitmap_count, serialize_bitmap
from src.bitmap_store import BitmapNotFoundError, BitmapReadError, load_bitmap
from src.config import get_settings
from src.models import BitmapQueryRequest, BitmapQueryResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = get_settings()
    yield


app = FastAPI(title="Bitmap Query Service", lifespan=lifespan)


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

    try:
        bitmap = load_bitmap(
            settings.bitmap_dir,
            request.clusters[0],
            request.census_version,
        )
    except BitmapNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BitmapReadError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return BitmapQueryResponse(
        operation=request.operation,
        cluster_iris=request.clusters,
        census_version=request.census_version,
        count=bitmap_count(bitmap),
        bitmap_base64=serialize_bitmap(bitmap),
    )
