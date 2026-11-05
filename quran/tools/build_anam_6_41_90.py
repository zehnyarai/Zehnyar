#!/usr/bin/env python3
"""Build source-linked draft dossiers for al-An'am 6:41–90."""
from __future__ import annotations

import json
import re
from pathlib import Path

import build_maida_5_111_120_anam_6_1_40 as prior
import build_nisa_4_1_12 as shared
import anam_6_41_90_data as curated

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
DOSSIER_PATH = STATIC / "verse-dossiers.json"
CATALOG_PATH = STATIC / "tafsir-catalog.json"
REGISTRY_PATH = STATIC / "tafsir-sources.json"
ATTRIBUTION_PATH = ROOT / "data" / "TAFSIR_ATTRIBUTION.md"
BATCH_ID = "dossier-59"
COLLECTION_ID = "anam-6-41-90-cited"

TABARI, IBN, QURTUBI = prior.TABARI, prior.IBN, prior.QURTUBI
TUSI, FAYD = prior.TUSI, prior.FAYD
QURANENC, WASIT = prior.QURANENC, prior.WASIT
CLASSICAL_ORDER = (TABARI, IBN, QURTUBI, TUSI, FAYD)
SOURCE_ORDER = (*CLASSICAL_ORDER, QURANENC, WASIT)
SUNNI = {TABARI, IBN, QURTUBI}
SHIA = {TUSI, FAYD}
MODELS = ("izutsu", "fillmore", "cognitive")
FIELDS = ("notes", "context", "classical", "modern", "critical", "research")
VERSES = tuple(curated.DATA)

# Each pair is the actual OpenITI marker scope, not a printed-page range.
TUSI_GROUPS: dict[str, tuple[int, int]] = {}
for start, end in (
    (40, 41), (42, 43), (44, 45), (46, 46), (47, 47), (48, 49),
    (50, 50), (51, 51), (52, 52), (53, 53), (54, 54), (55, 55),
    (56, 56), (57, 57), (58, 58), (59, 59), (60, 60), (61, 62),
    (63, 63), (64, 64), (65, 65), (66, 67), (68, 68), (69, 69),
    (70, 70), (71, 71), (72, 72), (73, 73), (74, 74), (75, 75),
    (76, 79), (80, 80), (81, 81), (82, 82), (83, 83), (84, 90),
):
    for ayah in range(max(start, 41), min(end, 90) + 1):
        TUSI_GROUPS[f"6:{ayah}"] = (start, end)

FAYD_GROUPS: dict[str, tuple[int, int]] = {}
for start, end in (
    (36, 41), (42, 49), (50, 53), (54, 59), (60, 65),
    (66, 71), (72, 75), (76, 79), (80, 81), (82, 90),
):
    for ayah in range(max(start, 41), min(end, 90) + 1):
        FAYD_GROUPS[f"6:{ayah}"] = (start, end)

IBN_GROUPS = {"6:55": (55, 56), "6:56": (55, 56)}
SECTIONS = (
    (41, 49, "اضطرار، نشانه‌ها و رسالتِ پیام‌آوران"),
    (50, 59, "پیروی از وحی، آیات و علمِ غیب"),
    (60, 70, "خواب، مرگ، بازگشت و مواجهه با تمسخر"),
    (71, 79, "دعوت به هدایت و احتجاجِ ابراهیم"),
    (80, 90, "حجت، امنیت و فهرستِ پیامبران"),
)


def fa_num(value: int) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def parse_key(key: str) -> tuple[int, int]:
    surah, ayah = key.split(":", 1)
    return int(surah), int(ayah)


def verse_ref(key: str) -> str:
    surah, ayah = parse_key(key)
    return f"انعام ۶:{fa_num(ayah)}"


def quran(key: str, end_key: str | None = None) -> str:
    if end_key is None or end_key == key:
        scope = verse_ref(key)
    else:
        start_surah, start_ayah = parse_key(key)
        end_surah, end_ayah = parse_key(end_key)
        assert start_surah == end_surah == 6
        scope = f"انعام ۶:{fa_num(start_ayah)}–{fa_num(end_ayah)}"
    return f"قرآن، {scope}؛ متنِ عربی و ترجمهٔ فولادوند/Tanzil در پیکرهٔ برنامه."


def quran_pair(first: str, second: str | None) -> str:
    if second is None:
        return quran(first)
    first_surah, first_ayah = parse_key(first)
    second_surah, second_ayah = parse_key(second)
    if first_surah == second_surah and second_ayah == first_ayah + 1:
        return quran(first, second)
    return quran(first) + "؛ " + quran(second)


def source_url(source_id: str, key: str) -> str:
    if source_id == IBN and key in IBN_GROUPS:
        return prior.qurancom_url(source_id, key, route_ayah=IBN_GROUPS[key][0])
    return prior.source_url(source_id, key)


def tusi_scope(key: str) -> str:
    start, end = TUSI_GROUPS[key]
    if start == end:
        return verse_ref(f"6:{start}")
    return f"انعام ۶:{fa_num(start)}–{fa_num(end)}"


def fayd_scope(key: str) -> str:
    start, end = FAYD_GROUPS[key]
    if start == end:
        return verse_ref(f"6:{start}")
    return f"انعام ۶:{fa_num(start)}–{fa_num(end)}"


def source_scope_text(source_id: str, key: str) -> str:
    if source_id == TUSI:
        return tusi_scope(key)
    if source_id == FAYD:
        return fayd_scope(key)
    if source_id == IBN and key in IBN_GROUPS:
        start, end = IBN_GROUPS[key]
        return f"انعام ۶:{fa_num(start)}–{fa_num(end)}"
    return verse_ref(key)


