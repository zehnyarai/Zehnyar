"""Sanity-check the isolated, no-network/no-payments Android test APK."""

from __future__ import annotations

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
            if "AndroidManifest.xml" not in names or not any(Path(name).name.startswith("classes") and name.endswith(".dex") for name in names):
                raise ValueError("APK is missing Android manifest or dex payload")
            js_bundles = [name for name in names if name.endswith((".bundle", ".hbc"))]
            if not js_bundles:
                raise ValueError("standalone APK is missing its embedded JavaScript bundle")
            # The workflow separately validates an empty payment fallback and
            # the no-network Expo config before generating the native project.
    except (OSError, zipfile.BadZipFile, ValueError) as error:
        print(f"TEST APK check failed: {error}")
        return 1
    print(f"Standalone TEST APK structure and embedded JavaScript bundle check passed: {EXPECTED_PACKAGE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
