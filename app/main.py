from fastapi import FastAPI
from app.models.registry import registry
from app.routes.health import router as health_router
from app.routes.inference import router as inference_router
from app.routes.local_data import router as local_data_router

app = FastAPI(title="MAINTAIN AI Local Intelligence", version="0.3.0")
app.include_router(health_router, prefix="/api")
app.include_router(inference_router, prefix="/api")
app.include_router(local_data_router, prefix="/api")


@app.on_event("startup")
def startup() -> None:
    registry.initialize()


@app.get("/")
def root():
    return {"name": "MAINTAIN AI Local Intelligence", "status": "running", "docs": "/docs"}
