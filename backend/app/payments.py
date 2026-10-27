"""Manual transfer payments, secure admin sessions, and assessment credits.

Prices are authoritative here (never accepted from the mobile client). Admin
credentials are provisioned via environment; managed secrets are encrypted at rest.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit

from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/payments", tags=["payments"])
ADMIN_PREFIX = "/api/admin/payments"
ADMIN = APIRouter(prefix=ADMIN_PREFIX, tags=["payment administration"])
AUTH = APIRouter(prefix="/api/admin/auth", tags=["admin authentication"])
SETTINGS = APIRouter(prefix="/api/admin/settings", tags=["admin settings"])
ADMIN_COOKIE = "visayar_admin_session"
SESSION_TTL_SECONDS = 12 * 60 * 60
LOGIN_FAILURES: dict[str, list[float]] = {}


class AdminLogin(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class GeminiKeyUpdate(BaseModel):
    apiKey: str = Field(min_length=20, max_length=512)


class PaymentCardUpdate(BaseModel):
    number: str = Field(min_length=16, max_length=32)
    holder: str = Field(min_length=2, max_length=120)
    bank: str = Field(min_length=2, max_length=80)
PACKAGES = {
    "assessment_1": {"credits": 1, "priceToman": 600_000, "labelFa": "یک ارزیابی", "labelEn": "1 assessment"},
    "assessment_3": {"credits": 3, "priceToman": 1_800_000, "labelFa": "سه ارزیابی", "labelEn": "3 assessments"},
    "assessment_6": {"credits": 6, "priceToman": 3_600_000, "labelFa": "شش ارزیابی", "labelEn": "6 assessments"},
    "assessment_12": {"credits": 12, "priceToman": 7_200_000, "labelFa": "دوازده ارزیابی", "labelEn": "12 assessments"},
}
MAX_RECEIPT_BYTES = 5 * 1024 * 1024
ALLOWED_RECEIPT_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def _root() -> Path:
    return Path(os.getenv("PAYMENTS_DATA_DIR", Path.cwd() / "data")).resolve()


def _db() -> sqlite3.Connection:
    root = _root()
    root.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(root / "payments.sqlite3", timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            install_id TEXT PRIMARY KEY,
            free_used INTEGER NOT NULL DEFAULT 0,
            credits INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS payment_requests (
            id TEXT PRIMARY KEY,
            install_id TEXT NOT NULL,
            sku TEXT NOT NULL,
            credits INTEGER NOT NULL,
            price_toman INTEGER NOT NULL,
            phone TEXT NOT NULL,
            tracking_code TEXT NOT NULL,
            receipt_filename TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            reviewed_at TEXT,
            FOREIGN KEY(install_id) REFERENCES customers(install_id)
        );
        CREATE UNIQUE INDEX IF NOT EXISTS payment_tracking_unique
            ON payment_requests(tracking_code);
        CREATE TABLE IF NOT EXISTS admin_sessions (
            token_hash TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            expires_at INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS admin_settings (
            setting_key TEXT PRIMARY KEY,
            encrypted_value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    return db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _install_id(value: str) -> str:
    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(422, "Invalid installation identifier")


def make_password_hash(password: str, iterations: int = 310_000) -> str:
    """Create the PBKDF2 format used by VISAYAR_ADMIN_PASSWORD_HASH."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def _password_hash_is_valid(encoded: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = encoded.split("$", 3)
        return (
            algorithm == "pbkdf2_sha256"
            and 100_000 <= int(rounds) <= 1_000_000
            and bool(re.fullmatch(r"[0-9a-f]{32}", salt_hex))
            and bool(re.fullmatch(r"[0-9a-f]{64}", digest_hex))
        )
    except (ValueError, TypeError):
        return False


def _verify_password(password: str, encoded: str) -> bool:
    try:
        if not _password_hash_is_valid(encoded):
            return False
        algorithm, rounds, salt_hex, expected_hex = encoded.split("$", 3)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(rounds))
        return hmac.compare_digest(digest.hex(), expected_hex)
    except (ValueError, TypeError):
        return False


