"""موتور ارزیابی نیوزیلند: Skilled Migrant Category (SMC)."""
from __future__ import annotations

from datetime import date

from app.engine.base import (
    build_costs,
    documents_score,
    estimate_readiness,
    factor,
    finish_result,
    gap,
    local_offer,
    program_meta,
)
from app.engine.types import ProgramResult
from app.engine.utils import age_on, at_least, convert
from app.schemas import Profile

PROGRAM_ID = "nz-smc"

MEDIAN_HOURLY = 35.00  # از ۹ مارس ۲۰۲۶
ANNUAL_HOURS = 2080
MEDIAN_ANNUAL = MEDIAN_HOURLY * ANNUAL_HOURS  # 72,800
POINTS_REQUIRED = 6


def _qualification_points(profile: Profile) -> int:
    level = profile.nz_qualification_level
    if not level:
        level = {
            "phd": 10,
            "master": 9,
            "bachelor": 7,
            "two_or_more": 7,
            "diploma2": 6,
            "diploma1": 4,
        }.get(profile.education_level, 0)
    points = {10: 6, 9: 5, 8: 4, 7: 3}.get(level, 0)
    if points and profile.education_country == "NZ":
        points = min(6, points + 1)
    return points


def _registration_points(years: float) -> int:
    if years >= 6:
        return 6
    if years >= 5:
        return 5
    if years >= 4:
        return 4
    if years >= 3:
        return 3
    return 0


def _income_points(hourly: float) -> int:
    if hourly >= MEDIAN_HOURLY * 3:
        return 6
    if hourly >= MEDIAN_HOURLY * 2:
        return 4
    if hourly >= MEDIAN_HOURLY * 1.5:
        return 3
    return 0


