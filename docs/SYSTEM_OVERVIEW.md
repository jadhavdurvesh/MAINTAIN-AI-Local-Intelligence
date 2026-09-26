# System Overview

## 1. Purpose

MAINTAIN AI Local Intelligence is a local-first inference engine for the MAINTAIN AI industrial ecosystem. Its job is to receive time-series telemetry, run supported local intelligence adapters, optionally combine anomaly indicators, and return structured results to local callers.

The current implementation is deliberately an inference/runtime layer. It does not train models during installation or normal inference. The project README explicitly separates calibrated MAINTAIN AI risk modelling from the current anomaly/forecast outputs.

## 2. Ecosystem position

The current repository sits at the edge/local-intelligence boundary:

```text
Industrial sensors / gateway / MAINTAIN AI application
                    |
                    v
        MAINTAIN AI Local Intelligence
                    |
          +---------+----------+
          |                    |
       FastAPI             Desktop UI
          |                    |
    +-----+------+             |
    |            |             |
 Built-in    Optional          |
 adapters    foundation       |
    |          models           |
    +-----+------+-------------+
          |
     Local SQLite
```

The repository README also describes local API consumers including the desktop UI, MAINTAIN AI backend, and industrial gateway/edge computer.

## 3. Runtime layers

### Layer A — Desktop operator application

`desktop.py` is a Windows Tkinter application. It starts the local API in-process through Uvicorn, provides model management, telemetry input, inference controls, diagnostics, and links to local API/data locations.

The UI is an operator client, not the intelligence implementation itself.

### Layer B — FastAPI application

`app/main.py` creates the FastAPI application, initializes the model registry during lifespan startup, and mounts the route groups under `/api`.

Current route groups:

- health;
- inference;
- analysis;
- local data;
- model management.

### Layer C — Model registry and adapters

`app/models/registry.py` describes the supported model catalog and runtime availability. `app/models/adapters.py` implements the actual local inference adapters.

### Layer D — Model management

`app/model_manager.py` owns optional model download locations, download jobs, installed-model status, deletion, and model storage under `~/.maintain-ai/models` by default.

### Layer E — Local persistence

`app/storage.py` creates a local SQLite database at `~/.maintain-ai/local_intelligence.db` by default. It stores telemetry and prediction results.

## 4. Request lifecycle

A typical direct API inference request follows:

```text
Client
  -> POST /api/inference/<model>
  -> Pydantic Telemetry validation
  -> route handler
  -> app.models.adapters.<model>()
  -> optional local model load/cache
  -> structured result
  -> HTTP JSON response
```

A full analysis request follows:

```text
Client
  -> POST /api/analysis
  -> online anomaly
  -> baseline
  -> optional TimeRadar
  -> optional Chronos-2
  -> optional Timer
  -> combine available anomaly scores
  -> save ensemble prediction to SQLite
  -> return structured analysis
```

## 5. Model families

There are two conceptual groups:

### Built-in lightweight adapters

- Online anomaly
- Random Forest baseline

They are represented as built-in model-manager entries and do not require model checkpoint downloads.

### Optional heavier models

- TimeRadar — zero-shot anomaly detection.
- Chronos-2 — forecasting.
- Timer — forecasting.

Heavy model dependencies are intentionally optional in `requirements.txt` so the base install remains lightweight.

## 6. Local-only security boundary

The default API host is `127.0.0.1` on port `8000`. This means the API is intended to be reachable only from the local machine by default.

This is a network exposure boundary, not an authentication system. The current local API has no user login, JWT/session authentication, technician identity verification, roles, or permissions. See [AUTHENTICATION.md](AUTHENTICATION.md).

## 7. Data boundary

Telemetry and prediction history are stored locally in SQLite. Optional model checkpoints are stored locally under the model directory. The runtime does not require a cloud database for the functionality implemented in this repository.

The wider MAINTAIN AI ecosystem may have cloud/backend services, but those are outside this repository unless an integration is explicitly implemented here.

## 8. What this system does not currently claim

The current code must not be interpreted as providing:

- calibrated machine failure probabilities;
- automatic maintenance decisions;
- model training;
- a cloud-hosted model registry;
- multi-user authentication;
- technician authentication;
- enterprise authorization/RBAC;
- public API exposure by default;
- a complete industrial asset-management system.

The README explicitly states that anomaly scores are indicators rather than calibrated failure probabilities.

## 9. Operational principle

The intended operating principle is:

**keep the edge inference runtime small, local, inspectable, and independently operable; install heavyweight intelligence only when needed.**
