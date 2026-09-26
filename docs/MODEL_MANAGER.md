# Model Manager

## Purpose

`app/model_manager.py` owns the local lifecycle of optional model assets. It does not implement inference itself.

Its responsibilities are:

1. define the supported model specifications;
2. determine local model paths;
3. report installation/status metadata;
4. start asynchronous downloads;
5. report download-job state;
6. delete optional downloaded models.

Runtime loading remains in `app/models/adapters.py`.

## Storage root

By default:

```text
~/.maintain-ai/
```

The environment variable `MAINTAIN_AI_HOME` can override the root.

Models are stored under:

```text
~/.maintain-ai/models/
```

## Model specifications

`MODEL_SPECS` defines five models:

- TimeRadar — GitHub archive source;
- Chronos-2 — Hugging Face repository `amazon/chronos-2`;
- Timer — Hugging Face repository `thuml/timer-base-84m`;
- Random Forest baseline — built-in;
- Online anomaly — built-in.

## Installed status

Built-in models are always considered installed/available by the model manager.

Downloadable models are considered installed when their configured model directory exists. This is a filesystem-level status and should be distinguished from dependency readiness and successful inference.

## Download flow

The API starts a background thread for optional model downloads:

```text
POST /download
      |
      v
create job ID
      |
      v
background thread
      |
      +--> temporary `.partial` directory
      |
      +--> download source
      |
      +--> rename temporary directory to final directory
      |
      v
job = done/error
```

The temporary directory prevents a failed download from looking like a completed model directory.

## Hugging Face models

For Chronos-2 and Timer, `huggingface_hub.snapshot_download()` copies the repository into the target local directory.

If `huggingface-hub` is unavailable, the download fails with a clear runtime error.

## TimeRadar

TimeRadar is downloaded from the configured GitHub archive URL. The manager extracts only the expected `TimeRadar-main/TimeRadar/` directory contents into the target directory.

## Delete vs unload

These operations are intentionally different:

### Delete

`DELETE /api/model-manager/{model_name}` removes the downloaded checkpoint directory from disk. It does not apply to built-in models.

### Unload

`POST /api/model-manager/{model_name}/unload` removes matching entries from the in-process `_MODEL_CACHE`. It does not remove files.

Therefore:

```text
Unload = free/release runtime model cache
Delete = remove local model files
```

## Failure handling

Download exceptions are recorded in the job state and the temporary download directory is removed.

The API returns the job ID so the desktop application can poll the job endpoint rather than blocking the UI.

## Security considerations

The current manager downloads released model assets from configured external sources. A production-grade future implementation should additionally consider:

- pinned revisions instead of floating branches;
- cryptographic integrity checks;
- signed metadata where available;
- disk-space checks;
- cancellation;
- download timeouts for every source;
- resume support for large files;
- model compatibility/version metadata.
