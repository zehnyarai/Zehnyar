"""Create a human-review checklist from the current dataset; never edits data."""

import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_report(dataset: dict, month: str) -> str:
    meta = dataset["meta"]
    lines = [
        f"# Monthly migration-data review — {month}",
        "",
        "This is a human verification task. **Do not change thresholds or mark data reviewed based only on this reminder.**",
        "Check each route against its linked official authority, save the exact page/notice and effective date in the pull request, and change only facts confirmed to have changed. No scraping or automatic rule publication is used.",
        "",
        f"- Dataset version: `{meta['version']}` (schema `{meta.get('schemaVersion', 'unknown')}`)",
        f"- Dataset-wide recorded review date: `{meta.get('lastVerified', 'missing')}`",
        f"- Review interval: {meta.get('reviewIntervalDays', 30)} days; stale threshold: {meta.get('staleAfterDays', 45)} days",
        f"- Coverage: {len(dataset['countries'])} countries, {sum(len(c['visas']) for c in dataset['countries'])} visa routes, {len(dataset['occupations'])} occupations",
        "",
        "## Review checklist",
        "",
        "- [ ] Confirm each cited source is an official, current government or regulator page.",
        "- [ ] Check eligibility, thresholds, points, occupation lists, quotas, language rules and application fees, including effective dates and family members.",
        "- [ ] Review marked-estimated values and `verified` flags; keep estimates explicitly labelled when no authoritative figure is available.",
        "- [ ] Record the reviewer, review date, source title/URL, effective date, and before/after values for each changed fact.",
        "- [ ] If a source is unavailable or ambiguous, leave the existing value unchanged and note the unresolved item; escalate rather than guess.",
        "- [ ] Run the dataset builder, freshness checker, parity tests and mobile tests; obtain human approval before merging.",
        "",
        "## Countries and routes",
        "",
    ]
    for country in dataset["countries"]:
        official = country["official"]
        lines.append(f"### {country['nameEn']} / {country['nameFa']} (`{country['code']}`)")
        lines.append(f"Official portal: [{official.get('portalLabelEn', 'Official portal')}]({official['portal']}) · recorded date: `{official.get('lastVerified', 'missing')}`")
        for visa in country["visas"]:
            lines.append(f"- [ ] {visa['nameEn']} (`{visa['id']}`) — [route source]({visa['officialUrl']})")
        lines.append("")
    lines.extend([
        "## Required PR evidence",
        "",
        "Include a concise review table with route/fact, official source and notice date, effective date, outcome (changed / confirmed unchanged / unresolved), reviewer, and dataset fields changed. Update `LAST_VERIFIED` only after the scheduled scope has genuinely been checked; the shared date is not evidence that each individual fact was independently verified.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--month", default=date.today().strftime("%Y-%m"))
    args = parser.parse_args()
    dataset = json.loads((ROOT / "shared" / "dataset.json").read_text(encoding="utf-8"))
    Path(args.output).write_text(build_report(dataset, args.month), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
