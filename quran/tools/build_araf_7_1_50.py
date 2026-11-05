#!/usr/bin/env python3
"""Build the first source-linked al-A'raf dossier batch (7:1–50)."""
from __future__ import annotations

import json
import re
from contextlib import contextmanager
from pathlib import Path

import build_anam_6_141_165 as previous_builder
import build_maida_5_111_120_anam_6_1_40 as source_builder
import build_nisa_4_1_12 as shared
import araf_7_1_50_data as curated

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
DOSSIER_PATH = STATIC / "verse-dossiers.json"
CATALOG_PATH = STATIC / "tafsir-catalog.json"
REGISTRY_PATH = STATIC / "tafsir-sources.json"
ATTRIBUTION_PATH = ROOT / "data" / "TAFSIR_ATTRIBUTION.md"
BATCH_ID = "dossier-62"
COLLECTION_ID = "araf-7-1-50-cited"

renderer = previous_builder.renderer
TABARI, IBN, QURTUBI = renderer.TABARI, renderer.IBN, renderer.QURTUBI
TUSI, FAYD = renderer.TUSI, renderer.FAYD
QURANENC, WASIT = renderer.QURANENC, renderer.WASIT
CLASSICAL_ORDER = renderer.CLASSICAL_ORDER
SOURCE_ORDER = renderer.SOURCE_ORDER
SUNNI, SHIA = renderer.SUNNI, renderer.SHIA
MODELS, FIELDS = renderer.MODELS, renderer.FIELDS
VERSES = tuple(curated.DATA)

# OpenITI marker spans are the actual text boundaries, never page references.
TUSI_GROUPS: dict[str, tuple[int, int]] = {}
for start, end in (
    (1, 2), (3, 3), (4, 4), (5, 5), (6, 7), (8, 9), (10, 10),
    (11, 11), (12, 12), (13, 13), (14, 15), (16, 17), (18, 18),
    (19, 19), (20, 20), (21, 21), (22, 22), (23, 23), (24, 24),
    (25, 25), (26, 26), (27, 27), (28, 28), (29, 30), (31, 31),
    (32, 32), (33, 33), (34, 34), (35, 35), (36, 36), (37, 37),
    (38, 38), (39, 39), (40, 40), (41, 41), (42, 42), (43, 43),
    (44, 44), (45, 45), (46, 46), (47, 47), (48, 48), (49, 49), (50, 50),
):
    for ayah in range(start, end + 1):
        TUSI_GROUPS[f"7:{ayah}"] = (start, end)

FAYD_GROUPS: dict[str, tuple[int, int]] = {}
for start, end in (
    (1, 1), (2, 2), (3, 3), (4, 9), (10, 15), (16, 22), (23, 28),
    (29, 31), (32, 32), (33, 33), (34, 38), (39, 44), (45, 46),
    (47, 49), (50, 54),
):
    for ayah in range(max(start, 1), min(end, 50) + 1):
        FAYD_GROUPS[f"7:{ayah}"] = (start, end)

# Quran.com stores one identical Wasit body under both target keys 35 and 36.
WASIT_GROUPS = {"7:35": (35, 36), "7:36": (35, 36)}

SECTIONS = (
    (1, 10, "وحی، هشدار و سنجشِ کردار"),
    (11, 25, "آدم، ابلیس، فریب و بازگشت"),
    (26, 33, "لباس، عبادت و مرزِ تحریم"),
    (34, 41, "اجل، رسالت و فرجامِ تکذیب"),
    (42, 50, "بهشت، دوزخ و گفت‌وگویِ اعراف"),
)


@contextmanager
def renderer_batch_context():
    names = (
        "TUSI_GROUPS", "FAYD_GROUPS", "WASIT_GROUPS", "SECTIONS", "VERSES",
        "verse_ref", "quran", "quran_pair", "source_scope_text", "source_cite",
        "source_evidence", "source_url", "tusi_scope", "fayd_scope",
    )
    missing = object()
    previous = {name: getattr(renderer, name, missing) for name in names}
    prior_surah_names = dict(source_builder.SURAH_NAMES)
    prior_fa_surahs = dict(source_builder.FA_SURAHS)
    source_builder.SURAH_NAMES = {**prior_surah_names, 7: "اعراف"}
    source_builder.FA_SURAHS = {**prior_fa_surahs, 7: "۷"}
    renderer.TUSI_GROUPS = TUSI_GROUPS
    renderer.FAYD_GROUPS = FAYD_GROUPS
    renderer.WASIT_GROUPS = WASIT_GROUPS
    renderer.SECTIONS = SECTIONS
    renderer.VERSES = VERSES
    renderer.verse_ref = verse_ref
    renderer.quran = quran
    renderer.quran_pair = quran_pair
    renderer.source_scope_text = source_scope_text
    renderer.source_cite = source_cite
    renderer.source_evidence = source_evidence
    renderer.source_url = source_url
    renderer.tusi_scope = tusi_scope
    renderer.fayd_scope = fayd_scope
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is missing:
                delattr(renderer, name)
            else:
                setattr(renderer, name, value)
        source_builder.SURAH_NAMES = prior_surah_names
        source_builder.FA_SURAHS = prior_fa_surahs


def fa_num(value: int) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def parse_key(key: str) -> tuple[int, int]:
    surah, ayah = key.split(":", 1)
    return int(surah), int(ayah)


def verse_ref(key: str) -> str:
    surah, ayah = parse_key(key)
    names = {6: ("انعام", "۶"), 7: ("اعراف", "۷")}
    name, fa_surah = names[surah]
    return f"{name} {fa_surah}:{fa_num(ayah)}"