def _admin_auth_configured() -> bool:
    username = os.getenv("VISAYAR_ADMIN_USERNAME", "").strip()
    encoded = os.getenv("VISAYAR_ADMIN_PASSWORD_HASH", "")
    return bool(username and _password_hash_is_valid(encoded))


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _login_allowed(request: Request) -> bool:
    now = time.time()
    attempts = [at for at in LOGIN_FAILURES.get(_client_key(request), []) if now - at < 900]
    LOGIN_FAILURES[_client_key(request)] = attempts
    return len(attempts) < 8


def _record_login_failure(request: Request) -> None:
    LOGIN_FAILURES.setdefault(_client_key(request), []).append(time.time())


def _check_same_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    host = request.headers.get("host", "").lower()
    if origin and urlsplit(origin).netloc.lower() != host:
        raise HTTPException(403, "Cross-origin admin request rejected")


def _session_user(request: Request) -> Optional[str]:
    token = request.cookies.get(ADMIN_COOKIE)
    if not token:
        return None
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    db = _db()
    try:
        row = db.execute("SELECT username,expires_at FROM admin_sessions WHERE token_hash=?", (digest,)).fetchone()
        if not row:
            return None
        if row["expires_at"] <= int(time.time()):
            db.execute("DELETE FROM admin_sessions WHERE token_hash=?", (digest,))
            db.commit()
            return None
        return row["username"]
    finally:
        db.close()


def _admin_guard(request: Request) -> str:
    _check_same_origin(request)
    username = _session_user(request)
    if username:
        return username
    if not _admin_auth_configured():
        raise HTTPException(503, "Admin account is not configured")
    raise HTTPException(401, "Admin login required")


def _require_session(request: Request) -> str:
    _check_same_origin(request)
    username = _session_user(request)
    if not username:
        raise HTTPException(401, "Admin login required")
    return username


def _fernet():
    key = os.getenv("VISAYAR_ENCRYPTION_KEY", "").strip()
    if not key:
        return None
    try:
        from cryptography.fernet import Fernet
        return Fernet(key.encode("ascii"))
    except (ImportError, ValueError, UnicodeEncodeError):
        return None


def _get_setting(name: str) -> Optional[str]:
    fernet = _fernet()
    if fernet is None:
        return None
    db = _db()
    try:
        row = db.execute("SELECT encrypted_value FROM admin_settings WHERE setting_key=?", (name,)).fetchone()
        if not row:
            return None
        try:
            return fernet.decrypt(row["encrypted_value"].encode("ascii")).decode("utf-8")
        except Exception:
            return None
    finally:
        db.close()


def _set_setting(name: str, value: str) -> None:
    fernet = _fernet()
    if fernet is None:
        raise HTTPException(503, "VISAYAR_ENCRYPTION_KEY is missing or invalid")
    encrypted = fernet.encrypt(value.encode("utf-8")).decode("ascii")
    db = _db()
    try:
        db.execute(
            "INSERT INTO admin_settings(setting_key,encrypted_value,updated_at) VALUES(?,?,?) "
            "ON CONFLICT(setting_key) DO UPDATE SET encrypted_value=excluded.encrypted_value,updated_at=excluded.updated_at",
            (name, encrypted, _now()),
        )
        db.commit()
    finally:
        db.close()


def _delete_setting(name: str) -> None:
    db = _db()
    try:
        db.execute("DELETE FROM admin_settings WHERE setting_key=?", (name,))
        db.commit()
    finally:
        db.close()


def get_gemini_api_key() -> Optional[str]:
    """Return the Gemini key only to backend code; never expose it via an API response."""
    return _get_setting("gemini_api_key") or os.getenv("GEMINI_API_KEY")


def _stored_or_environment(name: str, env_name: str) -> str:
    return _get_setting(name) or os.getenv(env_name, "").strip()


def _ensure_customer(db: sqlite3.Connection, install_id: str) -> None:
    db.execute(
        "INSERT OR IGNORE INTO customers(install_id,free_used,credits,updated_at) VALUES(?,0,0,?)",
        (install_id, _now()),
    )


