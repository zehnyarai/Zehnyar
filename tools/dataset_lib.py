"""Shared helpers for building the Visayar dataset.

The dataset is the single source of truth consumed by both the Python backend
engine and the TypeScript mobile engine.  Everything the scoring logic needs is
described declaratively here, so the two engines stay in lock-step.
"""

from __future__ import annotations

LAST_VERIFIED = "2026-10-25"
DATASET_VERSION = "2.0.1"
DATA_SCHEMA_VERSION = 1
REVIEW_INTERVAL_DAYS = 30
STALE_AFTER_DAYS = 45

# ---------------------------------------------------------------------------
# Reference FX rates (1 unit -> USD), used only to normalise money inputs.
# They are indicative reference rates and are shown to the user as such.
# ---------------------------------------------------------------------------
FX = {
    "USD": {"rate": 1.0, "fa": "دلار آمریکا", "en": "US dollar", "symbol": "$"},
    "EUR": {"rate": 1.09, "fa": "یورو", "en": "Euro", "symbol": "€"},
    "CAD": {"rate": 0.73, "fa": "دلار کانادا", "en": "Canadian dollar", "symbol": "C$"},
    "AUD": {"rate": 0.66, "fa": "دلار استرالیا", "en": "Australian dollar", "symbol": "A$"},
    "GBP": {"rate": 1.34, "fa": "پوند بریتانیا", "en": "Pound sterling", "symbol": "£"},
    "AED": {"rate": 0.272, "fa": "درهم امارات", "en": "UAE dirham", "symbol": "AED"},
    "OMR": {"rate": 2.60, "fa": "ریال عمان", "en": "Omani rial", "symbol": "OMR"},
    "TRY": {"rate": 0.028, "fa": "لیر ترکیه", "en": "Turkish lira", "symbol": "₺"},
    "SEK": {"rate": 0.095, "fa": "کرون سوئد", "en": "Swedish krona", "symbol": "kr"},
    "DKK": {"rate": 0.146, "fa": "کرون دانمارک", "en": "Danish krone", "symbol": "kr"},
    "NZD": {"rate": 0.60, "fa": "دلار نیوزیلند", "en": "New Zealand dollar", "symbol": "NZ$"},
}

EDUCATION_LEVELS = [
    {"id": "highschool", "rank": 1, "fa": "دیپلم متوسطه", "en": "High school diploma"},
    {"id": "diploma", "rank": 2, "fa": "دیپلم فنی و حرفه‌ای یا کاردانی", "en": "Technical diploma / college certificate"},
    {"id": "associate", "rank": 3, "fa": "کاردانی پیشرفته یا فوق دیپلم", "en": "Associate degree"},
    {"id": "bachelor", "rank": 4, "fa": "کارشناسی", "en": "Bachelor's degree"},
    {"id": "master", "rank": 5, "fa": "کارشناسی ارشد", "en": "Master's degree"},
    {"id": "phd", "rank": 6, "fa": "دکترا", "en": "Doctorate"},
]

