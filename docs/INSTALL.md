# Windows Installation and Operation

## 1. Source/developer mode

Create a Python 3.11 virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the API directly:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

## 2. Desktop/source mode

Run:

```powershell
python desktop.py
```

The desktop application starts the local API and exposes the operator workspace.

## 3. Packaged/installer mode

The GitHub Actions pipeline produces the Windows installer after tests, executable build, smoke test, and Inno Setup packaging pass.

For release/signing details, see [PACKAGING.md](PACKAGING.md) and [SIGNING.md](SIGNING.md).

## 4. Built-in intelligence

The base installation can use the lightweight built-in adapters. They do not require large model checkpoints.

## 5. Optional heavy intelligence

TimeRadar, Chronos-2, and Timer require additional dependencies/checkpoints.

The source-checkout helper is:

```powershell
python scripts/install_models.py --timeradar
python scripts/install_models.py --forecasts
```

The desktop model manager also has a download path for optional models.

## 6. Local data locations

Default root:

```text
%USERPROFILE%\.maintain-ai
```

Database:

```text
%USERPROFILE%\.maintain-ai\local_intelligence.db
```

Models:

```text
%USERPROFILE%\.maintain-ai\models
```

## 7. Environment overrides

Use environment variables when a deployment needs custom locations or model IDs. See [DEVELOPMENT.md](DEVELOPMENT.md).

## 8. Production edge rule

Keep the local service on a private/local interface. Authentication, authorization, TLS, and remote access policy must be designed at the trusted gateway/backend boundary before the service is exposed beyond the local machine.

## 9. First-run verification

After installation:

1. launch the desktop;
2. confirm the engine reaches Running;
3. open Diagnostics;
4. confirm `/api/health` responds;
5. confirm the model catalog is visible;
6. select a built-in model;
7. run a small telemetry analysis;
8. inspect the result/history.

Only then install optional heavyweight models.
