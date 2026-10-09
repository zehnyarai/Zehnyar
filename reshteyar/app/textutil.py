"""ابزارهای متن و قالب‌بندی فارسی (اعداد، پول، تاریخ شمسی)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jdatetime

_NORMALIZE = str.maketrans({
    "ي": "ی",
    "ك": "ک",
    "\u200c": " ",
    "\u200f": "",
    "\u200e": "",
    "\xad": "",
})
_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
TEHRAN_TZ = timezone(timedelta(hours=3, minutes=30))


def norm(value) -> str:
    """یکدست‌سازی برای جستجو: حروف عربی، نیم‌فاصله، حروف کوچک، فاصله‌های اضافه."""
    text = "" if value is None else str(value)
    return " ".join(text.translate(_NORMALIZE).lower().split())


def fa_digits(value) -> str:
    return str(value).translate(_FA_DIGITS)


def fa_number(value, decimals: int = 0) -> str:
    if value is None or value == "":
        return "—"
    if decimals:
        text = f"{float(value):,.{decimals}f}"
    else:
        text = f"{int(round(float(value))):,}"
    return fa_digits(text.replace(",", "٬").replace(".", "٫"))


def toman(value) -> str:
    return f"{fa_number(value)} تومان"


def jalali_datetime(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(TEHRAN_TZ)
    jd = jdatetime.datetime.fromgregorian(datetime=local.replace(tzinfo=None))
    return fa_digits(jd.strftime("%Y/%m/%d ساعت %H:%M"))


def jalali_date(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(TEHRAN_TZ)
    jd = jdatetime.datetime.fromgregorian(datetime=local.replace(tzinfo=None))
    return fa_digits(jd.strftime("%Y/%m/%d"))
