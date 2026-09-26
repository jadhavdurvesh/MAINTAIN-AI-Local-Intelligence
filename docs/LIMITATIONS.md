# Current Limitations and Explicit Non-Goals

This document prevents future development from accidentally treating planned capabilities as already implemented.

## 1. No user authentication in this repository

The local API is localhost-bound but has no user/session/JWT/RBAC implementation.

## 2. No enterprise system of record

SQLite is local runtime storage. It is not the wider MAINTAIN AI platform database.

## 3. No calibrated failure probability

Current anomaly outputs and the `anomaly_index` are indicators, not validated failure probabilities.

## 4. No training pipeline

The repository is an inference/runtime layer. It does not train the listed foundation models during normal installation or inference.

## 5. Forecasts are not maintenance decisions

Chronos-2 and Timer produce forecasts. The current system does not automatically turn them into work orders or maintenance actions.

## 6. Built-in baseline naming is ahead of implementation

The catalog label says `Random Forest baseline`, but the current adapter returns basic statistics and does not train/use a Random Forest model.

## 7. Model readiness is multi-dimensional

The existence of a model-manager entry does not mean the model is installed, its dependencies are ready, its checkpoint is valid, or it has been successfully loaded.

## 8. Download integrity is not yet cryptographically pinned

The model manager downloads from configured GitHub/Hugging Face sources but does not currently verify a project-specific cryptographic manifest for every checkpoint.

## 9. Desktop UI is local and synchronous by design

The Tkinter UI needs careful background-thread handling for long inference/download operations.

## 10. Test coverage is incomplete

Heavy-model inference, real downloads, GPU paths, packaged UI interaction, installer behavior, and security boundaries need more comprehensive testing.

## 11. Remote exposure is not a supported default

The API is intentionally bound to `127.0.0.1`. Making it remotely reachable requires a new security design.

## 12. Wider ecosystem modules are external

Technician authentication, Workforce Android, maintenance/work-order workflows, central machine records, cloud database behavior, and sensor firmware are not implemented in this repository.

## Development rule

When adding a feature that crosses one of these boundaries, update this document and the relevant focused architecture document so the repository's conceptual model remains accurate.