# ---------------------------------------------------------------------------
# Language test meta-data: raw score -> CLB level (Canadian benchmark).
# Each entry gives, per skill, the ascending thresholds [min_score, clb].
# CLB is used as the common internal yardstick; CEFR is derived from it.
# ---------------------------------------------------------------------------
LANGUAGE_TESTS = [
    {
        "id": "ielts",
        "group": "en",
        "fa": "آیلتس",
        "en": "IELTS",
        "kind": "band",
        "scale": {"min": 0, "max": 9, "step": 0.5, "labelFa": "نمره هر مهارت (۰ تا ۹)", "labelEn": "Band per skill (0-9)"},
        "thresholds": {
            "listening": [[0, 0], [4.5, 4], [5.0, 5], [5.5, 6], [6.0, 7], [7.5, 8], [8.0, 9], [8.5, 10]],
            "reading": [[0, 0], [3.5, 4], [4.0, 5], [5.0, 6], [6.0, 7], [6.5, 8], [7.0, 9], [7.5, 10]],
            "writing": [[0, 0], [4.0, 4], [5.0, 5], [5.5, 6], [6.0, 7], [6.5, 8], [7.0, 9], [7.5, 10]],
            "speaking": [[0, 0], [4.0, 4], [5.0, 5], [5.5, 6], [6.0, 7], [6.5, 8], [7.0, 9], [7.5, 10]],
        },
    },
    {
        "id": "celpip",
        "group": "en",
        "fa": "سلپیپ",
        "en": "CELPIP",
        "kind": "band",
        "scale": {"min": 0, "max": 12, "step": 1, "labelFa": "نمره هر مهارت (۰ تا ۱۲)", "labelEn": "Score per skill (0-12)"},
        "directClb": True,
        "thresholds": {
            "listening": [[0, 0], [4, 4], [5, 5], [6, 6], [7, 7], [8, 8], [9, 9], [10, 10]],
            "reading": [[0, 0], [4, 4], [5, 5], [6, 6], [7, 7], [8, 8], [9, 9], [10, 10]],
            "writing": [[0, 0], [4, 4], [5, 5], [6, 6], [7, 7], [8, 8], [9, 9], [10, 10]],
            "speaking": [[0, 0], [4, 4], [5, 5], [6, 6], [7, 7], [8, 8], [9, 9], [10, 10]],
        },
    },
    {
        "id": "pte",
        "group": "en",
        "fa": "پی‌تی‌ای آکادمیک",
        "en": "PTE Academic",
        "kind": "band",
        "scale": {"min": 10, "max": 90, "step": 1, "labelFa": "نمره هر مهارت (۱۰ تا ۹۰)", "labelEn": "Score per skill (10-90)"},
        "thresholds": {
            "listening": [[0, 0], [36, 4], [43, 5], [50, 6], [58, 7], [68, 8], [79, 9], [84, 10]],
            "reading": [[0, 0], [36, 4], [43, 5], [50, 6], [58, 7], [68, 8], [79, 9], [84, 10]],
            "writing": [[0, 0], [36, 4], [43, 5], [50, 6], [58, 7], [68, 8], [79, 9], [84, 10]],
            "speaking": [[0, 0], [36, 4], [43, 5], [50, 6], [58, 7], [68, 8], [79, 9], [84, 10]],
        },
    },
    {
        "id": "toefl",
        "group": "en",
        "fa": "تافل اینترنتی",
        "en": "TOEFL iBT",
        "kind": "band",
        "scale": {"min": 0, "max": 120, "step": 1, "labelFa": "نمره هر مهارت (۰ تا ۳۰)", "labelEn": "Score per skill (0-30)"},
        "thresholds": {
            "listening": [[0, 0], [12, 4], [17, 5], [20, 6], [22, 7], [24, 8], [27, 9], [29, 10]],
            "reading": [[0, 0], [12, 4], [17, 5], [20, 6], [22, 7], [24, 8], [27, 9], [29, 10]],
            "writing": [[0, 0], [14, 4], [18, 5], [21, 6], [23, 7], [25, 8], [28, 9], [30, 10]],
            "speaking": [[0, 0], [14, 4], [18, 5], [21, 6], [23, 7], [25, 8], [28, 9], [30, 10]],
        },
    },
    {
        "id": "duolingo",
        "group": "en",
        "fa": "دولینگو",
        "en": "Duolingo English Test",
        "kind": "band",
        "scale": {"min": 10, "max": 160, "step": 1, "labelFa": "نمره کل (۱۰ تا ۱۶۰)", "labelEn": "Overall score (10-160)"},
        "overallOnly": True,
        "thresholds": {
            "overall": [[0, 0], [75, 4], [85, 5], [95, 6], [105, 7], [120, 8], [130, 9], [140, 10]],
        },
    },
    {
        "id": "goethe",
        "group": "de",
        "fa": "گوته یا تلک آلمانی",
        "en": "Goethe / telc German",
        "kind": "cefr",
        "cefr": ["A1", "A2", "B1", "B2", "C1", "C2"],
        "labelFa": "سطح مدرک آلمانی",
        "labelEn": "German certificate level",
    },
    {
        "id": "tcf",
        "group": "fr",
        "fa": "تی‌سی‌اف فرانسه",
        "en": "TCF French",
        "kind": "band",
        "scale": {"min": 100, "max": 699, "step": 1, "labelFa": "نمره هر مهارت (۱۰۰ تا ۶۹۹)", "labelEn": "Score per skill (100-699)"},
        "thresholds": {
            "listening": [[0, 0], [331, 4], [369, 5], [397, 6], [453, 7], [499, 8], [523, 9], [549, 10]],
            "reading": [[0, 0], [342, 4], [375, 5], [406, 6], [458, 7], [502, 8], [526, 9], [549, 10]],
            "writing": [[0, 0], [4, 4], [6, 5], [8, 6], [10, 7], [12, 8], [14, 9], [16, 10]],
            "speaking": [[0, 0], [4, 4], [6, 5], [8, 6], [10, 7], [12, 8], [14, 9], [16, 10]],
        },
    },
    {
        "id": "tef",
        "group": "fr",
        "fa": "تی‌ای‌اف فرانسه",
        "en": "TEF French",
        "kind": "band",
        "scale": {"min": 0, "max": 900, "step": 1, "labelFa": "نمره هر مهارت (۰ تا ۹۰۰)", "labelEn": "Score per skill (0-900)"},
        "thresholds": {
            "listening": [[0, 0], [316, 4], [352, 5], [378, 6], [434, 7], [472, 8], [502, 9], [526, 10]],
            "reading": [[0, 0], [324, 4], [352, 5], [378, 6], [428, 7], [472, 8], [502, 9], [526, 10]],
            "writing": [[0, 0], [4, 4], [6, 5], [8, 6], [10, 7], [12, 8], [14, 9], [16, 10]],
            "speaking": [[0, 0], [4, 4], [6, 5], [8, 6], [10, 7], [12, 8], [14, 9], [16, 10]],
        },
    },
]

