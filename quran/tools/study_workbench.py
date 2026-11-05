#!/usr/bin/env python3
"""Prepare, validate and merge verse-study dossiers without inventing content.

The workbench gathers exact local source material and creates an EMPTY editorial
form. It never turns lexical matches, generic prose or source excerpts into a
reviewed annotation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
ANNOTATIONS = STATIC / "verse-study-annotations.json"
MODELS = ("izutsu", "fillmore", "cognitive", "historical", "interdisciplinary")
SECTIONS = ("notes", "messages", "principles", "framework", "thematic", "context", "network", "research")
LIST_SECTIONS = ("notes", "messages", "principles", "thematic", "context", "network", "research")
MIN_ITEMS = 5
SOURCE_FILES = {
    "ar_qe_arabic_moyassar": STATIC / "tafsir/arabic-moyassar-quranenc-1.0.0.json",
    "ar_tabari_qurancom": STATIC / "tafsir/arabic-tabari-quran-com-api-1.1.json",
    "ar_qurtubi_qurancom": STATIC / "tafsir/arabic-qurtubi-quran-com-api-1.1.json",
    "fa_mizan_furqan": STATIC / "tafsir/persian-mizan-furqan-2026.json",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def verse_id(surah: int, ayah: int) -> str:
    return f"{surah}:{ayah}"


def collect_sources():
    return {key: load(path) for key, path in SOURCE_FILES.items()}


def prepare(start: str, count: int) -> dict:
    corpus = load(STATIC / "offline-corpus.json")["verses"]
    ids = [verse_id(row[0], row[1]) for row in corpus]
    if start not in ids:
        raise ValueError(f"Unknown verse id: {start}")
    if count < 1:
        raise ValueError("count must be positive")
    first = ids.index(start)
    if first + count > len(corpus):
        raise ValueError(f"Requested {count} verses from {start}, but only {len(corpus) - first} remain")
    rows = corpus[first:first + count]
    tafsirs = collect_sources()
    result = []
    for surah, ayah, arabic, translation, surah_name, revelation in rows:
        key = verse_id(surah, ayah)
        source_texts = {}
        for source_id, payload in tafsirs.items():
            record = payload.get("verses", {}).get(str(surah), {}).get(str(ayah))
            if record is None and payload.get("ayahMapping"):
                content_id = payload["ayahMapping"].get(str(surah), {}).get(str(ayah))
                record = payload.get("contents", {}).get(str(content_id))
            if record:
                source_texts[source_id] = record.get("text", "")
        annotation = {
            "status": "پیش‌نویس تحریری؛ نیازمند بازبینی تخصصی",
            "notes": [], "messages": [], "principles": [],
            "framework": {model: {field: "" for field in ("input", "operation", "meaning", "limit", "cite")} for model in MODELS},
            "thematic": [], "context": [], "network": [], "research": [], "sources": list(source_texts),
        }
        result.append({
            "id": key,
            "sourceMaterial": {
                "arabic": arabic, "translation_fa": translation,
                "surah_name_ar": surah_name, "revelation": revelation,
                "tafsir": source_texts,
            },
            "annotation": annotation,
        })
    return {
        "schemaVersion": 1,
        "notice": "منابع برای پژوهش گردآوری شده‌اند؛ annotation عمداً خالی است و نباید پیش از نگارش و بازبینی منتشر شود.",
        "start": rows[0][:2], "end": rows[-1][:2],
        "verses": result,
    }


def validate_batch(batch: dict) -> list[str]:
    errors = []
    entries = batch.get("verses")
    if not isinstance(entries, list) or not entries:
        return ["verses must be a non-empty list"]
    seen = set()
    for item in entries:
        key = item.get("id", "?")
        if key in seen:
            errors.append(f"{key}: duplicate verse")
        seen.add(key)
        a = item.get("annotation", {})
        for section in LIST_SECTIONS:
            values = a.get(section)
            if not isinstance(values, list) or not values:
                errors.append(f"{key}: {section} is empty or must be a list")
                continue
            if len(values) < MIN_ITEMS:
                errors.append(f"{key}: {section} needs at least five distinct, evidence-backed items")
                continue
            seen_text = set()
            for index, value in enumerate(values, 1):
                if not isinstance(value, dict):
                    errors.append(f"{key}: {section}[{index}] must be an object")
                    continue
                if section in ("notes", "messages", "principles"):
                    content = str(value.get("text", "")).strip()
                    required = ("text", "evidence")
                elif section in ("thematic", "context", "network"):
                    content = str(value.get("relation", "")).strip()
                    required = ("reference", "relation", "evidence")
                else:
                    content = str(value.get("question", "")).strip()
                    required = ("title", "question", "evidence")
                missing = [field for field in required if not str(value.get(field, "")).strip()]
                if missing:
                    errors.append(f"{key}: {section}[{index}] needs {', '.join(missing)}")
                    continue
                normalized_text = " ".join(content.split()).casefold()
                if normalized_text in seen_text:
                    errors.append(f"{key}: {section}[{index}] duplicates an earlier item")
                seen_text.add(normalized_text)
        framework = a.get("framework", {})
        if not isinstance(framework, dict):
            errors.append(f"{key}: framework must be an object")
            framework = {}
        for model in MODELS:
            for field in ("input", "operation", "meaning", "limit", "cite"):
                if not str(framework.get(model, {}).get(field, "")).strip():
                    errors.append(f"{key}: framework.{model}.{field} is empty")
        if not a.get("sources"):
            errors.append(f"{key}: source ids are required")
        for source in a.get("sources", []):
            if source not in SOURCE_FILES:
                errors.append(f"{key}: unknown local source {source}")
    return errors


def merge(batch: dict) -> int:
    errors = validate_batch(batch)
    if errors:
        raise ValueError("Cannot merge incomplete batch:\n" + "\n".join(errors))
    payload = load(ANNOTATIONS)
    verses = payload.setdefault("verses", {})
    for item in batch["verses"]:
        key = item["id"]
        if key in verses:
            raise ValueError(f"{key} already exists; refusing to overwrite")
        verses[key] = item["annotation"]
    lo, hi = batch["start"], batch["end"]
    ranges = payload.get("coverageRange", payload.get("reviewedRange", ""))
    ranges += f"; {lo[0]}:{lo[1]}-{hi[0]}:{hi[1]}"
    payload["coverageRange"] = ranges.lstrip("; ")
    payload.pop("reviewedRange", None)
    ANNOTATIONS.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(batch["verses"])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="collect verse and local tafsir source material")
    prep.add_argument("--start", required=True, help="verse id, e.g. 2:41")
    prep.add_argument("--count", type=int, default=50)
    prep.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("validate", help="check a completed batch; no files are changed")
    check.add_argument("batch", type=Path)
    join = sub.add_parser("merge", help="merge only a complete batch; never overwrites an existing verse")
    join.add_argument("batch", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            data = prepare(args.start, args.count)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Prepared {len(data['verses'])} source packets: {data['verses'][0]['id']}–{data['verses'][-1]['id']}")
        elif args.command == "validate":
            errors = validate_batch(load(args.batch))
            if errors:
                print("\n".join(errors), file=sys.stderr)
                return 1
            print("Batch structure and required fields are complete; this does not certify scholarly correctness.")
        else:
            print(f"Merged {merge(load(args.batch))} verse dossier(s). Expert review status remains explicit.")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
