# -*- coding: utf-8 -*-
"""Targeted source, scope, and attribution checks for Al-Ma'idah 5:19–24."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = json.loads((ROOT / "static" / "verse-dossiers.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))

SUNNI = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
SHIA = {"ar_tusi_tibyan", "ar_fayd_safi"}
QURANENC = "ar_qe_arabic_moyassar"
TAFHEEM = "en_tafheem_ul_quran"
WASIT = "ar_wasit_qurancom"
MODELS = {"izutsu", "fillmore", "cognitive"}
FIELDS = ("notes", "context", "classical", "modern", "critical", "research")

TAFHEEM_GROUPS = {
    19: ("۵:۱۲–۱۹", "verse=12&to=19", "یادداشتِ ۴۱"),
    20: ("۵:۲۰–۲۶", "verse=20&to=26", "یادداشتِ ۴۲"),
    21: ("۵:۲۰–۲۶", "verse=20&to=26", "یادداشت‌های ۴۳–۴۴"),
    22: ("۵:۲۰–۲۶", "verse=20&to=26", "ترجمهٔ آیه؛ بی‌یادداشتِ مستقل"),
    23: ("۵:۲۰–۲۶", "verse=20&to=26", "یادداشتِ ۴۵"),
    24: ("۵:۲۰–۲۶", "verse=20&to=26", "ترجمهٔ آیه؛ بی‌یادداشتِ مستقل"),
}


def _by_source(items):
    return {item["sourceId"]: item for item in items if item.get("sourceId")}


def test_maida_5_19_24_has_six_complete_balanced_drafts():
    expected = {f"5:{ayah}" for ayah in range(19, 25)}
    assert expected <= set(DOSSIER["verses"])
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-50")
    assert batch["range"] == "5:19–24" and batch["count"] == 6
    assert "پیش‌نویسِ نیازمندِ داوریِ تخصصی" in batch["status"]
    assert "در زمانِ ثبتِ این بسته، مائده تا ۵:۲۴ پوشش داشت" in batch["status"]
    assert "ادامهٔ سوره نیازمندِ تکمیل بود" in batch["status"]
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    assert "بسته‌های مائده ۵:۱–۶، ۵:۷–۱۲، ۵:۱۳–۱۸، ۵:۱۹–۲۴، ۵:۲۵–۳۰، ۵:۳۱–۳۶، ۵:۳۷–۴۲، ۵:۴۳–۴۸، ۵:۴۹–۵۴، ۵:۵۵–۶۰، ۵:۶۱–۱۱۰ و ۵:۱۱۱–۱۲۰ افزوده شده‌اند" in DOSSIER["notice"]
    assert "در بستهٔ مائده ۵:۱۹–۲۴" in DOSSIER["editorialMethod"]
    assert "۵:۱۲–۱۹ برای ۵:۱۹ و ۵:۲۰–۲۶ برای ۵:۲۰–۲۴" in DOSSIER["editorialMethod"]
    assert "فرمانِ رفتن به مصر و فتحِ آن" in DOSSIER["editorialMethod"]

    registry_by_id = {item["id"]: item for item in REGISTRY["sources"]}
    assert len(REGISTRY["sources"]) == 15 and REGISTRY["version"] >= 8
    for ayah in range(19, 25):
        vid = f"5:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) == 5 for field in FIELDS), vid
        assert {item["sourceId"] for item in entry["classical"]} == SUNNI | SHIA
        assert sum(item["tradition"] == "اهل‌سنت" for item in entry["classical"]) == 3
        assert sum(item["tradition"] == "شیعهٔ امامیه" for item in entry["classical"]) == 2
        modern = _by_source(entry["modern"])
        expected_modern = {QURANENC, WASIT} if ayah in (22, 24) else {QURANENC, TAFHEEM}
        assert set(modern) == expected_modern
        assert {item["model"] for item in entry["modern"] if item.get("model")} == MODELS
        for field in FIELDS:
            for record in entry[field]:
                assert len(record["text"].split()) >= 14, f"{vid}:{field}: بند کوتاه"
                assert record["cite"].strip(), f"{vid}:{field}: ارجاع خالی"
                if record.get("sourceUrl"):
                    assert record["sourceUrl"].startswith("https://")
        for record in entry["classical"] + [x for x in entry["modern"] if x.get("kind") == "source-summary"]:
            sid = record["sourceId"]
            assert sid in registry_by_id, f"{vid}: منبع در رجیستری نیست: {sid}"
            assert record["tradition"] == registry_by_id[sid]["tradition"]
            assert record["evidence"].strip() and record["limit"].strip()


def test_maida_5_19_24_records_direct_and_real_grouped_source_ranges():
    for ayah in range(19, 25):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        classical = _by_source(entry["classical"])
        for sid, slug in (
            ("ar_tabari_qurancom", "ar-tafsir-al-tabari"),
            ("ar_ibn_kathir_qurancom", "ar-tafsir-ibn-kathir"),
            ("ar_jalalayn_qurancom", "ar-tafsir-jalalayn"),
        ):
            assert classical[sid]["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/{slug}"
        tusi = classical["ar_tusi_tibyan"]
        assert f"TafsirNo=39&SoraNo=5&AyahNo={ayah}&LanguageID=1" in tusi["sourceUrl"]
        assert f"AyahNo={ayah}" in tusi["cite"]
        fayd = classical["ar_fayd_safi"]
        assert f"TafsirNo=41&SoraNo=5&AyahNo={ayah}&LanguageID=1" in fayd["sourceUrl"]
        assert "۵:۱۸–۲۶" in fayd["cite"] and "۵:۱۸–۲۶" in fayd["evidence"]

        modern = _by_source(entry["modern"])
        scope, query, note = TAFHEEM_GROUPS[ayah]
        if ayah in (22, 24):
            tafheem_ref = next(
                record for field in FIELDS for record in entry[field]
                if "مودودی" in record.get("cite", "") and "تفہیم القرآن" in record.get("cite", "")
            )
            assert TAFHEEM not in modern
            assert scope in tafheem_ref["cite"] and note in tafheem_ref["cite"]
            assert "بی‌یادداشتِ مستقل" in tafheem_ref["cite"]
            wasit = modern[WASIT]
            assert wasit["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-al-wasit"
            assert "طنطاوی" in wasit["cite"]
        else:
            tafheem = modern[TAFHEEM]
            assert query in tafheem["sourceUrl"]
            assert scope in tafheem["cite"] and scope in tafheem["evidence"]
            assert note in tafheem["cite"]
            assert WASIT not in modern
        assert modern[QURANENC]["sourceUrl"].startswith("https://")

    collection = next(item for item in CATALOG["collections"] if item["id"] == "maida-5-19-24-cited")
    assert CATALOG["version"] >= 28
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ مائده ۵:۱۹–۲۴"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == SUNNI
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == SHIA
    by_id = {item["id"]: item for item in collection["items"]}
    assert set(by_id) == SUNNI | SHIA | {QURANENC, TAFHEEM, WASIT}
    assert len(by_id[TAFHEEM]["sourceUrls"]) == 2
    assert set(by_id[TAFHEEM]["sourceUrls"]) == {
        "https://www.islamicstudies.info/tafheem.php?sura=5&verse=12&to=19",
        "https://www.islamicstudies.info/tafheem.php?sura=5&verse=20&to=26",
    }
    assert "۵:۱۲–۱۹" in by_id[TAFHEEM]["basis"] and "۵:۲۰–۲۶" in by_id[TAFHEEM]["basis"]
    assert "۵:۲۲ و ۵:۲۴ فقط ترجمه دارند" in by_id[TAFHEEM]["basis"]
    assert set(by_id[WASIT]["sourceUrls"]) == {
        f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-al-wasit" for ayah in (22, 24)
    }
    assert by_id[WASIT]["scope"] == "مائده ۵:۲۲ و ۵:۲۴"
    assert "دامنه‌های واقعیِ مودودی" in collection["comparativeCore"]["note"]
    assert REGISTRY["version"] >= 8 and len(REGISTRY["sources"]) == 15


def test_maida_5_19_24_keeps_disagreements_and_attributions_visible():
    verses = DOSSIER["verses"]

    v19 = _by_source(verses["5:19"]["classical"])
    assert "فترة" in v19["ar_tabari_qurancom"]["text"]
    assert "اوصیای پنهان" in v19["ar_fayd_safi"]["text"]
    assert "۵۶۹" in v19["ar_jalalayn_qurancom"]["text"]
    assert "۵:۱۲–۱۹" in _by_source(verses["5:19"]["modern"])[TAFHEEM]["cite"]

    v20 = _by_source(verses["5:20"]["classical"])
    assert "ملوک" in v20["ar_tabari_qurancom"]["text"]
    assert "زمانِ موسی" in v20["ar_tabari_qurancom"]["text"]
    assert "مصر" in _by_source(verses["5:20"]["modern"])[TAFHEEM]["text"]

    v21 = verses["5:21"]
    assert "فلسطین" in _by_source(v21["classical"])["ar_tusi_tibyan"]["text"]
    assert "از رفتن به مصر و فتحِ آن" in _by_source(v21["modern"])[TAFHEEM]["text"]
    assert "سیاستِ امروز" in " ".join(record["text"] for record in v21["critical"])

    v22 = verses["5:22"]
    assert "کذب" in _by_source(v22["classical"])["ar_ibn_kathir_qurancom"]["text"]
    assert "بی‌یادداشتِ مستقل" in _by_source(v22["classical"])["ar_tabari_qurancom"]["cite"] or any(
        "بی‌یادداشتِ مستقل" in record["cite"] for field in FIELDS for record in v22[field]
    )
    assert "داوریِ جدلی" in _by_source(v22["modern"])[WASIT]["text"]
    assert "en_tafheem_ul_quran" not in _by_source(v22["modern"])

    v23 = verses["5:23"]
    assert "قرائتِ مشهور" in _by_source(v23["classical"])["ar_tabari_qurancom"]["text"]
    assert "ویراستار" in _by_source(v23["modern"])[TAFHEEM]["text"]
    assert "یادداشتِ ۴۵" in _by_source(v23["modern"])[TAFHEEM]["cite"]

    v24 = verses["5:24"]
    assert "بدر" in _by_source(v24["classical"])["ar_tabari_qurancom"]["text"]
    assert "نحوی" in _by_source(v24["classical"])["ar_tusi_tibyan"]["text"]
    assert "سه تأکید" in _by_source(v24["modern"])[WASIT]["text"]
    assert "بی‌یادداشتِ مستقل" in next(
        record for field in FIELDS for record in v24[field]
        if "مودودی" in record.get("cite", "") and "تفہیم القرآن" in record.get("cite", "")
    )["cite"]
    assert "5:26" not in " ".join(record["cite"] for record in v24["modern"])
