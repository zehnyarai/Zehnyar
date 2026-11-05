#!/usr/bin/env python3
"""Build the closing, source-linked al-An'am 6:141–165 dossier batch."""
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

import build_anam_6_91_140 as previous_builder
import build_maida_5_111_120_anam_6_1_40 as source_builder
import build_nisa_4_1_12 as shared
import anam_6_141_165_data as curated

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
DOSSIER_PATH = STATIC / "verse-dossiers.json"
CATALOG_PATH = STATIC / "tafsir-catalog.json"
REGISTRY_PATH = STATIC / "tafsir-sources.json"
ATTRIBUTION_PATH = ROOT / "data" / "TAFSIR_ATTRIBUTION.md"
BATCH_ID = "dossier-61"
COLLECTION_ID = "anam-6-141-165-cited"

renderer = previous_builder.renderer
TABARI, IBN, QURTUBI = renderer.TABARI, renderer.IBN, renderer.QURTUBI
TUSI, FAYD = renderer.TUSI, renderer.FAYD
QURANENC, WASIT = renderer.QURANENC, renderer.WASIT
CLASSICAL_ORDER = renderer.CLASSICAL_ORDER
SOURCE_ORDER = renderer.SOURCE_ORDER
SUNNI, SHIA = renderer.SUNNI, renderer.SHIA
MODELS, FIELDS = renderer.MODELS, renderer.FIELDS
VERSES = tuple(curated.DATA)

# OpenITI marker spans are source-text boundaries, not printed-page ranges.
TUSI_GROUPS = {f"6:{ayah}": (ayah, ayah) for ayah in range(141, 166)}
TUSI_GROUPS["6:162"] = TUSI_GROUPS["6:163"] = (162, 163)

FAYD_GROUPS: dict[str, tuple[int, int]] = {}
for start, end in (
    (136, 141), (142, 145), (146, 146), (147, 151), (152, 155),
    (156, 158), (159, 160), (161, 164), (165, 165),
):
    for ayah in range(max(start, 141), min(end, 165) + 1):
        FAYD_GROUPS[f"6:{ayah}"] = (start, end)

SECTIONS = (
    (141, 145, "باغ‌ها، دام‌ها و سنجشِ تحریم‌هایِ خوراکی"),
    (146, 150, "محدودیت‌هایِ پیشین، مشیت و مطالبهٔ دلیل"),
    (151, 153, "وصایا، عدالت و راهِ مستقیم"),
    (154, 160, "کتابِ مبارک، رفعِ عذر و پاداش"),
    (161, 165, "توحید، مسئولیتِ فردی و آزمونِ نعمت"),
)


def fayd_marker_note(key: str) -> str:
    if key == "6:150":
        return (
            "در متنِ OpenITI، سرعنوانِ گروه ۶:۱۴۷–۱۵۱ است؛ نشانِ درونیِ (۱۵۱) برایِ دو عبارت تکرار شده و عبارتِ نخستِ «قل هلم شهداءكم» "
            "با متنِ قرآنِ ۶:۱۵۰ منطبق است؛ دامنه با مقابلهٔ عبارت تعیین شد، نه با شمارهٔ تکراری."
        )
    if key == "6:151":
        return (
            "در متنِ OpenITI، سرعنوانِ گروه ۶:۱۴۷–۱۵۱ است؛ نشانِ درونیِ (۱۵۱) دو بار آمده و عبارتِ دومِ «قل تعالوا أتل» "
            "با متنِ قرآنِ ۶:۱۵۱ منطبق است؛ دامنه با مقابلهٔ عبارت تعیین شد، نه با شمارهٔ تکراری."
        )
    return ""


