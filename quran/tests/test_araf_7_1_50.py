"""Coverage, source-marker, and draft-quality checks for al-A'raf 7:1–50."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import araf_7_1_50_data as curated
import build_araf_7_1_50 as builder

DOSSIER_PATH = ROOT / "static" / "verse-dossiers.json"
CATALOG_PATH = ROOT / "static" / "tafsir-catalog.json"
REGISTRY_PATH = ROOT / "static" / "tafsir-sources.json"
ATTRIBUTION_PATH = ROOT / "data" / "TAFSIR_ATTRIBUTION.md"
DOSSIER = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))
CATALOG = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
REGISTRY = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

TABARI, IBN, QURTUBI = builder.TABARI, builder.IBN, builder.QURTUBI
TUSI, FAYD = builder.TUSI, builder.FAYD
QURANENC, WASIT = builder.QURANENC, builder.WASIT
CLASSICAL = set(builder.CLASSICAL_ORDER)
MODELS = set(builder.MODELS)
FIELDS = builder.FIELDS
COLLECTION_ID = builder.COLLECTION_ID
BATCH_ID = builder.BATCH_ID
EXPECTED = [f"7:{ayah}" for ayah in range(1, 51)]


def _by_source(items: list[dict]) -> dict[str, dict]:
    return {item["sourceId"]: item for item in items if item.get("sourceId")}


def test_batch_has_fifty_complete_distinct_dossiers_and_preserves_prior_ranges():
    assert list(builder.VERSES) == EXPECTED
    assert list(curated.DATA) == EXPECTED
    builder.validate_data(REGISTRY)
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    assert len(DOSSIER["batches"]) >= 62
    assert all(f"6:{ayah}" in DOSSIER["verses"] for ayah in range(1, 166))
    assert all(key in DOSSIER["verses"] for key in EXPECTED)
    batch_ids = [item["id"] for item in DOSSIER["batches"]]
    batch_index = batch_ids.index(BATCH_ID)
    assert batch_ids[batch_index - 2:batch_index + 1] == ["dossier-60", "dossier-61", BATCH_ID]
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])

    batch = next(item for item in DOSSIER["batches"] if item["id"] == BATCH_ID)
    assert batch["range"] == "7:1–50" and batch["count"] == 50
    assert "شش فیلد" in batch["status"] and "پنج‌بندی" in batch["status"]
    assert "پنج شرحِ کهن و دو شرحِ معاصر" in batch["status"]
    assert "سه کاربستِ معنایی جداست" in batch["status"]
    assert "قرطبی در ۷:۳۶" in batch["status"]
    assert "پیش‌نویس" in batch["status"] and "داوریِ تخصصی" in batch["status"]

    batch_texts: set[str] = set()
    for key in EXPECTED:
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
                texts.append(" ".join(item["text"].split()))
        assert len(texts) == len(set(texts)), f"Repeated prose within {key}"
        for text in texts:
            assert text not in batch_texts, f"Repeated prose across verses: {key}: {text}"
            batch_texts.add(text)

        classical = _by_source(entry["classical"])
        assert set(classical) == CLASSICAL
        assert all(item["kind"] == "source-summary" for sid, item in classical.items() if not (key == "7:36" and sid == QURTUBI))
        modern_sources = {item.get("sourceId") for item in entry["modern"] if item.get("sourceId")}
        models = {item.get("model") for item in entry["modern"] if item.get("model")}
        assert modern_sources == {QURANENC, WASIT}
        assert models == MODELS
        assert len({item["text"] for item in entry["modern"] if item.get("model")}) == 3
        assert all("تحریریِ چارچوب" in item["limit"] for item in entry["modern"] if item.get("model"))
        assert all(not item.get("sourceId") for field in ("notes", "context", "critical", "research") for item in entry[field])
        assert all(item["kind"] == "editorial-critique" for item in entry["critical"])
        assert all(item["kind"] == "editorial-question" for item in entry["research"])


def test_openiti_and_wasit_marker_ranges_are_mapped_without_invented_pages():
    expected_tusi_groups = {
        1: (1, 2), 2: (1, 2), 6: (6, 7), 7: (6, 7),
        8: (8, 9), 9: (8, 9), 14: (14, 15), 15: (14, 15),
        16: (16, 17), 17: (16, 17), 29: (29, 30), 30: (29, 30),
    }
    for ayah in range(1, 51):
        key = f"7:{ayah}"
        expected = expected_tusi_groups.get(ayah, (ayah, ayah))
        assert builder.TUSI_GROUPS[key] == expected
        classical = _by_source(DOSSIER["verses"][key]["classical"])
        tusi, fayd = classical[TUSI], classical[FAYD]
        assert "OpenITI/0475AH" in tusi["cite"] and "metadata volume file" in tusi["cite"]
        assert "OpenITI/1100AH" in fayd["cite"] and "metadata volume file" in fayd["cite"]
        assert "چاپ و صفحه احراز نشده" in tusi["cite"]
        assert "چاپ و صفحه احراز نشده" in fayd["cite"]
        assert "وفات" not in fayd["cite"] and "وفات" not in fayd["text"]
        assert tusi["sourceUrl"] and fayd["sourceUrl"]
        assert "۷:" in tusi["cite"] and "۷:" in fayd["cite"]
        if expected[0] == expected[1]:
            assert "شرحِ مستقیم" in tusi["cite"]
        else:
            assert "شرحِ گروهی" in tusi["cite"]

    expected_fayd = (
        (1, 1), (2, 2), (3, 3), (4, 9), (10, 15), (16, 22), (23, 28),
        (29, 31), (32, 32), (33, 33), (34, 38), (39, 44), (45, 46),
        (47, 49), (50, 54),
    )
    for start, end in expected_fayd:
        for ayah in range(max(start, 1), min(end, 50) + 1):
            assert builder.FAYD_GROUPS[f"7:{ayah}"] == (start, end)
            cite = _by_source(DOSSIER["verses"][f"7:{ayah}"]["classical"])[FAYD]["cite"]
            fa_start, fa_end = builder.fa_num(start), builder.fa_num(end)
            assert f"اعراف ۷:{fa_start}" in cite
            if start != end:
                assert f"–{fa_end}" in cite

    assert builder.WASIT_GROUPS == {"7:35": (35, 36), "7:36": (35, 36)}
    wasit35 = _by_source(DOSSIER["verses"]["7:35"]["modern"])[WASIT]
    wasit36 = _by_source(DOSSIER["verses"]["7:36"]["modern"])[WASIT]
    for item in (wasit35, wasit36):
        assert "اعراف ۷:۳۵–۳۶" in item["cite"]
        assert "یک بدنهٔ یکسان" in item["evidence"]
        assert "/7/35/tafsirs/" in item["sourceUrl"]

    gap = _by_source(DOSSIER["verses"]["7:36"]["classical"])[QURTUBI]
    assert gap["kind"] == "source-coverage-note"
    assert "لا يوجد تفسير لهذه الأية" in gap["text"]
    assert "خلأ" in gap["evidence"] and "کلِ اثر" in gap["limit"]
    assert "/7/36/tafsirs/" in gap["sourceUrl"]

    snapshots = DOSSIER["sourceSnapshots"]["araf_7_1_50"]
    assert snapshots["batchId"] == BATCH_ID and snapshots["range"] == "7:1–50"
    assert "grouped 7:1–2" in snapshots["scopeNotes"]["tusi"]
    assert "7:50–54" in snapshots["scopeNotes"]["fayd"]
    assert "same body" in snapshots["scopeNotes"]["wasit"]
    assert "explicitly says no tafsir" in snapshots["scopeNotes"]["qurancom"]
    assert snapshots["rawWorkBench"]["path"] == "/tmp/araf/sources.json"
    assert snapshots["rawWorkBench"]["sha256"] == "d9e82786be7355349f1d02592e69748bf330f2fad2da0ba8dc28569e4ea3ad66"
    assert snapshots["rawWorkBench"]["quranEbookZipSha256"] == "1ab619c4b4c6b71b18db2a4a602bb1b810d17f590bbd150a3460f43bb76bf842"
    for source_id in (TUSI, FAYD):
        openiti_snapshot = snapshots["openIti"][source_id]
        assert openiti_snapshot.get("deathDate") is None
        assert openiti_snapshot["edition"] == "not identified"
        assert openiti_snapshot["pagination"] == "not specified"

    registry = {item["id"]: item for item in REGISTRY["sources"]}
    assert REGISTRY["version"] >= 11
    for source_id in (TUSI, FAYD):
        record = registry[source_id]
        assert BATCH_ID in record["researchSnapshot"]["coveredBatches"]
        assert record["researchSnapshot"]["edition"] == "not identified"
        assert record["researchSnapshot"]["pagination"] == "not specified"
        assert record["licenseStatus"] == "unresolved"


def test_verse_specific_disagreements_critical_cautions_and_context_are_visible():
    verses = DOSSIER["verses"]

    v1 = _by_source(verses["7:1"]["classical"])
    assert "نامِ سوره‌دانستن" in v1[TUSI]["text"]
    assert "روایت‌هایِ امامی" in v1[FAYD]["text"]
    assert "توقف" in v1[QURTUBI]["text"]

    v12 = _by_source(verses["7:12"]["classical"])
    assert "«لا»" in v12[IBN]["text"] and "قیاسِ نادرست" in v12[TABARI]["text"]
    assert "ترتیبِ ماده‌هایِ آفرینش" in " ".join(item["text"] for item in verses["7:12"]["critical"])

    v15 = _by_source(verses["7:15"]["classical"])
    assert "نفخهٔ نخست" in v15[QURTUBI]["text"]
    assert "تعیینِ نفخهٔ نخست یا دوم" in " ".join(item["text"] for item in verses["7:15"]["critical"])

    v28 = _by_source(verses["7:28"]["classical"])
    assert "طوافِ برهنه" in v28[IBN]["text"]
    assert "شرک و کفر" in v28[QURTUBI]["text"]
    assert "طوافِ برهنه" in " ".join(item["text"] for item in verses["7:28"]["notes"])

    v32 = _by_source(verses["7:32"]["classical"])
    assert "رفع و نصبِ «خالصة»" in v32[TUSI]["text"]

    v46 = _by_source(verses["7:46"]["classical"])
    assert "امامانِ آلِ محمد" in v46[FAYD]["text"]
    assert "تساویِ اعمال" in v46[FAYD]["text"]
    v46_critical = " ".join(item["text"] for item in verses["7:46"]["critical"])
    assert "روایاتِ امامی" in v46_critical and "یکی نگیرید" in v46_critical

    v49 = _by_source(verses["7:49"]["classical"])
    assert "چند قول دربارهٔ گوینده" in v49[TABARI]["text"]
    assert "بلال و سلمان" in v49[QURTUBI]["text"]
    assert "نام‌هایِ بلال، سلمان و خباب" in " ".join(item["text"] for item in verses["7:49"]["critical"])

    assert "انعام ۶:۱۶۵" in verses["7:1"]["context"][0]["text"] and "پیش ازِ اعراف ۷:۱" in verses["7:1"]["context"][0]["text"]
    assert "پس ازِ اعراف ۷:۴۹، اعراف ۷:۵۰" in verses["7:49"]["context"][2]["text"]
    assert "اعراف ۷:۵۱" in verses["7:50"]["context"][2]["text"]
    assert "دسته‌بندیِ پژوهشیِ امروز" in verses["7:50"]["context"][3]["text"]


def test_catalog_registry_notice_method_and_attribution_are_current_and_caveated():
    assert CATALOG["version"] >= 40
    assert len(CATALOG["collections"]) >= 37
    collection = next(item for item in CATALOG["collections"] if item["id"] == COLLECTION_ID)
    assert {item["id"] for item in collection["items"]} == set(builder.SOURCE_ORDER)
    assert collection["comparativeCore"]["scope"].startswith("اعراف ۷:۱–۵۰")
    assert "طنطاوی در ۷:۳۵–۳۶ یک مدخلِ گروهی دارد" in collection["comparativeCore"]["note"]
    assert "لا يوجد تفسير لهذه الأية" in collection["comparativeCore"]["note"]
    assert "خلاصه‌ها بازنویسی‌اند، نه نقلِ لفظی" in collection["comparativeCore"]["note"]
    assert "مجوز" in collection["notice"] and "پیش‌نویس" in collection["notice"]
    catalog_by_id = {item["id"]: item for item in collection["items"]}
    assert "بدنهٔ ذخیره‌شدهٔ ۷:۳۶" in catalog_by_id[QURTUBI]["scope"]
    assert "یک بدنهٔ گروهیِ یکسان" in catalog_by_id[WASIT]["scope"]
    assert "۵۰–۵۴" in catalog_by_id[FAYD]["scope"]

    notice = DOSSIER["notice"]
    assert "اعراف بازهٔ ۷:۱–۱۰۰ را پوشش می‌دهد" in notice
    assert "ادامهٔ ترتیبیِ همین سوره از ۷:۱۰۱ است" in notice
    assert "پیش‌نویس" in notice and "بازبینیِ تخصصی انجام نشده" in notice
    assert "مجوزِ متنِ تفسیریِ آرشیوهایِ Quran.com" in notice
    method = DOSSIER["editorialMethod"]
    assert "طنطاوی در ۷:۳۵–۳۶" in method
    assert "ادامهٔ ترتیبیِ بعدی اعراف ۷:۵۱–۱۰۰" in method
    assert "ایزوتسو، فیلمور و معناشناسیِ شناختی" in method

    text = ATTRIBUTION_PATH.read_text(encoding="utf-8")
    assert "## ۹. منابعِ بررسی‌شده برایِ بستهٔ اعراف ۷:۱–۵۰" in text
    assert "1ab619c4b4c6b71b18db2a4a602bb1b810d17f590bbd150a3460f43bb76bf842" in text
    assert "d9e82786be7355349f1d02592e69748bf330f2fad2da0ba8dc28569e4ea3ad66" in text
    assert "تاریخِ وفات، چاپ و صفحه در این پرونده حدس زده نشده‌اند" in text
