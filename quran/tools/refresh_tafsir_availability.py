#!/usr/bin/env python3
"""Mark commentary sources according to the files present in this checkout/build."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
SOURCE_PATH = STATIC / "tafsir-sources.json"
CATALOG_PATH = STATIC / "tafsir-catalog.json"

EXCERPT_BASIS = (
    "در دادهٔ محلی ارجاع و خلاصهٔ منتسب موجود است؛ متن کامل در این بسته نیست. "
    "برای نقلِ مستقیم، نسخهٔ منبع را بررسی کنید."
)
AVAILABLE_BASIS = {
    "ar_qe_arabic_moyassar": "QuranEnc، نسخهٔ 1.0.0؛ متن آیه‌به‌آیه در بستهٔ محلی موجود است.",
    "ar_tabari_qurancom": "متن آیه‌به‌آیه در بستهٔ محلی موجود است؛ نسخهٔ 1.1 و انتساب ثبت شده است.",
    "ar_qurtubi_qurancom": "متن آیه‌به‌آیه در بستهٔ محلی موجود است؛ نسخهٔ 1.1 و انتساب ثبت شده است.",
    "fa_mizan_furqan": "متن آیه‌به‌آیه در بستهٔ محلی موجود است؛ نسخهٔ 2026.0 و انتساب ثبت شده است.",
}
CATALOG_ALIASES = {
    "tabari": "ar_tabari_qurancom",
    "qurtubi": "ar_qurtubi_qurancom",
    "mizan": "fa_mizan_furqan",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    registry = read_json(SOURCE_PATH)
    source_status: dict[str, bool] = {}
    for source in registry.get("sources", []):
        relative = Path(source.get("file", ""))
        available = bool(relative.parts) and (ROOT / relative).is_file()
        source["localAvailable"] = available
        source_status[source["id"]] = available

    catalog = read_json(CATALOG_PATH)
    for collection in catalog.get("collections", []):
        if collection.get("id") not in {"current-cited", "requested-comparative"}:
            continue
        for item in collection.get("items", []):
            source_id = CATALOG_ALIASES.get(item.get("id"), item.get("id"))
            if source_id not in source_status:
                continue
            available = source_status[source_id]
            item["status"] = "available" if available else "excerpt-only"
            if available:
                item["basis"] = AVAILABLE_BASIS.get(
                    source_id,
                    "متنِ منبع در بستهٔ محلی موجود است؛ انتساب و نسخه در فراداده ثبت شده است.",
                )
            else:
                item["basis"] = EXCERPT_BASIS

    write_json(SOURCE_PATH, registry)
    write_json(CATALOG_PATH, catalog)
    print("Reconciled tafsir source availability with the files in this checkout.")


if __name__ == "__main__":
    main()