@contextmanager
def renderer_batch_context():
    names = ("TUSI_GROUPS", "FAYD_GROUPS", "SECTIONS", "VERSES", "source_cite", "source_evidence")
    previous = {name: getattr(renderer, name) for name in names}
    original_cite = previous["source_cite"]
    original_evidence = previous["source_evidence"]
    renderer.TUSI_GROUPS = TUSI_GROUPS
    renderer.FAYD_GROUPS = FAYD_GROUPS
    renderer.SECTIONS = SECTIONS
    renderer.VERSES = VERSES

    def source_cite(source_id: str, key: str) -> str:
        cite = original_cite(source_id, key)
        if source_id == FAYD and FAYD_GROUPS[key][0] == FAYD_GROUPS[key][1]:
            cite = cite.replace("شرحِ گروهیِ", "شرحِ مستقیم")
        if source_id == FAYD and key in {"6:150", "6:151"}:
            cite += "؛ " + fayd_marker_note(key)
        return cite

    def source_evidence(source_id: str, key: str) -> str:
        if source_id == FAYD and key in {"6:150", "6:151"}:
            return (
                "شاهدِ OpenITI: دامنهٔ سرعنوانی ۶:۱۴۷–۱۵۱ است؛ نشانِ (۱۵۱) درونِ متن تکرار شده است. "
                + fayd_marker_note(key)
                + " چاپ و صفحه از metadata احراز نشده است."
            )
        return original_evidence(source_id, key)

    renderer.source_cite = source_cite
    renderer.source_evidence = source_evidence
    try:
        yield
    finally:
        for name, value in previous.items():
            setattr(renderer, name, value)


