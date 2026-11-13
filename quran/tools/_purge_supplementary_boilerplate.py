#!/usr/bin/env python3
"""حذفِ قالب‌های تکراریِ فیلدهای تکمیلی (extendedFields) از هر دو شارد.

قاعده: در هر فیلد، اسکلتِ متن (اعداد، ارجاعِ آیه و نامِ سوره نرمال‌شده) اگر در
۸ آیه یا بیشتر تکرار شده باشد قالبِ سراسری است و مدخل حذف می‌شود. فقط محتوای
یکتای برگرفته از همان آیه می‌ماند؛ فیلدِ خالی و extendedFieldsِ خالی حذف می‌شوند.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "static"
FILES = ["verse-dossier-extended-fields.json", "verse-dossier-extended-fields-2.json"]
THRESHOLD = 8

FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def skeleton(text: str) -> str:
    t = str(text or "").translate(FA_DIGITS)
    t = re.sub(r"«[^»]{0,80}»", "«X»", t)
    t = re.sub(r"\d+[:.]\d+(?:-\d+)?", "R", t)
    t = re.sub(r"\d+", "N", t)
    return t


def main() -> int:
    payloads = {}
    verses = {}
    for name in FILES:
        data = json.loads((STATIC / name).read_text(encoding="utf-8"))
        payloads[name] = data
        for vid, rec in (data.get("verses") or {}).items():
            verses[vid] = (name, rec)

    # شمارش اسکلت در هر فیلد
    skeleton_counts = {}
    for vid, (_name, rec) in verses.items():
        for field, fdata in (rec.get("extendedFields") or {}).items():
            counter = skeleton_counts.setdefault(field, Counter())
            for entry in fdata.get("entries") or []:
                counter[skeleton(entry.get("text", ""))] += 1

    removed_entries = 0
    removed_fields = 0
    total_before = 0
    for vid, (_name, rec) in verses.items():
        extended = rec.get("extendedFields") or {}
        for field in list(extended.keys()):
            fdata = extended[field] or {}
            entries = fdata.get("entries") or []
            total_before += len(entries)
            kept = [
                e
                for e in entries
                if skeleton_counts[field][skeleton(e.get("text", ""))] < THRESHOLD
            ]
            removed_entries += len(entries) - len(kept)
            if kept:
                fdata["entries"] = kept
                if isinstance(fdata.get("coverage"), dict):
                    fdata["coverage"]["completed"] = len(kept)
                fdata["status"] = "partial"
            else:
                del extended[field]
                removed_fields += 1
        if extended:
            rec["extendedFields"] = extended
        else:
            rec.pop("extendedFields", None)

    for name in FILES:
        data = payloads[name]
        (STATIC / name).write_text(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        print(name, "size MB:", round((STATIC / name).stat().st_size / 1e6, 2))
    print(f"entries before={total_before} removed={removed_entries} fields removed={removed_fields}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
