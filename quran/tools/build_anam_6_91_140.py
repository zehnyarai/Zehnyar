#!/usr/bin/env python3
"""Build source-linked draft dossiers for al-An'am 6:91–140."""
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

import build_anam_6_41_90 as renderer
import build_maida_5_111_120_anam_6_1_40 as source_builder
import build_nisa_4_1_12 as shared
import anam_6_91_140_data as curated

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
DOSSIER_PATH = STATIC / "verse-dossiers.json"
CATALOG_PATH = STATIC / "tafsir-catalog.json"
REGISTRY_PATH = STATIC / "tafsir-sources.json"
ATTRIBUTION_PATH = ROOT / "data" / "TAFSIR_ATTRIBUTION.md"
BATCH_ID = "dossier-60"
COLLECTION_ID = "anam-6-91-140-cited"

TABARI, IBN, QURTUBI = renderer.TABARI, renderer.IBN, renderer.QURTUBI
TUSI, FAYD = renderer.TUSI, renderer.FAYD
QURANENC, WASIT = renderer.QURANENC, renderer.WASIT
CLASSICAL_ORDER = renderer.CLASSICAL_ORDER
SOURCE_ORDER = renderer.SOURCE_ORDER
SUNNI, SHIA = renderer.SUNNI, renderer.SHIA
MODELS, FIELDS = renderer.MODELS, renderer.FIELDS
VERSES = tuple(curated.DATA)

# OpenITI marker spans define actual source coverage, not printed-page ranges.
TUSI_GROUPS = {f"6:{ayah}": (ayah, ayah) for ayah in range(91, 141)}
for ayah in (126, 127):
    TUSI_GROUPS[f"6:{ayah}"] = (126, 127)

FAYD_GROUPS: dict[str, tuple[int, int]] = {}
for start, end in (
    (91, 93), (94, 96), (97, 99), (100, 103), (104, 108),
    (109, 112), (113, 119), (120, 122), (123, 125), (126, 127),
    (128, 135), (136, 141),
):
    for ayah in range(max(start, 91), min(end, 140) + 1):
        FAYD_GROUPS[f"6:{ayah}"] = (start, end)

SECTIONS = (
    (91, 100, "وحی، یگانگی و نشانه‌هایِ آفرینش"),
    (101, 110, "صفاتِ خدا، حجت و جدالِ مخاطبان"),
    (111, 120, "دشمنی، داوری و مرزِ حلال و حرام"),
    (121, 130, "خوراک، هدایت و بازخواستِ جن و انس"),
    (131, 140, "عدالت، فرجام و رسم‌هایِ خودساخته"),
)

# Reuse citation/rendering functions without mutating batch 59's module state.
@contextmanager
def renderer_batch_context():
    names = ("TUSI_GROUPS", "FAYD_GROUPS", "SECTIONS", "VERSES")
    previous = {name: getattr(renderer, name) for name in names}
    renderer.TUSI_GROUPS = TUSI_GROUPS
    renderer.FAYD_GROUPS = FAYD_GROUPS
    renderer.SECTIONS = SECTIONS
    renderer.VERSES = VERSES
    try:
        yield
    finally:
        for name, value in previous.items():
            setattr(renderer, name, value)