def source_cite(source_id: str, key: str) -> str:
    if source_id in prior.QURANCOM_SLUGS:
        author_and_title = {
            TABARI: "طبری، ۳۱۰ق، *جامع البيان عن تأويل آي القرآن*",
            IBN: "ابن‌کثیر، ۷۷۴ق، *تفسير القرآن العظيم*",
            QURTUBI: "قرطبی، ۶۷۱ق، *الجامع لأحكام القرآن*",
            WASIT: "محمد سید طنطاوی، *التفسير الوسيط للقرآن الكريم*",
        }[source_id]
        grouped = source_id == IBN and key in IBN_GROUPS
        scope = source_scope_text(source_id, key)
        group_note = "؛ عنوانِ مدخلِ آرشیوی ۶:۵۵–۵۶ است" if grouped else ""
        return (
            f"{author_and_title}، ذیلِ {scope}؛ Quran.com API v4، متنِ آرشیویِ نسخهٔ 1.1 "
            f"از zeeyado/quran-ebook، commit {prior.QURAN_EBOOK_COMMIT}؛ "
            f"چاپ و صفحهٔ متنِ تفسیری احراز نشده{group_note}."
        )
    if source_id == TUSI:
        start, end = TUSI_GROUPS[key]
        direct_or_group = "مستقیم" if start == end else "گروهی"
        snapshot = prior.OPENITI_SNAPSHOTS[TUSI]
        return (
            f"طوسی، ۴۶۰ق، *التبيان الجامع لعلوم القرآن*، شرحِ {direct_or_group} {tusi_scope(key)}؛ "
            f"OpenITI/0475AH، commit {prior.OPENITI_TUSI_COMMIT}، پروندهٔ `{prior.TUSI_PATH}`، "
            f"metadata volume file `{snapshot['metadataPath']}`؛ نسخهٔ ناقصِ برگرفته از altafsir.com؛ "
            "چاپ و صفحه احراز نشده."
        )
    if source_id == FAYD:
        snapshot = prior.OPENITI_SNAPSHOTS[FAYD]
        return (
            f"فیض کاشانی، *الصافي في تفسير كلام الله الوافي*، شرحِ گروهیِ {fayd_scope(key)}؛ "
            f"OpenITI/1100AH، commit {prior.OPENITI_FAYD_COMMIT}، پروندهٔ `{prior.FAYD_PATH}`، "
            f"metadata volume file `{snapshot['metadataPath']}`؛ نسخهٔ ناقصِ برگرفته از altafsir.com؛ "
            "چاپ و صفحه احراز نشده."
        )
    if source_id == QURANENC:
        return f"التفسير الميسر، قرآن‌انک، نسخهٔ 1.0.0، ذیلِ {verse_ref(key)}؛ متنِ محلیِ آیه‌به‌آیه."
    raise KeyError(source_id)


def source_evidence(source_id: str, key: str) -> str:
    if source_id in {TABARI, IBN, QURTUBI}:
        if source_id == IBN and key == "6:56":
            return (
                "شاهدِ پوشش: عنوانِ مدخلِ آرشیوشده «Al-An'am 55–56» است، اما بدنهٔ ذخیره‌شده فقط ۶:۵۵ را شرح می‌دهد؛ "
                "برایِ ۶:۵۶ در این مدخل، شرحِ مستقل یافت نشد."
            )
        if source_id == IBN and key == "6:55":
            return (
                "شاهدِ منبع: عنوانِ آرشیوشده «Al-An'am 55–56» است و بدنه دربارهٔ ۶:۵۵ سخن می‌گوید؛ "
                "سرعنوانِ گروهی دامنهٔ مدخل است، نه شاهدِ شرحِ مستقل برایِ ۶:۵۶."
            )
        return (
            f"شاهدِ منبع: مدخلِ عربیِ آیه‌محورِ {verse_ref(key)} در آرشیوِ نسخهٔ 1.1 بررسی شد؛ "
            "خلاصه فقط به متنِ مدخل محدود است و چاپ/صفحهٔ متنِ تفسیری از آرشیو احراز نشده."
        )
    if source_id == WASIT:
        return (
            f"شاهدِ منبع: مدخلِ عربیِ طنطاوی برایِ {verse_ref(key)} در آرشیوِ نسخهٔ 1.1 بررسی شد؛ "
            "خلاصه به همان موضع محدود است و چاپ/صفحه احراز نشده است."
        )
    if source_id in {TUSI, FAYD}:
        scope = source_scope_text(source_id, key)
        start, end = (TUSI_GROUPS if source_id == TUSI else FAYD_GROUPS)[key]
        note = "فقط موضعِ آیهٔ هدف از شرحِ گروهی خلاصه شد." if start != end else "موضعِ آیه در متنِ ناقص بررسی شد."
        return (
            f"شاهدِ OpenITI: دامنهٔ واقعیِ متن {scope} است؛ {note} "
            "metadata چاپ و شمارهٔ صفحه را مشخص نمی‌کند."
        )
    if source_id == QURANENC:
        return f"شاهدِ محلی: متنِ نسخهٔ 1.0.0 قرآن‌انک برایِ {verse_ref(key)} بررسی شد؛ خلاصه نقلِ لفظی نیست."
    raise KeyError(source_id)


def source_limit(source_id: str) -> str:
    if source_id in {TABARI, IBN, QURTUBI, WASIT}:
        return (
            "این بند خلاصهٔ منسوب است، نه نقلِ لفظی؛ نسخه و صفحهٔ اثر احراز نشده‌اند. "
            "مخزنِ quran-ebook دارایِ LICENSE با GPL-3.0 است، اما دامنهٔ آن نسبت به متنِ تفسیریِ برگرفته از Quran.com "
            "و شرایطِ منبعِ اصلی نیازمندِ بررسی است؛ حقوقِ اقتباس/بازنشر هنوز نهایی نشده است."
        )
    if source_id in {TUSI, FAYD}:
        return (
            "این بند خلاصهٔ تحریری از نسخه‌ای ناقص است، نه نقلِ لفظی؛ چاپ و صفحه شناسایی نشده و "
            "مجوزِ OpenITI/Altafsir برایِ اقتباس یا بازنشر در این بررسی احراز نشده است."
        )
    if source_id == QURANENC:
        return shared.SOURCE_LIMIT
    raise KeyError(source_id)


def source_item(source_id: str, key: str, text: str) -> dict:
    record = {
        "text": text,
        "cite": source_cite(source_id, key),
        "kind": "source-summary",
        "language": "fa",
        "sourceId": source_id,
        "sourceUrl": source_url(source_id, key),
        "evidence": source_evidence(source_id, key),
        "limit": source_limit(source_id),
        "tradition": shared.SOURCE_TRADITIONS.get(source_id, "اهل‌سنت"),
    }
    if source_id == IBN and key == "6:56":
        record["kind"] = "source-coverage-note"
        record["limit"] = (
            "این کارت فقط خلأِ بدنهٔ آرشیوشده را ثبت می‌کند؛ عنوانِ گروهی به معنایِ شرحِ مستقل نیست، "
            "این یادداشت تفسیر شمرده نمی‌شود و نبودِ آن در این فایل، نبودِ شرح در کلِ اثر را ثابت نمی‌کند."
        )
    return record


