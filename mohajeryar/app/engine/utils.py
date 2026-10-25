"""توابع کمکی مشترک موتور: سن، زبان، ارز و آستانه‌ها."""
from __future__ import annotations

from datetime import date
from typing import Iterable, Sequence

from app.schemas import LanguageProfile

LEVEL_ORDER = ["none", "a1", "a2", "b1", "b2", "c1", "c2"]
LEVEL_LABELS = {
    "none": "بدون دانش",
    "a1": "A1",
    "a2": "A2",
    "b1": "B1",
    "b2": "B2",
    "c1": "C1",
    "c2": "C2",
}

# نرخ‌های تقریبی تبدیل ارز (فقط برای مقایسه؛ مبنای رسمی نیست)
FX_TO_EUR = {
    "EUR": 1.0,
    "USD": 0.90,
    "CAD": 0.63,
    "GBP": 1.15,
    "AUD": 0.57,
    "NZD": 0.52,
    "CHF": 1.07,
    "SEK": 0.09,
    "IRR": 0.0000015,
    "AED": 0.245,
    "TRY": 0.021,
}
CURRENCY_LABELS = {
    "EUR": "یورو",
    "USD": "دلار آمریکا",
    "CAD": "دلار کانادا",
    "GBP": "پوند",
    "AUD": "دلار استرالیا",
    "NZD": "دلار نیوزیلند",
}


def level_rank(level: str) -> int:
    try:
        return LEVEL_ORDER.index(level)
    except ValueError:
        return 0


def at_least(level: str, minimum: str) -> bool:
    return level_rank(level) >= level_rank(minimum)


def convert_to_eur(amount: float, currency: str) -> float:
    return float(amount) * FX_TO_EUR.get(currency.upper(), 1.0)


def convert(amount: float, currency: str, target: str) -> float:
    if currency.upper() == target.upper():
        return float(amount)
    eur = convert_to_eur(amount, currency)
    rate = FX_TO_EUR.get(target.upper(), 1.0)
    return eur / rate if rate else eur


def ielts_to_clb(language: LanguageProfile) -> dict[str, int]:
    """تبدیل نمره‌های آیلتس جنرال به CLB برای هر مهارت (جدول رسمی IRCC)."""
    table = {
        "listening": [(8.5, 10), (8.0, 9), (7.5, 8), (6.0, 7), (5.5, 6), (5.0, 5), (4.5, 4)],
        "reading": [(8.0, 10), (7.0, 9), (6.5, 8), (6.0, 7), (5.0, 6), (4.0, 5), (3.5, 4)],
        "writing": [(7.5, 10), (7.0, 9), (6.5, 8), (6.0, 7), (5.5, 6), (5.0, 5), (4.0, 4)],
        "speaking": [(7.5, 10), (7.0, 9), (6.5, 8), (6.0, 7), (5.5, 6), (5.0, 5), (4.0, 4)],
    }
    out: dict[str, int] = {}
    for skill, rows in table.items():
        score = getattr(language, skill)
        if score is None:
            continue
        value = 0
        for minimum, clb in rows:
            if score >= minimum:
                value = clb
                break
        out[skill] = value
    return out


def clb_from_level(level: str) -> int:
    return {"none": 0, "a1": 2, "a2": 3, "b1": 6, "b2": 7, "c1": 9, "c2": 10}.get(level, 0)


def clb_profile(language: LanguageProfile) -> tuple[dict[str, int], bool]:
    """CLB هر مهارت + این‌که آیا از نمره‌ی آزمون واقعی محاسبه شده است."""
    if language.clb:
        return {s: language.clb for s in ("listening", "reading", "writing", "speaking")}, True
    if language.test.lower() in {"ielts", "ielts_gt", "ielts-general"} and language.has_scores():
        scores = ielts_to_clb(language)
        if len(scores) == 4:
            return scores, True
    base = clb_from_level(language.level)
    return {s: base for s in ("listening", "reading", "writing", "speaking")}, False


def min_clb(language: LanguageProfile) -> int:
    skills, _ = clb_profile(language)
    return min(skills.values())


def avg_clb(language: LanguageProfile) -> float:
    skills, _ = clb_profile(language)
    return sum(skills.values()) / 4


def english_test_band(language: LanguageProfile) -> str:
    """سطح تقریبی انگلیسی برای استرالیا/بریتانیا: competent/proficient/superior."""
    if language.test.lower() == "ielts" and language.has_scores():
        lowest = min(
            language.listening or 0,
            language.reading or 0,
            language.writing or 0,
            language.speaking or 0,
        )
        if lowest >= 8:
            return "superior"
        if lowest >= 7:
            return "proficient"
        if lowest >= 6:
            return "competent"
        return "below"
    rank = level_rank(language.level)
    if rank >= 6:
        return "superior"
    if rank >= 5:
        return "proficient"
    if rank >= 4:
        return "competent"
    return "below"


def annual_salary(profile) -> tuple[float, str]:
    """حقوق سالانه‌ی پیشنهاد شغلی به ارز اصلی آن."""
    if not profile.has_job_offer:
        return 0.0, profile.job_offer_currency or "EUR"
    return float(profile.job_offer_salary or 0), (profile.job_offer_currency or "EUR").upper()


def salary_eur(profile) -> float:
    amount, currency = annual_salary(profile)
    return convert_to_eur(amount, currency)


def salary_monthly_eur(profile) -> float:
    return salary_eur(profile) / 12


def pick(points: Sequence[tuple[float, float]], value: float) -> float:
    """بازگرداندن امتیاز اولین آستانه‌ای که مقدار از آن بیشتر/مساوی است."""
    for minimum, score in points:
        if value >= minimum:
            return score
    return 0


def years_band(years: float, bands: Iterable[tuple[float, int]]) -> int:
    for minimum, points in bands:
        if years >= minimum:
            return points
    return 0


def age_on(birth_date: date, on: date | None = None) -> int:
    on = on or date.today()
    years = on.year - birth_date.year
    if (on.month, on.day) < (birth_date.month, birth_date.day):
        years -= 1
    return max(0, years)
