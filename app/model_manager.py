from __future__ import annotations

import os
import shutil
import threading
import uuid
import zipfile
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

try:
    from huggingface_hub import snapshot_download
except ImportError:
    snapshot_download = None

ROOT = Path(os.getenv("MAINTAIN_AI_HOME", str(Path.home() / ".maintain-ai"))).expanduser()
MODELS_DIR = ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_SPECS: dict[str, dict[str, Any]] = {
    "TimeRadar": {"kind": "zero_shot_anomaly", "folder": "TimeRadar", "source": "github", "source_label": "mala-lab/TimeRadar", "url": "https://github.com/mala-lab/TimeRadar/archive/refs/heads/main.zip", "description": "Zero-shot time-series anomaly detection; sequence length 100.", "dependencies": "torch, transformers, torch-frft, safetensors"},
    "Chronos-2": {"kind": "forecast", "folder": "Chronos-2", "source": "huggingface", "repo": "amazon/chronos-2", "description": "Chronos-2 time-series forecasting foundation model.", "dependencies": "torch, chronos-forecasting"},
    "Timer": {"kind": "forecast", "folder": "Timer", "source": "huggingface", "repo": "thuml/timer-base-84m", "description": "Timer foundation model for time-series forecasting.", "dependencies": "torch, transformers"},
    "Random Forest baseline": {"kind": "baseline", "folder": "built-in", "source": "built-in", "description": "Lightweight local baseline using scikit-learn/statistics.", "dependencies": "scikit-learn"},
    "Online anomaly": {"kind": "online", "folder": "built-in", "source": "built-in", "description": "Lightweight streaming anomaly statistics adapter.", "dependencies": "numpy"},
}

_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def model_path(name: str) -> Path:
    spec = MODEL_SPECS[name]
    return MODELS_DIR if spec["source"] == "built-in" else MODELS_DIR / spec["folder"]


def _folder_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def _status(name: str) -> dict[str, Any]:
    spec = MODEL_SPECS[name]
    path = model_path(name)
    installed = spec["source"] == "built-in" or path.exists()
    size = _folder_size(path) if installed else 0
    return {"name": name, "kind": spec["kind"], "installed": installed, "available": installed, "path": str(path), "size_bytes": size, "size_mb": round(size / (1024 * 1024), 1), "source": spec["source"], "source_label": spec.get("source_label") or spec.get("repo") or "Built in", "description": spec["description"], "dependencies": spec["dependencies"], "downloadable": spec["source"] != "built-in"}


def statuses() -> list[dict[str, Any]]:
    return [_status(name) for name in MODEL_SPECS]


def job_status(job_id: str) -> dict[str, Any]:
    with _LOCK:
        return dict(_JOBS.get(job_id, {"job_id": job_id, "state": "unknown"}))


def _set_job(job_id: str, **updates: Any) -> None:
    with _LOCK:
        _JOBS.setdefault(job_id, {"job_id": job_id})
        _JOBS[job_id].update(updates)


def _download_hf(target: Path, repo: str) -> None:
    if snapshot_download is None:
        raise RuntimeError("huggingface-hub is not installed in this build.")
    target.mkdir(parents=True, exist_ok=True)
    snapshot_download(repo_id=repo, local_dir=str(target))


def _download_timeradar(target: Path, url: str) -> None:
    temp_zip = ROOT / f"timeradar-{uuid.uuid4().hex}.zip"
    req = Request(url, headers={"User-Agent": "MAINTAIN-AI-Local-Intelligence"})
    try:
        with urlopen(req, timeout=60) as response, open(temp_zip, "wb") as out:
            shutil.copyfileobj(response, out)
        with zipfile.ZipFile(temp_zip) as archive:
            prefix = "TimeRadar-main/TimeRadar/"
            if not any(n.startswith(prefix) for n in archive.namelist()):
                raise RuntimeError("TimeRadar model directory was not found in the official archive.")
            target.mkdir(parents=True, exist_ok=True)
            for member in archive.namelist():
                if member.startswith(prefix) and not member.endswith("/"):
                    relative = member[len(prefix):]
                    destination = target / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(member) as src, open(destination, "wb") as dst:
                        shutil.copyfileobj(src, dst)
    finally:
        temp_zip.unlink(missing_ok=True)


def _run_download(job_id: str, name: str) -> None:
    spec = MODEL_SPECS[name]
    target = model_path(name)
    temp = target.with_name(target.name + ".partial")
    _set_job(job_id, state="running", model=name, message="Downloading…", progress=None)
    try:
        if target.exists() and any(target.iterdir()):
            _set_job(job_id, state="done", model=name, message="Already installed", progress=100)
            return
        shutil.rmtree(temp, ignore_errors=True)
        if spec["source"] == "huggingface":
            _download_hf(temp, spec["repo"])
        elif spec["source"] == "github":
            _download_timeradar(temp, spec["url"])
        else:
            raise RuntimeError("This model does not support downloading.")
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        temp.rename(target)
        _set_job(job_id, state="done", model=name, message="Download complete", progress=100)
    except Exception as exc:
        shutil.rmtree(temp, ignore_errors=True)
        _set_job(job_id, state="error", model=name, message=str(exc), progress=None)


def start_download(name: str) -> dict[str, Any]:
    if name not in MODEL_SPECS:
        raise KeyError(name)
    if MODEL_SPECS[name]["source"] == "built-in":
        return {"state": "done", "message": "Built-in model; nothing to download."}
    job_id = uuid.uuid4().hex
    _set_job(job_id, state="queued", model=name, message="Queued", progress=0)
    threading.Thread(target=_run_download, args=(job_id, name), daemon=True, name=f"download-{name}").start()
    return job_status(job_id)


def delete_model(name: str) -> dict[str, Any]:
    if name not in MODEL_SPECS:
        raise KeyError(name)
    if MODEL_SPECS[name]["source"] == "built-in":
        return {"deleted": False, "message": "Built-in models cannot be deleted."}
    path = model_path(name)
    if path.exists():
        shutil.rmtree(path, ignore_errors=False)
    return {"deleted": True, "model": name, "path": str(path)}
