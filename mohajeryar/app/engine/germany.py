"""موتور ارزیابی آلمان: کارت آبی اروپا و کارت فرصت (Chancenkarte)."""
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
from app.engine.utils import age_on, at_least, convert_to_eur, level_rank
from app.formatting import education_label
from app.schemas import Profile

BC_ID = "de-bluecard"
CHANCEN_ID = "de-chancenkarte"

BLUE_CARD_STANDARD = 50700.0
BLUE_CARD_REDUCED = 45934.20
OPPORTUNITY_CARD_FUNDS = 13092.0
EDU_LEVELS = {"none", "secondary", "diploma1", "diploma2"}


def _recent_graduate(profile: Profile, rule_date: date) -> bool:
    return bool(profile.graduation_year and profile.graduation_year >= rule_date.year - 3)


def _shortage(profile: Profile) -> bool:
    return profile.occupation_shortage or profile.job_offer_shortage


def _blue_card(profile: Profile, rule_date: date) -> ProgramResult:
    meta = program_meta(BC_ID)
    age = age_on(profile.birth_date, rule_date)
    gaps = []

    offer_local, offer_issue = local_offer(profile, "DE")
    salary = convert_to_eur(profile.job_offer_salary, profile.job_offer_currency) if offer_local else 0.0
    reduced = _shortage(profile) or _recent_graduate(profile, rule_date)
    threshold = BLUE_CARD_REDUCED if reduced else BLUE_CARD_STANDARD

    has_degree = profile.education_level not in EDU_LEVELS
    it_route = (
        not has_degree
        and profile.education_field in {"stem"}
        and profile.experience_last7 >= 3
    )

    if not offer_local:
        gaps.append(
            gap(
                "job_offer",
                "پیشنهاد شغلی در آلمان",
                "blocker",
                "کارت آبی بدون قرارداد کار مرتبط با مدرک صادر نمی‌شود."
                + (" پیشنهاد فعلی شما برای کشور دیگری است." if offer_issue == "other" else ""),
                "در پورتال‌های تخصصی آلمان (Make it in Germany، StepStone، LinkedIn) شغل مرتبط با مدرک پیدا کنید؛ حداقل قرارداد ۶ ماه باشد.",
                25,
            )
        )
    if not has_degree and not it_route:
        gaps.append(
            gap(
                "degree",
                "مدرک دانشگاهی یا مسیر IT",
                "blocker",
                "کارت آبی مدرک آموزش عالی شناخته‌شده می‌خواهد؛ مسیر جایگزین، ۳ سال تجربه‌ی IT در ۷ سال گذشته است.",
                "مدرک کارشناسی یا بالاتر ارائه دهید؛ یا با ۳ سال سابقه‌ی IT درخواست مسیر ویژه‌ی متخصصان IT بدهید.",
                22,
            )
        )
    if has_degree and profile.recognition == "none":
        gaps.append(
            gap(
                "recognition",
                "شناسایی مدرک در آلمان",
                "blocker",
                "مدرک شما در ANABIN به‌عنوان نامعتبر ثبت شده است؛ کارت آبی صادر نمی‌شود.",
                "با سازمان ارزیابی مدارک ایالت (ZAB) یا مسیر «شناسایی حرفه‌ای» اقدام کنید یا مدرک معتبر دیگری ارائه دهید.",
                20,
            )
        )
    elif has_degree and profile.recognition in {"unknown", "partial"}:
        gaps.append(
            gap(
                "recognition",
                "بررسی شناسایی مدرک",
                "major",
                "وضعیت مدرک شما در ANABIN مشخص نیست یا شناسایی جزئی است.",
                "نام دانشگاه و رشته را در anabin.kmk.org جست‌وجو کنید و نتیجه را همراه مدارک نگه دارید.",
                10,
            )
        )
    if offer_local and salary < threshold:
        gaps.append(
            gap(
                "salary",
                "حداقل حقوق سالانه",
                "blocker",
                f"حقوق پیشنهادی {salary:,.0f} یورو است؛ آستانه {threshold:,.0f} یورو است.",
                "یا حقوق بالاتر مذاکره کنید، یا شغلی در فهرست مشاغل کمبود نیرو/IT انتخاب کنید. فارغ‌التحصیلان سه سال اخیر نیز آستانه‌ی کاهش‌یافته دارند.",
                18,
            )
        )
    if offer_local and profile.job_offer_contract_years < 0.5:
        gaps.append(
            gap(
                "contract",
                "مدت قرارداد",
                "major",
                "قرارداد کار باید حداقل ۶ ماه باشد.",
                "قرارداد یک‌ساله یا دائمی ارائه دهید.",
                8,
            )
        )
    if level_rank(profile.german.level) < level_rank("a1"):
        gaps.append(
            gap(
                "german",
                "زبان آلمانی برای اقامت دائم",
                "minor",
                "برای کارت آبی زبان آلمانی الزامی نیست، اما برای اقامت دائم ۲۱ ماهه به B1 و برای ۲۷ ماهه به A1 نیاز دارید.",
                "از A1 شروع کنید و تا B1 پیش بروید؛ مسیر اقامت دائم را ۶ ماه کوتاه می‌کند.",
                6,
            )
        )

    blockers = [g for g in gaps if g.severity == "blocker"]
    if blockers:
        status = "needs_job_offer" if not offer_local else "ineligible"
    elif any(g.key == "recognition" for g in gaps):
        status = "potential"
    else:
        status = "eligible"

    ratio = salary / threshold if threshold else 0
    band, band_label = None, None
    if salary >= threshold * 1.15:
        band, band_label = "strong", "قوی"
    elif salary >= threshold:
        band, band_label = "moderate", "کافی"
    elif salary >= threshold * 0.9:
        band, band_label = "competitive", "نزدیک به آستانه"
    else:
        band, band_label = "weak", "پایین‌تر از آستانه"

    factors = [
        factor("salary", "حقوق سالانه", f"{salary:,.0f} یورو", salary, threshold, note="معیار کاهش‌یافته" if reduced else "معیار عمومی"),
        factor("threshold", "آستانه‌ی قانونی ۲۰۲۶", f"{threshold:,.0f} یورو", None, None),
        factor("age", "سن", f"{age} سال"),
        factor("degree", "مدرک", education_label(profile.education_level), note="شناسایی: " + {"full": "کامل", "partial": "جزئی", "none": "ردشده", "unknown": "نامشخص"}.get(profile.recognition, profile.recognition)),
        factor("shortage", "شغل کمبود نیرو / فارغ‌التحصیل اخیر", "بله" if reduced else "خیر"),
    ]
    costs, total_eur = build_costs(meta, profile)
    docs = documents_score(profile, needs_eca=False)
    readiness = estimate_readiness(status, ratio if ratio else None, gaps, docs)

    highlights = []
    if reduced:
        highlights.append("شما مشمول آستانه‌ی کاهش‌یافته‌ی ۴۵٬۹۳۴٫۲۰ یورو هستید.")
    if salary >= threshold:
        highlights.append("حقوق پیشنهادی از آستانه‌ی قانونی عبور می‌کند.")
    if it_route:
        highlights.append("مسیر ویژه‌ی متخصصان IT بدون مدرک دانشگاهی برای شما باز است.")
    if level_rank(profile.german.level) >= level_rank("b1"):
        highlights.append("آلمانی B1 دارید؛ اقامت دائم پس از ۲۱ ماه ممکن است.")
    if profile.spouse_included:
        highlights.append("همسر و فرزندان می‌توانند در قالب پیوست خانواده همراه شوند.")

    summary = (
        "بدون پیشنهاد شغلی در آلمان، این مسیر فعلاً باز نیست."
        if not offer_local
        else f"با حقوق {salary:,.0f} یورو و آستانه‌ی {threshold:,.0f} یورو، "
        + ("شرایط کارت آبی را دارید." if status == "eligible" else "برای رسیدن به شرایط باید شکاف‌ها را رفع کنید.")
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
        score=round(salary),
        score_threshold=threshold,
        score_unit="حقوق سالانه (یورو)",
        score_note="آستانه‌ی ۲۰۲۶ برای مشاغل کمبود نیرو، فارغ‌التحصیلان سه سال اخیر و متخصصان IT بدون مدرک پایین‌تر است.",
        band=band,
        band_label=band_label,
        highlights=highlights,
    )