# ---------------------------------------------------------------------------
# Criterion catalogue.  Every criterion used anywhere in the dataset has a
# bilingual label, an improvement hint and a radar category.
# ---------------------------------------------------------------------------
CRITERIA_LABELS = {
    "age": ("سن متقاضی", "Applicant age", "سن", "age",
            "کاهش سن در زمان ارسال درخواست یا انتخاب مسیری که سقف سنی بالاتری دارد",
            "Apply before the age band drops, or choose a route with a higher age ceiling"),
    "education": ("سطح تحصیلات", "Education level", "تحصیلات", "education",
                  "ارتقای مدرک یا دریافت ارزیابی رسمی مدارک برای معادل‌سازی کامل",
                  "Upgrade the credential or obtain a formal credential assessment"),
    "education_stem": ("تحصیلات در رشته‌های فنی، مهندسی و علوم پایه", "STEM qualification", "تحصیلات", "education",
                       "گذراندن دوره تکمیلی معتبر در رشته‌های فنی و علوم پایه",
                       "Complete an accredited STEM specialisation"),
    "education_eca": ("ارزیابی مدارک تحصیلی", "Credential assessment (ECA)", "تحصیلات", "education",
                      "درخواست ارزیابی رسمی مدارک پیش از تشکیل پرونده",
                      "Request a formal credential assessment before applying"),
    "language_en": ("مهارت زبان انگلیسی در چهار مهارت", "English proficiency across four skills", "زبان", "language",
                    "ارتقای دست‌کم یک سطح در هر چهار مهارت شنیداری، خواندن، نوشتن و گفتاری",
                    "Raise each of the four skills by at least one band"),
    "language_de": ("مهارت زبان آلمانی", "German proficiency", "زبان", "language",
                    "ارتقای سطح آلمانی به سطح بعدی با مدرک گوته یا تلک",
                    "Move up one German level with a Goethe or telc certificate"),
    "language_fr": ("مهارت زبان فرانسه", "French proficiency", "زبان", "language",
                    "ارتقای سطح فرانسه با مدرک تی‌سی‌اف یا تی‌ای‌اف",
                    "Move up one French level with a TCF or TEF certificate"),
    "language_tr": ("مهارت زبان ترکی", "Turkish proficiency", "زبان", "language",
                    "ارتقای سطح ترکی با مدرک رسمی آزمون تومر", "Move up one Turkish level with an official exam certificate"),
    "language_it": ("مهارت زبان ایتالیایی", "Italian proficiency", "زبان", "language",
                    "کسب مدرک زبان ایتالیایی در سطح میانی", "Obtain an intermediate Italian certificate"),
    "language_es": ("مهارت زبان اسپانیایی", "Spanish proficiency", "زبان", "language",
                    "کسب مدرک زبان اسپانیایی در سطح میانی", "Obtain an intermediate Spanish certificate"),
    "language_sv": ("مهارت زبان سوئدی", "Swedish proficiency", "زبان", "language",
                    "کسب مدرک زبان سوئدی برای تسریع ورود به بازار کار", "Obtain a Swedish certificate to speed up labour-market entry"),
    "language_da": ("مهارت زبان دانمارکی", "Danish proficiency", "زبان", "language",
                    "کسب مدرک زبان دانمارکی برای تسریع ورود به بازار کار", "Obtain a Danish certificate to speed up labour-market entry"),
    "language_nl": ("مهارت زبان هلندی", "Dutch proficiency", "زبان", "language",
                    "کسب مدرک زبان هلندی برای اقامت دائم و بازار کار", "Obtain a Dutch certificate for settlement and employment"),
    "language_second": ("زبان رسمی دوم", "Second official language", "زبان", "language",
                        "افزودن مدرک زبان رسمی دوم با حداقل سطح میانی",
                        "Add a second official-language certificate at intermediate level"),
    "overseas_experience": ("سابقه کار خارج از کشور مقصد", "Skilled experience outside the destination", "سابقه کار", "experience",
                            "تکمیل سابقه کار تمام‌وقت و مستند در حوزه شغلی اصلی",
                            "Build verifiable full-time experience in the primary occupation"),
    "in_country_experience": ("سابقه کار در کشور مقصد", "Work experience inside the destination", "سابقه کار", "experience",
                              "کسب سابقه کار یا کارآموزی داخل کشور مقصد",
                              "Gain work or internship experience inside the destination country"),
    "total_experience": ("سابقه کار کل", "Total skilled work experience", "سابقه کار", "experience",
                         "افزایش سابقه کار پیوسته با بیمه و قرارداد قابل استناد",
                         "Increase continuous, documented work experience"),
    "indemand_occupation": ("شغل مورد نیاز بازار کار", "Occupation on the in-demand list", "سابقه کار", "experience",
                            "انتقال به یکی از مشاغل فهرست مورد نیاز یا دریافت گواهی مهارت آن شغل",
                            "Move into an in-demand occupation or obtain its skills certification"),
    "job_offer": ("جاب‌آفر رسمی", "Formal job offer", "سازگاری", "adaptability",
                  "دریافت پیشنهاد شغلی رسمی از کارفرمای دارای مجوز",
                  "Secure a formal offer from a licensed employer"),
    "spouse": ("امتیاز همسر", "Spouse or partner points", "سازگاری", "adaptability",
               "بهبود مدرک، زبان یا سابقه کار همسر برای کسب امتیاز همراه",
               "Improve the spouse's education, language or work history"),
    "spouse_language": ("مهارت زبان همسر", "Spouse language proficiency", "زبان", "language",
                        "کسب مدرک زبان پایه برای همسر",
                        "Obtain a basic language certificate for the spouse"),
    "funds": ("تمکن مالی در دسترس", "Available settlement funds", "تمکن مالی", "funds",
              "تأمین و مستندسازی مانده حساب و منابع مالی قابل انتقال",
              "Secure and document liquid settlement funds"),
    "investment": ("سرمایه‌گذاری یا سرمایه کسب‌وکار", "Investment or business capital", "تمکن مالی", "funds",
                   "تأمین حداقل سرمایه لازم برای مسیر سرمایه‌گذاری",
                   "Reach the minimum capital required by the investment route"),
    "remote_income": ("درآمد دورکاری ماهانه", "Monthly remote income", "تمکن مالی", "funds",
                      "افزایش درآمد قراردادی مستند و پایدار",
                      "Increase documented, stable contract income"),
    "salary": ("سطح حقوق پیشنهادی", "Offered salary level", "سابقه کار", "experience",
               "مذاکره برای حقوق بالاتر یا انتخاب شغلی با نرخ بازار بالاتر",
               "Negotiate a higher salary or target a better-paid occupation"),
    "adaptability": ("فاکتورهای سازگاری", "Adaptability factors", "سازگاری", "adaptability",
                     "افزودن سابقه تحصیل، کار یا بستگان درجه یک در کشور مقصد",
                     "Add study, work or close-family ties in the destination"),
    "nomination": ("نامزدی ایالت یا استان", "State or provincial nomination", "سازگاری", "adaptability",
                   "ثبت درخواست در برنامه‌های نامزدی استانی با شرایط متناسب",
                   "Apply to provincial or state nomination streams that match the profile"),
    "licensing": ("مجوز حرفه‌ای در کشور مقصد", "Professional licence in the destination", "سابقه کار", "experience",
                  "شروع فرآیند معادل‌سازی و مجوز حرفه‌ای",
                  "Start the professional licensing and recognition process"),
    "business_plan": ("برنامه کسب‌وکار و نوآوری", "Business plan and innovation", "تمکن مالی", "funds",
                      "تدوین برنامه کسب‌وکار پذیرفته‌شده توسط نهاد تأییدکننده",
                      "Prepare a business plan accepted by a designated body"),
    "study_offer": ("پذیرش تحصیلی معتبر", "Valid study admission", "تحصیلات", "education",
                    "دریافت پذیرش از مؤسسه آموزش عالی شناخته‌شده",
                    "Obtain admission from a recognised institution"),
    "employer_sponsor": ("حمایت کارفرمای معتبر", "Accredited employer sponsorship", "سازگاری", "adaptability",
                        "یافتن کارفرمای دارای مجوز حمایت از اتباع خارجی",
                        "Find an employer licensed to sponsor foreign nationals"),
    "achievement": ("دستاوردهای حرفه‌ای و علمی", "Professional and academic achievements", "سازگاری", "adaptability",
                    "مستندسازی دستاوردها، انتشارات، جوایز و نقش رهبری",
                    "Document achievements, publications, awards and leadership"),
    "citizenship_path": ("مسیر تابعیت", "Pathway to citizenship", "سازگاری", "adaptability",
                         "بررسی شرایط اقامت دائم و تابعیت در مسیر انتخابی",
                         "Review permanent residence and citizenship conditions"),
}

