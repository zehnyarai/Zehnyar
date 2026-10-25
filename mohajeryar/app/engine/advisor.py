"""لایه‌ی مشاوره: رتبه‌بندی، نقشه‌ی راه، چک‌لیست مدارک و روایت فارسی."""
from __future__ import annotations

from datetime import date

from app.engine.types import Gap, ProgramResult, Step
from app.formatting import fa_money, fa_number, fa_percent
from app.schemas import Profile

# برآورد زمان تا اقامت دائم و شهروندی (سال) برای مقایسه‌ی ترجیحات
PR_YEARS = {
    "ca-ee": 0.0,
    "de-bluecard": 1.75,
    "de-chancenkarte": 3.5,
    "nl-hsm": 5.0,
    "nl-bluecard": 5.0,
    "uk-skilled": 5.0,
    "au-189": 0.0,
    "au-190": 0.0,
    "au-491": 3.0,
    "nz-smc": 0.0,
    "pt-d7": 5.0,
    "pt-d8": 5.0,
}
CITIZENSHIP_YEARS = {
    "ca-ee": 3.0,
    "de-bluecard": 5.0,
    "de-chancenkarte": 6.0,
    "nl-hsm": 5.0,
    "nl-bluecard": 5.0,
    "uk-skilled": 6.0,
    "au-189": 4.0,
    "au-190": 4.0,
    "au-491": 5.0,
    "nz-smc": 5.0,
    "pt-d7": 5.0,
    "pt-d8": 5.0,
}
TIMELINE_MONTHS = {
    "ca-ee": 10,
    "de-bluecard": 3,
    "de-chancenkarte": 2,
    "nl-hsm": 2.5,
    "nl-bluecard": 2,
    "uk-skilled": 3,
    "au-189": 9,
    "au-190": 9,
    "au-491": 9,
    "nz-smc": 5,
    "pt-d7": 4.5,
    "pt-d8": 4.5,
}
JOB_MARKET = {
    "ca-ee": 0.9,
    "de-bluecard": 0.9,
    "de-chancenkarte": 0.7,
    "nl-hsm": 0.9,
    "nl-bluecard": 0.8,
    "uk-skilled": 0.8,
    "au-189": 0.7,
    "au-190": 0.7,
    "au-491": 0.5,
    "nz-smc": 0.7,
    "pt-d7": 0.3,
    "pt-d8": 0.4,
}
ENGLISH_COUNTRIES = {"CA", "GB", "AU", "NZ", "IE", "US"}


def preference_score(result: ProgramResult, profile: Profile) -> float:
    """هم‌خوانی برنامه با ترجیحات کاربر (۰ تا ۱)."""
    parts: list[float] = []
    priorities = set(profile.priorities)
    if not priorities:
        priorities = {"speed", "cost", "pr"}

    timeline = TIMELINE_MONTHS.get(result.program_id, 8)
    cost = result.total_cost_eur or 6000
    pr_years = PR_YEARS.get(result.program_id, 5)
    citizen_years = CITIZENSHIP_YEARS.get(result.program_id, 6)

    if "speed" in priorities:
        parts.append(1 - min(1.0, timeline / 12))
    if "cost" in priorities:
        parts.append(1 - min(1.0, cost / 12000))
    if "pr" in priorities:
        parts.append(1 - min(1.0, pr_years / 6))
    if "citizenship" in priorities:
        parts.append(1 - min(1.0, citizen_years / 7))
    if "family" in priorities:
        parts.append(1.0 if result.category in {"work", "skilled"} else 0.6)
    if "job_market" in priorities:
        parts.append(JOB_MARKET.get(result.program_id, 0.5))
    if "english" in priorities:
        parts.append(1.0 if result.country_code in ENGLISH_COUNTRIES else 0.15)
    if "low_risk" in priorities:
        parts.append(1.0 if result.status == "eligible" else 0.4)

    score = sum(parts) / len(parts) if parts else 0.5
    if profile.target_countries and result.country_code in profile.target_countries:
        score = min(1.0, score + 0.25)
    if (
        profile.has_job_offer
        and (profile.job_offer_country or "").upper() == result.country_code
    ):
        score = min(1.0, score + 0.12)
    return round(score, 3)


