from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.models.adapters import online_anomaly, baseline, timeradar, chronos2, timer

router = APIRouter(prefix="/inference", tags=["inference"])

class Telemetry(BaseModel):
    machine_id: str
    values: list[float] = Field(min_length=2)
    horizon: int = Field(default=12, ge=1, le=512)

@router.post("/online")
def online(req: Telemetry):
    return {"machine_id": req.machine_id, **online_anomaly(req.values)}

@router.post("/baseline")
def base(req: Telemetry):
    return {"machine_id": req.machine_id, **baseline(req.values)}

@router.post("/timeradar")
def radar(req: Telemetry):
    return {"machine_id": req.machine_id, **timeradar(req.values)}

@router.post("/chronos2")
def chrono(req: Telemetry):
    return {"machine_id": req.machine_id, **chronos2(req.values, req.horizon)}

@router.post("/timer")
def timer_route(req: Telemetry):
    return {"machine_id": req.machine_id, **timer(req.values, req.horizon)}

@router.post("/{model_name}")
def unknown(model_name: str, req: Telemetry):
    raise HTTPException(status_code=404, detail=f"Unknown model: {model_name}")
