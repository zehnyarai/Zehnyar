#!/usr/bin/env python3
"""Build the source-linked al-A'raf 7:51–100 dossier batch."""
from __future__ import annotations

import json
import re
from contextlib import contextmanager
from pathlib import Path

import build_araf_7_1_50 as previous_builder
import araf_7_51_100_data as curated

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
DOSSIER_PATH = STATIC / "verse-dossiers.json"
CATALOG_PATH = STATIC / "tafsir-catalog.json"
REGISTRY_PATH = STATIC / "tafsir-sources.json"
ATTRIBUTION_PATH = ROOT / "data" / "TAFSIR_ATTRIBUTION.md"
BATCH_ID = "dossier-63"
COLLECTION_ID = "araf-7-51-100-cited"

renderer = previous_builder.renderer
source_builder = previous_builder.source_builder
shared = previous_builder.shared
TABARI, IBN, QURTUBI = renderer.TABARI, renderer.IBN, renderer.QURTUBI
TUSI, FAYD = renderer.TUSI, renderer.FAYD
QURANENC, WASIT = renderer.QURANENC, renderer.WASIT
CLASSICAL_ORDER = renderer.CLASSICAL_ORDER
SOURCE_ORDER = renderer.SOURCE_ORDER
SUNNI, SHIA = renderer.SUNNI, renderer.SHIA
MODELS, FIELDS = renderer.MODELS, renderer.FIELDS
VERSES = tuple(curated.DATA)

TUSI_GROUPS = {f"7:{ayah}": (ayah, ayah) for ayah in range(51, 101)}
for start, end in ((78, 79), (83, 84), (97, 98)):
    for ayah in range(start, end + 1):
        TUSI_GROUPS[f"7:{ayah}"] = (start, end)

FAYD_GROUPS: dict[str, tuple[int, int]] = {}
for start, end in (
    (50, 54), (55, 58), (59, 65), (66, 72), (73, 79),
    (80, 81), (82, 88), (89, 99), (100, 103),
):
    for ayah in range(max(start, 51), min(end, 100) + 1):
        FAYD_GROUPS[f"7:{ayah}"] = (start, end)

WASIT_GROUPS: dict[str, tuple[int, int]] = {}
SECTIONS = (
    (51, 58, "کتاب، قیامت، دعا و نشانه‌هایِ طبیعت"),
    (59, 72, "دعوتِ نوح و هود و فرجامِ تکذیب"),
    (73, 79, "صالح و ثمود، ناقه و عاقبتِ سرپیچی"),
    (80, 84, "لوط و قومِ پاسخ‌ناپذیر"),
    (85, 93, "شعیب، مدین و اختلافِ دو گروه"),
    (94, 100, "سنتِ آزمونِ امت‌ها و هشدار از غفلت"),
)


def fa_num(value: int) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def source_evidence(source_id: str, key: str) -> str:
    if source_id == QURTUBI and key == "7:76":
        return (
            "شاهدِ پوشش: بدنهٔ آرشیوشدهٔ قرطبی زیرِ اعراف ۷:۷۶ صریحاً «لا يوجد تفسير لهذه الأية» دارد؛ "
            "این خلأ فقط به مدخلِ ذخیره‌شده اشاره می‌کند و نبودِ شرح در کلِ اثر را ثابت نمی‌کند."
        )
    return previous_builder.source_evidence(source_id, key)


@contextmanager
def renderer_batch_context():
    names = (
        "TUSI_GROUPS", "FAYD_GROUPS", "WASIT_GROUPS", "SECTIONS", "VERSES",
        "verse_ref", "quran", "quran_pair", "source_scope_text", "source_cite",
        "source_evidence", "source_url", "tusi_scope", "fayd_scope",
    )
    previous = {name: getattr(previous_builder, name) for name in names}
    previous_builder.TUSI_GROUPS = TUSI_GROUPS
    previous_builder.FAYD_GROUPS = FAYD_GROUPS
    previous_builder.WASIT_GROUPS = WASIT_GROUPS
    previous_builder.SECTIONS = SECTIONS
    previous_builder.VERSES = VERSES
    try:
        with previous_builder.renderer_batch_context():
            renderer.source_evidence = source_evidence
            yield
    finally:
        for name, value in previous.items():
            setattr(previous_builder, name, value)


