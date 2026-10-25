"""زیرساخت مشترک برنامه‌های مهاجرتی: فراداده، هزینه‌ها، آمادگی."""
from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path

from app.engine.types import CostItem, Factor, Gap, ProgramResult, Source, Step
from app.formatting import fa_digits
from app.engine.utils import convert_to_eur
from app.schemas import Profile

RULES_FILE = Path(__file__).resolve().parent.parent / "rules" / "programs.json"

STATUS_LABELS = {
    "eligible": "شرایط پایه را دارید",
    "potential": "با رفع چند شکاف ممکن است",
    "needs_job_offer": "نیازمند پیشنهاد شغلی",
    "ineligible": "فعلاً واجد شرایط نیست",
}

STATUS_ORDER = {"eligible": 3, "potential": 2, "needs_job_offer": 1, "ineligible": 0}


@lru_cache(maxsize=1)
def _load() -> dict:
    return json.loads(RULES_FILE.read_text(encoding="utf-8"))


def all_program_meta() -> list[dict]:
    return list(_load()["programs"])


def program_meta(program_id: str) -> dict:
    for item in _load()["programs"]:
        if item["id"] == program_id:
            return item
    raise KeyError(program_id)


def rules_verified_on() -> date:
    return date.fromisoformat(_load()["verified_on"])


def meta_sources(meta: dict) -> list[Source]:
    return [Source(**s) for s in meta.get("sources", [])]


def _family_counts(profile: Profile) -> dict[str, int]:
    return {
        "applicant": 1,
        "spouse": 1 if profile.spouse_included else 0,
        "child": profile.dependents,
        "family": 1 + (1 if profile.spouse_included else 0) + profile.dependents,
    }


def local_offer(profile: Profile, country_code: str) -> tuple[bool, str | None]:
    """آیا پیشنهاد شغلی کاربر برای همین کشور است؟

    خروجی: (معتبر بودن، دلیل نامعتبر بودن)
    دلیل‌ها: ``none`` (پیشنهادی نیست) یا ``other`` (پیشنهاد برای کشور دیگری است).
    """
    if not profile.has_job_offer:
        return False, "none"
    if (profile.job_offer_country or "").upper() != country_code.upper():
        return False, "other"
    return True, None


def build_costs(
    meta: dict,
    profile: Profile,
    include_labels: set[str] | None = None,
    years: float | None = None,
    include_extras: bool = True,
) -> tuple[list[CostItem], float]:
    """ساخت فهرست هزینه‌ها و جمع آن‌ها به یورو.

    آیتم‌های «قابل بازگشت» (مانند اثبات تمکن) در جمع محاسبه نمی‌شوند.
    """
    counts = _family_counts(profile)
    items: list[CostItem] = []
    total_eur = 0.0
    for fee in meta.get("fees", []):
        if include_labels is not None and fee["label"] not in include_labels:
            continue
        per = fee.get("per", "applicant")
        count = counts.get(per, 1)
        multiplier = 1.0
        if years is not None and fee.get("per_year"):
            multiplier = max(1.0, float(years))
            count = max(count, 1)
        amount = float(fee["amount"]) * count * multiplier
        if amount <= 0:
            continue
        refundable = bool(fee.get("refundable"))
        items.append(
            CostItem(
                label=fee["label"],
                amount=amount,
                currency=fee["currency"],
                note=fee.get("note"),
                approximate=bool(fee.get("approximate")),
                refundable=refundable,
            )
        )
        if not refundable:
            total_eur += convert_to_eur(amount, fee["currency"])

    for extra in (meta.get("extra_costs", []) if include_extras else []):
        items.append(
            CostItem(
                label=extra["label"],
                amount=float(extra["amount"]),
                currency=extra.get("currency", "EUR"),
                note=extra.get("note"),
                approximate=bool(extra.get("approximate", True)),
                refundable=bool(extra.get("refundable")),
            )
        )
        if not extra.get("refundable"):
            total_eur += convert_to_eur(float(extra["amount"]), extra["currency"])
    return items, round(total_eur)


