"""Coverage, source-scope, attribution, and rerun-safety checks for al-An'am 6:91–140."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import build_anam_6_41_90 as previous_builder
import build_anam_6_91_140 as builder
import anam_6_91_140_data as curated

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


def test_batch_has_fifty_ordered_complete_dossiers_and_preserves_prior_batches():
    expected = [f"6:{ayah}" for ayah in range(91, 141)]
    assert list(builder.VERSES) == expected
    assert set(curated.DATA) == set(expected)
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    assert len(DOSSIER["batches"]) >= 62
    assert list(previous_builder.VERSES) == [f"6:{ayah}" for ayah in range(41, 91)]

    batch = next(item for item in DOSSIER["batches"] if item["id"] == BATCH_ID)
    assert batch["range"] == "6:91–140" and batch["count"] == 50
    assert "شش فیلدِ پنج‌بندی" in batch["status"]
    assert "سه کاربستِ جداگانهٔ ایزوتسو، فیلمور و معناشناسیِ شناختی" in batch["status"]
    assert "گروهیِ طوسی و فیض" in batch["status"]
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
        assert len(texts) == len(set(texts)), f"Repeated field text in {key}"
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


def test_tusi_and_fayd_grouped_scopes_match_the_pinned_text_markers():
    expected_fayd = (
        (91, 93), (94, 96), (97, 99), (100, 103), (104, 108), (109, 112),
        (113, 119), (120, 122), (123, 125), (126, 127), (128, 135), (136, 141),
    )
    for start, end in expected_fayd:
        for ayah in range(start, min(end, 140) + 1):
            assert builder.FAYD_GROUPS[f"6:{ayah}"] == (start, end)
    assert builder.TUSI_GROUPS["6:126"] == builder.TUSI_GROUPS["6:127"] == (126, 127)
    assert all(builder.TUSI_GROUPS[f"6:{ayah}"] == (ayah, ayah) for ayah in range(91, 141) if ayah not in (126, 127))

    for ayah in range(91, 141):
        key = f"6:{ayah}"
        classical = _by_source(DOSSIER["verses"][key]["classical"])
        tusi, fayd = classical[TUSI], classical[FAYD]
        assert "شرحِ مستقیم" in tusi["cite"] if ayah not in (126, 127) else "شرحِ گروهی" in tusi["cite"]
        assert "OpenITI/0475AH" in tusi["cite"] and "metadata volume file" in tusi["cite"]
        assert "چاپ و صفحه احراز نشده" in tusi["cite"]
        assert "شرحِ گروهی" in fayd["cite"] and "OpenITI/1100AH" in fayd["cite"]
        assert "metadata volume file" in fayd["cite"] and "چاپ و صفحه احراز نشده" in fayd["cite"]
        assert "وفات" not in fayd["cite"] and "وفات" not in fayd["text"]
        assert "صفحهٔ چاپی" not in fayd["cite"]
        assert tusi["sourceUrl"] and fayd["sourceUrl"]

    v126 = _by_source(DOSSIER["verses"]["6:126"]["classical"])
    assert "۶:۱۲۶–۱۲۷" in v126[TUSI]["cite"] and "۶:۱۲۶–۱۲۷" in v126[TUSI]["evidence"]
    assert "۶:۱۳۶–۱۴۱" in _by_source(DOSSIER["verses"]["6:140"]["classical"])[FAYD]["cite"]
    assert "۶:۹۱–۹۳" in _by_source(DOSSIER["verses"]["6:91"]["classical"])[FAYD]["cite"]

    snapshot = DOSSIER["sourceSnapshots"]["anam_6_91_140"]
    assert snapshot["batchId"] == BATCH_ID and snapshot["range"] == "6:91–140"
    assert "6:126–127" in snapshot["scopeNotes"]["tusi"]
    assert "136–141" in snapshot["scopeNotes"]["fayd"]
    assert snapshot["rawWorkBench"]["path"] == "/tmp/anam_6_91_140_sources.json"
    fayd_snapshot = snapshot["openIti"][FAYD]
    assert fayd_snapshot.get("deathDate") is None
    assert fayd_snapshot["pagination"] == "not specified"

    registry = {item["id"]: item for item in REGISTRY["sources"]}
    for source_id in (TUSI, FAYD):
        assert set(registry[source_id]["researchSnapshot"]["coveredBatches"]) >= {"dossier-58", "dossier-59", BATCH_ID}
        assert registry[source_id]["researchSnapshot"]["edition"] == "not identified"
        assert registry[source_id]["researchSnapshot"]["pagination"] == "not specified"
        assert registry[source_id]["licenseStatus"] == "unresolved"


def test_source_disagreements_and_editorial_cautions_are_visible():
    verses = DOSSIER["verses"]
    v103 = _by_source(verses["6:103"]["classical"])
    assert "إدراك" in v103[TUSI]["text"] or "ادراک" in v103[TUSI]["text"]
    assert "رؤیت" in v103[IBN]["text"] and "آخرت" in v103[IBN]["text"]
    assert "رؤیت" in v103[QURTUBI]["text"] and "احاطه" in v103[QURTUBI]["text"]
    assert "امامان" in v103[FAYD]["text"] and "چشمِ جسمانی" in v103[FAYD]["text"]
    v103_critical = " ".join(item["text"] for item in verses["6:103"]["critical"])
    assert "اختلافِ کلامی" in v103_critical and "فیض" in v103_critical

    v137 = _by_source(verses["6:137"]["classical"])
    assert "فقر یا ننگ" in v137[IBN]["text"]
    assert "قرائتِ ابن‌عامر" in v137[TUSI]["text"]
    assert "شیاطین" in v137[QURTUBI]["text"] and "متولیانِ بت" in v137[QURTUBI]["text"]
    assert "فقر" in v137[FAYD]["text"] and "نحر" in v137[FAYD]["text"]
    assert any("همگانیِ همهٔ عرب‌ها" in item["text"] for item in verses["6:137"]["critical"])

    v130 = _by_source(verses["6:130"]["classical"])
    assert "دو قول" in v130[TABARI]["text"] and "نذیرانِ جنی" in v130[TABARI]["text"]
    assert "جنیان را نذیر" in v130[IBN]["text"]
    assert "قولِ مجاهد را صحیح" in v130[QURTUBI]["text"]
    assert "اقوی می‌شمارد" in v130[TUSI]["text"]
    assert "یوسفِ پیامبر" in v130[FAYD]["text"] and "باقر" in v130[FAYD]["text"]
    v130_critical = " ".join(item["text"] for item in verses["6:130"]["critical"])
    assert "قولِ پیامبرانِ جن را اقوی می‌شمارد" in v130_critical

    v139 = _by_source(verses["6:139"]["classical"])
    assert "شیر" in v139[TABARI]["text"] and "جنین" in v139[TABARI]["text"]
    assert "شیر" in v139[QURTUBI]["text"] and "جنین" in v139[QURTUBI]["text"]
    assert "شیر، جنین یا هر دو" in v139[TUSI]["text"]
    assert "زنده" in v139[FAYD]["text"] and "مرده" in v139[FAYD]["text"]
    assert "اختصاصِ خوراک به مردان" in " ".join(item["text"] for item in verses["6:139"]["critical"])
    v140_critical = " ".join(item["text"] for item in verses["6:140"]["critical"])
    assert "منقولِ مفسران" in v140_critical and "قتلِ فرزند" in v140_critical


def test_cumulative_catalog_notice_method_and_attribution_are_current():
    assert CATALOG["version"] >= 40
    assert len(CATALOG["collections"]) >= 37
    collection = next(item for item in CATALOG["collections"] if item["id"] == COLLECTION_ID)
    assert {item["id"] for item in collection["items"]} == set(builder.SOURCE_ORDER)
    assert collection["comparativeCore"]["scope"].startswith("انعام ۶:۹۱–۱۴۰")
    assert "۶:۱۲۶–۱۲۷" in collection["comparativeCore"]["note"]
    assert "۶:۱۳۶–۱۴۱" in collection["comparativeCore"]["note"]
    assert "خلاصه‌ها نقلِ لفظی نیستند" in collection["comparativeCore"]["note"]
    assert "مجوز" in collection["notice"] and "پیش‌نویس" in collection["notice"]

    notice = DOSSIER["notice"]
    assert "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است" in notice
    assert "ادامهٔ ترتیبیِ همین سوره از ۷:۱۰۱ است" in notice
    assert "خلأِ بدنهٔ ابن‌کثیر در ۶:۵۶" in notice
    assert "مجوزِ متنِ تفسیریِ آرشیوهایِ Quran.com" in notice

    method = DOSSIER["editorialMethod"]
    assert method.count("در بستهٔ انعام ۶:۴۱–۹۰") == 1
    assert method.count("در بستهٔ انعام ۶:۹۱–۱۴۰") == 1
    assert "دامنهٔ طوسی برایِ ۶:۱۲۶–۱۲۷ گروهی" in method
    assert "فیلمور و معناشناسیِ شناختی" in method
    assert builder.update_method(method) == method

    attribution = ATTRIBUTION_PATH.read_text(encoding="utf-8")
    assert attribution.count("## ۶. منابعِ بررسی‌شده برایِ بستهٔ انعام ۶:۴۱–۹۰") == 1
    assert attribution.count("## ۷. منابعِ بررسی‌شده برایِ بستهٔ انعام ۶:۹۱–۱۴۰") == 1
    assert "۶:۱۳۶–۱۴۱" in attribution
    later_section = attribution.split("## ۷. منابعِ بررسی‌شده برایِ بستهٔ انعام ۶:۹۱–۱۴۰", 1)[1]
    later_section = later_section.split("## ۸. منابعِ بررسی‌شده برایِ بستهٔ انعام ۶:۱۴۱–۱۶۵", 1)[0]
    assert "وفات" not in later_section


def test_earlier_batch_builder_rerun_does_not_overwrite_batch_sixty(tmp_path, monkeypatch):
    # Exercise the real earlier builder on temporary copies to protect the committed output.
    dossier_path = tmp_path / "verse-dossiers.json"
    catalog_path = tmp_path / "tafsir-catalog.json"
    registry_path = tmp_path / "tafsir-sources.json"
    attribution_path = tmp_path / "TAFSIR_ATTRIBUTION.md"
    for source, destination in (
        (DOSSIER_PATH, dossier_path),
        (CATALOG_PATH, catalog_path),
        (REGISTRY_PATH, registry_path),
        (ATTRIBUTION_PATH, attribution_path),
    ):
        destination.write_bytes(source.read_bytes())

    before = json.loads(dossier_path.read_text(encoding="utf-8"))
    later_entries = {key: before["verses"][key] for key in (f"6:{ayah}" for ayah in range(91, 141))}
    monkeypatch.setattr(previous_builder, "DOSSIER_PATH", dossier_path)
    monkeypatch.setattr(previous_builder, "CATALOG_PATH", catalog_path)
    monkeypatch.setattr(previous_builder, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(previous_builder, "ATTRIBUTION_PATH", attribution_path)

    previous_builder.main()

    after = json.loads(dossier_path.read_text(encoding="utf-8"))
    assert {key: after["verses"][key] for key in later_entries} == later_entries
    assert any(item["id"] == "dossier-60" and item["range"] == "6:91–140" for item in after["batches"])
    assert after["notice"] == before["notice"]
    assert after["editorialMethod"].count("در بستهٔ انعام ۶:۹۱–۱۴۰") == 1
    assert "anam_6_91_140" in after["sourceSnapshots"]

    after_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert after_catalog["version"] >= 40
    assert any(item["id"] == COLLECTION_ID for item in after_catalog["collections"])
    assert any(item["id"] == "anam-6-41-90-cited" for item in after_catalog["collections"])

    after_registry = json.loads(registry_path.read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in after_registry["sources"]}
    for source_id in (TUSI, FAYD):
        assert BATCH_ID in by_id[source_id]["researchSnapshot"]["coveredBatches"]

    attribution = attribution_path.read_text(encoding="utf-8")
    assert attribution.count("## ۷. منابعِ بررسی‌شده برایِ بستهٔ انعام ۶:۹۱–۱۴۰") == 1


def test_batch_sixty_builder_is_idempotent_on_copied_outputs(tmp_path, monkeypatch):
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
        monkeypatch.setattr(builder, name, destination)
    monkeypatch.setattr(builder.renderer, "ATTRIBUTION_PATH", paths["ATTRIBUTION_PATH"])

    builder.main()
    first_run = {name: path.read_bytes() for name, path in paths.items()}
    builder.main()
    second_run = {name: path.read_bytes() for name, path in paths.items()}
    assert second_run == first_run
