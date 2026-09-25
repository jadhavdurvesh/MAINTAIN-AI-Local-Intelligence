from fastapi import APIRouter, HTTPException

from app.model_manager import delete_model, job_status, start_download, statuses
from app.models.adapters import _MODEL_CACHE, timer_status, timeradar_status
from app.models.registry import registry

router = APIRouter(prefix="/model-manager", tags=["model management"])


@router.get("")
def list_models():
    registry.initialize()
    return {"models": statuses()}


@router.get("/{model_name}/status")
def model_status(model_name: str):
    normalized = model_name.lower().replace("_", "-")
    if normalized == "timeradar":
        return timeradar_status()
    if normalized == "timer":
        return timer_status()
    if normalized == "chronos-2":
        return {"model": "Chronos-2", "loaded": any(k.startswith("chronos2:") for k in _MODEL_CACHE)}
    if normalized in {"online", "online-anomaly"}:
        return {"model": "Online anomaly", "available": True}
    if normalized in {"baseline", "random-forest-baseline"}:
        return {"model": "Random Forest baseline", "available": True}
    return {"model": model_name, "available": False, "reason": "Unknown model"}


@router.post("/{model_name}/download")
def download_model(model_name: str):
    name = next((n for n in statuses() if n["name"].lower() == model_name.lower()), None)
    if not name:
        raise HTTPException(status_code=404, detail=f"Unknown model: {model_name}")
    try:
        return start_download(name["name"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/jobs/{job_id}")
def download_job(job_id: str):
    return job_status(job_id)


@router.delete("/{model_name}")
def delete_downloaded_model(model_name: str):
    name = next((n["name"] for n in statuses() if n["name"].lower() == model_name.lower()), None)
    if not name:
        raise HTTPException(status_code=404, detail=f"Unknown model: {model_name}")
    try:
        return delete_model(name)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{model_name}/unload")
def unload_model(model_name: str):
    prefix = model_name.lower().replace("-", "")
    removed = [key for key in list(_MODEL_CACHE) if key.lower().replace("-", "").startswith(prefix)]
    for key in removed:
        _MODEL_CACHE.pop(key, None)
    return {"model": model_name, "unloaded": bool(removed), "cache_keys_removed": len(removed)}
