"""تبدیل فرم چندمرحله‌ای HTML به مدل Profile با پیام خطای فارسی."""
from __future__ import annotations

from datetime import date
from typing import Any, Mapping

from pydantic import ValidationError

from app.schemas import Documents, LanguageProfile, Profile

ERRORS_FA = {
    "birth_date": "تاریخ تولد را وارد کنید.",
    "dependents": "تعداد فرزندان باید بین ۰ تا ۱۰ باشد.",
    "experience_last10": "سابقه‌ی کاری معتبر نیست.",
    "job_offer_salary": "حقوق را به‌صورت عدد مثبت وارد کنید.",
    "savings_eur": "موجودی پس‌انداز را وارد کنید.",
    "monthly_income_eur": "درآمد ماهانه را وارد کنید.",
}


def _text(form: Mapping[str, Any], key: str, default: str = "") -> str:
    value = form.get(key)
    if value is None:
        return default
    return str(value).strip()


def _bool(form: Mapping[str, Any], key: str) -> bool:
    value = form.get(key)
    return str(value).lower() in {"1", "true", "on", "yes", "بله"}


def _float(form: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    raw = _text(form, key)
    if not raw:
        return default
    raw = raw.replace("٬", "").replace(",", "").replace("،", "")
    raw = raw.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
    try:
        return float(raw)
    except ValueError:
        return default


def _int(form: Mapping[str, Any], key: str, default: int = 0) -> int:
    return int(_float(form, key, default))


def _optional_int(form: Mapping[str, Any], key: str) -> int | None:
    raw = _text(form, key)
    if not raw:
        return None
    try:
        return int(float(raw))
    except ValueError:
        return None


def _list(form: Mapping[str, Any], key: str) -> list[str]:
    getlist = getattr(form, "getlist", None)
    if callable(getlist):
        return [str(v).strip() for v in getlist(key) if str(v).strip()]
    value = form.get(key)
    return [value] if value else []


def _date(form: Mapping[str, Any]) -> date | None:
    raw = _text(form, "birth_date")
    if raw:
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return None
    year = _optional_int(form, "birth_year")
    month = _optional_int(form, "birth_month") or 1
    day = _optional_int(form, "birth_day") or 1
    if year:
        try:
            return date(year, month, day)
        except ValueError:
            return None
    return None


LEVELS = {"none", "a1", "a2", "b1", "b2", "c1", "c2"}


def _language(
    form: Mapping[str, Any],
    prefix: str,
    errors: dict[str, str] | None = None,
    label: str = "زبان",
) -> LanguageProfile:
    def score(name: str) -> float | None:
        raw = _text(form, f"{prefix}_{name}")
        if not raw:
            return None
        try:
            return float(raw.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")))
        except ValueError:
            return None

    level = (_text(form, f"{prefix}_level", "none") or "none").lower()
    if level not in LEVELS:
        if errors is not None:
            errors.setdefault(f"{prefix}_level", f"سطح {label} انتخاب‌شده معتبر نیست.")
        level = "none"

    data: dict[str, Any] = {
        "level": level,
        "test": _text(form, f"{prefix}_test"),
        "listening": score("listening"),
        "reading": score("reading"),
        "writing": score("writing"),
        "speaking": score("speaking"),
    }
    clb = _optional_int(form, f"{prefix}_clb")
    if clb:
        data["clb"] = clb
    try:
        return LanguageProfile.model_validate(data)
    except ValidationError:
        if errors is not None:
            errors.setdefault(f"{prefix}_level", f"اطلاعات {label} معتبر نیست.")
        return LanguageProfile()


def parse_profile(form: Mapping[str, Any]) -> tuple[Profile | None, dict[str, str], dict[str, Any]]:
    """خروجی: (پروفایل، خطاها، داده‌ی خام برای بازنمایش فرم)."""
    errors: dict[str, str] = {}
    birth = _date(form)
    if not birth:
        errors["birth_date"] = ERRORS_FA["birth_date"]

    data: dict[str, Any] = {
        "name": _text(form, "name") or "پروفایل من",
        "nationality": (_text(form, "nationality", "IR") or "IR").upper(),
        "residence": (_text(form, "residence", "IR") or "IR").upper(),
        "birth_date": birth or date(1995, 1, 1),
        "marital_status": _text(form, "marital_status", "single") or "single",
        "spouse_included": _bool(form, "spouse_included"),
        "dependents": _int(form, "dependents"),
        "education_level": _text(form, "education_level", "bachelor") or "bachelor",
        "education_field": _text(form, "education_field", "stem") or "stem",
        "education_country": (_text(form, "education_country", "IR") or "IR").upper(),
        "graduation_year": _optional_int(form, "graduation_year"),
        "eca": _bool(form, "eca"),
        "recognition": _text(form, "recognition", "unknown") or "unknown",
        "nz_qualification_level": _int(form, "nz_qualification_level"),
        "english": _language(form, "english", errors, "انگلیسی"),
        "german": _language(form, "german", errors, "آلمانی"),
        "french": _language(form, "french", errors, "فرانسه"),
        "occupation_title": _text(form, "occupation_title"),
        "occupation_code": _text(form, "occupation_code"),
        "occupation_shortage": _bool(form, "occupation_shortage"),
        "total_experience_years": _float(form, "total_experience_years"),
        "experience_last5": _float(form, "experience_last5"),
        "experience_last7": _float(form, "experience_last7"),
        "experience_last10": _float(form, "experience_last10"),
        "canadian_experience_years": _float(form, "canadian_experience_years"),
        "australian_experience_years": _float(form, "australian_experience_years"),
        "nz_experience_years": _float(form, "nz_experience_years"),
        "skills_assessment": _bool(form, "skills_assessment"),
        "registration_years": _float(form, "registration_years"),
        "has_job_offer": _bool(form, "has_job_offer"),
        "job_offer_country": (_text(form, "job_offer_country") or "").upper(),
        "job_offer_salary": _float(form, "job_offer_salary"),
        "job_offer_currency": (_text(form, "job_offer_currency", "EUR") or "EUR").upper(),
        "job_offer_recognized_sponsor": _bool(form, "job_offer_recognized_sponsor"),
        "job_offer_contract_years": _float(form, "job_offer_contract_years", 1.0),
        "job_offer_wage_multiple": _float(form, "job_offer_wage_multiple"),
        "job_offer_going_rate": _bool(form, "job_offer_going_rate"),
        "job_offer_shortage": _bool(form, "job_offer_shortage"),
        "savings_eur": _float(form, "savings_eur"),
        "monthly_income_eur": _float(form, "monthly_income_eur"),
        "passive_income_eur": _float(form, "passive_income_eur"),
        "remote_work": _bool(form, "remote_work"),
        "spouse_education": _text(form, "spouse_education", "none") or "none",
        "spouse_english": _language(form, "spouse_english", errors, "انگلیسی همسر"),
        "spouse_canadian_experience_years": _float(form, "spouse_canadian_experience_years"),
        "relatives_in": [c.upper() for c in _list(form, "relatives_in")],
        "prior_stay": [c.upper() for c in _list(form, "prior_stay")],
        "target_countries": [c.upper() for c in _list(form, "target_countries")],
        "priorities": _list(form, "priorities"),
        "max_budget_eur": _float(form, "max_budget_eur", 6000.0),
        "willing_to_learn_language": _bool(form, "willing_to_learn_language"),
        "documents": Documents(
            passport_valid_years=_float(form, "passport_valid_years", 3.0),
            police_clearance=_bool(form, "police_clearance"),
            medical=_bool(form, "medical"),
            eca=_bool(form, "doc_eca"),
            language_certificate=_bool(form, "language_certificate"),
            birth_certificate=_bool(form, "birth_certificate"),
            marriage_certificate=_bool(form, "marriage_certificate"),
            proof_of_funds=_bool(form, "proof_of_funds"),
            education_transcripts=_bool(form, "education_transcripts"),
            employment_letters=_bool(form, "employment_letters"),
        ),
        "notes": _text(form, "notes"),
    }

    try:
        profile = Profile.model_validate(data)
    except ValidationError as exc:
        for item in exc.errors():
            loc = ".".join(str(part) for part in item["loc"] if part != "documents")
            errors.setdefault(loc, ERRORS_FA.get(loc, "مقدار واردشده معتبر نیست."))
        return None, errors, data
    return profile, errors, data
