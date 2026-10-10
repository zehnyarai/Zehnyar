import hashlib
import hmac
import secrets
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from time import monotonic
from fastapi import HTTPException

# Keep the existing cookie name so a display rebrand does not invalidate sessions.
SESSION_COOKIE = "pesteyar_session"
# Single-process pilot limit; use a shared limiter before scaling to >1 worker.
ATTEMPTS = defaultdict(deque)


def password_hash(password):
    salt = secrets.token_hex(16)
    value = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return f"scrypt${salt}${value}"


def check_password(password, encoded):
    if not encoded:
        # Do not turn unknown users into an inexpensive account-enumeration path.
        password_hash(password)
        return False
    try:
        scheme, salt, expected = encoded.split("$")
        if scheme != "scrypt":
            return False
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def new_session(db, user_id, response, secure=False):
    token = secrets.token_urlsafe(48)
    expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    db.execute("DELETE FROM sessions WHERE expires_at < ?", (datetime.now(timezone.utc).isoformat(),))
    db.execute("INSERT INTO sessions VALUES (?,?,?)", (token_hash(token), user_id, expires))
    response.set_cookie(SESSION_COOKIE, token, max_age=30 * 86400, httponly=True, secure=secure, samesite="lax", path="/")


def rate_limit(key, limit, period):
    time = monotonic()
    bucket = ATTEMPTS[key]
    while bucket and bucket[0] <= time - period:
        bucket.popleft()
    if len(bucket) >= limit:
        raise HTTPException(429, "درخواست‌های زیادی ثبت شده است؛ کمی بعد دوباره تلاش کنید.")
    bucket.append(time)
    # Bound memory for long-running pilots with many guest sessions / addresses.
    if len(ATTEMPTS) > 10000:
        stale = [k for k, v in ATTEMPTS.items() if not v or v[-1] < time - 3600]
        for k in stale:
            ATTEMPTS.pop(k, None)