@AUTH.post("/login")
def admin_login(payload: AdminLogin, request: Request, response: Response):
    _check_same_origin(request)
    username = os.getenv("VISAYAR_ADMIN_USERNAME", "").strip()
    password_hash = os.getenv("VISAYAR_ADMIN_PASSWORD_HASH", "")
    if not username or not _password_hash_is_valid(password_hash):
        raise HTTPException(503, "Username/password admin login is not configured")
    if not _login_allowed(request):
        raise HTTPException(429, "Too many login attempts; try again later")
    if not secrets.compare_digest(payload.username, username) or not _verify_password(payload.password, password_hash):
        _record_login_failure(request)
        raise HTTPException(401, "Invalid username or password")

    token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    db = _db()
    try:
        db.execute("DELETE FROM admin_sessions WHERE expires_at<=?", (int(time.time()),))
        db.execute(
            "INSERT INTO admin_sessions(token_hash,username,expires_at,created_at) VALUES(?,?,?,?)",
            (token_hash, username, int(time.time()) + SESSION_TTL_SECONDS, _now()),
        )
        db.commit()
    finally:
        db.close()
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    secure_cookie = request.url.scheme == "https" or forwarded_proto.split(",")[0].strip() == "https"
    response.set_cookie(
        ADMIN_COOKIE, token, max_age=SESSION_TTL_SECONDS, httponly=True,
        secure=secure_cookie, samesite="strict", path="/api/admin",
    )
    return {"authenticated": True, "username": username}


@AUTH.get("/me")
def admin_me(request: Request):
    username = _session_user(request)
    if not username:
        raise HTTPException(401, "Admin login required")
    return {"authenticated": True, "username": username}


@AUTH.post("/logout")
def admin_logout(request: Request, response: Response):
    _check_same_origin(request)
    token = request.cookies.get(ADMIN_COOKIE)
    if token:
        db = _db()
        try:
            db.execute("DELETE FROM admin_sessions WHERE token_hash=?", (hashlib.sha256(token.encode("utf-8")).hexdigest(),))
            db.commit()
        finally:
            db.close()
    response.delete_cookie(ADMIN_COOKIE, path="/api/admin", httponly=True, samesite="strict")
    return {"authenticated": False}


@SETTINGS.get("")
def get_admin_settings(request: Request):
    _require_session(request)
    card_number = _stored_or_environment("payment_card_number", "PAYMENT_CARD_NUMBER")
    translated = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    card_number = re.sub(r"\D", "", card_number.translate(translated))
    api_key = get_gemini_api_key()
    return {
        "geminiConfigured": bool(api_key),
        "geminiMasked": ("••••" + api_key[-4:]) if api_key else "",
        "card": {
            "number": card_number,
            "holder": _stored_or_environment("payment_card_holder", "PAYMENT_CARD_HOLDER"),
            "bank": _stored_or_environment("payment_bank_name", "PAYMENT_BANK_NAME"),
        },
        "encryptionConfigured": _fernet() is not None,
    }


@SETTINGS.put("/gemini")
def update_gemini_key(payload: GeminiKeyUpdate, request: Request):
    _require_session(request)
    key = payload.apiKey.strip()
    if not key.startswith("AIza") or not re.fullmatch(r"[A-Za-z0-9_-]{20,512}", key):
        raise HTTPException(422, "Invalid Gemini API key format")
    _set_setting("gemini_api_key", key)
    return {"saved": True, "masked": "••••" + key[-4:]}


@SETTINGS.delete("/gemini")
def delete_gemini_key(request: Request):
    _require_session(request)
    _delete_setting("gemini_api_key")
    return {"saved": True, "configured": False}


