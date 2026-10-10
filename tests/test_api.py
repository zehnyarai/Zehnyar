import io
from datetime import date
import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import ValidationError

import server.api as service
from server.api import app
from server.database import connect, sample_report
from server.security import ATTEMPTS, SESSION_COOKIE

ADMIN_EMAIL = "manager@example.com"
ADMIN_PASSWORD = "test-admin-password-2026"
USER_PASSWORD = "test-user-password-2026"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.setenv("ADMIN_EMAIL", ADMIN_EMAIL)
    monkeypatch.setenv("ADMIN_PASSWORD", ADMIN_PASSWORD)
    for name in ["VISION_MODEL", "GROQ_API_KEY", "OPENAI_API_KEY", "ZARINPAL_MERCHANT_ID", "PUBLIC_BASE_URL"]:
        monkeypatch.delenv(name, raising=False)
    ATTEMPTS.clear()
    with TestClient(app) as instance:
        yield instance


def guest(client):
    response = client.get("/api/bootstrap")
    assert response.status_code == 200
    return response.json()


def register(client, email="farmer@example.com"):
    response = client.post("/api/auth/register", json={"name": "باغدار آزمون", "email": email, "password": USER_PASSWORD})
    assert response.status_code == 200, response.text
    return guest(client)


def admin_login(client):
    assert client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}).status_code == 200


def orchard_data():
    return {"name": "باغ آزمایش", "city": "رفسنجان", "province": "کرمان", "cultivar": "اکبری", "area": 4.5, "trees": 400, "irrigation": "قطره‌ای", "age": 12}


def photo(size=(500, 400)):
    stream = io.BytesIO()
    image = Image.new("RGB", size, (105, 160, 90))
    exif = Image.Exif()
    exif[270] = "private metadata"
    image.save(stream, "JPEG", exif=exif)
    return stream.getvalue()


def enable_vision(monkeypatch):
    monkeypatch.setenv("VISION_PROVIDER", "groq")
    monkeypatch.setenv("VISION_MODEL", "test-vision-model")
    monkeypatch.setenv("GROQ_API_KEY", "not-a-real-key")


async def mock_vision(image, context):
    result = sample_report()
    result.update({"provider": "test-provider", "is_pistachio": True, "summary": "نتیجه آزمون اتصال، نه تشخیص بالینی"})
    return result


def send_image(client, **kwargs):
    fields = {"consent": "true", "tree_part": "برگ", **kwargs}
    return client.post("/api/analyses", files={"image": ("tree.jpg", photo(), "image/jpeg")}, data=fields)


def enable_payments(monkeypatch):
    enable_vision(monkeypatch)
    monkeypatch.setenv("ZARINPAL_MERCHANT_ID", "test-merchant-id")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://pistachio.example.com")
    monkeypatch.setenv("COOKIE_SECURE", "false")


def test_bootstrap_and_private_guest_sessions(client):
    data = guest(client)
    assert data["user"]["is_demo"] == 1
    assert len(data["orchards"]) == 2 and len(data["reports"]) == 2 and len(data["tasks"]) == 3
    assert all(r["is_sample"] for r in data["reports"])
    assert not data["services"]["vision_configured"]
    assert not data["services"]["payment_configured"]
    assert not data["services"]["weather_configured"]
    assert guest(client)["user"]["id"] == data["user"]["id"]
    other = TestClient(app)
    second = guest(other)
    assert data["user"]["id"] != second["user"]["id"]
    assert other.get(f"/api/reports/{data['reports'][0]['id']}").status_code == 404
    assert other.put(f"/api/orchards/{data['orchards'][0]['id']}", json=orchard_data()).status_code == 404


def test_real_account_removes_only_demo_fixtures(client):
    guest(client)
    created = client.post("/api/orchards", json=orchard_data())
    assert created.status_code == 201
    result = register(client)
    assert result["user"]["is_demo"] == 0
    assert len(result["orchards"]) == 1
    assert result["orchards"][0]["id"] == created.json()["id"]
    assert result["reports"] == [] and result["tasks"] == []
    with connect() as db:
        stored = db.execute("SELECT password_hash FROM users WHERE email=?", ("farmer@example.com",)).fetchone()[0]
        assert stored.startswith("scrypt$") and USER_PASSWORD not in stored


def test_password_validation_and_registration_conflict(client):
    assert client.post("/api/auth/register", json={"name": "نام", "email": "wrong", "password": "123"}).status_code == 422
    register(client)
    assert client.post("/api/auth/register", json={"name": "نام", "email": "farmer@example.com", "password": USER_PASSWORD}).status_code == 409
    assert client.post("/api/auth/login", json={"email": "farmer@example.com", "password": "wrong-password"}).status_code == 401


