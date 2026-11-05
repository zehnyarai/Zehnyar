"""Coverage, grouped-source, attribution, and draft-quality checks for al-An'am 6:41–90."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import build_anam_6_41_90 as builder
import anam_6_41_90_data as curated

DOSSIER = json.loads((ROOT / "static" / "verse-dossiers.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))

TABARI, IBN, QURTUBI = builder.TABARI, builder.IBN, builder.QURTUBI
TUSI, FAYD = builder.TUSI, builder.FAYD
QURANENC, WASIT = builder.QURANENC, builder.WASIT
CLASSICAL = {TABARI, IBN, QURTUBI, TUSI, FAYD}
MODELS = {"izutsu", "fillmore", "cognitive"}
FIELDS = builder.FIELDS
COLLECTION_ID = "anam-6-41-90-cited"


def _by_source(records: list[dict]) -> dict[str, dict]:
    return {record["sourceId"]: record for record in records if record.get("sourceId")}


def _registry_by_id() -> dict[str, dict]:
    return {source["id"]: source for source in REGISTRY["sources"]}


def test_batch_has_fifty_ordered_dossiers_with_six_balanced_fields():
    expected = [f"6:{ayah}" for ayah in range(41, 91)]
    assert list(builder.VERSES) == expected
    assert set(curated.DATA) == set(expected)
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    assert len(DOSSIER["batches"]) >= 62

    batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-59")
    assert batch["range"] == "6:41–90" and batch["count"] == 50
    assert "شش فیلدِ پنج‌بندی" in batch["status"]
    assert "۶:۵۶" in batch["status"] and "خلأ" in batch["status"]
    assert "پیش‌نویس" in batch["status"] and "داوریِ تخصصی" in batch["status"]

    all_batch_texts: set[str] = set()
    for key in expected:
        entry = DOSSIER["verses"][key]
        assert entry["standard"] == 2
        assert "پیش‌نویس" in entry["status"] and "تخصصی" in entry["status"]
        texts: list[str] = []
        for field in FIELDS:
            items = entry[field]
            assert len(items) == 5, (key, field)
            for item in items:
                assert len(item["text"].split()) >= 14, (key, field, item["text"])
                assert item["cite"].strip() and item["evidence"].strip() and item["limit"].strip()
                texts.append(item["text"])
        assert len(texts) == len(set(texts)), f"Repeated field text in {key}"
        for text in texts:
            assert text not in all_batch_texts, f"Repeated prose across verses: {key}: {text}"
            all_batch_texts.add(text)

        classical = _by_source(entry["classical"])
        assert set(classical) == CLASSICAL
        if key == "6:56":
            assert classical[IBN]["kind"] == "source-coverage-note"
            assert "Al-An'am 55–56" in classical[IBN]["evidence"]
            assert "فقط ۶:۵۵" in classical[IBN]["evidence"]
            assert "تفسیر شمرده نمی‌شود" in classical[IBN]["limit"]
            assert sum(item["kind"] == "source-summary" for item in entry["classical"]) == 4
        else:
            assert all(item["kind"] == "source-summary" for item in entry["classical"])

        modern_sources = {item.get("sourceId") for item in entry["modern"] if item.get("sourceId")}
        models = {item.get("model") for item in entry["modern"] if item.get("model")}
        assert modern_sources == {QURANENC, WASIT}
        assert models == MODELS
        assert len({item["text"] for item in entry["modern"] if item.get("model")}) == 3
        assert all("تحریریِ چارچوب" in item["limit"] for item in entry["modern"] if item.get("model"))


def test_source_ranges_and_metadata_paths_are_explicit_and_correct():
    expected_tusi = {
        "6:41": (40, 41), "6:42": (42, 43), "6:44": (44, 45),
        "6:48": (48, 49), "6:61": (61, 62), "6:66": (66, 67),
        "6:76": (76, 79), "6:84": (84, 90),
    }
    expected_fayd = {
        "6:41": (36, 41), "6:42": (42, 49), "6:50": (50, 53),
        "6:54": (54, 59), "6:60": (60, 65), "6:66": (66, 71),
        "6:72": (72, 75), "6:76": (76, 79), "6:80": (80, 81),
        "6:82": (82, 90),
    }
    for key, span in expected_tusi.items():
        assert builder.TUSI_GROUPS[key] == span
        item = _by_source(DOSSIER["verses"][key]["classical"])[TUSI]
        assert builder.tusi_scope(key) in item["cite"]
        assert builder.tusi_scope(key) in item["evidence"]
    for key, span in expected_fayd.items():
        assert builder.FAYD_GROUPS[key] == span
        item = _by_source(DOSSIER["verses"][key]["classical"])[FAYD]
        assert builder.fayd_scope(key) in item["cite"]
        assert builder.fayd_scope(key) in item["evidence"]

    assert builder.source_url(IBN, "6:55").endswith("/6/55/tafsirs/ar-tafsir-ibn-kathir")
    assert builder.source_url(IBN, "6:56").endswith("/6/55/tafsirs/ar-tafsir-ibn-kathir")
    assert "۶:۵۵–۵۶" in _by_source(DOSSIER["verses"]["6:55"]["classical"])[IBN]["cite"]

    by_id = _registry_by_id()
    tusi_path = "data/0460ShaykhTusi/0460ShaykhTusi.Tibyan/0460ShaykhTusi.Tibyan.Tafsir04039-ara1.yml"
    fayd_path = "data/1091MuhammadMuhsinFaydKashani/1091MuhammadMuhsinFaydKashani.TafsirSafi/1091MuhammadMuhsinFaydKashani.TafsirSafi.Tafsir04041-ara1.yml"
    assert by_id[TUSI]["researchSnapshot"]["metadataPath"] == tusi_path
    assert by_id[FAYD]["researchSnapshot"]["metadataPath"] == fayd_path
    snapshot = DOSSIER["sourceSnapshots"]["anam_6_41_90"]
    assert snapshot["openIti"][TUSI]["metadataPath"] == tusi_path
    assert snapshot["openIti"][FAYD]["metadataPath"] == fayd_path
    assert snapshot["scopeNotes"]["ibnKathir"].startswith("The archive entry heading spans Al-An'am 55–56")
    assert snapshot["openIti"][FAYD].get("deathDate") is None

    fayd_cite = _by_source(DOSSIER["verses"]["6:41"]["classical"])[FAYD]["cite"]
    assert "صفحه احراز نشده" in fayd_cite
    assert "وفات" not in fayd_cite and "چاپِ" not in fayd_cite


def test_disagreements_and_attributed_reports_are_not_collapsed():
    verses = DOSSIER["verses"]
    v41 = _by_source(verses["6:41"]["classical"])[TUSI]
    assert "ترکِ دعا" in v41["text"] and "فراموشی" in v41["text"]
    assert any(
        "ساعتِ ناگزیر" in item["text"] and "آسیبِ قابلِ رفع" in item["text"]
        for item in verses["6:41"]["critical"]
    )

    v56 = _by_source(verses["6:56"]["classical"])[IBN]
    assert v56["kind"] == "source-coverage-note"
    assert "شرحِ ۶:۵۵" not in v56["text"]

    v65 = _by_source(verses["6:65"]["classical"])[FAYD]["text"]
    assert "باقر و صادق" in v65 and "اهلِ قبله" in v65

    v74 = _by_source(verses["6:74"]["classical"])
    assert "تارح" in v74[QURTUBI]["text"]
    assert "جد" in v74[FAYD]["text"] and "عمو" in v74[FAYD]["text"]
    assert "تارح" in v74[TUSI]["text"]

    v75_fayd = _by_source(verses["6:75"]["classical"])[FAYD]["text"]
    assert "محمد" in v75_fayd and "علی" in v75_fayd and "امامان" in v75_fayd
    assert "نه اجماع" in " ".join(item["text"] for item in verses["6:75"]["critical"])

    v79_fayd = _by_source(verses["6:79"]["classical"])[FAYD]["text"]
    assert "رضا" in v79_fayd and "انکار" in v79_fayd
    assert "نه اجماع" in " ".join(item["text"] for item in verses["6:79"]["critical"])

    v82_tusi = _by_source(verses["6:82"]["classical"])[TUSI]["text"]
    assert "گناهانِ کبیره" in v82_tusi and "شرک" in v82_tusi
    v90_tusi = _by_source(verses["6:90"]["classical"])[TUSI]["text"]
    assert "شریعتِ پیشین" in v90_tusi and "دلیل‌هایِ پیامبران" in v90_tusi


def test_notice_catalog_method_and_attribution_are_idempotent_and_caveated():
    assert CATALOG["version"] >= 40
    assert len(CATALOG["collections"]) >= 37
    collection = next(item for item in CATALOG["collections"] if item["id"] == COLLECTION_ID)
    assert collection["comparativeCore"]["scope"] == "انعام ۶:۴۱–۹۰؛ یک پوششِ صریحِ منبعی برایِ ۶:۵۶ ثبت نشده است"
    assert "مدخلِ ابن‌کثیر عنوانِ ۵۵–۵۶ دارد" in collection["comparativeCore"]["note"]
    assert "خلأ" in collection["comparativeCore"]["note"]
    assert {item["id"] for item in collection["items"]} == set(builder.SOURCE_ORDER)

    notice = DOSSIER["notice"]
    assert "مائده در این checkout بازهٔ ۵:۱–۱۲۰" in notice
    assert "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است" in notice
    assert "ادامهٔ ترتیبیِ همین سوره از ۷:۱۰۱ است" in notice
    assert notice.count("مجوزِ متنِ تفسیریِ آرشیوهایِ Quran.com") == 1
    assert notice.count("خلاصه‌ها نقلِ لفظی نیستند") == 1
    assert "خلأِ بدنهٔ ابن‌کثیر در ۶:۵۶" in notice

    method = DOSSIER["editorialMethod"]
    assert method.count("در بستهٔ انعام ۶:۴۱–۹۰") == 1
    assert "در بستهٔ مائده ۵:۱۱۱–۱۲۰ و انعام ۶:۱–۴۰" in method
    assert builder.update_method(method) == method

    attribution = (ROOT / "data" / "TAFSIR_ATTRIBUTION.md").read_text(encoding="utf-8")
    assert attribution.count("## ۶. منابعِ بررسی‌شده برایِ بستهٔ انعام ۶:۴۱–۹۰") == 1
    assert "metadata volume file `data/0460ShaykhTusi/0460ShaykhTusi.Tibyan/0460ShaykhTusi.Tibyan.Tafsir04039-ara1.yml`" in attribution
    assert "metadata volume file `data/1091MuhammadMuhsinFaydKashani/1091MuhammadMuhsinFaydKashani.TafsirSafi/1091MuhammadMuhsinFaydKashani.TafsirSafi.Tafsir04041-ara1.yml`" in attribution
    assert "صفحهٔ چاپی تعیین نشده" in attribution
