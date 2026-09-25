from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.models.registry import registry
from app.routes.analysis import router as analysis_router
from app.routes.health import router as health_router
from app.routes.inference import router as inference_router
from app.routes.local_data import router as local_data_router
from app.routes.models import router as models_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    registry.initialize()
    yield


app = FastAPI(
    title="MAINTAIN AI Local Intelligence",
    version="0.6.2",
    lifespan=lifespan,
)
app.include_router(health_router, prefix="/api")
app.include_router(inference_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(local_data_router, prefix="/api")
app.include_router(models_router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "MAINTAIN AI Local Intelligence",
        "version": "0.6.2",
        "status": "running",
        "docs": "/docs",
        "api": "/api/health",
    }
