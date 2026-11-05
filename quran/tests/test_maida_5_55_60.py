"""Source-scope, disagreement, and draft-quality checks for Al-Ma'idah 5:55–60."""
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
TAFHEEM_51_57 = "https://www.islamicstudies.info/tafheem.php?sura=5&verse=51&to=57"
TAFHEEM_58_64 = "https://www.islamicstudies.info/tafheem.php?sura=5&verse=58&to=64"
TAFHEEM_GROUPS = {
    55: (TAFHEEM_51_57, "بی‌شرحِ مستقل"),
    56: (TAFHEEM_51_57, "بی‌شرحِ مستقل"),
    57: (TAFHEEM_51_57, "بی‌شرحِ مستقل"),
    58: (TAFHEEM_58_64, "یادداشت‌هایِ ۸۹–۹۰"),
    59: (TAFHEEM_58_64, "بی‌شرحِ مستقل"),
    60: (TAFHEEM_58_64, "یادداشتِ ۹۱"),
}
FAYD_GROUPS = {
    55: (55, "۵:۵۵"),
    56: (59, "۵:۵۶–۵۹"),
    57: (59, "۵:۵۶–۵۹"),
    58: (59, "۵:۵۶–۵۹"),
    59: (59, "۵:۵۶–۵۹"),
    60: (60, "۵:۶۰–۶۴"),
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


def test_maida_5_55_60_has_six_complete_balanced_drafts():
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-56")
    assert batch["range"] == "5:55–60" and batch["count"] == 6
    assert "پیش‌نویسِ نیازمندِ داوریِ تخصصی" in batch["status"]
    assert "۵:۵۴" in batch["status"]
    assert "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است" in DOSSIER["notice"]
    previous = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-55")
    assert previous["range"] == "5:49–54"
    assert "در بستهٔ مائده ۵:۵۵–۶۰" in DOSSIER["editorialMethod"]

    for ayah in range(55, 61):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        assert entry["status"].startswith("پیش‌نویس") and "تخصصی" in entry["status"]
        for field in ("notes", "context", "classical", "modern", "critical", "research"):
            assert len(entry[field]) == 5, (ayah, field)
        classical = _by_source(entry["classical"])
        assert set(classical) == SUNNI | SHIA
        assert {record["tradition"] for record in entry["classical"] if record["sourceId"] in SUNNI} == {"اهل‌سنت"}
        assert {record["tradition"] for record in entry["classical"] if record["sourceId"] in SHIA} == {"شیعهٔ امامیه"}

        modern = _by_source(entry["modern"])
        expected_modern = {QURANENC, TAFHEEM} if ayah in {58, 60} else {QURANENC, WASIT}
        assert set(modern) == expected_modern
        models = {record["model"]: record for record in entry["modern"] if record.get("model")}
        assert set(models) == MODELS
        assert len({record["text"] for record in models.values()}) == 3
        assert all(record["cite"].strip() and record["evidence"].strip() for record in models.values())
        for field in ("notes", "context", "critical", "research"):
            assert all(len(record["text"].split()) >= 14 and record["cite"].strip() for record in entry[field])
        for record in entry["classical"] + [record for record in entry["modern"] if record.get("sourceId")]:
            assert record["sourceUrl"].startswith("https://")
            assert record["evidence"].strip() and record["limit"].strip()


def test_maida_5_55_60_catalog_records_direct_grouped_and_unavailable_scopes():
    for ayah in range(55, 61):
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
        if ayah in {55, 60}:
            assert "قطعه‌هایِ ۰ و ۱" in tusi["cite"]

        fayd_page, fayd_scope = FAYD_GROUPS[ayah]
        fayd = classical["ar_fayd_safi"]
        assert fayd["sourceUrl"] == _greattafsirs_url(41, fayd_page)
        assert fayd_scope in fayd["cite"] and fayd_scope in fayd["evidence"]

        modern = _by_source(entry["modern"])
        assert modern[QURANENC]["sourceUrl"] == "https://quranenc.com/en/browse/arabic_moyassar"
        if ayah in {58, 60}:
            tafheem_url, note = TAFHEEM_GROUPS[ayah]
            assert modern[TAFHEEM]["sourceUrl"] == tafheem_url
            assert note in modern[TAFHEEM]["cite"]
        else:
            wasit = modern[WASIT]
            assert wasit["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-al-wasit"
            assert f"مسیرِ ۵:{_fa_num(ayah)}" in wasit["cite"]
            assert "عنوان و بدنهٔ عربی" in wasit["cite"]

    collection = next(item for item in CATALOG["collections"] if item["id"] == "maida-5-55-60-cited")
    assert CATALOG["version"] >= 36
    assert len(CATALOG["collections"]) >= 37
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ مائده ۵:۵۵–۶۰"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == SUNNI
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == SHIA
    by_id = {source["id"]: source for source in collection["items"]}
    assert set(by_id) == SUNNI | SHIA | {QURANENC, TAFHEEM, WASIT}

    assert set(by_id["ar_tabari_qurancom"]["sourceUrls"]) == {
        f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-al-tabari" for ayah in range(55, 61)
    }
    assert set(by_id["ar_ibn_kathir_qurancom"]["sourceUrls"]) == {
        f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-ibn-kathir" for ayah in range(55, 61)
    }
    assert set(by_id["ar_jalalayn_qurancom"]["sourceUrls"]) == {
        f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-jalalayn" for ayah in range(55, 61)
    }
    assert set(by_id["ar_tusi_tibyan"]["sourceUrls"]) == {
        _greattafsirs_url(39, ayah) for ayah in range(55, 61)
    }
    assert "شش شرحِ مستقیم" in by_id["ar_tusi_tibyan"]["scope"]
    assert set(by_id["ar_fayd_safi"]["sourceUrls"]) == {
        _greattafsirs_url(41, ayah) for ayah in (55, 59, 60)
    }
    assert "۵:۵۶–۵۹" in by_id["ar_fayd_safi"]["scope"]
    assert "۵:۶۰–۶۴" in by_id["ar_fayd_safi"]["scope"]
    assert by_id[TAFHEEM]["sourceUrls"] == [TAFHEEM_51_57, TAFHEEM_58_64]
    assert "یادداشتِ ۹۱" in by_id[TAFHEEM]["basis"]
    assert "برایِ ۵:۵۵–۵۷ و ۵:۵۹ یادداشتِ مستقل" in by_id[TAFHEEM]["basis"]
    assert len(by_id[WASIT]["sourceUrls"]) == 6
    assert all(f"/al-maidah/{ayah}/" in url for ayah, url in zip(range(55, 61), by_id[WASIT]["sourceUrls"]))
    assert REGISTRY["version"] >= 8 and len(REGISTRY["sources"]) == 15


def test_maida_5_55_60_preserves_interpretive_disagreements_and_limits():
    verses = DOSSIER["verses"]
    v55 = _by_source(verses["5:55"]["classical"])
    assert "ناصر" in v55["ar_tabari_qurancom"]["text"]
    assert "ضعفِ سندها" in v55["ar_ibn_kathir_qurancom"]["text"]
    assert "امامتِ علی" in v55["ar_tusi_tibyan"]["text"]
    assert "دو نوبت" in v55["ar_fayd_safi"]["text"]
    assert "خاشعان" in v55["ar_jalalayn_qurancom"]["text"]
    assert "عمومِ مؤمنان" in _by_source(verses["5:55"]["modern"])["ar_wasit_qurancom"]["text"]

    v56 = _by_source(verses["5:56"]["classical"])
    assert "انصار" in v56["ar_tabari_qurancom"]["text"]
    assert "وجهی دیگر" in v56["ar_tusi_tibyan"]["text"]
    assert "امامان" in v56["ar_fayd_safi"]["text"]
    assert "پیروزی" in _by_source(verses["5:56"]["modern"])["ar_wasit_qurancom"]["text"]

    v57 = _by_source(verses["5:57"]["classical"])
    assert "هم‌معنا" in " ".join(row["text"] for row in verses["5:57"]["notes"])
    assert "با جرّ" in v57["ar_tabari_qurancom"]["text"] and "با نصب" in v57["ar_tabari_qurancom"]["text"]
    assert "مشرکان" in v57["ar_ibn_kathir_qurancom"]["text"]
    assert "جرّ و نصب" in v57["ar_tusi_tibyan"]["text"]

    v58 = _by_source(verses["5:58"]["classical"])
    assert "سدی" in v58["ar_tabari_qurancom"]["text"]
    assert "ابومحذوره" in v58["ar_ibn_kathir_qurancom"]["text"]
    assert "دو توضیح" in v58["ar_tusi_tibyan"]["text"]
    assert "یادداشت‌هایِ ۸۹–۹۰" in _by_source(verses["5:58"]["modern"])[TAFHEEM]["cite"]

    v59 = _by_source(verses["5:59"]["classical"])
    assert "تنقمون" in v59["ar_tabari_qurancom"]["text"]
    assert "چند وجه" in v59["ar_tusi_tibyan"]["text"]
    assert "اکثر" in _by_source(verses["5:59"]["modern"])["ar_wasit_qurancom"]["text"]

    v60 = _by_source(verses["5:60"]["classical"])
    assert "ترجیح" in v60["ar_tabari_qurancom"]["text"]
    assert "چند قرائت" in v60["ar_tusi_tibyan"]["text"]
    assert "اصحابِ سبت" in v60["ar_fayd_safi"]["text"]
    assert "شکستنِ سبت" in _by_source(verses["5:60"]["modern"])[TAFHEEM]["text"]

    all_critical = " ".join(row["text"] for ayah in range(55, 61) for row in verses[f"5:{ayah}"]["critical"])
    assert "از بدنهٔ تفسیر جداست" in all_critical
    assert "مستقلاً آزموده" in all_critical
    assert "یهودیانِ امروز" in all_critical


def test_maida_5_55_60_keeps_models_separate_bibliographic_limits_explicit():
    for ayah in range(55, 61):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        models = {record["model"]: record for record in entry["modern"] if record.get("model")}
        assert set(models) == MODELS
        assert "تحریریِ چارچوب" in " ".join(record["limit"] for record in models.values())
        assert len({record["text"] for record in models.values()}) == 3
        assert "ایزوتسو" not in models["fillmore"]["cite"]
        assert "Fillmore" in models["fillmore"]["cite"]
        assert "معناشناسیِ شناختی" in models["cognitive"]["cite"]
        for record in entry["classical"] + [row for row in entry["modern"] if row.get("sourceId")]:
            if "چاپ و صفحه" in record["cite"]:
                assert "احراز نشده" in record["cite"]
        assert "پیش‌نویس" in entry["status"]

    method = DOSSIER["editorialMethod"]
    assert "AyahNo=55–60" in method
    assert "یادداشت‌هایِ ۸۹–۹۰" in method and "یادداشتِ ۹۱" in method
    assert "قطعهٔ ۰ از انتخابِ ۵:۵۸–۶۴" in method
    assert "سه قطعه" in method and "پیش‌نویس و نیازمندِ داوریِ تخصصی‌اند" in method
