"""Source-scope, exception, rights, and draft-quality checks for Ma'idah 5:111–120 and al-An'am 6:1–40."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import build_maida_5_111_120_anam_6_1_40 as builder
import maida_5_111_120_anam_6_1_40_data as curated

DOSSIER = json.loads((ROOT / "static" / "verse-dossiers.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))

TABARI = "ar_tabari_qurancom"
IBN = "ar_ibn_kathir_qurancom"
QURTUBI = "ar_qurtubi_qurancom"
TUSI = "ar_tusi_tibyan"
FAYD = "ar_fayd_safi"
QURANENC = "ar_qe_arabic_moyassar"
WASIT = "ar_wasit_qurancom"
SUNNI = {TABARI, IBN, QURTUBI}
SHIA = {TUSI, FAYD}
CLASSICAL = {TABARI, IBN, QURTUBI, TUSI, FAYD}
MODELS = {"izutsu", "fillmore", "cognitive"}
FIELDS = ("notes", "context", "classical", "modern", "critical", "research")
COLLECTION_ID = "maida-5-111-120-anam-6-1-40-cited"


def _by_source(records: list[dict]) -> dict[str, dict]:
    return {record["sourceId"]: record for record in records if record.get("sourceId")}


def _target_keys() -> list[str]:
    return [*(f"5:{ayah}" for ayah in range(111, 121)), *(f"6:{ayah}" for ayah in range(1, 41))]


def _verse_url(source_id: str, key: str) -> str:
    surah, ayah = key.split(":")
    return f"https://quran.com/{surah}/{ayah}/tafsirs/{builder.QURANCOM_SLUGS[source_id]}"


def test_batch_has_fifty_balanced_drafts_and_preserves_inventory():
    expected_keys = _target_keys()
    assert list(builder.VERSES) == expected_keys
    assert set(curated.DATA) == set(expected_keys)
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    assert len(DOSSIER["batches"]) >= 62

    batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-58")
    assert batch["range"] == "5:111–120; 6:1–40" and batch["count"] == 50
    assert "پیش‌نویسِ نیازمندِ داوریِ تخصصی" in batch["status"]
    assert "چهار خلاصه و یک یادداشتِ خلأ" in batch["status"]
    assert "مجوزِ اقتباس/بازنشرِ متن‌هایِ آرشیوی هنوز احراز نشده" in batch["status"]
    assert "مائده در این checkout بازهٔ ۵:۱–۱۲۰" in DOSSIER["notice"]
    assert "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است" in DOSSIER["notice"]
    assert "در بستهٔ مائده ۵:۱۱۱–۱۲۰ و انعام ۶:۱–۴۰" in DOSSIER["editorialMethod"]

    for key in expected_keys:
        entry = DOSSIER["verses"][key]
        assert entry["status"].startswith("پیش‌نویس") and "تخصصی" in entry["status"]
        assert entry["standard"] == 2
        for field in FIELDS:
            records = entry[field]
            assert len(records) == 5, (key, field)
            assert all(record["text"].strip() and len(record["text"].split()) >= 14 for record in records), (key, field)
            assert all(record["cite"].strip() and record["evidence"].strip() for record in records), (key, field)
            assert all(record.get("limit", "").strip() for record in records), (key, field)

        classical = entry["classical"]
        classical_by_source = _by_source(classical)
        assert set(classical_by_source) == CLASSICAL, key
        if key == "6:26":
            gap = classical_by_source[FAYD]
            assert gap["kind"] == "source-coverage-note"
            assert "نشانِ (۲۵) به (۲۷)" in gap["text"]
            assert "پنجمین تفسیر شمرده نمی‌شود" in gap["limit"]
            assert sum(item["kind"] == "source-summary" for item in classical) == 4
        else:
            assert all(classical_by_source[source]["kind"] == "source-summary" for source in CLASSICAL)
        assert {record["tradition"] for record in classical if record["sourceId"] in SUNNI} == {"اهل‌سنت"}
        assert {record["tradition"] for record in classical if record["sourceId"] in SHIA} == {"شیعهٔ امامیه"}

        modern = _by_source(entry["modern"])
        assert set(modern) == {QURANENC, WASIT}
        models = {record["model"]: record for record in entry["modern"] if record.get("model")}
        assert set(models) == MODELS
        assert len({record["text"] for record in models.values()}) == 3
        assert all("تحریریِ چارچوب" in record["limit"] for record in models.values())
        assert all(record["kind"] == "editorial-method-application" for record in models.values())


def test_direct_and_grouped_source_scopes_are_not_misrepresented():
    for key in _target_keys():
        classical = _by_source(DOSSIER["verses"][key]["classical"])
        for source_id in (TABARI, IBN, QURTUBI):
            assert classical[source_id]["sourceUrl"] == _verse_url(source_id, key)
        assert classical[TUSI]["sourceUrl"] == builder.TUSI_URL
        assert classical[FAYD]["sourceUrl"] == builder.FAYD_URL
        assert builder.tusi_scope(key) in classical[TUSI]["cite"]
        assert builder.tusi_scope(key) in classical[TUSI]["evidence"]
        assert builder.fayd_scope(key).split(" ", 1)[1] in classical[FAYD]["cite"]
        assert builder.fayd_scope(key).split(" ", 1)[1] in classical[FAYD]["evidence"]

    assert builder.TUSI_GROUPS["5:119"] == builder.TUSI_GROUPS["5:120"] == (119, 120)
    assert builder.tusi_scope("5:120") == "مائده ۵:۱۱۹–۱۲۰"
    for first, second in ((8, 9), (12, 13), (17, 18), (23, 24), (29, 30)):
        assert builder.TUSI_GROUPS[f"6:{first}"] == builder.TUSI_GROUPS[f"6:{second}"] == (first, second)
    assert builder.TUSI_GROUPS["6:40"] == (40, 41)

    v2 = _by_source(DOSSIER["verses"]["6:2"]["classical"])[FAYD]
    assert builder.FAYD_GROUPS["6:2"] == (1, 4)
    assert "نشانِ جداگانهٔ (۲) ثبت نشده است" in v2["text"]
    assert "هو الذي خلقكم من طين" in v2["evidence"]
    assert "۶:۱–۴" in v2["cite"]
    v26 = _by_source(DOSSIER["verses"]["6:26"]["classical"])[FAYD]
    assert builder.FAYD_GROUPS["6:26"] == (25, 31)
    assert "از نشانِ (۲۵) به (۲۷) می‌پرد" in v26["text"]
    assert "برایِ ۶:۲۶" in v26["evidence"]

    for key in ("6:4", "6:5"):
        wasit = _by_source(DOSSIER["verses"][key]["modern"])[WASIT]
        assert builder.source_url(WASIT, key) == "https://quran.com/6/4/tafsirs/ar-tafsir-al-wasit"
        assert "۶:۴–۵" in wasit["cite"]
        assert "هر دو آیه را شرح می‌دهد" in wasit["evidence"]

    tusi_640 = _by_source(DOSSIER["verses"]["6:40"]["classical"])[TUSI]
    assert "شرحِ گروهیِ انعام ۶:۴۰–۴۱" in tusi_640["cite"]
    assert "۶:۴۰–۴۱" in tusi_640["evidence"]


def test_disagreements_and_editorial_analysis_remain_separate():
    verses = DOSSIER["verses"]
    v112 = _by_source(verses["5:112"]["classical"])
    assert "هل تستطيع" in v112[TABARI]["text"]
    assert "هل يستطيع/هل تستطيع" in v112[IBN]["text"]
    assert "قدرتِ خدا" in v112[QURTUBI]["text"]

    v115 = _by_source(verses["5:115"]["classical"])
    assert "نزول" in v115[TABARI]["text"]
    assert "فرونفرستادنِ مائده" in v115[QURTUBI]["text"] and "نظرِ جمهور" in v115[QURTUBI]["text"]
    v116 = _by_source(verses["5:116"]["classical"])
    assert "رفعِ عیسی" in v116[TABARI]["text"] and "روزِ قیامت" in v116[TABARI]["text"]

    for key, source_id, needle in (
        ("6:2", IBN, "أجل مسمى عنده"),
        ("6:3", TUSI, "حلولِ مکانی"),
        ("6:23", QURTUBI, "فتنه"),
        ("6:31", TUSI, "پاداش و کیفر"),
        ("6:33", TUSI, "قرائت"),
    ):
        source_text = _by_source(verses[key]["classical"])[source_id]["text"]
        assert needle in source_text

    for key in _target_keys():
        entry = verses[key]
        assert all(not record.get("sourceId") for record in entry["critical"] + entry["research"])
        assert all(record["kind"] == "editorial-critique" for record in entry["critical"])
        assert all(record["kind"] == "editorial-question" for record in entry["research"])
        models = {record["model"]: record for record in entry["modern"] if record.get("model")}
        assert "ایزوتسو" in models["izutsu"]["cite"]
        assert "Fillmore" in models["fillmore"]["cite"]
        assert "معناشناسیِ شناختی" in models["cognitive"]["cite"]
        assert all(not record.get("sourceId") for record in models.values())


def test_catalog_registry_snapshots_and_rights_notes_are_complete():
    assert CATALOG["version"] >= 40
    assert len(CATALOG["collections"]) >= 37
    collection = next(item for item in CATALOG["collections"] if item["id"] == COLLECTION_ID)
    assert collection["comparativeCore"]["scope"].startswith("مائده ۵:۱۱۱–۱۲۰ و انعام ۶:۱–۴۰")
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == SUNNI
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == SHIA
    by_id = {item["id"]: item for item in collection["items"]}
    assert set(by_id) == {TABARI, IBN, QURTUBI, TUSI, FAYD, QURANENC, WASIT}
    assert len(by_id[TABARI]["sourceUrls"]) == 50
    assert len(by_id[IBN]["sourceUrls"]) == 50
    assert len(by_id[QURTUBI]["sourceUrls"]) == 50
    assert len(by_id[TUSI]["sourceUrls"]) == 1
    assert len(by_id[FAYD]["sourceUrls"]) == 1
    assert len(by_id[QURANENC]["sourceUrls"]) == 1
    assert len(by_id[WASIT]["sourceUrls"]) == 49
    assert "گروهِ واقعیِ ۶:۴–۵" in by_id[WASIT]["scope"]

    assert REGISTRY["version"] >= 11
    assert len(REGISTRY["sources"]) == 15
    registry = {item["id"]: item for item in REGISTRY["sources"]}
    for source_id in (TUSI, FAYD):
        assert registry[source_id]["licenseStatus"] == "unresolved"
        assert "احراز نشده" in registry[source_id]["license"]
    for source_id in (TABARI, IBN, QURTUBI, WASIT):
        assert registry[source_id]["licenseStatus"] == "review-needed"
        assert "GPL-3.0" in registry[source_id]["license"]
        assert "دامنهٔ آن نسبت به متنِ تفسیری" in registry[source_id]["license"]

    snapshot = DOSSIER["sourceSnapshots"]["maida_111_120_anam_6_1_40"]
    assert snapshot["quranEbook"]["commit"] == builder.QURAN_EBOOK_COMMIT
    assert snapshot["openIti"][TUSI]["commit"] == builder.OPENITI_TUSI_COMMIT
    assert snapshot["openIti"][FAYD]["commit"] == builder.OPENITI_FAYD_COMMIT
    assert snapshot["openIti"][TUSI]["metadataPath"] == "data/0460ShaykhTusi/0460ShaykhTusi.Tibyan/0460ShaykhTusi.Tibyan.Tafsir04039-ara1.yml"
    assert snapshot["openIti"][FAYD]["metadataPath"] == "data/1091MuhammadMuhsinFaydKashani/1091MuhammadMuhsinFaydKashani.TafsirSafi/1091MuhammadMuhsinFaydKashani.TafsirSafi.Tafsir04041-ara1.yml"
    assert snapshot["openIti"][TUSI]["metadataGitBlobSha"] == "5198ad76db15585eed0cbf9b516e9e1b102b2572"
    assert snapshot["openIti"][FAYD]["metadataGitBlobSha"] == "a792babb30635c941a7864463428356ecb45481e"
    assert "unresolved" in snapshot["quranEbook"]["textRightsStatus"]
    assert all("unresolved" in snapshot["openIti"][source]["licenseStatus"] for source in (TUSI, FAYD))

    attribution = (ROOT / "data" / "TAFSIR_ATTRIBUTION.md").read_text(encoding="utf-8")
    assert builder.QURAN_EBOOK_COMMIT in attribution
    assert "مجوزی در این بررسی احراز نشد" in attribution
    assert "نسخه‌هایی ناقص و اخذشده از altafsir.com" in attribution
    assert "موضعِ ۶:۲۶ غایب است" in attribution


def test_builder_validates_curated_data_against_registered_sources():
    builder.validate_data(REGISTRY)