@SETTINGS.put("/payment-card")
def update_payment_card(payload: PaymentCardUpdate, request: Request):
    _require_session(request)
    digits = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    number = re.sub(r"\D", "", payload.number.translate(digits))
    if len(number) != 16:
        raise HTTPException(422, "Card number must contain 16 digits")
    if not payload.holder.strip() or not payload.bank.strip():
        raise HTTPException(422, "Card holder and bank are required")
    for name, value in (
        ("payment_card_number", number),
        ("payment_card_holder", payload.holder.strip()),
        ("payment_bank_name", payload.bank.strip()),
    ):
        _set_setting(name, value)
    return {"saved": True, "lastFour": number[-4:]}


def _request_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"], "installId": row["install_id"], "sku": row["sku"],
        "credits": row["credits"], "priceToman": row["price_toman"],
        "phone": row["phone"], "trackingCode": row["tracking_code"],
        "status": row["status"], "createdAt": row["created_at"],
        "reviewedAt": row["reviewed_at"],
    }


@router.get("/config")
def payment_config():
    raw_card = _stored_or_environment("payment_card_number", "PAYMENT_CARD_NUMBER")
    digits = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    card_number = re.sub(r"\D", "", raw_card.translate(digits))
    holder = _stored_or_environment("payment_card_holder", "PAYMENT_CARD_HOLDER")
    bank = _stored_or_environment("payment_bank_name", "PAYMENT_BANK_NAME")
    enabled = len(card_number) == 16 and bool(holder) and bool(bank) and _admin_auth_configured()
    return {
        "enabled": enabled,
        "freeAssessments": 2,
        "currency": "TOMAN",
        "packages": [{"sku": sku, **item} for sku, item in PACKAGES.items()],
        "card": ({"number": card_number, "holder": holder, "bank": bank} if enabled else None),
    }


@router.get("/credits/{install_id}")
def credits(install_id: str):
    install_id = _install_id(install_id)
    db = _db()
    try:
        _ensure_customer(db, install_id)
        db.commit()
        row = db.execute("SELECT free_used,credits FROM customers WHERE install_id=?", (install_id,)).fetchone()
        return {"freeRemaining": max(0, 2 - row["free_used"]), "paidCredits": row["credits"]}
    finally:
        db.close()


@router.post("/consume/{install_id}")
def consume_credit(install_id: str):
    """Consume a free assessment first, then an approved paid credit."""
    install_id = _install_id(install_id)
    db = _db()
    try:
        db.execute("BEGIN IMMEDIATE")
        _ensure_customer(db, install_id)
        row = db.execute("SELECT free_used,credits FROM customers WHERE install_id=?", (install_id,)).fetchone()
        if row["free_used"] < 2:
            db.execute("UPDATE customers SET free_used=free_used+1,updated_at=? WHERE install_id=?", (_now(), install_id))
            kind = "free"
        elif row["credits"] > 0:
            db.execute("UPDATE customers SET credits=credits-1,updated_at=? WHERE install_id=?", (_now(), install_id))
            kind = "paid"
        else:
            db.rollback()
            raise HTTPException(402, "No assessment credits remaining")
        db.commit()
        updated = db.execute("SELECT free_used,credits FROM customers WHERE install_id=?", (install_id,)).fetchone()
        return {"consumed": kind, "freeRemaining": max(0, 2-updated["free_used"]), "paidCredits": updated["credits"]}
    finally:
        db.close()