def validate_data(registry: dict | None = None) -> None:
    expected = tuple(f"7:{ayah}" for ayah in range(51, 101))
    assert VERSES == expected, (len(VERSES), VERSES[:2], VERSES[-2:])
    assert set(curated.DATA) == set(expected)
    assert set(TUSI_GROUPS) == set(expected)
    assert set(FAYD_GROUPS) == set(expected)
    assert TUSI_GROUPS["7:78"] == TUSI_GROUPS["7:79"] == (78, 79)
    assert TUSI_GROUPS["7:83"] == TUSI_GROUPS["7:84"] == (83, 84)
    assert TUSI_GROUPS["7:97"] == TUSI_GROUPS["7:98"] == (97, 98)
    assert all(
        TUSI_GROUPS[f"7:{ayah}"] == (ayah, ayah)
        for ayah in range(51, 101) if ayah not in {78, 79, 83, 84, 97, 98}
    )
    expected_fayd = (
        (50, 54), (55, 58), (59, 65), (66, 72), (73, 79),
        (80, 81), (82, 88), (89, 99), (100, 103),
    )
    for start, end in expected_fayd:
        for ayah in range(max(start, 51), min(end, 100) + 1):
            assert FAYD_GROUPS[f"7:{ayah}"] == (start, end)
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
    assert "لا يوجد تفسير لهذه الأية" in curated.DATA["7:76"]["classical"][QURTUBI]
    if registry:
        assert {source["id"] for source in registry["sources"]} >= set(SOURCE_ORDER)


def validate_generated_entry(key: str, entry: dict) -> None:
    renderer.validate_generated_entry(key, entry)
    by_source = {item.get("sourceId"): item for item in entry["classical"]}
    assert set(by_source) == set(CLASSICAL_ORDER), key
    if key == "7:76":
        assert by_source[QURTUBI]["kind"] == "source-coverage-note"
        assert "نه تفسیر" in by_source[QURTUBI]["limit"]
        assert sum(item["kind"] == "source-summary" for item in entry["classical"]) == 4
    else:
        assert all(item["kind"] == "source-summary" for item in entry["classical"])
    modern_sources = {item.get("sourceId") for item in entry["modern"] if item.get("sourceId")}
    models = {item.get("model") for item in entry["modern"] if item.get("model")}
    assert modern_sources == {QURANENC, WASIT} and models == set(MODELS), key


def build_entry(key: str, record: dict, previous_key: str, next_key: str, dossier: dict) -> dict:
    entry = previous_builder.build_entry(key, record, previous_key, next_key, dossier)
    if key == "7:76":
        qurtubi = next(item for item in entry["classical"] if item.get("sourceId") == QURTUBI)
        qurtubi["kind"] = "source-coverage-note"
        qurtubi["text"] = (
            "بدنهٔ آرشیوشدهٔ قرطبی برایِ اعراف ۷:۷۶ صریحاً عبارتِ «لا يوجد تفسير لهذه الأية» را دارد؛ "
            "این خلأِ نسخهٔ بررسی‌شده است، نه شاهدی بر نبودِ شرح در کلِ اثر."
        )
        qurtubi["evidence"] = source_evidence(QURTUBI, key)
        qurtubi["limit"] = (
            "این کارت یادداشتِ پوشش است، نه تفسیر؛ بدنهٔ غایب در این آرشیو را به کلِ اثر یا نسخه‌هایِ دیگر تعمیم ندهید."
        )
    validate_generated_entry(key, entry)
    return entry


def update_registry(registry: dict) -> dict:
    registry["version"] = max(int(registry.get("version", 0)), 12)
    by_id = {source["id"]: source for source in registry.get("sources", [])}
    assert set(SOURCE_ORDER) <= set(by_id)
    for source_id in SOURCE_ORDER:
        source = by_id[source_id]
        source["availabilityNote"] = (
            "در بسته‌هایِ اعراف ۷:۱–۱۰۰، با دامنهٔ واقعیِ مدخل یا نشان بررسی شده؛ "
            "این ثبتِ دسترسی و حدودِ متن است، نه احرازِ حقوقِ اقتباس."
        )
        if source_id in {TUSI, FAYD}:
            snapshot = source.get("researchSnapshot", {})
            covered = set(snapshot.get("coveredBatches", [])) | {BATCH_ID}
            snapshot["coveredBatches"] = sorted(covered, key=lambda value: int(value.split("-")[1]))
            snapshot["edition"] = "not identified"
            snapshot["pagination"] = "not specified"
            snapshot["licenseStatus"] = "unresolved"
            source["researchSnapshot"] = snapshot
        elif source_id in {TABARI, IBN, QURTUBI, WASIT}:
            source["archiveSnapshot"] = source_builder.QURAN_EBOOK_ARCHIVES[source_id]
            source["licenseStatus"] = "review-needed"
    return registry


