# Windows Installation

## Developer mode

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

API: `http://127.0.0.1:8000/docs`

## Desktop mode

```powershell
python desktop.py
```

The desktop control panel starts the local FastAPI process and shows model readiness.

## Heavy model setup

Heavy ML packages and model checkpoints are intentionally optional. This keeps the base desktop application small. Install PyTorch/Transformers/Chronos and download checkpoints on machines that are intended to perform local inference.

## Production edge mode

Keep the service on a private interface. Put authentication, authorization, TLS and network policy in the MAINTAIN AI gateway/backend rather than embedding public authentication into the local model process.
