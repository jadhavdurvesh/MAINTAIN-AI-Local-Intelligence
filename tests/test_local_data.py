from fastapi.testclient import TestClient

from app.main import app


def test_local_telemetry_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("MAINTAIN_LOCAL_DB", str(tmp_path / "test.db"))
    client = TestClient(app)

    r = client.post('/api/local/telemetry', json={'machine_id': 'TEST-001', 'values': [1, 2, 3]})
    assert r.status_code == 200
    assert r.json()['accepted'] is True

    r = client.get('/api/local/telemetry?machine_id=TEST-001')
    assert r.status_code == 200
    assert r.json()['items'][0]['machine_id'] == 'TEST-001'