# Currency formatting hints
FA = "fa"
PRIMARY = "primary"


def criterion(cid, maximum, rule, label=None, note_fa=None, note_en=None, gate=False):
    fa, en, short_fa, category, action_fa, action_en = CRITERIA_LABELS[cid]
    if label:
        fa, en = label
    return {
        "id": cid,
        "labelFa": fa,
        "labelEn": en,
        "shortFa": short_fa,
        "category": category,
        "max": maximum,
        "rule": rule,
        "actionFa": action_fa,
        "actionEn": action_en,
        "noteFa": note_fa,
        "noteEn": note_en,
        "gate": gate,
    }


def age_bands(bands, hard_max=None):
    """bands: list of (min_age, max_age, points)."""
    return {"kind": "age_band", "bands": [list(b) for b in bands], "hardMax": hard_max}


def edu_rank(mapping, note_fa=None, note_en=None):
    return {"kind": "education_rank", "map": mapping}


def lang_skills(group, bands, cap=None, tests=None):
    """bands: descending list of (min_clb, points_per_skill)."""
    return {
        "kind": "language_skills",
        "group": group,
        "bands": [list(b) for b in bands],
        "cap": cap,
        "tests": tests,
    }


def lang_single(group, bands, tests=None, label_fa=None):
    """Single-score language criterion (e.g. bonus for a second language)."""
    return {
        "kind": "language_best",
        "group": group,
        "bands": [list(b) for b in bands],
        "tests": tests,
    }