def quran(key: str, end_key: str | None = None) -> str:
    if end_key is None or end_key == key:
        scope = verse_ref(key)
    else:
        start_surah, start_ayah = parse_key(key)
        end_surah, end_ayah = parse_key(end_key)
        if start_surah == end_surah:
            scope = f"{verse_ref(key).rsplit(':', 1)[0]}:{fa_num(start_ayah)}–{fa_num(end_ayah)}"
        else:
            scope = f"{verse_ref(key)} و {verse_ref(end_key)}"
    return f"قرآن، {scope}؛ متنِ عربی و ترجمهٔ فولادوند/Tanzil در پیکرهٔ برنامه."


def quran_pair(first: str, second: str | None) -> str:
    if second is None:
        return quran(first)
    first_surah, first_ayah = parse_key(first)
    second_surah, second_ayah = parse_key(second)
    if first_surah == second_surah and second_ayah == first_ayah + 1:
        return quran(first, second)
    return quran(first) + "؛ " + quran(second)


def scope_range(source_id: str, key: str) -> tuple[int, int]:
    if source_id == TUSI:
        return TUSI_GROUPS[key]
    if source_id == FAYD:
        return FAYD_GROUPS[key]
    if source_id == WASIT and key in WASIT_GROUPS:
        return WASIT_GROUPS[key]
    ayah = parse_key(key)[1]
    return ayah, ayah


def source_scope_text(source_id: str, key: str) -> str:
    start, end = scope_range(source_id, key)
    if start == end:
        return verse_ref(f"7:{start}")
    return f"اعراف ۷:{fa_num(start)}–{fa_num(end)}"


def tusi_scope(key: str) -> str:
    return source_scope_text(TUSI, key)


def fayd_scope(key: str) -> str:
    return source_scope_text(FAYD, key)


def source_url(source_id: str, key: str) -> str:
    if source_id == WASIT and key in WASIT_GROUPS:
        start, _ = WASIT_GROUPS[key]
        return source_builder.qurancom_url(source_id, key, route_ayah=start)
    return source_builder.source_url(source_id, key)


def source_cite(source_id: str, key: str) -> str:
    if source_id in source_builder.QURANCOM_SLUGS:
        titles = {
            TABARI: "طبری، ۳۱۰ق، *جامع البيان عن تأويل آي القرآن*",
            IBN: "ابن‌کثیر، ۷۷۴ق، *تفسير القرآن العظيم*",
            QURTUBI: "قرطبی، ۶۷۱ق، *الجامع لأحكام القرآن*",
            WASIT: "محمد سید طنطاوی، *التفسير الوسيط للقرآن الكريم*",
        }
        start, end = scope_range(source_id, key)
        grouped = start != end
        scope = source_scope_text(source_id, key)
        group_note = "؛ عنوانِ مدخلِ آرشیوی «Al-A'raf 35–36» است و همان بدنه برایِ هر دو آیه ذخیره شده" if source_id == WASIT and grouped else ""
        return (
            f"{titles[source_id]}، ذیلِ {scope}؛ Quran.com API v4، متنِ آرشیویِ نسخهٔ 1.1 "
            f"از zeeyado/quran-ebook، commit {source_builder.QURAN_EBOOK_COMMIT}؛ "
            f"چاپ و صفحهٔ متنِ تفسیری احراز نشده{group_note}."
        )
    if source_id == TUSI:
        start, end = TUSI_GROUPS[key]
        kind = "مستقیم" if start == end else "گروهی"
        snapshot = source_builder.OPENITI_SNAPSHOTS[TUSI]
        return (
            f"طوسی، *التبيان الجامع لعلوم القرآن*، شرحِ {kind} {tusi_scope(key)}؛ "
            f"OpenITI/0475AH، commit {source_builder.OPENITI_TUSI_COMMIT}، پروندهٔ `{source_builder.TUSI_PATH}`، "
            f"metadata volume file `{snapshot['metadataPath']}`؛ نسخهٔ ناقصِ برگرفته از altafsir.com؛ چاپ و صفحه احراز نشده."
        )
    if source_id == FAYD:
        start, end = FAYD_GROUPS[key]
        kind = "مستقیم" if start == end else "گروهی"
        snapshot = source_builder.OPENITI_SNAPSHOTS[FAYD]
        return (
            f"فیض کاشانی، *الصافي في تفسير كلام الله الوافي*، شرحِ {kind} {fayd_scope(key)}؛ "
            f"OpenITI/1100AH، commit {source_builder.OPENITI_FAYD_COMMIT}، پروندهٔ `{source_builder.FAYD_PATH}`، "
            f"metadata volume file `{snapshot['metadataPath']}`؛ نسخهٔ ناقصِ برگرفته از altafsir.com؛ چاپ و صفحه احراز نشده."
        )
    if source_id == QURANENC:
        return f"التفسير الميسر، قرآن‌انک، نسخهٔ 1.0.0، ذیلِ {verse_ref(key)}؛ متنِ محلیِ آیه‌به‌آیه."
    raise KeyError(source_id)