def editorial_item(text: str, cite: str, key: str, field: str, evidence: str | None = None) -> dict:
    return {
        "text": text,
        "cite": cite,
        "kind": shared.FIELD_KIND[field],
        "language": "fa",
        "evidence": evidence or f"شاهدِ متنی: {quran(key)}؛ این بند تحلیلِ تحریری است.",
        "limit": shared.EDITORIAL_LIMIT,
    }


def expand_item_text(text: str, key: str, field: str, source_ids: tuple[str, ...]) -> str:
    if len(text.split()) >= 14:
        return text
    source_name = prior.SOURCE_NAMES[source_ids[0]]
    additions = {
        "notes": f"این نکته در {verse_ref(key)} با مدخلِ {source_name} مقابله شده و به همین موضع محدود است.",
        "critical": f"این ارزیابی از مدخلِ {source_name} و سیاقِ {verse_ref(key)} فراتر نمی‌رود؛ تعمیم نیازمندِ شاهد است.",
        "research": f"پاسخ را با متنِ عربیِ {verse_ref(key)} و مدخلِ {source_name} مقابله کنید و اختلافِ نقل را جدا ثبت کنید.",
    }
    expanded = f"{text} {additions[field]}"
    assert len(expanded.split()) >= 14, (key, field, expanded)
    return expanded


def custom_item(item: tuple[str, tuple[str, ...]], key: str, field: str) -> dict:
    text, source_ids = item
    assert source_ids and set(source_ids) <= set(SOURCE_ORDER), (key, field, source_ids)
    text = expand_item_text(text, key, field, source_ids)
    cites = [source_cite(source_id, key) for source_id in source_ids]
    evidence = "؛ ".join(source_evidence(source_id, key) for source_id in source_ids)
    return editorial_item(
        text,
        "؛ مقابله با ".join(cites),
        key,
        field,
        evidence=f"شاهدِ قرآنی: {quran(key)}؛ شاهدهایِ منبع: {evidence}",
    )


def section_for(key: str) -> tuple[int, int, str]:
    _, ayah = parse_key(key)
    for start, end, title in SECTIONS:
        if start <= ayah <= end:
            return start, end, title
    raise KeyError(key)


def context_items(key: str, record: dict, previous_key: str, next_key: str | None, dossier: dict) -> list[dict]:
    previous_title = dossier["verses"][previous_key]["title"]
    next_title = (
        dossier["verses"][next_key]["title"] if next_key and next_key in dossier["verses"]
        else "ادامهٔ سوره پس از پایانِ بازهٔ این بسته"
    )
    start, end, section_title = section_for(key)
    focus = record["notes"][0][0]
    tusi_start, tusi_end = TUSI_GROUPS[key]
    fayd_start, fayd_end = FAYD_GROUPS[key]
    tusi_scope_text = tusi_scope(key)
    fayd_scope_text = fayd_scope(key)
    grouped_detail = (
        f"طوسی در دامنهٔ {tusi_scope_text} و فیض در دامنهٔ {fayd_scope_text} شرحِ گروهی دارد؛ "
        "این ارجاع‌ها محدودهٔ متن را نشان می‌دهند، نه صفحهٔ چاپی یا شرحِ مستقلِ هر آیه."
    )
    if key == "6:56":
        grouped_detail += " سرعنوانِ ابن‌کثیر ۵۵–۵۶ است، اما بدنهٔ ذخیره‌شده برایِ ۵۶ شرحی ندارد."
    texts = [
        (
            f"در ترتیبِ مصحف، {verse_ref(previous_key)} با محورِ «{previous_title}» پیش ازِ {verse_ref(key)} می‌آید؛ "
            f"آیهٔ حاضر با «{record['title']}» ادامه می‌یابد و این پیوندِ ساختاری است، نه سببِ نزول."
        ),
        (
            f"لنگرِ سیاقیِ {verse_ref(key)} در این پرونده «{record['title']}» است؛ "
            f"«{focus}» باید کنارِ عبارتِ عربی خوانده شود، نه به جایِ آن."
        ),
        (
            f"در ادامهٔ نزدیک، {verse_ref(key)} به «{next_title}» می‌رسد؛ "
            "این مقایسه گذارِ موضوعی را نشان می‌دهد و به‌تنهایی وحدتِ سببِ نزول را ثابت نمی‌کند."
        ),
        (
            f"{verse_ref(key)} در بخشِ تحریریِ «{section_title}»، یعنی انعام ۶:{fa_num(start)}–{fa_num(end)} قرار دارد؛ "
            "این بخش‌بندی برایِ مطالعه است و عنوانِ تاریخیِ منبع نیست."
        ),
        (
            f"برایِ دامنهٔ ارجاعِ {verse_ref(key)}، «{record['title']}» را با محدودهٔ واقعیِ متن بسنجید: "
            f"{grouped_detail}"
        ),
    ]
    cites = [
        quran_pair(previous_key, key),
        quran(key) + "؛ مقابله با " + source_cite(TABARI, key),
        quran_pair(key, next_key) if next_key and next_key in dossier["verses"] else quran(key),
        quran(f"6:{start}", f"6:{end}"),
        source_cite(TUSI, key) + "؛ مقابله با " + source_cite(FAYD, key),
    ]
    return [
        editorial_item(
            text,
            cite,
            key,
            "context",
            evidence=f"شاهدِ متنی: {quran(key)}؛ پیوندِ درون‌سوره‌ای، تحلیلِ تحریری است و دامنهٔ منابع در ارجاع آمده است.",
        )
        for text, cite in zip(texts, cites)
    ]


def model_items(key: str, record: dict) -> list[dict]:
    descriptions = prior.models_for(key, record)
    return [prior.model_item(model, text, key) for model, text in descriptions.items()]


