"""قالب‌بندی فارسی: اعداد، مبالغ، تاریخ شمسی."""
from __future__ import annotations

from datetime import date

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_MONTHS = [
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
]


EDUCATION_LABELS = {
    "none": "زیر دیپلم",
    "secondary": "دیپلم",
    "diploma1": "کاردانی",
    "diploma2": "کارشناسی پیوسته/دیپلم فنی",
    "bachelor": "کارشناسی",
    "master": "کارشناسی ارشد",
    "phd": "دکتری",
    "two_or_more": "دو مدرک یا بیشتر",
}


def education_label(value: str) -> str:
    return EDUCATION_LABELS.get(value, value)


def fa_digits(value: object) -> str:
    return str(value).translate(FA_DIGITS)


def fa_number(value: float | int, decimals: int = 0) -> str:
    if value is None:
        return "—"
    if decimals > 0:
        text = f"{value:,.{decimals}f}"
    else:
        text = f"{round(value):,}"
    text = text.replace(",", "٬").replace(".", "٫")
    return fa_digits(text)


def fa_money(amount: float, currency: str = "EUR", decimals: int = 0) -> str:
    symbols = {
        "EUR": "یورو",
        "USD": "دلار",
        "CAD": "دلار کانادا",
        "GBP": "پوند",
        "AUD": "دلار استرالیا",
        "NZD": "دلار نیوزیلند",
        "IRR": "تومان",
    }
    return f"{fa_number(amount, decimals)} {symbols.get(currency, currency)}"


def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple[int, int, int]:
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy - 1600
    gm2 = gm - 1
    g_day_no = 365 * gy2 + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
    g_day_no += g_d_m[gm2] + (gd - 1)
    if gm > 2 and ((gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0):
        g_day_no += 1
    j_day_no = g_day_no - 79
    j_np = j_day_no // 12053
    j_day_no %= 12053
    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
    j_day_no %= 1461
    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365
    months = [31] * 6 + [30] * 5 + [29]
    jm = 12
    for index, length in enumerate(months):
        if j_day_no < length:
            jm = index + 1
            break
        j_day_no -= length
    return jy, jm, j_day_no + 1


def fa_date(value: date | str) -> str:
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value[:10])
        except ValueError:
            return value
    jy, jm, jd = gregorian_to_jalali(value.year, value.month, value.day)
    return f"{fa_digits(jd)} {_MONTHS[jm - 1]} {fa_digits(jy)}"


def fa_percent(value: float) -> str:
    return f"{fa_digits(round(value))}٪"