def source_evidence(source_id: str, key: str) -> str:
    if source_id == QURTUBI and key == "7:36":
        return (
            "شاهدِ پوشش: بدنهٔ آرشیوشدهٔ قرطبی زیرِ اعراف ۷:۳۶ صریحاً «لا يوجد تفسير لهذه الأية» دارد؛ "
            "این خلأ فقط به متنِ ذخیره‌شده اشاره می‌کند، نه کلِ اثر."
        )
    if source_id in {TABARI, IBN, QURTUBI}:
        return (
            f"شاهدِ منبع: مدخلِ عربیِ آیه‌محورِ {verse_ref(key)} در آرشیوِ نسخهٔ 1.1 بررسی شد؛ "
            "خلاصه فقط به بدنهٔ همان مدخل محدود است و چاپ/صفحه از آرشیو احراز نشده."
        )
    if source_id == WASIT:
        start, end = scope_range(source_id, key)
        if start != end:
            return (
                "شاهدِ منبع: مدخلِ طنطاوی با عنوانِ «Al-A'raf 35–36» برایِ دو کلیدِ ۷:۳۵ و ۷:۳۶ "
                "یک بدنهٔ یکسان دارد؛ این ارجاع گروهی است، نه دو شرحِ مستقل."
            )
        return f"شاهدِ منبع: مدخلِ عربیِ طنطاوی برایِ {verse_ref(key)} بررسی شد؛ چاپ و صفحهٔ متنِ تفسیری احراز نشده است."
    if source_id in {TUSI, FAYD}:
        start, end = scope_range(source_id, key)
        scope = source_scope_text(source_id, key)
        note = "متنِ هدف در دامنهٔ گروهی بررسی شد." if start != end else "موضعِ آیه در متنِ ناقص بررسی شد."
        return f"شاهدِ OpenITI: دامنهٔ واقعیِ متن {scope} است؛ {note} metadata چاپ و شمارهٔ صفحه را مشخص نمی‌کند."
    if source_id == QURANENC:
        return f"شاهدِ محلی: متنِ نسخهٔ 1.0.0 قرآن‌انک برایِ {verse_ref(key)} بررسی شد؛ خلاصه نقلِ لفظی نیست."
    raise KeyError(source_id)


def source_item(source_id: str, key: str, text: str) -> dict:
    return renderer.source_item(source_id, key, text)


def context_items(key: str, record: dict, previous_key: str, next_key: str | None, dossier: dict) -> list[dict]:
    previous_title = dossier["verses"][previous_key]["title"]
    next_title = dossier["verses"][next_key]["title"] if next_key and next_key in dossier["verses"] else "ادامهٔ سوره پس از این بسته"
    start, end, section_title = section_for(key)
    tusi_start, tusi_end = TUSI_GROUPS[key]
    fayd_start, fayd_end = FAYD_GROUPS[key]
    tusi_kind = "مستقیم" if tusi_start == tusi_end else "گروهی"
    fayd_kind = "مستقیم" if fayd_start == fayd_end else "گروهی"
    scope_detail = (
        f"طوسی شرحِ {tusi_kind} {tusi_scope(key)} و فیض شرحِ {fayd_kind} {fayd_scope(key)} دارد؛ "
        "این مرزها دامنهٔ متن را نشان می‌دهند، نه صفحهٔ چاپی یا شرحِ مستقلِ هر آیه."
    )
    focus = record["notes"][0][0]
    texts = [
        (
            f"در ترتیبِ مصحف، {verse_ref(previous_key)} با عنوانِ «{previous_title}» پیش ازِ {verse_ref(key)} می‌آید؛ "
            f"پروندهٔ حاضر «{record['title']}» را پی می‌گیرد و این پیوندِ ترتیبی، سببِ نزول نیست."
        ),
        (
            f"لنگرِ سیاقیِ {verse_ref(key)} «{record['title']}» است؛ «{focus}» باید کنارِ عبارتِ عربی خوانده شود، "
            "نه به‌جایِ آن یا به‌جایِ داوریِ تخصصی."
        ),
        (
            f"پس ازِ {verse_ref(key)}، {verse_ref(next_key)} با محورِ «{next_title}» می‌آید؛ "
            "این گذارِ نزدیک برایِ مقایسه است و وحدتِ سببِ نزول را به‌تنهایی ثابت نمی‌کند."
        ),
        (
            f"{verse_ref(key)} در بخشِ تحریریِ «{section_title}»، یعنی اعراف ۷:{fa_num(start)}–{fa_num(end)} قرار دارد؛ "
            "این عنوانْ دسته‌بندیِ پژوهشیِ امروز است، نه سرعنوانِ نسخهٔ کهن."
        ),
        (
            f"برایِ دامنهٔ ارجاعِ {verse_ref(key)}، عنوانِ «{record['title']}» را با متن بسنجید: {scope_detail}"
        ),
    ]
    cites = [
        quran_pair(previous_key, key),
        quran(key) + "؛ مقابله با " + source_cite(TABARI, key),
        quran_pair(key, next_key),
        quran(f"7:{start}", f"7:{end}"),
        source_cite(TUSI, key) + "؛ مقابله با " + source_cite(FAYD, key),
    ]
    return [
        renderer.editorial_item(
            text, cite, key, "context",
            evidence=f"شاهدِ متنی: {quran(key)}؛ پیوندِ درون‌سوره‌ای تحلیلِ تحریری است و دامنهٔ منابع در ارجاع آمده است.",
        )
        for text, cite in zip(texts, cites)
    ]


def section_for(key: str) -> tuple[int, int, str]:
    _, ayah = parse_key(key)
    for start, end, title in SECTIONS:
        if start <= ayah <= end:
            return start, end, title
    raise KeyError(key)


