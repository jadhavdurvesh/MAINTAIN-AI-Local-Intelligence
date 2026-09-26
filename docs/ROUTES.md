# Route-by-Route Component Guide

This document maps every current FastAPI route module to its responsibility.

## `app/routes/health.py`

### `GET /api/health`

Purpose: minimal liveness response.

### `GET /api/models`

Purpose: expose the registry's model status list.

## `app/routes/inference.py`

Defines the `Telemetry` Pydantic request model:

- `machine_id: str`
- `values: list[float]`, minimum length 2
- `horizon: int`, default 12, range 1–512

Routes:

- `POST /api/inference/online`
- `POST /api/inference/baseline`
- `POST /api/inference/timeradar`
- `POST /api/inference/chronos2`
- `POST /api/inference/timer`

There is also a catch-all model-name route that returns HTTP 404 for unsupported model names.

## `app/routes/analysis.py`

Defines `AnalysisRequest` and orchestrates multiple adapters.

Route:

- `POST /api/analysis`

It persists the final ensemble result.

## `app/routes/local_data.py`

Routes:

- `POST /api/local/telemetry`
- `GET /api/local/telemetry`
- `GET /api/local/predictions`

These are the local persistence interface.

## `app/routes/models.py`

Routes:

- `GET /api/model-manager`
- `GET /api/model-manager/{model_name}/status`
- `POST /api/model-manager/{model_name}/download`
- `GET /api/model-manager/jobs/{job_id}`
- `DELETE /api/model-manager/{model_name}`
- `POST /api/model-manager/{model_name}/unload`

This module is orchestration only; actual model file lifecycle is in `app/model_manager.py`.

## Route design rule

Routes should remain thin. They should validate input, call the owning component, and shape the HTTP response. Model algorithms, download implementation, and database internals belong in their respective modules.
