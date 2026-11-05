# -*- coding: utf-8 -*-
"""Targeted source, scope, disagreement, and attribution checks for Al-Ma'idah 5:31–36."""
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

TUSI_GROUPS = {
    31: (31, "۵:۳۱"), 32: (32, "۵:۳۲"), 33: (33, "۵:۳۳"),
    34: (34, "۵:۳۴"), 35: (35, "۵:۳۵"), 36: (36, "۵:۳۶–۳۷"),
}
FAYD_GROUPS = {
    31: (31, "۵:۳۱"), 32: (33, "۵:۳۲–۳۳"), 33: (33, "۵:۳۲–۳۳"),
    34: (35, "۵:۳۴–۳۸"), 35: (35, "۵:۳۴–۳۸"), 36: (35, "۵:۳۴–۳۸"),
}
TAFHEEM_GROUPS = {
    31: ("۵:۲۷–۳۴", "verse=27&to=34", "یادداشت‌های ۵۱–۵۲"),
    32: ("۵:۲۷–۳۴", "verse=27&to=34", "یادداشت‌های ۵۳–۵۴"),
    33: ("۵:۲۷–۳۴", "verse=27&to=34", "یادداشت‌های ۵۵–۵۶"),
    34: ("۵:۲۷–۳۴", "verse=27&to=34", "یادداشتِ ۵۷"),
    35: ("۵:۳۵–۳۶", "verse=35&to=36", "یادداشت‌های ۵۸–۵۹ ذیلِ ۵:۳۵"),
    36: ("۵:۳۵–۳۶", "verse=35&to=36", "ترجمهٔ آیه؛ بی‌یادداشتِ مستقل برای ۵:۳۶"),
}


def _by_source(items):
    return {item["sourceId"]: item for item in items if item.get("sourceId")}


def _all_records(entry):
    return [record for field in FIELDS for record in entry[field]]


def test_maida_5_31_36_has_six_complete_balanced_drafts():
    expected = {f"5:{ayah}" for ayah in range(31, 37)}
    assert expected <= set(DOSSIER["verses"])
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-52")
    assert batch["range"] == "5:31–36" and batch["count"] == 6
    assert "پیش‌نویسِ نیازمندِ داوریِ تخصصی" in batch["status"]
    assert "در زمانِ ثبتِ این بسته، مائده تا ۵:۳۶ پوشش داشت" in batch["status"]
    assert "ادامهٔ سوره نیازمندِ تکمیل بود" in batch["status"]
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    assert "۵:۲۵–۳۰، ۵:۳۱–۳۶، ۵:۳۷–۴۲، ۵:۴۳–۴۸، ۵:۴۹–۵۴، ۵:۵۵–۶۰، ۵:۶۱–۱۱۰ و ۵:۱۱۱–۱۲۰ افزوده شده‌اند" in DOSSIER["notice"]
    assert "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است" in DOSSIER["notice"]
    assert "در بستهٔ مائده ۵:۳۱–۳۶" in DOSSIER["editorialMethod"]
    assert "ادعاهای تلمودیِ مودودی مستقلاً مقابله نشده‌اند" in DOSSIER["editorialMethod"]

    batch51 = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-51")
    assert "در زمانِ ثبتِ این بسته، مائده تا ۵:۳۰ پوشش داشت" in batch51["status"]

    registry_by_id = {item["id"]: item for item in REGISTRY["sources"]}
    assert len(REGISTRY["sources"]) == 15 and REGISTRY["version"] >= 8
    for ayah in range(31, 37):
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
        expected_modern = {QURANENC, WASIT} if ayah == 36 else {TAFHEEM, WASIT}
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


