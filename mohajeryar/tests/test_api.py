"""آزمون‌های مسیرهای وب و API."""
from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "path",
    ["/", "/wizard", "/profiles", "/methodology", "/offline", "/robots.txt", "/favicon.ico"],
)
def test_pages_render(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.content


def test_manifest_and_service_worker(client):
    manifest = client.get("/manifest.webmanifest")
    assert manifest.status_code == 200
    data = manifest.json()
    assert data["dir"] == "rtl"
    assert data["lang"] == "fa"
    assert any(icon["sizes"] == "512x512" for icon in data["icons"])

    worker = client.get("/sw.js")
    assert worker.status_code == 200
    assert "caches" in worker.text
    assert worker.headers.get("service-worker-allowed") == "/"


def test_health(client):
    payload = client.get("/api/health").json()
    assert payload["status"] == "ok"
    assert payload["rules_verified_on"]


def test_programs_api_has_all_programs(client):
    payload = client.get("/api/programs").json()
    verified_on = payload["verified_on"]
    ids = {item["id"] for item in payload["items"]}
    assert ids == {
        "ca-ee",
        "de-bluecard",
        "de-chancenkarte",
        "nl-hsm",
        "nl-bluecard",
        "uk-skilled",
        "au-189",
        "au-190",
        "au-491",
        "nz-smc",
        "pt-d7",
        "pt-d8",
    }
    for item in payload["items"]:
        assert item["sources"], item["id"]
        assert verified_on


def test_assessment_flow(client, assessment_id):
    page = client.get(f"/results/{assessment_id}")
    assert page.status_code == 200
    html = page.text
    assert "top-card" in html or "برترین مسیر" in html
    assert "نقشه" in html

    api = client.get(f"/api/assessments/{assessment_id}")
    assert api.status_code == 200
    payload = api.json()
    assert len(payload["results"]) == 12
    assert 0 <= payload["readiness"] <= 100


@pytest.mark.parametrize(
    "program_id",
    [
        "ca-ee",
        "de-bluecard",
        "de-chancenkarte",
        "nl-hsm",
        "nl-bluecard",
        "uk-skilled",
        "au-189",
        "au-190",
        "au-491",
        "nz-smc",
        "pt-d7",
        "pt-d8",
    ],
)
def test_compare_single_program(client, assessment_id, program_id):
    response = client.get(f"/compare/{assessment_id}?p={program_id}")
    assert response.status_code == 200
    assert "compare-table" in response.text


def test_compare_all_programs(client, assessment_id):
    response = client.get(f"/compare/{assessment_id}")
    assert response.status_code == 200
    assert len(response.text) > 5000


def test_validation_errors_return_422(client):
    response = client.post("/assess", data={"name": "", "birth_date": "2030-01-01"})
    assert response.status_code == 422
    assert "alert" in response.text
    assert 'data-error-fields="birth_date"' in response.text


def test_invalid_language_level_is_reported_not_crashed(client):
    response = client.post(
        "/assess",
        data={"name": "زبان نامعتبر", "birth_date": "1994-01-01", "english_level": "z9"},
    )
    assert response.status_code == 422
    assert "wizard-form" in response.text
    assert "english_level" in response.text


def test_profiles_lifecycle(client, assessment_id):
    items = client.get("/api/profiles").json()["items"]
    assert items
    profile_id = items[0]["id"]

    assert client.get(f"/profiles/{profile_id}/edit").status_code == 200

    reassessed = client.post(f"/profiles/{profile_id}/reassess", follow_redirects=False)
    assert reassessed.status_code == 303
    assert "/results/" in reassessed.headers["location"]

    latest = client.get(f"/profiles/{profile_id}/latest", follow_redirects=False)
    assert latest.status_code == 303
    assert "/results/" in latest.headers["location"]

    assert client.post(f"/profiles/{profile_id}/delete", follow_redirects=False).status_code == 303


def test_unknown_pages(client):
    assert client.get("/not-a-page").status_code == 404
    assert client.get("/results/does-not-exist").status_code == 404


def test_chat_requires_question(client):
    assert client.post("/api/chat", json={"question": ""}).status_code == 422
    response = client.post("/api/chat", json={"question": "برای آلمان چه مدرکی لازم است؟"})
    assert response.status_code == 200
    assert response.json()["answer"]


def test_api_assess_json(client):
    response = client.post(
        "/api/assess",
        json={
            "name": "API",
            "birth_date": "1992-01-01",
            "education_level": "bachelor",
            "english_level": "b2",
            "experience_last10": 4,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["results"]) == 12
    assert payload["results"][0]["program_id"]


def test_security_headers(client):
    response = client.get("/")
    csp = response.headers["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "frame-ancestors" in csp
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"]
