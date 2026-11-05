#!/usr/bin/env python3
"""Build the browser corpus from the pinned Arabic and Persian verse files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
STATIC = ROOT / "static"
OUTPUT = STATIC / "offline-corpus.json"
ATTRIBUTION = (
    "Tanzil Uthmani + fa.fooladvand (Mohammad Mahdi Fooladvand; Tanzil.net; "
    "non-commercial use); the upstream display basmala prefix is removed from verse 1 "
    "of surahs 2–8 and 10–114; see data/ATTRIBUTION.md"
)
BASMALA_DISPLAY_PREFIX = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
ARABIC_MARKS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u08d4-\u08ff]")
ARABIC_WORDS = re.compile(r"[\u0600-\u06ff]+")
LETTER_MAP = str.maketrans({"ٱ": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ئ": "ي", "ؤ": "و", "ة": "ه", "ك": "ك", "ـ": ""})
EXPECTED_BASMALA_WORDS = tuple(ARABIC_MARKS.sub("", word).translate(LETTER_MAP) for word in BASMALA_DISPLAY_PREFIX.split())


def strip_display_basmala(text: str, surah: int, ayah: int) -> str:
    """Remove only the source package's decorative prefix, never Quranic basmala verses."""
    if surah in (1, 9) or ayah != 1:
        return text
    words = list(ARABIC_WORDS.finditer(text))
    actual = tuple(ARABIC_MARKS.sub("", match.group()).translate(LETTER_MAP) for match in words[:4])
    if actual != EXPECTED_BASMALA_WORDS:
        raise ValueError(f"Expected the upstream basmala display prefix at {surah}:{ayah}.")
    return text[words[3].end():].lstrip()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build() -> dict:
    arabic = read_json(DATA / "quran-uthmani.json")
    persian = read_json(DATA / "quran-fa-fooladvand.json")
    chapters = read_json(DATA / "chapters.json")["chapters"]
    chapter_by_id = {int(item["id"]): item for item in chapters}
    expected_ids = {str(number) for number in range(1, 115)}
    if set(arabic) != expected_ids or set(persian) != expected_ids:
        raise ValueError("The Arabic and Persian files must each contain all 114 surahs.")

    rows = []
    for sid in range(1, 115):
        arabic_verses = arabic[str(sid)]
        persian_verses = persian[str(sid)]
        chapter = chapter_by_id[sid]
        expected = int(chapter["total_verses"])
        if len(arabic_verses) != expected or len(persian_verses) != expected:
            raise ValueError(f"Surah {sid}: verse count does not match chapter metadata.")
        for ayah, (arabic_verse, persian_verse) in enumerate(zip(arabic_verses, persian_verses), 1):
            reference = (sid, ayah)
            if (int(arabic_verse["chapter"]), int(arabic_verse["verse"])) != reference:
                raise ValueError(f"Arabic numbering mismatch at {sid}:{ayah}.")
            if (int(persian_verse["chapter"]), int(persian_verse["verse"])) != reference:
                raise ValueError(f"Persian numbering mismatch at {sid}:{ayah}.")
            arabic_text = strip_display_basmala(str(arabic_verse["text"]), sid, ayah)
            persian_text = str(persian_verse["text"])
            if not arabic_text.strip() or not persian_text.strip():
                raise ValueError(f"Empty verse text at {sid}:{ayah}.")
            rows.append([
                sid,
                ayah,
                arabic_text,
                persian_text,
                chapter["name"],
                "مکی" if chapter["type"] == "meccan" else "مدنی",
            ])

    if len(rows) != 6236 or (rows[0][0], rows[0][1]) != (1, 1) or (rows[-1][0], rows[-1][1]) != (114, 6):
        raise ValueError(f"Expected 6,236 consecutive verses from 1:1 to 114:6; got {len(rows)}.")
    return {"version": 2, "attribution": ATTRIBUTION, "verses": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the generated corpus is stale")
    args = parser.parse_args()
    payload = json.dumps(build(), ensure_ascii=False, separators=(",", ":")) + "\n"
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != payload:
            raise SystemExit("offline-corpus.json is stale; run python3 tools/build_offline_corpus.py")
        print("offline-corpus.json is current (6,236 verses).")
    else:
        OUTPUT.write_text(payload, encoding="utf-8")
        print(f"Built {OUTPUT} with 6,236 verses and the Fooladvand/Tanzil attribution.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
