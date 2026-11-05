"""Source coverage and draft-quality checks for al-A'raf 7:51–100."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import araf_7_51_100_data as curated
import build_araf_7_1_50 as earlier_araf_builder
import build_araf_7_51_100 as builder

STATIC = ROOT / "static"
DOSSIER = json.loads((STATIC / "verse-dossiers.json").read_text(encoding="utf-8"))
CATALOG = json.loads((STATIC / "tafsir-catalog.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((STATIC / "tafsir-sources.json").read_text(encoding="utf-8"))
ATTRIBUTION = (ROOT / "data" / "TAFSIR_ATTRIBUTION.md").read_text(encoding="utf-8")

EXPECTED = [f"7:{ayah}" for ayah in range(51, 101)]
BATCH_ID = builder.BATCH_ID
FIELDS = builder.FIELDS
CLASSICAL = set(builder.CLASSICAL_ORDER)
MODELS = set(builder.MODELS)


def _by_source(items: list[dict]) -> dict[str, dict]:
    return {item["sourceId"]: item for item in items if item.get("sourceId")}


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def test_batch_is_complete_source_scoped_and_preserves_earlier_batches():
    assert list(builder.VERSES) == EXPECTED
    assert list(curated.DATA) == EXPECTED
    builder.validate_data(REGISTRY)
    assert sum(batch["count"] for batch in DOSSIER["batches"]) == len(DOSSIER["verses"])
    assert all(f"7:{ayah}" in DOSSIER["verses"] for ayah in range(1, 101))
    assert all(f"6:{ayah}" in DOSSIER["verses"] for ayah in range(1, 166))
    batch_ids = [batch["id"] for batch in DOSSIER["batches"]]
    assert BATCH_ID in batch_ids and "dossier-62" in batch_ids
    assert batch_ids.index("dossier-62") + 1 == batch_ids.index(BATCH_ID)
    assert batch_ids == sorted(batch_ids, key=lambda value: int(value.split("-")[1]))

    batch = next(item for item in DOSSIER["batches"] if item["id"] == BATCH_ID)
    assert batch["range"] == "7:51–100" and batch["count"] == 50
    assert "شش فیلد" in batch["status"] and "پنج‌بندی" in batch["status"]
    assert "پنج شرحِ کهن و دو شرحِ معاصر" in batch["status"]
    assert "سه کاربستِ معنایی" in batch["status"]
    assert "قرطبی در ۷:۷۶" in batch["status"]
    assert "پیش‌نویس" in batch["status"] and "داوریِ تخصصی" in batch["status"]

    all_earlier_texts = {
        _normalized(item["text"])
        for key, entry in DOSSIER["verses"].items() if key not in EXPECTED
        for field in FIELDS for item in entry.get(field, []) if item.get("text", "").strip()
    }
    batch_texts: set[str] = set()
    for key in EXPECTED:
        entry = DOSSIER["verses"][key]
        assert entry["standard"] == 2
        assert "پیش‌نویس" in entry["status"] and "تخصصی" in entry["status"]
        verse_texts: list[str] = []
        for field in FIELDS:
            assert len(entry[field]) == 5, (key, field)
            for item in entry[field]:
                assert len(item["text"].split()) >= 14, (key, field, item["text"])
                assert item["cite"].strip() and item["evidence"].strip() and item["limit"].strip()
                verse_texts.append(_normalized(item["text"]))
        assert len(verse_texts) == len(set(verse_texts)), f"Repeated prose within {key}"
        for text in verse_texts:
            assert text not in batch_texts, f"Repeated prose across target verses: {key}: {text}"
            assert text not in all_earlier_texts, f"Repeated prose against earlier dossier: {key}: {text}"
            batch_texts.add(text)

        classical = _by_source(entry["classical"])
        assert set(classical) == CLASSICAL
        assert all(
            item["kind"] == "source-summary"
            for source_id, item in classical.items()
            if not (key == "7:76" and source_id == builder.QURTUBI)
        )
        modern_sources = {item.get("sourceId") for item in entry["modern"] if item.get("sourceId")}
        models = {item.get("model") for item in entry["modern"] if item.get("model")}
        assert modern_sources == {builder.QURANENC, builder.WASIT}
        assert models == MODELS
        assert len({item["text"] for item in entry["modern"] if item.get("model")}) == 3
        assert all("تحریریِ چارچوب" in item["limit"] for item in entry["modern"] if item.get("model"))
        assert all(not item.get("sourceId") for field in ("notes", "context", "critical", "research") for item in entry[field])
        assert all(item["kind"] == "editorial-critique" for item in entry["critical"])
        assert all(item["kind"] == "editorial-question" for item in entry["research"])


def test_qurtubi_7_76_is_a_scoped_coverage_note_not_a_tafsir_summary():
    key = "7:76"
    entry = DOSSIER["verses"][key]
    classical = _by_source(entry["classical"])
    gap = classical[builder.QURTUBI]
    assert gap["kind"] == "source-coverage-note"
    assert "لا يوجد تفسير لهذه الأية" in gap["text"]
    assert "خلأ" in gap["evidence"]
    assert "نه تفسیر" in gap["limit"] and "کلِ اثر" in gap["limit"]
    assert sum(item["kind"] == "source-summary" for item in entry["classical"]) == 4
    assert all(
        classical[source_id]["kind"] == "source-summary"
        for source_id in CLASSICAL - {builder.QURTUBI}
    )


def test_real_openiti_ranges_and_archive_scopes_are_not_expanded_into_page_claims():
    expected_tusi = {ayah: (ayah, ayah) for ayah in range(51, 101)}
    for start, end in ((78, 79), (83, 84), (97, 98)):
        for ayah in range(start, end + 1):
            expected_tusi[ayah] = (start, end)
    for ayah, span in expected_tusi.items():
        assert builder.TUSI_GROUPS[f"7:{ayah}"] == span
        item = _by_source(DOSSIER["verses"][f"7:{ayah}"]["classical"])[builder.TUSI]
        assert "OpenITI/0475AH" in item["cite"] and "metadata volume file" in item["cite"]
        assert "چاپ و صفحه احراز نشده" in item["cite"]
        assert item["sourceUrl"]
        assert ("شرحِ مستقیم" in item["cite"]) == (span[0] == span[1])
        if span[0] != span[1]:
            assert f"۷:{builder.fa_num(span[0])}–{builder.fa_num(span[1])}" in item["cite"]

    expected_fayd = (
        (50, 54), (55, 58), (59, 65), (66, 72), (73, 79),
        (80, 81), (82, 88), (89, 99), (100, 103),
    )
    for start, end in expected_fayd:
        for ayah in range(max(start, 51), min(end, 100) + 1):
            assert builder.FAYD_GROUPS[f"7:{ayah}"] == (start, end)
            item = _by_source(DOSSIER["verses"][f"7:{ayah}"]["classical"])[builder.FAYD]
            assert "OpenITI/1100AH" in item["cite"] and "metadata volume file" in item["cite"]
            assert "چاپ و صفحه احراز نشده" in item["cite"] and item["sourceUrl"]
            assert f"اعراف ۷:{builder.fa_num(start)}" in item["cite"]
            if start != end:
                assert f"–{builder.fa_num(end)}" in item["cite"]
            assert "وفات" not in item["cite"] and "وفات" not in item["text"]

    snapshots = DOSSIER["sourceSnapshots"]["araf_7_51_100"]
    assert snapshots["batchId"] == BATCH_ID and snapshots["range"] == "7:51–100"
    assert "7:78–79" in snapshots["scopeNotes"]["tusi"]
    assert "7:50–54" in snapshots["scopeNotes"]["fayd"]
    assert "cross this batch boundary" in snapshots["scopeNotes"]["fayd"]
    assert snapshots["rawWorkBench"]["path"] == "/tmp/araf/sources.json"
    assert snapshots["rawWorkBench"]["sha256"] == "d9e82786be7355349f1d02592e69748bf330f2fad2da0ba8dc28569e4ea3ad66"
    assert snapshots["quranEncSnapshot"]["sha256"] == "b056e4d67ac720235de019d7c4887acc1407e1deb935ec8830cf40e663a029ae"


def test_catalog_registry_and_rerun_of_batch_62_preserve_batch_63_metadata():
    collection = next(item for item in CATALOG["collections"] if item["id"] == builder.COLLECTION_ID)
    assert collection["comparativeCore"]["scope"].startswith("اعراف ۷:۵۱–۱۰۰")
    assert {item["id"] for item in collection["items"]} == set(builder.SOURCE_ORDER)
    assert "۷:۷۶" in collection["items"][2]["scope"]
    assert "فاقدِ تفسیر" in collection["items"][2]["basis"]
    assert "طوسی ۷:۷۸–۷۹" in collection["comparativeCore"]["note"]
    assert "فیض ۷:۵۰–۵۴" in collection["comparativeCore"]["note"]
    assert "پیش‌نویسِ نیازمندِ داوریِ تخصصی" in collection["notice"]

    assert REGISTRY["version"] >= 12
    registry = {item["id"]: item for item in REGISTRY["sources"]}
    for source_id in (builder.TUSI, builder.FAYD):
        source = registry[source_id]
        assert BATCH_ID in source["researchSnapshot"]["coveredBatches"]
        assert source["researchSnapshot"]["edition"] == "not identified"
        assert source["researchSnapshot"]["pagination"] == "not specified"
    assert "۷:۱–۱۰۰" in registry[builder.TABARI]["availabilityNote"]

    # Batch 62 is deliberately rerunnable after this batch: its updater must
    # keep the later coverage note, method section, registry coverage, and catalog.
    assert "اعراف بازهٔ ۷:۱–۱۰۰ را پوشش می‌دهد؛ ادامهٔ ترتیبیِ همین سوره از ۷:۱۰۱ است." in DOSSIER["notice"]
    assert "در بستهٔ اعراف ۷:۵۱–۱۰۰" in DOSSIER["editorialMethod"]
    assert "7:50–54" in DOSSIER["sourceSnapshots"]["araf_7_51_100"]["scopeNotes"]["fayd"]
    updated_registry = earlier_araf_builder.update_registry(json.loads(json.dumps(REGISTRY)))
    updated_sources = {item["id"]: item for item in updated_registry["sources"]}
    assert BATCH_ID in updated_sources[builder.TUSI]["researchSnapshot"]["coveredBatches"]
    assert any(item["id"] == builder.COLLECTION_ID for item in CATALOG["collections"])
    assert "## ۱۰. منابعِ بررسی‌شده برایِ بستهٔ اعراف ۷:۵۱–۱۰۰" in ATTRIBUTION
    assert "۷:۷۶" in ATTRIBUTION