def build_catalog(registry: dict) -> dict:
    collection = previous_builder.build_catalog(registry)
    by_id = {item["id"]: item for item in collection["items"]}
    collection["id"] = COLLECTION_ID
    collection["title"] = "منابعِ تفسیریِ مورد استناد در بستهٔ اعراف ۷:۵۱–۱۰۰"
    collection["comparativeCore"]["scope"] = "اعراف ۷:۵۱–۱۰۰؛ از گفت‌وگویِ بهشت و دوزخ تا هشدار به وارثانِ آبادی‌هایِ پیشین"
    tusi_groups = "۷:۷۸–۷۹، ۷:۸۳–۸۴ و ۷:۹۷–۹۸؛ دیگر مواضعِ هدف مستقیم‌اند"
    fayd_groups = "۷:۵۰–۵۴، ۷:۵۵–۵۸، ۷:۵۹–۶۵، ۷:۶۶–۷۲، ۷:۷۳–۷۹، ۷:۸۰–۸۱، ۷:۸۲–۸۸، ۷:۸۹–۹۹ و ۷:۱۰۰–۱۰۳"
    bases = {
        TABARI: "۵۰ مدخلِ مستقیمِ طبری برایِ اعراف ۷:۵۱–۱۰۰ در آرشیوِ نسخهٔ 1.1 بررسی شد؛ اقوال و ترجیح‌ها به خودِ مفسر منسوب‌اند.",
        IBN: "۵۰ مدخلِ مستقیمِ ابن‌کثیر برایِ اعراف ۷:۵۱–۱۰۰ بررسی شد؛ گزارش‌هایِ روایی از متنِ آیه جدا نگه داشته شده‌اند.",
        QURTUBI: "مدخل‌هایِ آیه‌محورِ قرطبی بررسی شد؛ کلیدِ ۷:۷۶ صریحاً فاقدِ تفسیرِ ذخیره‌شده است و به‌صورتِ خلأ، نه قول، ثبت شده است.",
        TUSI: f"متنِ ناقصِ *التبيان* از OpenITI بررسی شد؛ مواضعِ گروهیِ {tusi_groups} و دیگر مواضعِ مستقیم‌اند.",
        FAYD: f"متنِ ناقصِ *الصافي* از OpenITI بررسی شد؛ دامنه‌هایِ گروهیِ {fayd_groups} آشکارند و به صفحهٔ چاپی تبدیل نشده‌اند.",
        QURANENC: "متنِ محلیِ آیه‌به‌آیهٔ قرآن‌انک، نسخهٔ 1.0.0، برایِ تمامِ ۵۰ آیه بررسی شد؛ خلاصه‌ها نقلِ لفظی نیستند.",
        WASIT: "مدخل‌هایِ طنطاوی برایِ کلیدهایِ ۷:۵۱–۱۰۰ آیه‌محورند؛ خلاصه‌ها فقط به متنِ ذخیره‌شدهٔ همان کلیدها محدودند.",
    }
    scopes = {
        TABARI: "اعراف ۷:۵۱–۱۰۰؛ ۵۰ مدخلِ آیه‌محورِ مستقیم در آرشیوِ نسخهٔ 1.1",
        IBN: "اعراف ۷:۵۱–۱۰۰؛ ۵۰ مدخلِ آیه‌محورِ مستقیم در آرشیوِ نسخهٔ 1.1",
        QURTUBI: "اعراف ۷:۵۱–۱۰۰؛ مدخل‌ها آیه‌محورند؛ بدنهٔ ذخیره‌شدهٔ ۷:۷۶ صریحاً «لا يوجد تفسير لهذه الأية» می‌گوید",
        TUSI: f"{tusi_groups}؛ متنِ ناقصِ OpenITI؛ ارجاعِ گروهی صفحهٔ چاپی نیست",
        FAYD: f"مواضعِ نشان‌دار: {fayd_groups}؛ گروهِ ۷:۵۰–۵۴ از آغازِ این بسته و گروهِ ۷:۱۰۰–۱۰۳ از پایانِ آن می‌گذرند",
        QURANENC: "اعراف ۷:۵۱–۱۰۰؛ متنِ محلیِ آیه‌به‌آیه، نسخهٔ 1.0.0",
        WASIT: "اعراف ۷:۵۱–۱۰۰؛ مدخل‌هایِ آرشیویِ آیه‌محور و مستقیم",
    }
    for source_id in SOURCE_ORDER:
        item = by_id[source_id]
        item["basis"] = bases[source_id]
        item["scope"] = scopes[source_id]
        item["version"] = item.get("version") or "مدخل یا نشانِ مستقیم/گروهی؛ چاپ و صفحهٔ کتاب احراز نشده"
    collection["comparativeCore"]["note"] = (
        "در هر یک از ۵۰ پرونده، شش فیلدِ notes/context/classical/modern/critical/research پنج‌بندی‌اند؛ "
        "پنج خوانشِ کهن، دو خلاصهٔ معاصر و سه کاربستِ ایزوتسو، فیلمور و معناشناسیِ شناختی از هم جدا هستند. "
        f"دامنه‌هایِ طوسی و فیض در هر پرونده ثبت شده‌اند: طوسی {tusi_groups}؛ فیض {fayd_groups}. "
        "بدنهٔ قرطبی در ۷:۷۶ صریحاً «لا يوجد تفسير لهذه الأية» دارد؛ این خلأ تنها به نسخهٔ آرشیوشده محدود است. "
        "اختلافِ رجفه و صیحه، قرائت‌ها، گزارش‌هایِ سببِ نزول و روایت‌هایِ منسوب به ناقلِ خود نسبت داده شده‌اند؛ خلاصه‌ها نقلِ لفظی نیستند. "
        "نسخه‌هایِ آرشیوی و OpenITI ناقص‌اند، چاپ یا صفحهٔ احرازنشده ساخته نشده، وضعیتِ حقوقِ اقتباس/بازنشر حل نشده و همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند."
    )
    collection["notice"] = (
        "این بسته پیش‌نویسِ نیازمندِ داوریِ تخصصی است؛ خلاصه‌ها نقلِ لفظی نیستند و پینِ نسخه مجوزِ اقتباس یا بازنشر را احراز نمی‌کند. "
        "بدنهٔ قرطبی برایِ ۷:۷۶ در آرشیو صریحاً فاقدِ تفسیر است و در پرونده یادداشتِ پوشش دارد."
    )
    return collection