def rank_results(
    results: list[ProgramResult],
    profile: Profile,
    rule_date: date | None = None,
) -> list[ProgramResult]:
    for result in results:
        result.preference_score = preference_score(result, profile)
    order = {"eligible": 3, "potential": 2, "needs_job_offer": 1, "ineligible": 0}
    return sorted(
        results,
        key=lambda r: (
            order.get(r.status, 0),
            round(
                r.readiness * 0.72
                + r.preference_score * 28
                + (
                    2.5
                    if profile.has_job_offer
                    and (profile.job_offer_country or "").upper() == r.country_code
                    else 0.0
                ),
                1,
            ),
            -len(r.blockers),
        ),
        reverse=True,
    )


def overall_readiness(results: list[ProgramResult], profile: Profile) -> int:
    if not results:
        return 0
    top = results[0]
    best = max((r.readiness for r in results if r.status != "ineligible"), default=top.readiness)
    base = round(best * 0.7 + top.readiness * 0.3)
    docs = profile.documents
    bonus = sum(
        1
        for flag in (
            docs.passport_valid_years >= 2,
            docs.birth_certificate,
            docs.education_transcripts,
            docs.language_certificate,
            docs.police_clearance,
            docs.proof_of_funds,
        )
        if flag
    )
    return max(5, min(99, base + bonus))


def _has_gap(result: ProgramResult, *keys: str) -> bool:
    return any(gap.key in keys for gap in result.gaps)