def build_entry(key: str, record: dict, previous_key: str, next_key: str, dossier: dict) -> dict:
    entry = {"title": record["title"]}
    entry["notes"] = [renderer.custom_item(item, key, "notes") for item in record["notes"]]
    entry["context"] = context_items(key, record, previous_key, next_key, dossier)
    entry["classical"] = [
        renderer.source_item(source_id, key, record["classical"][source_id])
        for source_id in CLASSICAL_ORDER
    ]
    entry["modern"] = [
        renderer.source_item(source_id, key, record["modern_sources"][source_id])
        for source_id in (QURANENC, WASIT)
    ]
    entry["modern"].extend(renderer.model_items(key, record))
    entry["critical"] = [
        renderer.custom_item(item, key, "critical")
        for item in renderer.critical_points(key, record["critical"])
    ]
    entry["research"] = [renderer.custom_item(item, key, "research") for item in record["research"]]
    entry["status"] = shared.STATUS
    entry["standard"] = 2
    if key == "7:36":
        for item in entry["classical"]:
            if item.get("sourceId") == QURTUBI:
                item["kind"] = "source-coverage-note"
                item["limit"] = (
                    "این کارت خلأِ صریحِ بدنهٔ آرشیوشده را ثبت می‌کند، نه تفسیر؛ نبودِ متن در این فایل، "
                    "نبودِ شرح در کلِ اثر یا نسخه‌هایِ دیگر را ثابت نمی‌کند."
                )
    return entry


def validate_data(registry: dict | None = None) -> None:
    expected = tuple(f"7:{ayah}" for ayah in range(1, 51))
    assert VERSES == expected, (len(VERSES), VERSES[:2], VERSES[-2:])
    assert set(curated.DATA) == set(expected)
    assert set(TUSI_GROUPS) == set(expected)
    assert set(FAYD_GROUPS) == set(expected)
    assert TUSI_GROUPS["7:1"] == TUSI_GROUPS["7:2"] == (1, 2)
    assert TUSI_GROUPS["7:6"] == TUSI_GROUPS["7:7"] == (6, 7)
    assert TUSI_GROUPS["7:8"] == TUSI_GROUPS["7:9"] == (8, 9)
    assert TUSI_GROUPS["7:14"] == TUSI_GROUPS["7:15"] == (14, 15)
    assert TUSI_GROUPS["7:16"] == TUSI_GROUPS["7:17"] == (16, 17)
    assert TUSI_GROUPS["7:29"] == TUSI_GROUPS["7:30"] == (29, 30)
    assert all(TUSI_GROUPS[f"7:{ayah}"] == (ayah, ayah) for ayah in range(1, 51) if ayah not in {1, 2, 6, 7, 8, 9, 14, 15, 16, 17, 29, 30})
    expected_fayd = (
        (1, 1), (2, 2), (3, 3), (4, 9), (10, 15), (16, 22), (23, 28),
        (29, 31), (32, 32), (33, 33), (34, 38), (39, 44), (45, 46),
        (47, 49), (50, 54),
    )
    for start, end in expected_fayd:
        for ayah in range(max(start, 1), min(end, 50) + 1):
            assert FAYD_GROUPS[f"7:{ayah}"] == (start, end)
    assert WASIT_GROUPS == {"7:35": (35, 36), "7:36": (35, 36)}
    for key, record in curated.DATA.items():
        assert len(record["notes"]) == len(record["critical"]) == len(record["research"]) == 5, key
        assert set(record["classical"]) == set(CLASSICAL_ORDER), key
        assert set(record["modern_sources"]) == {QURANENC, WASIT}, key
        assert len(record["model_terms"]) == 3 and all(record["model_terms"]), key
        for field in ("notes", "critical", "research"):
            for text, source_ids in record[field]:
                assert text.strip() and source_ids and set(source_ids) <= set(SOURCE_ORDER), (key, field, source_ids)
                assert len(renderer.expand_item_text(text, key, field, source_ids).split()) >= 14, (key, field, text)
        for source_id, text in record["classical"].items():
            assert text.strip() and len(text.split()) >= 14, (key, source_id, text)
        for source_id, text in record["modern_sources"].items():
            assert text.strip() and len(text.split()) >= 14, (key, source_id, text)
    assert "لا يوجد تفسير لهذه الأية" in curated.DATA["7:36"]["classical"][QURTUBI]
    if registry:
        assert {source["id"] for source in registry["sources"]} >= set(SOURCE_ORDER)


