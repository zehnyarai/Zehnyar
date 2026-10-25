"""آزمون‌های موتور امتیازدهی کشورها و مشاور."""
from __future__ import annotations

from datetime import date

import pytest

from app.engine.advisor import build_roadmap, documents_checklist, rank_results
from app.engine.registry import assess_all
from app.schemas import Documents, LanguageProfile, Profile

RULE_DATE = date(2026, 10, 25)


def profile(**overrides) -> Profile:
    base = dict(
        name="آزمون",
        birth_date=date(1994, 6, 1),
        education_level="master",
        education_field="stem",
        education_country="IR",
        graduation_year=2017,
        recognition="full",
        eca=True,
        english=LanguageProfile(level="c1", test="ielts", listening=8, reading=7.5, writing=7, speaking=7),
        experience_last5=5,
        experience_last7=6,
        experience_last10=7,
        total_experience_years=8,
        documents=Documents(
            passport_valid_years=6,
            birth_certificate=True,
            education_transcripts=True,
            language_certificate=True,
            employment_letters=True,
            police_clearance=True,
            medical=True,
            proof_of_funds=True,
            eca=True,
        ),
    )
    base.update(overrides)
    return Profile(**base)


def by_id(results, program_id):
    return next(result for result in results if result.program_id == program_id)


# ------------------------------------------------------------------ کانادا
def test_canada_crs_matches_reference_table():
    result = by_id(assess_all(profile(), RULE_DATE), "ca-ee")
    assert 430 <= result.score <= 520
    assert result.score_threshold is None  # آستانه‌ی CRS ثابت نیست
    assert "CRS" in result.score_unit


def test_canada_requires_eca_and_language():
    weak = profile(
        eca=False,
        english=LanguageProfile(level="b1"),
        experience_last5=2,
        experience_last7=2,
        experience_last10=2,
        documents=Documents(),
    )
    result = by_id(assess_all(weak, RULE_DATE), "ca-ee")
    keys = {gap.key for gap in result.gaps}
    assert "eca" in keys
    assert result.status in {"potential", "ineligible"}


def test_canada_new_rules_from_november_2026():
    candidate = profile(
        has_job_offer=True,
        job_offer_country="CA",
        job_offer_salary=120000,
        job_offer_currency="CAD",
        job_offer_wage_multiple=1.6,
        canadian_experience_years=2,
    )
    before = by_id(assess_all(candidate, date(2026, 11, 1)), "ca-ee")
    after = by_id(assess_all(candidate, date(2026, 11, 10)), "ca-ee")
    assert after.score >= before.score
    assert any("نوامبر" in warning for warning in after.warnings)


# ------------------------------------------------------------------ آلمان
@pytest.mark.parametrize(
    "salary,status",
    [(45_000, "ineligible"), (46_000, "eligible"), (60_000, "eligible")],
)
def test_germany_blue_card_threshold(salary, status):
    candidate = profile(
        occupation_shortage=True,
        has_job_offer=True,
        job_offer_country="DE",
        job_offer_salary=salary,
        job_offer_currency="EUR",
        job_offer_recognized_sponsor=True,
        job_offer_contract_years=2,
        german=LanguageProfile(level="a1"),
    )
    result = by_id(assess_all(candidate, RULE_DATE), "de-bluecard")
    assert result.status == status
    assert result.score == pytest.approx(salary, rel=1e-6)


def test_germany_blue_card_requires_local_offer():
    candidate = profile(
        has_job_offer=True,
        job_offer_country="CA",
        job_offer_salary=90000,
        job_offer_currency="CAD",
    )
    result = by_id(assess_all(candidate, RULE_DATE), "de-bluecard")
    assert result.status == "needs_job_offer"
    assert any(gap.key == "job_offer" for gap in result.gaps)


def test_germany_opportunity_card_points():
    candidate = profile(
        birth_date=date(1997, 1, 1),
        education_level="bachelor",
        recognition="partial",
        experience_last5=2,
        experience_last7=2,
        experience_last10=2,
        german=LanguageProfile(level="b1"),
        english=LanguageProfile(level="b2"),
        savings_eur=14_000,
    )
    result = by_id(assess_all(candidate, RULE_DATE), "de-chancenkarte")
    assert result.score >= 6
    assert result.status == "eligible"
    assert result.score_threshold == 6


def test_germany_opportunity_card_blocked_without_money():
    candidate = profile(savings_eur=0, german=LanguageProfile(level="a1"), english=LanguageProfile(level="b1"))
    result = by_id(assess_all(candidate, RULE_DATE), "de-chancenkarte")
    assert result.status == "potential"
    assert any(g.key == "funds" and g.severity == "blocker" for g in result.gaps)


# ------------------------------------------------------------------ هلند
def test_netherlands_hsm_under_30_threshold():
    young = profile(
        birth_date=date(2000, 1, 1),
        has_job_offer=True,
        job_offer_country="NL",
        job_offer_salary=53_000,
        job_offer_currency="EUR",
        job_offer_recognized_sponsor=True,
    )
    result = by_id(assess_all(young, RULE_DATE), "nl-hsm")
    assert result.status == "eligible"
    assert result.score_threshold == pytest.approx(4357, rel=1e-6)


def test_netherlands_hsm_reduced_scheme():
    graduate = profile(
        education_country="NL",
        graduation_year=2026,
        has_job_offer=True,
        job_offer_country="NL",
        job_offer_salary=40_000,
        job_offer_currency="EUR",
        job_offer_recognized_sponsor=True,
    )
    result = by_id(assess_all(graduate, RULE_DATE), "nl-hsm")
    assert result.score_threshold == pytest.approx(3122, rel=1e-6)