def fa_num(value: int) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def validate_data(registry: dict | None = None) -> None:
    expected = tuple(f"6:{ayah}" for ayah in range(91, 141))
    assert VERSES == expected, (len(VERSES), VERSES[:2], VERSES[-2:])
    assert set(curated.DATA) == set(expected)
    assert set(TUSI_GROUPS) == set(expected)
    assert set(FAYD_GROUPS) == set(expected)
    assert TUSI_GROUPS["6:126"] == TUSI_GROUPS["6:127"] == (126, 127)
    assert TUSI_GROUPS["6:125"] == (125, 125) and TUSI_GROUPS["6:128"] == (128, 128)
    assert FAYD_GROUPS["6:91"] == FAYD_GROUPS["6:93"] == (91, 93)
    assert FAYD_GROUPS["6:104"] == FAYD_GROUPS["6:108"] == (104, 108)
    assert FAYD_GROUPS["6:128"] == FAYD_GROUPS["6:135"] == (128, 135)
    assert FAYD_GROUPS["6:136"] == FAYD_GROUPS["6:140"] == (136, 141)
    for key, record in curated.DATA.items():
        assert len(record["notes"]) == len(record["critical"]) == len(record["research"]) == 5, key
        assert set(record["classical"]) == set(CLASSICAL_ORDER), key
        assert set(record["modern_sources"]) == {QURANENC, WASIT}, key
        assert len(record["model_terms"]) == 3 and all(record["model_terms"]), key
        for field in ("notes", "critical", "research"):
            for text, source_ids in record[field]:
                assert text.strip() and source_ids and set(source_ids) <= set(SOURCE_ORDER), (key, field, source_ids)
                expanded = renderer.expand_item_text(text, key, field, source_ids)
                assert len(expanded.split()) >= 14, (key, field, text)
        for source_id, text in record["classical"].items():
            assert text.strip() and len(text.split()) >= 14, (key, source_id, text)
        for source_id, text in record["modern_sources"].items():
            assert text.strip() and len(text.split()) >= 14, (key, source_id, text)
    if registry:
        assert {source["id"] for source in registry["sources"]} >= set(SOURCE_ORDER)


