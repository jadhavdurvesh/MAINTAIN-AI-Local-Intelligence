from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

_DB_LOCK = threading.Lock()


def _db_path() -> Path:
    configured = os.getenv("MAINTAIN_LOCAL_DB")
    if configured:
        path = Path(configured).expanduser()
    else:
        path = Path.home() / ".maintain-ai" / "local_intelligence.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path(), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS telemetry (id INTEGER PRIMARY KEY AUTOINCREMENT, machine_id TEXT NOT NULL, received_at REAL NOT NULL, values_json TEXT NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS predictions (id INTEGER PRIMARY KEY AUTOINCREMENT, machine_id TEXT NOT NULL, created_at REAL NOT NULL, model TEXT NOT NULL, result_json TEXT NOT NULL)")
    conn.commit()
    return conn


def save_telemetry(machine_id: str, values: list[float]) -> int:
    with _DB_LOCK, _connect() as conn:
        cur = conn.execute("INSERT INTO telemetry(machine_id, received_at, values_json) VALUES(?,?,?)", (machine_id, time.time(), json.dumps(values)))
        conn.commit()
        return int(cur.lastrowid)


def recent_telemetry(machine_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    with _DB_LOCK, _connect() as conn:
        if machine_id:
            rows = conn.execute("SELECT id,machine_id,received_at,values_json FROM telemetry WHERE machine_id=? ORDER BY id DESC LIMIT ?", (machine_id, limit)).fetchall()
        else:
            rows = conn.execute("SELECT id,machine_id,received_at,values_json FROM telemetry ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [{"id": r["id"], "machine_id": r["machine_id"], "received_at": r["received_at"], "values": json.loads(r["values_json"])} for r in rows]


def save_prediction(machine_id: str, model: str, result: dict[str, Any]) -> int:
    with _DB_LOCK, _connect() as conn:
        cur = conn.execute("INSERT INTO predictions(machine_id, created_at, model, result_json) VALUES(?,?,?,?)", (machine_id, time.time(), model, json.dumps(result)))
        conn.commit()
        return int(cur.lastrowid)


def recent_predictions(machine_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    with _DB_LOCK, _connect() as conn:
        if machine_id:
            rows = conn.execute("SELECT id,machine_id,created_at,model,result_json FROM predictions WHERE machine_id=? ORDER BY id DESC LIMIT ?", (machine_id, limit)).fetchall()
        else:
            rows = conn.execute("SELECT id,machine_id,created_at,model,result_json FROM predictions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [{"id": r["id"], "machine_id": r["machine_id"], "created_at": r["created_at"], "model": r["model"], "result": json.loads(r["result_json"])} for r in rows]
