"""Connection evidence, never a claim of scientific accuracy.

A key/model configuration is not a successful photo request. Readiness is
recorded only after the provider returns a validated image response and expires
or changes when the configured provider/model/key changes. No secret is exposed.
"""
import hashlib
from datetime import datetime, timedelta, timezone

from .database import connect, now_iso

MAX_AGE = timedelta(hours=24)


def identity(settings):
    provider, model, key = settings
    return hashlib.sha256((provider + '\0' + model + '\0' + key).encode()).hexdigest()


def record(settings, succeeded):
    with connect() as db:
        db.execute("INSERT INTO vision_connection (id,identity,succeeded,checked_at) VALUES (1,?,?,?) ON CONFLICT(id) DO UPDATE SET identity=excluded.identity,succeeded=excluded.succeeded,checked_at=excluded.checked_at", (identity(settings), int(succeeded), now_iso()))


def status(settings, configured):
    result = {"vision_verified": False, "vision_checked_at": None, "vision_connection_state": "unconfigured" if not configured else "untested", "vision_scientifically_validated": False}
    if not configured:
        return result
    with connect() as db:
        row = db.execute("SELECT * FROM vision_connection WHERE id=1").fetchone()
    if not row or row['identity'] != identity(settings):
        return result
    checked = datetime.fromisoformat(row['checked_at'])
    age = datetime.now(timezone.utc) - checked
    result['vision_checked_at'] = row['checked_at']
    if age < timedelta(0) or age > MAX_AGE:
        result['vision_connection_state'] = 'expired'
    else:
        result['vision_connection_state'] = 'responded' if row['succeeded'] else 'failed'
        result['vision_verified'] = bool(row['succeeded'])
    return result