def build_catalog(registry: dict) -> dict:
    by_id = {source["id"]: source for source in registry["sources"]}
    urls_by_source = {source_id: [] for source_id in SOURCE_ORDER}
    for key in VERSES:
        for source_id in SOURCE_ORDER:
            urls_by_source[source_id].append(renderer.source_url(source_id, key))
    bases = {
        TABARI: "مدخل‌هایِ آیه‌محورِ طبری در آرشیوِ Quran.com API v4 نسخهٔ 1.1 برایِ انعام ۶:۹۱–۱۴۰ بررسی شدند؛ اقوالِ نقل‌شده به خودِ مفسر منسوب‌اند.",
        IBN: "مدخل‌هایِ آیه‌محورِ ابن‌کثیر برایِ ۵۰ آیهٔ انعام ۶:۹۱–۱۴۰ بررسی شدند؛ گزارش‌هایِ سببِ نزول در خلاصه‌ها به ناقل نسبت داده شده‌اند.",
        QURTUBI: "مدخل‌هایِ آیه‌محورِ قرطبی در آرشیوِ نسخهٔ 1.1 بررسی شدند؛ اختلافِ قرائت، نحو و فقه جدا ثبت شده است.",
        TUSI: "متنِ ناقصِ *التبيان* از OpenITI بررسی شد؛ شرحِ گروهیِ ۶:۱۲۶–۱۲۷ از آیاتِ مستقیم جدا نگه داشته شده است.",
        FAYD: "متنِ ناقصِ *الصافي* از OpenITI بررسی شد؛ گروه‌هایِ نشان‌گذاری‌شده از ۶:۹۱–۹۳ تا ۶:۱۳۶–۱۴۱ حفظ شده‌اند و نقل‌هایِ خاص به ناقلان نسبت دارند.",
        QURANENC: "متنِ محلیِ آیه‌به‌آیهٔ قرآن‌انک، نسخهٔ 1.0.0، برایِ هر ۵۰ آیه بررسی شد؛ خلاصه‌ها نقلِ لفظی نیستند.",
        WASIT: "مدخل‌هایِ عربیِ طنطاوی از آرشیوِ Quran.com API v4 نسخهٔ 1.1 برایِ آیاتِ بازه بررسی شدند؛ چاپ و صفحه احراز نشده است.",
    }
    scopes = {
        TABARI: "انعام ۶:۹۱–۱۴۰؛ مدخل‌هایِ آیه‌محورِ آرشیوِ نسخهٔ 1.1",
        IBN: "انعام ۶:۹۱–۱۴۰؛ مدخل‌هایِ آیه‌محورِ آرشیوِ نسخهٔ 1.1",
        QURTUBI: "انعام ۶:۹۱–۱۴۰؛ مدخل‌هایِ آیه‌محورِ آرشیوِ نسخهٔ 1.1",
        TUSI: "شرحِ گروهیِ ۶:۱۲۶–۱۲۷؛ دیگر مواضعِ بازه، نشانِ مستقیم دارند؛ متنِ ناقصِ OpenITI",
        FAYD: "گروه‌ها: ۶:۹۱–۹۳، ۹۴–۹۶، ۹۷–۹۹، ۱۰۰–۱۰۳، ۱۰۴–۱۰۸، ۱۰۹–۱۱۲، ۱۱۳–۱۱۹، ۱۲۰–۱۲۲، ۱۲۳–۱۲۵، ۱۲۶–۱۲۷، ۱۲۸–۱۳۵ و ۱۳۶–۱۴۱؛ متنِ ناقصِ OpenITI",
        QURANENC: "انعام ۶:۹۱–۱۴۰؛ متنِ محلیِ آیه‌به‌آیه، نسخهٔ 1.0.0",
        WASIT: "انعام ۶:۹۱–۱۴۰؛ مدخل‌هایِ آیه‌محورِ آرشیوِ نسخهٔ 1.1",
    }
    items = []
    for source_id in SOURCE_ORDER:
        source = by_id[source_id]
        urls = list(dict.fromkeys(urls_by_source[source_id]))
        items.append({
            "id": source_id,
            "title": source["title"],
            "author": source["author"],
            "language": source["language"],
            "status": "available" if source.get("localAvailable", False) else "excerpt-only",
            "basis": bases[source_id],
            "sourceUrl": urls[0],
            "sourceUrls": urls,
            "scope": scopes[source_id],
            "version": source.get("version", "صفحاتِ مستقیم/گروهی؛ چاپ و صفحهٔ کتاب احراز نشده"),
            "tradition": source.get("tradition") or shared.SOURCE_TRADITIONS.get(source_id, "اهل‌سنت"),
            "licenseStatus": source.get("licenseStatus", "review-needed"),
        })
    note = (
        "در هر یک از ۵۰ پرونده، شش فیلدِ notes/context/classical/modern/critical/research پنج‌بندی‌اند؛ "
        "پنج شرحِ کهن، دو شرحِ معاصر و سه کاربستِ محدودِ ایزوتسو، فیلمور و معناشناسیِ شناختی از هم جدا شده‌اند. "
        "دامنهٔ گروهیِ طوسی در ۶:۱۲۶–۱۲۷ و گروه‌هایِ فیض از ۶:۹۱–۹۳ تا ۶:۱۳۶–۱۴۱ در هر پرونده ثبت شده‌اند. "
        "گزارش‌هایِ سببِ نزول، قرائت، اختلافِ کلامی و روایت‌هایِ خاص به ناقلِ خود نسبت داده شده‌اند؛ خلاصه‌ها نقلِ لفظی نیستند. "
        "نسخه‌هایِ آرشیوی و OpenITI ناقص‌اند؛ GPL-3.0 مخزن به‌تنهایی حقِ اقتباس از متنِ تفسیری را ثابت نمی‌کند و مجوزِ OpenITI/Altafsir نیز احراز نشده است. "
        "اطلاعاتِ چاپ یا صفحهٔ احرازنشده درج نشده؛ همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند."
    )
    return {
        "id": COLLECTION_ID,
        "title": "منابعِ تفسیریِ مورد استناد در بستهٔ انعام ۶:۹۱–۱۴۰",
        "status": "mixed-linked-and-summary-only",
        "items": items,
        "comparativeCore": {
            "scope": "انعام ۶:۹۱–۱۴۰؛ دامنه‌هایِ گروهیِ طوسی و فیض در هر آیه آشکار است",
            "sunniSourceIds": sorted(SUNNI),
            "shiaSourceIds": sorted(SHIA),
            "modernSourceIds": [QURANENC, WASIT],
            "note": note,
        },
        "notice": (
            "این بسته پیش‌نویسِ نیازمندِ داوریِ تخصصی است؛ پیوند و خلاصه مجوزِ اقتباس یا بازنشر را احراز نمی‌کند. "
            "شرح‌هایِ گروهی به صفحهٔ چاپی تبدیل نشده‌اند و گزارش‌هایِ روایی و اختلاف‌هایِ کلامی با انتسابِ روشن آمده‌اند."
        ),
    }


