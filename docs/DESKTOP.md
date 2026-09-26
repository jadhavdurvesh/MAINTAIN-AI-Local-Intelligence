# Windows Desktop Application

## Purpose

`desktop.py` is the Windows operator application for the local intelligence engine.

It provides a graphical way to:

- start/stop the local engine;
- refresh model status;
- inspect/download/delete/unload models;
- enter telemetry;
- select a model and run inference/analysis;
- inspect local data and diagnostics;
- open FastAPI docs and the local data/model directories.

## Technology

The UI uses Python Tkinter/ttk. The local API is FastAPI served by Uvicorn.

The desktop imports the FastAPI app directly and runs Uvicorn on localhost. Therefore the packaged desktop process is the operator shell around the same API application used in development/tests.

## Startup lifecycle

The desktop constructor:

1. configures the window;
2. initializes application state;
3. configures ttk styles;
4. builds the UI;
5. registers the close handler;
6. schedules startup.

The UI maintains a small local catalog so it can render supported model entries even while API/model initialization is occurring.

## UI state

Important application state includes:

- `engine` — Uvicorn server/thread state;
- `busy` — operation state;
- `models` — current model-manager data;
- `active_model` — selected model;
- machine ID;
- forecast horizon;
- selected model.

## Workspace flow

The workspace allows the operator to provide telemetry and select an inference model. The desktop sends HTTP requests to the localhost API rather than duplicating adapter logic in the UI.

This separation is important:

```text
UI = presentation + operator actions
API = validation + routing
Adapters = intelligence
Storage = persistence
```

## Model workspace

The model area is expected to distinguish built-in models from downloadable models.

Built-in:

- Online anomaly;
- Random Forest baseline.

Downloadable:

- TimeRadar;
- Chronos-2;
- Timer.

The desktop should not require a manual model-file workflow for built-in adapters.

## Progress and diagnostics

Download jobs are asynchronous. The UI polls job status so a large model download does not block the main Tkinter event loop.

Diagnostics should report at least:

- whether the API port is listening;
- whether the health endpoint responds;
- whether the model manager endpoint responds;
- the local data/model locations;
- actionable failure text.

## UI design principle

The desktop is an operator console, not a generic model downloader. The primary experience should remain:

```text
Asset -> telemetry -> selected intelligence -> result -> interpretation/history
```

Model installation is a supporting workflow.

## Known architectural constraints

Tkinter is synchronous/event-loop driven. Long-running operations must remain outside the UI thread.

Heavy model inference can also be expensive. Future UI improvements should use background workers for operations that can block, then marshal results back onto the Tk event loop.

## Packaged application

The CI pipeline packages `desktop.py` with PyInstaller. The resulting executable is then used by the Inno Setup installer.
