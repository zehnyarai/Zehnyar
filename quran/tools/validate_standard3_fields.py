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

    design_errors: list[str] = []
    for field in data["fields"]:
        for key in ("question", "acceptance", "rejection"):
            if not str(field.get(key, "")).strip():
                design_errors.append(f"field {field.get('id')!r}: missing design key {key}")
        if field.get("allowedKinds") != ["analysis", "source-coverage-note"]:
            design_errors.append(f"field {field.get('id')!r}: allowedKinds drifted")
        if field.get("minEntries") != {"core": 1, "full": 5}:
            design_errors.append(f"field {field.get('id')!r}: minEntries drifted")
        if field.get("evidenceKeys") != ["text", "cite", "evidence", "limit"]:
            design_errors.append(f"field {field.get('id')!r}: evidenceKeys drifted")
    errors.extend(design_errors)

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

        if dossier.get("requiresDiverseSources"):
            mix = dossier.get("sourceMix")
            roles = {str(item.get("role", "")) for item in mix} if isinstance(mix, list) else set()
            if not any(role.startswith("shia") for role in roles):
                errors.append(f"{verse_id}: diversity policy needs at least one Shia source")
            if "journal" not in roles:
                errors.append(f"{verse_id}: diversity policy needs at least one peer-reviewed article")

        for field_id in BASE_FIELDS:
            entries = dossier.get(field_id)
            if not isinstance(entries, list):
                errors.append(f"{verse_id}:{field_id}: base field entries must be a list")
                continue
            tier = str(dossier.get("tier", "full"))
            if tier not in ("full", "core"):
                errors.append(f"{verse_id}: unknown coverage tier {tier!r}")
            required_here = required if tier == "full" else 3
            if tier == "core" and not str(dossier.get("coverageNote", "")).strip():
                errors.append(f"{verse_id}: core tier requires an explicit coverageNote")
            if len(entries) < required_here:
                errors.append(
                    f"{verse_id}:{field_id}: base field has fewer than {required_here} entries ({tier} tier)"
                )
            for index, entry in enumerate(entries, 1):
                counts["baseEntries"] += 1
                check_text(verse_id, field_id, index, entry, base=True)

        extended = dossier.get("extendedFields")
        if not isinstance(extended, dict) or set(extended) != field_ids:
            errors.append(f"{verse_id}: Standard 3 fields do not match schema")
            continue

        if int(dossier.get("sourcePolicyVersion", 1)) >= 2:
            analysed = 0
            for field_id, field in (dossier.get("extendedFields") or {}).items():
                kinds = [entry.get("kind") for entry in field.get("entries", [])]
                analysed += 1 if "analysis" in kinds else 0
                for kind in kinds:
                    if kind not in ("analysis", "source-coverage-note"):
                        errors.append(f"{verse_id}:{field_id}: unknown entry kind {kind!r}")
            if analysed < 8:
                errors.append(f"{verse_id}: only {analysed}/10 fields carry a researched entry")

        # --- source-diversity policy v2 (see criteria.policyNote)
        if int(dossier.get("sourcePolicyVersion", 1)) >= 2:
            mix = dossier.get("sourceMix")
            if not isinstance(mix, list) or not mix:
                errors.append(f"{verse_id}: policy v2 requires a non-empty sourceMix")
            else:
                named = [item for item in mix if item.get("role") in ("classical", "modern", "academic")]
                roles = {item.get("role") for item in named}
                if len(named) < 3:
                    errors.append(f"{verse_id}: policy v2 needs at least three distinct works, found {len(named)}")
                if "classical" not in roles or "modern" not in roles:
                    errors.append(f"{verse_id}: policy v2 needs at least one classical and one modern work")
                contemporary = [item for item in named if item.get("role") in ("modern", "academic")]
                contemporary_entries = sum(int(item.get("entries", 0)) for item in contemporary)
                for item in contemporary:
                    if int(item.get("entries", 0)) == 0:
                        continue
                    share = int(item.get("entries", 0)) / max(contemporary_entries, 1)
                    if share > 0.6:
                        errors.append(
                            f"{verse_id}: policy v2 caps one contemporary work at 60% of contemporary entries; "
                            f"{item.get('work')} holds {share:.0%}"
                        )
                for item in named:
                    if item.get("work") == "التفسير الميسر" and int(item.get("entries", 0)) > 1:
                        errors.append(f"{verse_id}: policy v2 allows at most one Muyassar entry per record")

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