def critical_points(key: str, points: list[tuple[str, tuple[str, ...]]]) -> list[tuple[str, tuple[str, ...]]]:
    direction_words = ("خطر", "پرسش", "نقد", "خطای خوانش", "تبار", "مرز", "فرق", "جدا", "مأخذ")
    if any(word in " ".join(text for text, _ in points) for word in direction_words):
        return points
    expanded = list(points)
    text, source_ids = expanded[-1]
    source_name = prior.SOURCE_NAMES[source_ids[0]]
    variants = (
        f"مرزِ این ارزیابی در {verse_ref(key)} را به شاهدِ {source_name} محدود کنید؛ تعمیمِ تاریخی نیازمندِ مأخذِ مستقل است.",
        f"برایِ نقدِ این نتیجه، گزارشِ {source_name} را از داوریِ تحریری جدا و ادعایِ فراتر از {verse_ref(key)} را مستند کنید.",
        f"در این خوانش، فرقِ گزارشِ {source_name} با تفسیرِ پژوهشگر باید روشن بماند؛ سیاقِ {verse_ref(key)} حدِّ نخستِ سنجش است.",
        f"پرسشِ اصلی این است که آیا {source_name} چنین تعمیمی را می‌پذیرد؛ شاهدِ بیرونی برایِ پاسخ همچنان لازم است.",
    )
    addition = variants[parse_key(key)[1] % len(variants)]
    expanded[-1] = (f"{text} {addition}", source_ids)
    return expanded


def build_entry(key: str, record: dict, previous_key: str, next_key: str | None, dossier: dict) -> dict:
    entry = {"title": record["title"]}
    entry["notes"] = [custom_item(item, key, "notes") for item in record["notes"]]
    entry["context"] = context_items(key, record, previous_key, next_key, dossier)
    entry["classical"] = [source_item(source_id, key, record["classical"][source_id]) for source_id in CLASSICAL_ORDER]
    entry["modern"] = [
        source_item(source_id, key, record["modern_sources"][source_id])
        for source_id in (QURANENC, WASIT)
    ]
    entry["modern"].extend(model_items(key, record))
    entry["critical"] = [custom_item(item, key, "critical") for item in critical_points(key, record["critical"])]
    entry["research"] = [custom_item(item, key, "research") for item in record["research"]]
    entry["status"] = shared.STATUS
    entry["standard"] = 2
    return entry


def validate_data(registry: dict | None = None) -> None:
    expected = tuple(f"6:{ayah}" for ayah in range(41, 91))
    assert VERSES == expected, (len(VERSES), VERSES[:2], VERSES[-2:])
    assert set(curated.DATA) == set(expected)
    assert set(TUSI_GROUPS) == set(expected)
    assert set(FAYD_GROUPS) == set(expected)
    assert TUSI_GROUPS["6:41"] == (40, 41)
    assert TUSI_GROUPS["6:76"] == TUSI_GROUPS["6:79"] == (76, 79)
    assert TUSI_GROUPS["6:84"] == TUSI_GROUPS["6:90"] == (84, 90)
    assert FAYD_GROUPS["6:41"] == (36, 41)
    assert FAYD_GROUPS["6:76"] == (76, 79)
    assert FAYD_GROUPS["6:82"] == (82, 90)
    for key, record in curated.DATA.items():
        assert len(record["notes"]) == len(record["critical"]) == len(record["research"]) == 5, key
        assert set(record["classical"]) == set(CLASSICAL_ORDER), key
        assert set(record["modern_sources"]) == {QURANENC, WASIT}, key
        assert len(record["model_terms"]) == 3 and all(record["model_terms"]), key
        for field in ("notes", "critical", "research"):
            for text, source_ids in record[field]:
                assert text.strip() and source_ids and set(source_ids) <= set(SOURCE_ORDER), (key, field, source_ids)
                assert len(expand_item_text(text, key, field, source_ids).split()) >= 14, (key, field, text)
        for source_id, text in record["classical"].items():
            assert text.strip() and len(text.split()) >= 14, (key, source_id, text)
        for source_id, text in record["modern_sources"].items():
            assert text.strip() and len(text.split()) >= 14, (key, source_id, text)
    assert "۵۵–۵۶" in source_cite(IBN, "6:56")
    if registry:
        assert {source["id"] for source in registry["sources"]} >= set(SOURCE_ORDER)


