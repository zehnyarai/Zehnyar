from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_legacy_and_new_clients_get_separate_datasets():
    old = client.get('/api/dataset')
    new = client.get('/api/v2/dataset')
    assert old.status_code == new.status_code == 200
    assert old.json()['meta']['version'] == '2.0.3'
    assert new.json()['meta']['version'] == '2.0.172'
    assert old.headers['etag'] != new.headers['etag']
    assert client.get('/api/v2/dataset', headers={'If-None-Match': new.headers['etag']}).status_code == 304
    assert client.get('/api/dataset', headers={'If-None-Match': new.headers['etag']}).status_code == 200