def exp_band(scope, bands, teer=None, label=None):
    return {"kind": "experience_band", "scope": scope, "bands": [list(b) for b in bands], "teer": teer}


def flag(key, points):
    return {"kind": "flag", "key": key, "points": points}


def salary_band(bands, metric="annualSalaryUsd"):
    return {"kind": "salary_band", "metric": metric, "bands": [list(b) for b in bands]}


def funds_ratio(points, gate=False, scale=1.0):
    return {"kind": "funds_ratio", "points": points, "gate": gate, "scale": scale}


def adaptability(factors, each, cap):
    return {"kind": "adaptability", "factors": factors, "each": each, "cap": cap}


def spouse_points(parts, cap):
    return {"kind": "spouse", "parts": parts, "cap": cap}


def gate(kind, **kwargs):
    """Hard eligibility gate, evaluated before scoring."""
    base = {"kind": kind, "gate": True}
    base.update(kwargs)
    return base


def fee(fa, en, amount, currency, note_fa=None, note_en=None, verified=True, payer="applicant"):
    return {
        "labelFa": fa,
        "labelEn": en,
        "amount": amount,
        "currency": currency,
        "noteFa": note_fa,
        "noteEn": note_en,
        "verified": verified,
        "payer": payer,
    }


def funds_table(currency, amounts, note_fa=None, note_en=None):
    """amounts: list of amounts indexed by family size 1..7 (then `extra`)."""
    return {
        "currency": currency,
        "byFamilySize": amounts,
        "noteFa": note_fa,
        "noteEn": note_en,
    }


