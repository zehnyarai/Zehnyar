"""تست‌های امنیتی: پرداخت جعلی، هدرها، CSRF، محدودیت ورودی و نرخ درخواست."""
import base64
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config, main
from app.config import ConfigError, Settings, validate_settings
from app.db import db
from app.security import RateLimiter, client_ip

TEMPLATES = Path(main.__file__).parent / "templates"


@pytest.fixture()
def client():
    with TestClient(main.app) as c:
        yield c


def _admin_headers():
    token = base64.b64encode(b"admin:test-pass").decode()
    return {"Authorization": f"Basic {token}"}


def _new_mock_authority(client) -> str:
    client.post("/premium/checkout", data={"plan": "month"}, follow_redirects=False)
    with db() as conn:
        return conn.execute("SELECT authority FROM payments ORDER BY id DESC LIMIT 1").fetchone()[0]


# ---------------------------------------------------------------- پرداخت آزمایشی
def test_forged_mock_callback_cannot_issue_license(client):
    """کسی که Status=OK را به callback می‌دهد، بدون تأیید کاربر، نباید لایسنس بگیرد."""
    authority = _new_mock_authority(client)
    r = client.get("/premium/callback", params={"Authority": authority, "Status": "OK"}, follow_redirects=False)
    assert r.status_code == 303
    assert "rz_license" not in r.headers.get("set-cookie", "")
    token = r.headers["location"].split("t=")[1]
    page = client.get(f"/premium/result?t={token}")
    assert "پرداخت انجام شد" not in page.text
    with db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM licenses").fetchone()[0] == 0


def test_forged_mock_callback_for_unknown_authority_is_404(client):
    r = client.get("/premium/callback", params={"Authority": "MOCKNOPE", "Status": "OK"}, follow_redirects=False)
    assert r.status_code == 404


def test_user_approval_in_mock_page_issues_license_once(client):
    authority = _new_mock_authority(client)
    client.post(f"/premium/mock/{authority}", data={"outcome": "OK"}, follow_redirects=False)
    r1 = client.get("/premium/callback", params={"Authority": authority, "Status": "OK"}, follow_redirects=False)
    r2 = client.get("/premium/callback", params={"Authority": authority, "Status": "OK"}, follow_redirects=False)
    assert "rz_license" in r1.headers.get("set-cookie", "")
    assert r2.status_code == 303
    with db() as conn:
        codes = conn.execute("SELECT code FROM licenses").fetchall()
    assert len(codes) == 1  # callback تکراری لایسنس دوم نمی‌سازد


def test_user_cancel_in_mock_page_issues_nothing(client):
    authority = _new_mock_authority(client)
    client.post(f"/premium/mock/{authority}", data={"outcome": "NOK"}, follow_redirects=False)
    r = client.get("/premium/callback", params={"Authority": authority, "Status": "OK"}, follow_redirects=False)
    token = r.headers["location"].split("t=")[1]
    assert "پرداخت انجام نشد" in client.get(f"/premium/result?t={token}").text
    with db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM licenses").fetchone()[0] == 0


def test_mock_page_rejected_when_mock_disabled(monkeypatch, client):
    authority = _new_mock_authority(client)
    monkeypatch.setattr(config, "settings", Settings(app_env="production", zarinpal_merchant_id="M" * 36))
    monkeypatch.setattr(main, "payment_mode", lambda: "zarinpal")
    r = client.post(f"/premium/mock/{authority}", data={"outcome": "OK"}, follow_redirects=False)
    assert r.status_code == 404


# ---------------------------------------------------------------- پیکربندی امن
def test_default_environment_is_production():
    """پیش‌فرض‌ها در یک فرایند جدا بررسی می‌شوند تا ماژول config در تست‌های دیگر دست‌نخورده بماند."""
    import os
    import subprocess
    import sys
    env = {k: v for k, v in os.environ.items() if k not in {"APP_ENV", "COOKIE_SECURE", "ZARINPAL_SANDBOX"}}
    code = ("import sys; sys.path.insert(0,'.'); from app.config import settings as s; "
            "print(s.app_env, s.cookie_secure, s.zarinpal_sandbox, s.allow_mock_payments)")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         cwd=str(Path(main.__file__).resolve().parents[1]), env=env, check=True).stdout.split()
    assert out == ["production", "True", "False", "False"]


def test_production_refuses_mock_payments_and_http_base_url():
    with pytest.raises(ConfigError, match="ALLOW_MOCK_PAYMENTS"):
        validate_settings(Settings(app_env="production", allow_mock_payments=True,
                                   public_base_url="https://x.ir", admin_password="long-enough-pass"))
    with pytest.raises(ConfigError, match="https"):
        validate_settings(Settings(app_env="production", public_base_url="http://x.ir",
                                   admin_password="long-enough-pass"))
    with pytest.raises(ConfigError, match="۱۲"):
        validate_settings(Settings(app_env="production", public_base_url="https://x.ir", admin_password="short"))
    validate_settings(Settings(app_env="production", public_base_url="https://x.ir", admin_password="long-enough-pass"))


def test_invalid_app_env_rejected():
    with pytest.raises(ConfigError):
        validate_settings(Settings(app_env="staging"))


# ---------------------------------------------------------------- هدرها و CSP
def test_security_headers_present(client):
    r = client.get("/")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert "script-src 'self'" in r.headers["content-security-policy"]
    assert "unsafe-inline'" not in r.headers["content-security-policy"].split("script-src")[1].split(";")[0]
    assert r.headers["referrer-policy"] == "strict-origin-when-cross-origin"