def build_catalog(registry: dict) -> dict:
    by_id = {source["id"]: source for source in registry["sources"]}
    urls_by_source = {source_id: [] for source_id in SOURCE_ORDER}
    for key in VERSES:
        for source_id in SOURCE_ORDER:
            urls_by_source[source_id].append(source_url(source_id, key))
    bases = {
        TABARI: "مدخل‌هایِ آیه‌محورِ طبری در آرشیوِ Quran.com API v4 نسخهٔ 1.1 برایِ انعام ۶:۴۱–۹۰ بررسی شدند؛ نقل‌ها و ترجیح‌هایِ او به خودِ مفسر منسوب‌اند.",
        IBN: "مدخل‌هایِ ابن‌کثیر برایِ آیاتِ بازه بررسی شدند؛ سرعنوانِ آرشیویِ ۶:۵۵–۵۶ در بدنه فقط ۶:۵۵ را شرح می‌دهد و ۶:۵۶ به‌عنوانِ خلأ ثبت شده است.",
        QURTUBI: "مدخل‌هایِ آیه‌محورِ قرطبی در آرشیوِ نسخهٔ 1.1 بررسی شدند؛ اختلافِ نحوی، روایی و فقهی به او نسبت داده شده است.",
        TUSI: "متنِ ناقصِ *التبيان* از OpenITI، commit پین‌شده، بررسی شد؛ دامنه‌هایِ مستقیم و گروهیِ ۶:۴۰–۴۱ تا ۶:۸۴–۹۰ بدونِ تبدیل به شمارهٔ صفحه ثبت شده‌اند.",
        FAYD: "متنِ ناقصِ *الصافي* از OpenITI بررسی شد؛ دامنه‌هایِ گروهیِ ۶:۳۶–۴۱ تا ۶:۸۲–۹۰ حفظ شده‌اند و جزئیاتِ روایی به ناقلان نسبت داده شده است.",
        QURANENC: "متنِ محلیِ آیه‌به‌آیهٔ قرآن‌انک، نسخهٔ 1.0.0، برایِ هر ۵۰ آیه بررسی شد؛ خلاصه‌ها نقلِ لفظی نیستند.",
        WASIT: "مدخل‌هایِ عربیِ طنطاوی از آرشیوِ Quran.com API v4 نسخهٔ 1.1 برایِ آیاتِ بازه بررسی شدند؛ چاپ و صفحه احراز نشده است.",
    }
    scopes = {
        TABARI: "انعام ۶:۴۱–۹۰؛ مدخل‌هایِ آیه‌محورِ آرشیوِ نسخهٔ 1.1",
        IBN: "انعام ۶:۴۱–۹۰؛ مدخل‌هایِ آیه‌محور؛ مدخلِ ۵۵–۵۶ فقط در بدنه ۵۵ را شرح می‌دهد",
        QURTUBI: "انعام ۶:۴۱–۹۰؛ مدخل‌هایِ آیه‌محورِ آرشیوِ نسخهٔ 1.1",
        TUSI: "گروه‌ها و آیاتِ مستقیم: ۶:۴۰–۴۱، ۴۲–۴۳، ۴۴–۴۵، ۴۶، ۴۷، ۴۸–۴۹، ۵۰–۶۰، ۶۱–۶۲، ۶۳–۶۵، ۶۶–۶۷، ۶۸–۷۵، ۷۶–۷۹، ۸۰–۸۳ و ۸۴–۹۰؛ متنِ ناقصِ OpenITI",
        FAYD: "گروه‌ها: ۶:۳۶–۴۱، ۴۲–۴۹، ۵۰–۵۳، ۵۴–۵۹، ۶۰–۶۵، ۶۶–۷۱، ۷۲–۷۵، ۷۶–۷۹، ۸۰–۸۱ و ۸۲–۹۰؛ متنِ ناقصِ OpenITI",
        QURANENC: "انعام ۶:۴۱–۹۰؛ متنِ محلیِ آیه‌به‌آیه، نسخهٔ 1.0.0",
        WASIT: "انعام ۶:۴۱–۹۰؛ مدخل‌هایِ آیه‌محورِ آرشیوِ نسخهٔ 1.1",
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
        "پنج منبعِ کهن و دو شرحِ معاصر جدا از سه کاربستِ محدودِ ایزوتسو، فیلمور و معناشناسیِ شناختی‌اند. "
        "در ۶:۵۶، مدخلِ ابن‌کثیر عنوانِ ۵۵–۵۶ دارد اما فقط ۵۵ را توضیح می‌دهد؛ کارتِ ۶:۵۶ خلأِ بدنه است، نه تفسیرِ پنجم. "
        "دامنه‌هایِ گروهیِ طوسی و فیض در هر dossier حفظ شده‌اند. گزارش‌هایِ اسبابِ نزول، قرائت، اختلافِ کلامی و روایت‌هایِ خاص به ناقلِ خود نسبت داده شده‌اند. "
        "متن‌هایِ quran-ebook و OpenITI ناقص/آرشیوی‌اند؛ GPL-3.0 مخزن به‌تنهایی حقوقِ متنِ تفسیریِ منقول را احراز نمی‌کند و مجوزِ اقتباسِ OpenITI/Altafsir نیز مشخص نشده است. "
        "اطلاعاتِ چاپ یا صفحهٔ احرازنشده درج نشده؛ همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند."
    )
    return {
        "id": COLLECTION_ID,
        "title": "منابعِ تفسیریِ مورد استناد در بستهٔ انعام ۶:۴۱–۹۰",
        "status": "mixed-linked-and-summary-only",
        "items": items,
        "comparativeCore": {
            "scope": "انعام ۶:۴۱–۹۰؛ یک پوششِ صریحِ منبعی برایِ ۶:۵۶ ثبت نشده است",
            "sunniSourceIds": sorted(SUNNI),
            "shiaSourceIds": sorted(SHIA),
            "modernSourceIds": [QURANENC, WASIT],
            "note": note,
        },
        "notice": (
            "پیوند و خلاصه به‌معنای بازنشرِ متنِ کامل یا احرازِ مجوزِ بازنشر نیست؛ "
            "مدخلِ ابن‌کثیر برایِ ۶:۵۶ یک خلأِ صریحِ پوشش دارد و این بسته پیش‌نویسِ نیازمندِ داوریِ تخصصی است."
        ),
    }


def update_registry(registry: dict) -> dict:
    existing_coverage = {
        source["id"]: set(source.get("researchSnapshot", {}).get("coveredBatches", []))
        for source in registry.get("sources", [])
    }
    registry = prior.update_registry(registry)
    registry["version"] = max(int(registry.get("version", 0)), 9)
    by_id = {source["id"]: source for source in registry["sources"]}
    for source_id in SOURCE_ORDER:
        source = by_id[source_id]
        prior_scopes = source.get("sourceUrls", [])
        source["availabilityNote"] = (
            "در دو بستهٔ متوالیِ مائده ۵:۱۱۱–۱۲۰ و انعام ۶:۱–۱۴۰ بررسی شده؛ "
            "این رکورد وضعیتِ دسترسی و حدودِ نسخه را ثبت می‌کند، نه احرازِ حقوقِ اقتباس."
        )
        if source_id in {TUSI, FAYD}:
            snapshot = source.get("researchSnapshot", {})
            covered_batches = existing_coverage.get(source_id, set()) | set(snapshot.get("coveredBatches", [])) | {"dossier-58", BATCH_ID}
            snapshot["coveredBatches"] = sorted(covered_batches, key=lambda value: int(value.split("-")[1]))
            snapshot["edition"] = "not identified"
            snapshot["pagination"] = "not specified"
            snapshot["licenseStatus"] = "unresolved"
            source["researchSnapshot"] = snapshot
        elif source_id in {TABARI, IBN, QURTUBI, WASIT}:
            source["archiveSnapshot"] = prior.QURAN_EBOOK_ARCHIVES[source_id]
            source["licenseStatus"] = "review-needed"
        if prior_scopes:
            source["availabilityNote"] += " نشانی‌هایِ مستقیم در کاتالوگِ بسته ثبت شده‌اند."
    return registry