def build_roadmap(
    result: ProgramResult,
    profile: Profile,
    rule_date: date | None = None,
) -> list[Step]:
    """نقشه‌ی راه مرحله‌به‌مرحله برای برنامه‌ی انتخاب‌شده."""
    country = result.country_code
    docs = profile.documents
    steps: list[Step] = [
        Step(
            phase="۱. تصمیم و بررسی",
            title="تثبیت مسیر و بررسی قوانین روز",
            detail=f"شرایط {result.program_name} را در صفحه‌ی رسمی ({result.official_url}) با آخرین به‌روزرسانی مقایسه کنید. "
            "هر برنامه‌ای که انتخاب می‌کنید باید با هدف بلندمدت شما (اقامت دائم/شهروندی/درآمد) هم‌خوان باشد.",
            duration="۱ تا ۲ هفته",
        ),
        Step(
            phase="۲. مدارک پایه",
            title="گذرنامه، شناسنامه و مدارک تحصیلی",
            detail="گذرنامه با اعتبار حداقل دو سال، شناسنامه، ترجمه‌ی رسمی مدارک تحصیلی و ریزنمرات را آماده کنید. "
            "برای همراهان، سند ازدواج و شناسنامه‌ی فرزندان نیز لازم است.",
            duration="۲ تا ۶ هفته",
            done=docs.passport_valid_years >= 2 and docs.birth_certificate and docs.education_transcripts,
        ),
    ]

    if _has_gap(result, "language", "english", "english_upgrade", "language_floor", "german"):
        steps.append(
            Step(
                phase="۳. زبان",
                title="برنامه‌ی زبان و آزمون رسمی",
                detail="زبان بزرگ‌ترین اهرم امتیاز و مهم‌ترین شرط پذیرش است. یک آزمون رسمی (آیلتس/PTE/Goethe) با تاریخ مشخص ثبت‌نام کنید "
                "و نتیجه را در پروفایل به‌روز کنید تا ارزیابی دقیق‌تر شود.",
                duration="۳ تا ۹ ماه بسته به سطح فعلی",
                cost="۱۵۰ تا ۳۵۰ یورو",
                done=docs.language_certificate,
            )
        )

    if country == "CA" and _has_gap(result, "eca"):
        steps.append(
            Step(
                phase="۳. ارزیابی مدارک",
                title="درخواست ECA",
                detail="مدرک تحصیلی را به یکی از سازمان‌های مورد تأیید IRCC (مثل WES) بفرستید؛ نتیجه معمولاً ۲ تا ۳ ماه طول می‌کشد.",
                duration="۲ تا ۳ ماه",
                cost="حدود ۲۵۰ دلار کانادا",
            )
        )
    if country == "AU" and _has_gap(result, "skills_assessment", "competition", "points"):
        steps.append(
            Step(
                phase="۳. ارزیابی مهارت",
                title="ارزیابی مهارت و انتخاب کد شغل",
                detail="سازمان ارزیابی رشته‌ی خود را انتخاب کنید و مدارک کاری/تحصیلی را ارسال کنید. "
                "کد شغل باید در فهرست مشاغل واجد شرایط همان ویزا باشد.",
                duration="۲ تا ۴ ماه",
                cost="۵۰۰ تا ۱٬۰۰۰ دلار استرالیا",
            )
        )
    if country == "NZ" and _has_gap(result, "iqa"):
        steps.append(
            Step(
                phase="۳. ارزیابی مدارک",
                title="ارزیابی مدارک در NZQA",
                detail="درخواست International Qualification Assessment ثبت کنید تا سطح معادل مدرک مشخص شود.",
                duration="۲ تا ۳ ماه",
                cost="حدود ۸۵۰ دلار نیوزیلند",
            )
        )
    if country == "DE" and _has_gap(result, "recognition"):
        steps.append(
            Step(
                phase="۳. شناسایی مدرک",
                title="بررسی ANABIN و شناسایی حرفه‌ای",
                detail="وضعیت دانشگاه و رشته را در ANABIN بررسی کنید؛ در صورت شناسایی جزئی، مسیر جبرانی (Anpassungslehrgang) یا آزمون دانش را برنامه‌ریزی کنید.",
                duration="۱ تا ۳ ماه",
            )
        )

    if result.status == "needs_job_offer" or _has_gap(result, "job_offer", "sponsor", "salary", "going_rate", "contract"):
        steps.append(
            Step(
                phase="۴. شغل",
                title="جست‌وجوی شغل و مذاکره‌ی حقوق",
                detail="رزومه را با استاندارد کشور مقصد بازنویسی کنید (Europass برای اروپا). "
                "برای مسیرهای دارای پیشنهاد شغلی، تنها کارفرمای واجد شرایط (حامی/دارای مجوز) کافی است. "
                "حداقل حقوق آستانه را از قبل بررسی و در مذاکره لحاظ کنید.",
                duration="۳ تا ۹ ماه",
            )
        )

    steps.extend(
        [
            Step(
                phase="۵. درخواست",
                title="ثبت درخواست و پرداخت هزینه‌ها",
                detail=f"فرم رسمی {result.program_name} را تکمیل کنید، هزینه‌های دولتی را بپردازید و بیومتریک/مصاحبه را انجام دهید. "
                "همه‌ی مدارک باید ترجمه‌ی رسمی و در صورت نیاز تأیید (apostille) داشته باشند.",
                duration="۲ تا ۶ هفته",
                cost=fa_money(result.total_cost_eur or 0, "EUR") + " (برآورد کل)",
                done=docs.proof_of_funds and docs.police_clearance,
            ),
            Step(
                phase="۶. پس از ورود",
                title="ثبت اقامت، حساب بانکی و بیمه",
                detail="پس از ورود، ثبت آدرس/اقامت، افتتاح حساب، بیمه‌ی درمانی و در صورت نیاز ثبت مالیات را انجام دهید. "
                "تاریخ شروع اقامت را برای محاسبه‌ی اقامت دائم نگه دارید.",
                duration="۱ تا ۴ هفته",
            ),
            Step(
                phase="۷. مسیر بلندمدت",
                title="اقامت دائم و شهروندی",
                detail=f"{result.pr_path or ''} {result.citizenship_path or ''}".strip(),
                duration="۲ تا ۶ سال",
            ),
        ]
    )
    return steps