def test_maida_5_31_36_records_actual_direct_and_grouped_source_ranges():
    for ayah in range(31, 37):
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
        if ayah == 36:
            assert TAFHEEM not in modern
            maududi_reference = next(
                record for record in _all_records(entry)
                if "مودودی" in record.get("cite", "") and "تفہیم القرآن" in record.get("cite", "")
            )
            assert group in maududi_reference["cite"]
            assert note in maududi_reference["cite"]
            assert "بی‌یادداشتِ مستقل" in maududi_reference["cite"]
            assert modern[QURANENC]["sourceUrl"] == "https://quranenc.com/en/browse/arabic_moyassar"
        else:
            tafheem = modern[TAFHEEM]
            assert query in tafheem["sourceUrl"]
            assert group in tafheem["cite"] and group in tafheem["evidence"]
            assert note in tafheem["cite"]
        assert modern[WASIT]["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-al-wasit"

    collection = next(item for item in CATALOG["collections"] if item["id"] == "maida-5-31-36-cited")
    assert CATALOG["version"] >= 30
    assert len(CATALOG["collections"]) >= 37
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ مائده ۵:۳۱–۳۶"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == SUNNI
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == SHIA
    by_id = {item["id"]: item for item in collection["items"]}
    assert set(by_id) == SUNNI | SHIA | {QURANENC, TAFHEEM, WASIT}
    assert set(by_id[TAFHEEM]["sourceUrls"]) == {
        "https://www.islamicstudies.info/tafheem.php?sura=5&verse=27&to=34",
        "https://www.islamicstudies.info/tafheem.php?sura=5&verse=35&to=36",
    }
    assert set(by_id["ar_tusi_tibyan"]["sourceUrls"]) == {
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=39&SoraNo=5&AyahNo=31&LanguageID=1",
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=39&SoraNo=5&AyahNo=32&LanguageID=1",
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=39&SoraNo=5&AyahNo=33&LanguageID=1",
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=39&SoraNo=5&AyahNo=34&LanguageID=1",
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=39&SoraNo=5&AyahNo=35&LanguageID=1",
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=39&SoraNo=5&AyahNo=36&LanguageID=1",
    }
    assert "صفحه‌های مستقیمِ ۵:۳۱–۳۵" in by_id["ar_tusi_tibyan"]["scope"]
    assert "صفحهٔ گروهیِ ۵:۳۶–۳۷" in by_id["ar_tusi_tibyan"]["scope"]
    assert "۵۱–۵۷" in by_id[TAFHEEM]["basis"]
    assert "۵۸–۵۹" in by_id[TAFHEEM]["basis"]
    assert "یادداشتِ مستقل" in by_id[TAFHEEM]["basis"]
    assert by_id[TAFHEEM]["scope"].find("۵:۳۵–۴۳") >= 0
    assert by_id[WASIT]["scope"] == "مائده ۵:۳۱–۳۶؛ صفحه‌های مستقیم"
    assert len(by_id[WASIT]["sourceUrls"]) == 6
    assert set(by_id["ar_fayd_safi"]["sourceUrls"]) == {
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=41&SoraNo=5&AyahNo=31&LanguageID=1",
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=41&SoraNo=5&AyahNo=33&LanguageID=1",
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=41&SoraNo=5&AyahNo=35&LanguageID=1",
    }
    assert REGISTRY["version"] >= 8 and len(REGISTRY["sources"]) == 15


def test_maida_5_31_36_preserves_distinct_reports_and_interpretations():
    verses = DOSSIER["verses"]

    v31 = verses["5:31"]
    v31_classical = _by_source(v31["classical"])
    assert "فرزندانِ مستقیمِ آدم" in v31_classical["ar_tabari_qurancom"]["text"]
    assert "دو کلاغ" in v31_classical["ar_ibn_kathir_qurancom"]["text"]
    assert "الهام یا تکلیف" in v31_classical["ar_tusi_tibyan"]["text"]
    assert "امام باقر" in v31_classical["ar_fayd_safi"]["text"]
    assert "یادداشتِ ۵۲" in _by_source(v31["modern"])[TAFHEEM]["text"]
    assert "توبهٔ برخاسته از ترسِ خدا" in _by_source(v31["modern"])[WASIT]["text"]

    v32 = verses["5:32"]
    v32_classical = _by_source(v32["classical"])
    assert "ترجیح می‌دهد" in v32_classical["ar_tabari_qurancom"]["text"]
    assert "هدایت" in v32_classical["ar_tusi_tibyan"]["text"]
    assert "امام باقر و صادق" in v32_classical["ar_fayd_safi"]["text"]
    assert "یادداشت‌های ۵۳–۵۴" in _by_source(v32["modern"])[TAFHEEM]["cite"]
    assert "انصاف با اقلیتِ مؤمن" in _by_source(v32["modern"])[WASIT]["text"]
    assert "تلمودی" in " ".join(item["text"] for item in v32["critical"])

    v33 = verses["5:33"]
    v33_classical = _by_source(v33["classical"])
    assert "نه اختیارِ بی‌قیدِ حاکم" in v33_classical["ar_tabari_qurancom"]["text"]
    assert "در شهر و بیرونِ آن" in v33_classical["ar_tusi_tibyan"]["text"]
    assert "بر حسبِ قتل، مال‌گرفتن یا ارعاب" in v33_classical["ar_fayd_safi"]["text"]
    assert "دولتِ اسلامی" in _by_source(v33["modern"])[TAFHEEM]["text"]

    v34 = verses["5:34"]
    v34_classical = _by_source(v34["classical"])
    assert "مالِ معینِ موجود" in v34_classical["ar_tabari_qurancom"]["text"]
    assert "حقوقِ اشخاص" in v34_classical["ar_tusi_tibyan"]["text"]
    assert "اولیای مقتول" in v34_classical["ar_fayd_safi"]["text"]
    assert "یادداشتِ ۵۷" in _by_source(v34["modern"])[TAFHEEM]["cite"]
    assert "رأیِ دوم" in _by_source(v34["modern"])[WASIT]["text"]
    assert "حقوقِ بندگان" in _by_source(v34["modern"])[WASIT]["text"]

    v35 = verses["5:35"]
    v35_classical = _by_source(v35["classical"])
    assert "زبان و دست و دل" in v35_classical["ar_tusi_tibyan"]["text"]
    assert "پیرویِ امام" in v35_classical["ar_fayd_safi"]["text"]
    assert "یادداشت‌های ۵۸–۵۹ ذیلِ ۵:۳۵" in _by_source(v35["modern"])[TAFHEEM]["cite"]
    assert "کوششِ فراگیر" in _by_source(v35["modern"])[TAFHEEM]["text"]
    assert "ابن‌تیمیه" in _by_source(v35["modern"])[WASIT]["text"]
    assert "جاهِ پیامبر" in _by_source(v35["modern"])[WASIT]["text"]
    assert "درخواستِ مستقیم از مردگان" in _by_source(v35["modern"])[WASIT]["text"]

    v36 = verses["5:36"]
    v36_classical = _by_source(v36["classical"])
    assert "بی‌توبه مرده‌اند" in v36_classical["ar_tabari_qurancom"]["text"]
    assert "نحوی" in v36_classical["ar_tusi_tibyan"]["text"]
    assert TAFHEEM not in _by_source(v36["modern"])
    assert "بی‌یادداشتِ مستقل" in " ".join(item["cite"] for item in _all_records(v36))


def test_maida_5_31_36_model_applications_are_separate_limited_analyses():
    for ayah in range(31, 37):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        model_records = {record["model"]: record for record in entry["modern"] if record.get("model")}
        assert set(model_records) == MODELS
        assert "تحریریِ چارچوب" in " ".join(record["limit"] for record in model_records.values())
        assert len({record["text"] for record in model_records.values()}) == 3
        assert all(record["cite"] and record["evidence"] for record in model_records.values())
        assert "ایزوتسو" not in model_records["fillmore"]["cite"]


def test_maida_5_31_36_keeps_claims_attributed_and_pages_uninvented():
    for ayah in range(31, 37):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        all_records = _all_records(entry)
        cites = " ".join(record["cite"] for record in all_records)
        assert "پیش‌نویس" in entry["status"]
        assert "چاپ و صفحه" not in cites or "احراز نشده" in cites or "Quran.com" in cites or "GreatTafsirs" in cites
        assert all(record["evidence"].strip() and record["limit"].strip() for record in entry["classical"])
    assert "مقابله نشده" in " ".join(
        record["text"] for ayah in range(31, 37) for record in DOSSIER["verses"][f"5:{ayah}"]["critical"]
    )
    assert "راهنمایِ اقدام نیستند" in DOSSIER["editorialMethod"]
