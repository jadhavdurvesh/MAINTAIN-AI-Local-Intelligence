# Analysis / Ensemble Layer

## Purpose

`app/routes/analysis.py` provides a higher-level operation that runs several local intelligence adapters and returns one structured analysis object.

It is an orchestration layer, not a new machine-learning model.

## Request

The request contains:

- `machine_id`;
- numeric `values`;
- forecast `horizon`;
- `include_heavy_models`.

## Execution order

The endpoint first runs:

1. Online anomaly;
2. baseline.

When heavy models are enabled, it additionally runs:

3. TimeRadar;
4. Chronos-2;
5. Timer.

The current implementation invokes these sequentially in one request.

## Available-model filtering

After execution, the endpoint builds `available_models` from results whose `available` field is truthy.

A model can therefore appear in `models` while not appearing in `available_models`.

## Anomaly index

The current index only uses anomaly-capable values:

- Online anomaly's latest z-score is normalized by dividing by 6 and capped at 1;
- TimeRadar's latest anomaly score is added directly when available.

The final index is the arithmetic mean of the available scores.

Chronos-2 and Timer forecasts are not included in the anomaly-index calculation.

## Interpretation

The endpoint explicitly returns:

```text
Model outputs are indicators, not calibrated failure probabilities.
```

This is an important product boundary. The ensemble should not be presented as a validated maintenance-risk probability.

## Persistence

The complete result is saved as a prediction with model name `ensemble` using `save_prediction()`.

This provides local historical traceability but is not currently an enterprise audit log.

## Future extension points

A future advanced analysis layer can add:

- calibrated risk models;
- model confidence/uncertainty;
- feature quality checks;
- missing-data handling;
- timestamp-aware sampling validation;
- model agreement/disagreement diagnostics;
- per-machine baselines;
- threshold configuration;
- industrial ground-truth evaluation.

Those should be added as explicit contracts rather than silently changing the meaning of `anomaly_index`.
