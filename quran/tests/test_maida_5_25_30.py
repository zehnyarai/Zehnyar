# -*- coding: utf-8 -*-
"""Targeted source, scope, disagreement, and attribution checks for Al-Ma'idah 5:25–30."""
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
    25: ("۵:۲۰–۲۶", "verse=20&to=26", "ترجمهٔ آیه؛ بی‌یادداشتِ مستقل"),
    26: ("۵:۲۰–۲۶", "verse=20&to=26", "یادداشت‌های ۴۶–۴۷"),
    27: ("۵:۲۷–۳۴", "verse=27&to=34", "یادداشتِ ۴۸"),
    28: ("۵:۲۷–۳۴", "verse=27&to=34", "یادداشتِ ۴۹"),
    29: ("۵:۲۷–۳۴", "verse=27&to=34", "یادداشتِ ۵۰"),
    30: ("۵:۲۷–۳۴", "verse=27&to=34", "ترجمهٔ آیه؛ بی‌یادداشتِ مستقل"),
}
TUSI_GROUPS = {
    25: (25, "۵:۲۵"), 26: (26, "۵:۲۶"),
    27: (27, "۵:۲۷–۲۸"), 28: (27, "۵:۲۷–۲۸"),
    29: (29, "۵:۲۹"), 30: (30, "۵:۳۰"),
}
FAYD_GROUPS = {
    25: (25, "۵:۱۸–۲۶"), 26: (25, "۵:۱۸–۲۶"),
    27: (27, "۵:۲۷–۳۰"), 28: (27, "۵:۲۷–۳۰"),
    29: (27, "۵:۲۷–۳۰"), 30: (27, "۵:۲۷–۳۰"),
}


def _by_source(items):
    return {item["sourceId"]: item for item in items if item.get("sourceId")}


def _all_records(entry):
    return [record for field in FIELDS for record in entry[field]]


def test_maida_5_25_30_has_six_complete_balanced_drafts():
    expected = {f"5:{ayah}" for ayah in range(25, 31)}
    assert expected <= set(DOSSIER["verses"])
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-51")
    assert batch["range"] == "5:25–30" and batch["count"] == 6
    assert "پیش‌نویسِ نیازمندِ داوریِ تخصصی" in batch["status"]
    assert "در زمانِ ثبتِ این بسته، مائده تا ۵:۳۰ پوشش داشت" in batch["status"]
    assert "ادامهٔ سوره نیازمندِ تکمیل بود" in batch["status"]
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    assert "۵:۱۹–۲۴، ۵:۲۵–۳۰، ۵:۳۱–۳۶، ۵:۳۷–۴۲، ۵:۴۳–۴۸، ۵:۴۹–۵۴، ۵:۵۵–۶۰، ۵:۶۱–۱۱۰ و ۵:۱۱۱–۱۲۰ افزوده شده‌اند" in DOSSIER["notice"]
    assert "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است" in DOSSIER["notice"]
    assert "در بستهٔ مائده ۵:۲۵–۳۰" in DOSSIER["editorialMethod"]
    assert "بازبینیِ تخصصی" in DOSSIER["editorialMethod"]

    batch50 = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-50")
    assert "در زمانِ ثبتِ این بسته، مائده تا ۵:۲۴ پوشش داشت" in batch50["status"]

    registry_by_id = {item["id"]: item for item in REGISTRY["sources"]}
    assert len(REGISTRY["sources"]) == 15 and REGISTRY["version"] >= 8
    for ayah in range(25, 31):
        vid = f"5:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) == 5 for field in FIELDS), vid
        assert {item["sourceId"] for item in entry["classical"]} == SUNNI | SHIA
        assert sum(item["tradition"] == "اهل‌سنت" for item in entry["classical"]) == 3
        assert sum(item["tradition"] == "شیعهٔ امامیه" for item in entry["classical"]) == 2
        modern_sources = {item["sourceId"] for item in entry["modern"] if item.get("sourceId")}
        expected_modern = {QURANENC, WASIT} if ayah in (25, 30) else {QURANENC, TAFHEEM}
        assert modern_sources == expected_modern, (vid, modern_sources)
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
            assert "چاپ و صفحه" not in record["cite"] or "احراز نشده" in record["cite"]


