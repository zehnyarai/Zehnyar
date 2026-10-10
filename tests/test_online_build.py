import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from tools.check_online_server import validate_url, verify_server


@pytest.mark.parametrize("url", [
    "http://pestino.example", "https://localhost", "https://127.0.0.1",
    "https://abc.e2b.app", "https://u:p@pestino.example", "https://pestino.example/app",
    "https://pestino.example/?key=secret", "https://pestino.example/#x",
])
def test_online_build_rejects_incomplete_or_temporary_hosts(url):
    with pytest.raises(ValueError):
        validate_url(url)


def test_online_build_checks_actual_server_identity():
    responses = [{"status": "ok", "app": "pestino"}, {"info": {"title": "Pestino API"}}]
    with patch("tools.check_online_server.get_json", side_effect=responses) as get:
        assert verify_server("https://pestino.example/")["app"] == "pestino"
        assert get.call_args_list[0].args[0] == "https://pestino.example/api/health"


def test_wrong_application_is_never_packaged():
    with patch("tools.check_online_server.get_json", return_value={"status": "ok", "app": "other"}), patch("tools.check_online_server.time.sleep"):
        with pytest.raises(RuntimeError):
            verify_server("https://different.example")


def test_pipeline_is_gated_to_this_branch_and_a_real_url():
    workflow = yaml.load(Path('.github/workflows/pestino-apk.yml').read_text(), Loader=yaml.BaseLoader)
    assert workflow["on"]["push"]["branches"] == ["arena/e819b607-zehnyar"]
    condition = workflow["jobs"]["apk"]["if"]
    assert "arena/e819b607-zehnyar" in condition and "PESTINO_SERVER_URL" in condition
    assert workflow["permissions"]["contents"] == "read"
    deployment = yaml.safe_load(Path('render.yaml').read_text())["services"][0]
    assert deployment["branch"] == "arena/e819b607-zehnyar"
    assert deployment["plan"] == "free" and "disk" not in deployment
    assert deployment["healthCheckPath"] == "/api/health"
