"""Manual transfer payment requests and admin-reviewed assessment credits.

Prices are authoritative here (never accepted from the mobile client). Set
PAYMENT_CARD_NUMBER, PAYMENT_CARD_HOLDER, PAYMENT_BANK_NAME and
PAYMENT_ADMIN_TOKEN in the deployment environment before enabling purchases.
"""
from __future__ import annotations

import os
import re
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/payments", tags=["payments"])
ADMIN_PREFIX = "/api/admin/payments"
ADMIN = APIRouter(prefix=ADMIN_PREFIX, tags=["payment administration"])
PACKAGES = {
    "assessment_1": {"credits": 1, "priceToman": 600_000, "labelFa": "یک ارزیابی", "labelEn": "1 assessment", "discountPercent": 0},
    "assessment_3": {"credits": 3, "priceToman": 1_500_000, "labelFa": "سه ارزیابی", "labelEn": "3 assessments", "discountPercent": 17},
    "assessment_6": {"credits": 6, "priceToman": 2_700_000, "labelFa": "شش ارزیابی", "labelEn": "6 assessments", "discountPercent": 25},
    "assessment_12": {"credits": 12, "priceToman": 4_800_000, "labelFa": "دوازده ارزیابی", "labelEn": "12 assessments", "discountPercent": 33},
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
    """)
    return db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _install_id(value: str) -> str:
    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(422, "Invalid installation identifier")


def _admin_guard(token: Optional[str]) -> None:
    expected = os.getenv("PAYMENT_ADMIN_TOKEN", "")
    if not expected:
        raise HTTPException(503, "Payment administration is not configured")
    if not token or not secrets.compare_digest(token, expected):
        raise HTTPException(403, "Administrator authentication failed")


def _ensure_customer(db: sqlite3.Connection, install_id: str) -> None:
    db.execute(
        "INSERT OR IGNORE INTO customers(install_id,free_used,credits,updated_at) VALUES(?,0,0,?)",
        (install_id, _now()),
    )


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
    raw_card = os.getenv("PAYMENT_CARD_NUMBER", "")
    digits = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    card_number = re.sub(r"\D", "", raw_card.translate(digits))
    admin_secret = os.getenv("PAYMENT_ADMIN_TOKEN", "")
    enabled = (
        len(card_number) == 16
        and bool(os.getenv("PAYMENT_CARD_HOLDER", "").strip())
        and bool(os.getenv("PAYMENT_BANK_NAME", "").strip())
        and len(admin_secret) >= 32
    )
    return {
        "enabled": enabled,
        "freeAssessments": 2,
        "currency": "TOMAN",
        "packages": [{"sku": sku, **item} for sku, item in PACKAGES.items()],
        "card": ({
            "number": card_number,
            "holder": os.getenv("PAYMENT_CARD_HOLDER", "").strip(),
            "bank": os.getenv("PAYMENT_BANK_NAME", "").strip(),
        } if enabled else None),
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
def admin_list(token: Optional[str] = Header(None, alias="X-Admin-Token"), status: str = "pending"):
    _admin_guard(token)
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
def admin_receipt(request_id: str, token: Optional[str] = Header(None, alias="X-Admin-Token")):
    _admin_guard(token)
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
def admin_approve(request_id: str, token: Optional[str] = Header(None, alias="X-Admin-Token")):
    _admin_guard(token)
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
def admin_reject(request_id: str, token: Optional[str] = Header(None, alias="X-Admin-Token")):
    _admin_guard(token)
    db = _db()
    try:
        cur = db.execute("UPDATE payment_requests SET status='rejected',reviewed_at=? WHERE id=? AND status='pending'", (_now(), request_id))
        if cur.rowcount == 0:
            raise HTTPException(404, "Pending payment request not found")
        db.commit()
        return {"status": "rejected"}
    finally:
        db.close()
