"""موتور ارزیابی استرالیا: ویزاهای ۱۸۹، ۱۹۰ و ۴۹۱."""
from __future__ import annotations

from datetime import date

from app.engine.base import (
    build_costs,
    documents_score,
    estimate_readiness,
    factor,
    finish_result,
    gap,
    program_meta,
)
from app.engine.types import ProgramResult
from app.formatting import education_label
from app.engine.utils import age_on, english_test_band
from app.schemas import Profile

PROGRAM_IDS = {"189": "au-189", "190": "au-190", "491": "au-491"}

def _age_points(age: int) -> int:
    if 18 <= age <= 24:
        return 25
    if 25 <= age <= 32:
        return 30
    if 33 <= age <= 39:
        return 25
    if 40 <= age <= 44:
        return 15
    return 0


def _english_points(band: str) -> int:
    return {"superior": 20, "proficient": 10, "competent": 0}.get(band, 0)


def _overseas_points(years: float) -> int:
    if years >= 8:
        return 15
    if years >= 5:
        return 10
    if years >= 3:
        return 5
    return 0


def _australian_points(years: float) -> int:
    if years >= 8:
        return 20
    if years >= 5:
        return 15
    if years >= 3:
        return 10
    if years >= 1:
        return 5
    return 0


def _education_points(profile: Profile) -> int:
    if profile.education_level == "phd":
        return 20
    if profile.education_level in {"bachelor", "master", "two_or_more"}:
        return 15
    if profile.education_level in {"diploma1", "diploma2"}:
        return 10
    return 0


