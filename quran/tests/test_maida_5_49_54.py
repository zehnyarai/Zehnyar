"""Source-scope, disagreement, and draft-quality checks for Al-Ma'idah 5:49–54."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = json.loads((ROOT / "static" / "verse-dossiers.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))

SUNNI = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
SHIA = {"ar_tusi_tibyan", "ar_fayd_safi"}
QURANENC = "ar_qe_arabic_moyassar"
TAFHEEM = "en_tafheem_ul_quran"
WASIT = "ar_wasit_qurancom"
MODELS = {"izutsu", "fillmore", "cognitive"}
TAFHEEM_44_50 = "https://www.islamicstudies.info/tafheem.php?sura=5&verse=44&to=50"
TAFHEEM_51_57 = "https://www.islamicstudies.info/tafheem.php?sura=5&verse=51&to=57"
TAFHEEM_NOTES = {
    49: "یادداشتِ ۸۲",
    50: "یادداشتِ ۸۳",
    51: "بی‌یادداشتِ تفسیریِ مستقل",
    52: "یادداشت‌هایِ ۸۴–۸۵",
    53: "یادداشتِ ۸۶",
    54: "یادداشت‌هایِ ۸۷–۸۸",
}
FAYD_GROUPS = {
    49: (47, "۵:۴۷–۵۱"),
    50: (47, "۵:۴۷–۵۱"),
    51: (47, "۵:۴۷–۵۱"),
    52: (52, "۵:۵۲–۵۴"),
    53: (52, "۵:۵۲–۵۴"),
    54: (52, "۵:۵۲–۵۴"),
}


def _by_source(records: list[dict]) -> dict[str, dict]:
    return {record["sourceId"]: record for record in records if record.get("sourceId")}


def _all_records(entry: dict) -> list[dict]:
    records = []
    for field in ("notes", "context", "classical", "modern", "critical", "research"):
        records.extend(entry[field])
    return records


def _fa_num(value: int) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def _greattafsirs_url(tafsir_no: int, ayah_no: int) -> str:
    return (
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1"
        f"&MadhabNo=4&TafsirNo={tafsir_no}&SoraNo=5&AyahNo={ayah_no}&LanguageID=1"
    )


def test_maida_5_49_54_has_six_complete_balanced_drafts():
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-55")
    assert batch["range"] == "5:49–54" and batch["count"] == 6
    assert "پیش‌نویسِ نیازمندِ داوریِ تخصصی" in batch["status"]
    assert "۵:۴۸" in batch["status"]
    assert "خلأِ شرحِ مستقیمِ طنطاوی برای ۵:۴۹" in batch["status"]
    assert "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است" in DOSSIER["notice"]
    prior_batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-54")
    assert "در زمانِ ثبتِ این بسته" in next(item for item in DOSSIER["batches"] if item["id"] == "dossier-53")["status"]
    assert "۵:۴۲" in prior_batch["status"]

    for ayah in range(49, 55):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        assert entry["status"].startswith("پیش‌نویس") and "تخصصی" in entry["status"]
        for field in ("notes", "context", "classical", "modern", "critical", "research"):
            assert len(entry[field]) == 5, (ayah, field)
        classical = _by_source(entry["classical"])
        assert set(classical) == SUNNI | SHIA
        assert {record["tradition"] for record in entry["classical"] if record["sourceId"] in SUNNI} == {"اهل‌سنت"}
        assert {record["tradition"] for record in entry["classical"] if record["sourceId"] in SHIA} == {"شیعهٔ امامیه"}

        modern = _by_source(entry["modern"])
        expected_modern = {QURANENC, TAFHEEM} if ayah == 49 else {QURANENC, WASIT}
        assert set(modern) == expected_modern
        model_records = {record["model"]: record for record in entry["modern"] if record.get("model")}
        assert set(model_records) == MODELS
        assert len({record["text"] for record in model_records.values()}) == 3
        assert all(record["cite"].strip() and record["evidence"].strip() for record in model_records.values())
        for field in ("notes", "context", "critical", "research"):
            assert all(len(record["text"].split()) >= 14 and record["cite"].strip() for record in entry[field])
        for record in entry["classical"] + [record for record in entry["modern"] if record.get("sourceId")]:
            assert record["sourceUrl"].startswith("https://")
            assert record["evidence"].strip() and record["limit"].strip()


def test_maida_5_49_54_records_actual_direct_grouped_and_missing_source_scopes():
    for ayah in range(49, 55):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        classical = _by_source(entry["classical"])
        for source_id, slug in (
            ("ar_tabari_qurancom", "ar-tafsir-al-tabari"),
            ("ar_ibn_kathir_qurancom", "ar-tafsir-ibn-kathir"),
            ("ar_jalalayn_qurancom", "ar-tafsir-jalalayn"),
        ):
            assert classical[source_id]["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/{slug}"

        tusi = classical["ar_tusi_tibyan"]
        assert tusi["sourceUrl"] == _greattafsirs_url(39, ayah)
        assert f"شرحِ مائده ۵:{_fa_num(ayah)}" in tusi["cite"]

        fayd_page, fayd_scope = FAYD_GROUPS[ayah]
        fayd = classical["ar_fayd_safi"]
        assert fayd["sourceUrl"] == _greattafsirs_url(41, fayd_page)
        assert fayd_scope in fayd["cite"] and fayd_scope in fayd["evidence"]

        modern = _by_source(entry["modern"])
        assert modern[QURANENC]["sourceUrl"] == "https://quranenc.com/en/browse/arabic_moyassar"
        if ayah == 49:
            assert modern[TAFHEEM]["sourceUrl"] == TAFHEEM_44_50
            assert "یادداشتِ ۸۲" in modern[TAFHEEM]["cite"]
            assert WASIT not in modern
        else:
            wasit = modern[WASIT]
            assert wasit["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-al-wasit"
            assert f"مسیرِ ۵:{_fa_num(ayah)}" in wasit["cite"]
            assert "بدنهٔ تفسیری و عنوانِ مسیر" in wasit["cite"]

        all_cites = " ".join(record.get("cite", "") for record in _all_records(entry))
        assert "تفہیم القرآن" in all_cites
        assert TAFHEEM_NOTES[ayah] in all_cites

    collection = next(item for item in CATALOG["collections"] if item["id"] == "maida-5-49-54-cited")
    assert CATALOG["version"] >= 36
    assert len(CATALOG["collections"]) >= 37
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ مائده ۵:۴۹–۵۴"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == SUNNI
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == SHIA
    by_id = {item["id"]: item for item in collection["items"]}
    assert set(by_id) == SUNNI | SHIA | {QURANENC, TAFHEEM, WASIT}
    assert by_id[TAFHEEM]["sourceUrls"] == [TAFHEEM_44_50, TAFHEEM_51_57]
    assert "یادداشت‌هایِ ۸۲–۸۸" in by_id[TAFHEEM]["basis"]
    assert "۵:۵۱ یادداشتِ مستقل دیده نشد" in by_id[TAFHEEM]["basis"]
    assert set(by_id["ar_tusi_tibyan"]["sourceUrls"]) == {
        _greattafsirs_url(39, ayah) for ayah in range(49, 55)
    }
    assert "شش شرحِ مستقیم" in by_id["ar_tusi_tibyan"]["scope"]
    assert set(by_id["ar_fayd_safi"]["sourceUrls"]) == {
        _greattafsirs_url(41, page) for page in (47, 52)
    }
    assert "۵:۴۷–۵۱" in by_id["ar_fayd_safi"]["scope"]
    assert "۵:۵۲–۵۴" in by_id["ar_fayd_safi"]["scope"]
    assert len(by_id[WASIT]["sourceUrls"]) == 5
    assert all(f"/al-maidah/{ayah}/" in url for ayah, url in zip(range(50, 55), by_id[WASIT]["sourceUrls"]))
    assert "۵:۴۹" in by_id[WASIT]["scope"] and "۵:۴۸" in by_id[WASIT]["basis"]
    assert "۵:۵۰–۵۴" in by_id[WASIT]["scope"]
    assert "۵:۴۹" in collection["comparativeCore"]["note"] and "جایگزین" in collection["comparativeCore"]["note"]
    assert REGISTRY["version"] >= 8 and len(REGISTRY["sources"]) == 15


def test_maida_5_49_54_preserves_source_disagreement_and_attributes_claims():
    verses = DOSSIER["verses"]
    v49 = verses["5:49"]
    assert "خلأ" in " ".join(row["text"] for row in v49["critical"])
    assert "۵:۴۸" in " ".join(row["text"] for row in v49["critical"])
    assert TAFHEEM in _by_source(v49["modern"])
    assert WASIT not in _by_source(v49["modern"])

    v50 = _by_source(verses["5:50"]["classical"])
    assert "احکامِ اهلِ شرک" in v50["ar_tabari_qurancom"]["text"]
    assert "تبغون/يبغون" in v50["ar_jalalayn_qurancom"]["text"]
    assert "یاسا" in v50["ar_ibn_kathir_qurancom"]["text"]
    assert "تبغون" in v50["ar_tusi_tibyan"]["text"]

    v51 = _by_source(verses["5:51"]["classical"])
    assert "اثباتِ قطعی کافی نیست" in v51["ar_tabari_qurancom"]["text"]
    assert "ابولبابه" in " ".join(row["text"] for row in _all_records(verses["5:51"]))
    assert "عیاشی" in v51["ar_fayd_safi"]["text"]
    assert "هم‌پیمان" in v51["ar_jalalayn_qurancom"]["text"]

    v52 = _by_source(verses["5:52"]["classical"])
    assert "دائرة" in v52["ar_tabari_qurancom"]["text"]
    assert "جزیه" in v52["ar_ibn_kathir_qurancom"]["text"]
    assert "فتحِ مکه" in v52["ar_tusi_tibyan"]["text"]
    assert "بنی‌امیه" in v52["ar_fayd_safi"]["text"]

    v53 = _by_source(verses["5:53"]["classical"])
    assert "قرائتِ «ويقول/يقول»" in v53["ar_tabari_qurancom"]["text"]
    assert "ابولبابه" in v53["ar_ibn_kathir_qurancom"]["text"]
    assert "رفع و نصب" in v53["ar_tusi_tibyan"]["text"]
    assert "نفاق" in v53["ar_fayd_safi"]["text"]

    v54 = _by_source(verses["5:54"]["classical"])
    assert "اهلِ یمن" in v54["ar_tabari_qurancom"]["text"]
    assert "بدونِ آن نقل" in v54["ar_tabari_qurancom"]["text"]
    assert "ابوبکر" in v54["ar_ibn_kathir_qurancom"]["text"]
    assert "ابوموسی" in v54["ar_jalalayn_qurancom"]["text"]
    assert "امیرالمؤمنین" in v54["ar_tusi_tibyan"]["text"]
    assert "مهدی" in v54["ar_fayd_safi"]["text"]
    assert "ترجیح می‌دهد" in v54["ar_tusi_tibyan"]["text"] and "موضعی جدلی" in v54["ar_tusi_tibyan"]["text"]

    assert "مقابله نشده است" in " ".join(row["text"] for row in verses["5:52"]["critical"])
    assert "فتوا" in " ".join(row["text"] for row in verses["5:54"]["critical"])
    assert "پیش‌نویس و نیازمندِ داوریِ تخصصی‌اند" in DOSSIER["editorialMethod"]


def test_maida_5_49_54_keeps_models_separate_and_bibliographic_limits_explicit():
    for ayah in range(49, 55):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        model_records = {record["model"]: record for record in entry["modern"] if record.get("model")}
        assert set(model_records) == MODELS
        assert "تحریریِ چارچوب" in " ".join(record["limit"] for record in model_records.values())
        assert len({record["text"] for record in model_records.values()}) == 3
        assert "ایزوتسو" not in model_records["fillmore"]["cite"]
        assert "Fillmore" in model_records["fillmore"]["cite"]
        assert "معناشناسیِ شناختی" in model_records["cognitive"]["cite"]
        for record in entry["classical"] + [item for item in entry["modern"] if item.get("sourceId")]:
            if "چاپ و صفحه" in record["cite"]:
                assert "احراز نشده" in record["cite"]
        assert "پیش‌نویس" in entry["status"]

    method = DOSSIER["editorialMethod"]
    assert "AyahNo=47" in method and "AyahNo=52" in method
    assert "Quran.com" in method and "شرحِ مستقیمِ ۵:۴۹" in method
    assert "یادداشتِ ۸۲" in method and "یادداشت‌هایِ ۸۷–۸۸" in method
