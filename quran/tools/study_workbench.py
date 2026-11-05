#!/usr/bin/env python3
"""Prepare, validate and merge verse-study dossiers without inventing content.

The workbench gathers exact local source material and creates an EMPTY editorial
form. It never turns lexical matches, generic prose or source excerpts into a
reviewed annotation. Sources absent from the current checkout are not represented
as if their full text had been loaded.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
ANNOTATIONS = STATIC / "verse-study-annotations.json"
SOURCE_REGISTRY = STATIC / "tafsir-sources.json"
MODELS = ("izutsu", "fillmore", "cognitive")
SECTIONS = ("notes", "messages", "principles", "framework", "thematic", "context", "network")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def verse_id(surah: int, ayah: int) -> str:
    return f"{surah}:{ayah}"


def collect_sources():
    """Return only commentary payloads that exist in this checkout."""
    registry = load(SOURCE_REGISTRY)
    sources = {}
    for source in registry.get("sources", []):
        path = ROOT / source.get("file", "")
        if path.is_file():
            sources[source["id"]] = {"metadata": source, "payload": load(path)}
    return sources


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
    sources = collect_sources()
    result = []
    for surah, ayah, arabic, translation, surah_name, revelation in rows:
        key = verse_id(surah, ayah)
        source_texts = {}
        for source_id, item in sources.items():
            metadata = item["metadata"]
            if surah in metadata.get("excludeFromSurahs", []):
                continue
            payload = item["payload"]
            record = payload.get("verses", {}).get(str(surah), {}).get(str(ayah))
            if record is None and payload.get("ayahMapping"):
                content_id = payload["ayahMapping"].get(str(surah), {}).get(str(ayah))
                record = payload.get("contents", {}).get(str(content_id))
            if record:
                source_texts[source_id] = record.get("text", "")
        annotation = {
            "status": "پیش‌نویس تحریری؛ نیازمند بازبینی تخصصی",
            "notes": [], "messages": [], "principles": [],
            "framework": {model: {field: "" for field in ("input", "operation", "meaning", "limit")} for model in MODELS},
            "thematic": [], "context": [], "network": [], "sources": list(source_texts),
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
        "notice": "منابعِ موجود در همین ساخت برای پژوهش گردآوری شده‌اند؛ منابعِ فاقد فایل در فراداده پیوند دارند. annotation عمداً خالی است و نباید پیش از نگارش و بازبینی منتشر شود.",
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
        for section in SECTIONS:
            values = a.get(section)
            if not values:
                errors.append(f"{key}: {section} is empty")
                continue
            if section in ("notes", "principles", "messages"):
                if not isinstance(values, list) or len(values) < 4:
                    errors.append(f"{key}: {section} needs at least four distinct, evidence-backed items")
                    continue
                seen_text = set()
                for index, value in enumerate(values, 1):
                    if not isinstance(value, dict) or not str(value.get("text", "")).strip() or not str(value.get("evidence", "")).strip():
                        errors.append(f"{key}: {section}[{index}] needs text and an explicit evidence citation")
                        continue
                    normalized_text = " ".join(str(value["text"]).split()).casefold()
                    if normalized_text in seen_text:
                        errors.append(f"{key}: {section}[{index}] duplicates an earlier item")
                    seen_text.add(normalized_text)
        framework = a.get("framework", {})
        for model in MODELS:
            for field in ("input", "operation", "meaning", "limit"):
                if not str(framework.get(model, {}).get(field, "")).strip():
                    errors.append(f"{key}: framework.{model}.{field} is empty")
        for field in ("thematic", "context", "network"):
            if not a.get(field):
                errors.append(f"{key}: {field} is empty")
    return errors


def merge_batch(batch: dict) -> int:
    errors = validate_batch(batch)
    if errors:
        raise ValueError("\n".join(errors))
    payload = load(ANNOTATIONS)
    verses = payload["verses"]
    inserted = 0
    for item in batch["verses"]:
        key = item["id"]
        if key in verses:
            continue
        verses[key] = item["annotation"]
        inserted += 1
    payload["verses"] = verses
    ANNOTATIONS.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return inserted


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--start", required=True)
    prepare_parser.add_argument("--count", type=int, required=True)
    prepare_parser.add_argument("--output", type=Path, required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("batch", type=Path)
    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("batch", type=Path)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        batch = prepare(args.start, args.count)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {len(batch['verses'])} empty editorial forms to {args.output}")
    elif args.command == "validate":
        errors = validate_batch(load(args.batch))
        if errors:
            print("\n".join(errors))
            return 1
        print("Batch structure is complete; this does not certify scholarly accuracy.")
    elif args.command == "merge":
        inserted = merge_batch(load(args.batch))
        print(f"Inserted {inserted} new verse records; existing annotations were not overwritten.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
