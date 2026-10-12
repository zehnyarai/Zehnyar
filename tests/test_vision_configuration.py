"""Synthetic keys only; no network or credential supplied in chat is used."""
import json

import pytest
from fastapi.testclient import TestClient

import server.api as service
from server.database import connect
from server.security import ATTEMPTS

DUMMY_KEY = 'dummy-private-runtime-key-for-tests-only'


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_PATH', str(tmp_path/'configuration.sqlite3'))
    monkeypatch.setenv('UPLOAD_DIR', str(tmp_path/'images'))
    monkeypatch.setenv('ADMIN_EMAIL', 'config-admin@example.com')
    monkeypatch.setenv('ADMIN_PASSWORD', 'config-test-password-2026')
    monkeypatch.setenv('COOKIE_SECURE', 'false')
    monkeypatch.setenv('DEMO_MODE', 'true')
    monkeypatch.setenv('LOAD_OWNER_DRAFT', 'false')
    monkeypatch.setenv('VISION_PROVIDER', 'gemini')
    monkeypatch.setenv('VISION_MODEL', '')
    monkeypatch.setenv('GEMINI_API_KEY', '')
    monkeypatch.setenv('GEMINI_REQUESTS_ENABLED', 'false')
    ATTEMPTS.clear()
    with TestClient(service.app, base_url='https://testserver') as c:
        yield c


def admin(c):
    assert c.post('/api/auth/login',json={'email':'config-admin@example.com','password':'config-test-password-2026'}).status_code == 200


def payload(**kwargs):
    return {'model':'gemini-3.1-pro-preview','replacement_key':DUMMY_KEY,'requests_enabled':False,'usage_approved':False,**kwargs}


def test_configuration_is_admin_only_and_never_reflects_a_secret(client):
    client.get('/api/bootstrap')
    assert client.get('/api/admin/vision/configuration').status_code == 401
    assert client.put('/api/admin/vision/configuration',json=payload()).status_code == 401
    admin(client)
    r=client.put('/api/admin/vision/configuration',json=payload())
    assert r.status_code == 200,r.text
    assert r.json()['key_present'] and not r.json()['requests_enabled']
    assert r.json()['storage']=='server-memory-only'
    assert DUMMY_KEY not in r.text
    assert DUMMY_KEY not in client.get('/api/admin/vision/configuration').text
    assert DUMMY_KEY not in client.get('/api/health').text
    assert DUMMY_KEY not in client.get('/api/bootstrap').text
    assert DUMMY_KEY not in client.get('/api/vision/status').text
    with connect() as db:
        for table in ['audit','vision_connection','users']:
            assert DUMMY_KEY not in json.dumps([dict(row) for row in db.execute('SELECT * FROM '+table)])
        assert db.execute('SELECT COUNT(*) FROM reports WHERE is_sample=0').fetchone()[0] == 0


@pytest.mark.parametrize('body',[
    {'model':'../bad','replacement_key':DUMMY_KEY},
    {'model':'gemini-valid','replacement_key':'short-secret'},
    {'model':'gemini-valid','replacement_key':DUMMY_KEY,'unexpected':DUMMY_KEY},
    {'model':'gemini-valid','replacement_key':DUMMY_KEY,'requests_enabled':'true'},
])
def test_validation_errors_are_sanitized_without_pydantic_input_echo(client,body):
    admin(client)
    r=client.put('/api/admin/vision/configuration',json=body)
    assert r.status_code == 422
    assert DUMMY_KEY not in r.text and 'short-secret' not in r.text
    assert 'input' not in r.text


def test_enabling_requires_explicit_usage_approval_and_does_not_make_a_model_request(client,monkeypatch):
    admin(client)
    r=client.put('/api/admin/vision/configuration',json=payload(requests_enabled=True))
    assert r.status_code == 422
    async def forbidden(*args,**kwargs):
        raise AssertionError('Saving a key must not call the provider')
    monkeypatch.setattr(service.gemini,'generate_content',forbidden)
    r=client.put('/api/admin/vision/configuration',json=payload(requests_enabled=True,usage_approved=True))
    assert r.status_code == 200 and r.json()['requests_enabled']
    s=client.get('/api/vision/status').json()
    assert s['vision_configured'] and not s['vision_verified']
    assert client.delete('/api/admin/vision/configuration').status_code == 200
    s=client.get('/api/vision/status').json()
    assert not s['vision_configured'] and not s['vision_verified']
    assert not client.get('/api/admin/vision/configuration').json()['key_present']


def test_http_cannot_accept_a_secret_even_for_admin(client):
    admin(client)
    r=client.put('http://testserver/api/admin/vision/configuration',json=payload())
    assert r.status_code == 400 and DUMMY_KEY not in r.text
    assert not client.get('/api/admin/vision/configuration').json()['key_present']


def test_malformed_json_does_not_echo_request_data(client):
    admin(client)
    r=client.put('/api/admin/vision/configuration',content='{bad-json-secret-test',headers={'Content-Type':'application/json'})
    assert r.status_code == 422 and 'bad-json-secret-test' not in r.text
