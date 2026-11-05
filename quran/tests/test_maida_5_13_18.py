# -*- coding: utf-8 -*-
"""Targeted validation for the source-scoped Al-Ma'idah 5:13–18 batch."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = json.loads((ROOT / "static" / "verse-dossiers.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))

SUNNI = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
SHIA = {"ar_tusi_tibyan", "ar_fayd_safi"}
MODERN_COMMON = {"ar_qe_arabic_moyassar", "en_tafheem_ul_quran"}
MODERN_WITH_WASIT = {"ar_qe_arabic_moyassar", "ar_wasit_qurancom"}
MODELS = {"izutsu", "fillmore", "cognitive"}
FIELDS = ("notes", "context", "classical", "modern", "critical", "research")


def _by_source(items):
    return {item["sourceId"]: item for item in items if item.get("sourceId")}


def test_maida_5_13_18_has_six_complete_drafts_and_balanced_source_families():
    expected = {f"5:{ayah}" for ayah in range(13, 19)}
    assert expected <= set(DOSSIER["verses"])
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-49")
    assert batch["range"] == "5:13–18" and batch["count"] == 6
    assert "پیش‌نویسِ نیازمندِ داوریِ تخصصی" in batch["status"]
    assert "در زمانِ ثبتِ این بسته، مائده تا ۵:۱۸ پوشش داشت" in batch["status"]
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    assert "بسته‌های مائده ۵:۱–۶، ۵:۷–۱۲، ۵:۱۳–۱۸، ۵:۱۹–۲۴، ۵:۲۵–۳۰، ۵:۳۱–۳۶، ۵:۳۷–۴۲، ۵:۴۳–۴۸، ۵:۴۹–۵۴، ۵:۵۵–۶۰، ۵:۶۱–۱۱۰ و ۵:۱۱۱–۱۲۰ افزوده شده‌اند" in DOSSIER["notice"]
    assert "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است" in DOSSIER["notice"]
    assert "در بستهٔ مائده ۵:۱۳–۱۸" in DOSSIER["editorialMethod"]
    assert "مودودی یادداشتِ مستقل ندارد" in DOSSIER["editorialMethod"]

    registry_by_id = {item["id"]: item for item in REGISTRY["sources"]}
    assert len(REGISTRY["sources"]) == 15 and REGISTRY["version"] >= 8
    for ayah in range(13, 19):
        vid = f"5:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) == 5 for field in FIELDS), vid
        assert {item["sourceId"] for item in entry["classical"]} == SUNNI | SHIA
        assert sum(item["tradition"] == "اهل‌سنت" for item in entry["classical"]) == 3
        assert sum(item["tradition"] == "شیعهٔ امامیه" for item in entry["classical"]) == 2
        expected_modern = MODERN_WITH_WASIT if ayah in (13, 18) else MODERN_COMMON
        assert {item["sourceId"] for item in entry["modern"] if item.get("kind") == "source-summary"} == expected_modern
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
            assert "چاپ و صفحه" not in record["cite"] or "احراز نشده" in record["cite"]

    assert len(DOSSIER["verses"]) == sum(item["count"] for item in DOSSIER["batches"])
    assert next(item for item in CATALOG["collections"] if item["id"] == "maida-5-13-18-cited")
    assert CATALOG["version"] >= 28


def test_maida_5_13_18_records_actual_grouped_pages_and_modern_commentary_pairs():
    fayd_groups = {
        13: (13, "۵:۸–۱۴"),
        14: (14, "۵:۸–۱۴"),
        15: (15, "۵:۱۵–۱۷"),
        16: (16, "۵:۱۵–۱۷"),
        17: (17, "۵:۱۵–۱۷"),
        18: (18, "۵:۱۸–۲۶"),
    }
    tusi_groups = {
        13: (13, "۵:۱۳"),
        14: (14, "۵:۱۴"),
        15: (15, "۵:۱۵–۱۶"),
        16: (16, "۵:۱۵–۱۶"),
        17: (17, "۵:۱۷"),
        18: (18, "۵:۱۸"),
    }
    note_labels = {
        13: "ترجمهٔ آیه؛ بی‌یادداشتِ مستقل",
        14: "یادداشتِ ۳۶",
        15: "یادداشتِ ۳۷",
        16: "یادداشتِ ۳۸",
        17: "یادداشت‌های ۳۹–۴۰",
        18: "ترجمهٔ آیه؛ بی‌یادداشتِ مستقل",
    }
    for ayah in range(13, 19):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        classical = _by_source(entry["classical"])
        for sid, tafsir_no, groups in (
            ("ar_tusi_tibyan", 39, tusi_groups),
            ("ar_fayd_safi", 41, fayd_groups),
        ):
            record = classical[sid]
            page, scope = groups[ayah]
            assert f"TafsirNo={tafsir_no}&SoraNo=5&AyahNo={page}&LanguageID=1" in record["sourceUrl"]
            assert scope in record["cite"] and scope in record["evidence"]
        assert f"AyahNo={ayah}" in classical["ar_tusi_tibyan"]["cite"]
        for sid, slug in (
            ("ar_tabari_qurancom", "ar-tafsir-al-tabari"),
            ("ar_ibn_kathir_qurancom", "ar-tafsir-ibn-kathir"),
            ("ar_jalalayn_qurancom", "ar-tafsir-jalalayn"),
        ):
            assert classical[sid]["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/{slug}"

        tafheem = TAFHEEM = next(
            record for field in FIELDS for record in entry[field]
            if "مودودی" in record.get("cite", "") and "تفہیم القرآن" in record.get("cite", "")
        )
        assert "verse=12&to=19" in tafheem["cite"] or "۵:۱۲–۱۹" in tafheem["cite"]
        assert note_labels[ayah] in tafheem["cite"]
        modern = _by_source(entry["modern"])
        assert ("en_tafheem_ul_quran" in modern) == (ayah not in (13, 18))
        if ayah in (13, 18):
            wasit = modern["ar_wasit_qurancom"]
            assert wasit["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-al-wasit"
            assert "طنطاوی" in wasit["cite"]
            assert "بی‌یادداشتِ مستقل" in tafheem["cite"]
        else:
            modern_tafheem = modern["en_tafheem_ul_quran"]
            assert note_labels[ayah] in modern_tafheem["cite"]
            assert "۵:۱۲–۱۹" in modern_tafheem["cite"]

    collection = next(item for item in CATALOG["collections"] if item["id"] == "maida-5-13-18-cited")
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ مائده ۵:۱۳–۱۸"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == SUNNI
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == SHIA
    assert "۵:۱۳ و ۵:۱۸" in collection["comparativeCore"]["note"]
    assert "یادداشت‌های ۳۶–۴۰ مودودی" in collection["comparativeCore"]["note"]
    by_id = {item["id"]: item for item in collection["items"]}
    for sid in SUNNI | SHIA:
        assert len(by_id[sid]["sourceUrls"]) == 6
    assert len(by_id["en_tafheem_ul_quran"]["sourceUrls"]) == 1
    assert by_id["en_tafheem_ul_quran"]["scope"] == "مائده ۵:۱۳–۱۸"
    assert len(by_id["ar_qe_arabic_moyassar"]["sourceUrls"]) == 1
    assert set(by_id["ar_wasit_qurancom"]["sourceUrls"]) == {
        f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-al-wasit" for ayah in (13, 18)
    }
    assert by_id["ar_wasit_qurancom"]["scope"] == "مائده ۵:۱۳ و ۵:۱۸"
    assert "یادداشتِ مستقل ندارد" in by_id["en_tafheem_ul_quran"]["basis"]
    assert "ترجمهٔ آن دو شاهدِ مکمل است" in by_id["en_tafheem_ul_quran"]["basis"]
    registry_source = next(item for item in REGISTRY["sources"] if item["id"] == "ar_wasit_qurancom")
    assert registry_source["sourceType"] == "modern-tafsir"


def test_maida_5_13_18_preserves_attribution_and_interpretive_disagreements():
    verses = DOSSIER["verses"]

    s13 = _by_source(verses["5:13"]["classical"])
    assert "قَسِيّة" in s13["ar_tabari_qurancom"]["text"]
    assert "قتاده" in s13["ar_ibn_kathir_qurancom"]["text"]
    assert "بلخی" in s13["ar_tusi_tibyan"]["text"]
    assert "قمی" in s13["ar_fayd_safi"]["text"]
    assert "عفو" in s13["ar_jalalayn_qurancom"]["text"]
    assert "سکهٔ ناخالص" in verses["5:13"]["notes"][0]["text"]

    s14 = _by_source(verses["5:14"]["classical"])
    assert "شمولِ یهود و نصارا" in s14["ar_tabari_qurancom"]["text"]
    assert "تکفیرِ متقابل" in s14["ar_ibn_kathir_qurancom"]["text"]
    assert "الزام" in s14["ar_fayd_safi"]["text"]
    assert "یادداشتِ مستقلِ ۳۶" in _by_source(verses["5:14"]["modern"])["en_tafheem_ul_quran"]["text"]

    s15 = _by_source(verses["5:15"]["classical"])
    assert "نور" in s15["ar_tabari_qurancom"]["text"] and "محمد" in s15["ar_tabari_qurancom"]["text"]
    assert "امیرالمؤمنین" in s15["ar_fayd_safi"]["text"]
    assert "وانهادنِ توضیح" in s15["ar_jalalayn_qurancom"]["text"]
    assert "یادداشتِ ۳۷" in _by_source(verses["5:15"]["modern"])["en_tafheem_ul_quran"]["cite"]

    s16 = _by_source(verses["5:16"]["classical"])
    assert "اسلام و صلح" in s16["ar_tabari_qurancom"]["text"]
    assert "بإذنه" in s16["ar_tusi_tibyan"]["text"]
    assert "عذاب" in s16["ar_fayd_safi"]["text"]

    s17 = _by_source(verses["5:17"]["classical"])
    assert "یعقوبیه" in s17["ar_jalalayn_qurancom"]["text"]
    assert "لحنی جدلی" in s17["ar_ibn_kathir_qurancom"]["text"]
    assert "استدلالِ توحیدی" in s17["ar_tusi_tibyan"]["text"]
    assert "یادداشت‌های مستقلِ ۳۹–۴۰" in _by_source(verses["5:17"]["modern"])["en_tafheem_ul_quran"]["text"]

    s18 = _by_source(verses["5:18"]["classical"])
    assert "قرب" in s18["ar_tabari_qurancom"]["text"]
    assert "نزدیکی" in s18["ar_ibn_kathir_qurancom"]["text"]
    assert "رحمت و شفقت" in s18["ar_jalalayn_qurancom"]["text"]
    assert "آمرزش و کیفر" in s18["ar_tusi_tibyan"]["text"]
    assert "روایی" in s18["ar_fayd_safi"]["text"]

    for ayah in (13, 18):
        entry = verses[f"5:{ayah}"]
        assert "en_tafheem_ul_quran" not in _by_source(entry["modern"])
        assert "ar_wasit_qurancom" in _by_source(entry["modern"])
        assert any(
            "بی‌یادداشتِ مستقل" in record["cite"]
            for field in FIELDS for record in entry[field]
        )