def assess(profile: Profile, subclass: str = "189", rule_date: date | None = None) -> ProgramResult:
    rule_date = rule_date or date.today()
    program_id = PROGRAM_IDS[subclass]
    meta = program_meta(program_id)
    age = age_on(profile.birth_date, rule_date)
    gaps = []

    band = english_test_band(profile.english)
    points = _age_points(age) + _english_points(band)

    overseas_years = max(0.0, profile.experience_last10 - profile.australian_experience_years)
    points += _overseas_points(overseas_years)
    points += _australian_points(profile.australian_experience_years)
    points += _education_points(profile)

    if profile.education_field == "stem" and profile.education_level == "phd":
        points += 10
    if profile.education_country == "AU":
        points += 5

    # شریک زندگی
    spouse_points = 10
    if profile.spouse_included:
        spouse_ok = (
            profile.spouse_education in {"bachelor", "master", "phd", "two_or_more"}
            and english_test_band(profile.spouse_english) in {"competent", "proficient", "superior"}
        )
        spouse_points = 10 if spouse_ok else 5
    points += spouse_points

    # نامزدی
    if subclass == "190":
        points += 5
    elif subclass == "491":
        points += 15

    if age >= 45:
        gaps.append(
            gap(
                "age",
                "سقف سنی ۴۵ سال",
                "blocker",
                "برای ویزاهای مهارتی استرالیا باید در زمان دعوت‌نامه زیر ۴۵ سال باشید.",
                "مسیرهای کارفرمایی یا سرمایه‌گذاری را بررسی کنید؛ سقف سنی این ویزاها قابل تمدید نیست.",
                30,
            )
        )
    if band == "below":
        gaps.append(
            gap(
                "english",
                "انگلیسی حداقل Competent",
                "blocker",
                "حداقل آیلتس ۶ در هر مهارت (یا معادل) لازم است.",
                "آزمون آیلتس/PTE بدهید؛ نمره‌ی ۷ در هر مهارت ۱۰ و نمره‌ی ۸ در هر مهارت ۲۰ امتیاز می‌دهد.",
                20,
            )
        )
    elif band in {"competent", "proficient"}:
        gaps.append(
            gap(
                "english_upgrade",
                "ارتقای زبان انگلیسی",
                "minor",
                f"سطح فعلی: {band}؛ هر سطح بالاتر تا ۱۰ امتیاز اضافه می‌کند.",
                "با آیلتس ۸ در هر مهارت به ۲۰ امتیاز کامل زبان می‌رسید.",
                8,
            )
        )
    if not profile.skills_assessment:
        gaps.append(
            gap(
                "skills_assessment",
                "ارزیابی مهارت (Skills Assessment)",
                "major",
                "بدون ارزیابی مثبت سازمان ارزیابی کننده، درخواست معتبر نیست.",
                "سازمان ارزیابی رشته‌ی خود را پیدا کنید (مثلاً ACS برای IT، Engineers Australia برای مهندسی) و مدارک را ارسال کنید.",
                14,
            )
        )
    if points < 65:
        gaps.append(
            gap(
                "points",
                "حداقل ۶۵ امتیاز",
                "blocker",
                f"امتیاز فعلی {points} است؛ حداقل قانونی ۶۵ است.",
                "زبان، سابقه‌ی کار، مدرک یا نامزدی ایالتی (۵ یا ۱۵ امتیاز) را تقویت کنید.",
                20,
            )
        )
    if points >= 65 and points < 75:
        gaps.append(
            gap(
                "competition",
                "رقابت در دعوت‌نامه",
                "major",
                f"امتیاز {points} برای حداقل قانونی کافی است، اما در دورهای اخیر ۱۸۹ معمولاً بالای ۷۵ بوده است.",
                "نامزدی ایالتی ۱۹۰ (۵ امتیاز) یا منطقه‌ای ۴۹۱ (۱۵ امتیاز) را جدی بگیرید؛ یا انگلیسی Superior و سابقه‌ی بیشتر.",
                12,
            )
        )

    blockers = [g for g in gaps if g.severity == "blocker"]
    if blockers:
        status = "ineligible"
    elif not profile.skills_assessment or points < 75:
        status = "potential"
    else:
        status = "eligible"

    if points >= 85:
        score_band, band_label = "strong", "قوی"
    elif points >= 75:
        score_band, band_label = "moderate", "متوسط"
    elif points >= 65:
        score_band, band_label = "competitive", "حداقلی"
    else:
        score_band, band_label = "weak", "ناکافی"

    factors = [
        factor("age", "سن", f"{age} سال", _age_points(age), 30),
        factor("english", "زبان انگلیسی", {"superior": "Superior", "proficient": "Proficient", "competent": "Competent"}.get(band, "زیر حداقل"), _english_points(band), 20),
        factor("overseas", "سابقه‌ی کار خارج از استرالیا", f"{overseas_years:g} سال", _overseas_points(overseas_years), 15),
        factor("australian", "سابقه‌ی کار در استرالیا", f"{profile.australian_experience_years:g} سال", _australian_points(profile.australian_experience_years), 20),
        factor("education", "تحصیلات", education_label(profile.education_level), _education_points(profile), 20),
        factor("partner", "وضعیت شریک زندگی", "همراه" if profile.spouse_included else "مجرد", spouse_points, 10),
        factor("nomination", "نامزدی", "ایالتی" if subclass == "190" else "منطقه‌ای" if subclass == "491" else "بدون نامزدی", 5 if subclass == "190" else 15 if subclass == "491" else 0, 15),
        factor("total", "جمع امتیاز", str(points), points, None),
    ]

    costs, total_eur = build_costs(meta, profile)
    docs = documents_score(profile, needs_eca=False)
    readiness = estimate_readiness(status, points / 65, gaps, docs)

    highlights = []
    if band == "superior":
        highlights.append("انگلیسی Superior: ۲۰ امتیاز کامل زبان.")
    if subclass == "190":
        highlights.append("نامزدی ایالتی ۵ امتیاز اضافه می‌کند و شانس دعوت‌نامه را بالا می‌برد.")
    if subclass == "491":
        highlights.append("نامزدی منطقه‌ای ۱۵ امتیاز اضافه می‌کند؛ مسیر اقامت دائم از ویزای ۱۹۱ است.")
    if profile.australian_experience_years:
        highlights.append("سابقه‌ی کار در استرالیا بیشترین امتیاز به‌ازای هر سال را دارد.")

    summary = f"امتیاز تخمینی شما {points} از حداقل ۶۵ است."
    if subclass == "491":
        summary += " این ویزا موقت است و اقامت دائم از مسیر ۱۹۱ می‌گذرد."

    return finish_result(
        meta,
        status=status,
        readiness=readiness,
        summary=summary,
        factors=factors,
        gaps=gaps,
        costs=costs,
        total_cost_eur=total_eur,
        score=points,
        score_threshold=65,
        score_unit="امتیاز",
        score_note="حداقل قانونی ۶۵ امتیاز است؛ دعوت‌نامه‌های واقعی معمولاً بالاتر هستند.",
        band=score_band,
        band_label=band_label,
        highlights=highlights,
    )
