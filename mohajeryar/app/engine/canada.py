"""موتور ارزیابی کانادا: اکسپرس اینتری (FSW/CEC) و امتیاز CRS.

مرجع: IRCC — معیارهای CRS و تغییرات ۳ نوامبر ۲۰۲۶.
"""
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
from app.engine.utils import age_on, clb_profile, min_clb
from app.formatting import education_label
from app.schemas import Profile

PROGRAM_ID = "ca-ee"
LMIF_EFFECTIVE = date(2026, 11, 3)

AGE_POINTS: dict[int, tuple[int, int]] = {
    18: (90, 99),
    19: (95, 105),
    20: (100, 110),
    21: (100, 110),
    22: (100, 110),
    23: (100, 110),
    24: (100, 110),
    25: (100, 110),
    26: (100, 110),
    27: (100, 110),
    28: (100, 110),
    29: (100, 110),
    30: (95, 105),
    31: (90, 99),
    32: (85, 94),
    33: (80, 88),
    34: (75, 83),
    35: (70, 77),
    36: (65, 72),
    37: (60, 66),
    38: (55, 61),
    39: (50, 55),
    40: (45, 50),
    41: (35, 39),
    42: (25, 28),
    43: (15, 17),
    44: (5, 6),
}

EDU_POINTS: dict[str, tuple[int, int]] = {
    "none": (0, 0),
    "secondary": (28, 30),
    "diploma1": (84, 90),
    "diploma2": (91, 98),
    "bachelor": (112, 120),
    "two_or_more": (119, 128),
    "master": (126, 135),
    "phd": (140, 150),
}

FIRST_LANG: dict[int, tuple[int, int]] = {
    0: (0, 0),
    1: (0, 0),
    2: (0, 0),
    3: (0, 0),
    4: (6, 6),
    5: (6, 6),
    6: (8, 9),
    7: (16, 17),
    8: (22, 23),
    9: (29, 31),
    10: (32, 34),
    11: (32, 34),
    12: (32, 34),
}

SECOND_LANG: dict[int, int] = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 1, 6: 1, 7: 3, 8: 3, 9: 6, 10: 6, 11: 6, 12: 6}

CND_EXP: dict[int, tuple[int, int]] = {
    0: (0, 0),
    1: (35, 40),
    2: (46, 53),
    3: (56, 64),
    4: (63, 72),
    5: (70, 80),
}

# FSW — شش عامل گزینش (۱۰۰ امتیاز)
FSW_AGE = {**{age: 12 for age in range(18, 36)}, 36: 11, 37: 10, 38: 9, 39: 8, 40: 7,
           41: 6, 42: 5, 43: 4, 44: 3, 45: 2, 46: 1}
FSW_EDU = {
    "none": 0,
    "secondary": 5,
    "diploma1": 15,
    "diploma2": 19,
    "bachelor": 21,
    "two_or_more": 22,
    "master": 23,
    "phd": 25,
}
SPOUSE_EDU = {
    "none": 0,
    "secondary": 2,
    "diploma1": 6,
    "diploma2": 7,
    "bachelor": 8,
    "two_or_more": 9,
    "master": 10,
    "phd": 10,
}
SPOUSE_EXP = {0: 0, 1: 5, 2: 7, 3: 8, 4: 9, 5: 10}
FSW_EXP = [(6, 15), (4, 13), (2, 11), (1, 9)]


def _age_points(age: int, with_spouse: bool) -> int:
    pair = AGE_POINTS.get(age)
    if not pair:
        return 0
    return pair[0] if with_spouse else pair[1]


def _spouse_language_points(profile: Profile) -> int:
    skills, _ = clb_profile(profile.spouse_english)
    points = 0
    for value in skills.values():
        if value >= 9:
            points += 5
        elif value >= 7:
            points += 3
        elif value >= 5:
            points += 1
    return min(20, points)


def _additional_points(profile: Profile, with_spouse: bool) -> tuple[int, list[str]]:
    points = 0
    notes: list[str] = []
    if "CA" in profile.relatives_in:
        points += 15
        notes.append("خواهر/برادر مقیم کانادا: ۱۵ امتیاز")
    clb_fr = min_clb(profile.french)
    clb_en = min_clb(profile.english)
    if clb_fr >= 7:
        if clb_en >= 5:
            points += 50
            notes.append("فرانسه NCLC 7+ و انگلیسی CLB 5+: ۵۰ امتیاز")
        else:
            points += 25
            notes.append("فرانسه NCLC 7+: ۲۵ امتیاز")
    if profile.education_country == "CA":
        if profile.education_level in {"bachelor", "master", "phd", "two_or_more"}:
            points += 30
            notes.append("تحصیل دانشگاهی در کانادا (۳ سال+): ۳۰ امتیاز")
        elif profile.education_level in {"diploma1", "diploma2"}:
            points += 15
            notes.append("تحصیل در کانادا (۱ تا ۲ سال): ۱۵ امتیاز")
    return points, notes


