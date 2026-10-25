"""Engine and API contract tests."""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.app.main import app  # noqa: E402
from backend.app.engine.engine import (  # noqa: E402
    Adaptability, Funds, LanguageResult, Profile, Work, assess, load_dataset,
    normalise_language, roadmap, score_visa, settlement_usd,
)

client = TestClient(app)
DATASET = load_dataset()


def base_profile(**overrides):
    data = dict(
        age=31,
        educationId="master",
        languages=[LanguageResult(testId="ielts", skills={"listening": 8.0, "reading": 7.5, "writing": 7.0, "speaking": 7.5})],
        work=Work(totalYears=6, overseasYears=6, occupationCode="21231"),
        funds=Funds(availableUsd=40000),
        adaptability=Adaptability(eca=True),
        familySize=2,
        goal="work",
    )
    data.update(overrides)
    return Profile(**data)


def test_dataset_shape():
    assert len(DATASET["countries"]) == 15
    assert sum(len(c["visas"]) for c in DATASET["countries"]) >= 50
    assert len(DATASET["occupations"]) >= 40
    ids = [v["id"] for c in DATASET["countries"] for v in c["visas"]]
    assert len(ids) == len(set(ids))


def test_every_country_has_official_portal_and_date():
    for country in DATASET["countries"]:
        assert country["official"]["portal"].startswith("http")
        assert country["official"]["lastVerified"] == "2026-10-25"


def test_persian_fields_have_no_latin_letters():
    import re

    latin = re.compile(r"[A-Za-z]")

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                yield from walk(value) if not isinstance(value, str) else []
                if key.endswith("Fa") and isinstance(value, str):
                    yield value
        elif isinstance(node, list):
            for item in node:
                yield from walk(item)

    for text in walk(DATASET["countries"]):
        assert not latin.search(text), text


def test_language_normalisation_matches_official_clb_table():
    ielts = LanguageResult(testId="ielts", skills={"listening": 8.0, "reading": 7.0, "writing": 7.0, "speaking": 7.0})
    normalised = normalise_language(DATASET, ielts)
    assert normalised["skills"]["listening"] == 9
    assert normalised["skills"]["reading"] == 9
    assert normalised["minClb"] == 9
    assert normalised["cefr"] == "C1"


def test_stronger_language_never_lowers_score():
    weaker = base_profile(languages=[LanguageResult(testId="ielts", skills={"listening": 6.0, "reading": 6.0, "writing": 6.0, "speaking": 6.0})])
    stronger = base_profile(languages=[LanguageResult(testId="ielts", skills={"listening": 9.0, "reading": 9.0, "writing": 9.0, "speaking": 9.0})])
    weak_result = assess(DATASET, weaker)
    strong_result = assess(DATASET, stronger)
    weak_ca = next(c for c in weak_result["countries"] if c["code"] == "CA")
    strong_ca = next(c for c in strong_result["countries"] if c["code"] == "CA")
    assert strong_ca["best"]["chance"] >= weak_ca["best"]["chance"]


def test_study_route_requires_admission():
    profile = base_profile(goal="study", studyOffer=False)
    result = assess(DATASET, profile)
    ca = next(c for c in result["countries"] if c["code"] == "CA")
    study = next(v for v in ca["visas"] if v["visaId"] == "ca_study")
    assert not study["eligible"]
    assert any(b["kind"] == "flag_gate" for b in study["blockers"])
    assert study["chance"] < 40


def test_study_route_unlocks_with_admission():
    profile = base_profile(goal="study", studyOffer=True)
    result = assess(DATASET, profile)
    ca = next(c for c in result["countries"] if c["code"] == "CA")
    study = next(v for v in ca["visas"] if v["visaId"] == "ca_study")
    assert study["eligible"]


