"""Load the pinned, verbatim Tanzil Persian translation snapshot."""
from __future__ import annotations

import hashlib
from pathlib import Path

TANZIL_TRANSLATION_SHA256 = "4d8cead0c9c7397e59adc4e773dd56b2da4c5700cda82d9ed648660fb190aa45"
TANZIL_TRANSLATION_ID = "fa.fooladvand"
TANZIL_TRANSLATION_MIRROR = "app-furqan/quran_translations"
TANZIL_TRANSLATION_COMMIT = "b46893686eabf1abf2157114e10fe5599bd42a2e"
TANZIL_TRANSLATION_PATH = "translations/fa.fooladvand.txt"
TANZIL_TRANSLATION_SOURCE_URL = "https://tanzil.net/trans/fa.fooladvand"
TANZIL_TRANSLATION_TERMS_URL = "https://tanzil.net/trans/"
TANZIL_TRANSLATOR = "Mohammad Mahdi Fooladvand"
TANZIL_TRANSLATOR_FA = "محمدمهدی فولادوند"
TANZIL_TRANSLATION_USE = "Non-commercial use only"


def load_tanzil_translation(path: Path) -> dict[tuple[int, int], str]:
    """Return exact (surah, ayah) text after verifying the pinned source bytes.

    The upstream format is ``surah|ayah|translation``. Only the two structural
    separators are parsed; the Persian text after them is retained verbatim.
    """
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != TANZIL_TRANSLATION_SHA256:
        raise ValueError(
            f"Unexpected Tanzil translation snapshot SHA-256: {digest}; "
            f"expected {TANZIL_TRANSLATION_SHA256}"
        )

    records: dict[tuple[int, int], str] = {}
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), start=1):
        if not line or line.startswith("#"):
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            raise ValueError(f"Malformed Tanzil translation row {line_number}")
        try:
            surah, ayah = int(parts[0]), int(parts[1])
        except ValueError as error:
            raise ValueError(f"Invalid reference on Tanzil row {line_number}") from error
        translation = parts[2]
        if not (1 <= surah <= 114) or ayah < 1 or not translation:
            raise ValueError(f"Invalid or empty Tanzil translation row {line_number}")
        reference = (surah, ayah)
        if reference in records:
            raise ValueError(f"Duplicate Tanzil translation reference {surah}:{ayah}")
        records[reference] = translation

    if len(records) != 6236:
        raise ValueError(f"Expected 6236 Tanzil translations, found {len(records)}")
    return records