def update_registry(registry: dict) -> dict:
    existing_coverage = {
        source["id"]: set(source.get("researchSnapshot", {}).get("coveredBatches", []))
        for source in registry.get("sources", [])
    }
    registry = renderer.update_registry(registry)
    registry["version"] = max(int(registry.get("version", 0)), 9)
    by_id = {source["id"]: source for source in registry["sources"]}
    for source_id in SOURCE_ORDER:
        source = by_id[source_id]
        source["availabilityNote"] = (
            "در بسته‌هایِ پیاپیِ مائده و انعام بررسی شده؛ دامنهٔ هر بسته در کاتالوگ و پروندهٔ منبع ثبت شده است. "
            "این رکورد وضعیتِ دسترسی و حدودِ نسخه را ثبت می‌کند، نه احرازِ حقوقِ اقتباس."
        )
        if source_id in {TUSI, FAYD}:
            snapshot = source.get("researchSnapshot", {})
            covered = existing_coverage.get(source_id, set()) | set(snapshot.get("coveredBatches", [])) | {"dossier-58", "dossier-59", BATCH_ID}
            snapshot["coveredBatches"] = sorted(covered, key=lambda value: int(value.split("-")[1]))
            snapshot["edition"] = "not identified"
            snapshot["pagination"] = "not specified"
            snapshot["licenseStatus"] = "unresolved"
            source["researchSnapshot"] = snapshot
        elif source_id in {TABARI, IBN, QURTUBI, WASIT}:
            source["archiveSnapshot"] = source_builder.QURAN_EBOOK_ARCHIVES[source_id]
            source["licenseStatus"] = "review-needed"
    return registry


def source_snapshot_metadata() -> dict:
    snapshot = renderer.source_snapshot_metadata()
    snapshot["batchId"] = BATCH_ID
    snapshot["range"] = "6:91–140"
    snapshot["scopeNotes"] = {
        "tusi": "OpenITI markers: direct ayas 6:91–125 and 6:128–140; grouped passage 6:126–127.",
        "fayd": "Grouped scopes: 6:91–93; 94–96; 97–99; 100–103; 104–108; 109–112; 113–119; 120–122; 123–125; 126–127; 128–135; 136–141. The final group extends beyond this batch.",
    }
    snapshot["rawWorkBench"] = {
        "path": "/tmp/anam_6_91_140_sources.json",
        "status": "temporary source extraction, not included in the application; curated paraphrases and source metadata are stored in the builder and data module",
    }
    return snapshot


def update_source_snapshots(dossier: dict) -> None:
    renderer.update_source_snapshots(dossier)
    dossier.setdefault("sourceSnapshots", {})["anam_6_91_140"] = source_snapshot_metadata()


