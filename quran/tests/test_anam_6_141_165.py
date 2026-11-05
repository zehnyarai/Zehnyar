"""Coverage, source-marker, attribution, and rerun-safety checks for al-An'am 6:141–165."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import build_anam_6_91_140 as previous_builder
import build_anam_6_141_165 as builder
import build_araf_7_1_50 as latest_builder
import anam_6_141_165_data as curated

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


def _by_source(items: list[dict]) -> dict[str, dict]:
    return {item["sourceId"]: item for item in items if item.get("sourceId")}


def test_batch_has_twenty_five_complete_distinct_dossiers_and_preserves_prior_ranges():
    expected = [f"6:{ayah}" for ayah in range(141, 166)]
    assert list(builder.VERSES) == expected
    assert list(curated.DATA) == expected
    builder.validate_data(REGISTRY)
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    assert len(DOSSIER["batches"]) >= 62
    assert all(f"6:{ayah}" in DOSSIER["verses"] for ayah in range(1, 166))
    batch_ids = [item["id"] for item in DOSSIER["batches"]]
    batch_index = batch_ids.index(BATCH_ID)
    assert batch_ids[batch_index - 1:batch_index + 2] == ["dossier-60", BATCH_ID, "dossier-62"]
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])

    batch = next(item for item in DOSSIER["batches"] if item["id"] == BATCH_ID)
    assert batch["range"] == "6:141–165" and batch["count"] == 25
    assert "شش فیلد پنج‌بندی" in batch["status"]
    assert "پنج شرحِ کهن و دو شرحِ معاصر" in batch["status"]
    assert "سه کاربستِ معنایی جداست" in batch["status"]
    assert "پیش‌نویس" in batch["status"] and "داوریِ تخصصی" in batch["status"]

    batch_texts: set[str] = set()
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
                texts.append(" ".join(item["text"].split()))
        assert len(texts) == len(set(texts)), f"Repeated prose within {key}"
        for text in texts:
            assert text not in batch_texts, f"Repeated prose across verses: {key}: {text}"
            batch_texts.add(text)

        classical = _by_source(entry["classical"])
        assert set(classical) == CLASSICAL
        assert all(item["kind"] == "source-summary" for item in classical.values())
        modern_sources = {item.get("sourceId") for item in entry["modern"] if item.get("sourceId")}
        models = {item.get("model") for item in entry["modern"] if item.get("model")}
        assert modern_sources == {QURANENC, WASIT}
        assert models == MODELS
        assert len({item["text"] for item in entry["modern"] if item.get("model")}) == 3
        assert all("تحریریِ چارچوب" in item["limit"] for item in entry["modern"] if item.get("model"))
        assert all(not item.get("sourceId") for field in ("notes", "context", "critical", "research") for item in entry[field])
        assert all(item["kind"] == "editorial-critique" for item in entry["critical"])
        assert all(item["kind"] == "editorial-question" for item in entry["research"])

    cumulative_texts = [
        " ".join(item["text"].split())
        for entry in DOSSIER["verses"].values()
        for field in FIELDS
        for item in entry[field]
    ]
    assert len(cumulative_texts) == len(set(cumulative_texts)), "Repeated prose exists across the cumulative dossier"


def test_openiti_marker_ranges_and_duplicate_fayd_marker_are_mapped_by_verse_text():
    expected_fayd = (
        (136, 141), (142, 145), (146, 146), (147, 151), (152, 155),
        (156, 158), (159, 160), (161, 164), (165, 165),
    )
    for start, end in expected_fayd:
        for ayah in range(max(start, 141), min(end, 165) + 1):
            assert builder.FAYD_GROUPS[f"6:{ayah}"] == (start, end)
    assert builder.TUSI_GROUPS["6:162"] == builder.TUSI_GROUPS["6:163"] == (162, 163)
    assert all(
        builder.TUSI_GROUPS[f"6:{ayah}"] == (ayah, ayah)
        for ayah in range(141, 166)
        if ayah not in (162, 163)
    )

    for ayah in range(141, 166):
        key = f"6:{ayah}"
        classical = _by_source(DOSSIER["verses"][key]["classical"])
        tusi, fayd = classical[TUSI], classical[FAYD]
        assert "OpenITI/0475AH" in tusi["cite"] and "metadata volume file" in tusi["cite"]
        assert "OpenITI/1100AH" in fayd["cite"] and "metadata volume file" in fayd["cite"]
        assert "چاپ و صفحه احراز نشده" in tusi["cite"]
        assert "چاپ و صفحه احراز نشده" in fayd["cite"]
        assert "وفات" not in fayd["cite"] and "وفات" not in fayd["text"]
        assert tusi["sourceUrl"] and fayd["sourceUrl"]
        if ayah in (162, 163):
            assert "شرحِ گروهی" in tusi["cite"]
            assert "۶:۱۶۲–۱۶۳" in tusi["cite"] and "۶:۱۶۲–۱۶۳" in tusi["evidence"]
        else:
            assert "شرحِ مستقیم" in tusi["cite"]
        if ayah in (146, 165):
            assert "شرحِ مستقیم" in fayd["cite"]
        else:
            assert "شرحِ گروهی" in fayd["cite"]

    fayd150 = _by_source(DOSSIER["verses"]["6:150"]["classical"])[FAYD]
    fayd151 = _by_source(DOSSIER["verses"]["6:151"]["classical"])[FAYD]
    assert "نشانِ درونیِ (۱۵۱)" in fayd150["evidence"] and "قل هلم شهداءكم" in fayd150["evidence"]
    assert "نشانِ درونیِ (۱۵۱)" in fayd151["evidence"] and "قل تعالوا أتل" in fayd151["evidence"]
    assert "با مقابلهٔ عبارت تعیین شد، نه با شمارهٔ تکراری" in fayd150["cite"]
    assert "با مقابلهٔ عبارت تعیین شد، نه با شمارهٔ تکراری" in fayd151["cite"]
    assert "۶:۱۴۷–۱۵۱" in fayd150["cite"] and "۶:۱۴۷–۱۵۱" in fayd151["cite"]

    snapshots = DOSSIER["sourceSnapshots"]["anam_6_141_165"]
    assert snapshots["batchId"] == BATCH_ID and snapshots["range"] == "6:141–165"
    assert snapshots["scopeNotes"]["tusi"].startswith("OpenITI markers: direct 6:141–161")
    assert "6:147–151" in snapshots["scopeNotes"]["fayd"]
    assert "duplicated" in snapshots["scopeNotes"]["fayd"]
    assert snapshots["rawWorkBench"]["path"] == "/tmp/anam_6_141_165_sources.json"
    assert snapshots["rawWorkBench"]["sha256"] == "8e758f9be83424c2a66110d26a8a0d383aba13547b236aea718fd1e5503919c4"
    assert snapshots["quranEncSnapshot"] == {
        "sourceId": QURANENC,
        "file": "static/tafsir/arabic-moyassar-quranenc-1.0.0.json",
        "version": "1.0.0",
        "sha256": "b056e4d67ac720235de019d7c4887acc1407e1deb935ec8830cf40e663a029ae",
    }
    for source_id in (TUSI, FAYD):
        openiti_snapshot = snapshots["openIti"][source_id]
        assert openiti_snapshot.get("deathDate") is None
        assert openiti_snapshot["edition"] == "not identified"
        assert openiti_snapshot["pagination"] == "not specified"

    registry = {item["id"]: item for item in REGISTRY["sources"]}
    assert REGISTRY["version"] >= 11
    for source_id in (TUSI, FAYD):
        record = registry[source_id]
        assert {"dossier-58", "dossier-59", "dossier-60", BATCH_ID} <= set(
            record["researchSnapshot"]["coveredBatches"]
        )
        assert record["researchSnapshot"]["edition"] == "not identified"
        assert record["researchSnapshot"]["pagination"] == "not specified"
        assert record["licenseStatus"] == "unresolved"
        assert record["researchSnapshot"].get("deathDate") is None


def test_verse_specific_disagreements_critical_cautions_and_context_are_visible():
    verses = DOSSIER["verses"]

    v141 = verses["6:141"]
    assert "هم زکاتِ مقرر و هم بخشش" in " ".join(item["text"] for item in v141["notes"])
    assert "هم قولِ زکات" in _by_source(v141["classical"])[FAYD]["text"]
    assert "صدقهٔ همان روز" in _by_source(v141["classical"])[FAYD]["text"]
    assert "زکاتِ مقرر" in " ".join(item["text"] for item in v141["critical"])

    v145 = verses["6:145"]
    assert "نسخ" in " ".join(item["text"] for item in v145["critical"])
    assert "نسخ" in _by_source(v145["classical"])[IBN]["text"]
    assert "دمًا مسفوحًا" in _by_source(v145["classical"])[TABARI]["text"]

    v146 = verses["6:146"]
    assert "ذي ظفر" in _by_source(v146["classical"])[TABARI]["text"]
    assert "چنگال" in _by_source(v146["classical"])[TUSI]["text"]
    assert "قانونِ غذاییِ همگانی" in " ".join(item["text"] for item in v146["notes"])

    v151_critical = " ".join(item["text"] for item in verses["6:151"]["critical"])
    assert "صحیفهٔ خاتم‌دار" in v151_critical and "وصایایِ ده‌گانه" in v151_critical
    v152 = _by_source(verses["6:152"]["classical"])
    assert "مال" in v152[TABARI]["text"] and "یتیم" in v152[IBN]["text"]
    assert "تذكرون" in v152[TUSI]["text"]
    assert "انصافِ سنجش" in v152[FAYD]["text"]

    v158 = _by_source(verses["6:158"]["classical"])
    assert "طلوعِ خورشید" in v158[TABARI]["text"]
    assert "امرِ خدا" in v158[FAYD]["text"] and "عذاب" in v158[FAYD]["text"]
    assert "حرکتِ جسمانی" in v158[QURTUBI]["text"] or "کیفیتِ جسمانی" in v158[QURTUBI]["text"]
    v158_critical = " ".join(item["text"] for item in verses["6:158"]["critical"])
    assert "ترتیبِ نشانه‌هایِ قیامت" in v158_critical

    v159 = _by_source(verses["6:159"]["classical"])
    assert "فرقوا/فارقوا" in v159[QURTUBI]["text"] or "فارقوا" in v159[QURTUBI]["text"]
    assert "چهار قول" in v159[TUSI]["text"]
    assert "قرائتِ «فارقوا»" in v159[FAYD]["text"]
    v159_critical = " ".join(item["text"] for item in verses["6:159"]["critical"])
    assert "تکفیر" in v159_critical and "گروه‌هایِ امروز" in v159_critical

    v164 = _by_source(verses["6:164"]["classical"])
    assert "جبر" in v164[TUSI]["text"]
    assert "گناهِ موروثی" in " ".join(item["text"] for item in verses["6:164"]["critical"])
    v165_critical = " ".join(item["text"] for item in verses["6:165"]["critical"])
    assert "برتریِ ذاتی" in v165_critical and "پاسداری از زمین" in v165_critical

    assert "پس ازِ انعام ۶:۱۴۱، انعام ۶:۱۴۲" in verses["6:141"]["context"][2]["text"]
    assert "پس ازِ انعام ۶:۱۶۴، انعام ۶:۱۶۵" in verses["6:164"]["context"][2]["text"]
    assert "اعراف ۷:۱" in verses["6:165"]["context"][2]["text"]


def test_catalog_registry_notice_method_and_attribution_are_current_and_caveated():
    assert CATALOG["version"] >= 40
    assert len(CATALOG["collections"]) >= 37
    collection = next(item for item in CATALOG["collections"] if item["id"] == COLLECTION_ID)
    assert {item["id"] for item in collection["items"]} == set(builder.SOURCE_ORDER)
    assert collection["comparativeCore"]["scope"].startswith("انعام ۶:۱۴۱–۱۶۵")
    assert "۶:۱۶۲–۱۶۳" in collection["comparativeCore"]["note"]
    assert "۶:۱۴۷–۱۵۱" in collection["comparativeCore"]["note"]
    assert "خلاصه‌ها بازنویسی‌اند، نه نقلِ لفظی" in collection["comparativeCore"]["note"]
    assert "مجوز" in collection["notice"] and "پیش‌نویس" in collection["notice"]
    catalog_by_id = {item["id"]: item for item in collection["items"]}
    assert "مواضعِ نشان‌دار" in catalog_by_id[FAYD]["scope"]
    assert "Direct" in catalog_by_id[TUSI]["basis"] or "گروهی" in catalog_by_id[TUSI]["basis"]

    notice = DOSSIER["notice"]
    assert "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است" in notice
    assert "ادامهٔ ترتیبیِ همین سوره از ۷:۱۰۱ است" in notice
    assert "مجوزِ متنِ تفسیریِ آرشیوهایِ Quran.com" in notice
    assert "پیش‌نویس" in notice and "بازبینیِ تخصصی انجام نشده" in notice
    assert "هیچ بندی بازبینیِ تخصصی‌شده معرفی نمی‌شود" in notice

    method = DOSSIER["editorialMethod"]
    assert method.count("در بستهٔ انعام ۶:۴۱–۹۰") == 1
    assert method.count("در بستهٔ انعام ۶:۹۱–۱۴۰") == 1
    assert method.count("در بستهٔ انعام ۶:۱۴۱–۱۶۵") == 1
    assert "گروهی" in method and "فیلمور و معناشناسیِ شناختی" in method
    assert "انعام ۶:۱–۱۶۵ اکنون پوشش دارد" in method
    assert latest_builder.update_method(method) == method

    attribution = ATTRIBUTION_PATH.read_text(encoding="utf-8")
    marker = "## ۸. منابعِ بررسی‌شده برایِ بستهٔ انعام ۶:۱۴۱–۱۶۵"
    assert attribution.count(marker) == 1
    assert "OpenITI/0475AH" in attribution and "OpenITI/1100AH" in attribution
    assert "قل هلم شهداءكم" in attribution and "قل تعالوا أتل" in attribution
    assert "b056e4d67ac720235de019d7c4887acc1407e1deb935ec8830cf40e663a029ae" in attribution
    assert "/tmp/anam_6_141_165_sources.json" in attribution
    batch_section = attribution.split(marker, 1)[1].split("\n## ۹.", 1)[0]
    assert "وفات" not in batch_section
    assert "صفحه ادعا نشده" in attribution
    assert "پیش‌نویس و نیازمندِ داوریِ تخصصی" in attribution


def _copy_outputs(tmp_path, monkeypatch, target_builder):
    paths = {
        "DOSSIER_PATH": tmp_path / "verse-dossiers.json",
        "CATALOG_PATH": tmp_path / "tafsir-catalog.json",
        "REGISTRY_PATH": tmp_path / "tafsir-sources.json",
        "ATTRIBUTION_PATH": tmp_path / "TAFSIR_ATTRIBUTION.md",
    }
    sources = {
        "DOSSIER_PATH": DOSSIER_PATH,
        "CATALOG_PATH": CATALOG_PATH,
        "REGISTRY_PATH": REGISTRY_PATH,
        "ATTRIBUTION_PATH": ATTRIBUTION_PATH,
    }
    for name, destination in paths.items():
        destination.write_bytes(sources[name].read_bytes())
        monkeypatch.setattr(target_builder, name, destination)
    return paths


def test_batch_sixty_one_builder_is_idempotent_on_copied_outputs(tmp_path, monkeypatch):
    paths = _copy_outputs(tmp_path, monkeypatch, builder)
    monkeypatch.setattr(previous_builder, "ATTRIBUTION_PATH", paths["ATTRIBUTION_PATH"])
    monkeypatch.setattr(builder.renderer, "ATTRIBUTION_PATH", paths["ATTRIBUTION_PATH"])

    builder.main()
    first_run = {name: path.read_bytes() for name, path in paths.items()}
    builder.main()
    second_run = {name: path.read_bytes() for name, path in paths.items()}
    assert second_run == first_run


def test_rebuilding_batch_sixty_preserves_completed_batch_sixty_one(tmp_path, monkeypatch):
    paths = _copy_outputs(tmp_path, monkeypatch, previous_builder)
    monkeypatch.setattr(builder, "ATTRIBUTION_PATH", paths["ATTRIBUTION_PATH"])
    monkeypatch.setattr(builder.renderer, "ATTRIBUTION_PATH", paths["ATTRIBUTION_PATH"])
    before = json.loads(paths["DOSSIER_PATH"].read_text(encoding="utf-8"))
    before_entries = {f"6:{ayah}": before["verses"][f"6:{ayah}"] for ayah in range(141, 166)}
    before_notice = before["notice"]

    previous_builder.main()

    after = json.loads(paths["DOSSIER_PATH"].read_text(encoding="utf-8"))
    assert {key: after["verses"][key] for key in before_entries} == before_entries
    assert after["notice"] == before_notice
    assert any(item["id"] == BATCH_ID and item["range"] == "6:141–165" for item in after["batches"])
    assert after["editorialMethod"].count("در بستهٔ انعام ۶:۱۴۱–۱۶۵") == 1
    assert "anam_6_141_165" in after["sourceSnapshots"]

    after_catalog = json.loads(paths["CATALOG_PATH"].read_text(encoding="utf-8"))
    assert after_catalog["version"] >= 40
    assert any(item["id"] == COLLECTION_ID for item in after_catalog["collections"])

    registry = json.loads(paths["REGISTRY_PATH"].read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in registry["sources"]}
    for source_id in (TUSI, FAYD):
        assert BATCH_ID in by_id[source_id]["researchSnapshot"]["coveredBatches"]

    attribution = paths["ATTRIBUTION_PATH"].read_text(encoding="utf-8")
    assert attribution.count("## ۸. منابعِ بررسی‌شده برایِ بستهٔ انعام ۶:۱۴۱–۱۶۵") == 1
