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
        "assessment_3": 1_200_000,
        "assessment_6": 2_500_000,
        "assessment_12": 4_500_000,
    }
    assert {p["sku"]: p["discountPercent"] for p in config["packages"]} == {
        "assessment_1": 0, "assessment_3": 33.3, "assessment_6": 30.6, "assessment_12": 37.5,
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
    assert response.json()["priceToman"] == 1_200_000
    stored_receipts = list((tmp_path / "receipts").glob("*"))
    assert len(stored_receipts) == 1
    assert b"fake-png" not in stored_receipts[0].read_bytes()
    assert client.get("/api/admin/payments").status_code == 401
    login = client.post("/api/admin/auth/login", json={"username": "owner", "password": ADMIN_PASSWORD})
    assert login.status_code == 200
    item = client.get("/api/admin/payments").json()["items"][0]
    assert item["id"] == request_id
    assert item["transferDate"] == "1405/08/05"
    assert item["phone"] == ""
    receipt_response = client.get(f"/api/admin/payments/{request_id}/receipt")
    assert receipt_response.status_code == 200
    assert receipt_response.content == b"fake-png"
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


def test_mobile_admin_session_bypasses_assessment_quotas_without_spending_credits(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    mobile = TestClient(app)
    login = mobile.post("/api/admin/auth/mobile-login", json={"username": "owner", "password": ADMIN_PASSWORD})
    assert login.status_code == 200
    body = login.json()
    assert body["authenticated"] is True
    assert body["username"] == "owner"
    assert body["expiresAt"] > 0
    token = body["accessToken"]
    assert not mobile.cookies
    auth = {"Authorization": f"Bearer {token}"}
    assert mobile.get("/api/admin/auth/me", headers=auth).json() == {"authenticated": True, "username": "owner"}
    assert mobile.get("/api/admin/payments", headers=auth).status_code == 200
    for _ in range(5):
        result = mobile.post(f"/api/payments/consume/{INSTALL}", headers=auth)
        assert result.status_code == 200
        assert result.json()["consumed"] == "admin"
    assert mobile.get(f"/api/payments/credits/{INSTALL}").json() == {"freeRemaining": 2, "paidCredits": 0}
    regular = TestClient(app)
    assert regular.post(f"/api/payments/consume/{INSTALL}").json()["consumed"] == "free"
    assert regular.post(f"/api/payments/consume/{INSTALL}").json()["consumed"] == "free"
    assert regular.post(f"/api/payments/consume/{INSTALL}").status_code == 402
    assert mobile.post("/api/admin/auth/logout", headers=auth).status_code == 200
    assert mobile.get("/api/admin/auth/me", headers=auth).status_code == 401


def test_receipt_submission_needs_review_security_but_not_server_card_configuration(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    monkeypatch.delenv("PAYMENT_CARD_NUMBER", raising=False)
    monkeypatch.delenv("PAYMENT_CARD_HOLDER", raising=False)
    monkeypatch.delenv("PAYMENT_BANK_NAME", raising=False)
    assert client.get("/api/payments/config").json()["enabled"] is False
    response = client.post(
        "/api/payments/requests",
        data={"install_id": INSTALL, "sku": "assessment_1", "transfer_date": "1405/08/05", "tracking_code": "TRX-CARDLESS"},
        files={"receipt": ("receipt.png", b"fake-png", "image/png")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "pending"
    assert client.get(f"/api/payments/credits/{INSTALL}").json()["paidCredits"] == 0


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


def _bazaar_signed_request(private_key, install_id=INSTALL, sku="assessment_3", order_id="bazaar-order-1"):
    import base64
    import json
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    purchase = {
        "orderId": order_id,
        "purchaseToken": f"token-{order_id}",
        "developerPayload": install_id,
        "packageName": "ai.visayar.app",
        "purchaseState": 0,
        "purchaseTime": 1_798_000_000_000,
        "productId": sku,
    }
    purchase_data = json.dumps(purchase, separators=(",", ":"))
    signature = private_key.sign(purchase_data.encode(), padding.PKCS1v15(), hashes.SHA1())
    return {
        "installId": install_id,
        "purchaseData": purchase_data,
        "dataSignature": base64.b64encode(signature).decode(),
    }


def test_bazaar_signed_purchase_grants_credits_idempotently(monkeypatch, tmp_path):
    import base64
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from backend.app import payments

    configure(monkeypatch, tmp_path)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_der = private_key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    monkeypatch.setattr(payments, "BAZAAR_RSA_PUBLIC_KEY", base64.b64encode(public_der).decode())
    body = _bazaar_signed_request(private_key)

    invalid = {**body, "dataSignature": base64.b64encode(b"not-a-valid-rsa-signature").decode()}
    assert client.post("/api/payments/bazaar/purchases", json=invalid).status_code == 403
    assert client.get(f"/api/payments/credits/{INSTALL}").json()["paidCredits"] == 0

    first = client.post("/api/payments/bazaar/purchases", json=body)
    assert first.status_code == 200, first.text
    assert first.json() == {
        "status": "granted",
        "creditsAdded": 3,
        "serverCredited": True,
        "freeRemaining": 2,
        "paidCredits": 3,
        "orderId": "bazaar-order-1",
    }
    retry = client.post("/api/payments/bazaar/purchases", json=body)
    assert retry.status_code == 200, retry.text
    assert retry.json()["status"] == "already_granted"
    assert retry.json()["creditsAdded"] == 0
    assert retry.json()["serverCredited"] is True
    assert retry.json()["paidCredits"] == 3

    assert client.post(f"/api/payments/consume/{INSTALL}").json()["consumed"] == "free"
    assert client.post(f"/api/payments/consume/{INSTALL}").json()["consumed"] == "free"
    assert client.post(f"/api/payments/consume/{INSTALL}").json()["consumed"] == "paid"
    assert client.get(f"/api/payments/credits/{INSTALL}").json()["paidCredits"] == 2


def test_bazaar_client_credited_purchase_is_recorded_without_granting(monkeypatch, tmp_path):
    """App-credited purchases (Bazaar guide flow) must never touch the server ledger."""
    import base64
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from backend.app import payments

    configure(monkeypatch, tmp_path)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_der = private_key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    monkeypatch.setattr(payments, "BAZAAR_RSA_PUBLIC_KEY", base64.b64encode(public_der).decode())

    body = _bazaar_signed_request(private_key, order_id="bazaar-order-local")
    body["clientCredited"] = True
    first = client.post("/api/payments/bazaar/purchases", json=body)
    assert first.status_code == 200, first.text
    assert first.json() == {
        "status": "recorded",
        "creditsAdded": 0,
        "serverCredited": False,
        "freeRemaining": 2,
        "paidCredits": 0,
        "orderId": "bazaar-order-local",
    }
    assert client.get(f"/api/payments/credits/{INSTALL}").json()["paidCredits"] == 0

    retry = client.post("/api/payments/bazaar/purchases", json=body)
    assert retry.status_code == 200, retry.text
    assert retry.json()["status"] == "already_granted"
    assert retry.json()["creditsAdded"] == 0
    assert retry.json()["serverCredited"] is False
    assert client.get(f"/api/payments/credits/{INSTALL}").json()["paidCredits"] == 0

    # A legacy registration (no clientCredited flag) for a different order still
    # grants once and reports the server ledger as the owner.
    legacy = _bazaar_signed_request(private_key, order_id="bazaar-order-legacy")
    legacy_first = client.post("/api/payments/bazaar/purchases", json=legacy)
    assert legacy_first.status_code == 200, legacy_first.text
    assert legacy_first.json()["status"] == "granted"
    assert legacy_first.json()["serverCredited"] is True
    assert client.get(f"/api/payments/credits/{INSTALL}").json()["paidCredits"] == 3


def test_bazaar_purchase_requires_matching_app_install_and_known_sku(monkeypatch, tmp_path):
    import base64
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from backend.app import payments

    configure(monkeypatch, tmp_path)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_der = private_key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    monkeypatch.setattr(payments, "BAZAAR_RSA_PUBLIC_KEY", base64.b64encode(public_der).decode())

    another_install = "ea355b30-302c-4604-bdca-3bd798ad618b"
    mismatched = _bazaar_signed_request(private_key, install_id=another_install)
    mismatched["installId"] = INSTALL
    assert client.post("/api/payments/bazaar/purchases", json=mismatched).status_code == 403
    assert client.get(f"/api/payments/credits/{INSTALL}").json()["paidCredits"] == 0

    unknown = _bazaar_signed_request(private_key, sku="assessment_unlisted", order_id="bazaar-order-unknown")
    assert client.post("/api/payments/bazaar/purchases", json=unknown).status_code == 422
    assert client.get(f"/api/payments/credits/{INSTALL}").json()["paidCredits"] == 0


def test_configured_bazaar_public_key_is_valid_rsa_der():
    import base64
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
    from backend.app.payments import BAZAAR_RSA_PUBLIC_KEY

    key = serialization.load_der_public_key(base64.b64decode(BAZAAR_RSA_PUBLIC_KEY, validate=True))
    assert isinstance(key, RSAPublicKey)
    assert key.key_size >= 1024
