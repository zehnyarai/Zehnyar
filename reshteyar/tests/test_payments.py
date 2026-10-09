import json
from dataclasses import replace

import httpx
import pytest

from app import config, payments
from app.config import payment_mode, settings
from app.db import db, init_db
from app.licensing import find_active_license
from app.catalog import Catalog

catalog = Catalog()
PLAN = next(p for p in catalog.plans if p["id"] == "month")


@pytest.fixture(autouse=True)
def _fresh_db():
    init_db()
    with db() as conn:
        conn.execute("DELETE FROM licenses")
        conn.execute("DELETE FROM payments")
    yield


def _zarinpal_transport(handler):
    return httpx.MockTransport(handler)


def test_zarinpal_request_sends_rial_and_builds_startpay_url():
    seen = {}

    def handler(request: httpx.Request):
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"data": {"code": 100, "message": "Success", "authority": "A0000000001"}, "errors": []})

    gw = payments.ZarinpalGateway("m" * 36, sandbox=True, transport=_zarinpal_transport(handler))
    req = gw.request(amount_toman=249000, description="test", callback_url="http://x/cb", mobile="09123456789", order_id=7)
    assert seen["url"] == "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
    assert seen["body"]["amount"] == 2490000  # ریال
    assert seen["body"]["metadata"]["mobile"] == "09123456789"
    assert req.redirect_url == "https://sandbox.zarinpal.com/pg/StartPay/A0000000001"


def test_zarinpal_production_host_and_error_message():
    def handler(request):
        return httpx.Response(200, json={"data": [], "errors": {"code": -9, "message": "Validation error"}})

    gw = payments.ZarinpalGateway("m" * 36, sandbox=False, transport=_zarinpal_transport(handler))
    with pytest.raises(payments.PaymentError, match="Validation error"):
        gw.request(amount_toman=99000, description="t", callback_url="http://x/cb")
    assert gw.base == "https://payment.zarinpal.com"


@pytest.mark.parametrize("code,ok", [(100, True), (101, True), (-54, False)])
def test_zarinpal_verify_codes(code, ok):
    def handler(request):
        body = json.loads(request.content)
        assert body["amount"] == 990000 and body["authority"] == "AUTH"
        return httpx.Response(200, json={"data": {"code": code, "ref_id": 123, "message": "m"}, "errors": []})

    gw = payments.ZarinpalGateway("m" * 36, sandbox=True, transport=_zarinpal_transport(handler))
    assert gw.verify(amount_toman=99000, authority="AUTH").ok is ok


def test_callback_is_idempotent_and_uses_db_amount():
    calls = []

    class FakeGateway:
        name = "zarinpal"

        def request(self, **kw):
            return payments.GatewayRequest("AUTH-IDEMP", "https://pg/startpay")

        def verify(self, *, amount_toman, authority):
            calls.append(amount_toman)
            return payments.VerifyResult(True, "REF1", 100, "ok")

    gw = FakeGateway()
    with db() as conn:
        url, token = payments.create_payment(conn, gw, PLAN, mobile=None, email=None, callback_url="http://x/cb")
        first = payments.handle_callback(conn, gw, catalog.plans, "AUTH-IDEMP", "OK")
        second = payments.handle_callback(conn, gw, catalog.plans, "AUTH-IDEMP", "OK")
        assert first["state"] == "paid" and second["state"] == "paid"
        assert first["code"] == second["code"] and first["code"].startswith("RZ-")
        assert calls == [PLAN["price_toman"]]  # callback دوم بدون verify مجدد، همان کد را برمی‌گرداند
        lic = find_active_license(conn, first["code"])
        assert lic is not None and lic["plan_id"] == "month"


def test_canceled_payment_issues_no_license():
    class GW:
        name = "zarinpal"

        def request(self, **kw):
            return payments.GatewayRequest("AUTH-NOK", "x")

        def verify(self, **kw):
            raise AssertionError("نباید برای پرداخت لغوشده verify شود")

    with db() as conn:
        payments.create_payment(conn, GW(), PLAN, mobile=None, email=None, callback_url="x")
        res = payments.handle_callback(conn, GW(), catalog.plans, "AUTH-NOK", "NOK")
        assert res["state"] == "canceled" and res["code"] is None
        assert conn.execute("SELECT COUNT(*) FROM licenses").fetchone()[0] == 0


def test_payment_mode_rules(monkeypatch):
    monkeypatch.setattr(config, "settings", replace(settings, app_env="production", zarinpal_merchant_id="",
                                                    allow_mock_payments=False))
    assert payment_mode() == "unavailable"
    monkeypatch.setattr(config, "settings", replace(settings, app_env="production", zarinpal_merchant_id="",
                                                    allow_mock_payments=True))
    assert payment_mode() == "mock"
    monkeypatch.setattr(config, "settings", replace(settings, app_env="production", zarinpal_merchant_id="M" * 36))
    assert payment_mode() == "zarinpal"