def test_blue_card_gate_follows_salary():
    de = next(c for c in DATASET["countries"] if c["code"] == "DE")
    visa = next(v for v in de["visas"] if v["id"] == "de_blue_card")
    low = base_profile(work=Work(totalYears=6, overseasYears=6, occupationCode="21231",
                                 salaryAnnualLocal=40000, salaryCurrency="EUR"))
    high = base_profile(work=Work(totalYears=6, overseasYears=6, occupationCode="21231",
                                  salaryAnnualLocal=62000, salaryCurrency="EUR"))
    assert not score_visa(DATASET, de, visa, low)["eligible"]
    assert score_visa(DATASET, de, visa, high)["eligible"]


def test_shortage_occupation_uses_reduced_blue_card_threshold():
    de = next(c for c in DATASET["countries"] if c["code"] == "DE")
    visa = next(v for v in de["visas"] if v["id"] == "de_blue_card")
    profile = base_profile(work=Work(totalYears=6, overseasYears=6, occupationCode="21231",
                                     salaryAnnualLocal=47000, salaryCurrency="EUR"))
    assert score_visa(DATASET, de, visa, profile)["eligible"]


def test_settlement_scales_with_family_size():
    ca = next(c for c in DATASET["countries"] if c["code"] == "CA")
    visa = next(v for v in ca["visas"] if v["id"] == "ca_ee_fsw")
    assert settlement_usd(DATASET, visa, 1) == pytest.approx(15263 * 0.73, rel=0.01)
    assert settlement_usd(DATASET, visa, 4) == pytest.approx(28362 * 0.73, rel=0.01)


def test_funds_gate_blocks_underfunded_profile():
    profile = base_profile(funds=Funds(availableUsd=1000), familySize=4)
    result = assess(DATASET, profile)
    ca = next(c for c in result["countries"] if c["code"] == "CA")
    fsw = next(v for v in ca["visas"] if v["visaId"] == "ca_ee_fsw")
    assert any(b["kind"] == "funds_gate" for b in fsw["blockers"])


def test_roadmap_is_prioritised_and_bounded():
    result = assess(DATASET, base_profile())
    top = result["countries"][0]
    items = roadmap(top["best"])
    assert 0 < len(items) <= 6
    assert all("actionFa" in item for item in items)


def test_chance_is_bounded():
    for profile in (base_profile(), base_profile(age=55, educationId="highschool", work=Work(totalYears=0))):
        result = assess(DATASET, profile)
        for country in result["countries"]:
            for visa in country["visas"]:
                assert 0 <= visa["chance"] <= 100
                assert visa["readiness"] <= 100


def test_api_health_and_meta():
    assert client.get("/health").json()["status"] == "ok"
    meta = client.get("/api/meta").json()
    assert meta["counts"]["countries"] == 15
    assert meta["counts"]["visas"] >= 50


def test_api_assess_endpoint():
    payload = {"profile": base_profile().model_dump()}
    response = client.post("/api/assess", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["countries"] == 15
    assert body["countries"][0]["best"]["chance"] > 0


def test_api_costs_endpoint_returns_verified_fees():
    body = client.get("/api/visas/ca_ee_fsw/costs?family_size=1").json()
    assert body["settlementUsd"] > 10000
    labels = " ".join(line["labelEn"] for line in body["lines"])
    assert "processing fee" in labels.lower()


def test_api_unknown_country_returns_404():
    assert client.get("/api/countries/ZZ").status_code == 404


def test_root_keeps_json_for_api_clients_and_redirects_browsers():
    payload = client.get("/").json()
    assert payload["name"] == "Zehnyar API"
    assert payload["datasetVersion"] == DATASET["meta"]["version"]
    browser = client.get("/", headers={"accept": "text/html"}, follow_redirects=False)
    # 307 to /app/ when the web preview is built, unchanged JSON otherwise.
    assert browser.status_code in (200, 307)


def test_health_reports_dataset_shape():
    health = client.get("/health").json()
    assert health["status"] == "ok"
    assert health["countries"] == 15
    assert health["visas"] == 58
