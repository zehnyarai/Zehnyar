from datetime import date

from fastapi.testclient import TestClient

from backend.app.main import app
from tools.check_dataset_freshness import get_report
from tools.monthly_data_review import build_report
from backend.app.engine.engine import load_dataset

client = TestClient(app)


def test_added_destinations_and_routes_have_official_source_records():
    dataset = load_dataset()
    destinations = {country["code"]: country for country in dataset["countries"]}
    expanded = {"IE", "PT", "FI", "BE", "CN", "QA", "JP", "KR", "MY", "SG"}
    assert expanded <= destinations.keys()
    assert len(destinations) == 25
    assert sum(len(country["visas"]) for country in destinations.values()) == 100
    assert {code: len(destinations[code]["visas"]) for code in expanded} == {
        "IE": 4, "PT": 5, "FI": 4, "BE": 4,
        "CN": 4, "QA": 4, "JP": 4, "KR": 4, "MY": 4, "SG": 5,
    }
    for code in expanded:
        country = destinations[code]
        assert country["official"]["lastVerified"] == "2026-11-01"
        assert all(visa["officialUrl"].startswith("https://") for visa in country["visas"])
    required_new_routes = {
        "cn_work_residence", "cn_r_talent", "cn_x1_student", "cn_q1_reunion",
        "qa_work_residence", "qa_education_residence", "qa_executive_residency", "qa_entrepreneur_residency",
        "jp_hsp", "jp_engineer_specialist", "jp_specified_skilled", "jp_student",
        "kr_e7_special_activity", "kr_d2_student", "kr_d10_jobseeker", "kr_d8_investor",
        "my_employment_pass", "my_de_rantau", "my_student_pass", "my_mm2h",
        "sg_employment_pass", "sg_s_pass", "sg_entrepass", "sg_student_pass", "sg_one_pass",
    }
    all_new_routes = {visa["id"] for code in ("CN", "QA", "JP", "KR", "MY", "SG") for visa in destinations[code]["visas"]}
    assert all_new_routes == required_new_routes
    for code in ("CNY", "QAR", "JPY", "KRW", "MYR", "SGD"):
        fx = dataset["fx"][code]
        assert fx["rate"] > 0 and fx["usdToLocal"] > 0
        assert fx["asOf"] in {"2026-10-30", "2026-11-01"}
        assert fx["source"].startswith("https://")
    portugal = destinations["PT"]
    assert "pt_jobseeker" not in {visa["id"] for visa in portugal["visas"]}
    remote_work = next(visa for visa in portugal["visas"] if visa["id"] == "pt_digital_nomad")
    assert any(gate["kind"] == "remote_income_gate" for gate in remote_work["gates"])
    specialist = next(visa for visa in destinations["FI"]["visas"] if visa["id"] == "fi_specialist")
    salary_gate = next(gate for gate in specialist["gates"] if gate["kind"] == "salary_gate")
    assert salary_gate["minAmount"] == 3937


def test_dataset_endpoint_supports_etag_revalidation():
    first = client.get("/api/dataset")
    assert first.status_code == 200
    assert first.headers["cache-control"] == "no-cache"
    etag = first.headers["etag"]
    assert len(etag.strip('"')) == 64
    assert first.json()["meta"]["schemaVersion"] == 1

    unchanged = client.get("/api/dataset", headers={"If-None-Match": etag})
    assert unchanged.status_code == 304
    assert unchanged.headers["etag"] == etag
    assert unchanged.content == b""


def test_dataset_meta_exposes_revision_and_review_policy():
    response = client.get("/api/meta")
    assert response.status_code == 200
    body = response.json()
    assert len(body["dataRevision"]) == 64
    assert body["freshness"]["lastVerified"] == load_dataset()["meta"]["lastVerified"]
    assert body["freshness"]["reviewIntervalDays"] == 30
    assert body["freshness"]["staleAfterDays"] == 45
    assert body["freshness"]["status"] in {"current", "review_due", "stale"}


def test_freshness_report_detects_review_due_stale_and_future_data():
    dataset = load_dataset()
    due = get_report(dataset, date(2026, 11, 24), 45)
    assert due["status"] == "review_due"
    report = get_report(dataset, date(2026, 12, 15), 45)
    assert report["stale"] is True
    assert len(report["records"]) == len(dataset["countries"]) + 1

    future = {**dataset, "meta": {**dataset["meta"], "lastVerified": "2027-01-01"}}
    try:
        get_report(future, date(2026, 12, 15), 45)
    except ValueError as error:
        assert "in the future" in str(error)
    else:
        raise AssertionError("future verification dates must be rejected")


def test_monthly_review_report_lists_all_sources_and_requires_human_approval():
    dataset = load_dataset()
    body = build_report(dataset, "2026-11")
    assert "human verification" in body
    assert "do not change thresholds" in body.lower()
    assert body.count("- [ ]") >= sum(len(country["visas"]) for country in dataset["countries"])
    for country in dataset["countries"]:
        for visa in country["visas"]:
            assert visa["officialUrl"] in body
