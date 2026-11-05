"""Source-scope, disagreement, and draft-quality checks for Al-Ma'idah 5:43–48."""
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
TAFHEEM_URLS = [
    "https://www.islamicstudies.info/tafheem.php?sura=5&verse=37&to=43",
    "https://www.islamicstudies.info/tafheem.php?sura=5&verse=44&to=50",
]
TAFHEEM_NOTES = {
    43: "یادداشتِ ۷۱",
    44: "یادداشت‌هایِ ۷۲–۷۳",
    45: "یادداشت‌هایِ ۷۴–۷۵",
    46: "یادداشتِ ۷۶",
    47: "یادداشتِ ۷۷",
    48: "یادداشت‌هایِ ۷۸–۸۱",
}
TUSI_GROUPS = {verse: (verse, f"۵:{str(verse).translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))}") for verse in range(43, 49)}
FAYD_GROUPS = {
    43: (43, "۵:۴۳–۴۶"),
    44: (43, "۵:۴۳–۴۶"),
    45: (43, "۵:۴۳–۴۶"),
    46: (43, "۵:۴۳–۴۶"),
    47: (47, "۵:۴۷–۵۱"),
    48: (47, "۵:۴۷–۵۱"),
}


def _by_source(records: list[dict]) -> dict[str, dict]:
    return {record["sourceId"]: record for record in records if record.get("sourceId")}


def _all_records(entry: dict) -> list[dict]:
    records = []
    for field in ("notes", "context", "classical", "modern", "critical", "research"):
        records.extend(entry[field])
    return records


def _greattafsirs_url(tafsir_no: int, ayah_no: int) -> str:
    return (
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1"
        f"&MadhabNo=4&TafsirNo={tafsir_no}&SoraNo=5&AyahNo={ayah_no}&LanguageID=1"
    )


def _fa_num(value: int) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def test_maida_5_43_48_has_six_complete_balanced_drafts():
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-54")
    assert batch["range"] == "5:43–48" and batch["count"] == 6
    assert "پیش‌نویسِ نیازمندِ داوریِ تخصصی" in batch["status"]
    assert "۵:۴۲" in batch["status"]
    assert "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است" in DOSSIER["notice"]
    prior_batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-53")
    assert "در زمانِ ثبتِ این بسته" in prior_batch["status"]
    assert "۵:۱–۴۲" in prior_batch["status"]

    for ayah in range(43, 49):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        assert entry["status"].startswith("پیش‌نویس") and "تخصصی" in entry["status"]
        for field in ("notes", "context", "classical", "modern", "critical", "research"):
            assert len(entry[field]) >= 5, (ayah, field)
        assert len(entry["classical"]) == 5
        classical = _by_source(entry["classical"])
        assert set(classical) == SUNNI | SHIA
        assert {record["tradition"] for record in entry["classical"] if record["sourceId"] in SUNNI} == {"اهل‌سنت"}
        assert {record["tradition"] for record in entry["classical"] if record["sourceId"] in SHIA} == {"شیعهٔ امامیه"}

        modern = _by_source(entry["modern"])
        assert set(modern) == {QURANENC, WASIT}
        model_records = {record["model"]: record for record in entry["modern"] if record.get("model")}
        assert set(model_records) == MODELS
        assert len({record["text"] for record in model_records.values()}) == 3
        assert all(record["cite"].strip() and record["evidence"].strip() for record in model_records.values())
        for field in ("notes", "context", "critical", "research"):
            assert all(len(record["text"].split()) >= 14 and record["cite"].strip() for record in entry[field])
        for record in entry["classical"] + [record for record in entry["modern"] if record.get("sourceId")]:
            assert record["sourceUrl"].startswith("https://")
            assert record["evidence"].strip() and record["limit"].strip()


