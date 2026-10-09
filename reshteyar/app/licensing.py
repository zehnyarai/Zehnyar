"""کد فعال‌سازی (لایسنس) پس از پرداخت موفق؛ اعتبار زمانی بر اساس پلن."""
from __future__ import annotations

import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

COOKIE_NAME = "rz_license"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def from_iso(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def new_code() -> str:
    raw = secrets.token_hex(8).upper()
    return "RZ-" + "-".join(raw[i:i + 4] for i in range(0, 16, 4))


def issue_license(conn: sqlite3.Connection, payment_id: int, plan_id: str, days: int) -> str:
    """برای هر پرداخت فقط یک کد صادر می‌شود (حتی اگر callback چند بار برسد)."""
    row = conn.execute("SELECT code FROM licenses WHERE payment_id = ?", (payment_id,)).fetchone()
    if row:
        return row["code"]
    now = utcnow()
    code = new_code()
    conn.execute(
        "INSERT INTO licenses (code, payment_id, plan_id, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
        (code, payment_id, plan_id, to_iso(now), to_iso(now + timedelta(days=days))),
    )
    return code


def find_active_license(conn: sqlite3.Connection, code: str | None) -> sqlite3.Row | None:
    if not code:
        return None
    row = conn.execute("SELECT * FROM licenses WHERE code = ?", (code.strip().upper(),)).fetchone()
    if row is None or from_iso(row["expires_at"]) <= utcnow():
        return None
    return row
