#!/usr/bin/env python3
"""Verify an APK uses the configured release certificate, not Android's debug key."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


def run(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout + result.stderr


def normalized_fingerprint(value: str) -> str:
    return re.sub(r"[^0-9a-f]", "", value.lower())


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: verify_android_apk_signature.py <apksigner> <apk>", file=sys.stderr)
        return 2

    apksigner, apk = sys.argv[1], Path(sys.argv[2])
    keystore = os.environ.get("ANDROID_KEYSTORE_PATH")
    alias = os.environ.get("ANDROID_KEY_ALIAS")
    store_password = os.environ.get("ANDROID_KEYSTORE_PASSWORD")
    if not apk.is_file() or not keystore or not alias or not store_password:
        print("Release signature verification is missing its APK or keystore configuration.", file=sys.stderr)
        return 1

    try:
        apk_info = run([apksigner, "verify", "--print-certs", str(apk)])
        key_info = run([
            "keytool", "-list", "-v", "-keystore", keystore,
            "-alias", alias, "-storepass", store_password,
        ])
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Release signature verification failed: {error}", file=sys.stderr)
        return 1

    apk_match = re.search(r"Signer #1 certificate SHA-256 digest:\s*([0-9a-f:]+)", apk_info, re.I)
    key_match = re.search(r"SHA256:\s*([0-9a-f:]+)", key_info, re.I)
    if not apk_match or not key_match:
        print("Could not read the APK and release-keystore certificate fingerprints.", file=sys.stderr)
        return 1
    if normalized_fingerprint(apk_match.group(1)) != normalized_fingerprint(key_match.group(1)):
        print("APK certificate does not match the configured release keystore.", file=sys.stderr)
        return 1
    if re.search(r"Owner:.*Android Debug", key_info, re.I):
        print("The configured keystore contains Android's debug certificate, not a release identity.", file=sys.stderr)
        return 1

    print("APK signature matches the configured non-debug release certificate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