def canonical_notice(dossier: dict | None = None) -> str:
    completed_anam = bool(dossier) and all(f"6:{ayah}" in dossier["verses"] for ayah in range(141, 166))
    completed_araf_1_50 = bool(dossier) and all(f"7:{ayah}" in dossier["verses"] for ayah in range(1, 51))
    if completed_anam and completed_araf_1_50:
        anam_scope = (
            "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است؛ "
            "اعراف بازهٔ ۷:۱–۵۰ را پوشش می‌دهد و ادامهٔ ترتیبیِ همین سوره از ۷:۵۱ است. "
        )
    elif completed_anam:
        anam_scope = "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است؛ گامِ ترتیبیِ بعدی اعراف ۷:۱ است. "
    else:
        anam_scope = "انعام بازهٔ ۶:۱–۱۴۰ را پوشش می‌دهد؛ ادامهٔ انعام، یعنی ۶:۱۴۱ به بعد، هنوز پوشش ندارد. "
    notice = (
        "این پرونده‌ها پیش‌نویس‌هایِ تحریریِ منبع‌محورند؛ بازبینیِ تخصصی انجام نشده است. "
        "بسته‌های مائده ۵:۱–۶، ۵:۷–۱۲، ۵:۱۳–۱۸، ۵:۱۹–۲۴، ۵:۲۵–۳۰، ۵:۳۱–۳۶، ۵:۳۷–۴۲، ۵:۴۳–۴۸، "
        "۵:۴۹–۵۴، ۵:۵۵–۶۰، ۵:۶۱–۱۱۰ و ۵:۱۱۱–۱۲۰ افزوده شده‌اند؛ مائده در این checkout بازهٔ ۵:۱–۱۲۰ را پوشش می‌دهد؛ "
        + anam_scope +
        "نساء در این checkout بازهٔ ۴:۱–۱۷۶ را پوشش می‌دهد؛ پوششِ آیه‌ایِ نساء به معنای تکمیلِ پژوهشِ تفسیری نیست. "
        "بسته‌های یونس بازه‌هایِ ۱۰:۴۹–۶۰، ۱۰:۶۱–۷۲ و ۱۰:۷۳–۸۴ را پوشش می‌دهند؛ برایِ ۱۰:۱–۴۸ پرونده‌ای ساخته نشده است. "
        "خلاصه‌ها نقلِ لفظی نیستند؛ دامنهٔ واقعیِ شرح‌هایِ گروهی و اختلافِ اقوال جدا ثبت شده‌اند. "
        "خلأِ نسخهٔ ناقصِ فیض در ۶:۲۶، نشانِ مستقلِ ۶:۲، گروهِ طنطاوی در ۶:۴–۵ و خلأِ بدنهٔ ابن‌کثیر در ۶:۵۶ آشکار ثبت شده‌اند. "
        "چاپ، صفحه یا اطلاعاتِ نشرِ احرازنشده ساخته نشده و هیچ بندی بازبینیِ تخصصی‌شده معرفی نمی‌شود. "
        "مجوزِ متنِ تفسیریِ آرشیوهایِ Quran.com و OpenITI/Altafsir برایِ اقتباس یا بازنشر در این کار احراز نشده است."
    )
    return renderer._refresh_araf_coverage(notice, dossier)


def update_method(method: str) -> str:
    later_marker = "در بستهٔ انعام ۶:۱۴۱–۱۶۵"
    later_section = method[method.index(later_marker):].strip() if later_marker in method else ""
    if later_marker in method:
        method = method.split(later_marker, 1)[0].rstrip()
    method = renderer.update_method(method)
    marker = "در بستهٔ انعام ۶:۹۱–۱۴۰"
    if marker in method:
        method = method.split(marker, 1)[0].rstrip()
    addition = (
        " در بستهٔ انعام ۶:۹۱–۱۴۰، مدخل‌هایِ آیه‌محورِ طبری، ابن‌کثیر و قرطبی، متنِ محلیِ قرآن‌انک، "
        "مدخل‌هایِ طنطاوی و مواضعِ نشان‌گذاری‌شدهٔ طوسی و فیض در نسخه‌هایِ ناقصِ OpenITI مقابله شدند. "
        "دامنهٔ طوسی برایِ ۶:۱۲۶–۱۲۷ گروهی و دیگر مواضعِ این بسته مستقیم است؛ گروه‌هایِ فیض از ۶:۹۱–۹۳ تا ۶:۱۳۶–۱۴۱ "
        "در هر پرونده روشن‌اند و گروهِ پایانی از محدودهٔ بسته فراتر می‌رود. "
        "گزارش‌هایِ سببِ نزول، قرائت، اختلافِ کلامی و روایت‌هایِ منسوب به امامان جدا از تحلیلِ تحریری ثبت شده‌اند؛ "
        "سه کاربستِ ایزوتسو، فیلمور و معناشناسیِ شناختی مستقل از خلاصه‌هایِ مفسران‌اند. "
        "نسخه‌هایِ آرشیوی ناقص‌اند، خلاصه‌ها نقلِ لفظی نیستند، چاپ و صفحهٔ احرازنشده ساخته نشده و همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند. "
        "مجوزِ متنِ تفسیریِ برگرفته از Quran.com و OpenITI/Altafsir در این کار احراز نشده است."
    )
    result = method.rstrip() + addition
    return result + (" " + later_section if later_section else "")


