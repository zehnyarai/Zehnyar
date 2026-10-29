#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""گزارشِ پیشرفتِ «پروندهٔ آیه» و اعتبارسنجیِ سریعِ بندها.

کاربرد:
    python3 tools/dossier_status.py            # خلاصهٔ پیشرفت و بستهٔ بعدی
    python3 tools/dossier_status.py --next 3   # سه بازهٔ بعدی برای نوشتن

این ابزار چیزی تولید نمی‌کند و هیچ بندی نمی‌سازد؛ فقط پوشش و سلامتِ داده را
گزارش می‌دهد تا کارِ تحریری آیه‌به‌آیه قابلِ پیگیری باشد.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
FIELDS = ("notes", "context", "classical", "modern", "critical", "research")
MIN_WORDS = 14


def load(name: str):
    return json.loads((STATIC / name).read_text(encoding="utf-8"))


def corpus_ids(records) -> list[str]:
    ids = []
    for record in records:
        if isinstance(record, list):
            ids.append(f"{record[0]}:{record[1]}")
    return ids


def span(first: str, last: str) -> int:
    """تعدادِ آیه در بازهٔ بسته."""
    fs, fa = map(int, first.split(":"))
    ls, la = map(int, last.split(":"))
    return la - fa + 1 if fs == ls else 10**6


def ranges(uncovered: list[str], size: int, batch_size: int = 12) -> list[str]:
    if not uncovered:
        return []
    out, start, prev = [], uncovered[0], uncovered[0]
    for vid in uncovered[1:]:
        surah, ayah = map(int, vid.split(":"))
        psurah, payah = map(int, prev.split(":"))
        if (surah, ayah) == (psurah, payah + 1) and span(start, vid) <= batch_size:
            prev = vid
            continue
        out.append((start, prev))
        start = prev = vid
    out.append((start, prev))
    labels = []
    for first, last in out:
        labels.append(first if first == last else f"{first}–{last.split(':')[1]}")
    return labels[:size]


def audit(entry: dict) -> list[str]:
    problems = []
    for field in FIELDS:
        items = entry.get(field) or []
        if not items:
            problems.append(f"{field} خالی")
            continue
        for item in items:
            if not item.get("text", "").strip() or not item.get("cite", "").strip():
                problems.append(f"{field}: بندِ بی‌متن یا بی‌ارجاع")
            elif len(item["text"].split()) < MIN_WORDS:
                problems.append(f"{field}: بندِ کوتاه")
    classical = [i for i in entry.get("classical", []) if "ق،" in i.get("cite", "")]
    modern = [i for i in entry.get("modern", []) if "ق،" not in i.get("cite", "")]
    if len(classical) < 2:
        problems.append("خوانش کهن کمتر از دو مورد")
    if len(modern) < 2:
        problems.append("پژوهش معاصر کمتر از دو مورد")
    if len(entry.get("critical", [])) < 3:
        problems.append("خوانش انتقادی کمتر از سه بند")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--next", type=int, default=1, help="تعدادِ بازه‌های بعدی")
    parser.add_argument("--batch-size", type=int, default=12)
    args = parser.parse_args()

    corpus = load("offline-corpus.json")["verses"]
    dossier = load("verse-dossiers.json")
    ids = corpus_ids(corpus)
    covered = [vid for vid in ids if vid in dossier["verses"]]
    uncovered = [vid for vid in ids if vid not in dossier["verses"]]
    unknown = set(dossier["verses"]) - set(ids)

    print(f"پوشش: {len(covered)} از {len(ids)} آیه ({len(covered) / len(ids):.2%})")
    print(f"بسته‌ها: {sum(b['count'] for b in dossier['batches'])} آیه در {len(dossier['batches'])} بسته")
    for batch in dossier["batches"]:
        print(f"  · {batch['id']}: {batch['range']} — {batch['count']} آیه — {batch['status']}")
    if unknown:
        print(f"هشدار: آیهٔ ناموجود در پیکره: {sorted(unknown)}")

    broken = {vid: audit(entry) for vid, entry in dossier["verses"].items() if audit(entry)}
    print("سلامتِ داده:", "سالم" if not broken else f"{len(broken)} مدخلِ نیازمندِ اصلاح")
    for vid, problems in broken.items():
        print(f"  · {vid}: {'؛ '.join(problems)}")

    upcoming = ranges(uncovered, args.next, args.batch_size)
    print("بازهٔ بعدی:", "، ".join(upcoming) if upcoming else "همهٔ آیه‌ها پوشش دارند")
    return 0 if not broken and not unknown else 1


if __name__ == "__main__":
    raise SystemExit(main())
