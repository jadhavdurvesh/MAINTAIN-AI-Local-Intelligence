from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'


def test_models():
    # Model management is exposed at /api/model-manager. The endpoint also
    # refreshes the registry, so optional heavyweight models remain optional.
    with TestClient(app) as client:
        r = client.get('/api/model-manager')
    assert r.status_code == 200
    models = r.json()['models']
    assert len(models) >= 5
    assert {m['name'] for m in models} >= {
        'TimeRadar',
        'Chronos-2',
        'Timer',
        'Random Forest baseline',
        'Online anomaly',
    }


def test_online_inference():
    with TestClient(app) as client:
        r = client.post('/api/inference/online', json={'machine_id': 'M-001', 'values': [1, 1, 1, 2]})
    assert r.status_code == 200
    assert r.json()['model'] == 'Online anomaly'


def test_model_status():
    with TestClient(app) as client:
        r = client.get('/api/model-manager/online-anomaly/status')
    assert r.status_code == 200
    assert r.json()['available'] is True