def documents_checklist(profile: Profile, results: list[ProgramResult]) -> list[dict]:
    countries = {r.country_code for r in results if r.status != "ineligible"}
    docs = profile.documents
    spouse = profile.spouse_included
    items = [
        {"title": "گذرنامه با اعتبار حداقل ۲ سال", "have": docs.passport_valid_years >= 2, "note": "برای همه‌ی مسیرها", "required": True},
        {"title": "شناسنامه و ترجمه‌ی رسمی", "have": docs.birth_certificate, "note": "برای همه‌ی مسیرها", "required": True},
        {"title": "مدارک تحصیلی و ریزنمرات", "have": docs.education_transcripts, "note": "برای ارزیابی مدارک و امتیاز تحصیلات", "required": True},
        {"title": "مدرک زبان معتبر", "have": docs.language_certificate, "note": "آیلتس/PTE/Goethe با تاریخ معتبر", "required": True},
        {"title": "نامه‌های سابقه‌ی کار", "have": docs.employment_letters, "note": "شامل عنوان شغل، تاریخ‌ها و وظایف", "required": True},
        {"title": "گواهی عدم سوءپیشینه", "have": docs.police_clearance, "note": "معمولاً با اعتبار ۶ ماه", "required": True},
        {"title": "معاینات پزشکی", "have": docs.medical, "note": "برای کانادا، استرالیا، نیوزیلند و بریتانیا", "required": True},
        {"title": "اثبات تمکن مالی", "have": docs.proof_of_funds, "note": "صورت‌حساب ۳ تا ۶ ماه", "required": True},
        {"title": "سند ازدواج/همراهی", "have": docs.marriage_certificate, "note": "برای همراهان", "required": spouse},
    ]
    if "CA" in countries:
        items.append({"title": "ارزیابی مدارک (ECA)", "have": profile.eca or docs.eca, "note": "الزامی برای اکسپرس اینتری", "required": True})
    if "AU" in countries:
        items.append({"title": "ارزیابی مهارت (Skills Assessment)", "have": profile.skills_assessment, "note": "الزامی برای ویزاهای مهارتی", "required": True})
    if "NZ" in countries:
        items.append({"title": "ارزیابی مدارک NZQA (در صورت نیاز)", "have": profile.nz_qualification_level > 0, "note": "برای مدارک خارجی", "required": False})
    if "DE" in countries:
        items.append({"title": "نتیجه‌ی ANABIN / شناسایی مدرک", "have": profile.recognition == "full", "note": "کلید کارت آبی و کارت فرصت", "required": True})
    return items


def quick_wins(results: list[ProgramResult], profile: Profile, limit: int = 5) -> list[str]:
    seen: set[str] = set()
    wins: list[str] = []
    priority = {"blocker": 0, "major": 1, "minor": 2, "info": 3}
    gaps: list[Gap] = []
    for result in results[:4]:
        gaps.extend(result.gaps)
    gaps.sort(key=lambda g: (priority.get(g.severity, 9), -g.impact))
    for item in gaps:
        if item.key in seen:
            continue
        seen.add(item.key)
        wins.append(item.fix)
        if len(wins) >= limit:
            break
    return wins


def narrative(
    results: list[ProgramResult],
    profile: Profile,
    rule_date: date | None = None,
) -> list[str]:
    """خلاصه‌ی فارسی قطعی (بدون نیاز به مدل زبانی)."""
    if not results:
        return ["برای ارزیابی، ابتدا پروفایل خود را تکمیل کنید."]
    top = results[0]
    eligible = [r for r in results if r.status == "eligible"]
    paragraphs = []
    eligible_text = (
        f"{fa_number(len(eligible))} مسیر شرایط پایه را دارند"
        if eligible
        else "هیچ مسیری هنوز شرایط پایه را ندارد"
    )
    paragraphs.append(
        f"بر اساس پروفایل شما، در مجموع {fa_number(len(results))} مسیر بررسی شد و "
        f"{eligible_text}. "
        f"بهترین گزینه‌ی فعلی «{top.program_name}» در {top.country_name} با آمادگی "
        f"{fa_percent(top.readiness)} است."
    )
    if len(results) > 1:
        others = "، ".join(f"{r.program_name} ({r.country_name})" for r in results[1:3])
        paragraphs.append(f"گزینه‌های بعدی: {others}.")
    blockers = top.blockers
    if blockers:
        paragraphs.append(
            "مهم‌ترین مانع فعلی: " + blockers[0].label + ". " + blockers[0].fix
        )
    else:
        paragraphs.append(
            "مانع قانونی جدی در این مسیر دیده نمی‌شود؛ گام بعدی تکمیل مدارک و ثبت درخواست است."
        )
    if top.status == "needs_job_offer":
        paragraphs.append(
            "این مسیر بدون پیشنهاد شغلی وارد مرحله‌ی درخواست نمی‌شود؛ تمرکز اصلی شما باید روی جست‌وجوی شغل و مذاکره‌ی حقوق باشد."
        )
    wins = [item.strip().rstrip(".;؛ ") for item in quick_wins(results, profile, 3) if item.strip()]
    if wins:
        paragraphs.append("سه اقدام با بیشترین اثر: " + "؛ ".join(wins) + ".")
    return paragraphs
