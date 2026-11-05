#!/usr/bin/env python3
"""Build the offline Quran corpus from pinned, source-attributed inputs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
STATIC = ROOT / "static"
sys.path.insert(0, str(ROOT))

from translation_source import (  # noqa: E402
    TANZIL_TRANSLATION_COMMIT,
    TANZIL_TRANSLATION_ID,
    TANZIL_TRANSLATION_MIRROR,
    TANZIL_TRANSLATION_PATH,
    TANZIL_TRANSLATION_SHA256,
    TANZIL_TRANSLATION_SOURCE_URL,
    TANZIL_TRANSLATION_TERMS_URL,
    TANZIL_TRANSLATION_USE,
    TANZIL_TRANSLATOR,
    TANZIL_TRANSLATOR_FA,
    load_tanzil_translation,
)

OUTPUT = STATIC / "offline-corpus.json"

TRANSLATION_METADATA = {
    "id": TANZIL_TRANSLATION_ID,
    "name": "ترجمهٔ فارسی قرآن",
    "translator": TANZIL_TRANSLATOR,
    "translatorFa": TANZIL_TRANSLATOR_FA,
    "language": "fa",
    "source": "Tanzil Project",
    "sourceUrl": TANZIL_TRANSLATION_SOURCE_URL,
    "termsUrl": TANZIL_TRANSLATION_TERMS_URL,
    "sourceVersion": TANZIL_TRANSLATION_ID,
    "license": f"Tanzil translation terms: {TANZIL_TRANSLATION_USE.lower()}; see the official terms page.",
    "licenseFa": "شرایط رسمی Tanzil استفاده از این ترجمه را به مقاصد غیرتجاری محدود می‌کند؛ برای کاربردهای دیگر باید از مترجم یا ناشر اجازه گرفت.",
    "sourceFileSha256": TANZIL_TRANSLATION_SHA256,
    "snapshot": {
        "repository": TANZIL_TRANSLATION_MIRROR,
        "commit": TANZIL_TRANSLATION_COMMIT,
        "commitDate": "2026-08-15T10:47:05Z",
        "path": TANZIL_TRANSLATION_PATH,
        "blob": "222d65d4a476ff13ac9512f59ae7f69b790a46bf",
    },
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_payload() -> dict:
    arabic = read_json(DATA / "quran-uthmani.json")
    chapter_rows = read_json(DATA / "chapters.json")["chapters"]
    chapters = {int(item["id"]): item for item in chapter_rows}
    translations = load_tanzil_translation(DATA / "quran-fa-fooladvand.txt")

    expected_refs: set[tuple[int, int]] = set()
    verses = []
    for arabic_verses in arabic.values():
        for arabic_verse in arabic_verses:
            surah = int(arabic_verse["chapter"])
            ayah = int(arabic_verse["verse"])
            reference = (surah, ayah)
            expected_refs.add(reference)
            if reference not in translations:
                raise ValueError(f"No translation for {surah}:{ayah}")
            chapter = chapters[surah]
            revelation = "مدنی" if chapter["type"] == "medinan" else "مکی"
            verses.append([
                surah,
                ayah,
                arabic_verse["text"],
                translations[reference],
                chapter["name"],
                revelation,
            ])

    if expected_refs != set(translations):
        missing = sorted(expected_refs - set(translations))[:5]
        extra = sorted(set(translations) - expected_refs)[:5]
        raise ValueError(f"Source verse map mismatch; missing={missing}, extra={extra}")
    if len(verses) != 6236:
        raise ValueError(f"Expected 6236 verses, found {len(verses)}")

    return {
        "version": 2,
        "attribution": (
            "Arabic: Tanzil Uthmani. Persian base translation: Mohammad Mahdi Fooladvand, "
            "Tanzil fa.fooladvand; non-commercial terms apply. See data/ATTRIBUTION.md."
        ),
        "translation": TRANSLATION_METADATA,
        "verses": verses,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify generated JSON without writing")
    args = parser.parse_args()

    rendered = json.dumps(build_payload(), ensure_ascii=False, separators=(",", ":")) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
            print("ERROR: static/offline-corpus.json is not reproducible", file=sys.stderr)
            return 1
        print("OK: 6,236 Arabic/Persian verse records; Tanzil translation snapshot verified")
        return 0

    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(json.loads(rendered)['verses'])} verses)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