def fa_num(value: int) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def validate_data(registry: dict | None = None) -> None:
    expected = tuple(f"6:{ayah}" for ayah in range(141, 166))
    assert VERSES == expected, (len(VERSES), VERSES[:2], VERSES[-2:])
    assert set(curated.DATA) == set(expected)
    assert set(TUSI_GROUPS) == set(expected)
    assert set(FAYD_GROUPS) == set(expected)
    assert all(TUSI_GROUPS[f"6:{ayah}"] == (ayah, ayah) for ayah in range(141, 166) if ayah not in (162, 163))
    assert TUSI_GROUPS["6:162"] == TUSI_GROUPS["6:163"] == (162, 163)
    assert FAYD_GROUPS["6:141"] == (136, 141)
    assert FAYD_GROUPS["6:142"] == FAYD_GROUPS["6:145"] == (142, 145)
    assert FAYD_GROUPS["6:147"] == FAYD_GROUPS["6:151"] == (147, 151)
    assert FAYD_GROUPS["6:152"] == FAYD_GROUPS["6:155"] == (152, 155)
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
        TABARI: "مدخل‌هایِ آیه‌محورِ طبری در آرشیوِ Quran.com API v4 نسخهٔ 1.1 برایِ انعام ۶:۱۴۱–۱۶۵ بررسی شدند؛ گزارش‌هایِ نقل‌شده به خودِ مفسر منسوب‌اند.",
        IBN: "مدخل‌هایِ آیه‌محورِ ابن‌کثیر برایِ ۲۵ آیهٔ پایانیِ انعام بررسی شدند؛ گزارش‌هایِ روایی و اختلافِ او در خوراک و قیامت جدا ثبت شده‌اند.",
        QURTUBI: "مدخل‌هایِ آیه‌محورِ قرطبی در آرشیوِ نسخهٔ 1.1 بررسی شدند؛ اختلاف‌هایِ فقهی، قرائت و نحو به خودِ اثر نسبت دارند.",
        TUSI: "متنِ ناقصِ *التبيان* از OpenITI بررسی شد؛ ۶:۱۶۲–۱۶۳ نشانِ گروهی دارد و دیگر مواضعِ این بازه مستقیم‌اند.",
        FAYD: "متنِ ناقصِ *الصافي* از OpenITI بررسی شد؛ دامنه‌هایِ نشان‌دار حفظ شده‌اند و دو نشانِ (۱۵۱) در ۶:۱۴۷–۱۵۱ با مقابلهٔ عبارت جدا شدند.",
        QURANENC: "متنِ محلیِ آیه‌به‌آیهٔ قرآن‌انک، نسخهٔ 1.0.0، برایِ تمامِ ۲۵ آیه بررسی شد؛ خلاصه‌ها نقلِ لفظی نیستند.",
        WASIT: "مدخل‌هایِ عربیِ طنطاوی از آرشیوِ Quran.com API v4 نسخهٔ 1.1 برایِ ۲۵ آیه بررسی شدند؛ چاپ و صفحه احراز نشده است.",
    }
    scopes = {
        TABARI: "انعام ۶:۱۴۱–۱۶۵؛ ۲۵ مدخلِ آیه‌محورِ آرشیوِ نسخهٔ 1.1",
        IBN: "انعام ۶:۱۴۱–۱۶۵؛ ۲۵ مدخلِ آیه‌محورِ آرشیوِ نسخهٔ 1.1",
        QURTUBI: "انعام ۶:۱۴۱–۱۶۵؛ ۲۵ مدخلِ آیه‌محورِ آرشیوِ نسخهٔ 1.1",
        TUSI: "مستقیم: ۶:۱۴۱–۱۶۱ و ۶:۱۶۴–۱۶۵؛ گروهی: ۶:۱۶۲–۱۶۳؛ متنِ ناقصِ OpenITI",
        FAYD: "مواضعِ نشان‌دار: ۶:۱۳۶–۱۴۱، ۱۴۲–۱۴۵، ۱۴۶، ۱۴۷–۱۵۱، ۱۵۲–۱۵۵، ۱۵۶–۱۵۸، ۱۵۹–۱۶۰، ۱۶۱–۱۶۴ و ۱۶۵؛ در ۶:۱۴۷–۱۵۱ نشانِ (۱۵۱) تکرار شده و دو عبارت با ۶:۱۵۰ و ۶:۱۵۱ مقابله شده‌اند.",
        QURANENC: "انعام ۶:۱۴۱–۱۶۵؛ متنِ محلیِ آیه‌به‌آیه، نسخهٔ 1.0.0",
        WASIT: "انعام ۶:۱۴۱–۱۶۵؛ مدخل‌هایِ آیه‌محورِ آرشیوِ نسخهٔ 1.1",
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
        "در هر یک از ۲۵ پرونده، شش فیلدِ notes/context/classical/modern/critical/research پنج‌بندی‌اند؛ "
        "پنج شرحِ کهن، دو شرحِ معاصر و سه کاربستِ محدودِ ایزوتسو، فیلمور و معناشناسیِ شناختی جدا مانده‌اند؛ خلاصه‌ها بازنویسی‌اند، نه نقلِ لفظی. "
        "دامنهٔ طوسی مستقیم است جز گروهِ ۶:۱۶۲–۱۶۳؛ دامنه‌هایِ نشان‌دارِ فیض در هر پرونده ثبت شده و نشانِ (۱۵۱) در ۶:۱۴۷–۱۵۱ برایِ دو عبارتِ پیاپی تکرار شده و با لفظِ آیه مقابله شده است. "
        "اختلافِ تفسیرِ «حقّه»، جفت‌هایِ دام، «يأتي ربك»، قرائتِ «فرقوا/فارقوا» و اقوالِ کلامی به منبعِ خود منسوب‌اند. "
        "متن‌هایِ آرشیوی و OpenITI ناقص‌اند؛ GPL-3.0 مخزن به‌تنهایی حقوقِ متنِ تفسیری را احراز نمی‌کند و مجوزِ OpenITI/Altafsir نیز روشن نیست. "
        "چاپ یا صفحهٔ احرازنشده ساخته نشده و همهٔ بندها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند."
    )
    return {
        "id": COLLECTION_ID,
        "title": "منابعِ تفسیریِ مورد استناد در بستهٔ انعام ۶:۱۴۱–۱۶۵",
        "status": "mixed-linked-and-summary-only",
        "items": items,
        "comparativeCore": {
            "scope": "انعام ۶:۱۴۱–۱۶۵؛ بخشِ پایانیِ سوره و دامنه‌هایِ نشان‌دارِ OpenITI",
            "sunniSourceIds": sorted(SUNNI),
            "shiaSourceIds": sorted(SHIA),
            "modernSourceIds": [QURANENC, WASIT],
            "note": note,
        },
        "notice": (
            "این بسته پیش‌نویسِ نیازمندِ داوریِ تخصصی است؛ متن‌هایِ خام بازنشر نشده‌اند و پیوند یا خلاصه مجوزِ اقتباس را احراز نمی‌کند. "
            "انعام ۶:۱۴۱–۱۶۵ پایانِ پوششِ این سوره است؛ بررسیِ سورهٔ بعدی باید از اعراف ۷:۱ آغاز شود."
        ),
    }