def update_attribution_doc() -> None:
    renderer.update_attribution_doc()
    if not ATTRIBUTION_PATH.exists():
        return
    text = ATTRIBUTION_PATH.read_text(encoding="utf-8")
    later_marker = "## ۸. منابعِ بررسی‌شده برایِ بستهٔ انعام ۶:۱۴۱–۱۶۵"
    later_section = "\n\n" + text[text.index(later_marker):].strip() if later_marker in text else ""
    marker = "## ۷. منابعِ بررسی‌شده برایِ بستهٔ انعام ۶:۹۱–۱۴۰"
    if marker in text:
        text = text.split(marker, 1)[0].rstrip()
    tusi = source_builder.OPENITI_SNAPSHOTS[TUSI]
    fayd = source_builder.OPENITI_SNAPSHOTS[FAYD]
    addition = f"""

{marker}

برایِ بستهٔ انعام ۶:۹۱–۱۴۰، متنِ خامِ تفسیری در فایل‌هایِ برنامه بازنشر نشده است؛ پرونده‌ها خلاصه‌هایِ تحریریِ منتسب و ارجاع‌هایِ دامنه‌مند دارند. پین‌کردنِ نسخه برایِ بازبینیِ متن است و به‌تنهایی تأییدِ حقِ اقتباس یا بازنشر نیست.

### آرشیوهایِ Quran.com API v4 در `zeeyado/quran-ebook`

- مخزنِ بررسی‌شده: commit `{source_builder.QURAN_EBOOK_COMMIT}`؛ مخزن فایلِ `LICENSE` با متنِ GPL-3.0 دارد. دامنهٔ حقوقیِ آن نسبت به متن‌هایِ تفسیریِ برگرفته از Quran.com و شرایطِ منبعِ اصلی در این کار احراز نشده است.
- طبری: `release/quran_tafsir_tabari_v1.1.zip`، blob `{source_builder.QURAN_EBOOK_ARCHIVES[TABARI]['gitBlobSha']}`, SHA-256 `{source_builder.QURAN_EBOOK_ARCHIVES[TABARI]['sha256']}`.
- ابن‌کثیر: `release/quran_tafsir_ibn_kathir_ar_v1.1.zip`، blob `{source_builder.QURAN_EBOOK_ARCHIVES[IBN]['gitBlobSha']}`, SHA-256 `{source_builder.QURAN_EBOOK_ARCHIVES[IBN]['sha256']}`.
- قرطبی: `release/quran_tafsir_qurtubi_v1.1.zip`، blob `{source_builder.QURAN_EBOOK_ARCHIVES[QURTUBI]['gitBlobSha']}`, SHA-256 `{source_builder.QURAN_EBOOK_ARCHIVES[QURTUBI]['sha256']}`.
- وسيطِ طنطاوی: `release/quran_tafsir_wasit_v1.1.zip`، blob `{source_builder.QURAN_EBOOK_ARCHIVES[WASIT]['gitBlobSha']}`, SHA-256 `{source_builder.QURAN_EBOOK_ARCHIVES[WASIT]['sha256']}`.

### متن‌هایِ OpenITI برایِ طوسی و فیض

- طوسی، *التبيان الجامع لعلوم القرآن*: مخزن `OpenITI/0475AH`، commit `{source_builder.OPENITI_TUSI_COMMIT}`؛ پروندهٔ `{source_builder.TUSI_PATH}`، Git blob `{tusi['gitBlobSha']}`، SHA-256 فایلِ دریافت‌شده `{tusi['fileSha256']}`؛ metadata volume file `{tusi['metadataPath']}`، blob `{tusi['metadataGitBlobSha']}`. در این بازه فقط ۶:۱۲۶–۱۲۷ نشانِ گروهی دارد.
- فیض کاشانی، *الصافي في تفسير كلام الله الوافي*: مخزن `OpenITI/1100AH`، commit `{source_builder.OPENITI_FAYD_COMMIT}`؛ پروندهٔ `{source_builder.FAYD_PATH}`، Git blob `{fayd['gitBlobSha']}`، SHA-256 فایلِ دریافت‌شده `{fayd['fileSha256']}`؛ metadata volume file `{fayd['metadataPath']}`، blob `{fayd['metadataGitBlobSha']}`. گروهِ ۶:۱۳۶–۱۴۱ از انتهایِ این بسته فراتر می‌رود.
- metadataهایِ این دو متن آنها را نسخه‌هایی ناقص و اخذشده از altafsir.com معرفی می‌کنند؛ چاپِ مشخص و صفحهٔ چاپی تعیین نشده است. برایِ متن/میزبان مجوزی در این بررسی احراز نشد؛ وضعیتِ اقتباس و بازنشر نامشخص است.

در فایلِ دادهٔ پژوهشی فقط خلاصه‌هایِ بازنویسی‌شده و نامِ منبع ثبت شده‌اند؛ نسخهٔ خامِ استخراج‌شده در `/tmp/anam_6_91_140_sources.json` موقت بود و در برنامه/مخزن گنجانده نشده است. همهٔ بندها پیش‌نویس‌اند و به داوریِ تخصصی نیاز دارند.
"""
    ATTRIBUTION_PATH.write_text(text.rstrip() + addition + later_section, encoding="utf-8")


