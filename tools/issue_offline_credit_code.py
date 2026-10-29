"""Issue a signed, device-bound offline credit code after manual payment review."""
from __future__ import annotations

import argparse
import base64
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def encode_url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-id", required=True, help="Installation ID shown in the user's payment request")
    parser.add_argument("--credits", required=True, type=int, choices=(1, 3, 6, 12))
    parser.add_argument("--private-key", default="release/visayar-offline-voucher-private.txt")
    args = parser.parse_args()
    try:
        install_id = str(uuid.UUID(args.install_id))
    except ValueError as error:
        raise SystemExit("Invalid installation ID") from error

    path = Path(args.private_key)
    if not path.is_file():
        raise SystemExit(f"Private key not found: {path}; create one with tools/generate_offline_voucher_key.py")
    private_text = path.read_text(encoding="ascii").strip()
    raw_private = base64.urlsafe_b64decode(private_text + "=" * (-len(private_text) % 4))
    if len(raw_private) != 32:
        raise SystemExit("Invalid private key file")
    payload = {
        "v": 1,
        "id": str(uuid.uuid4()),
        "installId": install_id,
        "credits": args.credits,
        "issuedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    signature = Ed25519PrivateKey.from_private_bytes(raw_private).sign(payload_bytes)
    print(f"{encode_url(payload_bytes)}.{encode_url(signature)}")


if __name__ == "__main__":
    main()
