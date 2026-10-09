"""ابزارهای امنیتی: محدودسازی تعداد درخواست، هدرهای امنیتی، و محافظت CSRF برای درخواست‌های تغییردهنده."""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from urllib.parse import urlsplit

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .config import settings

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "form-action 'self' https://payment.zarinpal.com https://sandbox.zarinpal.com; "
    "frame-ancestors 'none'; base-uri 'self'; object-src 'none'"
)

PERMISSIONS = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"

# مسیرهایی که نباید در کش مرورگر/پراکسی بمانند (داده‌ی شخصی یا حساس)
NO_STORE_PREFIXES = ("/account", "/premium/result", "/admin", "/api/groups/", "/premium/mock/")


class RateLimiter:
    """پنجره‌ی لغزان ساده در حافظه. برای چند نمونه‌ی برنامه، Redis لازم است."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window: int) -> bool:
        """True اگر درخواست مجاز است."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > window:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def client_ip(scope: Scope) -> str:
    if settings.trust_proxy_headers:
        for name, value in scope.get("headers", []):
            if name == b"x-forwarded-for":
                return value.decode("latin-1").split(",")[0].strip() or "unknown"
    client = scope.get("client")
    return client[0] if client else "unknown"


def _host_of(origin: str) -> str:
    return urlsplit(origin).netloc.lower()


class SecurityMiddleware:
    """هدرهای امنیتی، no-store برای صفحات حساس، و رد درخواست‌های تغییردهنده‌ی cross-origin."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET").upper()
        path = scope.get("path", "")
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}

        if method in UNSAFE_METHODS and not self._same_origin(headers):
            await _plain_response(send, 403, "درخواست از منبع دیگری رد شد.")
            return

        no_store = path.startswith(NO_STORE_PREFIXES)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                hdrs = list(message.get("headers", []))
                extra = {
                    b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"DENY",
                    b"referrer-policy": b"strict-origin-when-cross-origin",
                    b"permissions-policy": PERMISSIONS.encode(),
                    b"content-security-policy": CSP.encode(),
                    b"cross-origin-opener-policy": b"same-origin",
                }
                if settings.cookie_secure:
                    extra[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains"
                if no_store:
                    extra[b"cache-control"] = b"no-store, private"
                existing = {k.lower() for k, _ in hdrs}
                for k, v in extra.items():
                    if k not in existing:
                        hdrs.append((k, v))
                message["headers"] = hdrs
            await send(message)

        await self.app(scope, receive, send_wrapper)

    @staticmethod
    def _same_origin(headers: dict[str, str]) -> bool:
        site = headers.get("sec-fetch-site")
        if site == "cross-site":
            return False
        origin = headers.get("origin")
        if origin is None or origin == "null":
            # بدون Origin (مثلاً فرم‌های قدیمی یا ابزارهای CLI): اگر Sec-Fetch-Site هم نبود، مجاز
            return origin is None or site in (None, "same-origin", "same-site", "none")
        allowed = {h.lower() for h in (headers.get("host", ""), headers.get("x-forwarded-host", "")) if h}
        return _host_of(origin) in allowed


async def _plain_response(send: Send, status: int, text: str) -> None:
    body = text.encode("utf-8")
    await send({"type": "http.response.start", "status": status,
                "headers": [(b"content-type", b"text/plain; charset=utf-8"),
                            (b"content-length", str(len(body)).encode()),
                            (b"cache-control", b"no-store")]})
    await send({"type": "http.response.body", "body": body})
