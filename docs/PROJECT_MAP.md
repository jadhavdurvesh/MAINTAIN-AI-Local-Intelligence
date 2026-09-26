# MAINTAIN AI Ecosystem + Local Intelligence Project Map

> This document distinguishes the wider MAINTAIN AI ecosystem from what is actually implemented in this repository.

## 1. Wider ecosystem boundary

The project map currently identifies these major responsibilities:

| Component | Responsibility | Boundary |
|---|---|---|
| Main MAINTAIN AI web/backend platform | Primary business platform and system of record | External to this repository |
| Workforce Android client | Technician-facing interaction, authentication, assigned machines, work orders, notifications | External to this repository |
| Local Intelligence | PC/edge inference node | **This repository** |
| Gateway/firmware | Sensor/machine acquisition and edge connectivity | External to this repository |

The current repository's implementation confirms that Local Intelligence is a standalone FastAPI + desktop inference runtime. The broader platform components must not be assumed to exist here merely because they are named in the ecosystem map.

## 2. Responsibility boundaries

### Identity and authorization

The wider ecosystem documentation places identity/authorization in the main MAINTAIN AI backend / Supabase Auth. This repository itself does not implement that identity system. See [AUTHENTICATION.md](AUTHENTICATION.md).

### Maintenance operations

Maintenance workflows belong to the main MAINTAIN AI backend. This repository supplies local intelligence results rather than owning work-order/business workflows.

### Local inference

This repository owns:

- model adapters;
- model readiness;
- local model files;
- inference APIs;
- local analysis;
- local inference history;
- Windows operator UI.

### Sensor acquisition

Gateway/firmware is the acquisition boundary. The local engine accepts telemetry values but does not implement machine firmware protocols in the current source tree.

### Technician interaction

The Workforce Android client is the technician-facing boundary in the wider ecosystem. The current desktop application is a local operator/inference workspace, not the Workforce application.

## 3. Local Intelligence internal map

```text
Desktop UI (`desktop.py`)
        |
        | localhost HTTP
        v
FastAPI (`app/main.py`)
        |
        +-------------------------------+
        |       |        |       |       |
      health inference analysis local  model-manager
                         data
        |       |        |       |       |
        +-------+--------+-------+-------+
                        |
                 model adapters
                 (`app/models`)
                        |
             +----------+----------+
             |                     |
        built-in adapters     optional models
             |                     |
          numpy/sklearn       local checkpoints
                        
                        +
                        |
                  SQLite storage
```

## 4. Important rule for future work

Do not move business-domain responsibilities into this repository simply because a local inference result is related to them.

For example:

- `anomaly_index` belongs to inference/analysis.
- deciding that a machine requires a maintenance work order belongs to the main platform.
- authenticating a technician belongs to the identity/auth boundary.
- reading raw industrial sensor protocols belongs to the gateway/firmware boundary.

This separation prevents the local intelligence node from becoming an accidental second backend.
