"""Check the actual published Pestino API before packaging an online test APK.

Run on the GitHub build runner, not against an invented or temporary server.
No private keys, login or user data are needed for these health checks.
"""
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def validate_url(value):
    parsed = urlparse(value)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.path not in {"", "/"}
            or parsed.query or parsed.fragment
            or parsed.hostname in {"localhost", "127.0.0.1", "::1"}
            or parsed.hostname.endswith(".e2b.app")):
        raise ValueError("A permanent public HTTPS Pestino site root is required")
    return value.rstrip("/")


def get_json(url):
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "Pestino-APK-build/0.1.0"})
    with urlopen(request, timeout=25) as response:
        return json.load(response)


def verify_server(url):
    root = validate_url(url)
    # A free pilot host can take time to wake. A bounded retry is for the remote
    # build job only, not a long-lived process or local dev-server polling.
    last_error = None
    for attempt in range(6):
        try:
            health = get_json(root + "/api/health")
            schema = get_json(root + "/api/openapi.json")
            if health.get("status") != "ok" or health.get("app") != "pestino":
                raise ValueError("This address is not the expected Pestino API")
            if schema.get("info", {}).get("title") != "Pestino API":
                raise ValueError("The published server is a different application")
            return health
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            last_error = error
            if attempt < 5:
                time.sleep(5)
    raise RuntimeError("Published Pestino API could not be verified; no APK will be packaged") from last_error


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python tools/check_online_server.py https://YOUR_PUBLIC_HOST")
    verify_server(sys.argv[1])
    print("Published Pestino API verified; this does not verify diagnosis or payment services.")
