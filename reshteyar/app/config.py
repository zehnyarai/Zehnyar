"""تنظیمات برنامه از متغیرهای محیطی (فایل .env.example را ببینید)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = Path(__file__).resolve().parent / "static"


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development").strip().lower()
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
    database_path: Path = Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "app.db")))
    cutoffs_path: Path = Path(os.getenv("CUTOFFS_PATH", str(DATA_DIR / "cutoffs.csv")))

    zarinpal_merchant_id: str = os.getenv("ZARINPAL_MERCHANT_ID", "").strip()
    zarinpal_sandbox: bool = _env_bool("ZARINPAL_SANDBOX", True)
    # حالت آزمایشی (بدون پرداخت واقعی). در production فقط با این پرچم فعال می‌شود.
    allow_mock_payments: bool = _env_bool("ALLOW_MOCK_PAYMENTS", False)

    admin_user: str = os.getenv("ADMIN_USER", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "")

    free_results_limit: int = int(os.getenv("FREE_RESULTS_LIMIT", "5"))
    cookie_secure: bool = _env_bool("COOKIE_SECURE", False)

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()


def payment_mode() -> str:
    """یکی از: zarinpal | mock | unavailable"""
    if settings.zarinpal_merchant_id:
        return "zarinpal"
    if not settings.is_production or settings.allow_mock_payments:
        return "mock"
    return "unavailable"
