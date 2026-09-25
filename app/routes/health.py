from fastapi import APIRouter
from app.models.registry import registry
router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {"status": "ok", "service": "maintain-ai-local-intelligence"}

@router.get("/models")
def models():
    return {"models": registry.status()}