def _chancenkarte_points(profile: Profile, rule_date: date) -> tuple[int, list[tuple[str, int]]]:
    age = age_on(profile.birth_date, rule_date)
    items: list[tuple[str, int]] = []
    if profile.recognition == "partial":
        items.append(("شناسایی جزئی مدرک", 4))
    if profile.education_level not in EDU_LEVELS and _shortage(profile):
        items.append(("مدرک در شغل کمبود نیرو", 1))
    if profile.experience_last7 >= 5:
        items.append(("۵ سال سابقه در ۷ سال", 3))
    elif profile.experience_last5 >= 2:
        items.append(("۲ سال سابقه در ۵ سال", 2))
    german = profile.german.level
    gpts = {"a2": 1, "b1": 2, "b2": 3, "c1": 3, "c2": 3}.get(german, 0)
    if gpts:
        items.append((f"زبان آلمانی {german.upper()}", gpts))
    if level_rank(profile.english.level) >= level_rank("c1"):
        items.append(("انگلیسی C1+", 1))
    if age <= 35:
        items.append(("سن ۳۵ سال یا کمتر", 2))
    elif age <= 40:
        items.append(("سن ۳۶ تا ۴۰ سال", 1))
    if "DE" in profile.prior_stay:
        items.append(("اقامت قبلی در آلمان", 1))
    spouse_ok = profile.spouse_included and profile.spouse_education not in {"none", "secondary"} and (
        level_rank(profile.spouse_english.level) >= level_rank("b2")
        or level_rank(profile.german.level) >= level_rank("b1")
    )
    if spouse_ok:
        items.append(("همسر نیز واجد شرایط", 1))
    return sum(points for _, points in items), items


