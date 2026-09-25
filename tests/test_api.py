from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'

def test_models():
    r = client.get('/api/models')
    assert r.status_code == 200
    assert len(r.json()['models']) >= 5

def test_online_inference():
    r = client.post('/api/inference/online', json={'machine_id':'M-001','values':[1,1,1,2]})
    assert r.status_code == 200
    assert r.json()['model'] == 'Online anomaly'
