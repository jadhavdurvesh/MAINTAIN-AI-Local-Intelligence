from fastapi import APIRouter, Query
from app.storage import recent_predictions, recent_telemetry, save_telemetry

router = APIRouter(prefix="/local", tags=["local data"])


@router.post("/telemetry")
def ingest_telemetry(payload: dict):
    machine_id = str(payload.get("machine_id", ""))
    values = payload.get("values", [])
    if not machine_id or not isinstance(values, list) or not values:
        return {"accepted": False, "reason": "machine_id and non-empty values are required"}
    row_id = save_telemetry(machine_id, [float(v) for v in values])
    return {"accepted": True, "id": row_id}


@router.get("/telemetry")
def telemetry(machine_id: str | None = None, limit: int = Query(default=100, ge=1, le=1000)):
    return {"items": recent_telemetry(machine_id, limit)}


@router.get("/predictions")
def predictions(machine_id: str | None = None, limit: int = Query(default=100, ge=1, le=1000)):
    return {"items": recent_predictions(machine_id, limit)}