def test_logout_invalidates_session_and_admin_is_guarded(client):
    register(client)
    assert client.get("/api/admin/overview").status_code == 403
    old = client.cookies.get(SESSION_COOKIE)
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/payments").status_code == 401
    client.cookies.set(SESSION_COOKIE, old)
    assert client.get("/api/payments").status_code == 401
    client.cookies.clear()
    admin_login(client)
    result = client.get("/api/admin/overview")
    assert result.status_code == 200 and not result.json()["is_demo"]
    assert result.json()["metrics"]["revenue_rial"] == 0


def test_orchard_crud_validation_and_free_limit(client):
    register(client)
    first = client.post("/api/orchards", json=orchard_data()).json()
    second = client.post("/api/orchards", json=orchard_data())
    assert second.status_code == 201
    assert client.post("/api/orchards", json=orchard_data()).status_code == 403
    assert client.post("/api/orchards", json={**orchard_data(), "area": -1}).status_code == 422
    assert client.put(f"/api/orchards/{first['id']}", json={**orchard_data(), "name": "باغ ویرایش"}).status_code == 200
    assert guest(client)["orchards"][0]["name"] == "باغ ویرایش"
    assert client.delete(f"/api/orchards/{first['id']}").status_code == 200
    assert len(guest(client)["orchards"]) == 1


def test_task_crud_and_ownership(client):
    info = guest(client)
    result = client.post("/api/tasks", json={"title": "آزمایش آب و خاک", "kind": "nutrition", "due_date": date.today().isoformat(), "orchard_id": info["orchards"][0]["id"]})
    assert result.status_code == 201
    id_ = result.json()["id"]
    assert client.put(f"/api/tasks/{id_}", json={"done": True}).status_code == 200
    assert next(t for t in guest(client)["tasks"] if t["id"] == id_)["done"] == 1
    other = TestClient(app)
    guest(other)
    assert other.delete(f"/api/tasks/{id_}").status_code == 404
    assert client.delete(f"/api/tasks/{id_}").status_code == 200
    assert client.post("/api/tasks", json={"title": "یادآور", "due_date": "not-a-date"}).status_code == 422


def test_unconfigured_analysis_never_fabricates_result(client):
    before = guest(client)
    response = send_image(client)
    assert response.status_code == 503
    assert len(guest(client)["reports"]) == len(before["reports"])
    result = client.get("/api/sample-report").json()
    assert result["is_sample"] is True and result["data"]["provider"] == "demo"


def test_image_validation_and_exif_stripping(client, monkeypatch):
    register(client)
    enable_vision(monkeypatch)
    monkeypatch.setattr(service, "analyze_with_provider", mock_vision)
    response = client.post("/api/analyses", files={"image": ("photo.jpg", b"not an image", "image/jpeg")}, data={"consent": "true"})
    assert response.status_code == 422
    small = client.post("/api/analyses", files={"image": ("photo.jpg", photo((32, 32)), "image/jpeg")}, data={"consent": "true"})
    assert small.status_code == 422
    response = send_image(client)
    assert response.status_code == 201
    report = response.json()
    assert report["is_sample"] == 0 and "image_path" not in report
    image = client.get(report["image_url"])
    assert image.status_code == 200
    assert not Image.open(io.BytesIO(image.content)).getexif()
    other = TestClient(app)
    guest(other)
    assert other.get(report["image_url"]).status_code == 404


def test_consent_and_real_login_required(client, monkeypatch):
    guest(client)
    enable_vision(monkeypatch)
    assert send_image(client).status_code == 401
    register(client)
    assert send_image(client, consent="false").status_code == 422
    assert send_image(client, tree_part="نامعتبر").status_code == 422


def test_server_enforced_credits_survive_report_deletion(client, monkeypatch):
    register(client)
    enable_vision(monkeypatch)
    monkeypatch.setattr(service, "analyze_with_provider", mock_vision)
    ids = [send_image(client).json()["id"] for _ in range(3)]
    assert send_image(client).status_code == 402
    assert client.delete(f"/api/reports/{ids[0]}").status_code == 200
    assert guest(client)["usage"]["used"] == 3
    assert send_image(client).status_code == 402
    assert client.get(f"/api/reports/{ids[0]}/image").status_code == 404


def test_provider_error_does_not_consume_credit(client, monkeypatch):
    register(client)
    enable_vision(monkeypatch)
    async def failed(*_):
        raise HTTPException(502, "provider unavailable")
    monkeypatch.setattr(service, "analyze_with_provider", failed)
    assert send_image(client).status_code == 502
    assert guest(client)["usage"]["used"] == 0
    with connect() as db:
        assert db.execute("SELECT image_path FROM reports").fetchone()[0] is None


