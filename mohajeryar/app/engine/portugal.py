"""موتور ارزیابی پرتغال: ویزاهای D7 (درآمد غیرفعال) و D8 (دورکاری)."""
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
from app.schemas import Profile

D7_ID = "pt-d7"
D8_ID = "pt-d8"

MIN_WAGE = 920.0
D7_SAVINGS_MONTHS = 12.0
D8_MULTIPLIER = 4.0
D8_SAVINGS = 11040.0


def _family_factor(profile: Profile) -> float:
    return 1.0 + (0.5 if profile.spouse_included else 0.0) + 0.3 * profile.dependents


def _d7(profile: Profile) -> ProgramResult:
    meta = program_meta(D7_ID)
    gaps = []
    factor_family = _family_factor(profile)
    required = MIN_WAGE * factor_family
    required_savings = MIN_WAGE * D7_SAVINGS_MONTHS * factor_family
    income = profile.passive_income_eur or profile.monthly_income_eur

    if profile.remote_work and not profile.passive_income_eur:
        gaps.append(
            gap(
                "income_type",
                "نوع درآمد",
                "major",
                "D7 برای درآمد غیرفعال (اجاره، سود سهام، بازنشستگی) است؛ درآمد دورکاری به D8 تعلق دارد.",
                "اگر دورکار هستید مسیر D8 را انتخاب کنید؛ اگر درآمد غیرفعال دارید آن را مستند کنید.",
                12,
            )
        )
    if income < required:
        gaps.append(
            gap(
                "income",
                "حداقل درآمد ماهانه",
                "blocker",
                f"درآمد ماهانه {income:,.0f} یورو است؛ حداقل {required:,.0f} یورو برای اندازه‌ی خانواده‌ی شما لازم است.",
                "درآمد پایدار غیرفعال را مستند کنید (قرارداد اجاره، سود سهام، حقوق بازنشستگی)؛ یا مسیر D8 را بررسی کنید.",
                24,
            )
        )
    if profile.savings_eur < required_savings:
        gaps.append(
            gap(
                "savings",
                "پس‌انداز لازم",
                "major",
                f"حداقل پس‌انداز {required_savings:,.0f} یورو (۱۲ برابر درآمد ماهانه) لازم است؛ موجودی شما {profile.savings_eur:,.0f} یورو است.",
                "موجودی حساب را افزایش دهید یا گواهی درآمد پایدار ارائه دهید.",
                12,
            )
        )
    if not profile.documents.proof_of_funds:
        gaps.append(
            gap(
                "proof",
                "مدارک تمکن مالی",
                "minor",
                "صورت‌حساب ۳ تا ۶ ماه و منبع درآمد لازم است.",
                "صورت‌حساب بانکی و مدارک منبع درآمد را آماده کنید.",
                6,
            )
        )

    blockers = [g for g in gaps if g.severity == "blocker"]
    status = "ineligible" if blockers else "potential" if any(g.severity == "major" for g in gaps) else "eligible"
    ratio = income / required if required else None
    band = "strong" if ratio and ratio >= 1.5 else "moderate" if ratio and ratio >= 1 else "weak"
    labels = {"strong": "قوی", "moderate": "کافی", "weak": "ناکافی"}

    factors = [
        factor("income", "درآمد ماهانه", f"{income:,.0f} یورو", round(income), round(required)),
        factor("required", "حداقل درآمد", f"{required:,.0f} یورو", note="۹۲۰ یورو + ۵۰٪ همسر + ۳۰٪ هر فرزند"),
        factor("savings", "پس‌انداز", f"{profile.savings_eur:,.0f} یورو", round(profile.savings_eur), round(required_savings)),
        factor("family", "اندازه‌ی خانواده", f"{1 + (1 if profile.spouse_included else 0) + profile.dependents} نفر"),
    ]
    costs, total_eur = build_costs(meta, profile)
    docs = documents_score(profile, needs_eca=False)
    readiness = estimate_readiness(status, ratio, gaps, docs)

    highlights = ["پس از ۵ سال اقامت قانونی، امکان اقامت دائم و شهروندی پرتغال وجود دارد."]
    if income >= required and profile.savings_eur >= required_savings:
        highlights.append("درآمد و پس‌انداز شما شرایط مالی D7 را پوشش می‌دهد.")

    return finish_result(
        meta,
        status=status,
        readiness=readiness,
        summary=f"درآمد ماهانه {income:,.0f} یورو در برابر حداقل {required:,.0f} یورو برای خانواده‌ی شما.",
        factors=factors,
        gaps=gaps,
        costs=costs,
        total_cost_eur=total_eur,
        score=round(income),
        score_threshold=round(required),
        score_unit="درآمد ماهانه (یورو)",
        score_note="آستانه بر پایه‌ی حداقل دستمزد ۲۰۲۶ پرتغال (۹۲۰ یورو) محاسبه شده است.",
        band=band,
        band_label=labels[band],
        highlights=highlights,
    )