def source_snapshot_metadata() -> dict:
    snapshot = previous_builder.source_snapshot_metadata()
    snapshot["batchId"] = BATCH_ID
    snapshot["range"] = "7:51–100"
    snapshot["scopeNotes"] = {
        "qurancom": "All target keys 7:51–100 have ayah-keyed Tabari, Ibn Kathir, and Qurtubi archive entries; the stored Qurtubi body at 7:76 explicitly says no tafsir is present in that entry.",
        "wasit": "All target keys have ayah-keyed Wasit entries; no grouped Wasit range occurs in this target batch.",
        "tusi": "OpenITI markers: grouped 7:78–79, 7:83–84, and 7:97–98; all other target ayas are direct markers.",
        "fayd": "OpenITI spans: 7:50–54; 55–58; 59–65; 66–72; 73–79; 80–81; 82–88; 89–99; and 100–103. The first and last groups cross this batch boundary.",
        "quranenc": "Local QuranEnc Arabic Muyassar v1.0.0 contains verse-keyed entries for all target ayat 7:51–100.",
    }
    snapshot["rawWorkBench"] = {
        "path": "/tmp/araf/sources.json",
        "sha256": "d9e82786be7355349f1d02592e69748bf330f2fad2da0ba8dc28569e4ea3ad66",
        "quranEbookCommit": source_builder.QURAN_EBOOK_COMMIT,
        "quranEbookZipSha256": "1ab619c4b4c6b71b18db2a4a602bb1b810d17f590bbd150a3460f43bb76bf842",
        "status": "temporary source extraction, not included in the application; curated paraphrases and source metadata are stored in the builder and data module",
    }
    snapshot["quranEncSnapshot"] = {
        "sourceId": QURANENC,
        "file": "static/tafsir/arabic-moyassar-quranenc-1.0.0.json",
        "version": "1.0.0",
        "sha256": "b056e4d67ac720235de019d7c4887acc1407e1deb935ec8830cf40e663a029ae",
    }
    return snapshot