def build_catalog(registry: dict) -> dict:
    by_id = {source["id"]: source for source in registry["sources"]}
    urls_by_source = {source_id: [] for source_id in SOURCE_ORDER}
    for key in VERSES:
        for source_id in SOURCE_ORDER:
            urls_by_source[source_id].append(source_url(source_id, key))
    archives = source_builder.QURAN_EBOOK_ARCHIVES
    bases = {
        TABARI: "مدخل‌هایِ آیه‌محورِ طبری برایِ اعراف ۷:۱–۵۰ در آرشیوِ Quran.com API v4 نسخهٔ 1.1 بررسی شدند؛ اقوال و ترجیح‌ها به خودِ مفسر منسوب‌اند.",
        IBN: "مدخل‌هایِ آیه‌محورِ ابن‌کثیر برایِ اعراف ۷:۱–۵۰ بررسی شدند؛ گزارش‌هایِ روایی و اختلاف‌هایِ نقل‌شده جدا ثبت شده‌اند.",
        QURTUBI: "مدخل‌هایِ آیه‌محورِ قرطبی بررسی شدند؛ بدنهٔ ذخیره‌شده برایِ ۷:۳۶ صریحاً فاقدِ تفسیر است و این خلأ به کلِ اثر تعمیم داده نمی‌شود.",
        TUSI: "متنِ ناقصِ *التبيان* از OpenITI بررسی شد؛ گروه‌هایِ نشان‌دار از ۷:۱–۲ تا ۷:۲۹–۳۰ حفظ شده و دیگر مواضعِ بازه مستقیم‌اند.",
        FAYD: "متنِ ناقصِ *الصافي* از OpenITI بررسی شد؛ دامنه‌هایِ گروهیِ ۷:۴–۹ تا ۷:۵۰–۵۴ در هر پرونده آشکارند و چاپ/صفحه احراز نشده است.",
        QURANENC: "متنِ محلیِ آیه‌به‌آیهٔ قرآن‌انک، نسخهٔ 1.0.0، برایِ تمامِ ۵۰ آیه بررسی شد؛ خلاصه‌ها نقلِ لفظی نیستند.",
        WASIT: "مدخل‌هایِ طنطاوی از آرشیوِ Quran.com API v4 بررسی شدند؛ مدخلِ دارایِ عنوانِ ۷:۳۵–۳۶ یک بدنهٔ یکسان برایِ هر دو کلید دارد.",
    }
    scopes = {
        TABARI: "اعراف ۷:۱–۵۰؛ ۵۰ مدخلِ آیه‌محورِ مستقیم در آرشیوِ نسخهٔ 1.1",
        IBN: "اعراف ۷:۱–۵۰؛ ۵۰ مدخلِ آیه‌محورِ مستقیم در آرشیوِ نسخهٔ 1.1",
        QURTUBI: "اعراف ۷:۱–۵۰؛ مدخل‌ها آیه‌محورند؛ بدنهٔ ذخیره‌شدهٔ ۷:۳۶ صریحاً می‌گوید «لا يوجد تفسير لهذه الأية»",
        TUSI: "گروهی: ۷:۱–۲، ۶–۷، ۸–۹، ۱۴–۱۵، ۱۶–۱۷ و ۲۹–۳۰؛ دیگر مواضعِ ۷:۱–۵۰ مستقیم؛ متنِ ناقصِ OpenITI",
        FAYD: "مواضعِ نشان‌دار: ۷:۱، ۲، ۳، ۴–۹، ۱۰–۱۵، ۱۶–۲۲، ۲۳–۲۸، ۲۹–۳۱، ۳۲، ۳۳، ۳۴–۳۸، ۳۹–۴۴، ۴۵–۴۶، ۴۷–۴۹ و ۵۰–۵۴؛ گروهِ پایانی از بازهٔ بسته فراتر می‌رود.",
        QURANENC: "اعراف ۷:۱–۵۰؛ متنِ محلیِ آیه‌به‌آیه، نسخهٔ 1.0.0",
        WASIT: "اعراف ۷:۱–۵۰؛ مدخلِ ۷:۳۵–۳۶ در هر دو کلید یک بدنهٔ گروهیِ یکسان دارد.",
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
            "version": source.get("version", "نشان‌هایِ مستقیم/گروهی؛ چاپ و صفحهٔ کتاب احراز نشده"),
            "tradition": source.get("tradition") or shared.SOURCE_TRADITIONS.get(source_id, "اهل‌سنت"),
            "licenseStatus": source.get("licenseStatus", "review-needed"),
        })

    note = (
        "در هر یک از ۵۰ پرونده، شش فیلدِ پژوهشیِ notes/context/classical/modern/critical/research پنج‌بندی‌اند؛ "
        "پنج شرحِ کهن، دو شرحِ معاصر و سه کاربستِ ایزوتسو، فیلمور و معناشناسیِ شناختی جدا ثبت شده‌اند. "
        "شرح‌هایِ طوسی و فیض با دامنهٔ واقعیِ نشان‌هایِ OpenITI ارجاع دارند؛ طنطاوی در ۷:۳۵–۳۶ یک مدخلِ گروهی دارد. "
        "بدنهٔ قرطبی زیرِ ۷:۳۶ عبارتِ «لا يوجد تفسير لهذه الأية» دارد؛ این خلأ به کلِ اثر تعمیم داده نشده است. "
        "خلاصه‌ها بازنویسی‌اند، نه نقلِ لفظی؛ اختلافِ اقوال، روایت‌هایِ منسوب و تحلیلِ تحریری از هم جدا مانده‌اند. "
        "نسخه‌هایِ آرشیوی/OpenITI ناقص‌اند، چاپ یا صفحهٔ احرازنشده ساخته نشده و حقوقِ اقتباس/بازنشر حل نشده است؛ همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند."
    )
    return {
        "id": COLLECTION_ID,
        "title": "منابعِ تفسیریِ مورد استناد در بستهٔ اعراف ۷:۱–۵۰",
        "status": "mixed-linked-and-summary-only",
        "items": items,
        "comparativeCore": {
            "scope": "اعراف ۷:۱–۵۰؛ آغازِ سوره تا درخواستِ آب و روزی در گفت‌وگویِ بهشت و دوزخ",
            "sunniSourceIds": sorted(SUNNI),
            "shiaSourceIds": sorted(SHIA),
            "modernSourceIds": [QURANENC, WASIT],
            "note": note,
        },
        "notice": (
            "این بسته پیش‌نویسِ نیازمندِ داوریِ تخصصی است؛ خلاصه‌ها نقلِ لفظی نیستند و پیوند یا پینِ نسخه مجوزِ اقتباس را احراز نمی‌کند. "
            "بدنهٔ قرطبی برایِ ۷:۳۶ صریحاً فاقدِ شرح است و در مدخلِ طنطاوی ۷:۳۵–۳۶ یک دامنهٔ گروهی ثبت شده است."
        ),
    }