def _d8(profile: Profile) -> ProgramResult:
    meta = program_meta(D8_ID)
    gaps = []
    factor_family = _family_factor(profile)
    required = MIN_WAGE * D8_MULTIPLIER * factor_family
    required_savings = D8_SAVINGS * factor_family
    income = profile.monthly_income_eur

    if not profile.remote_work:
        gaps.append(
            gap(
                "remote",
                "دورکاری از خارج پرتغال",
                "blocker",
                "D8 مخصوص افرادی است که برای کارفرما یا مشتری خارج از پرتغال دورکاری می‌کنند.",
                "قرارداد کار یا قرارداد فریلنسری با طرف خارج از پرتغال ارائه دهید.",
                22,
            )
        )
    if income < required:
        gaps.append(
            gap(
                "income",
                "حداقل درآمد ماهانه",
                "blocker",
                f"درآمد ماهانه {income:,.0f} یورو است؛ حداقل {required:,.0f} یورو لازم است (۴ برابر حداقل دستمزد).",
                "درآمد ماهانه‌ی پایدار (میانگین ۳ ماه) را مستند کنید یا مسیر D7 را بررسی کنید.",
                24,
            )
        )
    if profile.savings_eur < required_savings:
        gaps.append(
            gap(
                "savings",
                "پس‌انداز لازم",
                "major",
                f"حداقل پس‌انداز {required_savings:,.0f} یورو لازم است؛ موجودی شما {profile.savings_eur:,.0f} یورو است.",
                "موجودی حساب را افزایش دهید (۱۲ برابر حداقل دستمزد + سهم همراهان).",
                12,
            )
        )
    if not profile.documents.proof_of_funds:
        gaps.append(
            gap(
                "proof",
                "مدارک درآمد و تمکن",
                "minor",
                "صورت‌حساب، قرارداد کار و اظهارنامه مالیاتی لازم است.",
                "مدارک سه ماه اخیر را آماده کنید.",
                6,
            )
        )

    blockers = [g for g in gaps if g.severity == "blocker"]
    status = "ineligible" if blockers else "potential" if any(g.severity == "major" for g in gaps) else "eligible"
    ratio = income / required if required else None
    band = "strong" if ratio and ratio >= 1.5 else "moderate" if ratio and ratio >= 1 else "weak"
    labels = {"strong": "قوی", "moderate": "کافی", "weak": "ناکافی"}

    factors = [
        factor("income", "درآمد ماهانه", f"{income:,.0f} یورو", round(income), round(required)),
        factor("required", "حداقل درآمد", f"{required:,.0f} یورو", note="۳٬۶۸۰ یورو + ۵۰٪ همسر + ۳۰٪ هر فرزند"),
        factor("savings", "پس‌انداز", f"{profile.savings_eur:,.0f} یورو", round(profile.savings_eur), round(required_savings)),
        factor("remote", "دورکاری", "بله" if profile.remote_work else "خیر"),
    ]
    costs, total_eur = build_costs(meta, profile)
    docs = documents_score(profile, needs_eca=False)
    readiness = estimate_readiness(status, ratio, gaps, docs)

    highlights = [
        "D8 امکان اقامت ۲ ساله و تمدید آن را می‌دهد و پس از ۵ سال به اقامت دائم می‌رسد.",
    ]
    if income >= required:
        highlights.append("درآمد شما از آستانه‌ی ۴ برابر حداقل دستمزد عبور می‌کند.")

    return finish_result(
        meta,
        status=status,
        readiness=readiness,
        summary=f"درآمد ماهانه {income:,.0f} یورو در برابر حداقل {required:,.0f} یورو.",
        factors=factors,
        gaps=gaps,
        costs=costs,
        total_cost_eur=total_eur,
        score=round(income),
        score_threshold=round(required),
        score_unit="درآمد ماهانه (یورو)",
        score_note="حداقل درآمد D8 چهار برابر حداقل دستمزد ملی پرتغال در ۲۰۲۶ است.",
        band=band,
        band_label=labels[band],
        highlights=highlights,
    )


def assess_d7(profile: Profile, rule_date: date | None = None) -> ProgramResult:
    return _d7(profile)


def assess_d8(profile: Profile, rule_date: date | None = None) -> ProgramResult:
    return _d8(profile)
