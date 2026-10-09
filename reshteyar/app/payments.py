"""
پرداخت به تومان. مبلغ‌ها در دیتابیس به تومان ذخیره می‌شوند و
درگاه زرین‌پال مبلغ را به ریال می‌خواهد (تومان × ۱۰).

حالت‌ها (از config.payment_mode):
  * zarinpal   : ZARINPAL_MERCHANT_ID تنظیم شده؛ ZARINPAL_SANDBOX=1 یعنی محیط آزمایشی زرین‌پال
  * mock       : بدون مرچنت، فقط در محیط توسعه یا با ALLOW_MOCK_PAYMENTS=1؛ پرداخت واقعی انجام نمی‌شود
  * unavailable: در production بدون مرچنت؛ خرید غیرفعال است
"""
from __future__ import annotations

import logging
import re
import secrets
import sqlite3
from contextlib import contextmanager
from typing import Iterator

import httpx

from .config import payment_mode, settings
from .licensing import issue_license, to_iso, utcnow

ZARINPAL_PRODUCTION = "https://payment.zarinpal.com"
ZARINPAL_SANDBOX = "https://sandbox.zarinpal.com"
MOBILE_RE = re.compile(r"^09\d{9}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


log = logging.getLogger("rz.payments")

MOCK_APPROVED = "mock_approved"


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """قفل نوشتن از ابتدا (BEGIN IMMEDIATE) تا دو callback هم‌زمان دو کد صادر نکنند."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")


class PaymentError(Exception):
    """خطای قابل نمایش به کاربر."""


class GatewayRequest:
    def __init__(self, authority: str, redirect_url: str) -> None:
        self.authority = authority
        self.redirect_url = redirect_url


class VerifyResult:
    def __init__(self, ok: bool, ref_id: str | None, code: int | None, message: str) -> None:
        self.ok = ok
        self.ref_id = ref_id
        self.code = code
        self.message = message


def _zarinpal_error(data) -> str:
    if isinstance(data, dict):
        errors = data.get("errors")
        if isinstance(errors, dict) and errors.get("message"):
            return f"خطای درگاه: {errors['message']}"
        payload = data.get("data")
        if isinstance(payload, dict) and payload.get("message"):
            return f"خطای درگاه: {payload['message']}"
    return "پرداخت انجام نشد؛ در صورت کسر وجه، با پشتیبانی تماس بگیرید."


class ZarinpalGateway:
    """کلاینت ساده‌ی زرین‌پال نسخه‌ی ۴ (request.json / StartPay / verify.json)."""

    name = "zarinpal"

    def __init__(self, merchant_id: str, sandbox: bool, transport: httpx.BaseTransport | None = None) -> None:
        self.merchant_id = merchant_id
        self.base = ZARINPAL_SANDBOX if sandbox else ZARINPAL_PRODUCTION
        self._client = httpx.Client(timeout=15.0, transport=transport,
                                    headers={"Accept": "application/json"})

    def _post(self, path: str, body: dict) -> dict:
        try:
            response = self._client.post(self.base + path, json=body)
        except httpx.HTTPError as exc:
            raise PaymentError("ارتباط با درگاه پرداخت برقرار نشد؛ لطفاً دوباره تلاش کنید.") from exc
        try:
            data = response.json()
        except ValueError as exc:
            raise PaymentError("پاسخ نامعتبر از درگاه پرداخت دریافت شد.") from exc
        return data if isinstance(data, dict) else {}

    def request(self, *, amount_toman: int, description: str, callback_url: str,
                mobile: str | None = None, email: str | None = None,
                order_id: int | None = None) -> GatewayRequest:
        body: dict = {
            "merchant_id": self.merchant_id,
            "amount": int(amount_toman) * 10,  # ریال
            "callback_url": callback_url,
            "description": description[:255],
        }
        metadata = {k: v for k, v in {"mobile": mobile, "email": email,
                                      "order_id": str(order_id) if order_id else None}.items() if v}
        if metadata:
            body["metadata"] = metadata
        data = self._post("/pg/v4/payment/request.json", body)
        payload = data.get("data") if isinstance(data.get("data"), dict) else {}
        if payload.get("code") == 100 and payload.get("authority"):
            authority = str(payload["authority"])
            return GatewayRequest(authority, f"{self.base}/pg/StartPay/{authority}")
        raise PaymentError(_zarinpal_error(data))

    def verify(self, *, amount_toman: int, authority: str) -> VerifyResult:
        body = {"merchant_id": self.merchant_id, "amount": int(amount_toman) * 10, "authority": authority}
        data = self._post("/pg/v4/payment/verify.json", body)
        payload = data.get("data") if isinstance(data.get("data"), dict) else {}
        code = payload.get("code")
        if code == 100:
            return VerifyResult(True, str(payload.get("ref_id") or ""), code, "پرداخت با موفقیت تایید شد.")
        if code == 101:  # قبلاً تایید شده؛ همان نتیجه‌ی موفق
            return VerifyResult(True, str(payload.get("ref_id") or ""), code, "این پرداخت قبلاً تایید شده است.")
        return VerifyResult(False, None, code, _zarinpal_error(data))


class MockGateway:
    """درگاه آزمایشی: فقط برای توسعه و تست. هیچ پولی جابه‌جا نمی‌شود."""

    name = "mock"

    def request(self, *, amount_toman: int, description: str, callback_url: str,
                mobile: str | None = None, email: str | None = None,
                order_id: int | None = None) -> GatewayRequest:
        authority = "MOCK" + secrets.token_hex(12).upper()
        return GatewayRequest(authority, f"/premium/mock/{authority}")

    def verify(self, *, amount_toman: int, authority: str) -> VerifyResult:
        # فقط وقتی فراخوانی می‌شود که handle_callback تأیید کاربر در دیتابیس را دیده باشد
        return VerifyResult(True, "MOCK-" + authority[-8:], 100, "پرداخت آزمایشی تایید شد (بدون پول واقعی).")


def get_gateway(transport: httpx.BaseTransport | None = None):
    mode = payment_mode()
    if mode == "zarinpal":
        return ZarinpalGateway(settings.zarinpal_merchant_id, settings.zarinpal_sandbox, transport)
    if mode == "mock":
        return MockGateway()
    raise PaymentError("درگاه پرداخت هنوز پیکربندی نشده است.")


def find_plan(plans: list[dict], plan_id: str) -> dict | None:
    return next((p for p in plans if p["id"] == plan_id), None)


def create_payment(conn: sqlite3.Connection, gateway, plan: dict, *, mobile: str | None,
                   email: str | None, callback_url: str) -> tuple[str, str]:
    """ثبت پرداخت در دیتابیس و درخواست به درگاه. خروجی: (redirect_url, result_token)."""
    token = secrets.token_urlsafe(18)
    cur = conn.execute(
        "INSERT INTO payments (plan_id, amount_toman, gateway, status, result_token, buyer_mobile, "
        "buyer_email, created_at) VALUES (?, ?, ?, 'created', ?, ?, ?, ?)",
        (plan["id"], plan["price_toman"], gateway.name, token, mobile, email, to_iso(utcnow())),
    )
    payment_id = cur.lastrowid
    try:
        req = gateway.request(amount_toman=plan["price_toman"], description=f"رشته‌یار - {plan['title']}",
                              callback_url=callback_url, mobile=mobile, email=email, order_id=payment_id)
    except PaymentError as exc:
        conn.execute("UPDATE payments SET status = 'failed', message = ? WHERE id = ?", (str(exc), payment_id))
        raise
    conn.execute("UPDATE payments SET authority = ? WHERE id = ?", (req.authority, payment_id))
    return req.redirect_url, token


def mock_confirm(conn: sqlite3.Connection, authority: str, approve: bool) -> bool:
    """ثبت تصمیم کاربر در صفحه‌ی درگاه آزمایشی. فقط برای پرداخت‌های در وضعیت created."""
    status = MOCK_APPROVED if approve else "canceled"
    cur = conn.execute(
        "UPDATE payments SET status = ?, message = ? WHERE authority = ? AND gateway = 'mock' AND status = 'created'",
        (status, "تایید در درگاه آزمایشی" if approve else "لغو در درگاه آزمایشی", authority),
    )
    return cur.rowcount == 1


def handle_callback(conn: sqlite3.Connection, gateway, plans: list[dict], authority: str,
                    status: str) -> dict:
    """
    پاسخ درگاه (Authority, Status) را پردازش می‌کند.

    قواعد امنیتی:
      * مبلغ همیشه از دیتابیس خوانده می‌شود، نه از پارامترهای بازگشتی.
      * در حالت آزمایشی، پارامتر Status نادیده گرفته می‌شود و فقط تصمیم ثبت‌شده در دیتابیس معتبر است.
      * کد لایسنس فقط یک‌بار صادر می‌شود؛ callback تکراری همان کد را برمی‌گرداند.
    """
    with transaction(conn):
        row = conn.execute("SELECT * FROM payments WHERE authority = ?", (authority,)).fetchone()
        if row is None:
            return {"state": "unknown", "token": None, "code": None}
        base = {"token": row["result_token"], "payment_id": row["id"]}

        if row["status"] == "paid":
            code = conn.execute("SELECT code FROM licenses WHERE payment_id = ?", (row["id"],)).fetchone()
            return {**base, "state": "paid", "code": code["code"] if code else None}

        if gateway.name == "mock":
            if row["status"] == "canceled":
                return {**base, "state": "canceled", "code": None}
            if row["status"] != MOCK_APPROVED:
                # هنوز کاربر در صفحه‌ی آزمایشی تأیید نکرده؛ هیچ کدی صادر نمی‌شود
                return {**base, "state": "pending", "code": None,
                        "message": "پرداخت هنوز توسط کاربر تایید نشده است."}
        else:
            if (status or "").upper() != "OK":
                conn.execute("UPDATE payments SET status = 'canceled', message = ? WHERE id = ?",
                             ("پرداخت توسط کاربر لغو شد یا ناموفق بود.", row["id"]))
                log.info("payment %s canceled by user/gateway", row["id"])
                return {**base, "state": "canceled", "code": None}

        plan = find_plan(plans, row["plan_id"])
        if plan is None:
            return {**base, "state": "failed", "code": None}

        try:
            result = gateway.verify(amount_toman=row["amount_toman"], authority=authority)
        except PaymentError as exc:
            conn.execute("UPDATE payments SET message = ? WHERE id = ?", (str(exc), row["id"]))
            log.warning("payment %s verify error: %s", row["id"], exc)
            return {**base, "state": "pending", "code": None, "message": str(exc)}

        if not result.ok:
            conn.execute("UPDATE payments SET status = 'failed', message = ? WHERE id = ?",
                         (result.message, row["id"]))
            log.warning("payment %s verify failed code=%s", row["id"], result.code)
            return {**base, "state": "failed", "code": None, "message": result.message}

        code = issue_license(conn, row["id"], plan["id"], plan["days"])
        conn.execute(
            "UPDATE payments SET status = 'paid', ref_id = ?, paid_at = ?, message = ? WHERE id = ?",
            (result.ref_id, to_iso(utcnow()), result.message, row["id"]),
        )
        log.info("payment %s paid plan=%s", row["id"], plan["id"])
        return {**base, "state": "paid", "code": code}


def payment_by_token(conn: sqlite3.Connection, token: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM payments WHERE result_token = ?", (token,)).fetchone()


def admin_stats(conn: sqlite3.Connection) -> dict:
    totals = conn.execute(
        "SELECT COUNT(*) AS n, COALESCE(SUM(amount_toman), 0) AS revenue FROM payments WHERE status = 'paid'"
    ).fetchone()
    by_status = {r["status"]: r["n"] for r in conn.execute(
        "SELECT status, COUNT(*) AS n FROM payments GROUP BY status")}
    active = conn.execute("SELECT COUNT(*) AS n FROM licenses WHERE expires_at > ?",
                          (to_iso(utcnow()),)).fetchone()["n"]
    recent = conn.execute(
        "SELECT p.*, l.code AS license_code FROM payments p LEFT JOIN licenses l ON l.payment_id = p.id "
        "ORDER BY p.id DESC LIMIT 100"
    ).fetchall()
    return {"paid_count": totals["n"], "revenue_toman": totals["revenue"], "by_status": by_status,
            "active_licenses": active, "recent": recent}