def documents_score(profile: Profile, needs_eca: bool = False) -> float:
    checks = [
        profile.documents.passport_valid_years >= 2,
        profile.documents.police_clearance,
        profile.documents.medical,
        profile.documents.birth_certificate,
        profile.documents.education_transcripts,
        profile.documents.employment_letters,
        profile.documents.language_certificate,
        profile.documents.proof_of_funds,
        (profile.eca or profile.documents.eca) if needs_eca else True,
    ]
    if profile.marital_status in {"married", "common_law"} and profile.spouse_included:
        checks.append(profile.documents.marriage_certificate)
    return sum(1 for c in checks if c) / len(checks)


def estimate_readiness(
    status: str,
    ratio: float | None,
    gaps: list[Gap],
    docs: float,
    preference: float = 0.0,
) -> int:
    base = {"eligible": 86, "potential": 60, "needs_job_offer": 46, "ineligible": 18}.get(status, 30)
    if ratio is not None:
        base += max(-16.0, min(12.0, (ratio - 1.0) * 55))
    penalty = {"blocker": 18, "major": 8, "minor": 3, "info": 0}
    base -= sum(penalty.get(g.severity, 0) for g in gaps)
    base += (docs - 0.5) * 10
    base += preference * 4
    return int(max(5, min(99, round(base))))


def finish_result(
    meta: dict,
    *,
    status: str,
    readiness: int,
    summary: str,
    factors: list[Factor] | None = None,
    gaps: list[Gap] | None = None,
    costs: list[CostItem] | None = None,
    total_cost_eur: float | None = None,
    score: float | None = None,
    score_threshold: float | None = None,
    score_unit: str | None = None,
    score_note: str | None = None,
    band: str | None = None,
    band_label: str | None = None,
    highlights: list[str] | None = None,
    warnings: list[str] | None = None,
    steps: list[Step] | None = None,
    preference_score: float = 0.0,
) -> ProgramResult:
    def _fa(value):
        if not isinstance(value, str):
            return value
        import re

        spaced = re.sub(r"(?<=\d),(?=\d{3})", "\u066c", value)
        return fa_digits(spaced)

    def _fa_factor(item):
        return item.model_copy(
            update={
                "label": _fa(item.label),
                "value": _fa(item.value),
                "note": _fa(item.note),
            }
        )

    def _fa_gap(item):
        return item.model_copy(
            update={"label": _fa(item.label), "detail": _fa(item.detail), "fix": _fa(item.fix)}
        )

    def _fa_cost(item):
        return item.model_copy(update={"label": _fa(item.label), "note": _fa(item.note)})

    return ProgramResult(
        program_id=meta["id"],
        country_code=meta["country_code"],
        country_name=meta["country_name"],
        country_flag=meta["flag"],
        program_name=meta["name"],
        category=meta["category"],
        summary=_fa(summary),
        status=status,
        status_label=STATUS_LABELS[status],
        readiness=readiness,
        score=score,
        score_threshold=score_threshold,
        score_unit=score_unit,
        score_note=_fa(score_note),
        band=band,
        band_label=band_label,
        factors=[_fa_factor(item) for item in (factors or [])],
        gaps=[_fa_gap(item) for item in (gaps or [])],
        costs=[_fa_cost(item) for item in (costs or [])],
        total_cost_eur=total_cost_eur,
        timeline_months=_fa(meta.get("timeline_months")),
        pr_path=_fa(meta.get("pr_path")),
        citizenship_path=_fa(meta.get("citizenship_path")),
        official_url=meta["official_url"],
        verified_on=rules_verified_on(),
        highlights=[_fa(item) for item in (highlights or [])],
        warnings=[_fa(item) for item in (warnings or []) + meta.get("warnings", [])],
        steps=steps or [],
        sources=meta_sources(meta),
        preference_score=preference_score,
    )


def gap(
    key: str,
    label: str,
    severity: str,
    detail: str,
    fix: str,
    impact: int = 0,
) -> Gap:
    return Gap(key=key, label=label, severity=severity, detail=detail, fix=fix, impact=impact)


def factor(
    key: str,
    label: str,
    value: str,
    points: float | None = None,
    max_points: float | None = None,
    note: str | None = None,
) -> Factor:
    return Factor(
        key=key,
        label=label,
        value=value,
        points=points,
        max_points=max_points,
        note=note,
    )
