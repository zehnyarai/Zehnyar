# -*- coding: utf-8 -*-
"""Rewrite the verse label inside per-field sourceCoverageNote so each record names its own ayah.

Builders inherited a shared constant for that label, so records copied from an
earlier builder carried the wrong surah/ayah in the note while the fields
themselves described the right verse. The fix is mechanical and idempotent.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "static" / "verse-dossier-extended-fields.json"
DATA = json.loads(PATH.read_text(encoding="utf-8"))

SURAHS = {7: "الأعراف", 8: "الأنفال", 9: "التوبة", 10: "يونس", 11: "هود", 12: "يوسف"}
SEP = " در فیلدِ"
fa = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def label(verse_id: str) -> str:
    sura, ayah = verse_id.split(":")
    name = SURAHS.get(int(sura), sura)
    return f"{name} {ayah.translate(fa)}"


changed = 0
for verse_id, record in DATA["verses"].items():
    for field in record["extendedFields"].values():
        note = field.get("sourceCoverageNote")
        if not note:
            continue
        if SEP not in note:
            continue
        new = f"برای {label(verse_id)}{SEP}" + note.split(SEP, 1)[1]
        if new != note:
            field["sourceCoverageNote"] = new
            changed += 1

PATH.write_text(json.dumps(DATA, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("notes updated:", changed)