def update_source_snapshots(dossier: dict) -> None:
    renderer.update_source_snapshots(dossier)
    dossier.setdefault("sourceSnapshots", {})["araf_7_51_100"] = source_snapshot_metadata()


def canonical_notice(dossier: dict) -> str:
    return previous_builder.canonical_notice(dossier)


def update_method(method: str) -> str:
    later_marker = "در بستهٔ اعراف ۷:۱۰۱–۱۵۰"
    later_section = method[method.index(later_marker):].strip() if later_marker in method else ""
    method = previous_builder.update_method(method)
    marker = "در بستهٔ اعراف ۷:۵۱–۱۰۰"
    if marker in method:
        method = method.split(marker, 1)[0].rstrip()
    addition = (
        " در بستهٔ اعراف ۷:۵۱–۱۰۰، مدخل‌هایِ آیه‌محورِ طبری، ابن‌کثیر و قرطبی، متنِ محلیِ قرآن‌انک، "
        "مدخل‌هایِ طنطاوی و نشان‌هایِ طوسی و فیض در نسخه‌هایِ ناقصِ OpenITI مقابله شدند. "
        "دامنه‌هایِ گروهیِ طوسی در ۷:۷۸–۷۹، ۷:۸۳–۸۴ و ۷:۹۷–۹۸ و گروه‌هایِ فیض از ۷:۵۰–۵۴ تا ۷:۱۰۰–۱۰۳ آشکارند. "
        "بدنهٔ قرطبی در ۷:۷۶ صریحاً فاقدِ تفسیر است و به‌عنوانِ خلأِ نسخه، نه دیدگاه، ثبت شد؛ اختلافِ قرائت، رجفه و صیحه و گزارش‌هایِ منسوب با انتسابِ روشن باقی ماندند. "
        "تحلیلِ تحریریِ آیه‌محور از خلاصهٔ مفسر جداست؛ سه کاربستِ ایزوتسو، فیلمور و معناشناسیِ شناختی مستقل از گزارش‌هایِ منبع‌اند. "
        "اعراف ۷:۱–۱۰۰ اکنون پوشش دارد؛ ادامهٔ ترتیبیِ بعدی اعراف ۷:۱۰۱–۱۵۰ است. خلاصه‌ها نقلِ لفظی نیستند، چاپ یا صفحهٔ احرازنشده ساخته نشده و همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند. "
        "مجوزِ متنِ تفسیریِ آرشیوهایِ Quran.com و OpenITI/Altafsir برایِ اقتباس یا بازنشر در این کار احراز نشده است."
    )
    result = method.rstrip() + addition
    return result + (" " + later_section if later_section else "")