def test_maida_5_25_30_records_actual_direct_and_grouped_source_ranges():
    for ayah in range(25, 31):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        classical = _by_source(entry["classical"])
        for source_id, slug in (
            ("ar_tabari_qurancom", "ar-tafsir-al-tabari"),
            ("ar_ibn_kathir_qurancom", "ar-tafsir-ibn-kathir"),
            ("ar_jalalayn_qurancom", "ar-tafsir-jalalayn"),
        ):
            assert classical[source_id]["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/{slug}"

        page, scope = TUSI_GROUPS[ayah]
        tusi = classical["ar_tusi_tibyan"]
        assert f"TafsirNo=39&SoraNo=5&AyahNo={page}&LanguageID=1" in tusi["sourceUrl"]
        assert scope in tusi["cite"] and scope in tusi["evidence"]
        page, scope = FAYD_GROUPS[ayah]
        fayd = classical["ar_fayd_safi"]
        assert f"TafsirNo=41&SoraNo=5&AyahNo={page}&LanguageID=1" in fayd["sourceUrl"]
        assert scope in fayd["cite"] and scope in fayd["evidence"]

        modern = _by_source(entry["modern"])
        group, query, note = TAFHEEM_GROUPS[ayah]
        if ayah in (25, 30):
            assert TAFHEEM not in modern
            maududi_reference = next(
                record for record in _all_records(entry)
                if "مودودی" in record.get("cite", "") and "تفہیم القرآن" in record.get("cite", "")
            )
            assert group in maududi_reference["cite"]
            assert note in maududi_reference["cite"] and "بی‌یادداشتِ مستقل" in note
            wasit = modern[WASIT]
            assert wasit["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-al-wasit"
        else:
            tafheem = modern[TAFHEEM]
            assert query in tafheem["sourceUrl"]
            assert group in tafheem["cite"] and group in tafheem["evidence"]
            assert note in tafheem["cite"]
            assert WASIT not in modern
        assert modern[QURANENC]["sourceUrl"] == "https://quranenc.com/en/browse/arabic_moyassar"

    collection = next(item for item in CATALOG["collections"] if item["id"] == "maida-5-25-30-cited")
    assert CATALOG["version"] >= 29
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ مائده ۵:۲۵–۳۰"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == SUNNI
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == SHIA
    by_id = {item["id"]: item for item in collection["items"]}
    assert set(by_id) == SUNNI | SHIA | {QURANENC, TAFHEEM, WASIT}
    assert set(by_id[TAFHEEM]["sourceUrls"]) == {
        "https://www.islamicstudies.info/tafheem.php?sura=5&verse=20&to=26",
        "https://www.islamicstudies.info/tafheem.php?sura=5&verse=27&to=34",
    }
    assert "۴۶–۴۷" in by_id[TAFHEEM]["basis"] and "۵۱–۵۲" in by_id[TAFHEEM]["basis"]
    assert set(by_id[WASIT]["sourceUrls"]) == {
        "https://quran.com/al-maidah/25/tafsirs/ar-tafsir-al-wasit",
        "https://quran.com/al-maidah/30/tafsirs/ar-tafsir-al-wasit",
    }
    assert set(by_id["ar_fayd_safi"]["sourceUrls"]) == {
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=41&SoraNo=5&AyahNo=25&LanguageID=1",
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=41&SoraNo=5&AyahNo=27&LanguageID=1",
    }
    assert by_id[WASIT]["scope"] == "مائده ۵:۲۵ و ۵:۳۰"
    assert REGISTRY["version"] >= 8 and len(REGISTRY["sources"]) == 15


def test_maida_5_25_30_keeps_disagreements_and_attributions_visible():
    verses = DOSSIER["verses"]

    v25 = verses["5:25"]
    v25_classical = _by_source(v25["classical"])
    assert "چهار وجه" in v25_classical["ar_tusi_tibyan"]["text"]
    assert "شرحِ مستقل" in v25_classical["ar_fayd_safi"]["text"]
    assert "هارون" in v25_classical["ar_tabari_qurancom"]["text"]
    assert "داوری" in v25_classical["ar_tabari_qurancom"]["text"]

    v26 = verses["5:26"]
    v26_classical = _by_source(v26["classical"])
    assert "ترجیح می‌دهد" in v26_classical["ar_tabari_qurancom"]["text"]
    assert "تکلیفی" in v26_classical["ar_tusi_tibyan"]["text"]
    assert "اغراق" in v26_classical["ar_tabari_qurancom"]["text"]
    assert "یادداشتِ ۴۶" in _by_source(v26["modern"])[TAFHEEM]["text"]
    assert "مصر" in v26_classical["ar_fayd_safi"]["text"]

    v27 = verses["5:27"]
    v27_classical = _by_source(v27["classical"])
    assert "دو مرد از بنی‌اسرائیل" in v27_classical["ar_tabari_qurancom"]["text"]
    assert "رد می‌کند" in v27_classical["ar_tabari_qurancom"]["text"]
    assert "وصایت" in v27_classical["ar_fayd_safi"]["text"]
    assert "یادداشتِ ۴۸" in _by_source(v27["modern"])[TAFHEEM]["text"]

    v28 = verses["5:28"]
    v28_classical = _by_source(v28["classical"])
    assert "اثبات نمی‌کند" in v28_classical["ar_tabari_qurancom"]["text"]
    assert "دو قول" in v28_classical["ar_tusi_tibyan"]["text"]
    assert "یادداشتِ ۴۹" in _by_source(v28["modern"])[TAFHEEM]["text"]

    v29 = verses["5:29"]
    v29_classical = _by_source(v29["classical"])
    assert "انتقالِ گناهِ مقتول را" in v29_classical["ar_tabari_qurancom"]["text"]
    assert "بی‌اصل" in v29_classical["ar_ibn_kathir_qurancom"]["text"]
    assert "امام باقر" in v29_classical["ar_fayd_safi"]["text"]
    assert "یادداشتِ ۵۰" in _by_source(v29["modern"])[TAFHEEM]["text"]

    v30 = verses["5:30"]
    v30_classical = _by_source(v30["classical"])
    assert "خبرِ قطعی" in v30_classical["ar_tabari_qurancom"]["text"]
    assert "خفه‌کردن" in v30_classical["ar_ibn_kathir_qurancom"]["text"]
    assert "صبح" in v30_classical["ar_tusi_tibyan"]["text"]
    assert TAFHEEM not in _by_source(v30["modern"])
    assert "۵۱–۵۲" in " ".join(record["text"] for record in _all_records(v30))
    assert "۵:۲۷–۳۱" in " ".join(record["cite"] for record in v30["context"])


def test_maida_5_25_30_model_applications_are_separate_limited_analyses():
    for ayah in range(25, 31):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        model_records = {record["model"]: record for record in entry["modern"] if record.get("model")}
        assert set(model_records) == MODELS
        assert "تحریریِ چارچوب" in " ".join(record["limit"] for record in model_records.values())
        assert len({record["text"] for record in model_records.values()}) == 3
        assert all(record["cite"] and record["evidence"] for record in model_records.values())
        assert "ایزوتسو" not in model_records["fillmore"]["cite"]


def test_maida_5_25_30_prevents_unsupported_scope_and_page_claims():
    for ayah in range(25, 31):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        text = " ".join(record["text"] for record in _all_records(entry))
        cites = " ".join(record["cite"] for record in _all_records(entry))
        assert "پیش‌نویس" in entry["status"]
        assert "صفحه" not in cites or "احراز نشده" in cites or "Quran.com" in cites or "GreatTafsirs" in cites
        if ayah in (25, 30):
            assert any("بی‌یادداشتِ مستقل" in (record["text"] + " " + record["cite"]) for record in _all_records(entry))
    assert "5:31" not in " ".join(
        record["cite"] for ayah in range(25, 31) for record in DOSSIER["verses"][f"5:{ayah}"]["modern"]
    )
