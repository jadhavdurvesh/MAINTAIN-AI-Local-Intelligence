# MAINTAIN AI Local Intelligence — Architecture

## 1. Position in the ecosystem

The local intelligence application is the PC/edge inference tier. It is not the hosted MAINTAIN AI backend and is not the technician Workforce client.

```text
Sensors / Gateway / Main Platform
              |
              | telemetry / controlled requests
              v
   MAINTAIN AI Local Intelligence
              |
      +-------+--------+
      |                |
   FastAPI          Desktop UI
      |
 +----+-----------------------------+
 |          |          |            |
Online   TimeRadar  Chronos-2     Timer
anomaly
 |          |          |            |
 +----------+----------+------------+
              |
          Local SQLite
```

The wider platform can consume local intelligence results, but business decisions remain outside the inference layer.

## 2. Process architecture

The FastAPI app is created in `app/main.py`.

At application lifespan startup it initializes the model registry. It then mounts these route groups:

- health;
- inference;
- analysis;
- local data;
- model management.

The desktop imports the same FastAPI app and serves it with Uvicorn on localhost.

## 3. Data flow

### Direct inference

```text
HTTP request
 -> Pydantic validation
 -> route
 -> adapter
 -> optional lazy model load
 -> structured JSON
```

### Analysis

```text
HTTP request
 -> Online anomaly + baseline
 -> optional heavy models
 -> anomaly-index aggregation
 -> SQLite prediction record
 -> JSON response
```

### Telemetry persistence

```text
HTTP/local caller
 -> /api/local/telemetry
 -> SQLite telemetry table
```

## 4. Model lifecycle

```text
Catalog entry
   |
   +--> dependency readiness
   |
   +--> checkpoint installed
   |
   +--> model loaded lazily
   |
   +--> cached in process
   |
   +--> unload cache
   |
   +--> delete checkpoint
```

These are separate states and should not be collapsed into a single `available` concept in future UI design.

## 5. Storage architecture

Local runtime state lives under `~/.maintain-ai` by default:

```text
~/.maintain-ai/
├── local_intelligence.db
└── models/
```

The database is SQLite. Model directories contain optional checkpoints.

## 6. Security architecture

Default network exposure:

```text
127.0.0.1:8000
```

This is deliberately local-only. It is not user authentication.

Identity and authorization belong to the wider platform boundary. If remote calls are later required, add an explicit authenticated gateway rather than directly exposing this service.

## 7. Component dependency rules

- UI may call API; UI should not implement model algorithms.
- Routes may call adapters/storage/model-manager; routes should not contain model internals.
- Adapters may load models; adapters should not own HTTP concerns.
- Storage owns persistence; it should not decide maintenance actions.
- Model manager owns model files/downloads; it should not calculate inference.
- Main platform owns maintenance business logic and identity.

## 8. Scalability boundary

The current application is a single-process local service with process-local model cache and local SQLite storage. It is appropriate for a PC/edge runtime, not a horizontally scaled cloud inference cluster.

A future distributed deployment would require deliberate changes to model storage, job execution, cache ownership, database access, and API security.
