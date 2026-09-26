# Models and Intelligence Catalog

## 1. Catalog source

The runtime catalog is defined by `app/model_manager.py`; runtime readiness is additionally reported by `app/models/registry.py`.

Current catalog:

| Model | Kind | Storage | Purpose |
|---|---|---|---|
| Online anomaly | online | Built-in | Streaming statistical anomaly indicator |
| Random Forest baseline | baseline | Built-in | Lightweight baseline/statistical checks |
| TimeRadar | zero-shot_anomaly | Optional local checkpoint | Zero-shot time-series anomaly detection |
| Chronos-2 | forecast | Optional local/downloaded checkpoint | Time-series forecasting |
| Timer | forecast | Optional local/downloaded checkpoint | Zero-shot time-series forecasting |

## 2. Online anomaly

Implemented by `online_anomaly()` in `app/models/adapters.py`.

The adapter computes the mean and standard deviation of the supplied values and calculates an absolute z-score for the newest observation:

```text
abs((latest - mean) / (std + 1e-9))
```

It requires no checkpoint.

## 3. Random Forest baseline

The current function is `baseline()` in `app/models/adapters.py`.

Important naming note: although the catalog calls this **Random Forest baseline**, the current adapter does not instantiate or train a Random Forest. It currently returns lightweight statistical values: mean, minimum, and maximum.

It requires no checkpoint.

## 4. TimeRadar

`timeradar()` requires PyTorch, Transformers, and a local TimeRadar checkpoint. It uses a 100-sample window and pads shorter sequences at the beginning.

The model is loaded lazily and cached in `_MODEL_CACHE`.

Default local location:

```text
~/.maintain-ai/models/TimeRadar
```

`MAINTAIN_TIMERADAR_MODEL` can override the configured checkpoint path.

## 5. Chronos-2

`chronos2()` requires PyTorch and `chronos-forecasting`. At least 32 samples are required.

The adapter uses up to the latest 512 samples and requests the caller's forecast horizon.

It uses `MAINTAIN_CHRONOS_MODEL_PATH` when a local model path is configured; otherwise it can use a model ID, defaulting to `amazon/chronos-2`.

## 6. Timer

`timer()` requires PyTorch and Transformers. At least 16 samples are required.

The current adapter uses up to the latest 2880 samples, normalizes the context, generates the requested horizon, then converts the generated values back to the input scale.

The default model ID is `thuml/timer-base-84m`, unless a local path or environment override is available.

## 7. Catalog vs readiness

A model can be listed even when it cannot currently execute.

Examples:

- TimeRadar may be catalogued while its checkpoint is missing.
- Chronos-2 may be catalogued while its optional runtime dependencies are absent.
- Timer may be catalogued while only its optional dependencies are absent.

The UI should therefore distinguish **catalogued**, **installed**, **dependencies ready**, **loaded**, and **inference-ready** states rather than reducing everything to one boolean.

## 8. Loading and unloading

Heavy models are loaded lazily. The loaded Python model objects are retained in the process `_MODEL_CACHE` so repeated requests do not reload them.

The model-management unload endpoint removes matching cache entries. It does not delete checkpoint files from disk.

## 9. Installation

The model manager stores optional checkpoints under:

```text
~/.maintain-ai/models/
```

The base runtime intentionally keeps heavy ML packages optional. `scripts/install_models.py` can install optional dependencies and cache released forecast checkpoints from a source checkout.

## 10. Interpretation boundary

An anomaly score means the model observed behaviour it considers unusual. A forecast estimates future signal values. Neither is automatically a calibrated machine-failure probability.

The repository README explicitly keeps a future calibrated MAINTAIN AI risk model separate from these inference outputs.

Any future risk score must have its own validated definition, data, calibration, thresholds, and evaluation procedure.