@router.post("/requests")
async def submit_payment_request(
    install_id: str = Form(...),
    sku: str = Form(...),
    phone: str = Form(...),
    tracking_code: str = Form(...),
    receipt: UploadFile = File(...),
):
    config = payment_config()
    if not config["enabled"]:
        raise HTTPException(503, "Manual payment is not configured")
    install_id = _install_id(install_id)
    package = PACKAGES.get(sku)
    if not package:
        raise HTTPException(422, "Unknown package")
    digit_translation = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    clean_phone = re.sub(r"[\s()+-]", "", phone.translate(digit_translation))
    if not re.fullmatch(r"\d{10,15}", clean_phone):
        raise HTTPException(422, "Enter a valid mobile number")
    clean_tracking = re.sub(r"\s+", "", tracking_code)
    if not re.fullmatch(r"[\w\-]{4,80}", clean_tracking, flags=re.UNICODE):
        raise HTTPException(422, "Enter a valid bank transfer reference")
    ext = ALLOWED_RECEIPT_TYPES.get(receipt.content_type or "")
    if not ext:
        raise HTTPException(415, "Receipt must be a JPEG, PNG or WebP image")
    content = await receipt.read(MAX_RECEIPT_BYTES + 1)
    if not content or len(content) > MAX_RECEIPT_BYTES:
        raise HTTPException(413, "Receipt image must be between 1 byte and 5 MB")
    request_id = str(uuid.uuid4())
    filename = f"{request_id}{ext}"
    receipt_dir = _root() / "receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / filename).write_bytes(content)
    db = _db()
    try:
        _ensure_customer(db, install_id)
        db.execute(
            "INSERT INTO payment_requests(id,install_id,sku,credits,price_toman,phone,tracking_code,receipt_filename,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (request_id, install_id, sku, package["credits"], package["priceToman"], clean_phone,
             clean_tracking, filename, "pending", _now()),
        )
        db.commit()
        return {"requestId": request_id, "status": "pending", "credits": package["credits"], "priceToman": package["priceToman"]}
    except sqlite3.IntegrityError:
        (receipt_dir / filename).unlink(missing_ok=True)
        raise HTTPException(409, "This transfer reference has already been submitted")
    finally:
        db.close()


@router.get("/requests/{request_id}")
def payment_request_status(request_id: str, install_id: str):
    install_id = _install_id(install_id)
    db = _db()
    try:
        row = db.execute("SELECT * FROM payment_requests WHERE id=? AND install_id=?", (request_id, install_id)).fetchone()
        if not row:
            raise HTTPException(404, "Payment request not found")
        return _request_dict(row)
    finally:
        db.close()


@ADMIN.get("")
def admin_list(request: Request, status: str = "pending"):
    _admin_guard(request)
    if status not in {"pending", "approved", "rejected", "all"}:
        raise HTTPException(422, "Invalid status")
    db = _db()
    try:
        query = "SELECT * FROM payment_requests" + ("" if status == "all" else " WHERE status=?") + " ORDER BY created_at DESC"
        rows = db.execute(query, () if status == "all" else (status,)).fetchall()
        return {"items": [_request_dict(row) for row in rows]}
    finally:
        db.close()


@ADMIN.get("/{request_id}/receipt")
def admin_receipt(request_id: str, request: Request):
    _admin_guard(request)
    db = _db()
    try:
        row = db.execute("SELECT receipt_filename FROM payment_requests WHERE id=?", (request_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Payment request not found")
        receipt_path = _root() / "receipts" / row["receipt_filename"]
        if not receipt_path.is_file():
            raise HTTPException(404, "Receipt file not found")
        return FileResponse(receipt_path)
    finally:
        db.close()


@ADMIN.post("/{request_id}/approve")
def admin_approve(request_id: str, request: Request):
    _admin_guard(request)
    db = _db()
    try:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM payment_requests WHERE id=?", (request_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Payment request not found")
        if row["status"] == "approved":
            return {"status": "approved", "creditsGranted": row["credits"]}
        if row["status"] != "pending":
            raise HTTPException(409, "Only pending requests can be approved")
        _ensure_customer(db, row["install_id"])
        db.execute("UPDATE customers SET credits=credits+?,updated_at=? WHERE install_id=?", (row["credits"], _now(), row["install_id"]))
        db.execute("UPDATE payment_requests SET status='approved',reviewed_at=? WHERE id=?", (_now(), request_id))
        db.commit()
        return {"status": "approved", "creditsGranted": row["credits"]}
    finally:
        db.close()


@ADMIN.post("/{request_id}/reject")
def admin_reject(request_id: str, request: Request):
    _admin_guard(request)
    db = _db()
    try:
        cur = db.execute("UPDATE payment_requests SET status='rejected',reviewed_at=? WHERE id=? AND status='pending'", (_now(), request_id))
        if cur.rowcount == 0:
            raise HTTPException(404, "Pending payment request not found")
        db.commit()
        return {"status": "rejected"}
    finally:
        db.close()