def _skill_transferability(
    profile: Profile, clb_min: int, cdn_years: int, foreign_years: int
) -> tuple[int, list[tuple[str, int, int]]]:
    detail: list[tuple[str, int, int]] = []
    high_credential = profile.education_level in {"master", "phd", "two_or_more"}
    post_secondary = profile.education_level in {"diploma1", "diploma2", "bachelor", "master", "phd", "two_or_more"}

    # آموزش + زبان
    edu_lang = 0
    if post_secondary and clb_min >= 7:
        top = 50 if high_credential else 25
        mid = 25 if high_credential else 13
        edu_lang = top if clb_min >= 9 else mid
    detail.append(("آموزش + زبان", edu_lang, 50))

    # آموزش + سابقه‌ی کانادا
    edu_cdn = 0
    if post_secondary and cdn_years >= 1:
        top = 50 if high_credential else 25
        mid = 25 if high_credential else 13
        edu_cdn = top if cdn_years >= 2 else mid
    detail.append(("آموزش + سابقه‌ی کانادا", edu_cdn, 50))

    education_total = min(50, edu_lang + edu_cdn)

    # سابقه‌ی خارجی + زبان / کانادا
    foreign_lang = 0
    if foreign_years >= 1 and clb_min >= 7:
        if foreign_years >= 3:
            foreign_lang = 50 if clb_min >= 9 else 25
        else:
            foreign_lang = 25 if clb_min >= 9 else 13
    foreign_cdn = 0
    if foreign_years >= 1 and cdn_years >= 1:
        if foreign_years >= 3:
            foreign_cdn = 50 if cdn_years >= 2 else 25
        else:
            foreign_cdn = 25 if cdn_years >= 2 else 13
    foreign_total = min(50, foreign_lang + foreign_cdn)

    total = min(100, education_total + foreign_total)
    return total, detail


def _lmif(profile: Profile, cdn_years: int, with_spouse: bool, offer_local: bool) -> tuple[int, str]:
    """Labour Market Integration Factor — از ۳ نوامبر ۲۰۲۶."""
    work_length = CND_EXP.get(min(5, cdn_years), (0, 0))[0 if with_spouse else 1]
    multiple = profile.job_offer_wage_multiple or 0
    bonus = 70 if multiple >= 2 else 40 if multiple >= 1.5 else 20 if multiple >= 1.3 else 0
    offer = 100 if multiple >= 2 else 70 if multiple >= 1.5 else 50 if multiple >= 1.3 else 0
    work_route = work_length + bonus
    cap = 140 if with_spouse else 150
    points = min(cap, max(work_route, offer if offer_local else 0))
    if offer > work_route and offer_local and offer:
        return points, "پیشنهاد شغلی با دستمزد بالا"
    if work_route:
        return points, "سابقه‌ی کاری کانادا (با پاداش دستمزد بالا)" if bonus else "سابقه‌ی کاری کانادا"
    return 0, "بدون امتیاز"