def visa(
    vid,
    vtype,
    name_fa,
    name_en,
    tagline_fa,
    tagline_en,
    description_fa,
    description_en,
    official_url,
    criteria,
    gates=None,
    fees=None,
    processing_fa="",
    processing_en="",
    selectivity=0.85,
    pass_mark=None,
    max_points=None,
    requirements_fa=None,
    requirements_en=None,
    notes_fa=None,
    notes_en=None,
    settlement=None,
    best_for_fa=None,
    best_for_en=None,
    fee_confidence="verified",
    quota_fa=None,
    quota_en=None,
):
    total = sum(c["max"] for c in criteria)
    return {
        "id": vid,
        "type": vtype,
        "nameFa": name_fa,
        "nameEn": name_en,
        "taglineFa": tagline_fa,
        "taglineEn": tagline_en,
        "descriptionFa": description_fa,
        "descriptionEn": description_en,
        "officialUrl": official_url,
        "criteria": criteria,
        "gates": gates or [],
        "fees": fees or [],
        "processingTimeFa": processing_fa,
        "processingTimeEn": processing_en,
        "selectivity": selectivity,
        "passMark": pass_mark if pass_mark is not None else round(total * 0.68),
        "maxPoints": max_points if max_points is not None else total,
        "requirementsFa": requirements_fa or [],
        "requirementsEn": requirements_en or [],
        "notesFa": notes_fa or [],
        "notesEn": notes_en or [],
        "settlement": settlement,
        "bestForFa": best_for_fa or [],
        "bestForEn": best_for_en or [],
        "feeConfidence": fee_confidence,
        "quotaFa": quota_fa,
        "quotaEn": quota_en,
    }


def country(code, name_fa, name_en, flag_emoji, region, currency, authority_fa, authority_en,
            portal, portal_label_fa, portal_label_en, visas, summary_fa, summary_en,
            language_groups, timezone_fa, timezone_en, pr_path_fa, pr_path_en,
            cost_of_living_fa, cost_of_living_en, priority=3):
    return {
        "code": code,
        "nameFa": name_fa,
        "nameEn": name_en,
        "flag": flag_emoji,
        "region": region,
        "currency": currency,
        "official": {
            "authorityFa": authority_fa,
            "authorityEn": authority_en,
            "portal": portal,
            "portalLabelFa": portal_label_fa,
            "portalLabelEn": portal_label_en,
            "lastVerified": LAST_VERIFIED,
        },
        "visas": visas,
        "summaryFa": summary_fa,
        "summaryEn": summary_en,
        "languageGroups": language_groups,
        "timezoneFa": timezone_fa,
        "timezoneEn": timezone_en,
        "prPathFa": pr_path_fa,
        "prPathEn": pr_path_en,
        "costOfLivingFa": cost_of_living_fa,
        "costOfLivingEn": cost_of_living_en,
        "priority": priority,
    }