def test_vision_schema_rejects_hallucinated_fields_and_invalid_scores():
    base = sample_report()
    for name in ["disclaimer", "provider", "knowledge_version"]:
        base.pop(name)
    base["hypotheses"][0]["confidence"] = 2
    with pytest.raises(ValidationError):
        service.VisionResult.model_validate(base)
    base["hypotheses"][0]["confidence"] = .5
    base["definitive_diagnosis"] = "unsupported"
    with pytest.raises(ValidationError):
        service.VisionResult.model_validate(base)


def test_unconfigured_payment_has_no_transaction(client):
    register(client)
    assert client.post("/api/payments/request", json={"plan": "monthly"}).status_code == 503
    assert client.get("/api/payments").json() == []
    assert client.post("/api/payments/request", json={"plan": "monthly", "amount": 1}).status_code == 422


def test_payment_amount_is_rial_verified_and_idempotent(client, monkeypatch):
    register(client)
    enable_payments(monkeypatch)
    calls = []
    authority = "A" * 32
    async def provider(path, payload, sandbox=None):
        calls.append((path, payload))
        if path == "request":
            assert payload["amount"] == 2490000
            assert payload["callback_url"].startswith("https://")
            return {"code": 100, "authority": authority}
        assert payload["amount"] == 2490000 and payload["authority"] == authority
        return {"code": 100, "ref_id": 20261009}
    monkeypatch.setattr(service, "provider_payment", provider)
    assert client.post("/api/payments/request", json={"plan": "monthly"}).status_code == 200
    # Use a separate callback client: verification does not trust a user's cookie.
    callback = TestClient(app)
    response = callback.get(f"/api/payments/callback?Authority={authority}&Status=OK", follow_redirects=False)
    assert response.status_code == 303 and response.headers["location"] == "/subscription?payment=success"
    with connect() as db:
        before = db.execute("SELECT subscription_until FROM users WHERE email='farmer@example.com'").fetchone()[0]
        assert before
        assert db.execute("SELECT status FROM payments").fetchone()[0] == "paid"
    callback.get(f"/api/payments/callback?Authority={authority}&Status=OK", follow_redirects=False)
    callback.get(f"/api/payments/callback?Authority={authority}&Status=NOK", follow_redirects=False)
    with connect() as db:
        after = db.execute("SELECT subscription_until FROM users WHERE email='farmer@example.com'").fetchone()[0]
        assert after == before
        assert db.execute("SELECT status FROM payments").fetchone()[0] == "paid"
    assert len(calls) == 2


def test_failed_and_forged_callback_never_activates_subscription(client, monkeypatch):
    register(client)
    enable_payments(monkeypatch)
    authority = "B" * 32
    async def provider(path, _, sandbox=None):
        return {"code": 100, "authority": authority} if path == "request" else {"code": -51}
    monkeypatch.setattr(service, "provider_payment", provider)
    assert client.post("/api/payments/request", json={"plan": "yearly"}).status_code == 200
    callback = TestClient(app)
    assert callback.get("/api/payments/callback?Authority=forged&Status=OK").status_code == 404
    response = callback.get(f"/api/payments/callback?Authority={authority}&Status=OK", follow_redirects=False)
    assert response.headers["location"] == "/subscription?payment=failed"
    with connect() as db:
        assert db.execute("SELECT subscription_until FROM users WHERE email='farmer@example.com'").fetchone()[0] is None


def test_payment_timeout_remains_pending_for_reconciliation(client, monkeypatch):
    register(client)
    enable_payments(monkeypatch)
    authority = "C" * 32
    async def provider(path, _, sandbox=None):
        if path == "request":
            return {"code": 100, "authority": authority}
        raise HTTPException(502, "timeout")
    monkeypatch.setattr(service, "provider_payment", provider)
    assert client.post("/api/payments/request", json={"plan": "monthly"}).status_code == 200
    response = TestClient(app).get(f"/api/payments/callback?Authority={authority}&Status=OK", follow_redirects=False)
    assert response.headers["location"] == "/subscription?payment=pending"
    with connect() as db:
        assert db.execute("SELECT status FROM payments").fetchone()[0] == "pending"


def test_csrf_limits_and_http_only_cookie(client):
    response = client.get("/api/bootstrap")
    cookie = response.headers.get("set-cookie")
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie
    assert client.post("/api/orchards", json=orchard_data(), headers={"Origin": "https://untrusted.example"}).status_code == 403
    assert client.post("/api/orchards", json=orchard_data(), headers={"Origin": "http://testserver"}).status_code == 201
    assert client.post("/api/orchards", content=b"x" * 65537).status_code == 413