def update_registry(registry: dict) -> dict:
    original_version = int(registry.get("version", 0))
    existing_coverage = {
        source["id"]: set(source.get("researchSnapshot", {}).get("coveredBatches", []))
        for source in registry.get("sources", [])
    }
    later_araf_coverage = original_version >= 12 or any(
        "dossier-63" in covered for covered in existing_coverage.values()
    )
    registry = previous_builder.update_registry(registry)
    registry["version"] = max(int(registry.get("version", 0)), original_version, 11)
    by_id = {source["id"]: source for source in registry["sources"]}
    for source_id in SOURCE_ORDER:
        source = by_id[source_id]
        scope_note = "اعراف ۷:۱–۱۰۰" if later_araf_coverage else "اعراف ۷:۱–۵۰"
        source["availabilityNote"] = (
            f"در بستهٔ {scope_note} با دامنهٔ واقعیِ مدخل یا نشان بررسی شده؛ "
            "این ثبتِ دسترسی و حدودِ متن است، نه احرازِ حقوقِ اقتباس."
        )
        if source_id in {TUSI, FAYD}:
            snapshot = source.get("researchSnapshot", {})
            covered = existing_coverage.get(source_id, set()) | set(snapshot.get("coveredBatches", [])) | {BATCH_ID}
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
    snapshot["range"] = "7:1–50"
    snapshot["scopeNotes"] = {
        "qurancom": "All 50 target keys are present in the pinned Tabari, Ibn Kathir, and Qurtubi v1.1 archives; the Qurtubi body at key 7:36 explicitly says no tafsir is present in that archived entry.",
        "wasit": "All target keys are present. The archive title is Al-A'raf 35–36 and the same body is stored under both keys 7:35 and 7:36; both citations are mapped to the grouped span.",
        "tusi": "OpenITI markers: grouped 7:1–2, 7:6–7, 7:8–9, 7:14–15, 7:16–17, and 7:29–30; all other target verses are direct markers.",
        "fayd": "OpenITI marker spans: 7:1; 7:2; 7:3; 7:4–9; 7:10–15; 7:16–22; 7:23–28; 7:29–31; 7:32; 7:33; 7:34–38; 7:39–44; 7:45–46; 7:47–49; and 7:50–54. The final grouped span crosses the batch boundary.",
        "quranenc": "Local QuranEnc Arabic Muyassar v1.0.0 contains verse-keyed entries for all target ayat 7:1–50.",
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
    dossier.setdefault("sourceSnapshots", {})["araf_7_1_50"] = source_snapshot_metadata()


def canonical_notice(dossier: dict) -> str:
    notice = previous_builder.canonical_notice(dossier)
    verses = dossier.get("verses", {})
    araf_ranges = (
        (206, "اعراف بازهٔ ۷:۱–۲۰۶ را پوشش می‌دهد و سورهٔ اعراف در این پرونده‌ها کامل است."),
        (200, "اعراف بازهٔ ۷:۱–۲۰۰ را پوشش می‌دهد؛ ادامهٔ ترتیبیِ همین سوره از ۷:۲۰۱ است."),
        (150, "اعراف بازهٔ ۷:۱–۱۵۰ را پوشش می‌دهد؛ ادامهٔ ترتیبیِ همین سوره از ۷:۱۵۱ است."),
        (100, "اعراف بازهٔ ۷:۱–۱۰۰ را پوشش می‌دهد؛ ادامهٔ ترتیبیِ همین سوره از ۷:۱۰۱ است."),
        (50, "اعراف بازهٔ ۷:۱–۵۰ را پوشش می‌دهد؛ ادامهٔ ترتیبیِ همین سوره از ۷:۵۱ است."),
    )
    for end, replacement in araf_ranges:
        if all(f"7:{ayah}" in verses for ayah in range(1, end + 1)):
            pattern = r"اعراف بازهٔ ۷:۱–(?:۵۰|۱۰۰|۱۵۰|۲۰۰|۲۰۶) را پوشش می\u200c?دهد[^.]*\."
            notice, count = re.subn(pattern, replacement, notice, count=1)
            if not count:
                notice = notice.replace("گامِ ترتیبیِ بعدی اعراف ۷:۱ است.", replacement)
            return notice
    return notice


def update_method(method: str) -> str:
    later_marker = "در بستهٔ اعراف ۷:۵۱–۱۰۰"
    later_section = method[method.index(later_marker):].strip() if later_marker in method else ""
    method = previous_builder.update_method(method)
    marker = "در بستهٔ اعراف ۷:۱–۵۰"
    if marker in method:
        method = method.split(marker, 1)[0].rstrip()
    addition = (
        " در بستهٔ اعراف ۷:۱–۵۰، مدخل‌هایِ آیه‌محورِ طبری، ابن‌کثیر و قرطبی، متنِ محلیِ قرآن‌انک، "
        "مدخل‌هایِ طنطاوی و نشان‌هایِ واقعیِ طوسی و فیض در نسخه‌هایِ ناقصِ OpenITI مقابله شدند. "
        "دامنه‌هایِ گروهیِ طوسی و فیض در هر پرونده آشکارند؛ طنطاوی در ۷:۳۵–۳۶ یک بدنهٔ مشترک دارد و بدنهٔ قرطبی در ۷:۳۶ صریحاً فاقدِ تفسیر است. "
        "اختلافِ معنایِ حروفِ مقطعه، ترتیبِ آفرینش و صورت‌بخشی، هویتِ اصحابِ اعراف، روایت‌هایِ منسوب و قرائت‌ها با انتسابِ روشن جدا مانده‌اند. "
        "تحلیلِ تحریری آیه‌محور است و از خلاصهٔ مفسر جداست؛ سه کاربستِ ایزوتسو، فیلمور و معناشناسیِ شناختی مستقل باقی مانده‌اند. "
        "اعراف ۷:۱–۵۰ اکنون پوشش دارد؛ ادامهٔ ترتیبیِ بعدی اعراف ۷:۵۱–۱۰۰ است. خلاصه‌ها نقلِ لفظی نیستند، چاپ یا صفحهٔ احرازنشده ساخته نشده و پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند. "
        "مجوزِ متنِ تفسیریِ آرشیوهایِ Quran.com و OpenITI/Altafsir برایِ اقتباس یا بازنشر در این کار احراز نشده است."
    )
    result = method.rstrip() + addition
    return result + (" " + later_section if later_section else "")


def update_attribution_doc() -> None:
    later_marker = "## ۱۰. منابعِ بررسی‌شده برایِ بستهٔ اعراف ۷:۵۱–۱۰۰"
    later_section = ""
    if ATTRIBUTION_PATH.exists():
        current = ATTRIBUTION_PATH.read_text(encoding="utf-8")
        if later_marker in current:
            later_section = "\n\n" + current[current.index(later_marker):].strip()
    previous_builder.update_attribution_doc()
    if not ATTRIBUTION_PATH.exists():
        return
    text = ATTRIBUTION_PATH.read_text(encoding="utf-8")
    marker = "## ۹. منابعِ بررسی‌شده برایِ بستهٔ اعراف ۷:۱–۵۰"
    if marker in text:
        text = text.split(marker, 1)[0].rstrip()
    archives = source_builder.QURAN_EBOOK_ARCHIVES
    tusi = source_builder.OPENITI_SNAPSHOTS[TUSI]
    fayd = source_builder.OPENITI_SNAPSHOTS[FAYD]
    addition = f"""

{marker}

این بسته، اعراف ۷:۱–۵۰، شاملِ ۵۰ پروندهٔ تحریری است. متنِ خامِ تفسیری در برنامه بازنشر نشده؛ خلاصه‌ها به نسخه و دامنهٔ واقعیِ مدخل یا نشان ارجاع دارند. پینِ نسخه برایِ بازبینی است و به‌تنهایی حقِ اقتباس یا بازنشر را ثابت نمی‌کند.

### آرشیوهایِ Quran.com API v4 در `zeeyado/quran-ebook`

- commitِ مخزن: `{source_builder.QURAN_EBOOK_COMMIT}`؛ فایلِ GPL-3.0 مخزن به‌تنهایی حقوقِ متنِ برگرفته از Quran.com یا شرایطِ منبعِ اصلی را احراز نمی‌کند.
- طبری: `release/quran_tafsir_tabari_v1.1.zip`، Git blob `{archives[TABARI]['gitBlobSha']}`، SHA-256 `{archives[TABARI]['sha256']}`؛ ۷:۱–۵۰ در آرشیو مدخل‌هایِ آیه‌محور دارد.
- ابن‌کثیر: `release/quran_tafsir_ibn_kathir_ar_v1.1.zip`، Git blob `{archives[IBN]['gitBlobSha']}`، SHA-256 `{archives[IBN]['sha256']}`؛ ۷:۱–۵۰ در آرشیو مدخل‌هایِ آیه‌محور دارد.
- قرطبی: `release/quran_tafsir_qurtubi_v1.1.zip`، Git blob `{archives[QURTUBI]['gitBlobSha']}`، SHA-256 `{archives[QURTUBI]['sha256']}`؛ بدنهٔ کلیدِ ۷:۳۶ صریحاً `لا يوجد تفسير لهذه الأية` می‌گوید. این خلأِ آرشیوی، نبودِ شرح در کلِ اثر را اثبات نمی‌کند.
- وسيطِ طنطاوی: `release/quran_tafsir_wasit_v1.1.zip`، Git blob `{archives[WASIT]['gitBlobSha']}`، SHA-256 `{archives[WASIT]['sha256']}`؛ عنوانِ مدخلِ ۷:۳۵–۳۶ است و همان بدنه زیرِ هر دو کلید ذخیره شده؛ ارجاع در هر دو پرونده گروهی است.

### متن‌هایِ OpenITI برایِ طوسی و فیض

- طوسی، *التبيان الجامع لعلوم القرآن*: مخزن `OpenITI/0475AH`، commit `{source_builder.OPENITI_TUSI_COMMIT}`؛ پروندهٔ `{source_builder.TUSI_PATH}`، Git blob `{tusi['gitBlobSha']}`، SHA-256 فایلِ دریافت‌شده `{tusi['fileSha256']}`؛ metadata `{tusi['metadataPath']}`، blob `{tusi['metadataGitBlobSha']}`. نشان‌هایِ گروهی در این بازه ۷:۱–۲، ۷:۶–۷، ۷:۸–۹، ۷:۱۴–۱۵، ۷:۱۶–۱۷ و ۷:۲۹–۳۰ است؛ دیگر مواضعِ هدف مستقیم‌اند.
- فیض کاشانی، *الصافي في تفسير كلام الله الوافي*: مخزن `OpenITI/1100AH`؛ پروندهٔ `{source_builder.FAYD_PATH}`، Git blob `{fayd['gitBlobSha']}`، SHA-256 فایلِ دریافت‌شده `{fayd['fileSha256']}`؛ metadata `{fayd['metadataPath']}`، blob `{fayd['metadataGitBlobSha']}`. تاریخِ وفات، چاپ و صفحه در این پرونده حدس زده نشده‌اند.
- دامنه‌هایِ فیض: ۷:۱، ۷:۲، ۷:۳، ۷:۴–۹، ۷:۱۰–۱۵، ۷:۱۶–۲۲، ۷:۲۳–۲۸، ۷:۲۹–۳۱، ۷:۳۲، ۷:۳۳، ۷:۳۴–۳۸، ۷:۳۹–۴۴، ۷:۴۵–۴۶، ۷:۴۷–۴۹ و ۷:۵۰–۵۴؛ گروهِ پایانی از بازهٔ این بسته فراتر می‌رود. metadata متن‌هایِ ناقص و برگرفته از altafsir.com را نشان می‌دهد؛ مجوزِ اقتباس/بازنشر در این کار احراز نشده است.

### منبعِ معاصرِ محلی و استخراجِ موقت

- التفسير الميسر، QuranEnc، نسخهٔ 1.0.0، فایلِ `quran/static/tafsir/arabic-moyassar-quranenc-1.0.0.json`، SHA-256 `b056e4d67ac720235de019d7c4887acc1407e1deb935ec8830cf40e663a029ae`؛ مدخل‌هایِ آیه‌به‌آیهٔ ۷:۱–۵۰ بررسی شدند.
- آرشیوِ کاملِ مخزنِ `zeeyado/quran-ebook` از commit `{source_builder.QURAN_EBOOK_COMMIT}` دریافت شد؛ SHA-256 فایلِ ZIP: `1ab619c4b4c6b71b18db2a4a602bb1b810d17f590bbd150a3460f43bb76bf842`. استخراجِ کاری در `/tmp/araf/sources.json` با SHA-256 `d9e82786be7355349f1d02592e69748bf330f2fad2da0ba8dc28569e4ea3ad66` بود و واردِ مخزن نشده است.

در فایلِ پژوهشی فقط خلاصه‌هایِ بازنویسی‌شده، ارجاع و metadata ذخیره شده‌اند. همهٔ پرونده‌ها پیش‌نویس و نیازمندِ داوریِ تخصصی‌اند.
"""
    ATTRIBUTION_PATH.write_text(text.rstrip() + addition + later_section, encoding="utf-8")


def main() -> None:
    registry = update_registry(json.loads(REGISTRY_PATH.read_text(encoding="utf-8")))
    validate_data(registry)
    dossier = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))
    expected_before = [f"6:{ayah}" for ayah in range(1, 166)]
    assert all(key in dossier["verses"] for key in expected_before)
    target_keys = set(VERSES)
    present = target_keys & set(dossier["verses"])
    assert len(present) in {0, len(target_keys)}, f"Partial existing batch: {sorted(present)[:5]}"

    ordered = list(VERSES)
    context_dossier = json.loads(json.dumps(dossier, ensure_ascii=False))
    for key, record in curated.DATA.items():
        context_dossier["verses"].setdefault(key, {"title": record["title"]})
    context_dossier["verses"].setdefault("7:51", {"title": "لهو و بازی با دین و فراموشیِ دیدار"})

    batch_texts: set[str] = set()
    with renderer_batch_context():
        for index, key in enumerate(ordered):
            previous_key = ordered[index - 1] if index else "6:165"
            next_key = ordered[index + 1] if index + 1 < len(ordered) else "7:51"
            entry = build_entry(key, curated.DATA[key], previous_key, next_key, context_dossier)
            renderer.validate_generated_entry(key, entry)
            for field in FIELDS:
                for item in entry[field]:
                    normalized = " ".join(item["text"].split())
                    assert normalized not in batch_texts, f"Repeated prose across verses: {key}: {normalized}"
                    batch_texts.add(normalized)
            dossier["verses"][key] = entry

        dossier["sourceSnapshots"] = dossier.get("sourceSnapshots", {})
        update_source_snapshots(dossier)

    dossier["batches"] = [batch for batch in dossier["batches"] if batch.get("id") != BATCH_ID]
    dossier["batches"].append({
        "id": BATCH_ID,
        "title": "بستهٔ شصت‌ودوم: اعراف ۷:۱–۵۰؛ وحی، آدم و صحنه‌هایِ فرجام",
        "range": "7:1–50",
        "count": 50,
        "status": (
            "۵۰ پروندهٔ آیه‌محور؛ هر شش فیلد پنج‌بندی‌اند، پنج شرحِ کهن و دو شرحِ معاصر ثبت شده و سه کاربستِ معنایی جداست. "
            "دامنه‌هایِ گروهیِ طوسی و فیض، گروهِ طنطاوی در ۷:۳۵–۳۶ و خلأِ صریحِ بدنهٔ قرطبی در ۷:۳۶ آشکارند. "
            "اختلاف‌ها و نقل‌هایِ روایی به منبعِ خود نسبت دارند؛ نسخه‌ها ناقص، حقوقِ اقتباس/بازنشر احرازنشده و همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند."
        ),
    })
    dossier["batches"].sort(key=lambda item: int(item["id"].split("-")[1]))
    dossier["notice"] = canonical_notice(dossier)
    dossier["editorialMethod"] = update_method(dossier.get("editorialMethod", ""))

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    catalog["collections"] = [item for item in catalog["collections"] if item.get("id") != COLLECTION_ID]
    catalog["collections"].append(build_catalog(registry))
    catalog["version"] = max(int(catalog.get("version", 0)), 40)

    DOSSIER_PATH.write_text(json.dumps(dossier, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_attribution_doc()
    print(f"Added {len(VERSES)} dossiers; total={len(dossier['verses'])}; batch=7:1–50")


if __name__ == "__main__":
    main()
