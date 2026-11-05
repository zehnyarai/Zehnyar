# -*- coding: utf-8 -*-
"""Targeted validation for the source-scoped Al-Ma'idah 5:1–6 batch."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = json.loads((ROOT / "static" / "verse-dossiers.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))

SUNNI = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
SHIA = {"ar_tusi_tibyan", "ar_fayd_safi"}
MODERN = {"ar_qe_arabic_moyassar", "en_tafheem_ul_quran"}
MODELS = {"izutsu", "fillmore", "cognitive"}
FIELDS = ("notes", "context", "classical", "modern", "critical", "research")


def _by_source(items):
    return {item["sourceId"]: item for item in items if item.get("sourceId")}


def test_maida_5_1_6_has_complete_drafts_and_balanced_source_families():
    expected = {f"5:{ayah}" for ayah in range(1, 7)}
    assert expected <= set(DOSSIER["verses"])
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-47")
    assert batch["range"] == "5:1–6" and batch["count"] == 6
    assert "پیش‌نویسِ نیازمندِ داوریِ تخصصی" in batch["status"]
    assert "نساء ۴:۱–۱۷۶ پوشش دارد" in batch["status"]
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    assert "بسته‌های مائده ۵:۱–۶، ۵:۷–۱۲، ۵:۱۳–۱۸، ۵:۱۹–۲۴، ۵:۲۵–۳۰، ۵:۳۱–۳۶، ۵:۳۷–۴۲، ۵:۴۳–۴۸، ۵:۴۹–۵۴، ۵:۵۵–۶۰، ۵:۶۱–۱۱۰ و ۵:۱۱۱–۱۲۰ افزوده شده‌اند" in DOSSIER["notice"]
    assert "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است" in DOSSIER["notice"]

    registry_by_id = {item["id"]: item for item in REGISTRY["sources"]}
    for ayah in range(1, 7):
        vid = f"5:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) == 5 for field in FIELDS), vid
        assert {item["sourceId"] for item in entry["classical"]} == SUNNI | SHIA
        assert sum(item["tradition"] == "اهل‌سنت" for item in entry["classical"]) == 3
        assert sum(item["tradition"] == "شیعهٔ امامیه" for item in entry["classical"]) == 2
        assert {item["sourceId"] for item in entry["modern"] if item.get("kind") == "source-summary"} == MODERN
        assert {item["model"] for item in entry["modern"] if item.get("model")} == MODELS
        assert any("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid

        for field in FIELDS:
            for record in entry[field]:
                assert len(record["text"].split()) >= 14, f"{vid}:{field}: بند کوتاه"
                assert record["cite"].strip(), f"{vid}:{field}: ارجاع خالی"
                if record.get("sourceUrl"):
                    assert record["sourceUrl"].startswith("https://")

        for record in entry["classical"] + [x for x in entry["modern"] if x.get("kind") == "source-summary"]:
            sid = record["sourceId"]
            assert sid in registry_by_id
            assert record["tradition"] == registry_by_id[sid]["tradition"]
            assert record["evidence"].strip() and record["limit"].strip()


def test_maida_5_1_6_records_actual_page_ranges_and_note_scopes():
    fayd_groups = {
        1: (1, "۵:۱–۳"),
        2: (2, "۵:۱–۳"),
        3: (3, "۵:۱–۳"),
        4: (4, "۵:۴–۵"),
        5: (5, "۵:۴–۵"),
        6: (6, "۵:۶–۷"),
    }
    tafheem_groups = {
        **{ayah: ("۵:۱–۵", "verse=1&to=5") for ayah in range(1, 6)},
        6: ("۵:۶–۱۱", "verse=6&to=11"),
    }
    tafheem_notes = {
        1: "یادداشت‌های ۱–۴",
        2: "یادداشت‌های ۵–۸",
        3: "یادداشت‌های ۹–۱۷",
        4: "یادداشت‌های ۱۸–۲۰",
        5: "یادداشت‌های ۲۱–۲۳",
        6: "یادداشت‌های ۲۴–۲۷",
    }
    for ayah in range(1, 7):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        classical = _by_source(entry["classical"])
        for sid, tafsir_no in (("ar_tusi_tibyan", 39), ("ar_fayd_safi", 41)):
            record = classical[sid]
            page = ayah if sid == "ar_tusi_tibyan" else fayd_groups[ayah][0]
            assert f"TafsirNo={tafsir_no}&SoraNo=5&AyahNo={page}&LanguageID=1" in record["sourceUrl"]
        tusi = classical["ar_tusi_tibyan"]
        assert f"AyahNo={ayah}" in tusi["cite"] and "GreatTafsirs" in tusi["cite"]
        fayd = classical["ar_fayd_safi"]
        scope = fayd_groups[ayah][1]
        assert scope in fayd["cite"] and scope in fayd["evidence"]
        if ayah == 2:
            assert "۵:۱–۳" in fayd["cite"] and "۵:۲–۶" not in fayd["cite"] + fayd["evidence"]

        tafheem = _by_source(entry["modern"])["en_tafheem_ul_quran"]
        scope, query = tafheem_groups[ayah]
        assert query in tafheem["sourceUrl"]
        assert scope in tafheem["cite"] and scope in tafheem["evidence"]
        assert tafheem_notes[ayah] in tafheem["cite"]

        for sid in SUNNI:
            assert f"/al-maidah/{ayah}/tafsirs/" in classical[sid]["sourceUrl"]

    collection = next(item for item in CATALOG["collections"] if item["id"] == "maida-5-1-6-cited")
    assert CATALOG["version"] >= 26
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ مائده ۵:۱–۶"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == SUNNI
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == SHIA
    assert all(item["scope"] == "مائده ۵:۱–۶" for item in collection["items"])
    by_id = {item["id"]: item for item in collection["items"]}
    assert len(by_id["ar_tabari_qurancom"]["sourceUrls"]) == 6
    assert len(by_id["ar_ibn_kathir_qurancom"]["sourceUrls"]) == 6
    assert len(by_id["ar_jalalayn_qurancom"]["sourceUrls"]) == 6
    assert len(by_id["ar_tusi_tibyan"]["sourceUrls"]) == 6
    assert len(by_id["ar_fayd_safi"]["sourceUrls"]) == 6
    assert "AyahNo=2" in by_id["ar_fayd_safi"]["basis"]
    assert "نه ۵:۲–۶" in by_id["ar_fayd_safi"]["basis"]
    assert len(by_id["en_tafheem_ul_quran"]["sourceUrls"]) == 2


def test_maida_5_1_6_keeps_theological_and_jurisprudential_disagreements_attributed():
    verses = DOSSIER["verses"]
    assert "ولایتِ علی" in _by_source(verses["5:1"]["classical"])["ar_fayd_safi"]["text"]
    assert "هفت تقریر" in _by_source(verses["5:2"]["classical"])["ar_tabari_qurancom"]["text"]
    assert "عدمِ نسخ" in _by_source(verses["5:2"]["classical"])["ar_fayd_safi"]["text"]
    assert "غدیر" in _by_source(verses["5:3"]["classical"])["ar_fayd_safi"]["text"]
    assert "باز و شاهین" in _by_source(verses["5:4"]["classical"])["ar_tusi_tibyan"]["text"]
    assert "حبوب" in _by_source(verses["5:5"]["classical"])["ar_fayd_safi"]["text"]
    assert "نکاحِ دائم" in _by_source(verses["5:5"]["classical"])["ar_tusi_tibyan"]["text"]
    assert "مسحِ پا" in _by_source(verses["5:6"]["classical"])["ar_tusi_tibyan"]["text"]
    assert "شستنِ پا" in _by_source(verses["5:6"]["classical"])["ar_ibn_kathir_qurancom"]["text"]
    assert "در بستهٔ مائده ۵:۱–۶" in DOSSIER["editorialMethod"]
