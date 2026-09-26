# API Reference

Base URL when the local engine is running:

```text
http://127.0.0.1:8000/api
```

Interactive FastAPI documentation is exposed at `/docs`.

## Health

### `GET /api/health`

Returns:

```json
{"status":"ok","service":"maintain-ai-local-intelligence"}
```

### `GET /api/models`

Returns the current registry model statuses.

## Inference

All direct inference routes use the same request shape:

```json
{
  "machine_id": "M-001",
  "values": [1, 2, 3, 4],
  "horizon": 12
}
```

`machine_id` identifies the asset in the caller's context. `values` is a numeric time-series. `horizon` is used by forecast models and defaults to 12, with a maximum of 512.

### `POST /api/inference/online`

Runs the lightweight Online anomaly adapter.

### `POST /api/inference/baseline`

Runs the Random Forest baseline adapter. The current implementation is a lightweight statistical baseline despite the historical name.

### `POST /api/inference/timeradar`

Runs TimeRadar when its dependencies and checkpoint are available. The adapter uses a 100-sample window.

### `POST /api/inference/chronos2`

Runs Chronos-2 forecasting when its dependencies are available. At least 32 input samples are required.

### `POST /api/inference/timer`

Runs Timer forecasting when its dependencies are available. At least 16 input samples are required.

### Unknown model

`POST /api/inference/{model_name}` returns HTTP 404 for unsupported model names.

## Analysis

### `POST /api/analysis`

Request:

```json
{
  "machine_id": "M-001",
  "values": [1, 2, 3, 4],
  "horizon": 12,
  "include_heavy_models": true
}
```

The endpoint always runs Online anomaly and the baseline. When `include_heavy_models` is true, it also invokes TimeRadar, Chronos-2, and Timer.

The response contains:

- `machine_id`;
- `models` — per-model results;
- `available_models` — models that returned `available=true`;
- `anomaly_index` — average of the available anomaly indicators currently used by the code;
- `interpretation` — explicit warning that the index is not a calibrated failure probability.

The resulting ensemble record is saved to local SQLite.

## Local data

### `POST /api/local/telemetry`

Stores a machine ID and numeric values in local SQLite.

### `GET /api/local/telemetry`

Returns recent telemetry. Optional query parameters:

- `machine_id`
- `limit` (1–1000, default 100)

### `GET /api/local/predictions`

Returns recent saved predictions. Optional `machine_id` and `limit` parameters have the same semantics.

## Model management

### `GET /api/model-manager`

Returns all model specifications and installed/readiness information.

### `GET /api/model-manager/{model_name}/status`

Returns runtime status for a specific model.

### `POST /api/model-manager/{model_name}/download`

Starts an asynchronous download for downloadable models. Built-in models return immediately with a message that there is nothing to download.

### `GET /api/model-manager/jobs/{job_id}`

Returns asynchronous download job state and progress/message information.

### `DELETE /api/model-manager/{model_name}`

Deletes an installed optional model. Built-in models cannot be deleted.

### `POST /api/model-manager/{model_name}/unload`

Removes matching loaded model objects from the in-process model cache. This is memory unloading, not disk deletion.

## API security boundary

The API is localhost-bound by default. There is no application-level authentication or authorization in these route modules. A caller that can reach the local API can invoke its endpoints. Do not expose the service publicly without adding an explicit security layer.
