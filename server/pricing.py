"""Explicit owner pricing in USD, converted from a dated, manually sourced rate.

No guessed/live exchange feed. All payable amounts are integer TOMAN. Each
receipt pins an immutable quote; a later rate edit never changes its price.
"""
import json
import os
from datetime import datetime, date, time, timedelta
from decimal import Decimal, ROUND_CEILING
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .database import connect, now_iso, uid

PACKAGE_IDS = {"trial", "season", "large"}


def iran_today():
    return datetime.now(ZoneInfo("Asia/Tehran")).date()


def pricing_mode():
    # Fixed sample prices are retained only for explicitly selected legacy mode.
    return "fixed" if os.getenv("BILLING_PRICING_MODE", "usd").lower() == "fixed" else "usd"


class PricingInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    receiving_requested: bool = Field(default=False, strict=True)
    confirmed: bool = Field(default=False, strict=True)
    rate_toman_per_usd: Decimal | None = Field(default=None, gt=0, le=10_000_000, max_digits=11, decimal_places=2)
    rate_date: date | None = None
    source: str = Field(default="", max_length=160)
    source_url: str = Field(default="", max_length=500)
    usd_prices: dict[str, Decimal] = Field(default_factory=dict, max_length=3)

    @field_validator("rate_toman_per_usd", mode="before")
    @classmethod
    def not_boolean(cls, value):
        if isinstance(value, bool):
            raise ValueError("Rate cannot be a boolean")
        return value

    @field_validator("usd_prices", mode="before")
    @classmethod
    def price_values(cls, values):
        if not isinstance(values, dict) or any(isinstance(v, bool) for v in values.values()):
            raise ValueError("Invalid USD values")
        return values

    @field_validator("usd_prices")
    @classmethod
    def bounded_prices(cls, values):
        if set(values) - PACKAGE_IDS or any(not v.is_finite() or v <= 0 or v > 1000 or v.as_tuple().exponent < -2 for v in values.values()):
            raise ValueError("USD prices must be positive amounts with up to two decimal places")
        return values

    @field_validator("source_url")
    @classmethod
    def source_link(cls, value):
        if value:
            url = urlparse(value)
            if url.scheme != "https" or not url.hostname or url.username or url.password:
                raise ValueError("Source link must be HTTPS, not an instruction or an API to fetch")
        return value

    @field_validator("rate_date")
    @classmethod
    def no_future_quote(cls, value):
        if value and value > iran_today():
            raise ValueError("Cannot date an exchange quote in the future")
        return value


EMPTY_PRICING = PricingInput()


def ready(data):
    return bool(data.confirmed and data.rate_toman_per_usd and data.rate_date == iran_today() and data.source and set(data.usd_prices) == PACKAGE_IDS)


def amount_toman(usd, rate):
    # Displayed rounding rule: upward to the nearest 1,000 toman. No float money.
    return int((usd * rate / Decimal(1000)).to_integral_value(rounding=ROUND_CEILING) * 1000)


def latest(db):
    row = db.execute("SELECT * FROM billing_price_quotes ORDER BY sequence DESC LIMIT 1").fetchone()
    return (row["id"], PricingInput.model_validate_json(row["data"])) if row else ("", EMPTY_PRICING)


def pricing_config(db, packages):
    if pricing_mode() == "fixed":
        return {"mode": "fixed", "ready": True, "receiving_requested": os.getenv("MANUAL_PAYMENTS_ENABLED", "false").lower() == "true", "quote_id": "", "packages": packages, "notice": "قیمت ثابت؛ حالت قدیمی صریحاً انتخاب شده است."}
    quote_id, data = latest(db)
    valid = ready(data)
    result = data.model_dump(mode="json")
    result['expires_at'] = datetime.combine(iran_today() + timedelta(days=1), time.min, ZoneInfo('Asia/Tehran')).isoformat() if valid else None
    result.update({"mode": "usd", "ready": valid, "quote_id": quote_id, "today": str(iran_today()), "rounding": "up-to-1000-toman", "notice": "نرخ ثبت‌شده مدیر، نه فید خودکار دلار. نرخ باید هر روز تهران با ذکر منبع تأیید شود؛ گرد کردن رو به بالا تا هزار تومان."})
    result["packages"] = [{**p, "price_usd": str(data.usd_prices[p["id"]]) if p["id"] in data.usd_prices else None, "price_toman": amount_toman(data.usd_prices[p["id"]], data.rate_toman_per_usd) if valid else None} for p in packages]
    return result


def receipt_quote(db, package_id, quote_id, packages):
    if pricing_mode() == "fixed":
        p = next((p for p in packages if p["id"] == package_id), None)
        if not p:
            raise HTTPException(422, "بسته معتبر نیست.")
        return p, {"mode": "fixed", "price_toman": p["price_toman"]}
    row = db.execute("SELECT data FROM billing_price_quotes WHERE id=?", (quote_id,)).fetchone()
    if not row:
        raise HTTPException(409, "پیشنهاد قیمت معتبر انتخاب نشده است؛ قیمت‌ها را دوباره بررسی کنید. واریز دوباره انجام ندهید.")
    data = PricingInput.model_validate_json(row["data"])
    # Only today's confirmed quotes; older deposits need manual reconciliation,
    # never a second deposit or an automatic reprice/credit allocation.
    if not ready(data):
        raise HTTPException(409, "نرخ این پیشنهاد مربوط به امروز یا کامل نیست؛ برای واریز قبلی با مدیر تطبیق دهید و دوباره واریز نکنید.")
    p = next((p for p in packages if p["id"] == package_id), None)
    if not p:
        raise HTTPException(422, "بسته معتبر نیست.")
    amount = amount_toman(data.usd_prices[package_id], data.rate_toman_per_usd)
    return {**p, "price_toman": amount}, {"mode": "usd", "quote_id": quote_id, "price_usd": str(data.usd_prices[package_id]), "rate_toman_per_usd": str(data.rate_toman_per_usd), "rate_date": str(data.rate_date), "source": data.source, "source_url": data.source_url, "price_toman": amount, "rounding": "up-to-1000-toman"}


def store_quote(db, data):
    quote_id = uid()
    db.execute("INSERT INTO billing_price_quotes (id,data,created_at) VALUES (?,?,?)", (quote_id, data.model_dump_json(), now_iso()))
    return quote_id


def register_pricing_routes(app, require_admin, packages, audit):
    @app.get("/api/billing/admin/pricing")
    def admin_pricing(request: Request):
        with connect() as db:
            require_admin(request, db)
            return pricing_config(db, packages)

    @app.put("/api/billing/admin/pricing")
    def save_pricing(data: PricingInput, request: Request):
        with connect() as db:
            admin = require_admin(request, db)
            if data.confirmed and not ready(data):
                raise HTTPException(422, "برای تأیید قیمت، هر سه مبلغ دلاری، نرخ تومان، تاریخ امروز تهران و منبع واقعی لازم‌اند.")
            quote_id = store_quote(db, data)
            audit(db, admin["id"], "usd_pricing_updated", quote_id)
            return pricing_config(db, packages)