def _chancenkarte(profile: Profile, rule_date: date) -> ProgramResult:
    meta = program_meta(CHANCEN_ID)
    gaps = []
    points, items = _chancenkarte_points(profile, rule_date)
    direct = profile.recognition == "full" and profile.education_level not in {"none", "secondary"}
    language_ok = at_least(profile.german.level, "a1") or at_least(profile.english.level, "b2")
    offer_local, offer_issue = local_offer(profile, "DE")
    funds_ok = profile.savings_eur >= OPPORTUNITY_CARD_FUNDS or (
        offer_local and profile.job_offer_contract_years >= 1
    )

    if not direct and points < 6:
        gaps.append(
            gap(
                "points",
                "امتیاز کافی در سیستم ۶ امتیازی",
                "blocker",
                f"امتیاز فعلی شما {points} است؛ حداقل ۶ امتیاز لازم است.",
                "بیشترین اثر را زبان آلمانی (تا ۳ امتیاز)، سابقه‌ی کار (تا ۳ امتیاز) و شناسایی جزئی مدرک (۴ امتیاز) دارد.",
                22,
            )
        )
    if not language_ok:
        gaps.append(
            gap(
                "language_floor",
                "حداقل شرط زبان",
                "blocker",
                "برای کارت فرصت حداقل آلمانی A1 یا انگلیسی B2 لازم است.",
                "یک آزمون A1 آلمانی (Goethe/telc) یا مدرک انگلیسی B2 (آیلتس ۵٫۵ تا ۶٫۵) ارائه دهید.",
                18,
            )
        )
    if not funds_ok:
        gaps.append(
            gap(
                "funds",
                "اثبات تمکن مالی ۱۲ ماه",
                "blocker",
                f"برای ۱۲ ماه حدود {OPPORTUNITY_CARD_FUNDS:,.0f} یورو (یا قرارداد کار پاره‌وقت) لازم است.",
                "حساب مسدود (Sperrkonto) باز کنید یا قرارداد کار پاره‌وقت حداقل ۲۰ ساعت در هفته ارائه دهید.",
                14,
            )
        )
    if profile.recognition in {"unknown", "partial"} and not direct:
        gaps.append(
            gap(
                "recognition",
                "شناسایی مدرک",
                "minor",
                "شناسایی کامل مدرک، شما را از مسیر امتیازی معاف می‌کند.",
                "وضعیت مدرک را در ANABIN بررسی و در صورت نیاز درخواست ارزیابی بدهید.",
                8,
            )
        )

    blockers = [g for g in gaps if g.severity == "blocker"]
    if blockers:
        status = "potential" if (direct or points >= 5) and language_ok else "ineligible"
    else:
        status = "eligible"

    ratio = (points / 6) if not direct else 1.2
    band, band_label = None, None
    if direct:
        band, band_label = "strong", "مسیر مستقیم"
    elif points >= 8:
        band, band_label = "strong", "قوی"
    elif points >= 6:
        band, band_label = "moderate", "کافی"
    else:
        band, band_label = "weak", "ناکافی"

    factors = [factor("points_item", label, f"{value:+d}", value) for label, value in items]
    factors.append(factor("total", "جمع امتیاز", f"{points} از ۶", points, 6))
    factors.append(factor("language", "شرط زبان", "برقرار" if language_ok else "برقرار نیست"))
    factors.append(factor("funds", "تمکن مالی", "برقرار" if funds_ok else "برقرار نیست"))

    costs, total_eur = build_costs(meta, profile)
    docs = documents_score(profile, needs_eca=False)
    readiness = estimate_readiness(status, ratio, gaps, docs)

    highlights = []
    if direct:
        highlights.append("مدرک شما کاملاً شناخته‌شده است؛ نیازی به امتیاز ۶ ندارید.")
    if points >= 6:
        highlights.append(f"امتیاز شما {points} از ۶ است.")
    if at_least(profile.german.level, "b1"):
        highlights.append("سطح آلمانی شما شانس استخدام در دوره‌ی جست‌وجوی کار را زیاد می‌کند.")
    if profile.savings_eur >= OPPORTUNITY_CARD_FUNDS:
        highlights.append("تمکن مالی ۱۲ ماه را پوشش می‌دهید.")

    summary = (
        f"امتیاز کارت فرصت شما {points} از ۶ است."
        if not direct
        else "مدرک شما مسیر مستقیم کارت فرصت را باز می‌کند."
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
        score=points,
        score_threshold=6,
        score_unit="امتیاز",
        score_note="حداقل ۶ امتیاز از ۸ معیار؛ امتیازهای هر دسته با هم جمع نمی‌شوند (بالاترین سطح ملاک است).",
        band=band,
        band_label=band_label,
        highlights=highlights,
    )


def assess_blue_card(profile: Profile, rule_date: date | None = None) -> ProgramResult:
    return _blue_card(profile, rule_date or date.today())


def assess_chancenkarte(profile: Profile, rule_date: date | None = None) -> ProgramResult:
    return _chancenkarte(profile, rule_date or date.today())
