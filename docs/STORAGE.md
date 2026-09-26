# Local Storage

## Purpose

`app/storage.py` provides the local persistence layer for telemetry and inference history.

It uses SQLite from the Python standard library.

## Database location

Default:

```text
~/.maintain-ai/local_intelligence.db
```

The `MAINTAIN_LOCAL_DB` environment variable can override this path.

## Tables

### `telemetry`

Columns:

- `id` — auto-increment integer primary key;
- `machine_id` — asset identifier supplied by the caller;
- `received_at` — Unix timestamp;
- `values_json` — JSON-encoded numeric list.

### `predictions`

Columns:

- `id` — auto-increment integer primary key;
- `machine_id` — asset identifier;
- `created_at` — Unix timestamp;
- `model` — model/analysis name;
- `result_json` — JSON-encoded inference result.

## Connection behavior

The module creates the database and tables on connection if they do not already exist.

A process-local threading lock protects connection/write operations.

## Telemetry flow

```text
POST /api/local/telemetry
        |
        v
save_telemetry()
        |
        v
SQLite telemetry row
```

## Prediction flow

The analysis endpoint calls `save_prediction()` after constructing the ensemble result.

```text
analysis result
      |
      v
save_prediction()
      |
      v
SQLite predictions row
```

## Read APIs

`recent_telemetry()` and `recent_predictions()` support optional machine filtering and bounded result limits.

The API exposes those through `/api/local/telemetry` and `/api/local/predictions`.

## Current limitations

This is local runtime storage, not the wider platform's system of record.

The current implementation does not provide:

- schema migrations;
- retention policies;
- encryption at rest;
- per-user access controls;
- immutable audit logging;
- cloud synchronization;
- database backup automation;
- foreign keys to a machine registry.

If enterprise history is required, synchronization to the main platform should be an explicit integration rather than turning this SQLite file into a second enterprise database.
