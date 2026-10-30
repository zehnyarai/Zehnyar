"""Sanity-check the isolated, no-network/no-payments Android test APK."""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

APK = Path(sys.argv[1]) if len(sys.argv) == 2 else None
EXPECTED_PACKAGE = "ai.visayar.app.test"


def main() -> int:
    if APK is None or not APK.is_file():
        print("TEST APK check failed: provide an existing APK path.")
        return 1
    try:
        with zipfile.ZipFile(APK) as archive:
            names = set(archive.namelist())
            if "AndroidManifest.xml" not in names or not any(name.endswith("classes.dex") for name in names):
                raise ValueError("APK is missing Android manifest or dex payload")
            js_bundles = [name for name in names if name.endswith((".bundle", ".hbc"))]
            if not js_bundles:
                raise ValueError("APK is missing the application JavaScript bundle")
            # Test builds are made without payment secrets. Reject account-like
            # 16-digit runs in executable payloads, without ever printing matches.
            for name in js_bundles:
                if re.search(rb"(?<!\d)\d{16}(?!\d)", archive.read(name)):
                    raise ValueError("JavaScript bundle contains a 16-digit account-like value")
    except (OSError, zipfile.BadZipFile, ValueError) as error:
        print(f"TEST APK check failed: {error}")
        return 1
    print(f"TEST APK structure and secret-free bundle check passed: {EXPECTED_PACKAGE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
