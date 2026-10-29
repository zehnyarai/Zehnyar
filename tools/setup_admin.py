"""Provision the Visayar admin account and encryption key for server secrets."""
from __future__ import annotations

import getpass
import re
import sys
from pathlib import Path

from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.payments import make_password_hash  # noqa: E402


def main() -> None:
    username = input("Admin username (no spaces): ").strip()
    if not username or any(char.isspace() for char in username):
        raise SystemExit("Username must be non-empty and contain no spaces.")
    password = getpass.getpass("Admin password (minimum 14 characters): ")
    confirmation = getpass.getpass("Repeat admin password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    if len(password) < 14:
        raise SystemExit("Password must contain at least 14 characters.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        print("Use a strong password with a mix of character types.", file=sys.stderr)
    print("\nAdd these values to the backend's secret environment variables:")
    print(f"VISAYAR_ADMIN_USERNAME={username}")
    print(f"VISAYAR_ADMIN_PASSWORD_HASH={make_password_hash(password)}")
    print(f"VISAYAR_ENCRYPTION_KEY={Fernet.generate_key().decode('ascii')}")
    print("\nKeep VISAYAR_ENCRYPTION_KEY backed up separately; losing it makes stored secrets unreadable.")


if __name__ == "__main__":
    main()
