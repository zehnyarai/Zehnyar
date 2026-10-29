import sqlite3
import sys
from pathlib import Path

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.app.main import app  # noqa: E402
from backend.app.payments import make_password_hash  # noqa: E402

client = TestClient(app)


def configure_admin(monkeypatch, tmp_path):
    monkeypatch.setenv("PAYMENTS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("VISAYAR_ADMIN_USERNAME", "owner")
    monkeypatch.setenv("VISAYAR_ADMIN_PASSWORD_HASH", make_password_hash("SecureOwnerPass2026!"))
    monkeypatch.setenv("VISAYAR_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))


def test_admin_login_encrypts_gemini_and_card_settings(monkeypatch, tmp_path):
    configure_admin(monkeypatch, tmp_path)
    wrong = client.post("/api/admin/auth/login", json={"username": "owner", "password": "bad-password"})
    assert wrong.status_code == 401

    login = client.post("/api/admin/auth/login", json={"username": "owner", "password": "SecureOwnerPass2026!"})
    assert login.status_code == 200
    assert login.json() == {"authenticated": True, "username": "owner"}
    assert "httponly" in login.headers["set-cookie"].lower()
    assert client.get("/api/admin/auth/me").status_code == 200

    settings_url = "/api/admin/settings"
    assert client.get(settings_url).json()["encryptionConfigured"] is True
    gemini_key = "AIza" + "X" * 35
    saved = client.put(f"{settings_url}/gemini", json={"apiKey": gemini_key})
    assert saved.status_code == 200
    assert gemini_key not in saved.text
    card = client.put(
        f"{settings_url}/payment-card",
        json={"number": "6037990000000000", "holder": "Test Owner", "bank": "Test Bank"},
    )
    assert card.status_code == 200
    stored = client.get(settings_url).json()
    assert stored["geminiConfigured"] is True
    assert gemini_key[-4:] in stored["geminiMasked"]
    assert stored["card"]["number"] == "6037990000000000"
    config = client.get("/api/payments/config").json()
    assert config["enabled"] is True
    assert config["card"]["number"] == "6037990000000000"

    db = sqlite3.connect(tmp_path / "payments.sqlite3")
    try:
        encrypted = db.execute("SELECT encrypted_value FROM admin_settings WHERE setting_key='gemini_api_key'").fetchone()[0]
    finally:
        db.close()
    assert gemini_key not in encrypted

    client.post(f"{settings_url}/gemini", json={"apiKey": gemini_key})
    assert client.post("/api/admin/auth/logout").status_code == 200
    assert client.get(settings_url).status_code == 401


def test_admin_settings_reject_without_login_and_bad_encryption(monkeypatch, tmp_path):
    configure_admin(monkeypatch, tmp_path)
    client.post("/api/admin/auth/logout")
    assert client.put("/api/admin/settings/gemini", json={"apiKey": "AIza" + "Q" * 35}).status_code == 401
    login = client.post("/api/admin/auth/login", json={"username": "owner", "password": "SecureOwnerPass2026!"})
    assert login.status_code == 200
    monkeypatch.setenv("VISAYAR_ENCRYPTION_KEY", "invalid-key")
    response = client.put("/api/admin/settings/gemini", json={"apiKey": "AIza" + "Q" * 35})
    assert response.status_code == 503
