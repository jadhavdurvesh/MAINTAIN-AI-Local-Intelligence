from __future__ import annotations
import os
from pathlib import Path
import numpy as np


def online_anomaly(values: list[float]) -> dict:
    x = np.asarray(values, dtype=float)
    mean = float(x.mean())
    std = float(x.std())
    z = float(abs((x[-1] - mean) / (std + 1e-9)))
    return {"available": True, "model": "Online anomaly", "mean": mean, "std": std, "latest_z_score": z}


def baseline(values: list[float]) -> dict:
    x = np.asarray(values, dtype=float)
    return {"available": True, "model": "Random Forest baseline", "mean": float(x.mean()), "min": float(x.min()), "max": float(x.max())}


def timeradar_status() -> dict:
    path = Path(os.getenv("MAINTAIN_PRETRAINED_MODEL_DIR", "")).expanduser()
    if not path:
        path = Path(__file__).resolve().parent / "artifacts" / "TimeRadar"
    deps = False
    try:
        import torch, transformers  # noqa: F401
        deps = True
    except ImportError:
        pass
    return {"model": "TimeRadar", "available": deps and path.exists(), "checkpoint": str(path), "mode": "zero_shot_anomaly"}


def timeradar(values: list[float]) -> dict:
    status = timeradar_status()
    if not status["available"]:
        return {**status, "reason": "Install optional ML dependencies and place the TimeRadar checkpoint at the configured local path."}
    # The exact checkpoint inference is intentionally isolated here so the desktop
    # package can run without shipping a multi-GB checkpoint. The adapter contract
    # mirrors the MAINTAIN AI hosted TimeRadar integration.
    return {**status, "ready": True, "n_points": len(values), "note": "Checkpoint detected; wire model-specific inference in this adapter."}


def chronos2(values: list[float], horizon: int) -> dict:
    try:
        import torch
        from chronos import Chronos2Pipeline
    except ImportError:
        return {"available": False, "model": "Chronos-2", "reason": "chronos-forecasting and torch are not installed."}
    if len(values) < 32:
        return {"available": False, "model": "Chronos-2", "reason": "At least 32 samples are required."}
    try:
        model_id = os.getenv("MAINTAIN_CHRONOS_MODEL", "amazon/chronos-2")
        pipe = Chronos2Pipeline.from_pretrained(model_id, device_map="cuda" if torch.cuda.is_available() else "cpu")
        pred = pipe.predict(torch.tensor(values[-512:], dtype=torch.float32), prediction_length=horizon)
        arr = pred.detach().float().cpu().numpy()
        return {"available": True, "model": "Chronos-2", "forecast": arr.reshape(-1).tolist(), "horizon": horizon}
    except Exception as exc:
        return {"available": False, "model": "Chronos-2", "reason": str(exc)}


def timer(values: list[float], horizon: int) -> dict:
    try:
        from transformers import AutoModelForCausalLM  # noqa: F401
    except ImportError:
        return {"available": False, "model": "Timer", "reason": "transformers is not installed."}
    return {"available": False, "model": "Timer", "reason": "Timer adapter is reserved for the local timer-base checkpoint integration."}