def update_registry(registry: dict) -> dict:
    existing_coverage = {
        source["id"]: set(source.get("researchSnapshot", {}).get("coveredBatches", []))
        for source in registry.get("sources", [])
    }
    registry = previous_builder.update_registry(registry)
    registry["version"] = max(int(registry.get("version", 0)), 10)
    by_id = {source["id"]: source for source in registry["sources"]}
    for source_id in SOURCE_ORDER:
        source = by_id[source_id]
        source["availabilityNote"] = (
            "در بسته‌هایِ پیوستهٔ مائده و انعام بررسی شده؛ این رکورد وضعیتِ دسترسی و حدودِ نسخه را ثبت می‌کند، نه احرازِ حقوقِ اقتباس."
        )
        if source_id in {TUSI, FAYD}:
            snapshot = source.get("researchSnapshot", {})
            covered = existing_coverage.get(source_id, set()) | set(snapshot.get("coveredBatches", [])) | {"dossier-58", "dossier-59", "dossier-60", BATCH_ID}
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
    snapshot["range"] = "6:141–165"
    snapshot["scopeNotes"] = {
        "qurancom": "All target keys 6:141–165 are direct Al-An'am entries in the pinned Tabari, Ibn Kathir, Qurtubi, and Wasit v1.1 archives.",
        "tusi": "OpenITI markers: direct 6:141–161 and 6:164–165; grouped passage 6:162–163.",
        "fayd": "OpenITI marker spans: 6:136–141; 142–145; 146; 147–151; 152–155; 156–158; 159–160; 161–164; 165. In the 6:147–151 section, inline marker (151) is duplicated; its two bodies were mapped by their quoted Qur'anic openings to 6:150 and 6:151, not by the repeated number.",
        "quranenc": "Local QuranEnc Arabic Muyassar v1.0.0 contains verse-keyed entries for each target ayah.",
    }
    snapshot["rawWorkBench"] = {
        "path": "/tmp/anam_6_141_165_sources.json",
        "sha256": "8e758f9be83424c2a66110d26a8a0d383aba13547b236aea718fd1e5503919c4",
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
    dossier.setdefault("sourceSnapshots", {})["anam_6_141_165"] = source_snapshot_metadata()


def canonical_notice(dossier: dict) -> str:
    return previous_builder.canonical_notice(dossier)


def update_method(method: str) -> str:
    method = previous_builder.update_method(method)
    marker = "در بستهٔ انعام ۶:۱۴۱–۱۶۵"
    if marker in method:
        method = method.split(marker, 1)[0].rstrip()
    addition = (
        " در بستهٔ انعام ۶:۱۴۱–۱۶۵، مدخل‌هایِ آیه‌محورِ طبری، ابن‌کثیر، قرطبی و طنطاوی، متنِ محلیِ قرآن‌انک و مواضعِ نشان‌گذاری‌شدهٔ طوسی و فیض مقابله شدند. "
        "نشان‌هایِ طوسی در ۶:۱۶۲–۱۶۳ گروهی است؛ دامنه‌هایِ نشان‌دارِ فیض از ۶:۱۳۶–۱۴۱ تا ۶:۱۶۵ در هر پرونده آشکارند و نشانِ (۱۵۱) دوبار آمده است؛ عبارت‌ها جداگانه مقابله شدند. "
        "اختلافِ «حقّه» و زکات، جفت‌هایِ اهلی/وحشی یا نر/ماده، «يأتي ربك»، قرائتِ «فرقوا/فارقوا» و اقوالِ «الحجة البالغة» با انتسابِ روشن باقی مانده‌اند. "
        "گزارش‌هایِ روایی از تحلیلِ تحریری جداست؛ سه کاربستِ ایزوتسو، فیلمور و معناشناسیِ شناختی مستقل از خلاصه‌هایِ مفسران‌اند. "
        "انعام ۶:۱–۱۶۵ اکنون پوشش دارد؛ اعراف ۷:۱–۵۰ افزوده شده و ادامهٔ ترتیبی از اعراف ۷:۵۱ است. خلاصه‌ها نقلِ لفظی نیستند، چاپ و صفحهٔ احرازنشده ساخته نشده و همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند. "
        "مجوزِ متنِ تفسیریِ آرشیوهایِ Quran.com و OpenITI/Altafsir برایِ اقتباس یا بازنشر در این کار احراز نشده است."
    )
    return method.rstrip() + addition


def update_attribution_doc() -> None:
    previous_builder.update_attribution_doc()
    if not ATTRIBUTION_PATH.exists():
        return
    text = ATTRIBUTION_PATH.read_text(encoding="utf-8")
    marker = "## ۸. منابعِ بررسی‌شده برایِ بستهٔ انعام ۶:۱۴۱–۱۶۵"
    if marker in text:
        text = text.split(marker, 1)[0].rstrip()
    archives = source_builder.QURAN_EBOOK_ARCHIVES
    tusi = source_builder.OPENITI_SNAPSHOTS[TUSI]
    fayd = source_builder.OPENITI_SNAPSHOTS[FAYD]
    addition = f"""

{marker}

این بسته، بخشِ پایانیِ انعام ۶:۱۴۱–۱۶۵، شاملِ ۲۵ پروندهٔ تحریری است. متنِ خامِ تفسیری در برنامه بازنشر نشده؛ خلاصه‌ها به نسخه و دامنهٔ واقعیِ متن ارجاع دارند. پینِ نسخه برایِ بازبینی است و به‌تنهایی حقِ اقتباس یا بازنشر را ثابت نمی‌کند.

### آرشیوهایِ Quran.com API v4 در `zeeyado/quran-ebook`

- commitِ مخزن: `{source_builder.QURAN_EBOOK_COMMIT}`؛ مخزن `LICENSE` با GPL-3.0 دارد، اما دامنهٔ آن بر متنِ برگرفته از Quran.com و شرایطِ منبعِ اصلی در این بررسی احراز نشده است.
- طبری: `release/quran_tafsir_tabari_v1.1.zip`، Git blob `{archives[TABARI]['gitBlobSha']}`، SHA-256 `{archives[TABARI]['sha256']}`؛ مدخل‌هایِ ۶:۱۴۱–۱۶۵ مستقیم‌اند.
- ابن‌کثیر: `release/quran_tafsir_ibn_kathir_ar_v1.1.zip`، Git blob `{archives[IBN]['gitBlobSha']}`، SHA-256 `{archives[IBN]['sha256']}`؛ مدخل‌هایِ ۶:۱۴۱–۱۶۵ مستقیم‌اند.
- قرطبی: `release/quran_tafsir_qurtubi_v1.1.zip`، Git blob `{archives[QURTUBI]['gitBlobSha']}`، SHA-256 `{archives[QURTUBI]['sha256']}`؛ مدخل‌هایِ ۶:۱۴۱–۱۶۵ مستقیم‌اند.
- وسيطِ طنطاوی: `release/quran_tafsir_wasit_v1.1.zip`، Git blob `{archives[WASIT]['gitBlobSha']}`، SHA-256 `{archives[WASIT]['sha256']}`؛ مدخل‌هایِ ۶:۱۴۱–۱۶۵ مستقیم‌اند.

### متن‌هایِ OpenITI برایِ طوسی و فیض

- طوسی، *التبيان الجامع لعلوم القرآن*: مخزن `OpenITI/0475AH`، commit `{source_builder.OPENITI_TUSI_COMMIT}`؛ پروندهٔ `{source_builder.TUSI_PATH}`، Git blob `{tusi['gitBlobSha']}`، SHA-256ِ فایلِ دریافت‌شده `{tusi['fileSha256']}`؛ metadata `{tusi['metadataPath']}`، blob `{tusi['metadataGitBlobSha']}`. نشان‌ها در این بازه برایِ ۶:۱۶۲–۱۶۳ گروهی و دیگر مواضع مستقیم‌اند.
- فیض کاشانی، *الصافي في تفسير كلام الله الوافي*: مخزن `OpenITI/1100AH`، commit `{source_builder.OPENITI_FAYD_COMMIT}`؛ پروندهٔ `{source_builder.FAYD_PATH}`، Git blob `{fayd['gitBlobSha']}`، SHA-256ِ فایلِ دریافت‌شده `{fayd['fileSha256']}`؛ metadata `{fayd['metadataPath']}`، blob `{fayd['metadataGitBlobSha']}`.
- دامنه‌هایِ فیض: ۶:۱۳۶–۱۴۱، ۱۴۲–۱۴۵، ۱۴۶، ۱۴۷–۱۵۱، ۱۵۲–۱۵۵، ۱۵۶–۱۵۸، ۱۵۹–۱۶۰، ۱۶۱–۱۶۴ و ۱۶۵. در گروهِ ۶:۱۴۷–۱۵۱، نشانِ درونیِ (۱۵۱) دوبار آمده است: عبارتِ نخست «قل هلم شهداءكم» با ۶:۱۵۰ و عبارتِ دوم «قل تعالوا أتل» با ۶:۱۵۱ منطبق است. ارجاع‌ها با مقابلهٔ خودِ عبارت نگاشت شدند، نه با شمارهٔ تکراری؛ چاپ و صفحه ادعا نشده است.
- metadata متن‌هایِ OpenITI آنها را ناقص و برگرفته از altafsir.com می‌داند؛ چاپ و صفحهٔ مشخص احراز نشده و مجوزِ اقتباس/بازنشر در این کار حل نشده است.

### منبعِ معاصرِ محلی

- التفسير الميسر، QuranEnc، نسخهٔ 1.0.0، فایلِ `quran/static/tafsir/arabic-moyassar-quranenc-1.0.0.json`، SHA-256 `b056e4d67ac720235de019d7c4887acc1407e1deb935ec8830cf40e663a029ae`؛ مدخل‌هایِ آیه‌به‌آیهٔ ۶:۱۴۱–۱۶۵ بررسی شدند. طنطاوی از آرشیوِ نسخهٔ 1.1 بالا استفاده می‌کند؛ مدخل‌ها مستقیم‌اند.

در فایلِ پژوهشی فقط خلاصه‌هایِ بازنویسی‌شده، ارجاع و metadata ذخیره شده‌اند؛ استخراجِ موقت در `/tmp/anam_6_141_165_sources.json` نگهداری شد و واردِ مخزن نشد. همهٔ پرونده‌ها پیش‌نویس و نیازمندِ داوریِ تخصصی‌اند.
"""
    ATTRIBUTION_PATH.write_text(text.rstrip() + addition, encoding="utf-8")


def main() -> None:
    registry = update_registry(json.loads(REGISTRY_PATH.read_text(encoding="utf-8")))
    validate_data(registry)
    dossier = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))
    target_keys = set(VERSES)
    present = target_keys & set(dossier["verses"])
    assert len(present) in {0, len(target_keys)}, f"Partial existing batch: {sorted(present)[:5]}"
    assert all(f"6:{ayah}" in dossier["verses"] for ayah in range(1, 141))

    ordered = list(VERSES)
    context_dossier = json.loads(json.dumps(dossier, ensure_ascii=False))
    for key, record in curated.DATA.items():
        context_dossier["verses"].setdefault(key, {"title": record["title"]})

    batch_texts: set[str] = set()
    with renderer_batch_context():
        for index, key in enumerate(ordered):
            previous_key = ordered[index - 1] if index else "6:140"
            next_key = ordered[index + 1] if index + 1 < len(ordered) else "7:1"
            entry = renderer.build_entry(key, curated.DATA[key], previous_key, next_key, context_dossier)
            if key == "6:165":
                entry["context"][2] = renderer.editorial_item(
                    "انعام با ۶:۱۶۵ پایان می‌یابد و در ترتیبِ مصحف پس از آن اعراف ۷:۱ می‌آید؛ این فقط پیوندِ ترتیبی است، نه تفسیرِ محتوایِ آیهٔ بعد.",
                    "قرآن، انعام ۶:۱۶۵ و اعراف ۷:۱؛ ترتیبِ مصحف و مرزِ پوششِ فعلی.",
                    key,
                    "context",
                    evidence="شاهدِ متنی: قرآن، انعام ۶:۱۶۵ و اعراف ۷:۱؛ پرونده‌هایِ این بسته تا پایانِ انعام پیش می‌روند.",
                )
            else:
                next_title = context_dossier["verses"][next_key]["title"]
                entry["context"][2] = renderer.editorial_item(
                    f"پس ازِ {renderer.verse_ref(key)}، {renderer.verse_ref(next_key)} با محورِ «{next_title}» می‌آید؛ این پیوندِ ترتیبی گذارِ موضوعی را نشان می‌دهد و به‌تنهایی وحدتِ سببِ نزول را ثابت نمی‌کند.",
                    renderer.quran_pair(key, next_key),
                    key,
                    "context",
                    evidence=f"شاهدِ متنی: {renderer.quran_pair(key, next_key)}؛ مقایسهٔ دو آیه تحلیلِ تحریری است، نه سببِ نزول.",
                )
            renderer.validate_generated_entry(key, entry)
            for field in FIELDS:
                for item in entry[field]:
                    normalized = " ".join(item["text"].split())
                    assert normalized not in batch_texts, f"Repeated prose across verses: {key}: {normalized}"
                    batch_texts.add(normalized)
            dossier["verses"][key] = entry

    dossier["batches"] = [batch for batch in dossier["batches"] if batch.get("id") != BATCH_ID]
    dossier["batches"].append({
        "id": BATCH_ID,
        "title": "بستهٔ شصت‌ویکم: انعام ۶:۱۴۱–۱۶۵؛ حقِ محصول، وصایا و مسئولیت",
        "range": "6:141–165",
        "count": 25,
        "status": (
            "۲۵ پروندهٔ آیه‌محور در پایانِ سورهٔ انعام؛ هر شش فیلد پنج‌بندی‌اند، پنج شرحِ کهن و دو شرحِ معاصر ثبت شده و سه کاربستِ معنایی جداست. "
            "دامنه‌هایِ نشان‌دارِ طوسی و فیض و تکرارِ نشانِ (۱۵۱) در نسخهٔ فیض آشکارند؛ اختلاف‌هایِ فقهی و کلامی به منبعِ خود نسبت دارند. "
            "نسخه‌هایِ آرشیوی ناقص و حقوقِ اقتباس/بازنشر احرازنشده‌اند؛ همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند."
        ),
    })
    dossier["batches"].sort(key=lambda item: int(item["id"].split("-")[1]))
    dossier["notice"] = canonical_notice(dossier)
    dossier["editorialMethod"] = update_method(dossier.get("editorialMethod", ""))
    update_source_snapshots(dossier)

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    catalog["collections"] = [item for item in catalog["collections"] if item.get("id") != COLLECTION_ID]
    catalog["collections"].append(build_catalog(registry))
    catalog["version"] = max(int(catalog.get("version", 0)), 39)

    DOSSIER_PATH.write_text(json.dumps(dossier, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_attribution_doc()
    print(f"Added {len(VERSES)} dossiers; total={len(dossier['verses'])}; batch=6:141–165")


if __name__ == "__main__":
    main()
