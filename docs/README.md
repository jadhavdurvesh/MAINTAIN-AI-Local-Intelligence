# MAINTAIN AI Local Intelligence — Documentation Hub

This directory is the engineering documentation source of truth for the **MAINTAIN-AI-Local-Intelligence** repository.

## What this repository is

MAINTAIN AI Local Intelligence is the local-first inference/runtime layer for the wider MAINTAIN AI industrial ecosystem. It runs selected intelligence workloads on a Windows PC or industrial edge computer and exposes them through a localhost FastAPI service. The desktop application is an operator workspace around that service.

The repository currently contains:

- a FastAPI application and REST API;
- lightweight built-in anomaly/baseline adapters;
- optional heavier pretrained-model adapters;
- a local model manager for downloading/removing optional models;
- SQLite-backed local telemetry and prediction history;
- a Windows Tkinter desktop operator application;
- PyInstaller/Inno Setup packaging;
- GitHub Actions validation, packaging, signing hooks, and artifact publication;
- automated API/local-data tests.

## Important scope boundary

This repository is **not** the whole MAINTAIN AI industrial platform. It does not currently contain the web/cloud application, central multi-user identity system, Supabase/Neon database, technician authentication, machine-maintenance workflow, or other product modules that may exist elsewhere in the wider MAINTAIN AI ecosystem.

When a concept is discussed in these docs but is not implemented in this repository, it is explicitly marked as **planned**, **external**, or **not implemented here**. Do not infer implementation from a design statement.

## Read in this order

1. [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) — complete system/ecosystem map and request lifecycle.
2. [PROJECT_MAP.md](PROJECT_MAP.md) — repository/file map.
3. [ARCHITECTURE.md](ARCHITECTURE.md) — architectural boundaries and data flow.
4. [API.md](API.md) — REST API contract and endpoint behavior.
5. [MODELS.md](MODELS.md) — model catalog, capabilities, readiness, and model selection.
6. [MODEL_MANAGER.md](MODEL_MANAGER.md) — downloading, storage, deletion, and unloading.
7. [INFERENCE.md](INFERENCE.md) — individual model adapters and inference behavior.
8. [ANALYSIS.md](ANALYSIS.md) — multi-model analysis/ensemble behavior.
9. [STORAGE.md](STORAGE.md) — local SQLite telemetry and prediction persistence.
10. [DESKTOP.md](DESKTOP.md) — Windows desktop application and UI architecture.
11. [AUTHENTICATION.md](AUTHENTICATION.md) — current authentication/security boundary.
12. [PACKAGING.md](PACKAGING.md) — executable and installer creation.
13. [CI_CD.md](CI_CD.md) — GitHub Actions pipeline.
14. [TESTING.md](TESTING.md) — tests and verification strategy.
15. [DEVELOPMENT.md](DEVELOPMENT.md) — local development workflow.
16. [LIMITATIONS.md](LIMITATIONS.md) — known architectural/product limitations.

## Existing focused documents

- [INSTALL.md](INSTALL.md) — installation notes.
- [INTEGRATION.md](INTEGRATION.md) — integration notes.
- [SIGNING.md](SIGNING.md) — Windows code-signing process.

Those documents remain useful, but the documents above provide the deeper component-level explanation.

## Documentation rules

### Source of truth

Implementation claims must be derived from the current repository code/configuration. If code and documentation disagree, the code is the current implementation and the documentation must be corrected.

### Implementation vs plan

Use these labels when needed:

- **Implemented** — present in the current repository and wired into runtime/build paths.
- **Optional** — implemented, but requires additional packages/model files.
- **Development-only** — used for source checkout or CI rather than normal packaged operation.
- **External** — belongs to another MAINTAIN AI repository/service.
- **Planned** — a future design target, not current functionality.
- **Limitation** — known gap or constraint in the current implementation.

### No silent assumptions

Do not document a model, endpoint, database table, authentication flow, cloud service, or UI feature as existing unless the repository actually implements it.
