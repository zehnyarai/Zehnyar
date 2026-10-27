import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.app.main import app  # noqa: E402
import backend.app.main as main_module  # noqa: E402

client = TestClient(app)


def test_advisor_uses_server_gemini_key_without_returning_it(monkeypatch, tmp_path):
    api_key = "AIza" + "V" * 35
    monkeypatch.setenv("PAYMENTS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("GEMINI_API_KEY", api_key)
    calls = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        @staticmethod
        def json():
            return {"candidates": [{"content": {"parts": [{"text": '{"narrativeFa":"راهنمای فارسی","narrativeEn":"English guidance"}'}]}}]}

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse()

    monkeypatch.setattr(main_module.httpx, "post", fake_post)
    result = client.post("/api/advisor", json={"profile": {}})
    assert result.status_code == 200
    assert result.json()["narrativeFa"] == "راهنمای فارسی"
    assert result.json()["narrativeEn"] == "English guidance"
    assert api_key not in result.text
    assert calls[0][1]["headers"]["x-goog-api-key"] == api_key
    assert "gemini-2.5-flash" in calls[0][0]
