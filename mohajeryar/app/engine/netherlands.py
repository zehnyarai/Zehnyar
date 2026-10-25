"""موتور ارزیابی هلند: مهاجر متخصص و کارت آبی اروپا."""
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
from app.engine.utils import age_on, convert_to_eur
from app.formatting import education_label
from app.schemas import Profile

HSM_ID = "nl-hsm"
BC_ID = "nl-bluecard"

HSM_30_PLUS = 5942.00
HSM_UNDER_30 = 4357.00
HSM_REDUCED = 3122.00
BC_STANDARD = 5942.00
BC_REDUCED = 4754.00


def _recent_graduate(profile: Profile, rule_date: date) -> bool:
    return bool(profile.graduation_year and profile.graduation_year >= rule_date.year - 3)


def _reduced_criterion(profile: Profile, rule_date: date) -> bool:
    """معیار کاهش‌یافته: فارغ‌التحصیل/دوره‌ی جست‌وجوی کار در هلند."""
    return _recent_graduate(profile, rule_date) and (
        profile.education_country == "NL" or "NL" in profile.prior_stay
    )


def _monthly_salary(profile: Profile) -> float:
    offer_local, _ = local_offer(profile, "NL")
    if not offer_local:
        return 0.0
    return convert_to_eur(profile.job_offer_salary, profile.job_offer_currency) / 12


def _hsm(profile: Profile, rule_date: date) -> ProgramResult:
    meta = program_meta(HSM_ID)
    age = age_on(profile.birth_date, rule_date)
    offer_local, offer_issue = local_offer(profile, "NL")
    monthly = _monthly_salary(profile)
    reduced = _reduced_criterion(profile, rule_date)
    threshold = HSM_REDUCED if reduced else (HSM_UNDER_30 if age < 30 else HSM_30_PLUS)
    gaps = []

    if not offer_local:
        gaps.append(
            gap(
                "job_offer",
                "پیشنهاد شغلی در هلند",
                "blocker",
                "این مسیر فقط با قرارداد کار از یک کارفرمای «حامی شناخته‌شده» IND ممکن است."
                + (" پیشنهاد فعلی شما برای کشور دیگری است." if offer_issue == "other" else ""),
                "در فهرست عمومی حامیان شناخته‌شده‌ی IND جست‌وجو کنید؛ کارفرما درخواست را ثبت می‌کند.",
                28,
            )
        )
    elif not profile.job_offer_recognized_sponsor:
        gaps.append(
            gap(
                "sponsor",
                "کارفرمای حامی شناخته‌شده",
                "blocker",
                "کارفرمای فعلی در فهرست Recognised Sponsors نیست و نمی‌تواند برای شما درخواست دهد.",
                "با کارفرمای حامی شناخته‌شده مذاکره کنید یا شرکت واسط مجاز (payroll) پیدا کنید.",
                22,
            )
        )
    if offer_local and monthly < threshold:
        gaps.append(
            gap(
                "salary",
                "حداقل حقوق ماهانه",
                "blocker",
                f"حقوق ماهانه‌ی شما {monthly:,.0f} یورو است؛ آستانه {threshold:,.0f} یورو است (بدون حقوق تعطیلات).",
                "حقوق بالاتر مذاکره کنید؛ یا اگر زیر ۳۰ سال هستید آستانه‌ی ۴٬۳۵۷ یورو اعمال می‌شود.",
                20,
            )
        )
    if not _recent_graduate(profile, rule_date) and profile.monthly_income_eur and monthly and monthly < threshold:
        gaps.append(
            gap(
                "reduced",
                "معیار کاهش‌یافته",
                "info",
                "معیار ۳٬۱۲۲ یورویی فقط برای فارغ‌التحصیلان/دوره‌ی جست‌وجوی کار هلند است.",
                "اگر واجد شرایط هستید، گواهی دوره‌ی orientation year را ضمیمه کنید.",
                2,
            )
        )

    blockers = [g for g in gaps if g.severity == "blocker"]
    if blockers:
        status = "needs_job_offer" if not offer_local else "ineligible"
    else:
        status = "eligible"

    ratio = monthly / threshold if threshold else None
    band, band_label = None, None
    if monthly >= threshold * 1.15:
        band, band_label = "strong", "قوی"
    elif monthly >= threshold:
        band, band_label = "moderate", "کافی"
    else:
        band, band_label = "weak", "ناکافی"

    factors = [
        factor("salary", "حقوق ماهانه (بدون ۸٪ تعطیلات)", f"{monthly:,.0f} یورو", round(monthly), round(threshold)),
        factor("threshold", "آستانه‌ی ۲۰۲۶", f"{threshold:,.0f} یورو"),
        factor("age", "سن", f"{age} سال", note="آستانه به سن و معیار کاهش‌یافته وابسته است"),
        factor("sponsor", "کارفرمای حامی", "تأییدشده" if profile.job_offer_recognized_sponsor else "تأییدنشده"),
        factor("reduced", "معیار کاهش‌یافته", "بله" if reduced else "خیر"),
    ]
    costs, total_eur = build_costs(meta, profile)
    docs = documents_score(profile, needs_eca=False)
    readiness = estimate_readiness(status, ratio, gaps, docs)

    highlights = []
    if age < 30:
        highlights.append("زیر ۳۰ سال هستید؛ آستانه‌ی ۴٬۳۵۷ یورو در ماه اعمال می‌شود.")
    if reduced:
        highlights.append("معیار کاهش‌یافته‌ی ۳٬۱۲۲ یورو برای شما قابل اعمال است.")
    highlights.append("IND معمولاً ظرف ۲ هفته (و حداکثر ۹۰ روز) تصمیم می‌گیرد.")

    summary = (
        "بدون پیشنهاد شغلی از کارفرمای حامی در هلند، این مسیر شروع نمی‌شود."
        if not offer_local
        else f"با حقوق ماهانه {monthly:,.0f} یورو و آستانه {threshold:,.0f} یورو، "
        + ("شرایط مهاجر متخصص را دارید." if status == "eligible" else "هنوز شرایط کامل نیست.")
    )

    return finish_result(
        meta,
        status=status,
        readiness=readiness,
        summary=summary,
        factors=factors,
        gaps=gaps,
        costs=costs,
        total_cost_eur=total_eur,
        score=round(monthly),
        score_threshold=threshold,
        score_unit="حقوق ماهانه (یورو)",
        score_note="مبالغ ۲۰۲۶ بدون احتساب ۸٪ حقوق تعطیلات؛ کارفرما باید حامی شناخته‌شده باشد.",
        band=band,
        band_label=band_label,
        highlights=highlights,
    )


