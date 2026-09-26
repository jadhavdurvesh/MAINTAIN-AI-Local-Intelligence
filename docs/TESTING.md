# Testing and Verification

## Current test suite

The repository currently contains API and local-storage tests.

### `tests/test_api.py`

Covers:

- `/api/health` success;
- model-manager catalog contains the expected five model entries;
- Online anomaly inference route;
- Online anomaly model status.

### `tests/test_local_data.py`

Covers a telemetry round-trip using a temporary SQLite database:

```text
POST telemetry
   -> SQLite
GET telemetry
   -> previously stored machine ID
```

## CI verification beyond tests

The workflow also verifies that:

```text
import desktop
from app.main import app
```

works successfully.

The packaged executable is then launched as a smoke test.

## What is not yet deeply tested

The current suite does not comprehensively test:

- TimeRadar actual inference;
- Chronos-2 actual inference;
- Timer actual inference;
- real model downloads;
- model deletion/unloading end-to-end;
- desktop UI interaction;
- installer installation/uninstallation;
- GPU execution;
- corrupted model checkpoints;
- concurrent inference/download operations;
- long-running memory behavior;
- public/remote API security.

Those should be added before treating the local engine as production-grade across all supported environments.

## Recommended test layers

### Unit tests

Test individual adapter calculations, path resolution, model status transitions, and storage functions.

### API contract tests

Test request validation, HTTP status codes, endpoint schemas, and error messages.

### Integration tests

Use controlled local fixtures/checkpoints to test model-manager -> adapter -> inference flows.

### Desktop tests

Launch the packaged application and exercise critical UI actions using a Windows automation strategy.

### Release smoke tests

On a clean Windows machine:

1. install;
2. launch;
3. verify API health;
4. verify built-in models;
5. run a built-in analysis;
6. optionally install a heavy model;
7. verify inference;
8. verify delete/unload;
9. uninstall.

## Testing principle

Every important product claim should map to a repeatable test. If a feature cannot be verified by an automated or documented manual test, mark it as unverified rather than assuming it works.
