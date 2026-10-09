"""پایگاه داده‌ی SQLite (کتابخانه‌ی استاندارد) برای پرداخت‌ها و لایسنس‌ها."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,
    amount_toman INTEGER NOT NULL,
    gateway TEXT NOT NULL,
    authority TEXT UNIQUE,
    status TEXT NOT NULL,
    ref_id TEXT,
    buyer_mobile TEXT,
    buyer_email TEXT,
    result_token TEXT NOT NULL UNIQUE,
    message TEXT,
    created_at TEXT NOT NULL,
    paid_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);

CREATE TABLE IF NOT EXISTS licenses (
    code TEXT PRIMARY KEY,
    payment_id INTEGER UNIQUE REFERENCES payments(id),
    plan_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
"""


def connect() -> sqlite3.Connection:
    path = settings.database_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=15, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 15000")
    return conn


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA)