def source_snapshot_metadata() -> dict:
    archives = {
        source_id: {
            "sourceId": source_id,
            "repository": "zeeyado/quran-ebook",
            "commit": prior.QURAN_EBOOK_COMMIT,
            **archive,
            "licenseStatus": "repository GPL-3.0 declared; scope for upstream tafsir text requires separate review",
        }
        for source_id, archive in prior.QURAN_EBOOK_ARCHIVES.items()
    }
    openiti = {
        source_id: {
            "sourceId": source_id,
            **snapshot,
            "edition": "not identified",
            "pagination": "not specified",
            "textStatus": "incomplete; scraped from altafsir.com per OpenITI metadata",
            "licenseStatus": "unresolved; no permission for adaptation/redistribution established",
        }
        for source_id, snapshot in prior.OPENITI_SNAPSHOTS.items()
    }
    return {
        "batchId": BATCH_ID,
        "range": "6:41–90",
        "quranEbook": {
            "repository": "zeeyado/quran-ebook",
            "commit": prior.QURAN_EBOOK_COMMIT,
            "repositoryLicense": "GPL-3.0 LICENSE file exists at the pinned repository snapshot",
            "textRightsStatus": "unresolved; repository license scope over Quran.com-derived tafsir text is not assumed",
            "archives": archives,
        },
        "openIti": openiti,
        "scopeNotes": {
            "ibnKathir": "The archive entry heading spans Al-An'am 55–56, but its stored body comments on 6:55 only; 6:56 is recorded as a coverage gap, not an independent interpretation.",
            "tusi": "Grouped scopes: 6:40–41; 42–43; 44–45; 48–49; 61–62; 66–67; 76–79; 84–90. Remaining target ayas have direct markers.",
            "fayd": "Grouped scopes: 6:36–41; 42–49; 50–53; 54–59; 60–65; 66–71; 72–75; 76–79; 80–81; 82–90.",
        },
        "rawWorkBench": {
            "path": "/tmp/anam_6_41_90_sources.json",
            "status": "temporary source extraction, not included in the application; curated paraphrases and source metadata are stored in the builder and data module",
        },
    }


def update_source_snapshots(dossier: dict) -> None:
    snapshots = dossier.setdefault("sourceSnapshots", {})
    snapshots["anam_6_41_90"] = source_snapshot_metadata()
    for key in ("tabari", "qurtubi"):
        if key in snapshots:
            snapshots[key]["textRightsStatus"] = (
                "The quran-ebook repository has a GPL-3.0 LICENSE; its scope over Quran.com-derived tafsir text and original-source terms still requires review."
            )


def _refresh_araf_coverage(notice: str, dossier: dict | None) -> str:
    if not dossier:
        return notice
    ranges = (
        (206, "اعراف بازهٔ ۷:۱–۲۰۶ را پوشش می‌دهد و سورهٔ اعراف در این پرونده‌ها کامل است."),
        (200, "اعراف بازهٔ ۷:۱–۲۰۰ را پوشش می‌دهد؛ ادامهٔ ترتیبیِ همین سوره از ۷:۲۰۱ است."),
        (150, "اعراف بازهٔ ۷:۱–۱۵۰ را پوشش می‌دهد؛ ادامهٔ ترتیبیِ همین سوره از ۷:۱۵۱ است."),
        (100, "اعراف بازهٔ ۷:۱–۱۰۰ را پوشش می‌دهد؛ ادامهٔ ترتیبیِ همین سوره از ۷:۱۰۱ است."),
        (50, "اعراف بازهٔ ۷:۱–۵۰ را پوشش می‌دهد؛ ادامهٔ ترتیبیِ همین سوره از ۷:۵۱ است."),
    )
    for end, replacement in ranges:
        if all(f"7:{ayah}" in dossier["verses"] for ayah in range(1, end + 1)):
            return re.sub(
                r"اعراف بازهٔ ۷:۱–(?:۵۰|۱۰۰|۱۵۰|۲۰۰|۲۰۶) را پوشش می\u200c?دهد[^.]*\.",
                replacement,
                notice,
                count=1,
            )
    return notice


def canonical_notice(dossier: dict | None = None) -> str:
    completed_anam = bool(dossier) and all(f"6:{ayah}" in dossier["verses"] for ayah in range(141, 166))
    completed_araf_1_50 = bool(dossier) and all(f"7:{ayah}" in dossier["verses"] for ayah in range(1, 51))
    if completed_anam and completed_araf_1_50:
        anam_coverage = (
            "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است؛ "
            "اعراف بازهٔ ۷:۱–۵۰ را پوشش می‌دهد و ادامهٔ ترتیبیِ همین سوره از ۷:۵۱ است."
        )
    elif completed_anam:
        anam_coverage = "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است؛ گامِ ترتیبیِ بعدی اعراف ۷:۱ است."
    else:
        anam_coverage = "انعام بازهٔ ۶:۱–۱۴۰ را پوشش می‌دهد؛ ادامهٔ انعام، یعنی ۶:۱۴۱ به بعد، هنوز پوشش ندارد."
    notice = (
        "این پرونده‌ها پیش‌نویس‌هایِ تحریریِ منبع‌محورند؛ بازبینیِ تخصصی انجام نشده است. "
        "بسته‌های مائده ۵:۱–۶، ۵:۷–۱۲، ۵:۱۳–۱۸، ۵:۱۹–۲۴، ۵:۲۵–۳۰، ۵:۳۱–۳۶، ۵:۳۷–۴۲، ۵:۴۳–۴۸، "
        "۵:۴۹–۵۴، ۵:۵۵–۶۰، ۵:۶۱–۱۱۰ و ۵:۱۱۱–۱۲۰ افزوده شده‌اند؛ مائده در این checkout بازهٔ ۵:۱–۱۲۰ را پوشش می‌دهد؛ "
        f"{anam_coverage} "
        "نساء در این checkout بازهٔ ۴:۱–۱۷۶ را پوشش می‌دهد؛ پوششِ آیه‌ایِ نساء به معنای تکمیلِ پژوهشِ تفسیری نیست. "
        "بسته‌های یونس بازه‌هایِ ۱۰:۴۹–۶۰، ۱۰:۶۱–۷۲ و ۱۰:۷۳–۸۴ را پوشش می‌دهند؛ برایِ ۱۰:۱–۴۸ پرونده‌ای ساخته نشده است. "
        "خلاصه‌ها نقلِ لفظی نیستند؛ دامنهٔ واقعیِ شرح‌هایِ گروهی و اختلافِ اقوال جدا ثبت شده‌اند. "
        "خلأِ نسخهٔ ناقصِ فیض در ۶:۲۶، نشانِ مستقلِ ۶:۲، گروهِ طنطاوی در ۶:۴–۵ و خلأِ بدنهٔ ابن‌کثیر در ۶:۵۶ آشکار ثبت شده‌اند. "
        "چاپ، صفحه یا اطلاعاتِ نشرِ احرازنشده ساخته نشده و هیچ بندی بازبینیِ تخصصی‌شده معرفی نمی‌شود. "
        "مجوزِ متنِ تفسیریِ آرشیوهایِ Quran.com و OpenITI/Altafsir برایِ اقتباس یا بازنشر در این کار احراز نشده است."
    )
    return _refresh_araf_coverage(notice, dossier)


