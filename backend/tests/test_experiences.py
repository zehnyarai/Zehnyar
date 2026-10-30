import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.app.main import app  # noqa: E402
from backend.app.payments import make_password_hash  # noqa: E402

client = TestClient(app)
ADMIN_PASSWORD = "CommunityModPass2026!"
CLIENT_TOKEN = "2c75e0e4-4365-4bd0-8e3b-146d8b480d9b"
HEADERS = {"X-Experience-Client-Token": CLIENT_TOKEN}
STORY = (
    "I spent several months comparing official requirements and preparing my application. "
    "Keeping a clear checklist helped me track translations, appointments, and unexpected delays. "
    "Every case is different, so I recommend checking current requirements directly before applying."
)


def configure(monkeypatch, tmp_path):
    monkeypatch.setenv("PAYMENTS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("VISAYAR_ADMIN_USERNAME", "moderator")
    monkeypatch.setenv("VISAYAR_ADMIN_PASSWORD_HASH", make_password_hash(ADMIN_PASSWORD))


def submit(title="My migration experience"):
    return client.post("/api/experiences", headers=HEADERS, json={
        "title": title,
        "body": STORY,
        "destination": "CA",
        "visaRoute": "Skilled worker",
        "stage": "living",
        "displayName": "",
    })


def login_admin():
    return client.post("/api/admin/auth/login", json={"username": "moderator", "password": ADMIN_PASSWORD})


def test_experience_requires_review_and_then_is_public(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    response = submit()
    assert response.status_code == 201, response.text
    experience_id = response.json()["id"]
    assert response.json()["status"] == "pending"
    assert client.get("/api/experiences").json()["count"] == 0
    own_story = client.get("/api/experiences", headers=HEADERS).json()["items"][0]
    assert own_story["moderationStatus"] == "pending"
    assert own_story["canDelete"] is True
    assert client.get("/api/admin/experiences").status_code == 401

    assert login_admin().status_code == 200
    queue = client.get("/api/admin/experiences?status=pending").json()["items"]
    assert len(queue) == 1
    assert queue[0]["id"] == experience_id
    assert client.post(f"/api/admin/experiences/{experience_id}/review", json={"status": "approved"}).json() == {"status": "approved"}

    public = client.get("/api/experiences", headers=HEADERS).json()
    assert public["count"] == 1
    assert public["items"][0]["displayName"] is None
    assert public["items"][0]["canDelete"] is True
    assert client.get("/api/experiences", headers={"X-Experience-Client-Token": "another-client-token-value"}).json()["items"][0]["canDelete"] is False


def test_reports_show_in_admin_queue_and_moderator_can_hide(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    response = submit()
    experience_id = response.json()["id"]
    assert login_admin().status_code == 200
    client.post(f"/api/admin/experiences/{experience_id}/review", json={"status": "approved"})
    assert client.post(f"/api/experiences/{experience_id}/report", headers=HEADERS, json={"reason": "privacy"}).status_code == 201
    report_item = client.get("/api/admin/experiences?status=reported").json()["items"][0]
    assert report_item["report_count"] == 1
    assert report_item["report_reasons"] == ["privacy"]
    hidden = client.post(f"/api/admin/experiences/{experience_id}/review", json={"status": "hidden"})
    assert hidden.json() == {"status": "hidden"}
    assert client.get("/api/experiences").json()["count"] == 0


def test_submission_limit_survives_deleting_stories(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    for index in range(5):
        assert submit(f"Migration journey number {index}").status_code == 201
    sixth = submit("Another migration journey")
    assert sixth.status_code == 429


def test_contact_details_are_rejected_and_author_can_delete(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    bad = client.post("/api/experiences", headers=HEADERS, json={
        "title": "My migration experience", "body": STORY + " Contact me at person@example.com", "destination": "CA", "stage": "planning",
    })
    assert bad.status_code == 422
    response = submit()
    experience_id = response.json()["id"]
    assert client.delete(f"/api/experiences/{experience_id}", headers=HEADERS).json() == {"deleted": True}
    assert login_admin().status_code == 200
    assert client.get("/api/admin/experiences?status=all").json()["items"] == []