def assess(profile: Profile, rule_date: date | None = None) -> ProgramResult:
    meta = program_meta(PROGRAM_ID)
    rule_date = rule_date or date.today()
    age = age_on(profile.birth_date, rule_date)
    with_spouse = profile.spouse_included
    gaps = []

    english_clb, english_real = clb_profile(profile.english)
    english_min = min(english_clb.values())
    french_clb, _ = clb_profile(profile.french)
    cdn_years_int = min(5, int(profile.canadian_experience_years))
    foreign_years_int = min(5, int(profile.experience_last10))

    # ------------------------------------------------ آموزش
    edu_points = EDU_POINTS.get(profile.education_level, (0, 0))
    edu_crs = edu_points[0] if with_spouse else edu_points[1]

    # ------------------------------------------------ زبان اول و دوم
    first_total = 0
    for value in english_clb.values():
        first_total += FIRST_LANG.get(value, (0, 0))[0 if with_spouse else 1]
    second_total = 0
    for value in french_clb.values():
        second_total += SECOND_LANG.get(value, 0)
    second_total = min(22 if with_spouse else 24, second_total)

    # ------------------------------------------------ سابقه‌ی کاری و LMIF
    cdn_points = CND_EXP.get(cdn_years_int, (0, 0))[0 if with_spouse else 1]
    lmif_note = ""
    ca_offer, _ = local_offer(profile, "CA")
    if rule_date >= LMIF_EFFECTIVE:
        cdn_points, lmif_note = _lmif(profile, cdn_years_int, with_spouse, ca_offer)

    # ------------------------------------------------ همسر
    spouse_points = 0
    if with_spouse:
        spouse_points = (
            SPOUSE_EDU.get(profile.spouse_education, 0)
            + _spouse_language_points(profile)
            + SPOUSE_EXP.get(min(5, int(profile.spouse_canadian_experience_years)), 0)
        )

    # ------------------------------------------------ انتقال مهارت
    transfer, transfer_detail = _skill_transferability(
        profile, english_min, cdn_years_int, foreign_years_int
    )
    additional, additional_notes = _additional_points(profile, with_spouse)
    core = _age_points(age, with_spouse) + edu_crs + first_total + second_total + cdn_points
    crs = core + spouse_points + transfer + additional

    # ------------------------------------------------ FSW 67
    fsw_age = FSW_AGE.get(age, 0)
    fsw_edu = FSW_EDU.get(profile.education_level, 0)
    fsw_lang = sum(4 if v == 7 else 5 if v == 8 else 6 if v >= 9 else 0 for v in english_clb.values())
    if min_clb(profile.french) >= 5:
        fsw_lang += 4
    fsw_exp = next((pts for minimum, pts in FSW_EXP if profile.experience_last10 >= minimum), 0)
    fsw_job = 10 if ca_offer else 0
    fsw_adapt = 0
    if with_spouse and min_clb(profile.spouse_english) >= 4:
        fsw_adapt += 5
    if cdn_years_int >= 1:
        fsw_adapt += 10
    if with_spouse and profile.spouse_canadian_experience_years >= 1:
        fsw_adapt += 10
    if profile.education_country == "CA":
        fsw_adapt += 5
    if "CA" in profile.relatives_in:
        fsw_adapt += 5
    fsw_adapt = min(10, fsw_adapt)
    fsw_total = fsw_age + fsw_edu + fsw_lang + fsw_exp + fsw_job + fsw_adapt

    # ------------------------------------------------ شکاف‌ها
    if profile.experience_last10 < 1:
        gaps.append(
            gap(
                "experience",
                "حداقل یک سال سابقه‌ی کاری ماهر",
                "blocker",
                "برنامه‌ی FSW حداقل ۱ سال کار پیوسته و تمام‌وقت (یا معادل پاره‌وقت) در ۱۰ سال گذشته در شغل TEER 0 تا 3 می‌خواهد.",
                "سابقه را مستند کنید یا تا تکمیل یک سال تمام‌وقت صبر کنید؛ سابقه‌ی بدون مدرک و کار داوطلبانه پذیرفته نیست.",
                20,
            )
        )
    if english_min < 7:
        gaps.append(
            gap(
                "language",
                "زبان انگلیسی در سطح CLB 7",
                "blocker",
                f"ضعیف‌ترین مهارت شما CLB {english_min} است؛ حداقل CLB 7 در هر چهار مهارت لازم است.",
                "با آیلتس جنرال ۶ در هر مهارت به CLB 7 می‌رسید. برنامه‌ی ۳ تا ۶ ماهه برای نوشتن و گفتار بگذارید.",
                25,
            )
        )
    if not (profile.eca or profile.documents.eca):
        gaps.append(
            gap(
                "eca",
                "ارزیابی مدارک تحصیلی (ECA)",
                "major",
                "مدرک خارجی برای کانادا باید توسط سازمان مورد تأیید IRCC ارزیابی شود.",
                "از WES یا سازمان معتبر دیگر ECA بگیرید (۲ تا ۳ ماه، حدود ۲۵۰ دلار کانادا).",
                12,
            )
        )
    if crs < 480 and not ca_offer:
        gaps.append(
            gap(
                "crs",
                "امتیاز CRS پایین‌تر از محدوده‌ی رقابتی",
                "major" if crs < 440 else "minor",
                f"امتیاز فعلی {crs} است؛ دعوت‌نامه‌های عمومی اخیر معمولاً بالای ۵۰۰ بوده‌اند.",
                "مهارت زبان (هر نیم سطح CLB حدود ۲۰ تا ۳۰ امتیاز)، مدرک بالاتر، سابقه‌ی کانادا، نامزدی استانی (۶۰۰ امتیاز) یا فرانسه را هدف بگیرید.",
                15,
            )
        )
    if with_spouse and min_clb(profile.spouse_english) < 5:
        gaps.append(
            gap(
                "spouse_lang",
                "زبان همسر",
                "minor",
                "زبان همسر همراه می‌تواند تا ۲۰ امتیاز CRS و ۵ امتیاز FSW اضافه کند.",
                "همسر می‌تواند آیلتس جنرال با حداقل CLB 5 بدهد.",
                8,
            )
        )
    if not profile.documents.proof_of_funds:
        gaps.append(
            gap(
                "funds",
                "اثبات تمکن مالی",
                "minor",
                "برای اقامت دائم باید سرمایه‌ی کافی برای اسکان خانواده نشان دهید.",
                "گردآوری صورت‌حساب و نامه‌ی بانکی ۶ ماهه؛ مبلغ به اندازه‌ی خانواده بستگی دارد.",
                6,
            )
        )

    blockers = [g for g in gaps if g.severity == "blocker"]
    if blockers:
        status = "ineligible"
    elif not (profile.eca or profile.documents.eca) or crs < 440:
        status = "potential"
    else:
        status = "eligible"

    band, band_label = None, None
    if crs >= 520:
        band, band_label = "strong", "قوی"
    elif crs >= 480:
        band, band_label = "moderate", "متوسط"
    elif crs >= 440:
        band, band_label = "competitive", "رقابتی"
    else:
        band, band_label = "weak", "ضعیف"

    factors = [
        factor("age", "سن", f"{age} سال", _age_points(age, with_spouse), 110 if not with_spouse else 100),
        factor("education", "تحصیلات", education_label(profile.education_level), edu_crs, 150 if not with_spouse else 140),
        factor("first_language", "زبان اول (انگلیسی)", f"حداقل CLB {english_min}", first_total, 136 if not with_spouse else 128,
               note=None if english_real else "سطح از روی خوداظهاری تخمین زده شده است"),
        factor("second_language", "زبان دوم (فرانسه)", f"NCLC {min_clb(profile.french)}", second_total, 24 if not with_spouse else 22),
        factor("canadian_experience", "سابقه‌ی کاری کانادا", f"{profile.canadian_experience_years:g} سال", cdn_points,
               150 if not with_spouse else 140, note=lmif_note or None),
        factor("skill_transfer", "انتقال مهارت", "ترکیب تحصیل/زبان/سابقه", transfer, 100),
    ]
    if with_spouse:
        factors.append(factor("spouse", "عوامل همسر", "تحصیل + زبان + سابقه", spouse_points, 40))
    factors.append(factor("additional", "امتیازهای اضافه", "فرانسه، تحصیل/خویشاوند در کانادا", additional, 95))
    factors.append(factor("fsw", "امتیاز گزینش FSW", f"{fsw_total} از ۱۰۰", fsw_total, 100))

    costs, total_eur = build_costs(meta, profile)
    docs = documents_score(profile, needs_eca=True)
    readiness = estimate_readiness(status, crs / 480 if crs else None, gaps, docs, preference=0)

    highlights = []
    if fsw_total >= 67 and not blockers:
        highlights.append(f"امتیاز گزینش FSW شما {fsw_total} از ۱۰۰ است (حداقل ۶۷).")
    if english_min >= 9:
        highlights.append("زبان انگلیسی در سطح CLB 9+؛ بزرگ‌ترین اهرم امتیاز شماست.")
    if min_clb(profile.french) >= 7:
        highlights.append("فرانسه NCLC 7+؛ امکان شرکت در قرعه‌کشی‌های فرانسه‌زبان با امتیاز پایین‌تر.")
    if "CA" in profile.relatives_in:
        highlights.append("خویشاوند درجه‌یک در کانادا: ۱۵ امتیاز اضافه.")
    if profile.has_job_offer and profile.job_offer_wage_multiple >= 1.3 and rule_date >= LMIF_EFFECTIVE:
        highlights.append("پیشنهاد شغلی با دستمزد بالا در عامل جدید LMIF امتیاز می‌دهد.")
    if profile.spouse_included and min_clb(profile.spouse_english) >= 7:
        highlights.append("زبان و تحصیلات همسر، امتیاز CRS را تقویت می‌کند.")

    summary = (
        f"امتیاز CRS فعلی شما {crs} است"
        + (" (با احتساب قوانین جدید ۳ نوامبر ۲۰۲۶)." if rule_date >= LMIF_EFFECTIVE else ".")
        + (" شرایط پایه‌ی ورود به استخر را دارید." if status != "ineligible" else " هنوز شرایط پایه را کامل نمی‌کنید.")
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
        score=crs,
        score_unit="امتیاز CRS",
        score_note="محدوده‌ی رقابتی عمومی در ۲۰۲۶: حدود ۴۸۰ تا ۵۲۰ (CEC اخیراً ۵۱۹).",
        band=band,
        band_label=band_label,
        highlights=highlights,
        preference_score=0.0,
    )
