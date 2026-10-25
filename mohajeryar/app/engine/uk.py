"""موتور ارزیابی بریتانیا: ویزای کارگر ماهر (Skilled Worker)."""
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
from app.engine.types import CostItem, ProgramResult
from app.engine.utils import age_on, at_least, convert
from app.schemas import Profile

PROGRAM_ID = "uk-skilled"

STANDARD = 41700.0
NEW_ENTRANT = 33400.0
PHD = 37500.0
STEM_PHD = 33400.0
ISL = 33400.0
IHS_PER_YEAR = 1035.0
MAINTENANCE = 1270.0


def _english_b2(profile: Profile) -> bool:
    if at_least(profile.english.level, "b2"):
        return True
    if profile.english.test.lower() == "ielts" and profile.english.has_scores():
        lowest = min(
            profile.english.listening or 0,
            profile.english.reading or 0,
            profile.english.writing or 0,
            profile.english.speaking or 0,
        )
        return lowest >= 5.5
    return False


def assess(profile: Profile, rule_date: date | None = None) -> ProgramResult:
    meta = program_meta(PROGRAM_ID)
    rule_date = rule_date or date.today()
    age = age_on(profile.birth_date, rule_date)
    offer_local, offer_issue = local_offer(profile, "GB")
    salary = convert(profile.job_offer_salary, profile.job_offer_currency, "GBP") if offer_local else 0.0
    recent_grad = bool(profile.graduation_year and profile.graduation_year >= rule_date.year - 2)
    new_entrant = age < 26 or recent_grad
    gaps = []

    threshold = STANDARD
    threshold_reason = "نرخ عمومی"
    if profile.occupation_shortage or profile.job_offer_shortage:
        threshold, threshold_reason = ISL, "فهرست مشاغل کمبود نیرو (ISL)"
    if profile.education_level == "phd":
        if profile.education_field == "stem":
            threshold, threshold_reason = STEM_PHD, "دکتری STEM مرتبط"
        else:
            threshold, threshold_reason = PHD, "دکتری مرتبط با شغل"
    if new_entrant and threshold == STANDARD:
        threshold, threshold_reason = NEW_ENTRANT, "تازه‌وارد (زیر ۲۶ یا فارغ‌التحصیل اخیر)"

    if not offer_local:
        gaps.append(
            gap(
                "job_offer",
                "پیشنهاد شغلی در بریتانیا",
                "blocker",
                "ویزای کارگر ماهر فقط با گواهی حمایت (CoS) از کارفرمای دارای مجوز ممکن است."
                + (" پیشنهاد فعلی شما برای کشور دیگری است." if offer_issue == "other" else ""),
                "در فهرست کارفرمایان دارای مجوز GOV.UK جست‌وجو کنید و شغل با کد SOC مناسب پیدا کنید.",
                28,
            )
        )
    elif not profile.job_offer_recognized_sponsor:
        gaps.append(
            gap(
                "sponsor",
                "مجوز حمایت کارفرما",
                "blocker",
                "کارفرمای فعلی مجوز حمایت از نیروی خارجی ندارد.",
                "کارفرمای دارای مجوز (Licensed Sponsor) پیدا کنید؛ گواهی حمایت باید قبل از درخواست صادر شود.",
                24,
            )
        )
    if offer_local and salary < threshold:
        gaps.append(
            gap(
                "salary",
                "حداقل حقوق سالانه",
                "blocker",
                f"حقوق پیشنهادی {salary:,.0f} پوند است؛ آستانه {threshold:,.0f} پوند است ({threshold_reason}).",
                "حقوق بالاتر مذاکره کنید؛ یا اگر واجد شرایط تازه‌وارد/دکتری/فهرست ISL هستید، آستانه‌ی پایین‌تر اعمال می‌شود.",
                22,
            )
        )
    if offer_local and not profile.job_offer_going_rate:
        gaps.append(
            gap(
                "going_rate",
                "نرخ رایج شغل (Going Rate)",
                "major",
                "علاوه بر آستانه‌ی عمومی، حقوق باید حداقل نرخ رایج کد شغل SOC باشد.",
                "نرخ رایج شغل را در جدول GOV.UK بررسی و حقوق را بر همان مبنا تنظیم کنید.",
                12,
            )
        )
    if not _english_b2(profile):
        gaps.append(
            gap(
                "english",
                "زبان انگلیسی سطح B2",
                "blocker",
                "از ۸ ژانویه ۲۰۲۶ حداقل سطح زبان برای این ویزا B2 است.",
                "آزمون SELT مورد تأیید (مثلاً آیلتس UKVI) در سطح B2 یا بالاتر بدهید.",
                18,
            )
        )
    if profile.education_level in {"none", "secondary", "diploma1", "diploma2"}:
        gaps.append(
            gap(
                "skill_level",
                "سطح مهارت شغل (RQF 6)",
                "major",
                "شغل باید در سطح مدرک دانشگاهی (RQF 6) باشد؛ برخی مشاغل فنی حذف شده‌اند.",
                "شغلی با کد SOC سطح ۶ انتخاب کنید؛ یا مدارک/تجربه‌ی معادل ارائه دهید.",
                10,
            )
        )

    blockers = [g for g in gaps if g.severity == "blocker"]
    if blockers:
        status = "needs_job_offer" if not offer_local else "ineligible"
    elif any(g.severity == "major" for g in gaps) or not profile.job_offer_recognized_sponsor:
        status = "potential"
    else:
        status = "eligible"

    ratio = salary / threshold if threshold else None
    band = "strong" if salary >= threshold * 1.15 else "moderate" if salary >= threshold else "weak"
    labels = {"strong": "قوی", "moderate": "کافی", "weak": "ناکافی"}

    factors = [
        factor("salary", "حقوق سالانه", f"{salary:,.0f} پوند", round(salary), round(threshold)),
        factor("threshold", "آستانه‌ی اعمال‌شده", f"{threshold:,.0f} پوند", note=threshold_reason),
        factor("english", "زبان انگلیسی", "B2 یا بالاتر" if _english_b2(profile) else "پایین‌تر از B2"),
        factor("sponsor", "کارفرمای دارای مجوز", "بله" if profile.job_offer_recognized_sponsor else "خیر"),
        factor("going_rate", "نرخ رایج شغل", "رعایت‌شده" if profile.job_offer_going_rate else "رعایت نشده"),
    ]

    # هزینه‌ها: انتخاب یک بازه‌ی ویزا + هزینه‌ی سلامت برای مدت اقامت
    years = 5.0 if profile.job_offer_contract_years >= 5 else max(3.0, min(5.0, profile.job_offer_contract_years))
    visa_label = "هزینه‌ی ویزا (تا ۳ سال)" if years <= 3 else "هزینه‌ی ویزا (بیش از ۳ سال)"
    costs, _ = build_costs(meta, profile, include_labels={visa_label}, include_extras=False)
    people = 1 + (1 if profile.spouse_included else 0)
    ihs = CostItem(
        label=f"هزینه‌ی سلامت (IHS) — {int(years)} سال × {int(people)} نفر",
        amount=IHS_PER_YEAR * years * people,
        currency="GBP",
        note="برای هر سال اقامت، برای متقاضی و همراهان",
    )
    maintenance = CostItem(
        label="اثبات تمکن مالی (۹۰ روز)",
        amount=MAINTENANCE * people,
        currency="GBP",
        note="پول شما می‌ماند و هزینه نیست",
        refundable=True,
    )
    costs.append(ihs)
    costs.append(maintenance)
    costs.append(CostItem(label="آزمون زبان و ترجمه مدارک", amount=400, currency="GBP", approximate=True))
    total_eur = sum(convert(item.amount, item.currency, "EUR") for item in costs if item is not maintenance)
    docs = documents_score(profile, needs_eca=False)
    readiness = estimate_readiness(status, ratio, gaps, docs)

    highlights = []
    if threshold < STANDARD:
        highlights.append(f"آستانه‌ی پایین‌تر {threshold:,.0f} پوندی برای شما اعمال می‌شود ({threshold_reason}).")
    if salary >= threshold:
        highlights.append("حقوق پیشنهادی با آستانه‌ی ویزا هم‌خوان است.")
    highlights.append("پس از ۵ سال اقامت با این ویزا می‌توانید اقامت دائم (ILR) بگیرید.")

    summary = (
        "بدون گواهی حمایت کارفرما در بریتانیا، این ویزا صادر نمی‌شود."
        if not offer_local
        else f"حقوق {salary:,.0f} پوند در برابر آستانه {threshold:,.0f} پوند؛ "
        + ("شرایط پایه را دارید." if status == "eligible" else "چند شکاف باقی است.")
    )

    return finish_result(
        meta,
        status=status,
        readiness=readiness,
        summary=summary,
        factors=factors,
        gaps=gaps,
        costs=costs,
        total_cost_eur=round(total_eur),
        score=round(salary),
        score_threshold=threshold,
        score_unit="حقوق سالانه (پوند)",
        score_note="آستانه بر اساس تازه‌وارد/دکتری/فهرست ISL انتخاب می‌شود؛ نرخ رایج شغل نیز باید رعایت شود.",
        band=band,
        band_label=labels[band],
        highlights=highlights,
    )