def assess(profile: Profile, rule_date: date | None = None) -> ProgramResult:
    meta = program_meta(PROGRAM_ID)
    rule_date = rule_date or date.today()
    age = age_on(profile.birth_date, rule_date)
    gaps = []
    offer_local, offer_issue = local_offer(profile, "NZ")

    salary_nzd = (
        convert(profile.job_offer_salary, profile.job_offer_currency, "NZD")
        if offer_local
        else 0.0
    )
    hourly = salary_nzd / ANNUAL_HOURS if salary_nzd else 0.0

    qualification = _qualification_points(profile)
    registration = _registration_points(profile.registration_years)
    income = _income_points(hourly)
    primary = max(qualification, registration, income)
    experience = min(3, int(profile.nz_experience_years))
    total = primary + experience

    if not offer_local:
        gaps.append(
            gap(
                "job_offer",
                "پیشنهاد شغلی در نیوزیلند",
                "blocker",
                "SMC بدون شغل یا پیشنهاد شغلی در نیوزیلند امکان‌پذیر نیست."
                + (" پیشنهاد فعلی شما برای کشور دیگری است." if offer_issue == "other" else ""),
                "شغل در نیوزیلند پیدا کنید؛ کارفرما باید Accredited Employer باشد.",
                30,
            )
        )
    if offer_local and salary_nzd < MEDIAN_ANNUAL:
        gaps.append(
            gap(
                "salary",
                "دستمزد حداقل میانه",
                "blocker",
                f"حقوق سالانه {salary_nzd:,.0f} دلار نیوزیلند است؛ حداقل برای مشاغل سطح ۱ تا ۳ برابر {MEDIAN_ANNUAL:,.0f} دلار (ساعتی ۳۵ دلار) است.",
                "حقوق بالاتر مذاکره کنید یا شغلی در سطح مهارتی ۱ تا ۳ بگیرید.",
                22,
            )
        )
    if age > 55:
        gaps.append(
            gap(
                "age",
                "سقف سنی ۵۵ سال",
                "blocker",
                "برای SMC باید ۵۵ سال یا کمتر باشید.",
                "مسیرهای سرمایه‌گذاری یا خانوادگی را بررسی کنید.",
                26,
            )
        )
    if total < 6:
        gaps.append(
            gap(
                "points",
                "۶ امتیاز مهارت",
                "blocker",
                f"امتیاز فعلی {total} است؛ حداقل ۶ امتیاز لازم است.",
                "مدرک بالاتر (لیسانس ۳، فوق‌لیسانس ۵، دکتری ۶)، درآمد ۱٫۵ برابر میانه (۳) یا سابقه‌ی کار در نیوزیلند (تا ۳) را تقویت کنید.",
                20,
            )
        )
    if not at_least(profile.english.level, "b2"):
        gaps.append(
            gap(
                "english",
                "زبان انگلیسی",
                "major",
                "SMC حداقل آیلتس ۶٫۵ (یا معادل) می‌خواهد؛ سطح B2 تقریبی است.",
                "آزمون آیلتس/PTE بدهید و نتیجه را ضمیمه کنید.",
                12,
            )
        )
    if not profile.skills_assessment and profile.nz_qualification_level == 0 and qualification:
        gaps.append(
            gap(
                "iqa",
                "ارزیابی مدارک بین‌المللی (IQA)",
                "minor",
                "مدرک خارجی معمولاً باید توسط NZQA ارزیابی شود.",
                "درخواست IQA در NZQA ثبت کنید (حدود ۲ تا ۳ ماه).",
                6,
            )
        )

    blockers = [g for g in gaps if g.severity == "blocker"]
    if blockers:
        status = "needs_job_offer" if not offer_local else "ineligible"
    elif total < POINTS_REQUIRED and offer_local:
        status = "potential"
    elif any(g.severity == "major" for g in gaps):
        status = "potential"
    else:
        status = "eligible"

    ratio = total / 6
    band = "strong" if total >= 8 else "moderate" if total >= 6 else "weak"
    labels = {"strong": "قوی", "moderate": "کافی", "weak": "ناکافی"}

    factors = [
        factor("qualification", "مدرک تحصیلی", f"{qualification} امتیاز", qualification, 6),
        factor("registration", "ثبت حرفه‌ای", f"{registration} امتیاز", registration, 6),
        factor("income", "درآمد (ساعتی)", f"{hourly:,.1f} دلار", income, 6),
        factor("experience", "سابقه‌ی کار در نیوزیلند", f"{profile.nz_experience_years:g} سال", experience, 3),
        factor("total", "جمع امتیاز", f"{total} از ۶", total, 6),
        factor("wage", "آستانه‌ی دستمزد", f"{MEDIAN_HOURLY:,.2f} دلار در ساعت"),
    ]
    costs, total_cost = build_costs(meta, profile)
    docs = documents_score(profile, needs_eca=False)
    readiness = estimate_readiness(status, ratio, gaps, docs)

    highlights = []
    if profile.nz_experience_years:
        highlights.append("سابقه‌ی کار در نیوزیلند تا ۳ امتیاز اضافه می‌کند.")
    if profile.education_country == "NZ":
        highlights.append("مدرک نیوزیلندی یک امتیاز بیشتر از معادل خارجی می‌گیرد.")
    if hourly >= MEDIAN_HOURLY * 1.5:
        highlights.append("درآمد بالای ۱٫۵ برابر میانه، ۳ امتیاز اضافه می‌دهد.")

    summary = (
        "بدون پیشنهاد شغلی از کارفرمای معتبر در نیوزیلند، SMC ممکن نیست."
        if not offer_local
        else f"امتیاز تخمینی {total} از ۶ با حقوق سالانه {salary_nzd:,.0f} دلار نیوزیلند."
    )

    return finish_result(
        meta,
        status=status,
        readiness=readiness,
        summary=summary,
        factors=factors,
        gaps=gaps,
        costs=costs,
        total_cost_eur=total_cost,
        score=total,
        score_threshold=6,
        score_unit="امتیاز",
        score_note="۶ امتیاز از مدرک، ثبت حرفه‌ای، درآمد یا ترکیب آن‌ها با سابقه‌ی کار در نیوزیلند.",
        band=band,
        band_label=labels[band],
        highlights=highlights,
    )
