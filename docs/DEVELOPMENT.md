# Development Guide

## Requirements

The CI baseline uses Python 3.11 on Windows.

Install base dependencies:

```text
python -m pip install -r requirements.txt
```

Heavy model dependencies are optional and are intentionally not part of the base requirements.

## Run the API from source

The FastAPI object is `app.main:app`.

A typical development server command is:

```text
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then open the FastAPI documentation at `/docs`.

## Run the desktop application

From the repository root:

```text
python desktop.py
```

The desktop application starts the local API itself.

## Optional models

The helper script supports optional setup:

```text
python scripts/install_models.py --timeradar
python scripts/install_models.py --forecasts
```

The script installs optional dependencies and can cache forecast checkpoints. It does not train models.

## Environment configuration

Important supported variables include:

- `MAINTAIN_AI_HOME` — local intelligence root directory;
- `MAINTAIN_LOCAL_DB` — explicit SQLite database path;
- `MAINTAIN_TIMERADAR_MODEL` — TimeRadar checkpoint path;
- `MAINTAIN_CHRONOS_MODEL_PATH` — Chronos-2 local path;
- `MAINTAIN_CHRONOS_MODEL` — Chronos-2 model ID;
- `MAINTAIN_TIMER_MODEL_PATH` — Timer local path;
- `MAINTAIN_TIMER_MODEL` — Timer model ID.

## Change workflow

Before changing code:

1. identify the owning layer;
2. read the relevant focused documentation;
3. inspect the existing tests;
4. make the smallest coherent change;
5. run tests;
6. verify desktop import when UI/runtime code changes;
7. update documentation if the contract changes.

## Ownership map

| Change | Primary file(s) |
|---|---|
| API route | `app/routes/*.py` |
| Application composition | `app/main.py` |
| Model algorithm | `app/models/adapters.py` |
| Model catalog | `app/models/registry.py` |
| Download lifecycle | `app/model_manager.py` |
| Local persistence | `app/storage.py` |
| Desktop UI | `desktop.py` |
| Packaging | `packaging/*` |
| CI | `.github/workflows/build.yml` |
| Tests | `tests/*` |

## Architecture rule

Do not put model-specific logic in the desktop UI. Do not put business-domain maintenance workflows in the inference service. Keep adapters, orchestration, persistence, API, and presentation separate.

## Commit hygiene

When a change crosses a contract boundary, update the corresponding documentation in the same change. This makes future debugging substantially easier than reconstructing architecture from old commits.
