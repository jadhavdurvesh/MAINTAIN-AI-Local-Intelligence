from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np

_MODEL_CACHE: dict[str, Any] = {}


def _default_model_dir(name: str) -> Path:
    return Path.home() / ".maintain-ai" / "models" / name


def _configured_path(env_name: str, name: str) -> Path:
    raw = os.getenv(env_name)
    return Path(raw).expanduser() if raw else _default_model_dir(name)


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
    path = _configured_path("MAINTAIN_TIMERADAR_MODEL", "TimeRadar")
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
        deps = True
    except ImportError:
        deps = False
    return {"model": "TimeRadar", "available": deps and path.exists(), "dependencies_ready": deps, "checkpoint": str(path), "mode": "zero_shot_anomaly", "sequence_length": 100}


def _load_timeradar() -> Any:
    key = "timeradar"
    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]
    import torch
    from transformers import AutoModel
    path = _configured_path("MAINTAIN_TIMERADAR_MODEL", "TimeRadar")
    if not path.exists():
        raise FileNotFoundError(f"TimeRadar checkpoint not found: {path}")
    model = AutoModel.from_pretrained(str(path), trust_remote_code=True)
    model.eval()
    if torch.cuda.is_available():
        model = model.to("cuda")
    _MODEL_CACHE[key] = model
    return model


def timeradar(values: list[float]) -> dict:
    status = timeradar_status()
    if not status["available"]:
        return {**status, "reason": "Install torch/transformers and download TimeRadar from Model Manager."}
    if len(values) < 2:
        return {**status, "reason": "At least 2 samples are required."}
    try:
        import torch
        x = np.asarray(values, dtype=np.float32)
        original_length = len(x)
        window = x[-100:] if len(x) >= 100 else np.pad(x, (100 - len(x), 0), mode="edge")
        tensor = torch.from_numpy(window).reshape(1, 100, 1)
        model = _load_timeradar()
        device = next(model.parameters()).device
        with torch.no_grad():
            outputs = model(input_values=tensor.to(device))
        scores = outputs.anomaly_scores.detach().float().cpu().numpy().reshape(-1)
        return {**status, "ready": True, "n_points": original_length, "window_length": 100, "latest_anomaly_score": float(scores[-1]), "anomaly_scores": scores.tolist()}
    except Exception as exc:
        return {**status, "available": False, "reason": f"TimeRadar inference failed: {exc}"}


def chronos2(values: list[float], horizon: int) -> dict:
    try:
        import torch
        from chronos import Chronos2Pipeline
    except ImportError:
        return {"available": False, "model": "Chronos-2", "reason": "chronos-forecasting and torch are not installed."}
    if len(values) < 32:
        return {"available": False, "model": "Chronos-2", "reason": "At least 32 samples are required."}
    try:
        local_path = _configured_path("MAINTAIN_CHRONOS_MODEL_PATH", "Chronos-2")
        model_id = str(local_path) if local_path.exists() else os.getenv("MAINTAIN_CHRONOS_MODEL", "amazon/chronos-2")
        cache_key = f"chronos2:{model_id}:{'cuda' if torch.cuda.is_available() else 'cpu'}"
        if cache_key not in _MODEL_CACHE:
            _MODEL_CACHE[cache_key] = Chronos2Pipeline.from_pretrained(model_id, device_map="cuda" if torch.cuda.is_available() else "cpu")
        pred = _MODEL_CACHE[cache_key].predict(torch.tensor(values[-512:], dtype=torch.float32), prediction_length=horizon)
        arr = pred.detach().float().cpu().numpy()
        return {"available": True, "model": "Chronos-2", "forecast": arr.reshape(-1).tolist(), "horizon": horizon}
    except Exception as exc:
        return {"available": False, "model": "Chronos-2", "reason": str(exc)}


def timer_status() -> dict:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
        deps = True
    except ImportError:
        deps = False
    local_path = _configured_path("MAINTAIN_TIMER_MODEL_PATH", "Timer")
    model_id = str(local_path) if local_path.exists() else os.getenv("MAINTAIN_TIMER_MODEL", "thuml/timer-base-84m")
    return {"model": "Timer", "available": deps, "dependencies_ready": deps, "model_id": model_id, "local_checkpoint": str(local_path) if local_path.exists() else None, "context_limit": 2880, "mode": "zero_shot_forecast"}


def _load_timer() -> Any:
    import torch
    from transformers import AutoModelForCausalLM
    local_path = _configured_path("MAINTAIN_TIMER_MODEL_PATH", "Timer")
    model_id = str(local_path) if local_path.exists() else os.getenv("MAINTAIN_TIMER_MODEL", "thuml/timer-base-84m")
    key = f"timer:{model_id}:{'cuda' if torch.cuda.is_available() else 'cpu'}"
    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]
    model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True)
    model.eval()
    if torch.cuda.is_available():
        model = model.to("cuda")
    _MODEL_CACHE[key] = model
    return model


def timer(values: list[float], horizon: int) -> dict:
    status = timer_status()
    if not status["available"]:
        return {**status, "reason": "Install torch and transformers to enable Timer inference."}
    if len(values) < 16:
        return {**status, "available": False, "reason": "At least 16 samples are required."}
    try:
        import torch
        x = torch.tensor(values[-2880:], dtype=torch.float32).reshape(1, -1)
        mean = x.mean(dim=-1, keepdim=True)
        std = x.std(dim=-1, keepdim=True).clamp_min(1e-6)
        normed = (x - mean) / std
        model = _load_timer()
        device = next(model.parameters()).device
        with torch.no_grad():
            generated = model.generate(normed.to(device), max_new_tokens=horizon)
        forecast = generated[:, -horizon:].detach().float().cpu()
        forecast = (forecast * std.cpu()) + mean.cpu()
        return {**status, "ready": True, "horizon": horizon, "context_length": int(x.shape[-1]), "forecast": forecast.reshape(-1).tolist()}
    except Exception as exc:
        return {**status, "available": False, "reason": f"Timer inference failed: {exc}"}
