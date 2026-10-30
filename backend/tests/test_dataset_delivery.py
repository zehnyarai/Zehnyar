from datetime import date

from fastapi.testclient import TestClient

from backend.app.main import app
from tools.check_dataset_freshness import get_report
from tools.monthly_data_review import build_report
from backend.app.engine.engine import load_dataset

client = TestClient(app)


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
