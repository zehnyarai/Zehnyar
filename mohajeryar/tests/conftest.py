"""فیکسچرهای آزمون: پایگاه‌دادهٔ موقت و کلاینت HTTP."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("DATABASE_PATH", str(Path(__file__).resolve().parent / "test.db"))
os.environ.setdefault("AI_ENABLED", "0")
os.environ.setdefault("APP_ENV", "test")


@pytest.fixture(scope="session", autouse=True)
def _clean_database():
    db_path = Path(os.environ["DATABASE_PATH"])
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(str(db_path) + suffix)
        if candidate.exists():
            candidate.unlink()
    yield
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(str(db_path) + suffix)
        if candidate.exists():
            candidate.unlink()


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def assessment_id(client) -> str:
    response = client.post(
        "/assess",
        data={
            "name": "کاربر آزمون",
            "nationality": "IR",
            "birth_date": "1994-04-12",
            "marital_status": "married",
            "spouse_included": "on",
            "dependents": "1",
            "education_level": "master",
            "education_field": "stem",
            "education_country": "IR",
            "graduation_year": "2018",
            "eca": "on",
            "recognition": "full",
            "english_level": "c1",
            "english_test": "ielts",
            "english_listening": "8",
            "english_reading": "7.5",
            "english_writing": "7",
            "english_speaking": "7",
            "german_level": "b1",
            "french_level": "b1",
            "occupation_title": "مهندس نرم‌افزار",
            "total_experience_years": "7",
            "experience_last5": "5",
            "experience_last7": "6",
            "experience_last10": "7",
            "occupation_shortage": "on",
            "savings_eur": "18000",
            "target_countries": ["CA", "DE", "AU"],
            "priorities": ["speed", "pr"],
            "passport_valid_years": "6",
            "birth_certificate": "on",
            "education_transcripts": "on",
            "language_certificate": "on",
            "employment_letters": "on",
            "police_clearance": "on",
            "medical": "on",
            "proof_of_funds": "on",
            "doc_eca": "on",
            "marriage_certificate": "on",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303, response.text[:800]
    return response.headers["location"].rsplit("/", 1)[-1]
