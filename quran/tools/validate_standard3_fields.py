# -*- coding: utf-8 -*-
"""Validate verse-level Standard 3 fields, word thresholds, honest gaps, and exact-text uniqueness."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "static" / "verse-dossier-extended-fields.json"
BASE_FIELDS = ("notes", "context", "classical", "modern", "critical", "research")
VALID_STATUSES = {"complete", "partial", "needs-research"}


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text.strip()))


def validate(path: Path = DATA_PATH) -> tuple[list[str], dict[str, int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    criteria = data["criteria"]
    required = int(criteria["requiredEntriesPerField"])
    minimum_words = int(criteria["minimumWordsPerEntry"])
    field_ids = {field["id"] for field in data["fields"]}
    errors: list[str] = []
    counts = {
        "verses": len(data["verses"]),
        "fields": 0,
        "baseEntries": 0,
        "complete": 0,
        "partial": 0,
        "needs-research": 0,
    }
    global_seen: dict[str, str] = {}

    def check_text(verse_id: str, field_id: str, index: int, entry: object, *, base: bool) -> None:
        if not isinstance(entry, dict):
            errors.append(f"{verse_id}:{field_id}[{index}]: entry must be an object")
            return
        text = str(entry.get("text", "")).strip()
        if word_count(text) < minimum_words:
            errors.append(f"{verse_id}:{field_id}[{index}]: fewer than {minimum_words} words")
        keys = ("cite",) if base else ("cite", "evidence", "limit")
        for key in keys:
            if not str(entry.get(key, "")).strip():
                errors.append(f"{verse_id}:{field_id}[{index}]: missing {key}")
        normalized = " ".join(text.split())
        if normalized:
            location = f"{verse_id}:{field_id}[{index}]"
            previous = global_seen.get(normalized)
            if previous:
                errors.append(f"{location}: exact duplicate text also occurs at {previous}")
            else:
                global_seen[normalized] = location

    for verse_id, dossier in data["verses"].items():
        if not isinstance(dossier, dict):
            errors.append(f"{verse_id}: dossier must be an object")
            continue

        for field_id in BASE_FIELDS:
            entries = dossier.get(field_id)
            if not isinstance(entries, list):
                errors.append(f"{verse_id}:{field_id}: base field entries must be a list")
                continue
            if len(entries) < required:
                errors.append(f"{verse_id}:{field_id}: base field has fewer than {required} entries")
            for index, entry in enumerate(entries, 1):
                counts["baseEntries"] += 1
                check_text(verse_id, field_id, index, entry, base=True)

        extended = dossier.get("extendedFields")
        if not isinstance(extended, dict) or set(extended) != field_ids:
            errors.append(f"{verse_id}: Standard 3 fields do not match schema")
            continue

        for field_id, field in extended.items():
            counts["fields"] += 1
            if not isinstance(field, dict):
                errors.append(f"{verse_id}:{field_id}: field must be an object")
                continue
            status = field.get("status")
            if status not in VALID_STATUSES:
                errors.append(f"{verse_id}:{field_id}: invalid status {status!r}")
                continue
            entries = field.get("entries")
            if not isinstance(entries, list):
                errors.append(f"{verse_id}:{field_id}: entries must be a list")
                continue
            if not field.get("followUp", "").strip() or not field.get("sourceCoverageNote", "").strip():
                errors.append(f"{verse_id}:{field_id}: field needs source note and follow-up")
            expected_coverage = {"completed": len(entries), "required": required}
            if field.get("coverage") != expected_coverage:
                errors.append(f"{verse_id}:{field_id}: coverage does not match recorded entries")
            if status == "needs-research" and entries:
                errors.append(f"{verse_id}:{field_id}: needs-research field unexpectedly has entries")
            if status == "partial" and not (0 < len(entries) < required):
                errors.append(f"{verse_id}:{field_id}: partial status requires 1..{required - 1} entries")
            if status == "complete":
                counts["complete"] += 1
                if len(entries) < required:
                    errors.append(f"{verse_id}:{field_id}: complete field has fewer than {required} entries")
            elif status == "partial":
                counts["partial"] += 1
            else:
                counts["needs-research"] += 1
            for index, entry in enumerate(entries, 1):
                check_text(verse_id, field_id, index, entry, base=False)
    return errors, counts


def main() -> int:
    errors, counts = validate()
    print(
        f"Standard 3: {counts['verses']} ayahs, {counts['fields']} extended fields, "
        f"{counts['baseEntries']} base entries; complete={counts['complete']}, "
        f"partial={counts['partial']}, needs-research={counts['needs-research']}"
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Schema, base-field thresholds, exact-text uniqueness, and recorded statuses are valid; pending fields are not counted complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