def update_attribution_doc() -> None:
    later_marker = "## ۱۱. منابعِ بررسی‌شده برایِ بستهٔ اعراف ۷:۱۰۱–۱۵۰"
    later_section = ""
    if ATTRIBUTION_PATH.exists():
        current = ATTRIBUTION_PATH.read_text(encoding="utf-8")
        if later_marker in current:
            later_section = "\n\n" + current[current.index(later_marker):].strip()
    previous_builder.update_attribution_doc()
    if not ATTRIBUTION_PATH.exists():
        return
    text = ATTRIBUTION_PATH.read_text(encoding="utf-8")
    marker = "## ۱۰. منابعِ بررسی‌شده برایِ بستهٔ اعراف ۷:۵۱–۱۰۰"
    if marker in text:
        text = text.split(marker, 1)[0].rstrip()
    archives = source_builder.QURAN_EBOOK_ARCHIVES
    tusi = source_builder.OPENITI_SNAPSHOTS[TUSI]
    fayd = source_builder.OPENITI_SNAPSHOTS[FAYD]
    addition = f"""

{marker}

این بسته اعراف ۷:۵۱–۱۰۰ را در ۵۰ پروندهٔ تحریری می‌افزاید. متنِ خامِ تفسیری در برنامه بازنشر نشده؛ خلاصه‌ها به نسخه و دامنهٔ واقعیِ مدخل یا نشان ارجاع دارند. پینِ نسخه برایِ بازبینی است و به‌تنهایی حقِ اقتباس یا بازنشر را ثابت نمی‌کند.

### آرشیوهایِ Quran.com API v4 در `zeeyado/quran-ebook`

- commitِ مخزن: `{source_builder.QURAN_EBOOK_COMMIT}`؛ مخزن فایلِ GPL-3.0 دارد، اما دامنهٔ آن بر متنِ برگرفته از Quran.com و شرایطِ منبعِ اصلی در این بررسی احراز نشده است.
- طبری: `release/quran_tafsir_tabari_v1.1.zip`، Git blob `{archives[TABARI]['gitBlobSha']}`، SHA-256 `{archives[TABARI]['sha256']}`؛ کلیدهایِ ۷:۵۱–۱۰۰ مدخلِ آیه‌محور دارند.
- ابن‌کثیر: `release/quran_tafsir_ibn_kathir_ar_v1.1.zip`، Git blob `{archives[IBN]['gitBlobSha']}`، SHA-256 `{archives[IBN]['sha256']}`؛ کلیدهایِ ۷:۵۱–۱۰۰ مدخلِ آیه‌محور دارند.
- قرطبی: `release/quran_tafsir_qurtubi_v1.1.zip`، Git blob `{archives[QURTUBI]['gitBlobSha']}`، SHA-256 `{archives[QURTUBI]['sha256']}`؛ بدنهٔ کلیدِ ۷:۷۶ صریحاً `لا يوجد تفسير لهذه الأية` می‌گوید. این خلأِ آرشیوی، نبودِ شرح در کلِ اثر را اثبات نمی‌کند.
- وسيطِ طنطاوی: `release/quran_tafsir_wasit_v1.1.zip`، Git blob `{archives[WASIT]['gitBlobSha']}`، SHA-256 `{archives[WASIT]['sha256']}`؛ کلیدهایِ هدفِ ۷:۵۱–۱۰۰ آیه‌محورند.

### متن‌هایِ OpenITI برایِ طوسی و فیض

- طوسی، *التبيان الجامع لعلوم القرآن*: مخزن `OpenITI/0475AH`، commit `{source_builder.OPENITI_TUSI_COMMIT}`؛ پروندهٔ `{source_builder.TUSI_PATH}`، Git blob `{tusi['gitBlobSha']}`، SHA-256 فایلِ دریافت‌شده `{tusi['fileSha256']}`؛ metadata `{tusi['metadataPath']}`، blob `{tusi['metadataGitBlobSha']}`. گروه‌هایِ این بازه ۷:۷۸–۷۹، ۷:۸۳–۸۴ و ۷:۹۷–۹۸ است؛ دیگر مواضعِ هدف مستقیم‌اند.
- فیض کاشانی، *الصافي في تفسير كلام الله الوافي*: مخزن `OpenITI/1100AH`، commit `{source_builder.OPENITI_FAYD_COMMIT}`؛ پروندهٔ `{source_builder.FAYD_PATH}`، Git blob `{fayd['gitBlobSha']}`، SHA-256 فایلِ دریافت‌شده `{fayd['fileSha256']}`؛ metadata `{fayd['metadataPath']}`، blob `{fayd['metadataGitBlobSha']}`. تاریخِ وفات، چاپ و صفحه حدس زده نشده‌اند.
- دامنه‌هایِ نشان‌دارِ فیض: ۷:۵۰–۵۴، ۷:۵۵–۵۸، ۷:۵۹–۶۵، ۷:۶۶–۷۲، ۷:۷۳–۷۹، ۷:۸۰–۸۱، ۷:۸۲–۸۸، ۷:۸۹–۹۹ و ۷:۱۰۰–۱۰۳؛ گروهِ آغازین از پیش از این بسته و گروهِ پایانی از پسِ آن امتداد دارد. metadata نسخهٔ ناقصِ برگرفته از altafsir.com را نشان می‌دهد؛ مجوزِ اقتباس/بازنشر در این کار احراز نشده است.

### منبعِ معاصرِ محلی و استخراجِ موقت

- التفسير الميسر، QuranEnc، نسخهٔ 1.0.0، فایلِ `quran/static/tafsir/arabic-moyassar-quranenc-1.0.0.json`، SHA-256 `b056e4d67ac720235de019d7c4887acc1407e1deb935ec8830cf40e663a029ae`؛ مدخل‌هایِ آیه‌به‌آیهٔ ۷:۵۱–۱۰۰ بررسی شدند.
- استخراجِ کاریِ چهار آرشیو و نشان‌هایِ OpenITI در `/tmp/araf/sources.json` با SHA-256 `d9e82786be7355349f1d02592e69748bf330f2fad2da0ba8dc28569e4ea3ad66` موقت بود و واردِ مخزن نشده است.

در فایلِ پژوهشی فقط خلاصه‌هایِ بازنویسی‌شده، ارجاع و metadata ذخیره شده‌اند. همهٔ پرونده‌ها پیش‌نویس و نیازمندِ داوریِ تخصصی‌اند.
"""
    ATTRIBUTION_PATH.write_text(text.rstrip() + addition + later_section, encoding="utf-8")