def test_export_is_admin_only_and_sanitizes_formula_email(client):
    register(client, email="=formula@example.com")
    assert client.get("/api/admin/payments/export").status_code == 403
    with connect() as db:
        user = db.execute("SELECT id FROM users WHERE email='=formula@example.com'").fetchone()[0]
        db.execute("INSERT INTO payments (id,user_id,plan,amount_rial,duration_days,status,created_at) VALUES ('test-csv',?,'monthly',2490000,30,'pending','2026-10-09')", (user,))
    admin_login(client)
    result = client.get("/api/admin/payments/export")
    assert result.status_code == 200 and "'=formula@example.com" in result.text


def test_knowledge_provenance_and_demo_is_read_only(client, monkeypatch):
    result = client.get("/api/knowledge").json()
    assert len(result["articles"]) == 18
    assert not result["reviewed"]
    assert all(a["sources"] and a["review_status"] for a in result["articles"])
    assert client.get("/api/admin/demo").json()["is_demo"]
    monkeypatch.setenv("DEMO_MODE", "false")
    assert TestClient(app).get("/api/bootstrap").json()["user"] is None
    assert client.get("/api/admin/demo").status_code == 403


def test_chunked_request_size_is_limited(client):
    guest(client)
    response = client.post("/api/orchards", content=iter([b"x" * 33000, b"x" * 33000]), headers={"Content-Type": "application/json"})
    assert response.status_code == 413


def test_sandbox_money_and_entitlement_are_not_real_sales(client, monkeypatch):
    register(client)
    enable_payments(monkeypatch)
    authority = "D" * 32
    async def provider(path, _, sandbox=None):
        if path == "verify":
            assert sandbox is True
        return {"code": 100, "authority": authority} if path == "request" else {"code": 100, "ref_id": 123456}
    monkeypatch.setattr(service, "provider_payment", provider)
    client.post("/api/payments/request", json={"plan": "monthly"})
    TestClient(app).get(f"/api/payments/callback?Authority={authority}&Status=OK", follow_redirects=False)
    assert guest(client)["usage"]["premium"] is True
    monkeypatch.setenv("ZARINPAL_SANDBOX", "false")
    assert guest(client)["usage"]["premium"] is False
    admin = TestClient(app, base_url="https://testserver")
    admin_login(admin)
    result = admin.get("/api/admin/overview").json()
    assert result["transactions"][0]["is_sandbox"] == 1
    assert result["metrics"]["revenue_rial"] == 0


def test_no_paid_plan_sold_without_vision_configuration(client, monkeypatch):
    register(client)
    enable_payments(monkeypatch)
    monkeypatch.delenv("VISION_MODEL")
    response = client.post("/api/payments/request", json={"plan": "monthly"})
    assert response.status_code == 503
    assert client.get("/api/payments").json() == []


@pytest.mark.parametrize("case", ["valid", "non_pistachio", "bad_score", "chemical_dose"])
def test_actual_provider_adapter_validates_structured_output(client, monkeypatch, case):
    import asyncio
    enable_vision(monkeypatch)
    base = sample_report()
    for key in ["disclaimer", "provider", "knowledge_version"]:
        base.pop(key)
    base["is_pistachio"] = case != "non_pistachio"
    if case == "bad_score":
        base["hypotheses"][0]["confidence"] = 100
    if case == "chemical_dose":
        base["actions"] = ["مصرف ۲ گرم ماده پیشنهاد می‌شود"]
    class FakeClient:
        def __init__(self, **_):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *_):
            pass
        async def post(self, endpoint, headers, json):
            assert endpoint.startswith("https://api.groq.com/")
            assert json["model"] == "test-vision-model"
            assert json["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
            return httpx.Response(200, json={"choices": [{"message": {"content": __import__('json').dumps(base, ensure_ascii=False)}}]}, request=httpx.Request("POST", endpoint))
    monkeypatch.setattr(service.httpx, "AsyncClient", FakeClient)
    if case in {"bad_score", "chemical_dose"}:
        with pytest.raises(HTTPException) as error:
            asyncio.run(service.analyze_with_provider(photo(), {"notes": "context"}))
        assert error.value.status_code == 502
    else:
        result = asyncio.run(service.analyze_with_provider(photo(), {"notes": "context"}))
        assert result["model"] == "test-vision-model"
        assert result["references"]
        if case == "non_pistachio":
            assert result["hypotheses"] == []


def test_render_public_url_fallback_and_override(client, monkeypatch):
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://pestino-pilot.example")
    assert service.public_base_url() == "https://pestino-pilot.example"
    assert service.secure_cookie() is True
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://pestino-custom.example")
    assert service.public_base_url() == "https://pestino-custom.example"


def test_health_identifies_pestino_without_leaking_secrets(client):
    result = client.get("/api/health").json()
    assert result["app"] == "pestino"
    assert result["version"] == "0.1.0"
    assert "GROQ_API_KEY" not in str(result)
