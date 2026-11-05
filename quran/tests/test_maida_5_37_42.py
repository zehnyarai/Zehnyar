"""Targeted source, scope, disagreement, and attribution checks for Al-Ma'idah 5:37–42."""
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
TAFHEEM_URL = "https://www.islamicstudies.info/tafheem.php?sura=5&verse=37&to=43"
TUSI_GROUPS = {
    37: (37, "۵:۳۶–۳۷"),
    38: (38, "۵:۳۸"),
    39: (39, "۵:۳۹"),
    40: (40, "۵:۴۰"),
    41: (41, "۵:۴۱"),
    42: (42, "۵:۴۲"),
}
FAYD_GROUPS = {
    37: (37, "۵:۳۴–۳۸"),
    38: (38, "۵:۳۴–۳۸"),
    39: (39, "۵:۳۹–۴۱"),
    40: (40, "۵:۳۹–۴۱"),
    41: (41, "۵:۳۹–۴۱"),
    42: (42, "۵:۴۲"),
}
TAFHEEM_NOTES = {
    37: "بی‌یادداشتِ تفسیریِ مستقل",
    38: "یادداشتِ ۶۰",
    39: "یادداشتِ ۶۱",
    40: "بی‌یادداشتِ تفسیریِ مستقل",
    41: "یادداشت‌های ۶۲–۶۸",
    42: "یادداشت‌های ۶۹–۷۰",
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


def test_maida_5_37_42_has_six_complete_balanced_drafts():
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-53")
    assert batch["range"] == "5:37–42" and batch["count"] == 6
    assert "پیش‌نویسِ نیازمندِ داوریِ تخصصی" in batch["status"]
    assert "۵:۱–۴۲" in batch["status"]
    assert "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است" in DOSSIER["notice"]

    for ayah in range(37, 43):
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


def test_maida_5_37_42_records_actual_direct_and_grouped_source_ranges():
    for ayah in range(37, 43):
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
        assert modern[WASIT]["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-al-wasit"
        all_cites = " ".join(record.get("cite", "") for record in _all_records(entry))
        assert "تفہیم القرآن" in all_cites
        assert TAFHEEM_NOTES[ayah] in all_cites

        if ayah in {37, 40}:
            assert TAFHEEM not in modern
            assert "بی‌یادداشتِ تفسیریِ مستقل" in all_cites

    collection = next(item for item in CATALOG["collections"] if item["id"] == "maida-5-37-42-cited")
    assert CATALOG["version"] >= 31
    assert len(CATALOG["collections"]) >= 37
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ مائده ۵:۳۷–۴۲"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == SUNNI
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == SHIA
    by_id = {item["id"]: item for item in collection["items"]}
    assert set(by_id) == SUNNI | SHIA | {QURANENC, TAFHEEM, WASIT}
    assert by_id[TAFHEEM]["sourceUrls"] == [TAFHEEM_URL]
    assert "۵:۳۵–۴۳" in by_id[TAFHEEM]["scope"]
    assert "۶۰" in by_id[TAFHEEM]["basis"] and "۶۲–۶۸" in by_id[TAFHEEM]["basis"]
    assert "۶۹–۷۰" in by_id[TAFHEEM]["basis"]
    assert "شرحِ مستقل ندارند" in by_id[TAFHEEM]["basis"]
    assert set(by_id["ar_tusi_tibyan"]["sourceUrls"]) == {
        _greattafsirs_url(39, ayah) for ayah in range(37, 43)
    }
    assert "گروهیِ ۵:۳۶–۳۷" in by_id["ar_tusi_tibyan"]["scope"]
    assert "مستقیم" in by_id["ar_tusi_tibyan"]["scope"]
    assert set(by_id["ar_fayd_safi"]["sourceUrls"]) == {
        _greattafsirs_url(41, page) for page in (37, 38, 39, 40, 41, 42)
    }
    assert "۵:۳۴–۳۸" in by_id["ar_fayd_safi"]["scope"]
    assert "۵:۳۹–۴۱" in by_id["ar_fayd_safi"]["scope"]
    assert "AyahNo=42: مستقیم" in by_id["ar_fayd_safi"]["scope"]
    assert len(by_id[WASIT]["sourceUrls"]) == 6
    assert REGISTRY["version"] >= 8 and len(REGISTRY["sources"]) == 15


def test_maida_5_37_42_preserves_disagreements_and_attribution():
    verses = DOSSIER["verses"]

    v37 = _by_source(verses["5:37"]["classical"])
    assert "دشمنانِ علی" in v37["ar_fayd_safi"]["text"]
    assert "عیاشی" in v37["ar_fayd_safi"]["text"]
    assert "کافران و فدیهٔ ناپذیرفته" in v37["ar_tabari_qurancom"]["text"]
    assert "بی‌یادداشتِ تفسیریِ مستقل" in " ".join(record["cite"] for record in _all_records(verses["5:37"]))

    v38 = _by_source(verses["5:38"]["classical"])
    assert "ربعِ دینار را برمی‌گزیند" in v38["ar_tabari_qurancom"]["text"]
    assert "حرز" in v38["ar_tusi_tibyan"]["text"]
    assert "نصاب و موضعِ قطع" in v38["ar_fayd_safi"]["text"]
    assert "یادداشتِ ۶۰" in " ".join(record["cite"] for record in _all_records(verses["5:38"]))

    v39 = _by_source(verses["5:39"]["classical"])
    assert "حقِّ مردم" in v39["ar_ibn_kathir_qurancom"]["text"]
    assert "کفارهٔ گناه" in v39["ar_tabari_qurancom"]["text"]
    assert "زمانِ ارجاعِ سارق به امام" in v39["ar_fayd_safi"]["text"]
    assert "یادداشتِ ۶۱" in " ".join(record["cite"] for record in _all_records(verses["5:39"]))

    v40 = _by_source(verses["5:40"]["classical"])
    assert "شرحِ مستقلِ «ملك»" in v40["ar_fayd_safi"]["text"]
    assert "احراز نشد" in v40["ar_fayd_safi"]["text"]
    assert "بی‌یادداشتِ تفسیریِ مستقل" in " ".join(record["cite"] for record in _all_records(verses["5:40"]))

    v41 = _by_source(verses["5:41"]["classical"])
    assert "ابولبابه" in v41["ar_tabari_qurancom"]["text"]
    assert "ابن‌صوریا" in v41["ar_tusi_tibyan"]["text"]
    assert "روایتِ قمی" in v41["ar_fayd_safi"]["text"]
    assert "یک بازه" in _by_source(verses["5:41"]["modern"])["ar_wasit_qurancom"]["text"]
    assert "یادداشت‌های ۶۲–۶۸" in " ".join(record["cite"] for record in _all_records(verses["5:41"]))

    v42 = _by_source(verses["5:42"]["classical"])
    assert "رشوه" in v42["ar_tabari_qurancom"]["text"]
    assert "منسوخ به آیهٔ ۴۹" in v42["ar_jalalayn_qurancom"]["text"]
    assert "اختیار یا وجوبِ داوری" in v42["ar_tusi_tibyan"]["text"]
    assert "یادداشت‌های ۶۹–۷۰" in " ".join(record["cite"] for record in _all_records(verses["5:42"]))


def test_maida_5_37_42_models_are_separate_and_limited():
    for ayah in range(37, 43):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        model_records = {record["model"]: record for record in entry["modern"] if record.get("model")}
        assert set(model_records) == MODELS
        assert "تحریریِ چارچوب" in " ".join(record["limit"] for record in model_records.values())
        assert len({record["text"] for record in model_records.values()}) == 3
        assert "ایزوتسو" not in model_records["fillmore"]["cite"]
        assert "Fillmore" in model_records["fillmore"]["cite"]
        assert "معناشناسیِ شناختی" in model_records["cognitive"]["cite"]


def test_maida_5_37_42_keeps_pages_uninvented_and_drafts_under_review():
    for ayah in range(37, 43):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        for record in entry["classical"] + [item for item in entry["modern"] if item.get("sourceId")]:
            assert record["evidence"].strip() and record["limit"].strip()
            if "چاپ و صفحه" in record["cite"]:
                assert "احراز نشده" in record["cite"]
        assert "پیش‌نویس" in entry["status"]
    assert "راهنمایِ اقدام نیستند" in DOSSIER["editorialMethod"] or "راهنمایِ اقدام" in DOSSIER["editorialMethod"]
    assert "پیش‌نویس و نیازمندِ داوریِ تخصصی‌اند" in DOSSIER["editorialMethod"]
    assert "تطبیق‌های تاریخیِ مودودی" in DOSSIER["editorialMethod"]