def _normalized_texts(entry: dict) -> list[str]:
    return [
        re.sub(r"\s+", " ", item["text"]).strip()
        for field in FIELDS
        for item in entry[field]
    ]


def _existing_texts(dossier: dict, excluded: set[str]) -> set[str]:
    return {
        re.sub(r"\s+", " ", item.get("text", "")).strip()
        for key, entry in dossier["verses"].items() if key not in excluded
        for field in FIELDS for item in entry.get(field, [])
        if item.get("text", "").strip()
    }


def main() -> None:
    registry = update_registry(json.loads(REGISTRY_PATH.read_text(encoding="utf-8")))
    dossier = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))
    assert all(f"7:{ayah}" in dossier["verses"] for ayah in range(1, 51))

    target_keys = set(VERSES)
    present = target_keys & set(dossier["verses"])
    assert len(present) in {0, len(target_keys)}, f"Partial existing batch: {sorted(present)[:5]}"
    context_dossier = json.loads(json.dumps(dossier, ensure_ascii=False))
    for key, record in curated.DATA.items():
        context_dossier["verses"].setdefault(key, {"title": record["title"]})
    context_dossier["verses"].setdefault("7:101", {"title": "گزارشِ شهرهایِ پیشین و پندِ وارثان"})

    with renderer_batch_context():
        validate_data(registry)
        earlier_texts = _existing_texts(dossier, target_keys)
        for index, key in enumerate(VERSES):
            previous_key = VERSES[index - 1] if index else "7:50"
            next_key = VERSES[index + 1] if index + 1 < len(VERSES) else "7:101"
            entry = build_entry(key, curated.DATA[key], previous_key, next_key, context_dossier)
            for text in _normalized_texts(entry):
                assert text not in earlier_texts, f"Repeated prose in another verse/batch: {key}: {text}"
                earlier_texts.add(text)
            dossier["verses"][key] = entry
        update_source_snapshots(dossier)

    dossier["batches"] = [batch for batch in dossier["batches"] if batch.get("id") != BATCH_ID]
    dossier["batches"].append({
        "id": BATCH_ID,
        "title": "بستهٔ شصت‌وسوم: اعراف ۷:۵۱–۱۰۰؛ قصصِ پیامبران و هشدار به وارثان",
        "range": "7:51–100",
        "count": 50,
        "status": (
            "۵۰ پروندهٔ آیه‌محور در ترتیبِ مصحف؛ شش فیلدِ پنج‌بندی، پنج شرحِ کهن و دو شرحِ معاصر ثبت شده و سه کاربستِ معنایی مستقل است. "
            "دامنه‌هایِ گروهیِ طوسی و فیض آشکارند؛ بدنهٔ آرشیوشدهٔ قرطبی در ۷:۷۶ فاقدِ تفسیر است و به‌صورتِ یادداشتِ پوشش ثبت شده. "
            "اختلافِ قرائت و تفسیر و روایت‌هایِ منسوب جدا مانده‌اند؛ نسخه‌هایِ آرشیوی ناقص، حقوقِ اقتباس/بازنشر احرازنشده و همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند."
        ),
    })
    dossier["batches"].sort(key=lambda item: int(item["id"].split("-")[1]))
    dossier["notice"] = canonical_notice(dossier)
    dossier["editorialMethod"] = update_method(dossier.get("editorialMethod", ""))

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    catalog["collections"] = [item for item in catalog["collections"] if item.get("id") != COLLECTION_ID]
    with renderer_batch_context():
        catalog["collections"].append(build_catalog(registry))
    catalog["version"] = max(int(catalog.get("version", 0)), 41)

    DOSSIER_PATH.write_text(json.dumps(dossier, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_attribution_doc()
    print(f"Added {len(VERSES)} dossiers; total={len(dossier['verses'])}; batch=7:51–100")


if __name__ == "__main__":
    main()