def test_netherlands_requires_recognized_sponsor():
    candidate = profile(
        has_job_offer=True,
        job_offer_country="NL",
        job_offer_salary=70_000,
        job_offer_currency="EUR",
        job_offer_recognized_sponsor=False,
    )
    result = by_id(assess_all(candidate, RULE_DATE), "nl-hsm")
    assert result.status in {"potential", "ineligible"}
    assert any(gap.key == "sponsor" for gap in result.gaps)


# ------------------------------------------------------------------ بریتانیا
def test_uk_skilled_worker_threshold_and_going_rate():
    candidate = profile(
        english=LanguageProfile(level="c1"),
        has_job_offer=True,
        job_offer_country="GB",
        job_offer_salary=46_000,
        job_offer_currency="GBP",
        job_offer_recognized_sponsor=True,
        job_offer_going_rate=True,
        job_offer_contract_years=5,
    )
    result = by_id(assess_all(candidate, RULE_DATE), "uk-skilled")
    assert result.status == "eligible"
    assert result.score == 46_000


def test_uk_skilled_worker_rejects_b1():
    candidate = profile(
        english=LanguageProfile(level="b1"),
        has_job_offer=True,
        job_offer_country="GB",
        job_offer_salary=60_000,
        job_offer_currency="GBP",
        job_offer_recognized_sponsor=True,
    )
    result = by_id(assess_all(candidate, RULE_DATE), "uk-skilled")
    assert any(gap.key == "english" for gap in result.gaps)


# ------------------------------------------------------------------ استرالیا
def test_australia_points_and_nominations():
    candidate = profile(
        birth_date=date(1995, 1, 1),
        education_level="bachelor",
        english=LanguageProfile(level="c2", test="ielts", listening=8.5, reading=8.5, writing=8, speaking=8),
        experience_last10=6,
        experience_last5=5,
        experience_last7=5,
        marital_status="single",
        skills_assessment=True,
    )
    independent = by_id(assess_all(candidate, RULE_DATE), "au-189")
    nominated = by_id(assess_all(candidate, RULE_DATE), "au-190")
    regional = by_id(assess_all(candidate, RULE_DATE), "au-491")
    assert nominated.score == independent.score + 5
    assert regional.score == independent.score + 15
    assert independent.score_threshold == 65


def test_australia_age_limit():
    candidate = profile(birth_date=date(1978, 1, 1), skills_assessment=True)
    result = by_id(assess_all(candidate, RULE_DATE), "au-189")
    assert result.status == "ineligible"
    assert any(gap.key == "age" for gap in result.gaps)


# ------------------------------------------------------------------ نیوزیلند
def test_new_zealand_income_points():
    candidate = profile(
        education_level="bachelor",
        nz_qualification_level=0,
        has_job_offer=True,
        job_offer_country="NZ",
        job_offer_salary=260_000,
        job_offer_currency="NZD",
        job_offer_recognized_sponsor=True,
        english=LanguageProfile(level="c1"),
    )
    result = by_id(assess_all(candidate, RULE_DATE), "nz-smc")
    assert result.score >= 6
    assert result.status in {"eligible", "potential"}


def test_new_zealand_requires_local_offer():
    candidate = profile(education_level="master", nz_qualification_level=9)
    result = by_id(assess_all(candidate, RULE_DATE), "nz-smc")
    assert result.status == "needs_job_offer"
    assert any(gap.key == "job_offer" for gap in result.gaps)


# ------------------------------------------------------------------ پرتغال
def test_portugal_d7_income_requirement():
    candidate = profile(passive_income_eur=1_000, savings_eur=12_000, monthly_income_eur=1_000)
    result = by_id(assess_all(candidate, RULE_DATE), "pt-d7")
    assert result.status == "eligible"
    assert result.score_threshold == pytest.approx(920, rel=1e-6)


def test_portugal_d8_remote_income():
    low = profile(passive_income_eur=3_000, savings_eur=15_000, remote_work=True, monthly_income_eur=3_000)
    assert by_id(assess_all(low, RULE_DATE), "pt-d8").status == "ineligible"

    high = profile(passive_income_eur=4_000, savings_eur=15_000, remote_work=True, monthly_income_eur=4_000)
    assert by_id(assess_all(high, RULE_DATE), "pt-d8").status == "eligible"


# ------------------------------------------------------------------ مشاور
def test_ranking_prefers_eligible_and_preferences():
    candidate = profile(
        has_job_offer=True,
        job_offer_country="DE",
        job_offer_salary=60_000,
        job_offer_currency="EUR",
        job_offer_recognized_sponsor=True,
        job_offer_contract_years=2,
        german=LanguageProfile(level="b1"),
        target_countries=["DE"],
        priorities=["speed", "pr"],
    )
    results = rank_results(assess_all(candidate, RULE_DATE), candidate)
    assert "de-bluecard" in [item.program_id for item in results[:3]]
    assert results[0].status in {"eligible", "potential"}
    assert results[0].preference_score >= results[-1].preference_score or results[0].readiness >= results[-1].readiness


def test_roadmap_and_checklist_are_actionable():
    candidate = profile()
    results = rank_results(assess_all(candidate, RULE_DATE), candidate)
    best = results[0]
    roadmap = build_roadmap(best, candidate, RULE_DATE)
    checklist = documents_checklist(candidate, results)
    assert len(roadmap) >= 3
    assert all(step.title for step in roadmap)
    assert checklist
    assert any("گذرنامه" in item["title"] for item in checklist)


def test_assessment_covers_every_program():
    results = assess_all(profile(), RULE_DATE)
    assert len(results) == 12
    assert len({result.program_id for result in results}) == 12
    for result in results:
        assert 0 <= result.readiness <= 100
        assert result.costs
        assert result.sources
        assert result.verified_on
