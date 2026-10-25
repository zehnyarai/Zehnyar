"""ثبت همه‌ی برنامه‌های مهاجرتی و اجرای یکپارچه‌ی ارزیابی."""
from __future__ import annotations

from datetime import date
from typing import Callable

from app.engine import australia, canada, germany, netherlands, newzealand, portugal, uk
from app.engine.base import all_program_meta
from app.engine.types import ProgramResult
from app.schemas import Profile

Assessor = Callable[[Profile, date], ProgramResult]

ASSESSORS: dict[str, Assessor] = {
    "ca-ee": canada.assess,
    "de-bluecard": germany.assess_blue_card,
    "de-chancenkarte": germany.assess_chancenkarte,
    "nl-hsm": netherlands.assess_hsm,
    "nl-bluecard": netherlands.assess_blue_card,
    "uk-skilled": uk.assess,
    "au-189": lambda profile, rule_date: australia.assess(profile, "189", rule_date),
    "au-190": lambda profile, rule_date: australia.assess(profile, "190", rule_date),
    "au-491": lambda profile, rule_date: australia.assess(profile, "491", rule_date),
    "nz-smc": newzealand.assess,
    "pt-d7": portugal.assess_d7,
    "pt-d8": portugal.assess_d8,
}


def assess_all(profile: Profile, rule_date: date | None = None) -> list[ProgramResult]:
    rule_date = rule_date or date.today()
    results: list[ProgramResult] = []
    for meta in all_program_meta():
        assessor = ASSESSORS.get(meta["id"])
        if not assessor:
            continue
        results.append(assessor(profile, rule_date))
    return results


def program_ids() -> list[str]:
    return [meta["id"] for meta in all_program_meta()]
