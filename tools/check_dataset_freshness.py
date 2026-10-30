"""Report whether the reference data has been reviewed recently.

A stale date is a release blocker only when --fail-when-stale is requested;
malformed or future dates always fail. This checker never changes data.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "shared" / "dataset.json"


def get_report(dataset: dict, today: date, max_age_days: int | None = None) -> dict:
    meta = dataset.get("meta", {})
    limit = max_age_days if max_age_days is not None else meta.get("staleAfterDays", 45)
    dates = [("dataset", meta.get("lastVerified"))]
    dates.extend(
        (country.get("code", "unknown"), country.get("official", {}).get("lastVerified"))
        for country in dataset.get("countries", [])
    )
    review_interval = meta.get("reviewIntervalDays", 30)
    results = []
    for name, raw in dates:
        try:
            verified = date.fromisoformat(raw)
        except (TypeError, ValueError):
            raise ValueError(f"{name}: lastVerified must be an ISO date (YYYY-MM-DD)")
        age = (today - verified).days
        if age < 0:
            raise ValueError(f"{name}: lastVerified {raw} is in the future")
        results.append({
            "name": name,
            "lastVerified": raw,
            "ageDays": age,
            "reviewDue": age >= review_interval,
            "stale": age > limit,
        })
    stale = any(row["stale"] for row in results)
    review_due = any(row["reviewDue"] for row in results)
    status = "stale" if stale else "review_due" if review_due else "current"
    return {"today": today.isoformat(), "reviewIntervalDays": review_interval, "maxAgeDays": limit, "status": status, "reviewDue": review_due, "stale": stale, "records": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-age-days", type=int, help="Override dataset staleAfterDays")
    parser.add_argument("--fail-when-stale", action="store_true", help="Exit non-zero when any date is older than the limit")
    args = parser.parse_args()
    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    try:
        report = get_report(dataset, date.today(), args.max_age_days)
    except ValueError as exc:
        print(f"DATA DATE ERROR: {exc}")
        return 1
    age = report["records"][0]["ageDays"]
    status = report["status"].replace("_", " ").upper()
    print(f"{status}: dataset review age {age} days; review interval {report['reviewIntervalDays']} days; stale limit {report['maxAgeDays']} days; {len(report['records']) - 1} country records checked")
    if report["stale"]:
        old = ", ".join(row["name"] for row in report["records"] if row["stale"])
        print(f"Review required: {old}")
        return 1 if args.fail_when_stale else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
