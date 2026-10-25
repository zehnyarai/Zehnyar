"""تنظیمات از متغیرهای محیطی."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_VERSION = "1.0.2"


def _flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "on", "yes"}


@dataclass(frozen=True)
class Settings:
    app_name: str = "مهاجریار"
    brand_en: str = "Mohajeryar"
    tagline: str = "سامانه هوشمند انتخاب مسیر مهاجرت"
    version: str = APP_VERSION
    app_env: str = field(default_factory=lambda: os.environ.get("APP_ENV", "development"))
    database_path: str = field(
        default_factory=lambda: os.environ.get(
            "DATABASE_PATH", str(BASE_DIR.parent / "data" / "mohajeryar.db")
        )
    )
    enforce_origin: bool = field(default_factory=lambda: _flag("ENFORCE_ORIGIN", "0"))
    ai_enabled: bool = field(default_factory=lambda: os.environ.get("AI_ENABLED", "1") != "0")
    max_body_bytes: int = 1_500_000

    @property
    def production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}


settings = Settings()
