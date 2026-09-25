# Model Inventory

## TimeRadar

TimeRadar is used as an optional zero-shot temporal anomaly detector. The MAINTAIN AI hosted implementation keeps the checkpoint outside the normal lightweight serverless dependency set and loads it locally when configured. fileciteturn9file0L2-L6

## Chronos-2

Chronos-2 is an optional zero-shot forecasting adapter. It forecasts future signal values and does not directly output a calibrated machine-failure probability. The existing MAINTAIN AI adapter requires at least 32 recent samples and uses `amazon/chronos-2` by default. fileciteturn8file0L2-L6

## Timer

Timer is an optional forecasting model. The main MAINTAIN AI setup caches `thuml/timer-base-84m` when the optional forecast setup is requested. fileciteturn7file0L7-L14

## Local baseline

The local runtime also exposes a lightweight baseline and online anomaly adapter so the application remains useful before heavyweight model checkpoints are installed.

## Important distinction

An anomaly score is evidence of unusual behaviour. A forecast is an estimate of future signal values. Neither should be presented as a calibrated failure probability without a separately validated risk model.
