from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models.adapters import baseline, chronos2, online_anomaly, timer, timeradar
from app.storage import save_prediction

router = APIRouter(prefix="/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    machine_id: str
    values: list[float] = Field(min_length=2)
    horizon: int = Field(default=12, ge=1, le=512)
    include_heavy_models: bool = True


@router.post("")
def analyze(req: AnalysisRequest):
    results = {
        "online": online_anomaly(req.values),
        "baseline": baseline(req.values),
    }
    if req.include_heavy_models:
        results["timeradar"] = timeradar(req.values)
        results["chronos2"] = chronos2(req.values, req.horizon)
        results["timer"] = timer(req.values, req.horizon)

    available = {name: value for name, value in results.items() if value.get("available")}
    scores = []
    online_z = results["online"].get("latest_z_score")
    if online_z is not None:
        scores.append(min(float(online_z) / 6.0, 1.0))
    radar_score = results.get("timeradar", {}).get("latest_anomaly_score")
    if radar_score is not None:
        scores.append(float(radar_score))

    anomaly_index = sum(scores) / len(scores) if scores else None
    result = {
        "machine_id": req.machine_id,
        "models": results,
        "available_models": list(available),
        "anomaly_index": anomaly_index,
        "interpretation": "Model outputs are indicators, not calibrated failure probabilities." if anomaly_index is not None else "No anomaly-capable model produced a score.",
    }
    save_prediction(req.machine_id, "ensemble", result)
    return result
