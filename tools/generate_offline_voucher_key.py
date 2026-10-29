"""Generate a private signing key for offline assessment-credit vouchers."""
from __future__ import annotations

import argparse
import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-key", default="release/visayar-offline-voucher-private.txt")
    args = parser.parse_args()
    path = Path(args.private_key)
    if path.exists():
        raise SystemExit(f"Refusing to overwrite existing key: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)

    private = Ed25519PrivateKey.generate()
    raw_private = private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    raw_public = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    path.write_text(base64.urlsafe_b64encode(raw_private).decode("ascii") + "\n", encoding="ascii")
    os.chmod(path, 0o600)
    print(f"Private key saved to: {path}")
    print("Public key (safe to embed in the app):")
    print(base64.urlsafe_b64encode(raw_public).decode("ascii"))
    print("Back up the private key offline. Anyone with it can issue assessment credits.")


if __name__ == "__main__":
    main()