def test_maida_5_43_48_records_actual_direct_grouped_and_offset_source_scopes():
    for ayah in range(43, 49):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        classical = _by_source(entry["classical"])
        for source_id, slug in (
            ("ar_tabari_qurancom", "ar-tafsir-al-tabari"),
            ("ar_ibn_kathir_qurancom", "ar-tafsir-ibn-kathir"),
            ("ar_jalalayn_qurancom", "ar-tafsir-jalalayn"),
        ):
            assert classical[source_id]["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/{slug}"

        tusi_page, tusi_scope = TUSI_GROUPS[ayah]
        tusi = classical["ar_tusi_tibyan"]
        assert tusi["sourceUrl"] == _greattafsirs_url(39, tusi_page)
        assert tusi_scope in tusi["cite"] and tusi_scope in tusi["evidence"]

        fayd_page, fayd_scope = FAYD_GROUPS[ayah]
        fayd = classical["ar_fayd_safi"]
        assert fayd["sourceUrl"] == _greattafsirs_url(41, fayd_page)
        assert fayd_scope in fayd["cite"] and fayd_scope in fayd["evidence"]

        modern = _by_source(entry["modern"])
        assert modern[QURANENC]["sourceUrl"] == "https://quranenc.com/en/browse/arabic_moyassar"
        route = ayah + 1
        wasit = modern[WASIT]
        assert wasit["sourceUrl"] == f"https://quran.com/al-maidah/{route}/tafsirs/ar-tafsir-al-wasit"
        assert f"مسیرِ ۵:{_fa_num(route)}" in wasit["cite"]
        assert f"۵:{_fa_num(ayah)}" in wasit["cite"]
        assert "یک آیه جلوتر" in wasit["cite"]
        assert "بدنهٔ عربی" in wasit["evidence"]
        assert "یک آیه جلوتر" in wasit["evidence"]

        all_cites = " ".join(record.get("cite", "") for record in _all_records(entry))
        assert "تفہیم القرآن" in all_cites
        assert TAFHEEM_NOTES[ayah] in all_cites

    collection = next(item for item in CATALOG["collections"] if item["id"] == "maida-5-43-48-cited")
    assert CATALOG["version"] >= 32
    assert len(CATALOG["collections"]) >= 37
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ مائده ۵:۴۳–۴۸"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == SUNNI
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == SHIA
    by_id = {item["id"]: item for item in collection["items"]}
    assert set(by_id) == SUNNI | SHIA | {QURANENC, TAFHEEM, WASIT}
    assert by_id[TAFHEEM]["sourceUrls"] == TAFHEEM_URLS
    assert "۵:۳۵–۴۳" in by_id[TAFHEEM]["scope"]
    assert "۷۱–۸۱" in by_id[TAFHEEM]["basis"]
    assert "۵:۴۴–۵۰" in by_id[TAFHEEM]["scope"]
    assert set(by_id["ar_tusi_tibyan"]["sourceUrls"]) == {
        _greattafsirs_url(39, ayah) for ayah in range(43, 49)
    }
    assert "شرحِ مستقیم" in by_id["ar_tusi_tibyan"]["scope"]
    assert set(by_id["ar_fayd_safi"]["sourceUrls"]) == {
        _greattafsirs_url(41, page) for page in (43, 47)
    }
    assert "۵:۴۳–۴۶" in by_id["ar_fayd_safi"]["scope"]
    assert "۵:۴۷–۵۱" in by_id["ar_fayd_safi"]["scope"]
    assert len(by_id[WASIT]["sourceUrls"]) == 6
    assert "جابه" in by_id[WASIT]["scope"]
    assert "عنوانِ مسیر و متن" in by_id[WASIT]["scope"]
    assert "مسیرِ ۵:۴۶ دو قطعه دارد" in by_id[WASIT]["basis"]
    assert "قطعهٔ دوم" in DOSSIER["editorialMethod"]
    assert REGISTRY["version"] >= 8 and len(REGISTRY["sources"]) == 15


def test_maida_5_43_48_preserves_interpretive_disagreements_and_attributes_modudi():
    verses = DOSSIER["verses"]
    v43 = _by_source(verses["5:43"]["classical"])
    assert "استفهام را تعجب" in v43["ar_jalalayn_qurancom"]["text"]
    assert "رجم" in v43["ar_ibn_kathir_qurancom"]["text"]
    assert "حکمی آسان‌تر" in v43["ar_fayd_safi"]["text"]
    assert "یادداشتِ ۷۱" in " ".join(row["cite"] for row in _all_records(verses["5:43"]))

    v44 = _by_source(verses["5:44"]["classical"])
    assert "النبيون" in v44["ar_tusi_tibyan"]["text"]
    assert "ربانیون" in v44["ar_jalalayn_qurancom"]["text"]
    assert "عیاشی" in v44["ar_fayd_safi"]["text"]
    assert "الكافرون" in v44["ar_tabari_qurancom"]["text"]

    v45 = _by_source(verses["5:45"]["classical"])
    assert "عفوکننده" in v45["ar_tabari_qurancom"]["text"]
    assert "نصب" in v45["ar_tusi_tibyan"]["text"]
    assert "نسخِ حکمِ نفس" in v45["ar_fayd_safi"]["text"]
    wasit_v45 = _by_source(verses["5:45"]["modern"])[WASIT]
    assert "عدالت و رحمت" in wasit_v45["text"] and "تشویق به عفو" in wasit_v45["text"]
    assert "هر دو قطعهٔ ۰ و ۱ خوانده شدند" in wasit_v45["evidence"]

    v46 = _by_source(verses["5:46"]["classical"])
    assert "دو احتمال" in v46["ar_tusi_tibyan"]["text"]
    assert "دو تصدیق" in v46["ar_jalalayn_qurancom"]["text"]

    v47 = _by_source(verses["5:47"]["classical"])
    assert "قرائتِ حمزه" in v47["ar_tusi_tibyan"]["text"]
    assert "الفاسقون" in v47["ar_jalalayn_qurancom"]["text"]

    v48 = _by_source(verses["5:48"]["classical"])
    assert "ترجیح" in v48["ar_tabari_qurancom"]["text"]
    assert "گواه و امین" in v48["ar_ibn_kathir_qurancom"]["text"]
    assert "رقیب" in v48["ar_tusi_tibyan"]["text"]
    assert "شرعة ومنهاجاً" in v48["ar_fayd_safi"]["text"]
    assert "یادداشت‌هایِ ۷۸–۸۱" in " ".join(row["cite"] for row in _all_records(verses["5:48"]))


def test_maida_5_43_48_keeps_semantic_models_separate_and_limited():
    for ayah in range(43, 49):
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
    assert "Quran.com" in method and "آیهٔ واقعیِ شرح" in method
    assert "گزارش‌هایِ تاریخیِ مودودی" in method
    assert "پیش‌نویس و نیازمندِ داوریِ تخصصی‌اند" in method
