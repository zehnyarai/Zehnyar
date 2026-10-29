# -*- coding: utf-8 -*-
"""Coverage, source attribution and UI checks for all four surah dossier fields."""
import json
import re
import struct
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
DOSSIERS = json.loads((STATIC / "surah-dossiers.json").read_text(encoding="utf-8"))
CORPUS = json.loads((STATIC / "offline-corpus.json").read_text(encoding="utf-8"))["verses"]
CHAPTERS = json.loads((ROOT / "data" / "chapters.json").read_text(encoding="utf-8"))["chapters"]
TAFSIR_REGISTRY = json.loads((STATIC / "tafsir-sources.json").read_text(encoding="utf-8"))["sources"]

DIACRITICS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u08d4-\u08ff]")
ARABIC_RUN = re.compile(r"[\u0600-\u06ff]+")
LETTER_MAP = str.maketrans({"ٱ": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ى": "ی", "ي": "ی", "ئ": "ی", "ؤ": "و", "ة": "ه", "ك": "ک", "ـ": " ", "‌": " "})
SOURCE_IDS = {"ar_tabari_qurancom", "ar_qurtubi_qurancom", "fa_mizan_furqan", "ar_qe_arabic_moyassar"}


def normalize(value):
    value = DIACRITICS.sub("", str(value)).translate(LETTER_MAP)
    value = re.sub(r"[^\w\s\u0600-\u06ff]", " ", value).lower()
    return " ".join(value.split())


def tokens(text):
    return [normalize(raw) for raw in ARABIC_RUN.findall(text) if normalize(raw) and " " not in normalize(raw)]


def record_map():
    return {f"{row[0]}:{row[1]}": row for row in CORPUS if isinstance(row, list)}


def parse_reference(reference):
    match = re.fullmatch(r"(\d+):(\d+)(?:-(\d+))?", str(reference))
    assert match, f"ارجاع نامعتبر: {reference}"
    surah, start, end = match.groups()
    return int(surah), int(start), int(end or start)


def range_references(dossier):
    return [parse_reference(unit["reference"]) for unit in dossier["overview"]]


def test_all_114_surahs_have_four_expanded_source_fields():
    expected = {str(chapter["id"]) for chapter in CHAPTERS}
    assert DOSSIERS["version"] == 2
    assert set(DOSSIERS["surahs"]) == expected
    assert len(expected) == 114
    assert set(DOSSIERS["sources"]) >= SOURCE_IDS
    for sid, dossier in DOSSIERS["surahs"].items():
        total = int(CHAPTERS[int(sid) - 1]["total_verses"])
        assert dossier["verseCount"] == total
        assert dossier["overview"]
        assert len(dossier["themes"]) >= 4
        assert len(dossier["vocabulary"]) >= 3
        assert len(dossier["reflections"]) >= 4
        assert sum(len(dossier[field]) for field in ("overview", "themes", "vocabulary", "reflections")) > 0
        source_quotes = [item for item in dossier["reflections"] if item["kind"] == "source-quote"]
        assert len(source_quotes) >= 4
        assert {item["sourceId"] for item in source_quotes} >= SOURCE_IDS
        assert sum(item["kind"] == "modern-research-note" for item in dossier["reflections"]) <= 5
        text_size = sum(
            len(str(value))
            for field in ("overview", "themes", "vocabulary", "reflections")
            for value in dossier[field]
        )
        assert text_size >= 1200, f"{sid}: محتوای چهار فیلد هنوز کم است ({text_size} نویسه)"

    baqarah = DOSSIERS["surahs"]["2"]
    assert len(baqarah["overview"]) == 72
    assert len(baqarah["themes"]) >= 100
    assert len(baqarah["vocabulary"]) >= 25
    assert len(baqarah["reflections"]) >= 20


def test_overview_ranges_cover_each_ayah_once_and_use_mizan_mapping():
    source_meta = DOSSIERS["sources"]["fa_mizan_furqan"]
    assert source_meta["version"] == "2026.0"
    assert source_meta["sourceUrl"].startswith("https://")
    for sid, dossier in DOSSIERS["surahs"].items():
        ranges = range_references(dossier)
        assert ranges == sorted(ranges, key=lambda item: (item[1], item[2]))
        cursor = 1
        for surah, start, end in ranges:
            assert surah == int(sid)
            assert start == cursor, f"{sid}: شکاف یا هم‌پوشانی در نقشهٔ بازه‌ها از آیهٔ {cursor}"
            assert end >= start
            cursor = end + 1
        assert cursor == dossier["verseCount"] + 1
        for unit in dossier["overview"]:
            assert unit["sourceId"] == "fa_mizan_furqan"
            assert unit["sourceRecordId"]
            assert unit["excerpt"].strip()
            assert isinstance(unit["excerptTruncated"], bool)
            assert isinstance(unit["headings"], list)


def test_source_headings_and_lexical_theme_witnesses_are_traceable():
    records = record_map()
    for sid, dossier in DOSSIERS["surahs"].items():
        overview_by_reference = {unit["reference"]: set(unit["headings"]) for unit in dossier["overview"]}
        for theme in dossier["themes"]:
            if theme["kind"] == "source-heading":
                assert theme["sourceId"] == "fa_mizan_furqan"
                assert theme["title"].strip()
                assert theme["references"]
                for reference in theme["references"]:
                    assert reference.startswith(f"{sid}:")
                    assert theme["title"] in overview_by_reference[reference]
                continue
            assert theme["kind"] == "lexical-witness"
            assert theme["count"] >= len(theme["references"]) > 0
            assert theme["witnesses"] and theme["terms"]
            for reference in theme["references"]:
                assert reference.startswith(f"{sid}:") and reference in records
            reference_text = " ".join(records[reference][2] for reference in theme["references"])
            normalized_reference_text = normalize(reference_text)
            for word in theme["witnesses"]:
                assert normalize(word) in normalized_reference_text, f"{sid}:{theme['title']}: شاهد در مواضع اعلام‌شده نیست"


def test_vocabulary_has_an_exact_quranic_surface_and_a_source_excerpt():
    frequencies = Counter()
    for row in CORPUS:
        if isinstance(row, list):
            frequencies.update(tokens(row[2]))
    records = record_map()
    for sid, dossier in DOSSIERS["surahs"].items():
        seen_surfaces = set()
        for item in dossier["vocabulary"]:
            assert item["sourceId"] in SOURCE_IDS
            assert item["excerpt"].strip()
            assert item["words"]
            context_surah, context_start, context_end = parse_reference(item["reference"])
            assert context_surah == int(sid)
            for word in item["words"]:
                reference = word["reference"]
                verse_surah, ayah, _ = parse_reference(reference)
                assert verse_surah == int(sid) and context_start <= ayah <= context_end
                assert reference in records
                surface = word.get("surface") or word["word"]
                surface_key = normalize(surface)
                assert surface_key in tokens(records[reference][2]), f"{reference}: صورتِ واژه در متنِ آیه نیست"
                assert word["frequency"] == frequencies[surface_key]
                assert surface_key not in seen_surfaces, f"{sid}: صورتِ واژه تکراری است"
                seen_surfaces.add(surface_key)


def test_reflections_attribute_quotes_and_mark_paraphrases():
    registry = {source["id"]: source for source in TAFSIR_REGISTRY}
    for source_id in SOURCE_IDS:
        saved = DOSSIERS["sources"][source_id]
        current = registry[source_id]
        for field in ("title", "version", "sourceUrl"):
            assert saved[field] == current[field]
    for sid, dossier in DOSSIERS["surahs"].items():
        for item in dossier["reflections"]:
            if item["kind"] == "source-quote":
                assert item["sourceId"] in SOURCE_IDS
                assert item["quote"].strip()
                surah, start, end = parse_reference(item["reference"])
                assert surah == int(sid) and 1 <= start <= end <= dossier["verseCount"]
                assert isinstance(item["quoteTruncated"], bool)
            elif item["kind"] == "modern-research-note":
                assert item["sourceId"] == "verse-dossier-research"
                assert item["verbatim"] is False
                assert item["text"].strip() and item["citation"].strip()
                assert parse_reference(item["reference"])[0] == int(sid)
            else:
                raise AssertionError(f"نوع نقل ناشناخته: {item.get('kind')}")

    for sid in ("1", "2"):
        notes = [item for item in DOSSIERS["surahs"][sid]["reflections"] if item["kind"] == "modern-research-note"]
        assert len(notes) <= 5
        assert len({item["citation"] for item in notes}) == len(notes)

    serialized_sources = json.dumps(DOSSIERS["sources"], ensure_ascii=False).lower()
    assert "fa_qe_persian_mokhtasar" not in serialized_sources
    assert "persian-mokhtasar" not in serialized_sources
    assert "ihsan elahi zaheer" not in serialized_sources
    assert all(item.get("sourceId") != "fa_qe_persian_mokhtasar" for dossier in DOSSIERS["surahs"].values() for field in ("overview", "themes", "vocabulary", "reflections") for item in dossier[field])


def test_surah_ui_uses_source_excerpts_and_does_not_use_a_translation_as_a_gloss():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    app = (STATIC / "app.js").read_text(encoding="utf-8")
    service_worker = (STATIC / "sw.js").read_text(encoding="utf-8")
    for tab in ("overview", "themes", "vocabulary", "reflections"):
        assert f'data-surah-tab="{tab}"' in html
    for label in ("نمای کلی سوره", "موضوعات محوری و کلیدی", "مفردات و لغات دشوار", "اقوال مهم و تأمل‌برانگیز"):
        assert label in html or label in app
    assert 'appPath("/static/surah-dossiers.json")' in service_worker
    assert "zehnyar-shell-v77" in service_worker
    assert "surahDossierMeta" in app
    assert "ayahMapping" in (ROOT / "tools" / "build_surah_dossiers.py").read_text(encoding="utf-8")
    assert "--sources-dir" in (ROOT / "tools" / "build_surah_dossiers.py").read_text(encoding="utf-8")
    dossier_renderer = app.split("function renderSurahOverview", 1)[1].split("function renderSurah()", 1)[0]
    assert "record.persian" not in dossier_renderer
    assert "المختصر" not in dossier_renderer
    assert "Ihsan Elahi Zaheer" not in dossier_renderer


def test_homepage_donation_card_is_voluntary_and_card_order_is_explicit():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    app = (STATIC / "app.js").read_text(encoding="utf-8")
    assert 'id="donation-card-number"' in html
    assert '6219 8610 5711 3903' in html
    assert 'data-card-number="6219861057113903"' in html
    assert "به انتخاب و میل خودتان" in html
    assert "6219861057113903" in app


def test_selected_brand_icon_is_consistent_across_web_and_android():
    manifest = json.loads((STATIC / "manifest.webmanifest").read_text(encoding="utf-8"))
    icons = {icon["sizes"]: icon for icon in manifest["icons"]}
    assert icons["192x192"]["src"] == "static/icons/zehnyar-192.png"
    assert icons["512x512"]["src"] == "static/icons/zehnyar-512.png"
    assert all("maskable" in icon["purpose"] for icon in icons.values())
    for size, path in ((192, STATIC / "icons" / "zehnyar-192.png"), (512, STATIC / "icons" / "zehnyar-512.png")):
        data = path.read_bytes()
        assert data.startswith(b"\x89PNG\r\n\x1a\n")
        assert struct.unpack(">II", data[16:24]) == (size, size)

    android_icon = ROOT / "mobile" / "android" / "app" / "src" / "main" / "res" / "drawable-nodpi" / "ic_zehnyar.png"
    assert android_icon.is_file()
    assert struct.unpack(">II", android_icon.read_bytes()[16:24]) == (512, 512)
    android_manifest = ET.parse(ROOT / "mobile" / "android" / "app" / "src" / "main" / "AndroidManifest.xml").getroot()
    application = android_manifest.find("application")
    assert application is not None and application.attrib["{http://schemas.android.com/apk/res/android}icon"] == "@drawable/ic_zehnyar"
    assert not (ROOT / "mobile" / "android" / "app" / "src" / "main" / "res" / "drawable" / "ic_zehnyar.xml").exists()

    svg = ET.parse(STATIC / "icons" / "zehnyar-icon.svg").getroot()
    assert svg.attrib["viewBox"] == "0 0 512 512"
    assert 'static/icons/zehnyar-192.png' in (STATIC / "index.html").read_text(encoding="utf-8")
