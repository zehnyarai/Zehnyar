# -*- coding: utf-8 -*-
"""Coverage and provenance checks for the four-field dossier of all 114 surahs."""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
DOSSIERS = json.loads((STATIC / "surah-dossiers.json").read_text(encoding="utf-8"))
CORPUS = json.loads((STATIC / "offline-corpus.json").read_text(encoding="utf-8"))["verses"]
CHAPTERS = json.loads((ROOT / "data" / "chapters.json").read_text(encoding="utf-8"))["chapters"]
ANNOTATIONS = json.loads((STATIC / "verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
TAFSIR = json.loads((STATIC / "tafsir" / "persian-mokhtasar-quranenc-1.0.0.json").read_text(encoding="utf-8"))
TAFSIR_REGISTRY = json.loads((STATIC / "tafsir-sources.json").read_text(encoding="utf-8"))["sources"]

DIACRITICS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u08d4-\u08ff]")
ARABIC_RUN = re.compile(r"[\u0600-\u06ff]+")
LETTER_MAP = str.maketrans({"ٱ": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ى": "ی", "ي": "ی", "ئ": "ی", "ؤ": "و", "ة": "ه", "ك": "ک", "ـ": " ", "‌": " "})


def normalize(value):
    value = DIACRITICS.sub("", str(value)).translate(LETTER_MAP)
    value = re.sub(r"[^\w\s\u0600-\u06ff]", " ", value).lower()
    return " ".join(value.split())


def tokens(text):
    return [normalize(raw) for raw in ARABIC_RUN.findall(text) if normalize(raw) and " " not in normalize(raw)]


def record_map():
    return {f"{row[0]}:{row[1]}": row for row in CORPUS if isinstance(row, list)}


def test_every_surah_has_all_four_research_fields():
    expected = {str(chapter["id"]) for chapter in CHAPTERS}
    assert set(DOSSIERS["surahs"]) == expected
    assert len(expected) == 114
    for sid, dossier in DOSSIERS["surahs"].items():
        assert dossier["verseCount"] == int(CHAPTERS[int(sid) - 1]["total_verses"])
        assert [point["stage"] for point in dossier["overview"]] == ["آغاز", "میانه", "پایان"]
        assert len(dossier["themes"]) >= 1
        assert len(dossier["vocabulary"]) == 3
        assert len(dossier["reflections"]) == 2


def test_overview_items_are_traceable_to_their_own_verse_notes():
    global_seen_text = set()
    for sid, dossier in DOSSIERS["surahs"].items():
        total = dossier["verseCount"]
        anchors = {point["stage"]: int(point["reference"].split(":")[1]) for point in dossier["overview"]}
        assert set(anchors) == {"آغاز", "میانه", "پایان"}
        assert 1 <= anchors["آغاز"] <= min(total, 6)
        midpoint = (total + 1) // 2
        assert max(1, midpoint - 3) <= anchors["میانه"] <= min(total, midpoint + 3)
        assert max(1, total - 5) <= anchors["پایان"] <= total
        assert len(set(anchors.values())) == 3
        for point in dossier["overview"]:
            reference = point["reference"]
            assert reference.startswith(f"{sid}:")
            annotation = ANNOTATIONS[reference]
            message = annotation["messages"][point["messageIndex"]]
            assert message["text"].strip()
            assert message["evidence"].strip()
            assert message["text"] not in global_seen_text, f"{reference}: یادداشت تکراری در پرونده‌ها"
            global_seen_text.add(message["text"])


def test_theme_labels_expose_verse_witnesses_and_references():
    records = record_map()
    for sid, dossier in DOSSIERS["surahs"].items():
        titles = [theme["title"] for theme in dossier["themes"]]
        assert len(titles) == len(set(titles)), f"{sid}: محور تکراری"
        counts = [theme["count"] for theme in dossier["themes"]]
        assert counts == sorted(counts, reverse=True), f"{sid}: ترتیب بسامد نامعتبر"
        for theme in dossier["themes"]:
            assert theme["count"] >= len(theme["references"]) > 0
            assert theme["witnesses"] and theme["terms"]
            for reference in theme["references"]:
                assert reference.startswith(f"{sid}:")
                assert reference in records
            reference_text = " ".join(records[reference][2] for reference in theme["references"])
            normalized_reference_text = normalize(reference_text)
            for word in theme["witnesses"]:
                assert normalize(word) in normalized_reference_text, f"{sid}:{theme['title']}: شاهد در مواضعِ اعلام‌شده نیست"


def test_vocabulary_entries_are_exact_low_frequency_corpus_forms():
    frequencies = Counter()
    for row in CORPUS:
        if isinstance(row, list):
            frequencies.update(tokens(row[2]))
    records = record_map()
    for sid, dossier in DOSSIERS["surahs"].items():
        seen = set()
        for item in dossier["vocabulary"]:
            reference = item["reference"]
            assert reference.startswith(f"{sid}:") and reference in records
            key = normalize(item["word"])
            assert key in tokens(records[reference][2]), f"{reference}: واژه در متنِ آیه نیست"
            assert key not in seen, f"{sid}: صورتِ واژه تکراری است"
            seen.add(key)
            assert item["frequency"] == frequencies[key]
            assert 1 <= item["frequency"] <= 5


def test_reflections_match_the_exact_local_tafsir_source():
    source = next(item for item in TAFSIR_REGISTRY if item["id"] == "fa_qe_persian_mokhtasar")
    assert DOSSIERS["sources"]["commentary"]["id"] == source["id"]
    assert DOSSIERS["sources"]["commentary"]["version"] == source["version"]
    assert DOSSIERS["sources"]["commentary"]["sourceUrl"] == source["sourceUrl"]
    records = record_map()
    tafsir_verses = TAFSIR["verses"]
    for sid, dossier in DOSSIERS["surahs"].items():
        refs = set()
        for item in dossier["reflections"]:
            assert item["sourceId"] == source["id"]
            reference = item["reference"]
            assert reference.startswith(f"{sid}:") and reference in records
            assert reference not in refs
            refs.add(reference)
            ayah = reference.split(":")[1]
            quote = tafsir_verses[sid][ayah]["text"]
            assert quote.strip()
            assert len(quote.strip()) <= 360


def test_homepage_donation_card_is_voluntary_and_card_order_is_explicit():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    app = (STATIC / "app.js").read_text(encoding="utf-8")
    assert 'id="donation-card-number"' in html
    assert '6219 8610 5711 3903' in html
    assert 'data-card-number="6219861057113903"' in html
    assert "به انتخاب و میل خودتان" in html
    assert "6219861057113903" in app


def test_surah_page_exposes_the_requested_fields_and_offline_data_is_cached():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    service_worker = (STATIC / "sw.js").read_text(encoding="utf-8")
    for tab in ("overview", "themes", "vocabulary", "reflections"):
        assert f'data-surah-tab="{tab}"' in html
    app = (STATIC / "app.js").read_text(encoding="utf-8")
    for label in ("نمای کلی سوره", "موضوعات محوری و کلیدی", "مفردات و لغات دشوار", "اقوال مهم و تأمل‌برانگیز"):
        assert label in html or label in app
    assert 'appPath("/static/surah-dossiers.json")' in service_worker
    assert "build_surah_dossiers.py" in (ROOT / "tools" / "build_surah_dossiers.py").read_text(encoding="utf-8")


def test_selected_brand_icon_is_consistent_across_web_and_android():
    import struct
    import xml.etree.ElementTree as ET

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
    assert "zehnyar-shell-v76" in (STATIC / "sw.js").read_text(encoding="utf-8")
