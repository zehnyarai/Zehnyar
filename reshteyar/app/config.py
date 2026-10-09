"""تنظیمات برنامه از متغیرهای محیطی (فایل .env.example را ببینید).

اصل: پیش‌فرض‌ها امن‌اند. اگر APP_ENV تنظیم نشود، برنامه در حالت production اجرا می‌شود
(کوکی امن، پرداخت آزمایشی خاموش، زرین‌پال روی درگاه واقعی). حالت توسعه باید صریح باشد.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = Path(__file__).resolve().parent / "static"


class ConfigError(RuntimeError):
    """تنظیمات ناامن یا ناقص برای محیط اجرا."""


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _app_env() -> str:
    return os.getenv("APP_ENV", "production").strip().lower() or "production"


@dataclass(frozen=True)
class Settings:
    app_env: str = _app_env()
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
    database_path: Path = Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "app.db")))
    cutoffs_path: Path = Path(os.getenv("CUTOFFS_PATH", str(DATA_DIR / "cutoffs.csv")))

    zarinpal_merchant_id: str = os.getenv("ZARINPAL_MERCHANT_ID", "").strip()
    zarinpal_sandbox: bool = _env_bool("ZARINPAL_SANDBOX", default=_app_env() != "production")
    # حالت آزمایشی (بدون پرداخت واقعی). در production فقط با این پرچم فعال می‌شود.
    allow_mock_payments: bool = _env_bool("ALLOW_MOCK_PAYMENTS", default=False)

    admin_user: str = os.getenv("ADMIN_USER", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "")

    free_results_limit: int = int(os.getenv("FREE_RESULTS_LIMIT", "5"))
    cookie_secure: bool = _env_bool("COOKIE_SECURE", default=_app_env() == "production")
    # فقط وقتی پشت reverse proxy مطمئن هستید فعال کنید؛ در غیر این صورت هدر X-Forwarded-For جعلی است
    trust_proxy_headers: bool = _env_bool("TRUST_PROXY_HEADERS", default=False)

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()


def validate_settings(cfg: Settings = settings) -> None:
    """خطاهای پیکربندی را هنگام راه‌اندازی گزارش می‌کند؛ در production جلوی اجرای ناامن را می‌گیرد."""
    if cfg.app_env not in {"production", "development", "test"}:
        raise ConfigError("APP_ENV باید production، development یا test باشد.")
    if cfg.is_production:
        if cfg.allow_mock_payments:
            raise ConfigError("ALLOW_MOCK_PAYMENTS=1 در production مجاز نیست؛ پرداخت آزمایشی فروش را بی‌اعتبار می‌کند.")
        if cfg.admin_password and len(cfg.admin_password) < 12:
            raise ConfigError("ADMIN_PASSWORD باید حداقل ۱۲ کاراکتر باشد.")
        if not cfg.public_base_url.startswith("https://"):
            raise ConfigError("PUBLIC_BASE_URL در production باید با https:// شروع شود.")
        if cfg.zarinpal_merchant_id and cfg.zarinpal_sandbox:
            # هشدار نه خطا: ممکن است عمداً در محیط آزمایشی زرین‌پال تست شود
            import logging
            logging.getLogger("rz").warning("ZARINPAL_SANDBOX=1 در production: پرداخت واقعی انجام نمی‌شود.")


def payment_mode() -> str:
    """یکی از: zarinpal | mock | unavailable"""
    if settings.zarinpal_merchant_id:
        return "zarinpal"
    if not settings.is_production or settings.allow_mock_payments:
        return "mock"
    return "unavailable"
