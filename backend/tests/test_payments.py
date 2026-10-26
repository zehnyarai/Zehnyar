import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.app.main import app  # noqa: E402

client = TestClient(app)
INSTALL = "bcbf7187-1c85-4fa9-9fc8-a97aa05bd901"
ADMIN_TOKEN = "test-admin-token-with-more-than-thirty-two-characters"


def configure(monkeypatch, tmp_path):
    monkeypatch.setenv("PAYMENTS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PAYMENT_CARD_NUMBER", "6037990000000000")
    monkeypatch.setenv("PAYMENT_CARD_HOLDER", "Visayar Test")
    monkeypatch.setenv("PAYMENT_BANK_NAME", "Test Bank")
    monkeypatch.setenv("PAYMENT_ADMIN_TOKEN", ADMIN_TOKEN)


def test_payment_prices_and_free_quota(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    config = client.get("/api/payments/config").json()
    assert config["enabled"] is True
    assert config["freeAssessments"] == 2
    assert {p["sku"]: p["priceToman"] for p in config["packages"]} == {
        "assessment_1": 600_000,
        "assessment_3": 1_500_000,
        "assessment_6": 2_700_000,
        "assessment_12": 4_800_000,
    }
    assert client.get(f"/api/payments/credits/{INSTALL}").json() == {"freeRemaining": 2, "paidCredits": 0}
    assert client.post(f"/api/payments/consume/{INSTALL}").json()["consumed"] == "free"
    assert client.post(f"/api/payments/consume/{INSTALL}").json()["consumed"] == "free"
    assert client.post(f"/api/payments/consume/{INSTALL}").status_code == 402


def test_manual_receipt_admin_approval_grants_credits_once(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    response = client.post(
        "/api/payments/requests",
        data={"install_id": INSTALL, "sku": "assessment_3", "phone": "۰۹۱۲۳۴۵۶۷۸۹", "tracking_code": "TRX-12345"},
        files={"receipt": ("receipt.png", b"fake-png", "image/png")},
    )
    assert response.status_code == 200, response.text
    request_id = response.json()["requestId"]
    assert response.json()["priceToman"] == 1_500_000
    assert client.get("/api/admin/payments", headers={"X-Admin-Token": ADMIN_TOKEN}).json()["items"][0]["id"] == request_id
    assert client.get(f"/api/admin/payments/{request_id}/receipt", headers={"X-Admin-Token": ADMIN_TOKEN}).status_code == 200
    assert client.post(f"/api/admin/payments/{request_id}/approve").status_code == 403
    approved = client.post(f"/api/admin/payments/{request_id}/approve", headers={"X-Admin-Token": ADMIN_TOKEN})
    assert approved.json() == {"status": "approved", "creditsGranted": 3}
    assert client.post(f"/api/admin/payments/{request_id}/approve", headers={"X-Admin-Token": ADMIN_TOKEN}).json()["creditsGranted"] == 3
    assert client.get(f"/api/payments/credits/{INSTALL}").json() == {"freeRemaining": 2, "paidCredits": 3}
    assert client.post(f"/api/payments/consume/{INSTALL}").json()["consumed"] == "free"
    assert client.post(f"/api/payments/consume/{INSTALL}").json()["consumed"] == "free"
    assert client.post(f"/api/payments/consume/{INSTALL}").json()["consumed"] == "paid"
    assert client.get(f"/api/payments/requests/{request_id}?install_id={INSTALL}").json()["status"] == "approved"
    assert client.get("/admin/payments").status_code == 200
    assert "بررسی رسیدهای ویزایار" in client.get("/admin/payments").text


def test_payment_is_disabled_without_owner_configuration(monkeypatch):
    for key in ("PAYMENT_CARD_NUMBER", "PAYMENT_CARD_HOLDER", "PAYMENT_BANK_NAME", "PAYMENT_ADMIN_TOKEN"):
        monkeypatch.delenv(key, raising=False)
    config = client.get("/api/payments/config").json()
    assert config["enabled"] is False
    assert config["card"] is None
    response = client.post(
        "/api/payments/requests",
        data={"install_id": INSTALL, "sku": "assessment_1", "phone": "09123456789", "tracking_code": "TRX-8888"},
        files={"receipt": ("receipt.png", b"fake-png", "image/png")},
    )
    assert response.status_code == 503