def test_sensitive_pages_not_cached(client):
    assert "no-store" in client.get("/account").headers.get("cache-control", "")
    analyze = client.post("/api/groups/riazi/analyze", json={"gpa": 15})
    assert analyze.status_code == 200
    assert "no-store" in analyze.headers.get("cache-control", "")
    assert "no-store" not in client.get("/").headers.get("cache-control", "")


def test_no_inline_script_in_templates():
    for path in TEMPLATES.glob("*.html"):
        text = path.read_text(encoding="utf-8")
        inline = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>", text)
        assert not inline, f"{path.name} has inline script"


# ---------------------------------------------------------------- CSRF / Origin
def test_cross_origin_post_is_blocked(client):
    h = {**_admin_headers(), "Origin": "https://evil.example", "Host": "testserver"}
    r = client.post("/admin/cutoffs", headers=h,
                    files={"file": ("x.csv", b"year,group,university,field,quota,last_rank\n", "text/csv")},
                    follow_redirects=False)
    assert r.status_code == 403


def test_cross_site_fetch_metadata_is_blocked(client):
    r = client.post("/account/logout", headers={"Sec-Fetch-Site": "cross-site"}, follow_redirects=False)
    assert r.status_code == 403


def test_same_origin_post_allowed(client):
    r = client.post("/account/logout", headers={"Origin": "http://testserver", "Host": "testserver"},
                    follow_redirects=False)
    assert r.status_code == 303


# ---------------------------------------------------------------- ورودی‌ها
def test_oversized_inputs_rejected(client):
    many = {f"k{i}": 1 for i in range(50)}
    assert client.post("/api/groups/riazi/analyze", json={"pct": many}).status_code == 422
    assert client.post("/api/groups/riazi/analyze", json={"pct": {"x" * 60: 1}}).status_code == 422
    assert client.post("/api/groups/riazi/analyze", json={"unknown": 1}).status_code == 422
    assert client.get("/api/fields", params={"q": "a" * 500}).status_code == 422
    assert client.get("/api/universities", params={"type": "x" * 100}).status_code == 422
    assert client.post("/account/activate", data={"code": "x" * 100}).status_code == 422


def test_invalid_mode_rejected(client):
    assert client.get("/api/universities", params={"mode": "bogus"}).status_code == 422


def test_xss_in_group_param_is_escaped(client):
    r = client.get("/universities", params={"group": '"><script>alert(1)</script>'})
    assert "<script>alert(1)" not in r.text


def test_unknown_plan_rejected(client):
    r = client.post("/premium/checkout", data={"plan": "../../etc"}, follow_redirects=False)
    assert r.status_code == 400


# ---------------------------------------------------------------- نرخ درخواست
def test_activation_rate_limited(client):
    statuses = [client.post("/account/activate", data={"code": "RZ-0000-0000-0000-0000"}).status_code
                for _ in range(12)]
    assert 429 in statuses and statuses.count(400) == 10


def test_checkout_rate_limited(client):
    statuses = [client.post("/premium/checkout", data={"plan": "bogus"}, follow_redirects=False).status_code
                for _ in range(22)]
    assert 429 in statuses


def test_admin_login_rate_limited(client):
    bad = {"Authorization": "Basic " + base64.b64encode(b"admin:wrong").decode()}
    statuses = [client.get("/admin", headers=bad).status_code for _ in range(35)]
    assert 429 in statuses and 401 in statuses


def test_rate_limiter_window_and_reset():
    rl = RateLimiter()
    assert all(rl.hit("k", 3, 60) for _ in range(3))
    assert rl.hit("k", 3, 60) is False
    assert rl.hit("other", 3, 60) is True
    rl.reset()
    assert rl.hit("k", 3, 60) is True


def test_client_ip_ignores_forwarded_header_by_default():
    scope = {"client": ("1.2.3.4", 1), "headers": [(b"x-forwarded-for", b"9.9.9.9")]}
    assert client_ip(scope) == "1.2.3.4"


# ---------------------------------------------------------------- پایداری
def test_app_works_without_lifespan():
    """قبلاً بدون اجرای lifespan، اولین درخواست پرداخت با خطای جدول مواجه می‌شد."""
    c = TestClient(main.app)  # بدون with
    r = c.post("/premium/checkout", data={"plan": "month"}, follow_redirects=False)
    assert r.status_code in (303, 400, 429, 503)


# ---------------------------------------------------------------- PWA
def test_manifest_and_service_worker_served(client):
    m = client.get("/static/manifest.webmanifest")
    assert m.status_code == 200
    data = m.json()
    assert data["display"] == "standalone" and data["dir"] == "rtl"
    assert any(i["sizes"] == "512x512" for i in data["icons"])
    for icon in data["icons"]:
        assert client.get(icon["src"]).status_code == 200
    sw = client.get("/sw.js")
    assert sw.status_code == 200
    assert sw.headers["service-worker-allowed"] == "/"
    assert "javascript" in sw.headers["content-type"]


def test_service_worker_never_caches_sensitive_paths():
    sw = (Path(main.__file__).parent / "static" / "sw.js").read_text(encoding="utf-8")
    assert "/static/" in sw and "req.method !== 'GET'" in sw
    for forbidden in ("/premium", "/admin", "/account", "/api"):
        assert forbidden not in sw.split("self.addEventListener('fetch'")[1].split("startsWith('/static/')")[0]


def test_install_button_and_pwa_script_on_pages(client):
    html = client.get("/").text
    assert 'id="install-app"' in html and 'rel="manifest"' in html
    assert "/static/js/pwa.js" in html