def main() -> None:
    registry = update_registry(json.loads(REGISTRY_PATH.read_text(encoding="utf-8")))
    validate_data(registry)
    dossier = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))
    target_keys = set(VERSES)
    present = target_keys & set(dossier["verses"])
    assert len(present) in {0, len(target_keys)}, f"Partial existing batch: {sorted(present)[:5]}"
    assert all(f"6:{ayah}" in dossier["verses"] for ayah in range(1, 91))

    ordered = list(VERSES)
    with renderer_batch_context():
        for index, key in enumerate(ordered):
            previous_key = ordered[index - 1] if index else "6:90"
            next_key = ordered[index + 1] if index + 1 < len(ordered) else "6:141"
            entry = renderer.build_entry(key, curated.DATA[key], previous_key, next_key, dossier)
            renderer.validate_generated_entry(key, entry)
            dossier["verses"][key] = entry

    dossier["batches"] = [batch for batch in dossier["batches"] if batch.get("id") != BATCH_ID]
    dossier["batches"].append({
        "id": BATCH_ID,
        "title": "بستهٔ شصتم: انعام ۶:۹۱–۱۴۰؛ وحی، نشانه‌ها و آدابِ اجتماعی",
        "range": "6:91–140",
        "count": 50,
        "status": (
            "۵۰ پروندهٔ آیه‌محور در ترتیبِ مصحف؛ شش فیلدِ پنج‌بندی، پنج خلاصهٔ کهن و دو شرحِ معاصر در هر آیه، "
            "به‌علاوهٔ سه کاربستِ جداگانهٔ ایزوتسو، فیلمور و معناشناسیِ شناختی. "
            "دامنهٔ گروهیِ طوسی و فیض و اختلاف‌هایِ قرائت، فقه و کلام حفظ شده‌اند؛ متن‌هایِ آرشیوی ناقص و حقوقِ اقتباس/بازنشر احرازنشده‌اند. "
            "همهٔ پرونده‌ها پیش‌نویس و نیازمندِ داوریِ تخصصی‌اند."
        ),
    })
    dossier["batches"].sort(key=lambda item: int(item["id"].split("-")[1]))
    dossier["notice"] = canonical_notice(dossier)
    dossier["editorialMethod"] = update_method(dossier.get("editorialMethod", ""))
    update_source_snapshots(dossier)

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    catalog["collections"] = [item for item in catalog["collections"] if item.get("id") != COLLECTION_ID]
    catalog["collections"].append(build_catalog(registry))
    catalog["version"] = max(int(catalog.get("version", 0)), 38)

    DOSSIER_PATH.write_text(json.dumps(dossier, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_attribution_doc()
    print(f"Added {len(VERSES)} dossiers; total={len(dossier['verses'])}; batch=6:91–140")


if __name__ == "__main__":
    main()