def update_method(method: str) -> str:
    later_marker = "در بستهٔ انعام ۶:۹۱–۱۴۰"
    later_section = method[method.index(later_marker):].strip() if later_marker in method else ""
    method = prior.update_method(method)
    marker = "در بستهٔ انعام ۶:۴۱–۹۰"
    if marker in method:
        method = method.split(marker, 1)[0].rstrip()
    addition = (
        " در بستهٔ انعام ۶:۴۱–۹۰، مدخل‌هایِ آیه‌محورِ طبری، ابن‌کثیر و قرطبی، متنِ محلیِ قرآن‌انک، "
        "مدخل‌هایِ طنطاوی و مواضعِ نشان‌گذاری‌شدهٔ طوسی و فیض در نسخه‌هایِ ناقصِ OpenITI مقابله شدند. "
        "دامنهٔ گروهیِ طوسی برایِ ۶:۴۰–۴۱، ۴۲–۴۳، ۴۴–۴۵، ۴۸–۴۹، ۶۱–۶۲، ۶۶–۶۷، ۷۶–۷۹ و ۸۴–۹۰ "
        "و دامنه‌هایِ فیض از ۶:۳۶–۴۱ تا ۸۲–۹۰ در هر پرونده آشکار است. سرعنوانِ ابن‌کثیر ۶:۵۵–۵۶ است، "
        "اما بدنه فقط ۶:۵۵ را شرح می‌دهد؛ ۶:۵۶ به‌عنوانِ خلأِ پوشش، نه خوانشِ پنجم، ثبت شد. "
        "گزارش‌هایِ سببِ نزول، قرائت، اختلافِ کلامی، تفسیرهایِ منسوب به امامان و تطبیق‌هایِ روایی جدا و به منبعِ خود نسبت داده شده‌اند؛ "
        "سه کاربستِ ایزوتسو، فیلمور و معناشناسیِ شناختی مستقل از خلاصه‌هایِ مفسران‌اند. "
        "خلاصه‌ها نقلِ لفظی نیستند، نسخه‌هایِ OpenITI ناقص و بی‌صفحه‌اند، چاپ یا اطلاعاتِ نشرِ احرازنشده ساخته نشده و همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند. "
        "مخزنِ quran-ebook دارایِ LICENSE با GPL-3.0 است، اما دامنهٔ آن بر متنِ تفسیریِ برگرفته از Quran.com و شرایطِ منبعِ اصلی نیازمندِ بررسی است؛ "
        "مجوزِ اقتباس/بازنشرِ متن‌هایِ OpenITI/Altafsir در این کار احراز نشده است."
    )
    result = method.rstrip() + addition
    return result + (" " + later_section if later_section else "")


def update_attribution_doc() -> None:
    if not ATTRIBUTION_PATH.exists():
        return
    text = ATTRIBUTION_PATH.read_text(encoding="utf-8")
    later_marker = "## ۷. منابعِ بررسی‌شده برایِ بستهٔ انعام ۶:۹۱–۱۴۰"
    later_section = "\n\n" + text[text.index(later_marker):].strip() if later_marker in text else ""
    marker = "## ۶. منابعِ بررسی‌شده برایِ بستهٔ انعام ۶:۴۱–۹۰"
    if marker in text:
        text = text.split(marker, 1)[0].rstrip()
    tusi = prior.OPENITI_SNAPSHOTS[TUSI]
    fayd = prior.OPENITI_SNAPSHOTS[FAYD]
    addition = f"""

{marker}

برایِ بستهٔ انعام ۶:۴۱–۹۰، متنِ خامِ تفسیری در فایل‌هایِ برنامه بازنشر نشده است؛ پرونده‌ها خلاصه‌هایِ تحریریِ منتسب و ارجاع‌هایِ دامنه‌مند دارند. پین‌کردنِ نسخه برایِ بازبینیِ متن است و به‌تنهایی تأییدِ حقِ اقتباس یا بازنشر نیست.

### آرشیوهایِ Quran.com API v4 در `zeeyado/quran-ebook`

- مخزنِ بررسی‌شده: commit `{prior.QURAN_EBOOK_COMMIT}`؛ مخزن فایلِ `LICENSE` با متنِ GPL-3.0 دارد. دامنهٔ حقوقیِ آن نسبت به متن‌هایِ تفسیریِ برگرفته از Quran.com و شرایطِ منبعِ اصلی در این کار احراز نشده است؛ وضعیتِ اقتباس/بازنشر را «نیازمندِ بررسی» بدانید.
- طبری: `release/quran_tafsir_tabari_v1.1.zip`، blob `{prior.QURAN_EBOOK_ARCHIVES[TABARI]['gitBlobSha']}`، SHA-256 `{prior.QURAN_EBOOK_ARCHIVES[TABARI]['sha256']}`.
- ابن‌کثیر: `release/quran_tafsir_ibn_kathir_ar_v1.1.zip`، blob `{prior.QURAN_EBOOK_ARCHIVES[IBN]['gitBlobSha']}`، SHA-256 `{prior.QURAN_EBOOK_ARCHIVES[IBN]['sha256']}`. عنوانِ مدخلِ آرشیویِ انعام ۶:۵۵–۵۶ در بدنه فقط ۶:۵۵ را شرح می‌دهد؛ ۶:۵۶ به‌عنوانِ خلأ ثبت شده است.
- قرطبی: `release/quran_tafsir_qurtubi_v1.1.zip`، blob `{prior.QURAN_EBOOK_ARCHIVES[QURTUBI]['gitBlobSha']}`، SHA-256 `{prior.QURAN_EBOOK_ARCHIVES[QURTUBI]['sha256']}`.
- وسيطِ طنطاوی: `release/quran_tafsir_wasit_v1.1.zip`، blob `{prior.QURAN_EBOOK_ARCHIVES[WASIT]['gitBlobSha']}`، SHA-256 `{prior.QURAN_EBOOK_ARCHIVES[WASIT]['sha256']}`.

### متن‌هایِ OpenITI برایِ طوسی و فیض

- طوسی، *التبيان الجامع لعلوم القرآن*: مخزن `OpenITI/0475AH`، commit `{prior.OPENITI_TUSI_COMMIT}`؛ پروندهٔ `{prior.TUSI_PATH}`، Git blob `{tusi['gitBlobSha']}`، SHA-256ِ فایلِ دریافت‌شده `{tusi['fileSha256']}`؛ metadata volume file `{tusi['metadataPath']}`، blob `{tusi['metadataGitBlobSha']}`.
- فیض کاشانی، *الصافي في تفسير كلام الله الوافي*: مخزن `OpenITI/1100AH`، commit `{prior.OPENITI_FAYD_COMMIT}`؛ پروندهٔ `{prior.FAYD_PATH}`، Git blob `{fayd['gitBlobSha']}`، SHA-256ِ فایلِ دریافت‌شده `{fayd['fileSha256']}`؛ metadata volume file `{fayd['metadataPath']}`، blob `{fayd['metadataGitBlobSha']}`.
- metadataهایِ این دو متن آنها را نسخه‌هایی ناقص و اخذشده از altafsir.com معرفی می‌کنند؛ مقدمهٔ اثر، چاپِ مشخص و صفحهٔ چاپی تعیین نشده است. برایِ متن/میزبان مجوزی در این بررسی احراز نشد؛ وضعیتِ اقتباس و بازنشر نامشخص است.
- دامنه‌هایِ گروهی در dossier و کاتالوگ ثبت شده‌اند: طوسی از ۶:۴۰–۴۱ تا ۶:۸۴–۹۰، و فیض از ۶:۳۶–۴۱ تا ۶:۸۲–۹۰. هر خلاصه تنها موضعِ آیهٔ هدف را بازگو می‌کند، نه کلِ شرحِ گروهی را.

در فایلِ دادهٔ پژوهشی فقط خلاصه‌هایِ بازنویسی‌شده و نامِ منبع ثبت شده‌اند؛ نسخهٔ خامِ استخراج‌شده در `/tmp/anam_6_41_90_sources.json` موقت بود و در برنامه/مخزن گنجانده نشده است. همهٔ بندها پیش‌نویس‌اند و به داوریِ تخصصی نیاز دارند.
"""
    ATTRIBUTION_PATH.write_text(text.rstrip() + addition + later_section, encoding="utf-8")