def _blue_card(profile: Profile, rule_date: date) -> ProgramResult:
    meta = program_meta(BC_ID)
    offer_local, offer_issue = local_offer(profile, "NL")
    monthly = _monthly_salary(profile)
    recent = _recent_graduate(profile, rule_date)
    threshold = BC_REDUCED if recent else BC_STANDARD
    gaps = []

    if profile.education_level in {"none", "secondary", "diploma1"}:
        gaps.append(
            gap(
                "degree",
                "مدرک آموزش عالی حداقل ۳ ساله",
                "blocker",
                "کارت آبی هلند مدرک آموزش عالی حداقل سه‌ساله یا تجربه‌ی هم‌ارز می‌خواهد.",
                "مدرک کارشناسی یا بالاتر ارائه دهید؛ مدارک فنی‌وحرفه‌ای دو ساله کافی نیست.",
                20,
            )
        )
    if not offer_local:
        gaps.append(
            gap(
                "job_offer",
                "پیشنهاد شغلی در هلند",
                "blocker",
                "بدون قرارداد کار، کارت آبی صادر نمی‌شود."
                + (" پیشنهاد فعلی شما برای کشور دیگری است." if offer_issue == "other" else ""),
                "شغل با حقوق بالای آستانه در هلند پیدا کنید؛ کارفرما باید در فرایند IND همکاری کند.",
                24,
            )
        )
    if offer_local and monthly < threshold:
        gaps.append(
            gap(
                "salary",
                "حداقل حقوق ماهانه",
                "blocker",
                f"حقوق {monthly:,.0f} یورو در ماه است؛ آستانه {threshold:,.0f} یورو است.",
                "حقوق بالاتر مذاکره کنید؛ برای فارغ‌التحصیلان سه سال اخیر آستانه ۴٬۷۵۴ یورو است.",
                18,
            )
        )
    if offer_local and not profile.job_offer_recognized_sponsor:
        gaps.append(
            gap(
                "sponsor",
                "کارفرمای حامی",
                "major",
                "در عمل درخواست کارت آبی در هلند از طریق کارفرمای حامی ثبت می‌شود.",
                "کارفرمای حامی شناخته‌شده پیدا کنید.",
                12,
            )
        )

    blockers = [g for g in gaps if g.severity == "blocker"]
    if blockers:
        status = "needs_job_offer" if not offer_local else "ineligible"
    else:
        status = "eligible" if profile.job_offer_recognized_sponsor else "potential"

    ratio = monthly / threshold if threshold else None
    band = "strong" if monthly >= threshold * 1.15 else "moderate" if monthly >= threshold else "weak"
    labels = {"strong": "قوی", "moderate": "کافی", "weak": "ناکافی"}

    factors = [
        factor("salary", "حقوق ماهانه", f"{monthly:,.0f} یورو", round(monthly), round(threshold)),
        factor("threshold", "آستانه‌ی ۲۰۲۶", f"{threshold:,.0f} یورو"),
        factor("degree", "تحصیلات", education_label(profile.education_level)),
        factor("sponsor", "کارفرمای حامی", "تأییدشده" if profile.job_offer_recognized_sponsor else "تأییدنشده"),
    ]
    costs, total_eur = build_costs(meta, profile)
    docs = documents_score(profile, needs_eca=False)
    readiness = estimate_readiness(status, ratio, gaps, docs)

    return finish_result(
        meta,
        status=status,
        readiness=readiness,
        summary=(
            "برای کارت آبی هلند به پیشنهاد شغلی با حقوق بالای آستانه نیاز دارید."
            if not offer_local
            else f"حقوق ماهانه {monthly:,.0f} یورو در برابر آستانه {threshold:,.0f} یورو."
        ),
        factors=factors,
        gaps=gaps,
        costs=costs,
        total_cost_eur=total_eur,
        score=round(monthly),
        score_threshold=threshold,
        score_unit="حقوق ماهانه (یورو)",
        score_note="کارت آبی هلند امکان جابه‌جایی آسان‌تر در اتحادیه اروپا را می‌دهد.",
        band=band,
        band_label=labels[band],
        highlights=["پس از ۱۲ ماه اقامت با کارت آبی، جابه‌جایی به کشورهای دیگر اروپایی آسان‌تر است."],
    )


def assess_hsm(profile: Profile, rule_date: date | None = None) -> ProgramResult:
    return _hsm(profile, rule_date or date.today())


def assess_blue_card(profile: Profile, rule_date: date | None = None) -> ProgramResult:
    return _blue_card(profile, rule_date or date.today())
