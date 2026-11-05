"""Source-scope, exception, and draft-quality checks for Al-Ma'idah 5:61–110."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import build_maida_5_61_110 as builder
import maida_5_61_110_data as curated

DOSSIER = json.loads((ROOT / "static" / "verse-dossiers.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))

TABARI = "ar_tabari_qurancom"
IBN = "ar_ibn_kathir_qurancom"
QURTUBI = "ar_qurtubi_qurancom"
JALALAYN = "ar_jalalayn_qurancom"
TUSI = "ar_tusi_tibyan"
FAYD = "ar_fayd_safi"
QURANENC = "ar_qe_arabic_moyassar"
WASIT = "ar_wasit_qurancom"
SUNNI = {TABARI, IBN, QURTUBI}
SHIA = {TUSI, FAYD}
MODELS = {"izutsu", "fillmore", "cognitive"}
FIELDS = ("notes", "context", "classical", "modern", "critical", "research")


def _by_source(records: list[dict]) -> dict[str, dict]:
    return {record["sourceId"]: record for record in records if record.get("sourceId")}


def _fa_num(value: int) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def _greattafsirs_url(tafsir_no: int, ayah_no: int) -> str:
    return (
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1"
        f"&MadhabNo=4&TafsirNo={tafsir_no}&SoraNo=5&AyahNo={ayah_no}&LanguageID=1"
    )


def test_maida_5_61_110_has_fifty_complete_balanced_drafts():
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    assert len(DOSSIER["batches"]) >= 62
    batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-57")
    assert batch["range"] == "5:61–110" and batch["count"] == 50
    assert "پیش‌نویسِ نیازمندِ داوریِ تخصصی" in batch["status"]
    assert "۵:۱۰۵ قرطبی در دسترس نبود" in batch["status"]
    assert "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است" in DOSSIER["notice"]
    assert "در بستهٔ مائده ۵:۶۱–۱۱۰" in DOSSIER["editorialMethod"]

    previous = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-56")
    assert previous["range"] == "5:55–60"
    assert "پیش از این بسته، مائده تا ۵:۶۰ پوشش داشت" in batch["status"]

    for ayah in range(61, 111):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        assert entry["status"].startswith("پیش‌نویس") and "تخصصی" in entry["status"]
        assert entry["standard"] == 2
        for field in FIELDS:
            assert len(entry[field]) == 5, (ayah, field)
            assert all(len(record["text"].split()) >= 14 for record in entry[field]), (ayah, field)
            assert all(record["cite"].strip() and record["evidence"].strip() for record in entry[field])

        classical = _by_source(entry["classical"])
        expected_classical = {TABARI, IBN, JALALAYN, TUSI, FAYD} if ayah == 105 else SUNNI | SHIA
        assert set(classical) == expected_classical
        assert {record["tradition"] for record in entry["classical"] if record["sourceId"] in SUNNI | {JALALAYN}} == {"اهل‌سنت"}
        assert {record["tradition"] for record in entry["classical"] if record["sourceId"] in SHIA} == {"شیعهٔ امامیه"}
        assert all(record["sourceUrl"].startswith("https://") for record in entry["classical"])
        assert all(record["limit"].strip() for record in entry["classical"])

        modern = _by_source(entry["modern"])
        assert set(modern) == {QURANENC, WASIT}
        models = {record["model"]: record for record in entry["modern"] if record.get("model")}
        assert set(models) == MODELS
        assert len({record["text"] for record in models.values()}) == 3
        assert all(record["cite"].strip() and record["evidence"].strip() for record in models.values())
        assert "تحریریِ چارچوب" in " ".join(record["limit"] for record in models.values())
        for record in entry["classical"] + [row for row in entry["modern"] if row.get("sourceId")]:
            assert record["sourceUrl"].startswith("https://")
            assert record["evidence"].strip() and record["limit"].strip()


def test_maida_5_61_110_records_direct_and_grouped_scopes():
    assert set(curated.DATA) == set(range(61, 111))
    for ayah in range(61, 111):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        classical = _by_source(entry["classical"])
        assert classical[TABARI]["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-al-tabari"
        assert classical[IBN]["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-ibn-kathir"
        if ayah != 105:
            assert classical[QURTUBI]["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-al-qurtubi"
        else:
            assert QURTUBI not in classical
            assert classical[JALALAYN]["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-jalalayn"

        page, start, end, _chunks = builder.TUSI_GROUPS[ayah]
        tusi = classical[TUSI]
        assert tusi["sourceUrl"] == _greattafsirs_url(39, page)
        assert builder.tusi_scope(ayah) in tusi["cite"]
        assert builder.tusi_scope(ayah) in tusi["evidence"]
        if ayah not in {101, 102}:
            assert start == end and f"AyahNo={ayah}" in tusi["cite"]
        else:
            assert (page, start, end) == (101, 101, 102)
            assert "AyahNo=101" in tusi["cite"]
            assert "۵:۱۰۱–۱۰۲" in tusi["cite"]

        fayd_page, fayd_start, fayd_end = builder.FAYD_GROUPS[ayah]
        fayd = classical[FAYD]
        assert fayd["sourceUrl"] == _greattafsirs_url(41, fayd_page)
        expected_scope = f"۵:{_fa_num(fayd_start)}–{_fa_num(fayd_end)}"
        assert expected_scope in fayd["cite"] and expected_scope in fayd["evidence"]

    for ayah in (89, 110):
        tusi = _by_source(DOSSIER["verses"][f"5:{ayah}"]["classical"])[TUSI]
        assert "قطعه‌هایِ ۰ و ۱ بررسی شدند" in tusi["cite"]
        assert "قطعه‌هایِ ۰ و ۱ خوانده شدند" in tusi["evidence"]

    for ayah in (61, 67, 68, 70, 76, 81, 86, 88, 90, 92, 94, 96, 104, 106, 109):
        assert builder.FAYD_GROUPS[ayah][0] == ayah
    assert builder.FAYD_GROUPS[61] == (61, 60, 64)
    assert builder.FAYD_GROUPS[96] == (96, 96, 101)
    assert builder.FAYD_GROUPS[102] == (104, 102, 105)
    assert builder.FAYD_GROUPS[110] == (109, 109, 113)


def test_maida_5_61_110_catalog_preserves_the_105_qurtubi_gap():
    assert CATALOG["version"] >= 36
    assert len(CATALOG["collections"]) >= 37
    collection = next(item for item in CATALOG["collections"] if item["id"] == "maida-5-61-110-cited")
    assert collection["comparativeCore"]["scope"].startswith("هر آیهٔ مائده ۵:۶۱–۱۱۰")
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == SUNNI
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == SHIA
    by_id = {item["id"]: item for item in collection["items"]}
    assert set(by_id) == {TABARI, IBN, QURTUBI, JALALAYN, TUSI, FAYD, QURANENC, WASIT}
    assert len(by_id[TABARI]["sourceUrls"]) == 50
    assert len(by_id[IBN]["sourceUrls"]) == 50
    assert len(by_id[QURTUBI]["sourceUrls"]) == 49
    assert all("/105/" not in url for url in by_id[QURTUBI]["sourceUrls"])
    assert by_id[JALALAYN]["sourceUrls"] == [
        "https://quran.com/al-maidah/105/tafsirs/ar-tafsir-jalalayn"
    ]
    assert "برایِ ۵:۱۰۵ شرحِ قابلِ استفاده" in by_id[QURTUBI]["basis"]
    assert "جلالین فقط برایِ همین آیه جایگزین شده است" in collection["comparativeCore"]["note"]

    assert len(by_id[TUSI]["sourceUrls"]) == 49
    assert _greattafsirs_url(39, 101) in by_id[TUSI]["sourceUrls"]
    assert _greattafsirs_url(39, 102) not in by_id[TUSI]["sourceUrls"]
    assert "۵:۱۰۱–۱۰۲" in by_id[TUSI]["scope"]
    assert "قطعهٔ دوم" in by_id[TUSI]["basis"]
    assert len(by_id[FAYD]["sourceUrls"]) == 15
    assert "۱۰۹–۱۱۳" in by_id[FAYD]["scope"]
    assert len(by_id[WASIT]["sourceUrls"]) == 50
    assert "جداگانه مقابله نشده" in by_id[WASIT]["basis"]
    assert REGISTRY["version"] >= 8 and len(REGISTRY["sources"]) == 15


def test_maida_5_61_110_keeps_attributions_and_open_questions_separate():
    verses = DOSSIER["verses"]
    v71 = _by_source(verses["5:71"]["classical"])
    assert "رفع و نصب" in v71["ar_tusi_tibyan"]["text"]
    assert "بازگشتِ دوباره" in v71["ar_fayd_safi"]["text"]

    v82 = _by_source(verses["5:82"]["classical"])
    assert "سازگار نیست" in v82[IBN]["text"]

    v89 = _by_source(verses["5:89"]["classical"])
    assert "لغو" in v89[TABARI]["text"]
    assert "قرائت‌هایِ" in v89[TUSI]["text"]

    v93 = _by_source(verses["5:93"]["classical"])
    assert "سه تکرارِ تقوا" in v93[TUSI]["text"]
    assert "رفعِ گناه" in _by_source(verses["5:93"]["modern"])[QURANENC]["text"]

    v101 = _by_source(verses["5:101"]["classical"])
    v102 = _by_source(verses["5:102"]["classical"])
    assert "شرحِ گروهیِ مائده ۵:۱۰۱–۱۰۲" in v101[TUSI]["cite"]
    assert "شرحِ گروهیِ مائده ۵:۱۰۱–۱۰۲" in v102[TUSI]["cite"]
    assert "پرسشِ پدر" in v101[TUSI]["text"]
    assert "مائده" in v102[TUSI]["text"]

    v103 = _by_source(verses["5:103"]["classical"])
    assert "جبر" in v103[TUSI]["text"]
    assert "اجماعِ مفسران" in verses["5:103"]["critical"][0]["text"] or "اجماع" in v103[TUSI]["text"]

    v105 = _by_source(verses["5:105"]["classical"])
    assert QURTUBI not in v105 and JALALAYN in v105
    assert "جلالین به‌جایِ قرطبی" in " ".join(row["text"] for row in verses["5:105"]["notes"])
    assert "قرطبی»" in " ".join(row["text"] for row in verses["5:105"]["critical"])
    assert "به جلالین نسبت ندهید" in verses["5:105"]["critical"][1]["text"]
    assert "مجوزِ بی‌اعتنایی به منکر نمی‌داند" in v105[IBN]["text"]

    for ayah in range(61, 111):
        critical_text = " ".join(row["text"] for row in verses[f"5:{ayah}"]["critical"])
        for doubled_author in ("می‌گوید طبری", "می‌گوید ابن‌کثیر", "می‌گوید قرطبی", "می‌گوید طوسی"):
            assert doubled_author not in critical_text, (ayah, doubled_author)

    v109 = _by_source(verses["5:109"]["classical"])
    assert "جانشینانِ پیامبران" in v109[FAYD]["text"]
    assert "چند تفسیرِ روایی و کلامی" in v109[QURTUBI]["text"]

    v110 = _by_source(verses["5:110"]["classical"])
    assert "قطعه‌هایِ ۰ و ۱ بررسی شدند" in v110[TUSI]["cite"]
    assert "دعایِ عیسی" in v110[TUSI]["text"]
    assert "اذنِ الهی" in v110[IBN]["text"]


def test_maida_5_61_110_models_and_bibliographic_limits_remain_distinct():
    for ayah in range(61, 111):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        models = {record["model"]: record for record in entry["modern"] if record.get("model")}
        assert set(models) == MODELS
        assert "ایزوتسو" in models["izutsu"]["cite"]
        assert "Fillmore" in models["fillmore"]["cite"]
        assert "معناشناسیِ شناختی" in models["cognitive"]["cite"]
        assert len({record["text"] for record in models.values()}) == 3
        assert all("مستقلاً تفسیر کرده باشد" in record["limit"] for record in models.values())
        for record in entry["classical"] + [row for row in entry["modern"] if row.get("sourceId")]:
            if "چاپ و صفحه" in record["cite"]:
                assert "احراز نشده" in record["cite"]
        assert "پیش‌نویس" in entry["status"]

    method = DOSSIER["editorialMethod"]
    assert "۵:۱۰۱–۱۰۲" in method
    assert "قطعهٔ دومِ ۵:۱۱۰" in method
    assert "قرطبی برایِ ۵:۱۰۵" in method