def validate_generated_entry(key: str, entry: dict) -> None:
    assert set(entry) >= {"title", *FIELDS, "status", "standard"}, key
    assert entry["standard"] == 2 and entry["status"] == shared.STATUS, key
    all_texts: list[str] = []
    for field in FIELDS:
        items = entry[field]
        assert len(items) == 5, (key, field, len(items))
        for item in items:
            assert len(item["text"].split()) >= 14, (key, field, item["text"])
            assert item["cite"].strip() and item["evidence"].strip() and item["limit"].strip(), (key, field)
            all_texts.append(item["text"])
    normalized = [re.sub(r"\s+", " ", text).strip() for text in all_texts]
    assert len(set(normalized)) == len(normalized), f"Repeated prose in {key}"
    classical_by_id = {item["sourceId"]: item for item in entry["classical"]}
    assert set(classical_by_id) == set(CLASSICAL_ORDER), key
    if key == "6:56":
        assert classical_by_id[IBN]["kind"] == "source-coverage-note"
        assert "فقط ۶:۵۵" in classical_by_id[IBN]["evidence"]
        assert "تفسیر شمرده نمی‌شود" in classical_by_id[IBN]["limit"]
        assert sum(item["kind"] == "source-summary" for item in entry["classical"]) == 4
    elif any(item["kind"] == "source-coverage-note" for item in entry["classical"]):
        assert sum(item["kind"] == "source-coverage-note" for item in entry["classical"]) == 1
        assert sum(item["kind"] == "source-summary" for item in entry["classical"]) == 4
    else:
        assert all(item["kind"] == "source-summary" for item in entry["classical"])
    modern_sources = {item.get("sourceId") for item in entry["modern"] if item.get("sourceId")}
    models = {item.get("model") for item in entry["modern"] if item.get("model")}
    assert modern_sources == {QURANENC, WASIT} and models == set(MODELS), key
    assert len({item["text"] for item in entry["modern"] if item.get("model")}) == 3


def main() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry = update_registry(registry)
    validate_data(registry)
    dossier = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))

    target_keys = set(VERSES)
    present = target_keys & set(dossier["verses"])
    assert len(present) in {0, len(target_keys)}, f"Partial existing batch: {sorted(present)[:5]}"
    assert all(f"6:{ayah}" in dossier["verses"] for ayah in range(1, 41))
    assert "6:40" in dossier["verses"]
    # Later contiguous batches are intentional; rebuilding this batch must not reject or replace them.

    ordered = list(VERSES)
    for index, key in enumerate(ordered):
        previous_key = ordered[index - 1] if index else "6:40"
        next_key = ordered[index + 1] if index + 1 < len(ordered) else "6:91"
        entry = build_entry(key, curated.DATA[key], previous_key, next_key, dossier)
        validate_generated_entry(key, entry)
        dossier["verses"][key] = entry

    dossier["batches"] = [batch for batch in dossier["batches"] if batch.get("id") != BATCH_ID]
    dossier["batches"].append({
        "id": BATCH_ID,
        "title": "بستهٔ پنجاه‌ونهم: انعام ۶:۴۱–۹۰؛ اضطرار، حجت و هدایتِ ابراهیم",
        "range": "6:41–90",
        "count": 50,
        "status": (
            "۵۰ پروندهٔ آیه‌محور در ترتیبِ مصحف؛ شش فیلدِ پنج‌بندی، پنج خلاصهٔ کهن در هر آیه به‌جز ۶:۵۶ "
            "که چهار شرح و یک یادداشتِ صریحِ خلأ دارد؛ دو شرحِ معاصر و سه کاربردِ جداگانهٔ معناشناختی. "
            "گروه‌بندیِ طوسی و فیض و اختلاف‌هایِ منقول حفظ شده‌اند؛ متن‌هایِ آرشیوی ناقص و حقوقِ اقتباس/بازنشر احرازنشده‌اند. "
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
    print(f"Added {len(VERSES)} dossiers; total={len(dossier['verses'])}; batch=6:41–90")


if __name__ == "__main__":
    main()
