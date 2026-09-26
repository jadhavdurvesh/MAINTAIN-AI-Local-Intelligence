# Inference Engine

## Entry point

`app/models/adapters.py` is the core local intelligence adapter layer.

It exposes five model functions:

- `online_anomaly(values)`
- `baseline(values)`
- `timeradar(values)`
- `chronos2(values, horizon)`
- `timer(values, horizon)`

## Common principle

Adapters return Python dictionaries that are directly serializable by FastAPI. Heavy models are imported and loaded lazily so the base runtime can operate without all heavyweight dependencies.

## Online anomaly flow

```text
list[float]
 -> numpy array
 -> mean/std
 -> newest-value z-score
 -> JSON result
```

This is a lightweight statistical detector, not a learned foundation model.

## Baseline flow

```text
list[float]
 -> numpy array
 -> mean/min/max
 -> JSON result
```

The current implementation does not fit a Random Forest. The name is retained as the catalog label.

## TimeRadar flow

```text
values
 -> status/dependency check
 -> require >=2 samples
 -> keep last 100 or edge-pad to 100
 -> torch tensor [1,100,1]
 -> lazy-load AutoModel
 -> move to CUDA when available
 -> inference
 -> anomaly scores
```

Loaded models are cached.

## Chronos-2 flow

```text
values
 -> dependency check
 -> require >=32 samples
 -> keep last 512
 -> resolve local model path or model ID
 -> lazy-load Chronos2Pipeline
 -> select CPU/CUDA
 -> predict(horizon)
 -> flatten forecast
```

## Timer flow

```text
values
 -> dependency check
 -> require >=16 samples
 -> keep last 2880
 -> normalize using mean/std
 -> lazy-load AutoModelForCausalLM
 -> generate max_new_tokens=horizon
 -> inverse normalization
 -> forecast
```

## Model cache

`_MODEL_CACHE` is process-local. It is not a persistent model database.

A restart clears the cache and models will be loaded again on demand.

## Device selection

TimeRadar and Timer move loaded models to CUDA when `torch.cuda.is_available()` is true. Chronos-2 selects CUDA vs CPU through the pipeline's `device_map` argument.

This means inference performance depends on the edge machine's CPU/GPU resources.

## Errors

Heavy adapters generally convert missing dependencies, missing checkpoints, insufficient input, or runtime failures into structured result dictionaries containing `available: false` and a `reason` string. The route layer therefore returns a normal HTTP response for many model-runtime failures rather than automatically turning them into HTTP 500 errors.

## Important interpretation rule

Inference output is evidence/forecast information. The current code intentionally does not claim that these outputs are calibrated probabilities of machine failure.
