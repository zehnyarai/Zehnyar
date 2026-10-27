import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.app.main import app  # noqa: E402
from backend.app.payments import make_password_hash  # noqa: E402

client = TestClient(app)
INSTALL = "bcbf7187-1c85-4fa9-9fc8-a97aa05bd901"
ADMIN_PASSWORD = "SecureOwnerPass2026!"


def configure(monkeypatch, tmp_path):
    monkeypatch.setenv("PAYMENTS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PAYMENT_CARD_NUMBER", "6037990000000000")
    monkeypatch.setenv("PAYMENT_CARD_HOLDER", "Visayar Test")
    monkeypatch.setenv("PAYMENT_BANK_NAME", "Test Bank")
    monkeypatch.setenv("VISAYAR_ADMIN_USERNAME", "owner")
    monkeypatch.setenv("VISAYAR_ADMIN_PASSWORD_HASH", make_password_hash(ADMIN_PASSWORD))
    monkeypatch.setenv("VISAYAR_ENCRYPTION_KEY", "test-key-does-not-enable-encryption")


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
    assert {p["sku"]: p["discountPercent"] for p in config["packages"]} == {
        "assessment_1": 0, "assessment_3": 17, "assessment_6": 25, "assessment_12": 33,
    }
    assert client.get(f"/api/payments/credits/{INSTALL}").json() == {"freeRemaining": 2, "paidCredits": 0}
    assert client.post(f"/api/payments/consume/{INSTALL}").json()["consumed"] == "free"
    assert client.post(f"/api/payments/consume/{INSTALL}").json()["consumed"] == "free"
    assert client.post(f"/api/payments/consume/{INSTALL}").status_code == 402


def test_manual_receipt_admin_approval_grants_credits_once(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    response = client.post(
        "/api/payments/requests",
        data={"install_id": INSTALL, "sku": "assessment_3", "transfer_date": "۱۴۰۵/۰۸/۰۵", "tracking_code": "TRX-12345"},
        files={"receipt": ("receipt.png", b"fake-png", "image/png")},
    )
    assert response.status_code == 200, response.text
    request_id = response.json()["requestId"]
    assert response.json()["priceToman"] == 1_500_000
    assert client.get("/api/admin/payments").status_code == 401
    login = client.post("/api/admin/auth/login", json={"username": "owner", "password": ADMIN_PASSWORD})
    assert login.status_code == 200
    item = client.get("/api/admin/payments").json()["items"][0]
    assert item["id"] == request_id
    assert item["transferDate"] == "1405/08/05"
    assert item["phone"] == ""
    assert client.get(f"/api/admin/payments/{request_id}/receipt").status_code == 200
    unauthenticated = TestClient(app)
    assert unauthenticated.post(f"/api/admin/payments/{request_id}/approve").status_code == 401
    approved = client.post(f"/api/admin/payments/{request_id}/approve")
    assert approved.json() == {"status": "approved", "creditsGranted": 3}
    assert client.post(f"/api/admin/payments/{request_id}/approve").json()["creditsGranted"] == 3
    assert client.get(f"/api/payments/credits/{INSTALL}").json() == {"freeRemaining": 2, "paidCredits": 3}
    assert client.post(f"/api/payments/consume/{INSTALL}").json()["consumed"] == "free"
    assert client.post(f"/api/payments/consume/{INSTALL}").json()["consumed"] == "free"
    assert client.post(f"/api/payments/consume/{INSTALL}").json()["consumed"] == "paid"
    assert client.get(f"/api/payments/requests/{request_id}?install_id={INSTALL}").json()["status"] == "approved"
    declined_response = client.post(
        "/api/payments/requests",
        data={"install_id": INSTALL, "sku": "assessment_1", "transfer_date": "2026-10-27", "tracking_code": "TRX-REJECT"},
        files={"receipt": ("receipt.png", b"fake-png", "image/png")},
    )
    declined_id = declined_response.json()["requestId"]
    declined = client.post(f"/api/admin/payments/{declined_id}/reject", json={"reason": "رسید با مبلغ سفارش تطبیق ندارد"})
    assert declined.json() == {"status": "rejected", "reason": "رسید با مبلغ سفارش تطبیق ندارد"}
    assert client.get(f"/api/payments/requests/{declined_id}?install_id={INSTALL}").json()["rejectionReason"] == "رسید با مبلغ سفارش تطبیق ندارد"
    assert client.get("/admin/payments").status_code == 200
    assert "پنل مدیریت ویزایار" in client.get("/admin/payments").text
    assert client.post("/api/admin/auth/logout").status_code == 200


def test_payment_is_disabled_without_owner_configuration(monkeypatch):
    for key in ("PAYMENT_CARD_NUMBER", "PAYMENT_CARD_HOLDER", "PAYMENT_BANK_NAME", "VISAYAR_ADMIN_USERNAME", "VISAYAR_ADMIN_PASSWORD_HASH"):
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
