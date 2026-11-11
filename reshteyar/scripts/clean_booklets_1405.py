"""پاکسازی فهرست‌های دفترچه‌ی ۱۴۰۵ (`data/booklets_1405.json`).

- نام‌هایی که فقط با پسوند «- شهر» از نام اصلی دانشگاه فرق دارند، زیر نام اصلی ادغام می‌شوند.
- ردیف‌های بدون نام دانشگاه به «(نامشخص)» بروند تا شمارش آن‌ها دیده شود.

اجرا: python3 reshteyar/scripts/clean_booklets_1405.py
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "data" / "booklets_1405.json"
SUFFIX = re.compile(r"^(.*?)\s+-\s+([^-]{2,20})$")


def main() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    for key, group in data["groups"].items():
        names = {u["name"]: u["rows"] for u in group["universities"]}
        merged: Counter = Counter()
        for name, rows in names.items():
            m = SUFFIX.match(name)
            base = m.group(1).strip() if m else None
            if base and base in names and name != "(نامشخص)":
                merged[base] += rows
            else:
                merged[name] += rows
        group["universities"] = sorted(
            ({"name": n, "rows": r} for n, r in merged.items()), key=lambda x: (-x["rows"], x["name"])
        )
        print(key, "universities", len(group["universities"]), "fields", len(group["fields"]),
              "unnamed rows", names.get("(نامشخص)", 0))
    data["note"] = ("فهرست از متن دفترچه‌های PDF استخراج شده و بازبینی دستی نشده است. "
                    "اصلاحیه‌های ۱۶، ۱۸ و ۱۹ مهر ۱۴۰۵ اعمال نشده‌اند. "
                    "فهرست رشته‌ها فقط از ردیف‌های کدرشته‌محل استخراج شده است.")
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
