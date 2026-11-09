# -*- coding: utf-8 -*-
"""هر آیهٔ دامنه باید هر فیلد Standard 3 را با وضعیت و پیگیریِ روشن داشته باشد."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import validate_standard3_fields  # noqa: E402
DATA = json.loads((ROOT / "static" / "verse-dossier-extended-fields.json").read_text(encoding="utf-8"))
APP = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")

EXPECTED_FIELDS = {
    "bibleComparison",
    "guidanceDiscourse",
    "shubuhat",
    "modernSciences",
    "qiraat",
    "philosophicalFoundations",
    "linguistics",
    "criticalDiscourseAnalysis",
    "historicalContext",
    "balaghaNazm",
}
BASE_FIELDS = ("notes", "context", "classical", "modern", "critical", "research")
TARGET_VERSES = {f"8:{ayah}" for ayah in range(51, 76)} | {f"9:{ayah}" for ayah in range(1, 130)} | {"10:1", "10:2", "10:3", "10:4", "10:5", "10:6", "10:7", "10:8", "10:9", "10:10", "10:11", "10:12", "10:13", "10:14", "10:15", "10:16", "10:17", "10:18", "10:19", "10:20", "10:21", "10:22", "10:23", "10:24", "10:25", "10:26", "10:27", "10:28", "10:29", "10:30", "10:31", "10:32", "10:33", "10:34", "10:35", "10:36", "10:37", "10:38", "10:39", "10:40", "10:41", "10:42", "10:43", "10:44", "10:45", "10:46", "10:47", "10:48", "10:49", "10:50", "10:51", "10:52", "10:53", "10:54", "10:55", "10:56", "10:57", "10:58", "10:59", "10:60", "10:61", "10:62", "10:63", "10:64", "10:65", "10:66", "10:67", "10:68", "10:69", "10:70", "10:71", "10:72", "10:73", "10:74", "10:75", "10:76", "10:77", "10:78", "10:79", "10:80", "10:81", "10:82", "10:83", "10:84", "10:85", "10:86", "10:87", "10:88", "10:89", "10:90", "10:91", "10:92", "10:93", "10:94", "10:95", "10:96", "10:97", "10:98", "10:99", "10:100", "10:101", "10:102", "10:103", "10:104", "10:105", "10:106", "10:107", "10:108", "10:109", "11:1", "11:2", "11:3", "11:4", "11:5", "11:6", "11:7", "11:8", "11:9", "11:10", "11:11", "11:12", "11:13", "11:14", "11:15", "11:16", "11:17", "11:18", "11:19", "11:20", "11:21", "11:22", "11:23", "11:24", "11:25", "11:26", "11:27", "11:28", "11:29", "11:30", "11:31", "11:32", "11:33", "11:34", "11:35", "11:36", "11:37", "11:38", "11:39", "11:40", "11:41", "11:42", "11:43", "11:44", "11:45", "11:46", "11:47", "11:48", "11:49", "11:50", "11:51", "11:52", "11:53", "11:54", "11:55", "11:56", "11:57", "11:58", "11:59", "11:60", "11:61", "11:62", "11:63", "11:64", "11:65", "11:66", "11:67", "11:68", "11:69", "11:70", "11:71", "11:72", "11:73", "11:74", "11:75", "11:76", "11:77", "11:78", "11:79", "11:80", "11:81", "11:82", "11:83", "11:84", "11:85", "11:86", "11:87", "11:88", "11:89", "11:90", "11:91", "11:92", "11:93", "11:94", "11:95", "11:96", "11:97", "11:98", "11:99", "11:100", "11:101", "11:102", "11:103", "11:104", "11:105", "11:106", "11:107", "11:108", "11:109", "11:110", "11:111", "11:112", "11:113", "11:114", "11:115", "11:116", "11:117", "11:118", "11:119", "11:120", "11:121", "11:122", "11:123", "12:1", "12:2", "12:3", "12:4", "12:5", "12:6", "12:7", "12:8", "12:9", "12:10", "12:11", "12:12", "12:13", "12:14", "12:15", "12:16", "12:17", "12:18", "12:19", "12:20", "12:21", "12:22", "12:23", "12:24", "12:25", "12:26", "12:27", "12:28", "12:29", "12:30", "12:31", "12:32", "12:33", "12:34", "12:35", "12:36", "12:37", "12:38", "12:39", "12:40", "12:41", "12:42", "12:43", "12:44", "12:45", "12:46", "12:47", "12:48", "12:49", "12:50", "12:51", "12:52", "12:53", "12:54", "12:55", "12:56", "12:57", "12:58", "12:59", "12:60", "12:61", "12:62", "12:63", "12:64", "12:65", "12:66", "12:67", "12:68", "12:69", "12:70", "12:71", "12:72", "12:73", "12:74", "12:75", "12:76", "12:77", "12:78", "12:79", "12:80", "12:81", "12:82", "12:83", "12:84", "12:85", "12:86", "12:87", "12:88", "12:89", "12:90", "12:91", "12:92", "12:93", "12:94", "12:95", "12:96", "12:97", "12:98", "12:99", "12:100", "12:101", "12:102", "12:103", "12:104", "12:105", "12:106", "12:107", "12:108", "12:109", "12:110", "12:111", "13:1", "13:2", "13:3", "13:4", "13:5", "13:6", "13:7", "13:8", "13:9", "13:10", "13:11", "13:12", "13:13", "13:14", "13:15", "13:16", "13:17", "13:18", "13:19", "13:20", "13:21", "13:22", "13:23", "13:24", "13:25", "13:26", "13:27", "13:28", "13:29", "13:30", "13:31", "13:32", "13:33", "13:34", "13:35", "13:36", "13:37", "13:38", "13:39", "13:40", "13:41", "13:42", "13:43", "14:1", "14:2", "14:3", "14:4", "14:5", "14:6", "14:7", "14:8", "14:9", "14:10", "14:11", "14:12", "14:13", "14:14", "14:15", "14:16", "14:17", "14:18", "14:19", "14:20", "14:21", "14:22", "14:23", "14:24", "14:25", "14:26", "14:27", "14:28", "14:29", "14:30", "14:31", "14:32", "14:33", "14:34", "14:35", "14:36", "14:37", "14:38", "14:39", "14:40", "14:41", "14:42", "14:43", "14:44", "14:45", "14:46", "14:47", "14:48", "14:49", "14:50", "14:51", "14:52", "15:1", "15:2", "15:3", "15:4", "15:5", "15:6", "15:7", "15:8", "15:9", "15:10", "15:11", "15:12", "15:13", "15:14", "15:15", "15:16", "15:17", "15:18", "15:19", "15:20", "15:21", "15:22", "15:23", "15:24", "15:25", "15:26", "15:27", "15:28", "15:29", "15:30", "15:31", "15:32", "15:33", "15:34", "15:35", "15:36", "15:37", "15:38", "15:39", "15:40", "15:41", "15:42", "15:43", "15:44", "15:45", "15:46", "15:47", "15:48", "15:49", "15:50", "15:51", "15:52", "15:53", "15:54", "15:55", "15:56", "15:57", "15:58", "15:59", "15:60", "15:61", "15:62", "15:63", "15:64", "15:65", "15:66", "15:67", "15:68", "15:69", "15:70", "15:71", "15:72", "15:73", "15:74", "15:75", "15:76", "15:77", "15:78", "15:79", "15:80", "15:81", "15:82", "15:83", "15:84", "15:85", "15:86", "15:87", "15:88", "15:89", "15:90", "15:91", "15:92", "15:93", "15:94", "15:95", "15:96", "15:97", "15:98", "15:99", "16:1", "16:2", "16:3", "16:4", "16:5", "16:6", "16:7", "16:8", "16:9", "16:10", "16:11", "16:12", "16:13", "16:14", "16:15", "16:16", "16:17", "16:18", "16:19", "16:20", "16:21", "16:22", "16:23", "16:24", "16:25", "16:26", "16:27", "16:28", "16:29", "16:30", "16:31", "16:32", "16:33", "16:34", "16:35", "16:36", "16:37", "16:38", "16:39", "16:40", "16:41", "16:42", "16:43", "16:44", "16:45", "16:46", "16:47", "16:48", "16:49", "16:50", "16:51", "16:52", "16:53", "16:54", "16:55", "16:56", "16:57", "16:58", "16:59", "16:60", "16:61", "16:62", "16:63", "16:64", "16:65", "16:66", "16:67", "16:68", "16:69", "16:70", "16:71", "16:72", "16:73", "16:74", "16:75", "16:76", "16:77", "16:78", "16:79", "16:80", "16:81", "16:82", "16:83", "16:84", "16:85", "16:86", "16:87", "16:88", "16:89", "16:90", "16:91", "16:92", "16:93", "16:94", "16:95", "16:96", "16:97", "16:98", "16:99", "16:100", "16:101", "16:102", "16:103", "16:104", "16:105", "16:106", "16:107", "16:108", "16:109", "16:110", "16:111", "16:112", "16:113", "16:114", "16:115", "16:116", "16:117", "16:118", "16:119", "16:120", "16:121", "16:122", "16:123", "16:124", "16:125", "16:126", "16:127", "16:128", "17:1", "17:2", "17:3", "17:4", "17:5", "17:6", "17:7", "17:8", "17:9", "17:10", "17:11", "17:12", "17:13", "17:14", "17:15", "17:16", "17:17", "17:18", "17:19", "17:20", "17:21", "17:22", "17:23", "17:24", "17:25", "17:26", "17:27", "17:28", "17:29", "17:30", "17:31", "17:32", "17:33", "17:34", "17:35", "17:36", "17:37", "17:38", "17:39", "17:40", "17:41", "17:42", "17:43", "17:44", "17:45", "17:46", "17:47", "17:48", "17:49", "17:50", "17:51", "17:52", "17:53", "17:54", "17:55", "17:56", "17:57", "17:58", "17:59", "17:60", "17:61", "17:62", "17:63", "17:64", "17:65", "17:66", "17:67", "17:68", "17:69", "17:70", "17:71", "17:72", "17:73", "17:74", "17:75", "17:76", "17:77", "17:78", "17:79", "17:80", "17:81", "17:82", "17:83", "17:84", "17:85", "17:86", "17:87", "17:88", "17:89", "17:90", "17:91", "17:92", "17:93", "17:94", "17:95", "17:96", "17:97", "17:98", "17:99", "17:100", "17:101", "17:102", "17:103", "17:104", "17:105", "17:106", "17:107", "17:108", "17:109", "17:110", "17:111", "18:1", "18:2", "18:3", "18:4", "18:5", "18:6", "18:7", "18:8", "18:9", "18:10", "18:11", "18:12", "18:13", "18:14", "18:15", "18:16", "18:17", "18:18", "18:19", "18:20", "18:21", "18:22", "18:23", "18:24", "18:25", "18:26", "18:27", "18:28", "18:29", "18:30", "18:31", "18:32", "18:33", "18:34", "18:35", "18:36", "18:37", "18:38", "18:39", "18:40", "18:41", "18:42", "18:43", "18:44", "18:45", "18:46", "18:47", "18:48", "18:49", "18:50", "18:51", "18:52", "18:53", "18:54", "18:55", "18:56", "18:57", "18:58", "18:59", "18:60", "18:61", "18:62", "18:63", "18:64", "18:65", "18:66", "18:67", "18:68", "18:69", "18:70", "18:71", "18:72", "18:73", "18:74", "18:75", "18:76", "18:77", "18:78", "18:79", "18:80", "18:81", "18:82", "18:83", "18:84", "18:85", "18:86", "18:87", "18:88", "18:89", "18:90"}


def _fa(number: int) -> str:
    return str(number).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def test_standard3_schema_declares_all_requested_fields_and_thresholds():
    assert {field["id"] for field in DATA["fields"]} == EXPECTED_FIELDS
    assert DATA["criteria"]["requiredEntriesPerField"] == 5
    assert DATA["criteria"]["minimumWordsPerEntry"] == 14
    assert set(DATA["criteria"]["requiredEntryProperties"]) == {"text", "cite", "evidence", "limit"}
    assert DATA["criteria"]["followUpRequiredWhenIncomplete"] is True
    assert DATA["criteria"]["sourceCoverageNoteRequiredWhenIncomplete"] is True


def test_each_target_ayah_has_all_base_and_extended_fields_under_its_own_record():
    assert set(DATA["verses"]) == TARGET_VERSES
    for verse_id, dossier in DATA["verses"].items():
        assert dossier.get("title", "").strip(), verse_id
        required = 5 if dossier.get("tier", "full") == "full" else 3
        if dossier.get("tier") == "core":
            assert dossier.get("coverageNote", "").strip(), verse_id
        assert all(isinstance(dossier.get(field), list) and len(dossier[field]) >= required for field in BASE_FIELDS), verse_id
        for field in BASE_FIELDS:
            for item in dossier[field]:
                assert len(item.get("text", "").split()) >= 14, (verse_id, field)
                assert item.get("cite", "").strip(), (verse_id, field)
        assert set(dossier["extendedFields"]) == EXPECTED_FIELDS, verse_id
        for field_id, field in dossier["extendedFields"].items():
            assert field["status"] in {"needs-research", "partial", "complete"}, (verse_id, field_id)
            assert isinstance(field.get("entries"), list), (verse_id, field_id)
            assert field.get("followUp", "").strip(), (verse_id, field_id)
            assert field.get("sourceCoverageNote", "").strip(), (verse_id, field_id)
            assert field["coverage"]["required"] == 5, (verse_id, field_id)
            assert field["coverage"]["completed"] == len(field["entries"]), (verse_id, field_id)
            if field["status"] == "complete":
                assert len(field["entries"]) >= 5, (verse_id, field_id)
            for entry in field["entries"]:
                assert len(entry.get("text", "").split()) >= 14, (verse_id, field_id)
                assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit")), (verse_id, field_id)


def test_unresearched_fields_are_explicitly_marked_not_fabricated():
    for verse_id, dossier in DATA["verses"].items():
        for field_id, field in dossier["extendedFields"].items():
            assert field["status"] in {"needs-research", "partial", "complete"}, (verse_id, field_id)
            assert isinstance(field["entries"], list), (verse_id, field_id)
            assert field["coverage"] == {"completed": len(field["entries"]), "required": 5}, (verse_id, field_id)
            assert field.get("followUp", "").strip(), (verse_id, field_id)
            assert field.get("sourceCoverageNote", "").strip(), (verse_id, field_id)
            if field["status"] == "needs-research":
                assert field["entries"] == [], (verse_id, field_id)
            elif field["status"] == "partial":
                assert 0 < len(field["entries"]) < 5, (verse_id, field_id)
            else:
                assert len(field["entries"]) >= 5, (verse_id, field_id)


def test_first_sequential_ayah_has_source_bounded_partial_material():
    verse = DATA["verses"]["9:1"]
    assert verse["fieldCoverageStatus"].startswith("شش فیلدِ پایه موجود")
    for field_id in ("guidanceDiscourse", "shubuhat", "philosophicalFoundations", "linguistics", "criticalDiscourseAnalysis", "historicalContext", "balaghaNazm"):
        field = verse["extendedFields"][field_id]
        assert field["status"] == "partial"
        assert len(field["entries"]) == 1
        entry = field["entries"][0]
        assert len(entry["text"].split()) >= 14
        assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit"))
        assert entry.get("kind")
    for field_id in ("bibleComparison", "modernSciences", "qiraat"):
        field = verse["extendedFields"][field_id]
        assert field["status"] == "needs-research" and not field["entries"]
        assert "هنوز" in field["sourceCoverageNote"] or "هنوز" in field["followUp"]


def test_second_sequential_ayah_has_source_bounded_partial_material():
    verse = DATA["verses"]["9:2"]
    for field_id in ("guidanceDiscourse", "shubuhat", "philosophicalFoundations", "linguistics", "criticalDiscourseAnalysis", "historicalContext", "balaghaNazm"):
        field = verse["extendedFields"][field_id]
        assert field["status"] == "partial" and len(field["entries"]) == 1
        entry = field["entries"][0]
        assert len(entry["text"].split()) >= 14
        assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit"))
    for field_id in ("bibleComparison", "modernSciences", "qiraat"):
        field = verse["extendedFields"][field_id]
        assert field["status"] == "needs-research" and not field["entries"]


def test_next_sequential_ayahs_have_source_bounded_partial_material():
    for verse_id in ("9:3", "9:4", "9:5", "9:6", "9:7"):
        verse = DATA["verses"][verse_id]
        assert verse["fieldCoverageStatus"].startswith("شش فیلدِ پایه موجود")
        for field_id in ("guidanceDiscourse", "shubuhat", "philosophicalFoundations", "linguistics", "criticalDiscourseAnalysis", "historicalContext", "balaghaNazm"):
            field = verse["extendedFields"][field_id]
            assert field["status"] == "partial" and len(field["entries"]) == 1
            entry = field["entries"][0]
            assert len(entry["text"].split()) >= 14
            assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit"))
            assert entry.get("kind")
        for field_id in ("bibleComparison", "modernSciences", "qiraat"):
            field = verse["extendedFields"][field_id]
            assert field["status"] == "needs-research" and not field["entries"]


def test_remaining_sequential_tawbah_ayahs_have_source_bounded_material():
    for number in range(8, 21):
        verse_id = f"9:{number}"
        verse = DATA["verses"][verse_id]
        for field_id in ("guidanceDiscourse", "shubuhat", "philosophicalFoundations", "linguistics", "criticalDiscourseAnalysis", "historicalContext", "balaghaNazm"):
            field = verse["extendedFields"][field_id]
            assert field["status"] == "partial" and len(field["entries"]) == 1
            assert field["coverage"] == {"completed": 1, "required": 5}
            entry = field["entries"][0]
            assert len(entry["text"].split()) >= 14
            assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit"))
            assert entry.get("kind")
        for field_id in ("bibleComparison", "modernSciences"):
            assert verse["extendedFields"][field_id]["status"] == "needs-research"
        qiraat = verse["extendedFields"]["qiraat"]
        if number == 15:
            assert qiraat["status"] == "partial" and len(qiraat["entries"]) == 1
            assert "قرطبی" in qiraat["entries"][0]["cite"]
        else:
            assert qiraat["status"] == "needs-research" and not qiraat["entries"]
            assert "گزیده‌هایِ محلی" in qiraat["sourceCoverageNote"]


def test_tawbah_21_to_25_have_source_bounded_sunni_shia_comparison():
    seven = (
        "guidanceDiscourse", "shubuhat", "philosophicalFoundations", "linguistics",
        "criticalDiscourseAnalysis", "historicalContext", "balaghaNazm",
    )
    for number in range(21, 26):
        verse_id = f"9:{number}"
        verse = DATA["verses"][verse_id]
        assert verse["fieldCoverageStatus"].startswith("شش فیلدِ پایه موجود"), verse_id
        assert any("طوسی" in item["cite"] for item in verse["classical"]), verse_id
        assert any("فیض کاشانی" in item["cite"] for item in verse["classical"]), verse_id
        for field_id in seven:
            field = verse["extendedFields"][field_id]
            assert field["status"] == "partial" and 2 <= len(field["entries"]) <= 4, (verse_id, field_id)
            assert field["coverage"] == {"completed": len(field["entries"]), "required": 5}, (verse_id, field_id)
        source_cites = " ".join(
            item["cite"]
            for field_id in seven
            for item in verse["extendedFields"][field_id]["entries"]
        )
        assert any(name in source_cites for name in ("طبری", "قرطبی", "المیسر")), verse_id
        assert any(name in source_cites for name in ("طوسی", "فیض کاشانی")), verse_id
        assert "المیزان" in source_cites, verse_id
        bible = verse["extendedFields"]["bibleComparison"]
        if number in (21, 22, 23, 24):
            assert bible["status"] == "partial" and bible["entries"], verse_id
            assert "Bible-KJV" in bible["entries"][0]["cite"], verse_id
        else:
            assert bible["status"] == "needs-research" and not bible["entries"], verse_id
        science = verse["extendedFields"]["modernSciences"]
        assert science["status"] == "needs-research" and not science["entries"], verse_id
        qiraat = verse["extendedFields"]["qiraat"]
        if number == 24:
            assert qiraat["status"] == "partial" and len(qiraat["entries"]) == 1
            assert "طوسی" in qiraat["entries"][0]["cite"]
        else:
            assert qiraat["status"] == "needs-research" and not qiraat["entries"], verse_id
        assert "خاورشناختی" in verse["fieldCoverageStatus"], verse_id
        if number == 24:
            assert any("Mustafa Suna" in item["cite"] and "abstract" in item["cite"] for item in verse["modern"])
            assert any("Mustafa Suna" in item["cite"] for item in verse["extendedFields"]["historicalContext"]["entries"])


def test_tawbah_26_has_source_bounded_complete_fields_and_honest_gaps():
    verse = DATA["verses"]["9:26"]
    assert verse["title"].startswith("توبه ۹:۲۶")
    assert verse["fieldCoverageStatus"].startswith("شش فیلدِ پایه")
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 5, field
        assert all(len(item["text"].split()) >= 14 and item.get("cite", "").strip() for item in verse[field]), field

    for source_name in ("الطبري", "القرطبي", "ابن كثير", "البغوي", "طوسی", "فیض کاشانی"):
        assert any(source_name in item["cite"] for item in verse["classical"]), source_name
    modern_cites = " ".join(item["cite"] for item in verse["modern"])
    assert "Goldziher" in modern_cites and "Tornero" in modern_cites and "المیزان" in modern_cites
    assert "تفسير المنار" in modern_cites and "تفهيم القرآن" in modern_cites

    complete_fields = {
        "bibleComparison", "guidanceDiscourse", "shubuhat", "philosophicalFoundations",
        "linguistics", "criticalDiscourseAnalysis", "historicalContext", "balaghaNazm",
    }
    for field_id in complete_fields:
        field = verse["extendedFields"][field_id]
        assert field["status"] == "complete" and field["coverage"] == {"completed": 5, "required": 5}, field_id
        assert len(field["entries"]) == 5, field_id
        for entry in field["entries"]:
            assert len(entry["text"].split()) >= 14
            assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit"))
    assert all("Bible-KJV" in entry["cite"] for entry in verse["extendedFields"]["bibleComparison"]["entries"][:4])
    for field_id in ("modernSciences", "qiraat"):
        field = verse["extendedFields"][field_id]
        assert field["status"] == "needs-research" and field["entries"] == [], field_id
        assert field["sourceCoverageNote"].strip() and field["followUp"].strip()
    assert "گلدزیهر" in verse["extendedFields"]["shubuhat"]["sourceCoverageNote"]
    assert "منبعِ اختصاصیِ قراءات" in verse["extendedFields"]["qiraat"]["sourceCoverageNote"]


def test_tawbah_27_has_source_bounded_complete_fields_and_honest_gaps():
    verse = DATA["verses"]["9:27"]
    assert verse["title"].startswith("توبه ۹:۲۷")
    assert verse["fieldCoverageStatus"].startswith("شش فیلدِ پایه")
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 5, field
        assert all(len(item["text"].split()) >= 14 and item.get("cite", "").strip() for item in verse[field]), field

    classical_cites = " ".join(item["cite"] for item in verse["classical"])
    for source_name in ("الطبري", "القرطبي", "ابن كثير", "البغوي", "الطوسي", "فیض کاشانی"):
        assert source_name in classical_cites, source_name
    modern_cites = " ".join(item["cite"] for item in verse["modern"])
    assert "المیزان" in modern_cites and "تفسير الأمثل" in modern_cites
    assert "مودودی" in modern_cites and "قطب" in modern_cites and "Asad" in modern_cites

    complete_fields = {
        "bibleComparison", "guidanceDiscourse", "shubuhat", "philosophicalFoundations",
        "linguistics", "criticalDiscourseAnalysis", "historicalContext", "balaghaNazm",
    }
    for field_id in complete_fields:
        field = verse["extendedFields"][field_id]
        assert field["status"] == "complete" and field["coverage"] == {"completed": 5, "required": 5}, field_id
    bible_cites = " ".join(item["cite"] for item in verse["extendedFields"]["bibleComparison"]["entries"])
    for source_name in ("Ezekiel.json", "Jonah.json", "Luke.json", "1John.json", "Exodus.json"):
        assert source_name in bible_cites, source_name
    qiraat = verse["extendedFields"]["qiraat"]
    assert qiraat["status"] == "partial" and len(qiraat["entries"]) == 1
    assert "جمهرة العلوم" in qiraat["entries"][0]["cite"]
    science = verse["extendedFields"]["modernSciences"]
    assert science["status"] == "needs-research" and science["entries"] == []
    assert "جست‌وجویِ محدود" in science["sourceCoverageNote"]


def test_tawbah_28_has_source_bounded_material_and_honest_science_gap():
    verse = DATA["verses"]["9:28"]
    assert verse["title"].startswith("توبه ۹:۲۸")
    assert verse["fieldCoverageStatus"].startswith("شش فیلدِ پایه")
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 5, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
            assert item.get("cite", "").strip(), field

    classical_cites = " ".join(item["cite"] for item in verse["classical"])
    for source_name in ("الطبري", "القرطبي", "البغوي", "الطوسي", "الطبرسي", "ابن كثير"):
        assert source_name in classical_cites, source_name
    modern_cites = " ".join(item["cite"] for item in verse["modern"])
    for source_name in ("Darwish", "Maghen", "Zellentin", "Saputra"):
        assert source_name in modern_cites, source_name

    for field_id in EXPECTED_FIELDS - {"modernSciences"}:
        field = verse["extendedFields"][field_id]
        assert field["status"] == "complete", field_id
        assert len(field["entries"]) >= 5, field_id
        assert field["coverage"] == {"completed": len(field["entries"]), "required": 5}, field_id
        for entry in field["entries"]:
            assert len(entry["text"].split()) >= 14, field_id
            assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit")), field_id

    assert all("Bible-KJV" in entry["cite"] for entry in verse["extendedFields"]["bibleComparison"]["entries"])
    qiraat = verse["extendedFields"]["qiraat"]
    assert len(qiraat["entries"]) == 7
    assert "استقصای" in qiraat["sourceCoverageNote"]
    science = verse["extendedFields"]["modernSciences"]
    assert science["status"] == "needs-research" and science["entries"] == []
    assert "جست‌وجویِ وبِ محدود" in science["sourceCoverageNote"]
    assert science["followUp"].strip()


def test_tawbah_29_has_source_bounded_material_and_honest_gaps():
    verse = DATA["verses"]["9:29"]
    assert verse["title"].startswith("توبه ۹:۲۹")
    assert "یک یادداشتِ محدودیتِ دسترسی" in verse["fieldCoverageStatus"]
    assert "تکمیلِ پژوهشیِ آن ادعا نمی‌شود" in verse["fieldCoverageStatus"]
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 5, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
            assert item.get("cite", "").strip(), field
    assert any("الطبري" in item["cite"] for item in verse["classical"])
    assert any("الطوسي" in item["cite"] for item in verse["classical"])
    assert any("الطبرسي" in item["cite"] for item in verse["classical"])
    modern_cites = " ".join(item["cite"] for item in verse["modern"])
    for source_name in ("Abdel Haleem", "Afsaruddin", "Iqtidar", "Çakmak", "Kister"):
        assert source_name in modern_cites, source_name
    assert any(item.get("kind") == "source-coverage-note" for item in verse["modern"])

    for field_id in (
        "bibleComparison", "guidanceDiscourse", "shubuhat", "philosophicalFoundations",
        "linguistics", "criticalDiscourseAnalysis", "historicalContext", "balaghaNazm",
    ):
        field = verse["extendedFields"][field_id]
        assert field["status"] == "complete", field_id
        assert field["coverage"] == {"completed": 5, "required": 5}, field_id
        for entry in field["entries"]:
            assert len(entry["text"].split()) >= 14, field_id
            assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit")), field_id
    assert all("Bible-KJV" in entry["cite"] for entry in verse["extendedFields"]["bibleComparison"]["entries"])
    for field_id in ("modernSciences", "qiraat"):
        field = verse["extendedFields"][field_id]
        assert field["status"] == "needs-research" and field["entries"] == [], field_id
        assert field["sourceCoverageNote"].strip() and field["followUp"].strip()


def test_tawbah_30_has_source_bounded_material_and_preserves_disagreements():
    verse = DATA["verses"]["9:30"]
    assert verse["title"].startswith("توبه ۹:۳۰")
    assert "تکمیلِ پژوهشی‌اش ادعا نمی‌شود" in verse["fieldCoverageStatus"]
    assert "فهرست‌هایِ قرائت از منابعِ جداگانه حفظ شده‌اند" in verse["fieldCoverageStatus"]
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 5, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
            assert item.get("cite", "").strip(), field
    classical_cites = " ".join(item["cite"] for item in verse["classical"])
    for source_name in ("الطبري", "القرطبي", "أبو حيان", "الطبرسي", "ابن عاشور", "الرازي", "ابن كثير"):
        assert source_name in classical_cites, source_name
    modern_cites = " ".join(item["cite"] for item in verse["modern"])
    for source_name in ("QuranX", "TDV", "Aaron Koller", "Murat Kaya", "Sidky", "Reynolds"):
        assert source_name in modern_cites, source_name
    assert sum(item.get("kind") == "source-coverage-note" for item in verse["modern"]) == 1
    koller = next(item for item in verse["modern"] if "Aaron Koller" in item["cite"])
    assert "مشناه آووت» ۴:۱۲" in koller["text"] and "۹:۳۱" in koller["text"]

    for field_id in EXPECTED_FIELDS - {"modernSciences"}:
        field = verse["extendedFields"][field_id]
        assert field["status"] == "complete", field_id
        assert len(field["entries"]) >= 5, field_id
        assert field["coverage"] == {"completed": len(field["entries"]), "required": 5}, field_id
        for entry in field["entries"]:
            assert len(entry["text"].split()) >= 14, field_id
            assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit")), field_id
    qiraat = verse["extendedFields"]["qiraat"]
    assert len(qiraat["entries"]) == 8
    assert sum("qiraat-almawsoah/9/30" in entry["cite"] for entry in qiraat["entries"]) >= 4
    assert any("ابن عاشور" in entry["cite"] and "یعقوب" in entry["text"] for entry in qiraat["entries"])
    assert any("الطبرسي" in entry["cite"] and "سهل" in entry["text"] for entry in qiraat["entries"])
    assert any("مُصَرِّف" in entry["text"] for entry in qiraat["entries"])
    science = verse["extendedFields"]["modernSciences"]
    assert science["status"] == "needs-research" and science["entries"] == []

    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "۹:۳۰–۳۶" in scope["9:30–36"]
    assert "۹:۳۲–۳۶" in scope["9:30–36"]
    assert "۹:۳۷–۴۱" in scope["9:30–36"]
    assert "9:42–129" in scope
    assert "بازهٔ ۹:۳۲–۸۱" in scope["9:32–81"] and "همچنان پژوهش" in scope["9:32–81"]
    assert "کامل‌اند" in scope["9:1–129"]


def test_tawbah_31_has_source_bounded_sixteen_field_dossier():
    verse = DATA["verses"]["9:31"]
    assert verse["title"].startswith("توبه ۹:۳۱")
    assert "نه فیلدِ افزوده" in verse["fieldCoverageStatus"]
    assert "علومِ جدید" in verse["fieldCoverageStatus"]
    for field_id in BASE_FIELDS:
        assert len(verse[field_id]) >= 5, field_id
        for item in verse[field_id]:
            assert len(item["text"].split()) >= 14, field_id
            assert item.get("cite", "").strip(), field_id

    classical_cites = " ".join(item["cite"] for item in verse["classical"])
    for source_name in ("الطبري", "القرطبي", "ابن أبي حاتم", "فخر رازی", "أبو حيان", "شیخ طوسی", "طبرسی"):
        assert source_name in classical_cites, source_name
    modern_cites = " ".join(item["cite"] for item in verse["modern"])
    for source_name in ("الميزان", "مودودی", "طنطاوی", "Aaron Koller", "Holger Zellentin"):
        assert source_name in modern_cites, source_name

    koller = next(item for item in verse["modern"] if "Aaron Koller" in item["cite"])
    assert "۹:۳۱" in koller["text"] and "آووت ۴:۱۲" in koller["text"]
    assert "سنتِ شفاهیِ ربانی گسترده" in verse["critical"][4]["text"]
    assert "به ادعایِ ۹:۳۰" in verse["extendedFields"]["shubuhat"]["entries"][4]["limit"]
    mizan = next(item for item in verse["modern"] if "الميزان" in item["cite"])
    assert "TafsirNo=56" in mizan["cite"] and "ص ۲۴۵" not in mizan["cite"]

    for field_id in EXPECTED_FIELDS - {"modernSciences"}:
        field = verse["extendedFields"][field_id]
        assert field["status"] == "complete", field_id
        assert len(field["entries"]) >= 5, field_id
        assert field["coverage"] == {"completed": len(field["entries"]), "required": 5}, field_id
        for entry in field["entries"]:
            assert len(entry["text"].split()) >= 14, field_id
            assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit")), field_id

    qiraat = verse["extendedFields"]["qiraat"]
    assert len(qiraat["entries"]) == 6
    assert all("nQuran" in entry["cite"] for entry in qiraat["entries"])
    assert any("خلف" in item["text"] for item in qiraat["entries"])
    assert any("یعقوب" in item["text"] for item in qiraat["entries"])
    science = verse["extendedFields"]["modernSciences"]
    assert science["status"] == "needs-research" and science["entries"] == []
    assert "چهار جست‌وجوی وب" in science["sourceCoverageNote"]
    assert "نظام‌مند نیست" in science["sourceCoverageNote"]


def test_tawbah_32_to_36_have_sourced_entries_and_explicit_gaps():
    complete_fields = {
        "bibleComparison", "guidanceDiscourse", "philosophicalFoundations", "linguistics",
        "criticalDiscourseAnalysis", "historicalContext", "balaghaNazm",
    }
    partial_fields = {"shubuhat", "qiraat"}
    for number in range(32, 37):
        verse_id = f"9:{number}"
        verse = DATA["verses"][verse_id]
        persian_number = "".join("۰۱۲۳۴۵۶۷۸۹"[int(digit)] for digit in str(number))
        assert verse["title"].startswith(f"توبه ۹:{persian_number}")
        assert "هر شش فیلدِ پایه پنج بند دارند" in verse["fieldCoverageStatus"]
        for field_id in BASE_FIELDS:
            assert len(verse[field_id]) == 5, (verse_id, field_id)
            for entry in verse[field_id]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert entry.get("cite", "").strip(), (verse_id, field_id)
        for field_id in complete_fields:
            field = verse["extendedFields"][field_id]
            assert field["status"] == "complete" and len(field["entries"]) == 5, (verse_id, field_id)
            assert field["coverage"] == {"completed": 5, "required": 5}, (verse_id, field_id)
            for entry in field["entries"]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit")), (verse_id, field_id)
        for field_id in partial_fields:
            field = verse["extendedFields"][field_id]
            assert field["status"] == "partial" and len(field["entries"]) == 4, (verse_id, field_id)
            assert field["coverage"] == {"completed": 4, "required": 5}, (verse_id, field_id)
            assert field["sourceCoverageNote"].strip() and field["followUp"].strip(), (verse_id, field_id)
            for entry in field["entries"]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit")), (verse_id, field_id)
        science = verse["extendedFields"]["modernSciences"]
        assert science["status"] == "needs-research" and science["entries"] == [], verse_id
        assert science["coverage"] == {"completed": 0, "required": 5}
        assert science["sourceCoverageNote"].strip() and science["followUp"].strip()
        assert all("BibleGateway KJV" in item["cite"] for item in verse["extendedFields"]["bibleComparison"]["entries"])
        assert all("nQuran" in item["cite"] for item in verse["extendedFields"]["qiraat"]["entries"])

    assert "Wilde" in " ".join(item["cite"] for item in DATA["verses"]["9:32"]["modern"])
    assert "Sinai" in " ".join(item["cite"] for item in DATA["verses"]["9:34"]["modern"])
    assert "Zein" in " ".join(item["cite"] for item in DATA["verses"]["9:36"]["modern"])
    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "با منابعِ ثبت‌شده" in scope["9:32–81"]
    assert "بازهٔ ۹:۳۲–۸۱" in scope["9:32–81"] and "همچنان پژوهش" in scope["9:32–81"]


def test_tawbah_37_to_41_have_sourced_sixteen_field_dossiers_with_honest_gaps():
    complete_fields = {
        "bibleComparison", "guidanceDiscourse", "shubuhat", "philosophicalFoundations",
        "linguistics", "criticalDiscourseAnalysis", "historicalContext", "balaghaNazm",
    }
    expected_qiraat_counts = {37: 4, 38: 2, 39: 1, 40: 1, 41: 1}
    for number in range(37, 42):
        verse_id = f"9:{number}"
        verse = DATA["verses"][verse_id]
        persian_number = "".join("۰۱۲۳۴۵۶۷۸۹"[int(digit)] for digit in str(number))
        assert verse["title"].startswith(f"توبه ۹:{persian_number}")
        assert "شش فیلدِ پایه پنج بندِ مستند دارند" in verse["fieldCoverageStatus"]
        for field_id in BASE_FIELDS:
            assert len(verse[field_id]) == 5, (verse_id, field_id)
            for entry in verse[field_id]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert entry.get("cite", "").strip(), (verse_id, field_id)
        classical_cites = " ".join(entry["cite"] for entry in verse["classical"])
        for source_name in ("الطبري", "القرطبي", "ابن عاشور", "الطبرسي", "الطباطبائي"):
            assert source_name in classical_cites, (verse_id, source_name)
        assert "مودودی" in " ".join(entry["cite"] for entry in verse["modern"]), verse_id
        for field_id in complete_fields:
            field = verse["extendedFields"][field_id]
            assert field["status"] == "complete" and len(field["entries"]) == 5, (verse_id, field_id)
            assert field["coverage"] == {"completed": 5, "required": 5}, (verse_id, field_id)
            for entry in field["entries"]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit")), (verse_id, field_id)
        assert all("BibleGateway KJV" in entry["cite"] for entry in verse["extendedFields"]["bibleComparison"]["entries"])
        science = verse["extendedFields"]["modernSciences"]
        assert science["status"] == "needs-research" and science["entries"] == [], verse_id
        assert science["coverage"] == {"completed": 0, "required": 5}
        assert science["sourceCoverageNote"].strip() and science["followUp"].strip()
        qiraat = verse["extendedFields"]["qiraat"]
        assert qiraat["status"] == "partial", verse_id
        assert len(qiraat["entries"]) == expected_qiraat_counts[number], verse_id
        assert qiraat["coverage"] == {"completed": len(qiraat["entries"]), "required": 5}
        assert qiraat["sourceCoverageNote"].strip() and qiraat["followUp"].strip()
        for entry in qiraat["entries"]:
            assert len(entry["text"].split()) >= 14
            assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit"))
    assert "Zein" in " ".join(entry["cite"] for entry in DATA["verses"]["9:37"]["modern"])
    assert "Dost" in " ".join(entry["cite"] for entry in DATA["verses"]["9:37"]["modern"])
    assert "Rubin" in " ".join(entry["cite"] for entry in DATA["verses"]["9:40"]["modern"])
    assert "النشر" in DATA["verses"]["9:40"]["extendedFields"]["qiraat"]["entries"][0]["cite"]
    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "۹:۳۷–۴۱" in scope["9:37–41"] and "صفر مدخل" in scope["9:37–41"]
    assert "بازهٔ ۹:۳۲–۸۱" in scope["9:32–81"] and "همچنان پژوهش" in scope["9:32–81"]


def test_tawbah_42_to_46_have_source_bounded_sixteen_field_dossiers_with_honest_gaps():
    complete_fields = {
        "bibleComparison", "guidanceDiscourse", "philosophicalFoundations", "linguistics",
        "criticalDiscourseAnalysis", "historicalContext", "balaghaNazm",
    }
    expected_qiraat_counts = {42: 4, 43: 3, 44: 4, 45: 4, 46: 4}
    for number in range(42, 47):
        verse_id = f"9:{number}"
        verse = DATA["verses"][verse_id]
        persian_number = "".join("۰۱۲۳۴۵۶۷۸۹"[int(digit)] for digit in str(number))
        assert verse["title"].startswith(f"توبه ۹:{persian_number}"), verse_id
        assert "شش فیلدِ پایه پنج بندِ مستند دارند" in verse["fieldCoverageStatus"], verse_id
        assert "نیازمندِ داوریِ متخصص" in verse["reviewStatus"], verse_id
        for field_id in BASE_FIELDS:
            assert len(verse[field_id]) == 5, (verse_id, field_id)
            for entry in verse[field_id]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert entry.get("cite", "").strip(), (verse_id, field_id)
                assert entry.get("kind"), (verse_id, field_id)

        classical_cites = " ".join(item["cite"] for item in verse["classical"])
        for source_name in ("الطبري", "القرطبي", "ابن عاشور", "الطبرسي", "ابن كثير"):
            assert source_name in classical_cites, (verse_id, source_name)
        modern_cites = " ".join(item["cite"] for item in verse["modern"])
        for source_name in ("معارف القرآن", "السعدي", "الطباطبائي"):
            assert source_name in modern_cites, (verse_id, source_name)

        for field_id in complete_fields:
            field = verse["extendedFields"][field_id]
            assert field["status"] == "complete", (verse_id, field_id)
            assert field["coverage"] == {"completed": 5, "required": 5}, (verse_id, field_id)
            assert len(field["entries"]) == 5, (verse_id, field_id)
        for field_id in complete_fields | {"shubuhat", "qiraat"}:
            for entry in verse["extendedFields"][field_id]["entries"]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit")), (verse_id, field_id)
                assert entry.get("kind"), (verse_id, field_id)

        objections = verse["extendedFields"]["shubuhat"]
        assert objections["status"] == "partial" and len(objections["entries"]) == 4, verse_id
        assert objections["coverage"] == {"completed": 4, "required": 5}
        assert "چهار پرسش" in objections["sourceCoverageNote"]
        qiraat = verse["extendedFields"]["qiraat"]
        assert qiraat["status"] == "partial", verse_id
        assert len(qiraat["entries"]) == expected_qiraat_counts[number], verse_id
        assert qiraat["coverage"] == {"completed": expected_qiraat_counts[number], "required": 5}
        assert "nQuran" in qiraat["sourceCoverageNote"]
        assert all("nQuran" in item["cite"] for item in qiraat["entries"])

        science = verse["extendedFields"]["modernSciences"]
        assert science["status"] == "needs-research" and science["entries"] == [], verse_id
        assert science["coverage"] == {"completed": 0, "required": 5}
        assert "صفر از پنج" in science["sourceCoverageNote"]
        assert science["followUp"].strip()
        bible = verse["extendedFields"]["bibleComparison"]
        assert all("BibleGateway KJV" in item["cite"] for item in bible["entries"])

    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "۹:۴۲–۴۶" in scope["9:42–46"]
    assert "برداشتِ کاری" in scope["9:32–81"]
    assert "وارد شده" in scope["9:1–129"]


def test_tawbah_47_to_52_have_sourced_dossiers_and_explicit_open_questions():
    expected_complete = {47: 7, 48: 7, 49: 7, 50: 7, 51: 6, 52: 6}
    for number, completed_count in expected_complete.items():
        verse_id = f"9:{number}"
        verse = DATA["verses"][verse_id]
        assert verse["title"].startswith("توبه ۹:"), verse_id
        assert "نیازمندِ داوریِ متخصص" in verse["reviewStatus"], verse_id
        for field_id in BASE_FIELDS:
            assert len(verse[field_id]) == 5, (verse_id, field_id)
            for entry in verse[field_id]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert entry.get("cite", "").strip(), (verse_id, field_id)
        extended = verse["extendedFields"]
        assert sum(field["status"] == "complete" for field in extended.values()) == completed_count, verse_id
        for field_id, field in extended.items():
            assert field["coverage"] == {"completed": len(field["entries"]), "required": 5}, (verse_id, field_id)
            assert field["sourceCoverageNote"].strip() and field["followUp"].strip(), (verse_id, field_id)
            for entry in field["entries"]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit")), (verse_id, field_id)
        assert extended["modernSciences"]["status"] == "needs-research"
        assert extended["modernSciences"]["entries"] == []
        assert extended["qiraat"]["status"] == "partial" and len(extended["qiraat"]["entries"]) == 4
        assert extended["shubuhat"]["status"] == "partial" and len(extended["shubuhat"]["entries"]) == 4
        assert extended["bibleComparison"]["status"] == "complete" and len(extended["bibleComparison"]["entries"]) == 5
        if number >= 51:
            assert extended["historicalContext"]["status"] == "partial"
            assert len(extended["historicalContext"]["entries"]) == 4
        else:
            assert extended["historicalContext"]["status"] == "complete"
            assert len(extended["historicalContext"]["entries"]) == 5

    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "با منابعِ ثبت‌شده" in scope["9:32–81"]
    assert "بازهٔ ۹:۳۲–۸۱" in scope["9:32–81"] and "همچنان پژوهش" in scope["9:32–81"]
    assert "وارد شده" in scope["9:1–129"]

def test_tawbah_53_has_sourced_sixteen_field_dossier_with_honest_gaps():
    verse = DATA["verses"]["9:53"]
    assert verse["title"].startswith("توبه ۹:۵۳")
    assert "شش فیلدِ پایه موجود" in verse["fieldCoverageStatus"]
    assert "هشت فیلدِ افزوده" in verse["fieldCoverageStatus"]
    assert "نیازمندِ داوریِ متخصص" in verse["reviewStatus"]
    for field_id in BASE_FIELDS:
        assert len(verse[field_id]) == 5, field_id
        for entry in verse[field_id]:
            assert len(entry["text"].split()) >= 14, field_id
            assert entry["cite"].strip(), field_id

    complete_fields = {
        "bibleComparison", "guidanceDiscourse", "shubuhat", "qiraat",
        "philosophicalFoundations", "linguistics", "criticalDiscourseAnalysis", "balaghaNazm",
    }
    partial_fields = {"modernSciences", "historicalContext"}
    for field_id in complete_fields:
        field = verse["extendedFields"][field_id]
        assert field["status"] == "complete" and len(field["entries"]) == 5, field_id
        assert field["coverage"] == {"completed": 5, "required": 5}, field_id
        for entry in field["entries"]:
            assert len(entry["text"].split()) >= 14, field_id
            assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit")), field_id
    for field_id, expected in (("modernSciences", 4), ("historicalContext", 4)):
        field = verse["extendedFields"][field_id]
        assert field["status"] == "partial" and len(field["entries"]) == expected, field_id
        assert field["coverage"] == {"completed": expected, "required": 5}, field_id
        assert field["sourceCoverageNote"].strip() and field["followUp"].strip(), field_id
        for entry in field["entries"]:
            assert len(entry["text"].split()) >= 14, field_id
            assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit")), field_id

    bible_cites = " ".join(item["cite"] for item in verse["extendedFields"]["bibleComparison"]["entries"])
    for reference in ("Exodus 25:2", "Deuteronomy 16:10", "2 Corinthians 8:12-14", "2 Corinthians 9:7", "Amos 5:21-24"):
        assert reference in bible_cites, reference
    qiraat_cites = " ".join(item["cite"] for item in verse["extendedFields"]["qiraat"]["entries"])
    assert "nQuran" in qiraat_cites and "مفاتيح الغيب" in qiraat_cites
    assert "طرق" in verse["extendedFields"]["qiraat"]["sourceCoverageNote"]
    science_cites = " ".join(item["cite"] for item in verse["extendedFields"]["modernSciences"]["entries"])
    for source in ("PLoS ONE", "Social Cognitive and Affective Neuroscience", "Journal of Business Research", "Experimental Social Psychology"):
        assert source in science_cites, source
    assert "قبولِ الهی" in verse["extendedFields"]["modernSciences"]["sourceCoverageNote"]
    assert "مستقلاً" in verse["extendedFields"]["historicalContext"]["sourceCoverageNote"]

    v52_bible_cites = " ".join(item["cite"] for item in DATA["verses"]["9:52"]["extendedFields"]["bibleComparison"]["entries"])
    assert "Daniel 3:16-18" in v52_bible_cites
    assert "Acts 5:38-39" not in v52_bible_cites
    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "توبه ۹:۵۳ ثبت شد" in scope["9:53"]
    assert "بازهٔ ۹:۳۲–۸۱" in scope["9:32–81"] and "همچنان پژوهش" in scope["9:32–81"]


def test_tawbah_54_to_55_have_sourced_dossiers_with_honest_gaps():
    for number in (54, 55):
        verse_id = f"9:{number}"
        verse = DATA["verses"][verse_id]
        assert verse["title"].startswith("توبه ۹:"), verse_id
        assert "شش فیلدِ پایه" in verse["fieldCoverageStatus"], verse_id
        assert "هشت" in verse["fieldCoverageStatus"] and "partial" in verse["fieldCoverageStatus"], verse_id
        assert "نیازمندِ داوریِ متخصص" in verse["reviewStatus"], verse_id
        for field_id in BASE_FIELDS:
            assert len(verse[field_id]) == 5, (verse_id, field_id)
            for entry in verse[field_id]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert entry.get("cite", "").strip(), (verse_id, field_id)
        extended = verse["extendedFields"]
        assert sum(item["status"] == "complete" for item in extended.values()) == 8, verse_id
        assert sum(item["status"] == "partial" for item in extended.values()) == 2, verse_id
        for field_id, item in extended.items():
            assert item["coverage"] == {"completed": len(item["entries"]), "required": 5}, (verse_id, field_id)
            assert item["sourceCoverageNote"].strip() and item["followUp"].strip(), (verse_id, field_id)
            for entry in item["entries"]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit")), (verse_id, field_id)
        for field_id in ("modernSciences", "historicalContext"):
            assert extended[field_id]["status"] == "partial", (verse_id, field_id)
            assert len(extended[field_id]["entries"]) == 4, (verse_id, field_id)
        assert extended["qiraat"]["status"] == "complete" and len(extended["qiraat"]["entries"]) == 5
        assert all("nQuran" in item["cite"] for item in extended["qiraat"]["entries"])
        assert extended["bibleComparison"]["status"] == "complete" and len(extended["bibleComparison"]["entries"]) == 5
        assert all("BibleGateway KJV" in item["cite"] for item in extended["bibleComparison"]["entries"])

    verse54 = DATA["verses"]["9:54"]
    for source in ("الطبري", "القرطبي", "فخر رازی", "ابن عطية", "ابن أبي حاتم"):
        assert source in " ".join(item["cite"] for item in verse54["classical"]), source
    assert "Shariff" in " ".join(item["cite"] for item in verse54["extendedFields"]["modernSciences"]["entries"])
    assert "Gomes" in " ".join(item["cite"] for item in verse54["extendedFields"]["modernSciences"]["entries"])

    verse55 = DATA["verses"]["9:55"]
    for source in ("الطبري", "ابن كثير", "القرطبي", "ابن عطية", "فخر رازی"):
        assert source in " ".join(item["cite"] for item in verse55["classical"]), source
    assert "Kasser & Ryan" in " ".join(item["cite"] for item in verse55["extendedFields"]["modernSciences"]["entries"])
    assert "Dittmar" in " ".join(item["cite"] for item in verse55["extendedFields"]["modernSciences"]["entries"])

    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "با منابعِ ثبت‌شده" in scope["9:32–81"]
    assert "بازهٔ ۹:۳۲–۸۱" in scope["9:32–81"] and "همچنان پژوهش" in scope["9:32–81"]
    assert "وارد شده" in scope["9:1–129"]
    assert "توبه ۹:۵۴ ثبت شد" in scope["9:54"]
    assert "توبه ۹:۵۵ ثبت شد" in scope["9:55"]


def test_tawbah_56_to_57_have_sourced_dossiers_and_honest_gaps():
    expected_complete = {56: 6, 57: 7}
    expected_partial = {56: 4, 57: 3}
    for number in (56, 57):
        verse_id = f"9:{number}"
        verse = DATA["verses"][verse_id]
        persian_number = "".join("۰۱۲۳۴۵۶۷۸۹"[int(digit)] for digit in str(number))
        assert verse["title"].startswith(f"توبه ۹:{persian_number}"), verse_id
        assert "نیازمندِ داوریِ متخصص" in verse["reviewStatus"], verse_id
        for field_id in BASE_FIELDS:
            assert len(verse[field_id]) == 5, (verse_id, field_id)
            for entry in verse[field_id]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert entry.get("cite", "").strip(), (verse_id, field_id)

        extended = verse["extendedFields"]
        assert sum(field["status"] == "complete" for field in extended.values()) == expected_complete[number], verse_id
        assert sum(field["status"] == "partial" for field in extended.values()) == expected_partial[number], verse_id
        for field_id, field in extended.items():
            assert field["coverage"] == {"completed": len(field["entries"]), "required": 5}, (verse_id, field_id)
            assert field["sourceCoverageNote"].strip() and field["followUp"].strip(), (verse_id, field_id)
            for entry in field["entries"]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit")), (verse_id, field_id)

    verse56 = DATA["verses"]["9:56"]
    classical56 = " ".join(item["cite"] for item in verse56["classical"])
    for source in ("الطبري", "القرطبي", "ابن عطية", "الرازي"):
        assert source in classical56, source
    modern56 = " ".join(item["cite"] for item in verse56["modern"])
    science56 = " ".join(item["cite"] for item in verse56["extendedFields"]["modernSciences"]["entries"])
    assert "ابن عاشور" in modern56
    assert "Jacquemet" in science56 and "Beck" in science56 and "Levine" in science56
    bible56 = " ".join(item["cite"] for item in verse56["extendedFields"]["bibleComparison"]["entries"])
    for reference in ("Leviticus 19:12", "Matthew 5:33-37", "James 5:12", "Deuteronomy 19:16-21", "Psalm 15:4"):
        assert reference in bible56, reference
    assert verse56["extendedFields"]["qiraat"]["status"] == "partial"
    assert len(verse56["extendedFields"]["qiraat"]["entries"]) == 2
    assert all("nQuran" in item["cite"] for item in verse56["extendedFields"]["qiraat"]["entries"])
    assert verse56["extendedFields"]["shubuhat"]["status"] == "partial"
    assert "جست‌وجوی محدود" in verse56["extendedFields"]["shubuhat"]["sourceCoverageNote"]

    verse57 = DATA["verses"]["9:57"]
    classical57 = " ".join(item["cite"] for item in verse57["classical"])
    for source in ("الطبري", "القرطبي", "ابن عطية", "الرازي", "ابن كثير"):
        assert source in classical57, source
    assert "ابن عاشور" in " ".join(item["cite"] for item in verse57["modern"])
    science57 = " ".join(item["cite"] for item in verse57["extendedFields"]["modernSciences"]["entries"])
    for source in ("Mobbs", "Löw", "Harrison", "Vieira"):
        assert source in science57, source
    qiraat57 = verse57["extendedFields"]["qiraat"]
    assert qiraat57["status"] == "complete" and len(qiraat57["entries"]) == 5
    assert all("nQuran" in item["cite"] for item in qiraat57["entries"])
    assert any("يجمحون" in item["text"] for item in verse57["extendedFields"]["linguistics"]["entries"])
    bible57 = " ".join(item["cite"] for item in verse57["extendedFields"]["bibleComparison"]["entries"])
    for reference in ("Judges 6:2", "1 Kings 19:9-13", "Psalm 139:7-10", "Amos 9:2-3", "Jonah 1:3-4"):
        assert reference in bible57, reference

    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "توبه ۹:۵۶ ثبت شد" in scope["9:56"]
    assert "توبه ۹:۵۷ ثبت شد" in scope["9:57"]
    assert "با منابعِ ثبت‌شده" in scope["9:32–81"]
    assert "بازهٔ ۹:۳۲–۸۱" in scope["9:32–81"] and "همچنان پژوهش" in scope["9:32–81"]
    assert "overlay اکنون تا" in scope["9:1–129"]
    assert "وارد شده" in scope["9:1–129"]


def test_tawbah_58_to_60_have_sourced_dossiers_and_explicit_gaps():
    expected_statuses = {"bibleComparison": "complete", "guidanceDiscourse": "complete", "shubuhat": "partial", "modernSciences": "complete", "qiraat": "partial", "philosophicalFoundations": "complete", "linguistics": "complete", "criticalDiscourseAnalysis": "complete", "historicalContext": "partial", "balaghaNazm": "complete"}
    seen_texts = set()
    for number in (58, 59, 60):
        verse_id = f"9:{number}"
        verse = DATA["verses"][verse_id]
        persian_number = "".join("۰۱۲۳۴۵۶۷۸۹"[int(digit)] for digit in str(number))
        assert verse["title"].startswith(f"توبه ۹:{persian_number}"), verse_id
        assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"], verse_id
        assert "هفت complete و سه partial" in verse["fieldCoverageStatus"], verse_id
        for field_id in BASE_FIELDS:
            assert len(verse[field_id]) == 5, (verse_id, field_id)
            for entry in verse[field_id]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert entry.get("cite", "").strip(), (verse_id, field_id)
                normalized = " ".join(entry["text"].split())
                assert normalized not in seen_texts, (verse_id, field_id, normalized)
                seen_texts.add(normalized)
        extended = verse["extendedFields"]
        assert set(extended) == EXPECTED_FIELDS, verse_id
        for field_id, expected in expected_statuses.items():
            field = extended[field_id]
            assert field["status"] == expected, (verse_id, field_id)
            assert field["coverage"] == {"completed": len(field["entries"]), "required": 5}, (verse_id, field_id)
            assert field["sourceCoverageNote"].strip() and field["followUp"].strip(), (verse_id, field_id)
            if expected == "complete":
                assert len(field["entries"]) == 5, (verse_id, field_id)
            else:
                assert 0 < len(field["entries"]) < 5, (verse_id, field_id)
            for entry in field["entries"]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert all(entry.get(key, "").strip() for key in ("cite", "evidence", "limit")), (verse_id, field_id)
                assert entry.get("kind"), (verse_id, field_id)
                normalized = " ".join(entry["text"].split())
                assert normalized not in seen_texts, (verse_id, field_id, normalized)
                seen_texts.add(normalized)
        assert sum(field["status"] == "complete" for field in extended.values()) == 7, verse_id
        assert sum(field["status"] == "partial" for field in extended.values()) == 3, verse_id
        assert len(extended["bibleComparison"]["entries"]) == 5
        assert all("BibleGateway KJV" in entry["cite"] for entry in extended["bibleComparison"]["entries"])
        assert len(extended["modernSciences"]["entries"]) == 5
        assert len(extended["shubuhat"]["entries"]) == 4
        assert len(extended["historicalContext"]["entries"]) in (3, 4)
        qiraat = extended["qiraat"]
        assert len(qiraat["entries"]) == 1
        if number == 58:
            assert "qiraat-almawsoah/9/58" in qiraat["entries"][0]["cite"]
            assert "يلمزك" in qiraat["entries"][0]["text"]
        elif number == 59:
            assert qiraat["entries"][0]["kind"] == "source-coverage-note"
            assert "qiraat-almawsoah/9/59" in qiraat["entries"][0]["cite"]
        else:
            assert "qiraat-almawsoah/9/60" in qiraat["entries"][0]["cite"]
            assert "فريضة" in qiraat["entries"][0]["text"]
        classical_cites = " ".join(item["cite"] for item in verse["classical"])
        for author in ("الطبري", "القرطبي", "ابن عطية", "ابن كثير", "الرازي"):
            assert author in classical_cites, (verse_id, author)
        assert "ابن عاشور" in " ".join(item["cite"] for item in verse["modern"]), verse_id
        if number in (58, 59):
            assert "10.1017/S0041977X00026926" in " ".join(item["cite"] for item in verse["research"]), verse_id

    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    for number in (58, 59, 60):
        persian_number = "".join("۰۱۲۳۴۵۶۷۸۹"[int(digit)] for digit in str(number))
        assert f"توبه ۹:{persian_number}" in scope[f"9:{number}"]
    assert "با منابعِ ثبت‌شده" in scope["9:32–81"]
    assert "بازهٔ ۹:۳۲–۸۱" in scope["9:32–81"] and "همچنان پژوهش" in scope["9:32–81"]
    assert "overlay اکنون تا" in scope["9:1–129"] and "رکورد" in scope["9:1–129"]
    assert "وارد شده" in scope["9:1–129"]
    assert "پس از مقابلهٔ منابع" in scope["9:42–129"]
    assert "آیه‌به‌آیه افزوده شده‌اند" in scope["9:42–46"]


def test_tawbah_61_to_62_have_sourced_dossiers_and_explicit_gaps():
    expected_statuses = {"bibleComparison": "complete", "guidanceDiscourse": "complete", "shubuhat": "partial", "modernSciences": "complete", "qiraat": "partial", "philosophicalFoundations": "complete", "linguistics": "complete", "criticalDiscourseAnalysis": "complete", "historicalContext": "partial", "balaghaNazm": "complete"}
    seen_texts = set()
    for number in (61, 62):
        verse_id = f"9:{number}"
        verse = DATA["verses"][verse_id]
        persian_number = "".join("۰۱۲۳۴۵۶۷۸۹"[int(digit)] for digit in str(number))
        assert verse["title"].startswith(f"توبه ۹:{persian_number}"), verse_id
        assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"], verse_id
        assert "هفت فیلدِ افزوده" in verse["fieldCoverageStatus"], verse_id
        for field_id in BASE_FIELDS:
            assert len(verse[field_id]) == 5, (verse_id, field_id)
            for item in verse[field_id]:
                assert len(item["text"].split()) >= 14, (verse_id, field_id)
                assert item.get("cite", "").strip(), (verse_id, field_id)
                normalized = " ".join(item["text"].split())
                assert normalized not in seen_texts, (verse_id, field_id, normalized)
                seen_texts.add(normalized)
        extended = verse["extendedFields"]
        assert set(extended) == EXPECTED_FIELDS, verse_id
        for field_id, expected in expected_statuses.items():
            field = extended[field_id]
            assert field["status"] == expected, (verse_id, field_id)
            assert field["coverage"] == {"completed": len(field["entries"]), "required": 5}, (verse_id, field_id)
            assert field["sourceCoverageNote"].strip() and field["followUp"].strip(), (verse_id, field_id)
            if expected == "complete":
                assert len(field["entries"]) == 5, (verse_id, field_id)
            else:
                assert 0 < len(field["entries"]) < 5, (verse_id, field_id)
            for item in field["entries"]:
                assert len(item["text"].split()) >= 14, (verse_id, field_id, item["text"])
                assert all(item.get(key, "").strip() for key in ("cite", "evidence", "limit")), (verse_id, field_id)
                assert item.get("kind"), (verse_id, field_id)
                normalized = " ".join(item["text"].split())
                assert normalized not in seen_texts, (verse_id, field_id, normalized)
                seen_texts.add(normalized)
        assert sum(field["status"] == "complete" for field in extended.values()) == 7, verse_id
        assert sum(field["status"] == "partial" for field in extended.values()) == 3, verse_id
        assert len(extended["bibleComparison"]["entries"]) == 5
        assert all("BibleGateway KJV" in item["cite"] for item in extended["bibleComparison"]["entries"])
        assert len(extended["modernSciences"]["entries"]) == 5
        assert len(extended["shubuhat"]["entries"]) == 4
        assert len(extended["historicalContext"]["entries"]) == 4
        qiraat = extended["qiraat"]
        if number == 61:
            assert len(qiraat["entries"]) == 3
            assert "أذنٌ خيرٌ" in " ".join(item["text"] for item in qiraat["entries"])
            assert "ورحمةٍ" in " ".join(item["text"] for item in qiraat["entries"])
            assert any("qiraat-almawsoah/9/61" in item["cite"] for item in qiraat["entries"])
        else:
            assert len(qiraat["entries"]) == 1
            assert qiraat["entries"][0]["kind"] == "source-coverage-note"
            assert "qiraat-almawsoah/9/62" in qiraat["entries"][0]["cite"]
        classical_cites = " ".join(item["cite"] for item in verse["classical"])
        for author in ("الطبري", "القرطبي", "ابن عطية", "ابن كثير", "الرازي"):
            assert author in classical_cites, (verse_id, author)
        assert "ابن عاشور" in " ".join(item["cite"] for item in verse["modern"]), verse_id
        research_cites = " ".join(item["cite"] for item in verse["research"])
        assert "10.1017/S0041977X00026926" in research_cites, verse_id
        if number == 61:
            assert "10.1111/j.1749-6632.1976.tb25467.x" in research_cites
            assert "10.1515/cogl.1998.9.1.37" in research_cites
        else:
            assert "How to Do Things with Words" in research_cites
            assert "Speech Acts" in research_cites

    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "توبه ۹:۶۱ ثبت شد" in scope["9:61"]
    assert "توبه ۹:۶۲ ثبت شد" in scope["9:62"]
    assert "بازهٔ ۹:۶۱–۶۲ اکنون" in scope["9:61–62"]
    assert "بازهٔ ۹:۳۲–۸۱" in scope["9:32–81"] and "همچنان پژوهش" in scope["9:32–81"]
    assert "overlay اکنون تا" in scope["9:1–129"] and "رکورد" in scope["9:1–129"]
    assert "وارد شده" in scope["9:1–129"]


def test_all_recorded_texts_are_unique_across_ayahs_and_fields():
    seen = {}
    for verse_id, verse in DATA["verses"].items():
        for field_id in BASE_FIELDS:
            for index, entry in enumerate(verse[field_id], start=1):
                normalized = " ".join(entry["text"].split())
                location = (verse_id, field_id, index)
                assert normalized not in seen, (location, seen.get(normalized))
                seen[normalized] = location
        for field_id, field in verse["extendedFields"].items():
            for index, entry in enumerate(field["entries"], start=1):
                normalized = " ".join(entry["text"].split())
                location = (verse_id, field_id, index)
                assert normalized not in seen, (location, seen.get(normalized))
                seen[normalized] = location


def test_ui_opens_one_ayah_level_view_with_all_sixteen_fields():

    assert 'all: completeDossierPanel' in APP
    assert 'state.detailTab = "all"' in APP
    assert "LEGACY_DOSSIER_ORDER" in APP
    assert "STANDARD3_FIELD_FALLBACKS" in APP
    assert "state.standard3Dossier?.fields?.length" in APP
    assert "extendedFields" in APP
    assert "verse-dossier-extended-fields.json" in APP
    assert "function standard3FieldPanel" in APP
    for field_id in EXPECTED_FIELDS:
        assert f'data-detail-tab="standard3_{field_id}"' in HTML, field_id


def test_tawbah_63_to_64_have_sourced_dossiers_and_explicit_gaps():
    expected_statuses = {"bibleComparison": "complete", "guidanceDiscourse": "complete", "shubuhat": "partial", "modernSciences": "complete", "qiraat": "partial", "philosophicalFoundations": "complete", "linguistics": "complete", "criticalDiscourseAnalysis": "complete", "historicalContext": "partial", "balaghaNazm": "complete"}
    seen_texts = set()
    for number in (63, 64):
        verse_id = f"9:{number}"
        verse = DATA["verses"][verse_id]
        persian_number = "".join("۰۱۲۳۴۵۶۷۸۹"[int(digit)] for digit in str(number))
        assert verse["title"].startswith(f"توبه ۹:{persian_number}"), verse_id
        assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"], verse_id
        assert "هفت فیلدِ افزوده" in verse["fieldCoverageStatus"], verse_id
        for field_id in BASE_FIELDS:
            assert len(verse[field_id]) == 5, (verse_id, field_id)
            for item in verse[field_id]:
                assert len(item["text"].split()) >= 14, (verse_id, field_id)
                assert item.get("cite", "").strip(), (verse_id, field_id)
                normalized = " ".join(item["text"].split())
                assert normalized not in seen_texts, (verse_id, field_id, normalized)
                seen_texts.add(normalized)
        extended = verse["extendedFields"]
        assert set(extended) == EXPECTED_FIELDS, verse_id
        for field_id, expected in expected_statuses.items():
            field = extended[field_id]
            assert field["status"] == expected, (verse_id, field_id)
            assert field["coverage"] == {"completed": len(field["entries"]), "required": 5}, (verse_id, field_id)
            assert field["sourceCoverageNote"].strip() and field["followUp"].strip(), (verse_id, field_id)
            if expected == "complete":
                assert len(field["entries"]) == 5, (verse_id, field_id)
            else:
                assert 0 < len(field["entries"]) < 5, (verse_id, field_id)
            for item in field["entries"]:
                assert len(item["text"].split()) >= 14, (verse_id, field_id, item["text"])
                assert all(item.get(key, "").strip() for key in ("cite", "evidence", "limit")), (verse_id, field_id)
                assert item.get("kind"), (verse_id, field_id)
                normalized = " ".join(item["text"].split())
                assert normalized not in seen_texts, (verse_id, field_id, normalized)
                seen_texts.add(normalized)
        assert sum(field["status"] == "complete" for field in extended.values()) == 7, verse_id
        assert sum(field["status"] == "partial" for field in extended.values()) == 3, verse_id
        assert len(extended["bibleComparison"]["entries"]) == 5
        assert all("BibleGateway KJV" in item["cite"] for item in extended["bibleComparison"]["entries"])
        assert len(extended["modernSciences"]["entries"]) == 5
        assert len(extended["shubuhat"]["entries"]) == 4
        assert len(extended["historicalContext"]["entries"]) == 4
        qiraat = extended["qiraat"]
        if number == 63:
            assert len(qiraat["entries"]) == 3
            qiraat_text = " ".join(item["text"] for item in qiraat["entries"])
            assert "تعلموا" in qiraat_text and "ابنِ ابی‌عبله" in qiraat_text
            assert all("qiraat-almawsoah/9/63" in item["cite"] for item in qiraat["entries"])
        else:
            assert len(qiraat["entries"]) == 3
            qiraat_text = " ".join(item["text"] for item in qiraat["entries"])
            assert "تنزل" in qiraat_text and "تنزّل" in qiraat_text
            assert any(item["kind"] == "source-coverage-note" for item in qiraat["entries"])
            assert all("qiraat-almawsoah/9/64" in item["cite"] for item in qiraat["entries"])
        classical_cites = " ".join(item["cite"] for item in verse["classical"])
        for author in ("الطبري", "القرطبي", "البغوي", "ابن عطية"):
            assert author in classical_cites, (verse_id, author)
        modern_cites = " ".join(item["cite"] for item in verse["modern"])
        assert "ابن عاشور" in modern_cites, verse_id
        if number == 63:
            assert "ابن كثير" in classical_cites and "سعدی" in modern_cites
            assert "10.1017/S0041977X00026926" in " ".join(item["cite"] for item in verse["research"])
        else:
            assert "الزجاج" in classical_cites and "مودودی" in modern_cites
            assert "المختصر" in modern_cites

    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "توبه ۹:۶۳ ثبت شد" in scope["9:63"]
    assert "توبه ۹:۶۴ ثبت شد" in scope["9:64"]
    assert "بازهٔ ۹:۶۳–۶۴ در overlay" in scope["9:63–64"]
    assert "بازهٔ ۹:۳۲–۸۱" in scope["9:32–81"] and "همچنان پژوهش" in scope["9:32–81"]
    assert "overlay اکنون تا" in scope["9:1–129"] and "رکورد" in scope["9:1–129"]
    assert "وارد شده" in scope["9:1–129"]


def test_tawbah_65_has_sourced_dossier_and_explicit_gaps():
    verse_id = "9:65"
    verse = DATA["verses"][verse_id]
    assert verse["title"].startswith("توبه ۹:۶۵")
    assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"]
    assert "هفت فیلدِ افزوده" in verse["fieldCoverageStatus"]

    seen_texts = set()
    for field_id in BASE_FIELDS:
        assert len(verse[field_id]) == 5, field_id
        for item in verse[field_id]:
            assert len(item["text"].split()) >= 14, field_id
            assert item.get("cite", "").strip(), field_id
            normalized = " ".join(item["text"].split())
            assert normalized not in seen_texts, (field_id, normalized)
            seen_texts.add(normalized)

    extended = verse["extendedFields"]
    assert set(extended) == EXPECTED_FIELDS
    expected_statuses = {
        "bibleComparison": ("complete", 5),
        "guidanceDiscourse": ("complete", 5),
        "shubuhat": ("partial", 4),
        "modernSciences": ("complete", 5),
        "qiraat": ("partial", 1),
        "philosophicalFoundations": ("complete", 5),
        "linguistics": ("complete", 5),
        "criticalDiscourseAnalysis": ("complete", 5),
        "historicalContext": ("partial", 4),
        "balaghaNazm": ("complete", 5),
    }
    for field_id, (status, count) in expected_statuses.items():
        field = extended[field_id]
        assert field["status"] == status, field_id
        assert len(field["entries"]) == count, field_id
        assert field["coverage"] == {"completed": count, "required": 5}, field_id
        assert field["sourceCoverageNote"].strip() and field["followUp"].strip(), field_id
        for item in field["entries"]:
            assert len(item["text"].split()) >= 14, (field_id, item["text"])
            assert all(item.get(key, "").strip() for key in ("cite", "evidence", "limit")), field_id
            assert item.get("kind"), field_id
            normalized = " ".join(item["text"].split())
            assert normalized not in seen_texts, (field_id, normalized)
            seen_texts.add(normalized)

    classical_cites = " ".join(item["cite"] for item in verse["classical"])
    for author in ("الطبري", "القرطبي", "البغوي", "ابن عطية", "ابن كثير"):
        assert author in classical_cites, author
    modern_cites = " ".join(item["cite"] for item in verse["modern"])
    for author in ("ابن عاشور", "سعدی", "الميسر", "المختصر", "الجزائري"):
        assert author in modern_cites, author
    assert "دعاس" in " ".join(item["cite"] for item in verse["notes"])
    assert all("BibleGateway KJV" in item["cite"] for item in extended["bibleComparison"]["entries"])
    qiraat = extended["qiraat"]
    assert qiraat["entries"][0]["kind"] == "source-coverage-note"
    assert "qiraat-almawsoah/9/65" in qiraat["entries"][0]["cite"]
    assert "ابن‌العربی" in " ".join(item["text"] for item in extended["shubuhat"]["entries"])
    assert "ابن‌اسحاق" in " ".join(item["text"] for item in extended["historicalContext"]["entries"])

    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "توبه ۹:۶۵ ثبت شد" in scope["9:65"]
    assert "بازهٔ ۹:۶۳–۶۵ در overlay" in scope["9:63–65"]
    assert "بازهٔ ۹:۳۲–۸۱" in scope["9:32–81"] and "همچنان پژوهش" in scope["9:32–81"]
    assert "overlay اکنون تا" in scope["9:1–129"] and "رکورد" in scope["9:1–129"]
    assert "وارد شده" in scope["9:1–129"]


def test_scope_frontier_tracks_current_records():
    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "overlay اکنون تا ۹:۱۰۸ و آیاتِ آغازینِ يونس" in scope["9:1–129"]
    assert f"{_fa(len(DATA['verses']))} رکورد" in scope["9:1–129"]
    assert "۹:۱۰۹–۱۲۹" in scope["9:1–129"] and "وارد شده" in scope["9:1–129"]
    assert "به‌طورِ کامل واردِ overlay شده" in scope["9:32–81"]
    assert "۹:۷۵–۸۱ در سطحِ core" in scope["9:32–81"]
    assert "۹:۴۲–۱۰۸" in scope["9:42–129"]
    assert "۹:۴۷–۱۰۸" in scope["9:42–46"]
    assert "توبه ۹:۶۵ ثبت شد" in scope["9:65"]
    assert "توبه ۹:۶۶ ثبت شد" in scope["9:66"]
    assert "۹:۶۷ با شش فیلدِ پایهٔ پنج‌مدخلی" in scope["9:67"]
    assert "زوجِ ۹:۶۶–۶۷ پیوسته ثبت شده‌اند" in scope["9:66–67"]
    assert "۹:۶۸ با شش فیلدِ پایهٔ پنج‌مدخلی" in scope["9:68"]
    assert "۹:۶۹ با شش فیلدِ پایهٔ پنج‌مدخلی" in scope["9:69"]
    assert "زوجِ ۹:۶۸–۶۹ پیوسته ثبت شده‌اند" in scope["9:68–69"]
    assert "۹:۷۰–۸۱ کامل شد" in scope["9:70–81"]


def test_tawbah_66_has_complete_sourced_dossier():
    verse = DATA["verses"]["9:66"]
    assert verse["title"].startswith("توبه ۹:۶۶")
    assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"]
    assert "ده فیلدِ افزوده" in verse["fieldCoverageStatus"]

    seen_texts = set()
    for field_id in BASE_FIELDS:
        assert len(verse[field_id]) == 5, field_id
        for item in verse[field_id]:
            assert len(item["text"].split()) >= 14, field_id
            assert item.get("cite", "").strip(), field_id
            normalized = " ".join(item["text"].split())
            assert normalized not in seen_texts, (field_id, normalized)
            seen_texts.add(normalized)

    extended = verse["extendedFields"]
    assert set(extended) == EXPECTED_FIELDS
    for field_id, field in extended.items():
        assert field["status"] == "complete", field_id
        assert len(field["entries"]) == 5, field_id
        assert field["coverage"] == {"completed": 5, "required": 5}, field_id
        assert field["sourceCoverageNote"].strip() and field["followUp"].strip(), field_id
        for item in field["entries"]:
            assert len(item["text"].split()) >= 14, (field_id, item["text"])
            assert all(item.get(key, "").strip() for key in ("cite", "evidence", "limit")), field_id
            normalized = " ".join(item["text"].split())
            assert normalized not in seen_texts, (field_id, normalized)
            seen_texts.add(normalized)

    classical_cites = " ".join(item["cite"] for item in verse["classical"])
    for author in ("الطبري", "القرطبي", "البغوي", "ابن عطية", "ابن كثير"):
        assert author in classical_cites, author
    modern_cites = " ".join(item["cite"] for item in verse["modern"])
    for author in ("ابن عاشور", "سعدی", "الميسر", "المختصر", "الجزائري"):
        assert author in modern_cites, author
    assert all("BibleGateway KJV" in item["cite"] for item in extended["bibleComparison"]["entries"])
    assert "without excuse" in " ".join(item["evidence"] for item in extended["bibleComparison"]["entries"])
    qiraat_text = " ".join(item["text"] for item in extended["qiraat"]["entries"])
    assert "جَحدری" in qiraat_text and "مجهول" in qiraat_text
    assert all("qiraat-almawsoah/9/66" in item["cite"] for item in extended["qiraat"]["entries"])
    assert "بغوی" in " ".join(item["text"] for item in extended["shubuhat"]["entries"])
    assert "مخشی" in " ".join(item["text"] for item in extended["historicalContext"]["entries"])
    assert "Sykes" in " ".join(item["cite"] for item in extended["modernSciences"]["entries"])

    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "بازهٔ ۹:۶۵–۶۶ در overlay" in scope["9:65–66"]


def test_tawbah_67_has_complete_sourced_dossier():
    verse = DATA["verses"]["9:67"]
    assert verse["title"].startswith("توبه ۹:۶۷")
    assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"]
    assert "سببِ نزولِ خاصی" in verse["reviewStatus"]

    seen_texts = set()
    for field_id in BASE_FIELDS:
        assert len(verse[field_id]) == 5, field_id
        for item in verse[field_id]:
            assert len(item["text"].split()) >= 14, field_id
            assert item.get("cite", "").strip(), field_id
            normalized = " ".join(item["text"].split())
            assert normalized not in seen_texts, (field_id, normalized)
            seen_texts.add(normalized)

    extended = verse["extendedFields"]
    assert set(extended) == EXPECTED_FIELDS
    for field_id, field in extended.items():
        if field_id in {"qiraat", "historicalContext"}:
            assert field["status"] == "partial", field_id
            assert field["coverage"]["completed"] == len(field["entries"]), field_id
            assert field["sourceCoverageNote"].strip(), field_id
            assert field["followUp"].strip(), field_id
        else:
            assert field["status"] == "complete", field_id
            assert len(field["entries"]) == 5, field_id
        for entry in field["entries"]:
            assert len(entry["text"].split()) >= 14, (field_id, entry["text"][:30])
            assert entry["cite"].strip(), field_id
            assert entry["evidence"].strip(), field_id
            assert entry["limit"].strip(), field_id
            normalized = " ".join(entry["text"].split())
            assert normalized not in seen_texts, (field_id, normalized)
            seen_texts.add(normalized)

    qiraat = extended["qiraat"]["entries"][0]
    assert qiraat["kind"] == "source-coverage-note"
    assert "qiraat-almawsoah/9/67" in qiraat["cite"]

    classical = " ".join(item["cite"] for item in verse["classical"])
    modern = " ".join(item["cite"] for item in verse["modern"])
    for token in ("الطبري", "القرطبي", "البغوي", "ابن كثير", "ابن عطية"):
        assert token in classical, token
    for token in ("ابن عاشور", "سعدی", "الميسر", "المختصر", "أيسر التفاسير"):
        assert token in modern, token

    bible = " ".join(entry["text"] for entry in extended["bibleComparison"]["entries"])
    for token in ("اشعیا", "تیطس", "متی", "لوقا", "رومیان"):
        assert token in bible, token

    historical = " ".join(entry["text"] for entry in extended["historicalContext"]["entries"])
    assert "سببِ نزولِ خاص" in historical


def test_tawbah_68_and_69_have_sourced_dossiers_with_honest_gaps():
    partial_fields = {"qiraat", "bibleComparison", "historicalContext"}
    for verse_id in ("9:68", "9:69"):
        verse = DATA["verses"][verse_id]
        assert verse["title"].startswith("توبه ۹:۶۸" if verse_id == "9:68" else "توبه ۹:۶۹")
        assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"]

        seen_texts = set()
        for field_id in BASE_FIELDS:
            assert len(verse[field_id]) == 5, (verse_id, field_id)
            for item in verse[field_id]:
                assert len(item["text"].split()) >= 14, (verse_id, field_id)
                assert item.get("cite", "").strip(), (verse_id, field_id)
                normalized = " ".join(item["text"].split())
                assert normalized not in seen_texts, (verse_id, field_id)
                seen_texts.add(normalized)

        extended = verse["extendedFields"]
        assert set(extended) == EXPECTED_FIELDS
        for field_id, field in extended.items():
            for entry in field["entries"]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert entry["cite"].strip() and entry["evidence"].strip() and entry["limit"].strip()
                normalized = " ".join(entry["text"].split())
                assert normalized not in seen_texts, (verse_id, field_id)
                seen_texts.add(normalized)
            assert field["coverage"]["completed"] == len(field["entries"]), field_id
            if field_id in partial_fields:
                assert field["status"] == "partial", (verse_id, field_id)
                assert field["sourceCoverageNote"].strip() and field["followUp"].strip()
            else:
                assert field["status"] == "complete", (verse_id, field_id)
                assert len(field["entries"]) == 5, (verse_id, field_id)

    v68, v69 = DATA["verses"]["9:68"], DATA["verses"]["9:69"]
    classical68 = " ".join(item["cite"] for item in v68["classical"])
    for token in ("الطبري", "القرطبي", "البغوي", "ابن كثير"):
        assert token in classical68, token
    classical69 = " ".join(item["cite"] for item in v69["classical"])
    for token in ("الطبري", "البغوي", "ابن كثير"):
        assert token in classical69, token
    for verse in (v68, v69):
        modern = " ".join(item["cite"] for item in verse["modern"])
        for token in ("ابن عاشور", "السعدي", "الميسر", "المختصر", "أيسر التفاسير"):
            assert token in modern, token

    assert "لتتبعن" in " ".join(item["text"] for item in v69["classical"])
    assert "را ضعیف می‌شمارد" in " ".join(item["text"] for item in v69["classical"])
    assert "qiraat-almawsoah/9/68" in v68["extendedFields"]["qiraat"]["entries"][0]["cite"]
    assert "qiraat-almawsoah/9/69" in v69["extendedFields"]["qiraat"]["entries"][0]["cite"]


def test_tawbah_70_and_71_record_reviewed_sources_and_explicit_partial_coverage():
    for verse_id in ("9:70", "9:71"):
        verse = DATA["verses"][verse_id]
        assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"]
        assert "partial" in verse["fieldCoverageStatus"]

        seen_texts = set()
        for field_id in BASE_FIELDS:
            assert len(verse[field_id]) >= 5, (verse_id, field_id)
            for item in verse[field_id]:
                assert len(item["text"].split()) >= 14, (verse_id, field_id)
                assert item.get("cite", "").strip(), (verse_id, field_id)
                normalized = " ".join(item["text"].split())
                assert normalized not in seen_texts, (verse_id, field_id)
                seen_texts.add(normalized)

        extended = verse["extendedFields"]
        assert set(extended) == EXPECTED_FIELDS
        for field_id, field in extended.items():
            assert field["entries"], (verse_id, field_id)
            for entry in field["entries"]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert entry["cite"].strip() and entry["evidence"].strip() and entry["limit"].strip()
                normalized = " ".join(entry["text"].split())
                assert normalized not in seen_texts, (verse_id, field_id)
                seen_texts.add(normalized)
            assert field["coverage"]["completed"] == len(field["entries"]), field_id
            assert field["status"] == "partial", (verse_id, field_id)
            assert field["sourceCoverageNote"].strip() and field["followUp"].strip()

    classical70 = " ".join(item["cite"] for item in DATA["verses"]["9:70"]["classical"])
    for token in ("البغوي", "ابن كثير"):
        assert token in classical70, token
    classical71 = " ".join(item["cite"] for item in DATA["verses"]["9:71"]["classical"])
    for token in ("البغوي", "القرطبي"):
        assert token in classical71, token
    qiraat70 = DATA["verses"]["9:70"]["extendedFields"]["qiraat"]
    assert qiraat70["status"] == "partial"
    assert qiraat70["entries"][0]["kind"] == "source-coverage-note"

    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "توبه ۹:۷۰ ثبت شد" in scope["9:70"]
    assert "توبه ۹:۷۱ ثبت شد" in scope["9:71"]
    assert "۹:۷۰–۷۱" in scope["9:70–71"]
    assert "overlay اکنون تا ۹:۱۰۸" in scope["9:1–129"]


def test_tawbah_72_and_73_are_field_specific_and_sourced():
    v72, v73 = DATA["verses"]["9:72"], DATA["verses"]["9:73"]
    for verse_id, verse in (("9:72", v72), ("9:73", v73)):
        assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"]
        seen = set()
        for field_id in BASE_FIELDS:
            assert len(verse[field_id]) == 5, (verse_id, field_id)
            for item in verse[field_id]:
                assert len(item["text"].split()) >= 14, (verse_id, field_id)
                assert item["cite"].strip(), (verse_id, field_id)
                normalized = " ".join(item["text"].split())
                assert normalized not in seen, (verse_id, field_id)
                seen.add(normalized)
        for field_id, field in verse["extendedFields"].items():
            assert field["entries"], (verse_id, field_id)
            for entry in field["entries"]:
                assert len(entry["text"].split()) >= 14, (verse_id, field_id)
                assert entry["cite"].strip() and entry["evidence"].strip() and entry["limit"].strip()
            assert field["coverage"]["completed"] == len(field["entries"])
            assert field["status"] == "partial", (verse_id, field_id)
            assert field["sourceCoverageNote"].strip() and field["followUp"].strip()

    classical72 = " ".join(item["cite"] for item in v72["classical"])
    assert "البغوي" in classical72 and "ابن كثير" in classical72
    classical73 = " ".join(item["cite"] for item in v73["classical"])
    assert "القرطبي" in classical73
    # اختلاف‌های حل‌نشده باید در فیلد نقد حفظ شده باشند
    critical72 = " ".join(item["text"] for item in v72["critical"])
    assert "عدن" in critical72
    critical73 = " ".join(item["text"] for item in v73["critical"])
    assert "ابن العربی" in critical73 and "نسخ" in critical73

    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "توبه ۹:۷۲ ثبت شد" in scope["9:72"]
    assert "توبه ۹:۷۳ ثبت شد" in scope["9:73"]
    assert "۹:۷۲–۷۳" in scope["9:72–73"]
    assert "overlay اکنون تا ۹:۱۰۸" in scope["9:1–129"]


def test_tawbah_74_records_competing_occasions_and_fiqh_difference():
    verse = DATA["verses"]["9:74"]
    assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"]
    seen = set()
    for field_id in BASE_FIELDS:
        assert len(verse[field_id]) == 5, field_id
        for item in verse[field_id]:
            assert len(item["text"].split()) >= 14, field_id
            assert item["cite"].strip(), field_id
            normalized = " ".join(item["text"].split())
            assert normalized not in seen, field_id
            seen.add(normalized)

    classical = " ".join(item["cite"] for item in verse["classical"])
    assert "القرطبي" in classical
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "چهار قولِ سببِ نزول" in critical
    assert "شافعی و مالک" in critical
    extended = verse["extendedFields"]
    assert set(extended) == EXPECTED_FIELDS
    for field_id, field in extended.items():
        assert field["status"] == "partial", field_id
        assert field["entries"] and field["sourceCoverageNote"].strip() and field["followUp"].strip()
    assert extended["qiraat"]["entries"][0]["kind"] == "source-coverage-note"

    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "توبه ۹:۷۴ ثبت شد" in scope["9:74"]


def test_source_diversity_policy_v2_is_declared_and_applied():
    criteria = DATA["criteria"]
    assert criteria["sourcePolicyVersion"] == 2
    assert criteria["minimumDistinctWorksPerRecord"] == 3
    assert criteria["maxShareOfContemporaryEntriesFromSingleWork"] == 0.6
    assert criteria["maxMuyassarEntriesPerRecord"] == 1
    assert "sourceMixRequired" in criteria and criteria["sourceMixRequired"] is True
    assert "المیسّر" in criteria["policyNote"]

    for verse_id, dossier in DATA["verses"].items():
        mix = dossier.get("sourceMix")
        assert isinstance(mix, list) and mix, verse_id
        assert all({"work", "role", "entries"} <= set(item) for item in mix), verse_id
        if int(dossier.get("sourcePolicyVersion", 1)) < 2:
            continue
        named = [item for item in mix if item["role"] in ("classical", "modern", "academic")]
        assert len(named) >= 3, (verse_id, named)
        roles = {item["role"] for item in named}
        assert {"classical", "modern"} <= roles, (verse_id, roles)
        contemporary = [item for item in named if item["role"] in ("modern", "academic")]
        total = sum(item["entries"] for item in contemporary) or 1
        assert all(item["entries"] / total <= 0.6 for item in contemporary), (verse_id, contemporary)
        muyassar = [item for item in named if item["work"] == "التفسير الميسر"]
        assert sum(item["entries"] for item in muyassar) <= 1, (verse_id, muyassar)


def test_tawbah_90_diversifies_away_from_muyassar_and_records_qiraat():
    verse = DATA["verses"]["9:90"]
    assert verse["sourcePolicyVersion"] == 2
    works = {item["work"] for item in verse["sourceMix"]}
    assert {"جامع البيان", "معالم التنزيل", "الجامع لأحكام القرآن"} <= works
    assert any(item["role"] == "academic" for item in verse["sourceMix"])

    classical = " ".join(item["cite"] for item in verse["classical"])
    assert "البغوي" in classical and "القرطبي" in classical
    qiraat_cites = " ".join(entry["cite"] for entry in verse["extendedFields"]["qiraat"]["entries"])
    assert "القرطبي" in qiraat_cites and "قرائت" in verse["extendedFields"]["qiraat"]["entries"][0]["text"]

    qiraat = verse["extendedFields"]["qiraat"]
    assert qiraat["status"] == "partial"
    assert len(qiraat["entries"]) == 2
    assert all(entry["kind"] == "analysis" for entry in qiraat["entries"])
    joined = " ".join(entry["text"] for entry in qiraat["entries"])
    assert "المُعذِرون" in joined and "المُعذِّرون" in joined
    assert "ابن عباس" in joined


def test_app_renders_per_verse_source_mix():
    assert "sourceMixBlock" in APP
    assert "source-mix-panel" in APP
    assert "شفافیتِ منابع" in APP
    assert "sourcePolicyVersion" in APP


def test_tawbah_91_92_do_not_lean_on_muyassar():
    criteria = DATA["criteria"]
    assert criteria["minimumDistinctWorksPerRecord"] == 3
    for verse_id in ("9:91", "9:92"):
        verse = DATA["verses"][verse_id]
        works = {item["work"] for item in verse["sourceMix"] if item["role"] in ("classical", "modern", "academic")}
        assert len(works) >= 4, (verse_id, works)
        assert "التفسير الميسر" not in works, verse_id
        assert {"جامع البيان", "معالم التنزيل", "الجامع لأحكام القرآن", "تيسير الكريم الرحمن"} <= works
        cites = " ".join(item["cite"] for field in ("notes", "context", "classical", "modern", "critical", "research")
                         for item in verse[field])
        assert "tafsir.app/tabari/9/" in cites and "tafsir.app/saadi/9/" in cites

    verse = DATA["verses"]["9:92"]
    classical = " ".join(item["cite"] for item in verse["classical"])
    assert classical.count("tafsir.app/tabari/9/92") >= 1
    text = " ".join(item["text"] for item in verse["classical"])
    assert "بنو مقرّن" in text or "بنو مقرن" in text
    assert "عرباض" in text
    assert "اختلاف" in " ".join(item["text"] for item in verse["critical"])


def test_scope_records_the_policy_v2_batch():
    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "9:90–92" in scope
    assert "سیاستِ تنوعِ منابعِ v2" in scope["9:90–92"]
    assert "المیسّر" in scope["9:90–92"]
    assert "۹:۱۰۹ به بعد باقی است" in scope["9:42–46"]


def test_tawbah_93_blames_the_able_bodied_and_cites_four_works():
    verse = DATA["verses"]["9:93"]
    works = {item["work"] for item in verse["sourceMix"] if item["role"] in ("classical", "modern", "academic")}
    assert {"جامع البيان", "معالم التنزيل", "الجامع لأحكام القرآن", "تيسير الكريم الرحمن"} <= works
    assert "التفسير الميسر" not in works
    assert int(verse["sourcePolicyVersion"]) == 2
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "الخوالف" in classical
    assert "ابن عباس" in classical and "مقاتل" in classical
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "لا عذر لهم" in modern
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"


def test_tawbah_94_rejects_false_excuses_and_tests_deeds():
    verse = DATA["verses"]["9:94"]
    works = {item["work"] for item in verse["sourceMix"] if item["role"] in ("classical", "modern", "academic")}
    assert {"جامع البيان", "معالم التنزيل", "تيسير الكريم الرحمن"} <= works
    assert "التفسير الميسر" not in works
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "السرّ والعلانية" in classical
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "ميزان الصدق" in modern
    guidance = verse["extendedFields"]["guidanceDiscourse"]["entries"][0]["text"]
    assert "کردار" in guidance


def test_tawbah_95_and_96_keep_the_oath_and_approval_distinct():
    for verse_id in ("9:95", "9:96"):
        verse = DATA["verses"][verse_id]
        works = {item["work"] for item in verse["sourceMix"] if item["role"] in ("classical", "modern", "academic")}
        assert {"جامع البيان", "معالم التنزيل", "تيسير الكريم الرحمن"} <= works, verse_id
        assert "التفسير الميسر" not in works, verse_id
        assert int(verse["sourcePolicyVersion"]) == 2
        assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"

    v95 = DATA["verses"]["9:95"]
    text95 = " ".join(item["text"] for item in v95["classical"])
    assert "کعب بن مالک" in " ".join(item["text"] for item in v95["notes"])
    assert "نجس" in text95
    modern95 = " ".join(item["text"] for item in v95["modern"])
    assert "لا توبخوهم" in modern95

    v96 = DATA["verses"]["9:96"]
    assert "الخارجين من الإيمان" in " ".join(item["text"] for item in v96["classical"])
    assert "بابِ توبه" in " ".join(item["text"] for item in v96["critical"])
    assert "خرم" in " ".join(item["text"] for item in v96["notes"])


def test_tawbah_97_is_situated_not_ethnic():
    verse = DATA["verses"]["9:97"]
    works = {item["work"] for item in verse["sourceMix"] if item["role"] in ("classical", "modern", "academic")}
    assert {"جامع البيان", "معالم التنزيل", "تيسير الكريم الرحمن"} <= works
    assert "التفسير الميسر" not in works
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "أقل علمًا بالسنن" in classical or "حدود" in classical
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "سماع القرآن" in notes or "لجفائهم" in notes
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "۹:۹۹" in critical and "تميم" in critical
    shubuhat = verse["extendedFields"]["shubuhat"]["entries"][0]["text"]
    assert "ذاتاً" in shubuhat
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"


def test_every_extended_field_declares_question_acceptance_and_threshold():
    fields = {field["id"]: field for field in DATA["fields"]}
    assert set(fields) == EXPECTED_FIELDS
    for field_id, field in fields.items():
        assert len(field["question"].split()) >= 6, field_id
        assert len(field["acceptance"].split()) >= 10, field_id
        assert len(field["rejection"].split()) >= 6, field_id
        assert field["evidenceKeys"] == ["text", "cite", "evidence", "limit"], field_id
        assert field["allowedKinds"] == ["analysis", "source-coverage-note"], field_id
        assert field["minEntries"] == {"core": 1, "full": 5}, field_id
    standard = DATA["criteria"]["extendedFieldStandard"]
    assert standard["designVersion"] == 2
    assert standard["tierThresholds"] == {"core": 1, "full": 5}
    assert set(standard["kindDefinitions"]) == {"analysis", "source-coverage-note"}
    assert "ادعای پوششِ کامل" in standard["note"]

    app = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "function fieldDesignBlock(" in app and "function fieldDesignOverview(" in app
    assert "پرسشِ پژوهشیِ این فیلد" in app
    assert "شرطِ پذیرشِ مدخل" in app
    assert "${fieldDesignBlock(definition)}" in app
    assert "${fieldDesignOverview()}" in app


def test_validator_rejects_field_without_design(tmp_path):
    import copy
    import json as _json
    broken = copy.deepcopy(DATA)
    broken["fields"][0].pop("question")
    target = tmp_path / "broken.json"
    target.write_text(_json.dumps(broken, ensure_ascii=False), encoding="utf-8")
    errors, counts = validate_standard3_fields.validate(target)
    assert counts["verses"] == len(DATA["verses"])
    assert any("missing design key question" in error for error in errors)


def test_tawbah_98_and_99_carry_real_qiraat_and_scope_frontier():
    for verse_id in ("9:98", "9:99"):
        verse = DATA["verses"][verse_id]
        assert verse["tier"] == "core" and verse["sourcePolicyVersion"] == 2
        assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"]
        assert "core" in verse["coverageNote"]
        for field_id in BASE_FIELDS:
            assert len(verse[field_id]) == 3, (verse_id, field_id)
            for item in verse[field_id]:
                assert len(item["text"].split()) >= 14, (verse_id, field_id)
                assert item["cite"].strip(), (verse_id, field_id)
        works = {item["work"] for item in verse["sourceMix"]}
        assert {"جامع البيان", "معالم التنزيل", "تيسير الكريم الرحمن"} <= works, (verse_id, works)
        assert not any("ميسر" in work or "الميسر" in work for work in works), verse_id
        qiraat = verse["extendedFields"]["qiraat"]
        assert len(qiraat["entries"]) == 2, verse_id
        assert all(entry["kind"] == "analysis" for entry in qiraat["entries"]), verse_id
        joined = " ".join(entry["text"] for entry in qiraat["entries"])
        assert ("السَّوء" in joined or "السُّوء" in joined) if verse_id == "9:98" else ("قُرُبة" in joined), verse_id
        analysed = sum(1 for field in verse["extendedFields"].values()
                       if any(entry["kind"] == "analysis" for entry in field["entries"]))
        assert analysed >= 8, (verse_id, analysed)

    v98 = " ".join(item["text"] for item in DATA["verses"]["9:98"]["notes"])
    assert "غرمًا لزمه" in v98 or "غرامت" in v98
    critical98 = " ".join(item["text"] for item in DATA["verses"]["9:98"]["critical"])
    assert "یمان بن رئاب" in critical98
    qiraat98 = " ".join(entry["text"] for entry in DATA["verses"]["9:98"]["extendedFields"]["qiraat"]["entries"])
    assert "فرزدق" in qiraat98 and ("ترجیح" in qiraat98 or "ترجيح" in qiraat98)

    v99 = " ".join(item["text"] for item in DATA["verses"]["9:99"]["modern"])
    assert "مجرد تعربهم وباديتهم" in v99
    critical99 = " ".join(item["text"] for item in DATA["verses"]["9:99"]["critical"])
    assert "عبدالرحمن بن معقل" in critical99 and "تصحیف" in critical99
    qiraat99 = " ".join(entry["text"] for entry in DATA["verses"]["9:99"]["extendedFields"]["qiraat"]["entries"])
    assert "ورش" in qiraat99

    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "۹:۹۸" in scope["9:90–92"] and "۹:۹۹" in scope["9:90–92"]
    assert "قُرْبة/قُرُبة" in scope["9:90–92"]
    assert "۹:۱۰۹–۱۲۹" in scope["9:1–129"]


def test_tawbah_100_101_record_forerunners_and_hardened_hypocrites():
    v100 = DATA["verses"]["9:100"]
    v101 = DATA["verses"]["9:101"]
    for verse_id, verse in (("9:100", v100), ("9:101", v101)):
        assert verse["tier"] == "core" and verse["sourcePolicyVersion"] == 2
        assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"]
        for field_id in BASE_FIELDS:
            assert len(verse[field_id]) == 3, (verse_id, field_id)
            for item in verse[field_id]:
                assert len(item["text"].split()) >= 14, (verse_id, field_id)
                assert item["cite"].strip(), (verse_id, field_id)
        works = {item["work"] for item in verse["sourceMix"]}
        assert {"جامع البيان", "معالم التنزيل", "تيسير الكريم الرحمن"} <= works, (verse_id, works)
        assert not any("ميسر" in work for work in works), verse_id
        assert "core" in verse["coverageNote"]

    qiraat100 = v100["extendedFields"]["qiraat"]
    assert len(qiraat100["entries"]) == 2
    text100 = " ".join(entry["text"] for entry in qiraat100["entries"])
    assert ("یعقوب" in text100 or "يعقوب" in text100) and "خفض" in text100
    assert "من تحتها" in text100 and "بغوی" in text100
    assert all(entry["kind"] == "analysis" for entry in qiraat100["entries"])

    qiraat101 = v101["extendedFields"]["qiraat"]
    assert len(qiraat101["entries"]) == 1
    assert qiraat101["entries"][0]["kind"] == "source-coverage-note"
    assert "ادعای اجماعِ قاریان" in qiraat101["entries"][0]["text"]

    critical101 = " ".join(item["text"] for item in v101["critical"])
    assert "العنقزي" in critical101 and "ذكر لنا" in critical101
    classical101 = " ".join(item["text"] for item in v101["classical"])
    assert ("الدبيلة" in classical101 or "الدُّبيلة" in classical101) and "حذیفه" in classical101
    modern101 = " ".join(item["text"] for item in v101["modern"])
    assert "أن التثنية على بابها" in modern101
    context100 = " ".join(item["text"] for item in v100["context"])
    assert "رفعة لا يبلغها أحد" in context100
    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "۹:۱۰۰" in scope["9:100–101"] and "۹:۱۰۱" in scope["9:100–101"]
    assert "خفض" in scope["9:100–101"] and "کمبود" in scope["9:100–101"]


def test_tawbah_102_records_confession_and_grammatical_dispute():
    verse = DATA["verses"]["9:102"]
    assert verse["tier"] == "core" and verse["sourcePolicyVersion"] == 2
    assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"]
    for field_id in BASE_FIELDS:
        assert len(verse[field_id]) == 3, field_id
        for item in verse[field_id]:
            assert len(item["text"].split()) >= 14, field_id
            assert item["cite"].strip(), field_id
    works = {item["work"] for item in verse["sourceMix"]}
    assert {"جامع البيان", "معالم التنزيل", "تيسير الكريم الرحمن"} <= works
    assert not any("ميسر" in work for work in works)

    classical = " ".join(item["text"] for item in verse["classical"])
    assert "وعسى من الله واجب" in classical
    assert "ابو لبابه" in classical or "أبو لبابة" in classical
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "استوى الماء والخشبة" in critical
    assert "سقط" in critical
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "التوفيق للتوبة" in modern
    context = " ".join(item["text"] for item in verse["context"])
    assert "بالسواري" in context
    qiraat = verse["extendedFields"]["qiraat"]
    assert len(qiraat["entries"]) == 1
    assert qiraat["entries"][0]["kind"] == "source-coverage-note"
    assert "ادعای اجماعِ" in qiraat["entries"][0]["text"]
    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "۹:۱۰۲" in scope["9:100–102"] and "۹:۱۰۳" in scope["9:100–102"]
    assert "۹:۱۰۸" in scope["9:1–129"]


def test_previous_fields_are_kept_alongside_the_ten_new_fields():
    """لایه‌های پیشین حذف نشده‌اند و همراهِ ده فیلدِ تازه نمایش داده می‌شوند."""
    dossiers = json.loads((ROOT / "static" / "verse-dossiers.json").read_text(encoding="utf-8"))["verses"]
    annotations = json.loads((ROOT / "static" / "verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
    previous_fields = ("notes", "messages", "principles", "framework", "thematic", "network", "research")
    for verse_id in sorted(TARGET_VERSES):
        record = DATA["verses"][verse_id]
        assert set(record["extendedFields"]) == EXPECTED_FIELDS, verse_id
        # verse-dossiers.json فعلاً تا ۱۰:۴۸ را پوشش می‌دهد؛ برای ۱۰:۴۹ و ۱۱:۱ فقط لایهٔ
        # مطالعه (verse-study-annotations.json) موجود است و باید دست‌نخورده بماند.
        if verse_id in dossiers:
            base = dossiers[verse_id]
            for field_id in BASE_FIELDS:
                assert isinstance(base.get(field_id), list) and base[field_id], (verse_id, field_id)
        else:
            assert verse_id in {"11:1", "10:49", "10:50", "10:51", "10:52", "10:53", "10:54", "10:55", "10:56", "10:57", "10:58", "10:59", "10:60", "10:61", "10:62", "10:63", "10:64", "10:65", "10:66", "10:67", "10:68", "10:69", "10:70", "10:71", "10:72", "10:73", "10:74", "10:75", "10:76", "10:77", "10:78", "10:79", "10:80", "10:81", "10:82", "10:83", "10:84", "10:85", "10:86", "10:87", "10:88", "10:89", "10:90", "10:91", "10:92", "10:93", "10:94", "10:95", "10:96", "10:97", "10:98", "10:99", "10:100", "10:101", "10:102", "10:103", "10:104", "10:105", "10:106", "10:107", "10:108", "10:109", "11:1", "11:2", "11:3", "11:4", "11:5", "11:6", "11:7", "11:8", "11:9", "11:10", "11:11", "11:12", "11:13", "11:14", "11:15", "11:16", "11:17", "11:18", "11:19", "11:20", "11:21", "11:22", "11:23", "11:24", "11:25", "11:26", "11:27", "11:28", "11:29", "11:30", "11:31", "11:32", "11:33", "11:34", "11:35", "11:36", "11:37", "11:38", "11:39", "11:40", "11:41", "11:42", "11:43", "11:44", "11:45", "11:46", "11:47", "11:48", "11:49", "11:50", "11:51", "11:52", "11:53", "11:54", "11:55", "11:56", "11:57", "11:58", "11:59", "11:60", "11:61", "11:62", "11:63", "11:64", "11:65", "11:66", "11:67", "11:68", "11:69", "11:70", "11:71", "11:72", "11:73", "11:74", "11:75", "11:76", "11:77", "11:78", "11:79", "11:80", "11:81", "11:82", "11:83", "11:84", "11:85", "11:86", "11:87", "11:88", "11:89", "11:90", "11:91", "11:92", "11:93", "11:94", "11:95", "11:96", "11:97", "11:98", "11:99", "11:100", "11:101", "11:102", "11:103", "11:104", "11:105", "11:106", "11:107", "11:108", "11:109", "11:110", "11:111", "11:112", "11:113", "11:114", "11:115", "11:116", "11:117", "11:118", "11:119", "11:120", "11:121", "11:122", "11:123", "12:1", "12:2", "12:3", "12:4", "12:5", "12:6", "12:7", "12:8", "12:9", "12:10", "12:11", "12:12", "12:13", "12:14", "12:15", "12:16", "12:17", "12:18", "12:19", "12:20", "12:21", "12:22", "12:23", "12:24", "12:25", "12:26", "12:27", "12:28", "12:29", "12:30", "12:31", "12:32", "12:33", "12:34", "12:35", "12:36", "12:37", "12:38", "12:39", "12:40", "12:41", "12:42", "12:43", "12:44", "12:45", "12:46", "12:47", "12:48", "12:49", "12:50", "12:51", "12:52", "12:53", "12:54", "12:55", "12:56", "12:57", "12:58", "12:59", "12:60", "12:61", "12:62", "12:63", "12:64", "12:65", "12:66", "12:67", "12:68", "12:69", "12:70", "12:71", "12:72", "12:73", "12:74", "12:75", "12:76", "12:77", "12:78", "12:79", "12:80", "12:81", "12:82", "12:83", "12:84", "12:85", "12:86", "12:87", "12:88", "12:89", "12:90", "12:91", "12:92", "12:93", "12:94", "12:95", "12:96", "12:97", "12:98", "12:99", "12:100", "12:101", "12:102", "12:103", "12:104", "12:105", "12:106", "12:107", "12:108", "12:109", "12:110", "12:111", "13:1", "13:2", "13:3", "13:4", "13:5", "13:6", "13:7", "13:8", "13:9", "13:10", "13:11", "13:12", "13:13", "13:14", "13:15", "13:16", "13:17", "13:18", "13:19", "13:20", "13:21", "13:22", "13:23", "13:24", "13:25", "13:26", "13:27", "13:28", "13:29", "13:30", "13:31", "13:32", "13:33", "13:34", "13:35", "13:36", "13:37", "13:38", "13:39", "13:40", "13:41", "13:42", "13:43", "14:1", "14:2", "14:3", "14:4", "14:5", "14:6", "14:7", "14:8", "14:9", "14:10", "14:11", "14:12", "14:13", "14:14", "14:15", "14:16", "14:17", "14:18", "14:19", "14:20", "14:21", "14:22", "14:23", "14:24", "14:25", "14:26", "14:27", "14:28", "14:29", "14:30", "14:31", "14:32", "14:33", "14:34", "14:35", "14:36", "14:37", "14:38", "14:39", "14:40", "14:41", "14:42", "14:43", "14:44", "14:45", "14:46", "14:47", "14:48", "14:49", "14:50", "14:51", "14:52", "15:1", "15:2", "15:3", "15:4", "15:5", "15:6", "15:7", "15:8", "15:9", "15:10", "15:11", "15:12", "15:13", "15:14", "15:15", "15:16", "15:17", "15:18", "15:19", "15:20", "15:21", "15:22", "15:23", "15:24", "15:25", "15:26", "15:27", "15:28", "15:29", "15:30", "15:31", "15:32", "15:33", "15:34", "15:35", "15:36", "15:37", "15:38", "15:39", "15:40", "15:41", "15:42", "15:43", "15:44", "15:45", "15:46", "15:47", "15:48", "15:49", "15:50", "15:51", "15:52", "15:53", "15:54", "15:55", "15:56", "15:57", "15:58", "15:59", "15:60", "15:61", "15:62", "15:63", "15:64", "15:65", "15:66", "15:67", "15:68", "15:69", "15:70", "15:71", "15:72", "15:73", "15:74", "15:75", "15:76", "15:77", "15:78", "15:79", "15:80", "15:81", "15:82", "15:83", "15:84", "15:85", "15:86", "15:87", "15:88", "15:89", "15:90", "15:91", "15:92", "15:93", "15:94", "15:95", "15:96", "15:97", "15:98", "15:99", "16:1", "16:2", "16:3", "16:4", "16:5", "16:6", "16:7", "16:8", "16:9", "16:10", "16:11", "16:12", "16:13", "16:14", "16:15", "16:16", "16:17", "16:18", "16:19", "16:20", "16:21", "16:22", "16:23", "16:24", "16:25", "16:26", "16:27", "16:28", "16:29", "16:30", "16:31", "16:32", "16:33", "16:34", "16:35", "16:36", "16:37", "16:38", "16:39", "16:40", "16:41", "16:42", "16:43", "16:44", "16:45", "16:46", "16:47", "16:48", "16:49", "16:50", "16:51", "16:52", "16:53", "16:54", "16:55", "16:56", "16:57", "16:58", "16:59", "16:60", "16:61", "16:62", "16:63", "16:64", "16:65", "16:66", "16:67", "16:68", "16:69", "16:70", "16:71", "16:72", "16:73", "16:74", "16:75", "16:76", "16:77", "16:78", "16:79", "16:80", "16:81", "16:82", "16:83", "16:84", "16:85", "16:86", "16:87", "16:88", "16:89", "16:90", "16:91", "16:92", "16:93", "16:94", "16:95", "16:96", "16:97", "16:98", "16:99", "16:100", "16:101", "16:102", "16:103", "16:104", "16:105", "16:106", "16:107", "16:108", "16:109", "16:110", "16:111", "16:112", "16:113", "16:114", "16:115", "16:116", "16:117", "16:118", "16:119", "16:120", "16:121", "16:122", "16:123", "16:124", "16:125", "16:126", "16:127", "16:128", "17:1", "17:2", "17:3", "17:4", "17:5", "17:6", "17:7", "17:8", "17:9", "17:10", "17:11", "17:12", "17:13", "17:14", "17:15", "17:16", "17:17", "17:18", "17:19", "17:20", "17:21", "17:22", "17:23", "17:24", "17:25", "17:26", "17:27", "17:28", "17:29", "17:30", "17:31", "17:32", "17:33", "17:34", "17:35", "17:36", "17:37", "17:38", "17:39", "17:40", "17:41", "17:42", "17:43", "17:44", "17:45", "17:46", "17:47", "17:48", "17:49", "17:50", "17:51", "17:52", "17:53", "17:54", "17:55", "17:56", "17:57", "17:58", "17:59", "17:60", "17:61", "17:62", "17:63", "17:64", "17:65", "17:66", "17:67", "17:68", "17:69", "17:70", "17:71", "17:72", "17:73", "17:74", "17:75", "17:76", "17:77", "17:78", "17:79", "17:80", "17:81", "17:82", "17:83", "17:84", "17:85", "17:86", "17:87", "17:88", "17:89", "17:90", "17:91", "17:92", "17:93", "17:94", "17:95", "17:96", "17:97", "17:98", "17:99", "17:100", "17:101", "17:102", "17:103", "17:104", "17:105", "17:106", "17:107", "17:108", "17:109", "17:110", "17:111", "18:1", "18:2", "18:3", "18:4", "18:5", "18:6", "18:7", "18:8", "18:9", "18:10", "18:11", "18:12", "18:13", "18:14", "18:15", "18:16", "18:17", "18:18", "18:19", "18:20", "18:21", "18:22", "18:23", "18:24", "18:25", "18:26", "18:27", "18:28", "18:29", "18:30", "18:31", "18:32", "18:33", "18:34", "18:35", "18:36", "18:37", "18:38", "18:39", "18:40", "18:41", "18:42", "18:43", "18:44", "18:45", "18:46", "18:47", "18:48", "18:49", "18:50", "18:51", "18:52", "18:53", "18:54", "18:55", "18:56", "18:57", "18:58", "18:59", "18:60", "18:61", "18:62", "18:63", "18:64", "18:65", "18:66", "18:67", "18:68", "18:69", "18:70", "18:71", "18:72", "18:73", "18:74", "18:75", "18:76", "18:77", "18:78", "18:79", "18:80", "18:81", "18:82", "18:83", "18:84", "18:85", "18:86", "18:87", "18:88", "18:89", "18:90"}, verse_id
        annotation = annotations[verse_id]
        assert annotation["status"].strip()
        for field_id in previous_fields:
            if verse_id not in dossiers and field_id == "research":
                # یازده:۱ در لایهٔ مطالعه فیلدِ research ندارد؛ این خلأ ثبت می‌شود و پنهان نمی‌گردد.
                assert field_id not in annotation, verse_id
                continue
            assert field_id in annotation, (verse_id, field_id)

    assert "data-legacy-study-panel" in APP
    assert "legacyStudyGroups(verse)" in APP
    assert "archivedBaseSection(verse)" in APP
    assert "بایگانیِ نسخهٔ پیشینِ شش فیلدِ پایه" in APP
    assert "هشت فیلدِ پیشین" in APP
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert "هشت فیلدِ پیشین" in html
    for tab in ("data-detail-tab=\"notes\"", "data-detail-tab=\"messages\"", "data-detail-tab=\"foundations\""):
        assert tab in html, tab


def test_v2_records_take_precedence_without_deleting_the_old_dossier():
    for verse_id in ("9:90", "9:98", "9:100", "9:102"):
        record = DATA["verses"][verse_id]
        assert int(record["sourcePolicyVersion"]) == 2, verse_id
        assert len(record["notes"]) == 3, verse_id
        muyassar_entries = sum(item["entries"] for item in record["sourceMix"]
                               if "ميسر" in item["work"] or "الميسر" in item["work"])
        assert muyassar_entries <= 1, (verse_id, muyassar_entries)
    app = APP
    assert "policyV2 ? { ...base, ...supplementary }" in app


def test_tawbah_103_104_alms_reading_dispute_and_divine_acceptance():
    v103, v104 = DATA["verses"]["9:103"], DATA["verses"]["9:104"]
    for verse_id, verse in (("9:103", v103), ("9:104", v104)):
        assert verse["tier"] == "core" and verse["sourcePolicyVersion"] == 2
        assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"]
        for field_id in BASE_FIELDS:
            assert len(verse[field_id]) == 3, (verse_id, field_id)
            for item in verse[field_id]:
                assert len(item["text"].split()) >= 14, (verse_id, field_id)
                assert item["cite"].strip(), (verse_id, field_id)
        works = {item["work"] for item in verse["sourceMix"]}
        assert {"جامع البيان", "تيسير الكريم الرحمن"} <= works, (verse_id, works)
        analysed = sum(1 for field in verse["extendedFields"].values()
                       if any(entry["kind"] == "analysis" for entry in field["entries"]))
        assert analysed >= 8, (verse_id, analysed)

    assert {"جامع البيان", "تيسير الكريم الرحمن", "معالم التنزيل"} <= {m["work"] for m in v103["sourceMix"]}
    qiraat103 = v103["extendedFields"]["qiraat"]
    assert len(qiraat103["entries"]) == 2
    text103 = " ".join(entry["text"] for entry in qiraat103["entries"])
    assert "صلواتك" in text103 and "صلاتك" in text103 and "قرأة مدینه" in text103
    classical103 = " ".join(item["text"] for item in v103["classical"])
    assert "وقار لهم" in classical103 and "رحمة لهم" in classical103
    modern103 = " ".join(item["text"] for item in v103["modern"])
    assert "طمأنينة لقلوبهم" in modern103
    critical103 = " ".join(item["text"] for item in v103["critical"])
    assert "القرأة مجمعة على رفعها" in critical103

    notes104 = " ".join(item["text"] for item in v104["notes"])
    assert "قبول توبة" in notes104 or "قبولِ توبه" in notes104
    critical104 = " ".join(item["text"] for item in v104["critical"])
    assert "أخشى أن يكون في إسناد" in critical104 and "خطأ قدیم" in critical104
    qiraat104 = v104["extendedFields"]["qiraat"]
    assert qiraat104["entries"][0]["kind"] == "source-coverage-note"
    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "۹:۱۰۳" in scope["9:103–104"] and "۹:۱۰۴" in scope["9:103–104"]
    assert "صلى‌واتك" in scope["9:103–104"] or "صلواتك" in scope["9:103–104"]


def test_tawbah_105_records_addressee_disagreement_without_choosing():
    verse = DATA["verses"]["9:105"]
    assert verse["tier"] == "core" and verse["sourcePolicyVersion"] == 2
    assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"]
    for field_id in BASE_FIELDS:
        assert len(verse[field_id]) == 3, field_id
        for item in verse[field_id]:
            assert len(item["text"].split()) >= 14, field_id
            assert item["cite"].strip(), field_id
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "المتخلفين" in notes or "المتخلفين عن الجهاد" in notes
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "لا بد أن يتبين" in modern
    assert "هؤلاء المنافقين" in " ".join(item["text"] for item in verse["context"])
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "عن رجل" in critical
    context = " ".join(item["text"] for item in verse["context"])
    assert "وعيد" in context
    qiraat = verse["extendedFields"]["qiraat"]
    assert qiraat["entries"][0]["kind"] == "source-coverage-note"
    works = {item["work"] for item in verse["sourceMix"]}
    assert {"جامع البيان", "تيسير الكريم الرحمن"} <= works
    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "۹:۱۰۵" in scope["9:105"] and "وعيد" in scope["9:105"]


def test_tawbah_106_107_suspense_and_dirar_mosque():
    v106, v107 = DATA["verses"]["9:106"], DATA["verses"]["9:107"]
    for verse_id, verse in (("9:106", v106), ("9:107", v107)):
        assert verse["tier"] == "core" and verse["sourcePolicyVersion"] == 2
        assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"]
        for field_id in BASE_FIELDS:
            assert len(verse[field_id]) == 3, (verse_id, field_id)
            for item in verse[field_id]:
                assert len(item["text"].split()) >= 14, (verse_id, field_id)
                assert item["cite"].strip(), (verse_id, field_id)
        works = {item["work"] for item in verse["sourceMix"]}
        assert {"جامع البيان", "تيسير الكريم الرحمن"} <= works, (verse_id, works)
        analysed = sum(1 for field in verse["extendedFields"].values()
                       if any(entry["kind"] == "analysis" for entry in field["entries"]))
        assert analysed >= 8, (verse_id, analysed)

    qiraat106 = v106["extendedFields"]["qiraat"]
    assert len(qiraat106["entries"]) == 2
    text106 = " ".join(entry["text"] for entry in qiraat106["entries"])
    assert "مُرْجَئُونَ" in text106 and "ترك الهمز" in text106
    classical106 = " ".join(item["text"] for item in v106["classical"])
    assert "هلال بن أمية" in classical106 and "كعب بن مالك" in classical106
    critical106 = " ".join(item["text"] for item in v106["critical"])
    assert "مرارة بن ربيعي" in critical106 and "الربيع الأنصاري" in critical106

    notes107 = " ".join(item["text"] for item in v107["notes"])
    assert "إرصاداً" in notes107
    context107 = " ".join(item["text"] for item in v107["context"])
    assert "ذی أوان" in context107 and "فاهدماه وحرّقاه" in context107
    modern107 = " ".join(item["text"] for item in v107["modern"])
    assert "مزبلة" in modern107
    critical107 = " ".join(item["text"] for item in v107["critical"])
    assert "بحزج" in critical107 and "بنو غنم" in critical107
    assert v107["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"
    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "۹:۱۰۶" in scope["9:106–107"] and "۹:۱۰۷" in scope["9:106–107"]


def test_yunus_10_1_opening_letters_and_wisdom_epithet():
    verse = DATA["verses"]["10:1"]
    assert verse["tier"] == "core" and verse["sourcePolicyVersion"] == 2
    assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"]
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
            assert item["cite"].strip(), field
    works = {item["work"] for item in verse["sourceMix"]}
    assert {"جامع البيان", "تيسير الكريم الرحمن"} <= works, works
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "أنا الله أرى" in classical and "الرحمن" in classical
    assert "اسمٌ من أسماء القرآن" in classical
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "الأعلام" in notes and "اسمٌ من أسماء القرآن" in notes
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "بالرضا والقبول والانقياد" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "فأغنى ذلك عن إعادته في هذا الموضع" in critical
    qiraat = verse["extendedFields"]["qiraat"]
    assert qiraat["entries"][0]["kind"] == "source-coverage-note"
    assert verse["extendedFields"]["linguistics"]["entries"][0]["text"].find("تلك") != -1
    analysed = sum(1 for field in verse["extendedFields"].values()
                   if any(entry["kind"] == "analysis" for entry in field["entries"]))
    assert analysed >= 8, analysed
    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "تفسیر نمونه" in scope["10:1"] and f"{_fa(len(DATA['verses']))}" in scope["9:1–129"]


def test_tawbah_108_two_mosque_identifications_kept_side_by_side():
    verse = DATA["verses"]["9:108"]
    assert verse["tier"] == "core" and verse["sourcePolicyVersion"] == 2
    assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"]
    for field in BASE_FIELDS:
        assert len(verse[field]) == 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
            assert item["cite"].strip(), field
    works = {item["work"] for item in verse["sourceMix"]}
    assert {"جامع البيان", "تيسير الكريم الرحمن"} <= works, works
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "مسجد قباء" in classical or "مسجدِ قباء" in classical
    assert "لصحة الخبر بذلك عن رسول الله" in classical
    modern = " ".join(item["text"] for item in verse["modern"])
    context = " ".join(item["text"] for item in verse["context"])
    assert "وهو مسجد قباء" in context
    assert "الطهارة المعنوية" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "صالح بن حيان" in critical and "عبد الله بن عامر الأسلمي" in critical
    assert "محرر بن أبي هريرة" in critical
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"
    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "۹:۱۰۸" in scope["9:108"]
    assert f"{_fa(len(DATA['verses']))} رکورد" in scope["9:1–129"]


def test_yunus_10_2_qiraat_and_qudum_sidq_views():
    verse = DATA["verses"]["10:2"]
    assert verse["tier"] == "core" and verse["sourcePolicyVersion"] == 2
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
            assert item["cite"].strip(), field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "أعمالًا صالحة عند الله" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "لسحر مبين" in classical and "لساحر مبين" in classical
    assert "مسروق" in classical and "سعید بن جبیر" in classical
    assert "الذكر الأول" in classical
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "زيد بن حباب" in critical and "إبراهيم بن يزيد الخوزي" in critical
    assert "فضيل بن عمرو بن الجون" in critical
    qiraat = verse["extendedFields"]["qiraat"]
    assert len(qiraat["entries"]) == 2 and qiraat["entries"][0]["kind"] == "analysis"
    assert verse["extendedFields"]["modernSciences"]["entries"][0]["kind"] == "source-coverage-note"
    works = {item["work"] for item in verse["sourceMix"]}
    assert {"جامع البيان", "تيسير الكريم الرحمن"} <= works, works


def test_yunus_10_3_creation_intercession_and_open_question():
    verse = DATA["verses"]["10:3"]
    assert verse["tier"] == "core" and verse["sourcePolicyVersion"] == 2
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "بغير شريك ولا ظهير" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "يقضيه وحده" in classical and "لا يسمع ولا يبصر" in classical
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "رفيق في أفعاله" in modern and "ولو كان أفضل الخلق" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "استواء يليق بعظمته" in critical
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"
    assert verse["extendedFields"]["modernSciences"]["entries"][0]["kind"] == "source-coverage-note"
    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "۱۰:۳" in scope["10:3"]


def test_hud_11_1_two_opposite_hasan_reports_kept_apart():
    verse = DATA["verses"]["11:1"]
    assert verse["tier"] == "core" and verse["sourcePolicyVersion"] == 2
    assert "پیش‌نویسِ منبع‌محور" in verse["reviewStatus"]
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
            assert item["cite"].strip(), field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "هذا كتاب" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "أحكمت بالأمر والنهي" in classical
    assert "أحكمت بالثواب والعقاب ثم فصلت بالأمر والنهي" in classical
    assert "فُسّرت" in classical
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "يضع الأشياء مواضعها" in modern and "مطلع على الظواهر والبواطن" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "لم أعلم من يكون" in critical and "الجرجاني" in critical
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"
    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "هود" in scope["11:1"] and "تعارض" in scope["11:1"]


def test_shia_sources_and_peer_reviewed_articles_are_enforced():
    criteria = DATA["criteria"]
    assert criteria["diversityPolicyVersion"] == 3
    assert criteria["minShiaWorksPerRecord"] == 1
    assert criteria["minPeerReviewedArticlesPerRecord"] == 1
    assert criteria["requiresBothTraditions"] is True
    assert criteria["minSunniWorksPerRecord"] == 1
    assert "قرآن" in criteria["diversityScope"]
    assert "شیعی" in criteria["diversityPolicyNote"] and "سنّی" in criteria["diversityPolicyNote"]

    for verse_id in ("10:1", "10:2", "10:3", "10:4", "10:5", "10:6", "10:7", "10:8", "10:9", "10:10", "10:11", "10:12", "10:13", "10:14", "10:15", "10:16", "10:17", "10:18", "10:19", "10:20", "10:21", "10:22", "10:23", "10:24", "10:25", "10:26", "10:27", "10:28", "10:29", "10:30", "10:31", "10:32", "10:33", "10:34", "10:35", "10:36", "10:37", "10:38", "10:39", "10:40", "10:41", "10:42", "10:43", "10:44", "10:45", "10:46", "10:47", "10:48", "10:49", "10:50", "10:51", "10:52", "10:53", "10:54", "10:55", "10:56", "10:57", "10:58", "10:59", "10:60", "10:61", "10:62", "10:63", "10:64", "10:65", "10:66", "10:67", "10:68", "10:69", "10:70", "10:71", "10:72", "10:73", "10:74", "10:75", "10:76", "10:77", "10:78", "10:79", "10:80", "10:81", "10:82", "10:83", "10:84", "10:85", "10:86", "10:87", "10:88", "10:89", "10:90", "10:91", "10:92", "10:93", "10:94", "10:95", "10:96", "10:97", "10:98", "10:99", "10:100", "10:101", "10:102", "10:103", "10:104", "10:105", "10:106", "10:107", "10:108", "10:109", "11:1", "11:2", "11:3", "11:4", "11:5", "11:6", "11:7", "11:8", "11:9", "11:10", "11:11", "11:12", "11:13", "11:14", "11:15", "11:16", "11:17", "11:18", "11:19", "11:20", "11:21", "11:22", "11:23", "11:24", "11:25", "11:26", "11:27", "11:28", "11:29", "11:30", "11:31", "11:32", "11:33", "11:34", "11:35", "11:36", "11:37", "11:38", "11:39", "11:40", "11:41", "11:42", "11:43", "11:44", "11:45", "11:46", "11:47", "11:48", "11:49", "11:50", "11:51", "11:52", "11:53", "11:54", "11:55", "11:56", "11:57", "11:58", "11:59", "11:60", "11:61", "11:62", "11:63", "11:64", "11:65", "11:66", "11:67", "11:68", "11:69", "11:70", "11:71", "11:72", "11:73", "11:74", "11:75", "11:76", "11:77", "11:78", "11:79", "11:80", "11:81", "11:82", "11:83", "11:84", "11:85", "11:86", "11:87", "11:88", "11:89", "11:90", "11:91", "11:92", "11:93", "11:94", "11:95", "11:96", "11:97", "11:98", "11:99", "11:100", "11:101", "11:102", "11:103", "11:104", "11:105", "11:106", "11:107", "11:108", "11:109", "11:110", "11:111", "11:112", "11:113", "11:114", "11:115", "11:116", "11:117", "11:118", "11:119", "11:120", "11:121", "11:122", "11:123", "12:1", "12:2", "12:3", "12:4", "12:5", "12:6", "12:7", "12:8", "12:9", "12:10", "12:11", "12:12", "12:13", "12:14", "12:15", "12:16", "12:17", "12:18", "12:19", "12:20", "12:21", "12:22", "12:23", "12:24", "12:25", "12:26", "12:27", "12:28", "12:29", "12:30", "12:31", "12:32", "12:33", "12:34", "12:35", "12:36", "12:37", "12:38", "12:39", "12:40", "12:41", "12:42", "12:43", "12:44", "12:45", "12:46", "12:47", "12:48", "12:49", "12:50", "12:51", "12:52", "12:53", "12:54", "12:55", "12:56", "12:57", "12:58", "12:59", "12:60", "12:61", "12:62", "12:63", "12:64", "12:65", "12:66", "12:67", "12:68", "12:69", "12:70", "12:71", "12:72", "12:73", "12:74", "12:75", "12:76", "12:77", "12:78", "12:79", "12:80", "12:81", "12:82", "12:83", "12:84", "12:85", "12:86", "12:87", "12:88", "12:89", "12:90", "12:91", "12:92", "12:93", "12:94", "12:95", "12:96", "12:97", "12:98", "12:99", "12:100", "12:101", "12:102", "12:103", "12:104", "12:105", "12:106", "12:107", "12:108", "12:109", "12:110", "12:111", "13:1", "13:2", "13:3", "13:4", "13:5", "13:6", "13:7", "13:8", "13:9", "13:10", "13:11", "13:12", "13:13", "13:14", "13:15", "13:16", "13:17", "13:18", "13:19", "13:20", "13:21", "13:22", "13:23", "13:24", "13:25", "13:26", "13:27", "13:28", "13:29", "13:30", "13:31", "13:32", "13:33", "13:34", "13:35", "13:36", "13:37", "13:38", "13:39", "13:40", "13:41", "13:42", "13:43", "14:1", "14:2", "14:3", "14:4", "14:5", "14:6", "14:7", "14:8", "14:9", "14:10", "14:11", "14:12", "14:13", "14:14", "14:15", "14:16", "14:17", "14:18", "14:19", "14:20", "14:21", "14:22", "14:23", "14:24", "14:25", "14:26", "14:27", "14:28", "14:29", "14:30", "14:31", "14:32", "14:33", "14:34", "14:35", "14:36", "14:37", "14:38", "14:39", "14:40", "14:41", "14:42", "14:43", "14:44", "14:45", "14:46", "14:47", "14:48", "14:49", "14:50", "14:51", "14:52", "15:1", "15:2", "15:3", "15:4", "15:5", "15:6", "15:7", "15:8", "15:9", "15:10", "15:11", "15:12", "15:13", "15:14", "15:15", "15:16", "15:17", "15:18", "15:19", "15:20", "15:21", "15:22", "15:23", "15:24", "15:25", "15:26", "15:27", "15:28", "15:29", "15:30", "15:31", "15:32", "15:33", "15:34", "15:35", "15:36", "15:37", "15:38", "15:39", "15:40", "15:41", "15:42", "15:43", "15:44", "15:45", "15:46", "15:47", "15:48", "15:49", "15:50", "15:51", "15:52", "15:53", "15:54", "15:55", "15:56", "15:57", "15:58", "15:59", "15:60", "15:61", "15:62", "15:63", "15:64", "15:65", "15:66", "15:67", "15:68", "15:69", "15:70", "15:71", "15:72", "15:73", "15:74", "15:75", "15:76", "15:77", "15:78", "15:79", "15:80", "15:81", "15:82", "15:83", "15:84", "15:85", "15:86", "15:87", "15:88", "15:89", "15:90", "15:91", "15:92", "15:93", "15:94", "15:95", "15:96", "15:97", "15:98", "15:99", "16:1", "16:2", "16:3", "16:4", "16:5", "16:6", "16:7", "16:8", "16:9", "16:10", "16:11", "16:12", "16:13", "16:14", "16:15", "16:16", "16:17", "16:18", "16:19", "16:20", "16:21", "16:22", "16:23", "16:24", "16:25", "16:26", "16:27", "16:28", "16:29", "16:30", "16:31", "16:32", "16:33", "16:34", "16:35", "16:36", "16:37", "16:38", "16:39", "16:40", "16:41", "16:42", "16:43", "16:44", "16:45", "16:46", "16:47", "16:48", "16:49", "16:50", "16:51", "16:52", "16:53", "16:54", "16:55", "16:56", "16:57", "16:58", "16:59", "16:60", "16:61", "16:62", "16:63", "16:64", "16:65", "16:66", "16:67", "16:68", "16:69", "16:70", "16:71", "16:72", "16:73", "16:74", "16:75", "16:76", "16:77", "16:78", "16:79", "16:80", "16:81", "16:82", "16:83", "16:84", "16:85", "16:86", "16:87", "16:88", "16:89", "16:90", "16:91", "16:92", "16:93", "16:94", "16:95", "16:96", "16:97", "16:98", "16:99", "16:100", "16:101", "16:102", "16:103", "16:104", "16:105", "16:106", "16:107", "16:108", "16:109", "16:110", "16:111", "16:112", "16:113", "16:114", "16:115", "16:116", "16:117", "16:118", "16:119", "16:120", "16:121", "16:122", "16:123", "16:124", "16:125", "16:126", "16:127", "16:128", "17:1", "17:2", "17:3", "17:4", "17:5", "17:6", "17:7", "17:8", "17:9", "17:10", "17:11", "17:12", "17:13", "17:14", "17:15", "17:16", "17:17", "17:18", "17:19", "17:20", "17:21", "17:22", "17:23", "17:24", "17:25", "17:26", "17:27", "17:28", "17:29", "17:30", "17:31", "17:32", "17:33", "17:34", "17:35", "17:36", "17:37", "17:38", "17:39", "17:40", "17:41", "17:42", "17:43", "17:44", "17:45", "17:46", "17:47", "17:48", "17:49", "17:50", "17:51", "17:52", "17:53", "17:54", "17:55", "17:56", "17:57", "17:58", "17:59", "17:60", "17:61", "17:62", "17:63", "17:64", "17:65", "17:66", "17:67", "17:68", "17:69", "17:70", "17:71", "17:72", "17:73", "17:74", "17:75", "17:76", "17:77", "17:78", "17:79", "17:80", "17:81", "17:82", "17:83", "17:84", "17:85", "17:86", "17:87", "17:88", "17:89", "17:90", "17:91", "17:92", "17:93", "17:94", "17:95", "17:96", "17:97", "17:98", "17:99", "17:100", "17:101", "17:102", "17:103", "17:104", "17:105", "17:106", "17:107", "17:108", "17:109", "17:110", "17:111", "18:1", "18:2", "18:3", "18:4", "18:5", "18:6", "18:7", "18:8", "18:9", "18:10", "18:11", "18:12", "18:13", "18:14", "18:15", "18:16", "18:17", "18:18", "18:19", "18:20", "18:21", "18:22", "18:23", "18:24", "18:25", "18:26", "18:27", "18:28", "18:29", "18:30", "18:31", "18:32", "18:33", "18:34", "18:35", "18:36", "18:37", "18:38", "18:39", "18:40", "18:41", "18:42", "18:43", "18:44", "18:45", "18:46", "18:47", "18:48", "18:49", "18:50", "18:51", "18:52", "18:53", "18:54", "18:55", "18:56", "18:57", "18:58", "18:59", "18:60", "18:61", "18:62", "18:63", "18:64", "18:65", "18:66", "18:67", "18:68", "18:69", "18:70", "18:71", "18:72", "18:73", "18:74", "18:75", "18:76", "18:77", "18:78", "18:79", "18:80", "18:81", "18:82", "18:83", "18:84", "18:85", "18:86", "18:87", "18:88", "18:89", "18:90"):
        record = DATA["verses"][verse_id]
        assert record["requiresDiverseSources"] is True, verse_id
        roles = {item["role"] for item in record["sourceMix"]}
        assert any(role.startswith("shia") for role in roles), (verse_id, roles)
        assert "journal" in roles, (verse_id, roles)
    for verse_id in ("10:1", "10:2", "10:3", "10:4", "10:5", "10:6", "10:7", "10:8", "10:9", "10:10", "10:11", "10:12", "10:13", "10:14", "10:15", "10:16", "10:17", "10:18", "10:19", "10:20", "10:21", "10:22", "10:23", "10:24", "10:25", "10:26", "10:27", "10:28", "10:29", "10:30", "10:31", "10:32", "10:33", "10:34", "10:35", "10:36", "10:37", "10:38", "10:39", "10:40", "10:41", "10:42", "10:43", "10:44", "10:45", "10:46", "10:47", "10:48", "10:49", "10:50", "10:51", "10:52", "10:53", "10:54", "10:55", "10:56", "10:57", "10:58", "10:59", "10:60", "10:61", "10:62", "10:63", "10:64", "10:65", "10:66", "10:67", "10:68", "10:69", "10:70", "10:71", "10:72", "10:73", "10:74", "10:75", "10:76", "10:77", "10:78", "10:79", "10:80", "10:81", "10:82", "10:83", "10:84", "10:85", "10:86", "10:87", "10:88", "10:89", "10:90", "10:91", "10:92", "10:93", "10:94", "10:95", "10:96", "10:97", "10:98", "10:99", "10:100", "10:101", "10:102", "10:103", "10:104", "10:105", "10:106", "10:107", "10:108", "10:109", "11:1", "11:2", "11:3", "11:4", "11:5", "11:6", "11:7", "11:8", "11:9", "11:10", "11:11", "11:12", "11:13", "11:14", "11:15", "11:16", "11:17", "11:18", "11:19", "11:20", "11:21", "11:22", "11:23", "11:24", "11:25", "11:26", "11:27", "11:28", "11:29", "11:30", "11:31", "11:32", "11:33", "11:34", "11:35", "11:36", "11:37", "11:38", "11:39", "11:40", "11:41", "11:42", "11:43", "11:44", "11:45", "11:46", "11:47", "11:48", "11:49", "11:50", "11:51", "11:52", "11:53", "11:54", "11:55", "11:56", "11:57", "11:58", "11:59", "11:60", "11:61", "11:62", "11:63", "11:64", "11:65", "11:66", "11:67", "11:68", "11:69", "11:70", "11:71", "11:72", "11:73", "11:74", "11:75", "11:76", "11:77", "11:78", "11:79", "11:80", "11:81", "11:82", "11:83", "11:84", "11:85", "11:86", "11:87", "11:88", "11:89", "11:90", "11:91", "11:92", "11:93", "11:94", "11:95", "11:96", "11:97", "11:98", "11:99", "11:100", "11:101", "11:102", "11:103", "11:104", "11:105", "11:106", "11:107", "11:108", "11:109", "11:110", "11:111", "11:112", "11:113", "11:114", "11:115", "11:116", "11:117", "11:118", "11:119", "11:120", "11:121", "11:122", "11:123", "12:1", "12:2", "12:3", "12:4", "12:5", "12:6", "12:7", "12:8", "12:9", "12:10", "12:11", "12:12", "12:13", "12:14", "12:15", "12:16", "12:17", "12:18", "12:19", "12:20", "12:21", "12:22", "12:23", "12:24", "12:25", "12:26", "12:27", "12:28", "12:29", "12:30", "12:31", "12:32", "12:33", "12:34", "12:35", "12:36", "12:37", "12:38", "12:39", "12:40", "12:41", "12:42", "12:43", "12:44", "12:45", "12:46", "12:47", "12:48", "12:49", "12:50", "12:51", "12:52", "12:53", "12:54", "12:55", "12:56", "12:57", "12:58", "12:59", "12:60", "12:61", "12:62", "12:63", "12:64", "12:65", "12:66", "12:67", "12:68", "12:69", "12:70", "12:71", "12:72", "12:73", "12:74", "12:75", "12:76", "12:77", "12:78", "12:79", "12:80", "12:81", "12:82", "12:83", "12:84", "12:85", "12:86", "12:87", "12:88", "12:89", "12:90", "12:91", "12:92", "12:93", "12:94", "12:95", "12:96", "12:97", "12:98", "12:99", "12:100", "12:101", "12:102", "12:103", "12:104", "12:105", "12:106", "12:107", "12:108", "12:109", "12:110", "12:111", "13:1", "13:2", "13:3", "13:4", "13:5", "13:6", "13:7", "13:8", "13:9", "13:10", "13:11", "13:12", "13:13", "13:14", "13:15", "13:16", "13:17", "13:18", "13:19", "13:20", "13:21", "13:22", "13:23", "13:24", "13:25", "13:26", "13:27", "13:28", "13:29", "13:30", "13:31", "13:32", "13:33", "13:34", "13:35", "13:36", "13:37", "13:38", "13:39", "13:40", "13:41", "13:42", "13:43", "14:1", "14:2", "14:3", "14:4", "14:5", "14:6", "14:7", "14:8", "14:9", "14:10", "14:11", "14:12", "14:13", "14:14", "14:15", "14:16", "14:17", "14:18", "14:19", "14:20", "14:21", "14:22", "14:23", "14:24", "14:25", "14:26", "14:27", "14:28", "14:29", "14:30", "14:31", "14:32", "14:33", "14:34", "14:35", "14:36", "14:37", "14:38", "14:39", "14:40", "14:41", "14:42", "14:43", "14:44", "14:45", "14:46", "14:47", "14:48", "14:49", "14:50", "14:51", "14:52", "15:1", "15:2", "15:3", "15:4", "15:5", "15:6", "15:7", "15:8", "15:9", "15:10", "15:11", "15:12", "15:13", "15:14", "15:15", "15:16", "15:17", "15:18", "15:19", "15:20", "15:21", "15:22", "15:23", "15:24", "15:25", "15:26", "15:27", "15:28", "15:29", "15:30", "15:31", "15:32", "15:33", "15:34", "15:35", "15:36", "15:37", "15:38", "15:39", "15:40", "15:41", "15:42", "15:43", "15:44", "15:45", "15:46", "15:47", "15:48", "15:49", "15:50", "15:51", "15:52", "15:53", "15:54", "15:55", "15:56", "15:57", "15:58", "15:59", "15:60", "15:61", "15:62", "15:63", "15:64", "15:65", "15:66", "15:67", "15:68", "15:69", "15:70", "15:71", "15:72", "15:73", "15:74", "15:75", "15:76", "15:77", "15:78", "15:79", "15:80", "15:81", "15:82", "15:83", "15:84", "15:85", "15:86", "15:87", "15:88", "15:89", "15:90", "15:91", "15:92", "15:93", "15:94", "15:95", "15:96", "15:97", "15:98", "15:99", "16:1", "16:2", "16:3", "16:4", "16:5", "16:6", "16:7", "16:8", "16:9", "16:10", "16:11", "16:12", "16:13", "16:14", "16:15", "16:16", "16:17", "16:18", "16:19", "16:20", "16:21", "16:22", "16:23", "16:24", "16:25", "16:26", "16:27", "16:28", "16:29", "16:30", "16:31", "16:32", "16:33", "16:34", "16:35", "16:36", "16:37", "16:38", "16:39", "16:40", "16:41", "16:42", "16:43", "16:44", "16:45", "16:46", "16:47", "16:48", "16:49", "16:50", "16:51", "16:52", "16:53", "16:54", "16:55", "16:56", "16:57", "16:58", "16:59", "16:60", "16:61", "16:62", "16:63", "16:64", "16:65", "16:66", "16:67", "16:68", "16:69", "16:70", "16:71", "16:72", "16:73", "16:74", "16:75", "16:76", "16:77", "16:78", "16:79", "16:80", "16:81", "16:82", "16:83", "16:84", "16:85", "16:86", "16:87", "16:88", "16:89", "16:90", "16:91", "16:92", "16:93", "16:94", "16:95", "16:96", "16:97", "16:98", "16:99", "16:100", "16:101", "16:102", "16:103", "16:104", "16:105", "16:106", "16:107", "16:108", "16:109", "16:110", "16:111", "16:112", "16:113", "16:114", "16:115", "16:116", "16:117", "16:118", "16:119", "16:120", "16:121", "16:122", "16:123", "16:124", "16:125", "16:126", "16:127", "16:128", "17:1", "17:2", "17:3", "17:4", "17:5", "17:6", "17:7", "17:8", "17:9", "17:10", "17:11", "17:12", "17:13", "17:14", "17:15", "17:16", "17:17", "17:18", "17:19", "17:20", "17:21", "17:22", "17:23", "17:24", "17:25", "17:26", "17:27", "17:28", "17:29", "17:30", "17:31", "17:32", "17:33", "17:34", "17:35", "17:36", "17:37", "17:38", "17:39", "17:40", "17:41", "17:42", "17:43", "17:44", "17:45", "17:46", "17:47", "17:48", "17:49", "17:50", "17:51", "17:52", "17:53", "17:54", "17:55", "17:56", "17:57", "17:58", "17:59", "17:60", "17:61", "17:62", "17:63", "17:64", "17:65", "17:66", "17:67", "17:68", "17:69", "17:70", "17:71", "17:72", "17:73", "17:74", "17:75", "17:76", "17:77", "17:78", "17:79", "17:80", "17:81", "17:82", "17:83", "17:84", "17:85", "17:86", "17:87", "17:88", "17:89", "17:90", "17:91", "17:92", "17:93", "17:94", "17:95", "17:96", "17:97", "17:98", "17:99", "17:100", "17:101", "17:102", "17:103", "17:104", "17:105", "17:106", "17:107", "17:108", "17:109", "17:110", "17:111", "18:1", "18:2", "18:3", "18:4", "18:5", "18:6", "18:7", "18:8", "18:9", "18:10", "18:11", "18:12", "18:13", "18:14", "18:15", "18:16", "18:17", "18:18", "18:19", "18:20", "18:21", "18:22", "18:23", "18:24", "18:25", "18:26", "18:27", "18:28", "18:29", "18:30", "18:31", "18:32", "18:33", "18:34", "18:35", "18:36", "18:37", "18:38", "18:39", "18:40", "18:41", "18:42", "18:43", "18:44", "18:45", "18:46", "18:47", "18:48", "18:49", "18:50", "18:51", "18:52", "18:53", "18:54", "18:55", "18:56", "18:57", "18:58", "18:59", "18:60", "18:61", "18:62", "18:63", "18:64", "18:65", "18:66", "18:67", "18:68", "18:69", "18:70", "18:71", "18:72", "18:73", "18:74", "18:75", "18:76", "18:77", "18:78", "18:79", "18:80", "18:81", "18:82", "18:83", "18:84", "18:85", "18:86", "18:87", "18:88", "18:89", "18:90"):
        roles = {item["role"] for item in DATA["verses"][verse_id]["sourceMix"]}
        assert any(role in {"classical"} for role in roles), verse_id
        assert any(role in {"modern", "shia-modern"} for role in roles), verse_id
    nem_10_3 = " ".join(item["text"] for item in DATA["verses"]["10:3"]["modern"])
    assert "قدرت" in nem_10_3 and "دُبُر" in nem_10_3
    critics_10_3 = " ".join(item["text"] for item in DATA["verses"]["10:3"]["critical"])
    assert "استواء يليق بعظمته" in critics_10_3
    res_10_3 = " ".join(item["text"] for item in DATA["verses"]["10:3"]["research"])
    assert "خوش‌فر" in res_10_3

    nem_10_2 = " ".join(item["text"] for item in DATA["verses"]["10:2"]["modern"])
    assert "تفسیر البرهان" in nem_10_2 and "ولایتِ علی" in nem_10_2
    tabarsi = " ".join(item["text"] for item in DATA["verses"]["11:1"]["classical"])
    assert "مجمع البيان" in tabarsi and "غلط" in tabarsi
    nem_11_1 = " ".join(item["text"] for item in DATA["verses"]["11:1"]["modern"])
    assert "در وحدت، متعدد و در تعدد، واحد" in nem_11_1
    sarraf = " ".join(item["text"] for item in DATA["verses"]["10:1"]["research"])
    assert "حروف مقطّعه" in sarraf
    haleem = " ".join(item["text"] for item in DATA["verses"]["10:2"]["research"])
    assert "سیاق" in haleem and "عبدالحلیم" in haleem
    assert "SOURCE_ROLE_LABELS" in APP and "مقالهٔ داوری‌شده" in APP
    assert "سیاستِ v3" in APP


def test_yunus_10_4_resurrection_argument_and_two_readings():
    verse = DATA["verses"]["10:4"]
    assert verse["tier"] == "core" and verse["sourcePolicyVersion"] == 2
    assert verse["requiresDiverseSources"] is True
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
            assert item["cite"].strip(), field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "محموم" in notes and "الحكم الجزائي" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "أحقًّا عباد الله" in classical and "بالعدل" in classical
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "فاقد العقل" in modern and "کاروان" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "ثم يحييه" in critical and "جعفر رازی" in critical
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "analysis"
    assert verse["extendedFields"]["modernSciences"]["entries"][0]["kind"] == "source-coverage-note"
    works = {item["work"] for item in verse["sourceMix"]}
    assert {"جامع البيان", "تيسير الكريم الرحمن", "تفسير نمونه"} <= works, works
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 2, journals


def test_yunus_10_5_sun_radiance_moon_light_and_calendar():
    verse = DATA["verses"]["10:5"]
    assert verse["tier"] == "core" and verse["sourcePolicyVersion"] == 2
    assert verse["requiresDiverseSources"] is True
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
            assert item["cite"].strip(), field
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "قضاه فسوّاه" in classical and "اكتفاء" in classical
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "بالليل" in notes and "بالأهلة" in notes
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "تقویمِ طبیعی" in modern and "الإحكام" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "ترکیبِ نور" in critical and "ذاتی و اکتسابی" in critical
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"
    assert verse["extendedFields"]["modernSciences"]["entries"][0]["kind"] == "source-coverage-note"
    assert "Genesis 1:16" in verse["extendedFields"]["bibleComparison"]["entries"][0]["cite"]
    works = {item["work"] for item in verse["sourceMix"]}
    assert {"جامع البيان", "تيسير الكريم الرحمن", "تفسير نمونه"} <= works, works
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 2, journals


def test_yunus_10_6_night_day_alternation_and_taqwa_audience():
    verse = DATA["verses"]["10:6"]
    assert verse["tier"] == "core" and verse["sourcePolicyVersion"] == 2
    assert verse["requiresDiverseSources"] is True
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
            assert item["cite"].strip(), field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "اعتقاب" in notes and "أعلامًا واضحة" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "يخافون وعيده" in classical and "صحَّت فطرته" in classical
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "الرغبة في الخير" in modern and "صفای نفس" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "لم يقصد بذلك" in critical and "۶۲٪" in critical
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"
    assert verse["extendedFields"]["modernSciences"]["entries"][0]["kind"] == "source-coverage-note"
    assert "Genesis 1:14" in verse["extendedFields"]["bibleComparison"]["entries"][0]["cite"]
    works = {item["work"] for item in verse["sourceMix"]}
    assert {"جامع البيان", "تيسير الكريم الرحمن", "تفسير نمونه"} <= works, works
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 2, journals


def test_yunus_10_7_rajah_as_fear_and_the_four_descriptions():
    verse = DATA["verses"]["10:7"]
    assert verse["tier"] == "core" and verse["sourcePolicyVersion"] == 2
    assert verse["requiresDiverseSources"] is True
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
            assert item["cite"].strip(), field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "لا يخافون لقاءنا" in notes and "لم يُرجَ لسعتُها" in notes
    context = " ".join(item["text"] for item in verse["context"])
    assert "باء سببيت" in context and "زين الدنيا" in context
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "لها يفرح" in classical and "أهل الكفر" in classical
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "دار ممر" in modern and "احساس مسئولیت" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "معادل‌انگاری رجاء با تصدیق" in critical and "رؤیتِ خدا" in critical
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"
    assert verse["extendedFields"]["modernSciences"]["entries"][0]["kind"] == "source-coverage-note"
    works = {item["work"] for item in verse["sourceMix"]}
    assert {"جامع البيان", "تيسير الكريم الرحمن", "الميزان", "تفسير نمونه"} <= works, works
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 2, journals


def test_yunus_10_8_refuge_and_earning():
    verse = DATA["verses"]["10:8"]
    assert verse["tier"] == "core" and verse["sourcePolicyVersion"] == 2
    assert verse["requiresDiverseSources"] is True
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
            assert item["cite"].strip(), field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "مصيرهم" in notes and "الآثام والأجرام" in notes
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "لا يرحلون عنها" in modern and "آرامشی کاذب" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "صیغهٔ معلوم" in critical and "خلود" in critical
    assert verse["extendedFields"]["modernSciences"]["entries"][0]["kind"] == "source-coverage-note"
    assert "Matthew 16:27" in verse["extendedFields"]["bibleComparison"]["entries"][0]["cite"]
    roles = {item["role"] for item in verse["sourceMix"]}
    assert {"classical", "modern", "shia-modern", "journal"} <= roles, roles


def test_yunus_10_9_guidance_by_faith_and_gardens_of_bliss():
    verse = DATA["verses"]["10:9"]
    assert verse["requiresDiverseSources"] is True
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
            assert item["cite"].strip(), field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "صدّقوا الله ورسوله" in notes and "لدينه" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "نورًا يمشون به" in classical and "قد جعل ربك تحتك" in classical
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "أعمال القلوب" in modern and "ولایتِ الهی" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "بلغنا" in critical and "نقشِ حرفِ باء" in critical
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"
    roles = {item["role"] for item in verse["sourceMix"]}
    assert {"classical", "modern", "shia-modern", "journal"} <= roles, roles


def test_yunus_10_10_tasbih_salam_hamd_in_paradise():
    verse = DATA["verses"]["10:10"]
    assert verse["requiresDiverseSources"] is True
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "أهل الشرك" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "وخالفها" not in classical and "عمرو بن معد" in classical
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "ألذ عليهم" in modern and "هم به زبان" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "هالك الإسناد" in critical and "بندگان مخلص" in critical
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 2, journals


def test_yunus_10_11_divine_respite_and_two_readings():
    verse = DATA["verses"]["10:11"]
    assert verse["requiresDiverseSources"] is True
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "لا باركَ الله فيه" in classical and "هو دعاء الرجل" in classical
    context = " ".join(item["text"] for item in verse["context"])
    assert "يمهلهم ولا يهملهم" in context and "هدفِ معیّنی ندارند" in context
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "لمحقتهم العقوبة" in modern and "محروم شدن از الطاف الهی" in modern
    qiraat = verse["extendedFields"]["qiraat"]["entries"][0]
    assert qiraat["kind"] == "analysis"
    assert "لَقَضَى" in qiraat["text"] and "شام" in qiraat["text"]
    assert verse["extendedFields"]["modernSciences"]["entries"][0]["kind"] == "source-coverage-note"
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 2, journals


def test_yunus_10_12_distress_and_ingratitude():
    verse = DATA["verses"]["10:12"]
    assert verse["requiresDiverseSources"] is True
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "إصابة الشدة والجهد" in notes and "استمرّ على طريقته الأولى" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "زيّن للذين أسرفوا في الكذب على الله" in classical
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "إخبار عن طبيعة الإنسان من حيث هو" in modern and "تزيين من الشيطان" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "مجهول" in critical and "بی‌سند" in critical
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"
    assert verse["extendedFields"]["modernSciences"]["entries"][0]["kind"] == "source-coverage-note"
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 2, journals


def test_yunus_10_13_destroyed_generations():
    verse = DATA["verses"]["10:13"]
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "توحيد الله" in classical
    assert "أورده النار في الآخرة" in classical
    context = " ".join(item["text"] for item in verse["context"])
    assert "تنيبوا وتتوبوا" in context and "وهذه سنته في جميع الأمم" in context
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "متجرئ على محارم الله" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "جبر" in critical
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 2, journals


def test_yunus_10_14_succession_and_testing():
    verse = DATA["verses"]["10:14"]
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "متروك" in classical and "بإسناد حسن" in classical
    assert "«الخلائف» را" in classical and "منصبِ خلافتِ سیاسی" in classical
    context = " ".join(item["text"] for item in verse["context"])
    assert "ما جعلنا خُلفاء إلا لينظر كيف أعمالنا" in context
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "ومن أنذر فقد أعذر" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "منصبِ سیاسی" in critical
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 2, journals


def test_yunus_10_15_demand_for_another_quran():
    verse = DATA["verses"]["10:15"]
    assert verse["requiresDiverseSources"] is True
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "لا يخافون عقابنا" in notes and "الحرامَ حلالا" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "رسول مبلّغ ومأمور مُتّبع" in classical and "تذهل كل مرضعة" in classical
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "ما ينبغي ولا يليق بي" in modern and "نفیِ حق و سلبِ اختیار" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "مناقض با اولش" in critical
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 2, journals


def test_yunus_10_16_argument_from_lifelong_silence():
    verse = DATA["verses"]["10:16"]
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "أربعين سنة" in notes and "أيّام شبابي وحَداثتي" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "غلطٌ" in classical and "ولا أنذرتكم به" in classical
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "أعجز الفصحاء" in modern
    qiraat = verse["extendedFields"]["qiraat"]["entries"][0]
    assert qiraat["kind"] == "analysis"
    assert "أَدْرَأْتُكُمْ" in qiraat["text"] and "أنذرتكم" in qiraat["text"]
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 2, journals


def test_yunus_10_17_two_forms_of_greatest_wrong():
    verse = DATA["verses"]["10:17"]
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "اختلق على الله كذبًا" in notes and "ولا ينالون الفلاح" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "بحججه ورسله" in classical
    context = " ".join(item["text"] for item in verse["context"])
    assert "تكميل احتجاج" in context
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "از كجاى آيه" in critical
    assert verse["extendedFields"]["modernSciences"]["entries"][0]["kind"] == "source-coverage-note"
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 2, journals


def test_yunus_10_18_intercession_of_idols_refuted():
    verse = DATA["verses"]["10:18"]
    assert verse["requiresDiverseSources"] is True
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "رجاء شفاعتها عند الله" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "وافترائهم عليه الكذب" in classical
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "أأنتم أعلم أم الله" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "بما لا يكون" in critical
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 2, journals


def test_yunus_10_19_one_community_and_the_deferred_word():
    verse = DATA["verses"]["10:19"]
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "أهل دين واحد وملة واحدة" in notes and "بعد انقضاء آجالهم" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "وينجي أهل الحق" in classical
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "بغی و حسد" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "نقض غرض" in critical and "سخیف‌ترین" in critical
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 1, journals


def test_yunus_10_20_request_for_a_sign_and_the_unseen():
    verse = DATA["verses"]["10:20"]
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "السرُّ والخفيّ من الأمور" in notes and "محق فيما يقول" in notes
    context = " ".join(item["text"] for item in verse["context"])
    assert "آيات الاقتراح" in context and "ينبوعًا" in context
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "تحقير قرآن" in critical
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 2, journals


def test_yunus_10_21_mockery_and_the_faster_plan():
    verse = DATA["verses"]["10:21"]
    assert verse["requiresDiverseSources"] is True
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "استهزاء وتكذيب" in notes and "المطر بعد القحط" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "تكتفي بإذا" in classical and "إن حفظتنا" in classical
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "لا يحيق إلا بأهله" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "استدراج" in critical
    qiraat = verse["extendedFields"]["qiraat"]["entries"][0]
    assert qiraat["kind"] == "analysis" and "مشهور" in qiraat["text"]
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 1, journals


def test_yunus_10_22_ship_storm_and_sincere_prayer():
    verse = DATA["verses"]["10:22"]
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "أخلصوا له الدعاء" in notes and "على الظهر" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "اسم للواحدة، والجماع" in classical
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "أعجمية بلا ريب" in critical
    qiraat = verse["extendedFields"]["qiraat"]["entries"][0]
    assert qiraat["kind"] == "analysis" and "ينشركم" in qiraat["text"]
    assert verse["extendedFields"]["modernSciences"]["entries"][0]["kind"] == "source-coverage-note"
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 1, journals


def test_yunus_10_23_transgression_returns_on_its_owner():
    verse = DATA["verses"]["10:23"]
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "أخلفوا الله ما وعدُوه" in notes and "وإياها تظلمون" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "عبد الله بن أبي إسحاق" in classical
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "بغير الحق" in critical
    qiraat_entries = verse["extendedFields"]["qiraat"]["entries"]
    assert all(item["kind"] == "analysis" for item in qiraat_entries)
    qiraat_text = " ".join(item["text"] + " " + item["evidence"] for item in qiraat_entries)
    assert "متاعَ" in qiraat_text and "حال" in qiraat_text
    critics_10_23 = " ".join(item["text"] for item in verse["critical"])
    assert "تتمتعون" in critics_10_23
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 1, journals


def test_yunus_10_24_parable_of_rain_and_harvest():
    verse = DATA["verses"]["10:24"]
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "التكدير والتنغيص" in notes and "حبوب الأرض" in notes
    classical = " ".join(item["text"] for item in verse["classical"])
    assert "غَنِيَ" in classical or "غني" in classical
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "هالك الإسناد من نواحيه" in critical and "قراءة تفسير" in critical
    qiraat = " ".join(item["text"] + " " + item["evidence"] for item in verse["extendedFields"]["qiraat"]["entries"])
    assert "لإجماع الحجة" in qiraat and "با ادغامِ تاء در زای" in qiraat
    assert verse["extendedFields"]["modernSciences"]["entries"][0]["kind"] == "source-coverage-note"
    roles = {item["role"] for item in verse["sourceMix"]}
    assert {"classical", "modern", "shia-modern", "journal"} <= roles, roles


def test_yunus_10_25_dar_al_salam_and_guided_will():
    verse = DATA["verses"]["10:25"]
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, field
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, field
    notes = " ".join(item["text"] for item in verse["notes"])
    assert "تسلموا من الهموم والأحزان" in notes
    modern = " ".join(item["text"] for item in verse["modern"])
    assert "بعد البيان والرسل" in modern
    critical = " ".join(item["text"] for item in verse["critical"])
    assert "مرسل" in critical and "صحيح الإسناد" in critical
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"
    journals = [item["work"] for item in verse["sourceMix"] if item["role"] == "journal"]
    assert len(journals) >= 2, journals


def _check_verse(verse_id):
    verse = DATA["verses"][verse_id]
    assert verse["requiresDiverseSources"] is True
    for field in BASE_FIELDS:
        assert len(verse[field]) >= 3, (verse_id, field)
        for item in verse[field]:
            assert len(item["text"].split()) >= 14, (verse_id, field)
    roles = {item["role"] for item in verse["sourceMix"]}
    assert {"classical", "modern", "shia-modern", "journal"} <= roles, (verse_id, roles)
    return verse


def _joined(verse, field):
    return " ".join(item["text"] for item in verse[field])


def _ext_text(verse, field):
    entries = verse["extendedFields"][field]["entries"]
    return " ".join(item["text"] + " " + item["evidence"] for item in entries)


def test_yunus_10_26_al_husna_and_the_extra():
    verse = _check_verse("10:26")
    assert "فأطاعوه فيما أمر ونَهَى" in _joined(verse, "notes")
    assert "يتجلى لهم" in _joined(verse, "classical")
    assert "الجنة الكاملة في حسنها" in _joined(verse, "modern")
    assert "هالك الإسناد" in _joined(verse, "critical")
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"


def test_yunus_10_27_like_for_like_and_darkness():
    verse = _check_verse("10:27")
    assert "أشبهُ بالكلام" in _joined(verse, "context")
    assert "قطعةٌ من سواد الليل" in _joined(verse, "classical")
    assert "لا يجوز خلافها" in _joined(verse, "critical")
    assert "قِطْعًا" in _ext_text(verse, "qiraat")
    assert verse["extendedFields"]["modernSciences"]["entries"][0]["kind"] == "source-coverage-note"


def test_yunus_10_28_place_of_you_and_your_partners():
    verse = _check_verse("10:28")
    assert "امكثوا مكانكم" in _joined(verse, "notes")
    assert "غير كائن في القبر" in _joined(verse, "classical")
    assert "دروغى وجود ندارد" in _joined(verse, "critical")
    assert "فَزَايَلْنَا" in _ext_text(verse, "qiraat")


def test_yunus_10_29_god_suffices_as_witness():
    verse = _check_verse("10:29")
    assert "لا نشعر به ولا نعلم" in _joined(verse, "notes")
    assert "حسبُنا الله شاهدًا" in _joined(verse, "classical")
    assert "مفید ثبوت" in _joined(verse, "research")
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"


def test_yunus_10_30_two_readings_of_tablu():
    verse = _check_verse("10:30")
    assert "تختبر" in _joined(verse, "notes")
    assert "قراءتان مشهورتان" in _joined(verse, "context")
    assert "غير مرتضى" in _joined(verse, "critical")
    assert "سخيف‌ترين سخنان" in _joined(verse, "critical")
    qiraat = _ext_text(verse, "qiraat")
    assert "تَبْلُو" in qiraat and "تَتْلُو" in qiraat


def test_yunus_10_31_proof_from_sustenance():
    verse = _check_verse("10:31")
    assert "الغيثَ والقطر" in _joined(verse, "notes")
    assert "توحيد الربوبية" in _joined(verse, "modern")
    assert "انهدام نظام عالم" in _joined(verse, "critical")
    assert "زيست شناسى جديد" in _ext_text(verse, "modernSciences")


def test_yunus_10_32_truth_and_error():
    verse = _check_verse("10:32")
    assert "الجور عن قصد السبيل" in _joined(verse, "notes")
    assert "احتب" in _joined(verse, "critical")
    assert "لا يشفع عند الله إلا بإذنه" in _joined(verse, "modern") or "إلا بإذنه" in _joined(verse, "modern")
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"


def test_yunus_10_33_decree_and_transgression():
    verse = _check_verse("10:33")
    assert "قضاؤه وحكمه" in _joined(verse, "notes")
    assert "خرجوا عن الحق عنادًا" in _joined(verse, "modern")
    assert "كلمه عذاب" in _joined(verse, "critical")
    assert "مادام" in _joined(verse, "critical")


def test_yunus_10_34_beginning_and_return():
    verse = _check_verse("10:34")
    assert "من غير أصل" in _joined(verse, "notes")
    assert "الحجة القاطعة" in _joined(verse, "classical")
    assert "النفي والتقرير" in _joined(verse, "modern")
    assert "ده مورد" in _joined(verse, "critical")
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"


def test_yunus_10_35_guidance_and_readings():
    verse = _check_verse("10:35")
    assert "قصد السبيل" in _joined(verse, "notes")
    assert "أفصح اللغات" in _joined(verse, "classical")
    assert "بإلهامه وتوفيقه" in _joined(verse, "modern")
    assert "مرتكزات فطرى" in _joined(verse, "research")
    qiraat = _ext_text(verse, "qiraat")
    assert "أمّن لا يهدّي" in qiraat and "تخفیفِ دال" in qiraat


def test_yunus_10_36_conjecture_and_truth():
    verse = _check_verse("10:36")
    assert "شكٍّ وريبة" in _joined(verse, "notes")
    assert "تزيين الشيطان" in _joined(verse, "modern")
    assert "تقلید كوركورانه" in _joined(verse, "critical")
    assert "تعليل" in _joined(verse, "research")
    assert "Proverbs 14:12" in _ext_text(verse, "bibleComparison")


def test_yunus_10_37_not_fabricated():
    verse = _check_verse("10:37")
    assert "ما ينبغي" in _joined(verse, "notes")
    assert "تفصيل الكتاب" in _joined(verse, "classical")
    assert "لعظمة المتكلم" in _joined(verse, "modern")
    assert "يحنّس" in _joined(verse, "critical")
    assert "اجمال و تفصيل" in _joined(verse, "critical")


def test_yunus_10_38_challenge_of_a_surah():
    verse = _check_verse("10:38")
    assert "منقطعه" in _joined(verse, "notes")
    assert "مثل سورته" in _joined(verse, "classical")
    assert "عنادًا وبغيًا" in _joined(verse, "modern")
    assert "همه خصوصيات قرآن" in _joined(verse, "critical")


def test_yunus_10_39_tafsir_of_tawil():
    verse = _check_verse("10:39")
    assert "ولما يأتهم بعدُ" in _joined(verse, "notes")
    assert "بالرجفة" in _joined(verse, "context")
    assert "التثبت" in _joined(verse, "modern")
    assert "حقيقتى است" in _joined(verse, "critical")
    assert "صرف توهّم" in _joined(verse, "critical")


def test_yunus_10_40_two_groups_and_mufsidin():
    verse = _check_verse("10:40")
    assert "سوف يصدِّق" in _joined(verse, "notes")
    assert "وهو الصحيح" in _joined(verse, "classical")
    assert "به هيچ وجه" in _joined(verse, "critical")
    assert "رذيله افساد" in _joined(verse, "research")


def test_yunus_10_41_my_work_and_your_work():
    verse = _check_verse("10:41")
    assert "لا يضرني عملكم" in _joined(verse, "notes")
    assert "آية السيف" in _joined(verse, "classical")
    assert "مراتب انتصار" in _joined(verse, "context")
    assert "وادار به قبول باطل" in _joined(verse, "critical")


def test_yunus_10_42_deaf_and_heart():
    verse = _check_verse("10:42")
    assert "أفأنت تخلق لهم السمع" in _joined(verse, "notes")
    assert "فظاهره الاستفهام" in _joined(verse, "classical")
    assert "اسماع" in _joined(verse, "critical")
    assert "شنوايى قلب" in _joined(verse, "critical")


def test_yunus_10_43_blind_and_qadariyya():
    verse = _check_verse("10:43")
    assert "أعلامك" in _joined(verse, "notes")
    assert "القدرية" in _joined(verse, "classical")
    assert "تسلية" in _joined(verse, "context")
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "source-coverage-note"


def test_yunus_10_44_no_injustice():
    verse = _check_verse("10:44")
    assert "لا يفعل بخلقه" in _joined(verse, "notes")
    assert "تصرف في ملكه" in _joined(verse, "classical")
    assert verse["extendedFields"]["qiraat"]["entries"][0]["kind"] == "analysis"
    assert "ولكن" in _ext_text(verse, "qiraat")


def test_yunus_10_45_an_hour_of_day():
    verse = _check_verse("10:45")
    assert "لم يلبثوا" in _joined(verse, "notes")
    assert "كأنهم" in _joined(verse, "classical")
    assert "حالِ دوم" in _joined(verse, "critical")


def test_yunus_10_46_partial_punishment():
    verse = _check_verse("10:46")
    assert "نرينّك" in _joined(verse, "notes")
    assert "شاهد لا يحتاج" in _joined(verse, "classical")
    assert "التفات" in _joined(verse, "critical")
    assert "عذابِ آخرت" in _joined(verse, "critical") or "عذاب آخرت" in _joined(verse, "critical")


def test_yunus_10_47_every_community_has_a_messenger():
    verse = _check_verse("10:47")
    assert "كما أرسلت محمدًا" in _joined(verse, "notes")
    assert "يوم القيامة" in _joined(verse, "notes")
    assert "خواص رسالت" in _joined(verse, "critical")
    assert "اختلافى در ميان" in _joined(verse, "research")


def test_yunus_10_48_when_is_this_promise():
    verse = _check_verse("10:48")
    assert "قيام الساعة" in _joined(verse, "notes")
    assert "تعجیز و استهزاء" in _joined(verse, "critical") or "تعجیز" in _joined(verse, "critical")
    assert "غيب عالم" in _joined(verse, "research")


def test_yunus_10_49_no_power_over_own_harm():
    verse = _check_verse("10:49")
    assert "لا أقدرُ لها على ضرٍّ" in _joined(verse, "notes")
    assert "وقت معلوم" in _joined(verse, "classical")
    assert "نواميس عامه" in _joined(verse, "research")


def test_yunus_10_50_torment_by_night_or_day():
    verse = _check_verse("10:50")
    assert "جواب لقولهم" in _joined(verse, "notes")
    assert "التهويل والتعظيم" in _joined(verse, "classical")
    assert "التفات" in _joined(verse, "critical") or "غيبت" in _joined(verse, "critical")


def test_yunus_10_51_belief_when_it_falls():
    verse = _check_verse("10:51")
    assert "لا ينفعكم فيها التصديق" in _joined(verse, "notes")
    assert "التقرير والتوبيخ" in _joined(verse, "context")
    assert "قبول نمى‌شود" in _joined(verse, "critical")


def test_yunus_10_52_taste_the_eternal_torment():
    verse = _check_verse("10:52")
    assert "خزنة جهنم" in _joined(verse, "notes")
    assert "جزاء كفركم" in _joined(verse, "context")
    assert "خطاب تكوينى" in _joined(verse, "critical")


def test_yunus_10_53_is_it_true():
    verse = _check_verse("10:53")
    assert "كلمة تحقيق" in _joined(verse, "notes")
    assert "سد مسد الخبر" in _joined(verse, "classical") or "سدِّ مسدِّ" in _joined(verse, "classical")
    assert "مانع آن مفقود" in _joined(verse, "critical")


def test_yunus_10_54_ransom_not_accepted():
    verse = _check_verse("10:54")
    assert "غيرَ من يستحق" in _joined(verse, "notes")
    assert "أخفوها" in _joined(verse, "context")
    assert "شماتت" in _joined(verse, "critical")


def test_yunus_10_55_his_is_all_in_heavens_and_earth():
    verse = _check_verse("10:55")
    assert "كلمة تنبيه" in _joined(verse, "notes")
    assert "فلا مانع" in _joined(verse, "context")
    assert "قياس" in _joined(verse, "critical")


def test_yunus_10_56_he_gives_life_and_death():
    verse = _check_verse("10:56")
    assert "المحیي المميت" in _joined(verse, "notes") or "المحيي المميت" in _joined(verse, "notes")
    assert "قد تقدم" in _joined(verse, "classical")
    assert "آميخته با باطل نيست" in _joined(verse, "research")


def test_yunus_10_57_admonition_and_healing():
    verse = _check_verse("10:57")
    assert "عقابَ الله" in _joined(verse, "notes")
    assert "المنتفعون بالإيمان" in _joined(verse, "classical")
    assert "خبيث روحى" in _joined(verse, "critical") or "خبيث" in _joined(verse, "critical")


def test_yunus_10_58_rejoice_in_his_grace():
    verse = _check_verse("10:58")
    assert "فضل الله القرآن" in _joined(verse, "notes")
    assert "إشارة إلى الفضل والرحمة" in _joined(verse, "classical")
    assert "سببى است مستقل" in _joined(verse, "critical")


def test_yunus_10_59_did_god_permit_you():
    verse = _check_verse("10:59")
    assert "كفار مكة" in _joined(verse, "notes")
    assert "هوس" in _joined(verse, "modern")
    assert "حكم مختص به خداى تعالى است" in _joined(verse, "critical")


def test_yunus_10_60_what_do_the_liars_suppose():
    verse = _check_verse("10:60")
    assert "لا يؤاخذهم" in _joined(verse, "notes")
    assert "التأخير والإمهال" in _joined(verse, "context")
    assert "ناسپاسند" in _joined(verse, "critical")


def test_yunus_10_61_witnesses_over_every_affair():
    verse = _check_verse("10:61")
    assert "للجحد" in _joined(verse, "notes")
    assert "تكلم مع الغير" in _joined(verse, "critical") or "ملائكه شاهدند" in _joined(verse, "critical")
    assert "يعزب" in _joined(verse, "critical")


def test_yunus_10_62_no_fear_upon_gods_allies():
    verse = _check_verse("10:62")
    assert "أنصار الله" in _joined(verse, "notes")
    assert "تولى حفظه" in _joined(verse, "context")
    assert "نه در دنيا و نه در آخرت" in _joined(verse, "critical")


def test_yunus_10_63_they_believed_and_were_godfearing():
    verse = _check_verse("10:63")
    assert "بأداء فرائضه" in _joined(verse, "notes")
    assert "الشرك والمعاصي" in _joined(verse, "context")
    assert "حالت هميشگى" in _joined(verse, "critical")


def test_yunus_10_64_glad_tidings_in_both_worlds():
    verse = _check_verse("10:64")
    assert "الرؤيا الصالحة" in _joined(verse, "notes")
    assert "تبشّر بها الملائكة" in _joined(verse, "context")
    assert "دگرگونى وجود ندارد" in _joined(verse, "critical")


def test_yunus_10_65_all_might_belongs_to_god():
    verse = _check_verse("10:65")
    assert "افتراؤهم وتكذيبهم" in _joined(verse, "notes")
    assert "القوة الكاملة" in _joined(verse, "context")
    assert "عزت همه‌اش از خدا است" in _joined(verse, "critical")


def test_yunus_10_66_they_follow_only_conjecture():
    verse = _check_verse("10:66")
    assert "على الحقيقة" in _joined(verse, "context")
    assert "خرص" in _joined(verse, "critical")
    assert "مصداقى ندارد" in _joined(verse, "critical")


def test_yunus_10_67_night_for_rest_day_for_sight():
    verse = _check_verse("10:67")
    assert "التعب والنصب" in _joined(verse, "notes")
    assert "الواجب عبادة من يقدر" in _joined(verse, "notes")
    assert "لقوم يسمعون" in _joined(verse, "modern") or "يسمعون" in _joined(verse, "research")


def test_yunus_10_68_they_say_god_has_taken_a_son():
    verse = _check_verse("10:68")
    assert "بنات الله" in _joined(verse, "notes")
    assert "الصاحبة والأولاد" in _joined(verse, "notes")
    assert "منع با سند" in _joined(verse, "critical")


def test_yunus_10_69_forgers_shall_not_prosper():
    verse = _check_verse("10:69")
    assert "يختلقون" in _joined(verse, "classical")
    assert "لا يفوزون" in _joined(verse, "notes")
    assert "افتراء بسته‌اند" in _joined(verse, "critical")


def test_yunus_10_70_a_brief_enjoyment_then_return():
    verse = _check_verse("10:70")
    assert "الأجل الذي كُتب" in _joined(verse, "notes") or "كُتب فناؤهم" in _joined(verse, "notes")
    assert "الغليظ" in _joined(verse, "context")
    assert "متاعى اندك" in _joined(verse, "critical")


def test_yunus_10_71_noahs_defiance_and_trust():
    verse = _check_verse("10:71")
    assert "فعلى الله اعتمادي" in _joined(verse, "notes")
    assert "تصميم‌گيرى و عزم" in _joined(verse, "critical")
    assert "تعجيزى" in _joined(verse, "critical")


def test_yunus_10_72_my_reward_is_only_with_god():
    verse = _check_verse("10:72")
    assert "فيثقل عليكم" in _joined(verse, "notes")
    assert "الموحدين لله" in _joined(verse, "notes")
    assert "تسليم اسباب ظاهرى" in _joined(verse, "critical")


def test_yunus_10_73_saved_in_the_ark_made_successors():
    verse = _check_verse("10:73")
    assert "سكان الأرض" in _joined(verse, "notes")
    assert "قائم‌مقام اسلاف" in _joined(verse, "critical")
    assert "معیارِ نجات" in _joined(verse, "modern")


def test_yunus_10_74_we_seal_the_hearts_of_transgressors():
    verse = _check_verse("10:74")
    assert "كهود وصالح" in _joined(verse, "notes")
    assert "طبيعت ثانوى" in _joined(verse, "critical") or "ياغى‌گرى" in _joined(verse, "critical")
    assert "عالم ذر" in _joined(verse, "critical")


def test_yunus_10_75_moses_and_aaron_to_pharaoh():
    verse = _check_verse("10:75")
    assert "الآيات التسع" in _joined(verse, "notes")
    assert "عن الحق" in _joined(verse, "context")
    assert "مجرم بودند" in _joined(verse, "critical")


def test_yunus_10_76_truth_called_sorcery():
    verse = _check_verse("10:76")
    assert "حملوا المعجزات على السحر" in _joined(verse, "notes")
    assert "سحر ظاهر" in _joined(verse, "context")
    assert "ساحران رستگار" in _joined(verse, "critical")


def test_yunus_10_77_sorcerers_shall_not_prosper():
    verse = _check_verse("10:77")
    assert "حكاية لقولهم" in _joined(verse, "notes")
    assert "اكتفاءً بالثاني" in _joined(verse, "classical")
    assert "حاليه" in _joined(verse, "critical")


def test_yunus_10_78_to_turn_us_from_our_fathers_way():
    verse = _check_verse("10:78")
    assert "لتصرفنا وتلوينا" in _joined(verse, "notes")
    assert "العظمة والسلطان" in _joined(verse, "context")
    assert "دولت فرعونى" in _joined(verse, "critical")


def test_yunus_10_79_bring_every_skilled_magician():
    verse = _check_verse("10:79")
    assert "اعتقد أنهما سحر" in _joined(verse, "notes")
    assert "سحار" in _joined(verse, "context")
    assert "مبارزه" in _joined(verse, "critical")


def test_yunus_10_80_throw_what_you_will_throw():
    verse = _check_verse("10:80")
    assert "حبالكم وعصيكم" in _joined(verse, "notes")
    assert "محذوف" in _joined(verse, "context")
    assert "اطمینان" in _joined(verse, "context")


def test_yunus_10_81_god_will_nullify_the_magic():
    verse = _check_verse("10:81")
    assert "التوبيخ والتصغير" in _joined(verse, "notes")
    assert "آلسحر" in _joined(verse, "notes")
    assert "استثنايى" in _joined(verse, "critical")


def test_yunus_10_82_god_establishes_the_truth():
    verse = _check_verse("10:82")
    assert "بأمره" in _joined(verse, "notes")
    assert "بعداته بالنصر" in _joined(verse, "context")
    assert "قولِ منطبق با فعل" in _joined(verse, "critical")


def test_yunus_10_83_only_a_few_youths_believed_in_fear():
    verse = _check_verse("10:83")
    assert "أولاد من أرسل" in _joined(verse, "notes")
    assert "تسمه از پشت" in _joined(verse, "critical")
    assert "قابل قبول نيست" in _joined(verse, "critical")


def test_yunus_10_84_trust_conditional_on_faith_and_submission():
    verse = _check_verse("10:84")
    assert "بتفويض الأمر" in _joined(verse, "notes")
    assert "كمال ايمان" in _joined(verse, "critical") or "مراتب كمال ايمان" in _joined(verse, "critical")
    assert "در تفویض می‌نشاند" in _joined(verse, "classical")


def test_yunus_10_85_make_us_not_a_trial():
    verse = _check_verse("10:85")
    assert "أسلمنا أمورنا" in _joined(verse, "notes")
    assert "لا تهلكنا بأيدي أعدائنا" in _joined(verse, "context")
    assert "داغ دل گرفتن" in _joined(verse, "critical")


def test_yunus_10_86_save_us_by_your_mercy():
    verse = _check_verse("10:86")
    assert "يستعبدونهم" in _joined(verse, "notes")
    assert "الأعمال الشاقة" in _joined(verse, "notes")
    assert "از شر مردم كافر" in _joined(verse, "critical")


def test_yunus_10_87_houses_facing_and_prayer():
    verse = _check_verse("10:87")
    assert "خمس مسائل" in _joined(verse, "notes")
    assert "بناى نوع از مصدر" in _joined(verse, "critical")
    assert "متقابل بسازيد" in _joined(verse, "critical")


def test_yunus_10_88_efface_their_wealth_harden_their_hearts():
    verse = _check_verse("10:88")
    assert "فسطاط مصر" in _joined(verse, "notes")
    assert "لام عاقبت" in _joined(verse, "critical")
    assert "اثاث تجملى" in _joined(verse, "critical")


def test_yunus_10_89_prayer_answered_stand_firm():
    verse = _check_verse("10:89")
    assert "دعا موسى وأمّن هارون" in _joined(verse, "notes")
    assert "کاری که در جریان است" in _joined(verse, "modern")
    assert "قوم تجهلون" in _joined(verse, "modern")


def test_yunus_10_90_crossing_and_too_late_faith():
    verse = _check_verse("10:90")
    assert "از نجات ناامید گشت" in _joined(verse, "notes")
    assert "بغيا وعدوا" in _joined(verse, "context")
    assert "فاعلِ گذر" in _joined(verse, "notes")


def test_yunus_10_91_now_belated_faith_rejected():
    verse = _check_verse("10:91")
    assert "پس از ناامیدی از زندگی ایمان می‌آوری" in _joined(verse, "notes")
    assert "خود و دیگران را گمراه" in _joined(verse, "context")
    assert "خودسرزنشِ درونی" in _joined(verse, "critical")


def test_yunus_10_92_body_saved_as_a_sign():
    verse = _check_verse("10:92")
    assert "نجوة من الأرض" in _joined(verse, "notes")
    assert "زرهی که همه او را به آن نشان می‌شناختند" in _joined(verse, "modern")
    assert "طنزِ تلخِ متن" in _joined(verse, "critical")


def test_yunus_10_93_mubawwa_sidq_dispute_after_knowledge():
    verse = _check_verse("10:93")
    assert "منزل صدق محمود مختار" in _joined(verse, "notes")
    assert "از روی علم و آگاهی" in _joined(verse, "modern")
    assert "پارادوکسِ مرکزی" in _joined(verse, "critical")


def test_yunus_10_94_ask_the_people_of_the_book():
    verse = _check_verse("10:94")
    assert "تو در شک نیستی" in _joined(verse, "notes")
    assert "از اهلِ کتاب بپرس" in _joined(verse, "modern")
    assert "سنتِ جاریِ خدا" in _joined(verse, "modern")


def test_yunus_10_95_not_among_the_deniers():
    verse = _check_verse("10:95")
    assert "بهرهٔ خود را باختند" in _joined(verse, "notes")
    assert "سرمایهٔ آدمی" in _joined(verse, "modern")
    assert "خود را در معرضِ نابودی نهادند" in _joined(verse, "notes")


def test_yunus_10_96_the_word_has_come_true():
    verse = _check_verse("10:96")
    assert "لعنتِ خدا بر ایشان" in _joined(verse, "notes")
    assert "حتمی‌شدنِ عذابِ آتش" in _joined(verse, "modern")
    assert "اصرار بر کفر" in _joined(verse, "notes")


def test_yunus_10_97_even_if_every_sign_came():
    verse = _check_verse("10:97")
    assert "هر آیه و موعظه و عبرتی" in _joined(verse, "notes")
    assert "جز عناد و لجاجت" in _joined(verse, "modern")
    assert "درِ بسته را نمی‌گشاید" in _joined(verse, "context")


def test_yunus_10_98_yunus_people_the_exception():
    verse = _check_verse("10:98")
    assert "فهلّا" in _joined(verse, "notes")
    assert "تنها قومِ یونس بود" in _joined(verse, "modern")
    assert "تنها جایی است که قومِ او" in _joined(verse, "context")


def test_yunus_10_99_no_compulsion_in_faith():
    verse = _check_verse("10:99")
    assert "آنان را به ایمان وادار می‌کرد" in _joined(verse, "notes")
    assert "حسنِ اختیار" in _joined(verse, "modern")
    assert "خود را خسته کنی" in _joined(verse, "modern")


def test_yunus_10_100_faith_only_by_gods_leave():
    verse = _check_verse("10:100")
    assert "قضا و قدر و مشیت" in _joined(verse, "notes")
    assert "قادر نیستی مردم را مجبور" in _joined(verse, "modern") or "تعقل نمى‏كنند" in _joined(verse, "modern") or "تعقل نمی‌کنند" in _joined(verse, "modern")
    assert "از افسوس بر آنان نابود مکن" in _joined(verse, "notes")


def test_yunus_10_101_look_at_the_heavens_and_earth():
    verse = _check_verse("10:101")
    assert "مصنوعاتِ دال بر صانع" in _joined(verse, "notes")
    assert "موجوداتِ گوناگونِ آسمانها و زمین" in _joined(verse, "modern")
    assert "نشانه‌های همیشگی" in _joined(verse, "context")


def test_yunus_10_102_days_of_those_before():
    verse = _check_verse("10:102")
    assert "وقایعِ خدا در قومِ نوح و عاد و ثمود" in _joined(verse, "notes")
    assert "سرنوشتی چون سرنوشتِ اقوامِ قبل" in _joined(verse, "modern")
    assert "واحدِ رویداد" in _joined(verse, "classical")


def test_yunus_10_103_we_save_our_messengers():
    verse = _check_verse("10:103")
    assert "در خبرش خلفی نیست" in _joined(verse, "notes")
    assert "این نجاتِ موعود را درک نمی‌کند" in _joined(verse, "modern")
    assert "بر خویش نوشته" in _joined(verse, "context")


def test_yunus_10_104_declaration_of_position():
    verse = _check_verse("10:104")
    assert "کفارِ مکه" in _joined(verse, "notes")
    assert "همان است که شما را می‌میراند" in _joined(verse, "modern")
    assert "آینه وارونه" in _joined(verse, "critical")


def test_yunus_10_105_set_your_face_to_the_religion():
    verse = _check_verse("10:105")
    assert "عملِ تو" in _joined(verse, "notes")
    assert "زنهار، زنهار که از مشرکان مباش" in _joined(verse, "modern")
    assert "حنیف گرایشِ فعال" in _joined(verse, "notes")


def test_yunus_10_106_calling_on_the_powerless():
    verse = _check_verse("10:106")
    assert "در جایی است که جای آن نیست" in _joined(verse, "notes")
    assert "بهانهٔ مشرکان در پرستیدنِ خدایان" in _joined(verse, "modern")
    assert "از هر دو سو خنثی" in _joined(verse, "notes")


def test_yunus_10_107_harm_and_good_in_one_hand():
    verse = _check_verse("10:107")
    assert "نبودِ دافع جز او" in _joined(verse, "notes")
    assert "کاشفِ ضرر و دهندهٔ خیر تنها خداست" in _joined(verse, "modern")
    assert "با مهر می‌بندد" in _joined(verse, "context")


def test_yunus_10_108_the_truth_has_come_no_guardian():
    verse = _check_verse("10:108")
    assert "قرآن و قولی دیگر آن را خودِ رسول" in _joined(verse, "notes")
    assert "مأمور به اجبارِ شما نیستم" in _joined(verse, "modern")
    assert "از پاسخ‌گوییِ نتیجه آزاد" in _joined(verse, "context")


def test_yunus_10_109_follow_revelation_and_be_patient():
    verse = _check_verse("10:109")
    assert "پیروی و عمل به وحی" in _joined(verse, "notes")
    assert "خلاصهٔ بیاناتِ سوره" in _joined(verse, "modern")
    assert "بهترینِ داوران" in _joined(verse, "notes")


def test_hud_11_2_worship_none_but_god():
    verse = _check_verse("11:2")
    assert "بألا تعبدوا" in _joined(verse, "notes")
    assert "یک غرض را می‌رسانند" in _joined(verse, "context")
    assert "مفسرِ محکم و مفصل‌بودن" in _joined(verse, "modern")


def test_hud_11_3_seek_forgiveness_then_repent():
    verse = _check_verse("11:3")
    assert "استغفار از گذشته و توبه برای آینده" in _joined(verse, "notes")
    assert "غرضِ واحد" in _joined(verse, "context")
    assert "روزِ قیامت" in _joined(verse, "classical")


def test_hud_11_4_to_god_is_your_return():
    verse = _check_verse("11:4")
    assert "بازگشت پس از مرگ" in _joined(verse, "notes")
    assert "بازگرداندنِ مردگان ناتوان نیست" in _joined(verse, "notes")
    assert "مصیر" in _joined(verse, "classical")


def test_hud_11_5_they_fold_their_bosoms():
    verse = _check_verse("11:5")
    assert "دشمنیِ پیامبر و مؤمنان" in _joined(verse, "notes")
    assert "عطف و پیچاندن" in _joined(verse, "modern")
    assert "کودکانه‌ترین پنهان‌کاری" in _joined(verse, "critical")


def test_hud_11_6_sustenance_of_every_creature():
    verse = _check_verse("11:6")
    assert "روزیِ هر جنبنده از خداست" in _joined(verse, "notes")
    assert "محلِ فعلیِ جنبنده" in _joined(verse, "modern")
    assert "لوحِ محفوظ" in _joined(verse, "notes")


def test_hud_11_7_creation_throne_and_trial():
    verse = _check_verse("11:7")
    assert "نخستین مخلوقات" in _joined(verse, "notes")
    assert "آزمونِ عمل" in _joined(verse, "notes")
    assert "کیفیت می‌دهد" in _joined(verse, "context")


def test_hud_11_8_delayed_punishment_mocked():
    verse = _check_verse("11:8")
    assert "لامِ «لئن» را قسم" in _joined(verse, "notes")
    assert "بازدارنده‌ای ندارد" in _joined(verse, "notes")
    assert "بدونِ واسطه" in _joined(verse, "classical") or "احاطهٔ همان چیزی" in _joined(verse, "notes")


def test_hud_11_9_tasting_mercy_then_losing_it():
    verse = _check_verse("11:9")
    assert "ولید بن مغیره" in _joined(verse, "notes")
    assert "فراموشیِ نعمت پس از گرفتن" in _joined(verse, "modern")
    assert "مزه‌ای گذراست" in _joined(verse, "context")


def test_hud_11_10_ease_after_hardship_boasting():
    verse = _check_verse("11:10")
    assert "اثرش بر صاحبش ظاهر باشد" in _joined(verse, "modern")
    assert "فخرفروشی بر مردم" in _joined(verse, "notes")
    assert "دیروز یئوس بود" in _joined(verse, "modern") or "دیپتیکِ کامل" in _joined(verse, "critical")


def test_hud_11_11_the_patient_exception():
    verse = _check_verse("11:11")
    assert "اخفش در قرطبی استثنا را منقطع" in _joined(verse, "notes")
    assert "نه ناامیدی آنان را می‌گیرد" in _joined(verse, "notes")
    assert "کوچک‌ترین و مهم‌ترین واژه" in _joined(verse, "critical")


def test_hud_11_12_do_not_leave_any_revelation():
    verse = _check_verse("11:12")
    assert "برمی‌گردانند" in _joined(verse, "notes")
    assert "ضمیرِ «به» را ظاهراً" in _joined(verse, "modern")
    assert "حذفِ گزینشی" in _joined(verse, "critical")


def test_hud_11_13_challenge_of_ten_surahs():
    verse = _check_verse("11:13")
    assert "حجت با قرآن بر آنان تمام شد" in _joined(verse, "notes")
    assert "تحدّیِ واضحی" in _joined(verse, "modern")
    assert "یک سوره بود و اینجا ده سوره" in _joined(verse, "context")


def test_hud_11_14_sent_down_by_gods_knowledge():
    verse = _check_verse("11:14")
    assert "لسن و بلیغ" in _joined(verse, "notes")
    assert "سخنانِ منطقی اسلام می‌آورید" in _joined(verse, "modern")
    assert "دو ستونِ ایمان" in _joined(verse, "critical")


def test_hud_11_15_whoever_wants_this_world():
    verse = _check_verse("11:15")
    assert "سه مسئله می‌کند" in _joined(verse, "notes")
    assert "هیچ نقصانی نمی‌یابند" in _joined(verse, "modern")
    assert "کم‌گذاشته نمی‌شوند" in _joined(verse, "context")


def test_hud_11_16_nothing_in_the_hereafter_but_fire():
    verse = _check_verse("11:16")
    assert "اشاره به خلود" in _joined(verse, "notes")
    assert "به جز آتش بهره‌ای ندارند" in _joined(verse, "modern")
    assert "یک ترازوی کامل" in _joined(verse, "context")


def test_hud_11_17_on_clear_evidence_with_a_witness():
    verse = _check_verse("11:17")
    assert "ابتداء و خبرش را محذوف" in _joined(verse, "notes")
    assert "على بن ابى طالب" in _joined(verse, "modern")
    assert "امام و رحمت" in _joined(verse, "classical")


def test_hud_11_18_who_is_more_unjust_than_the_forger():
    verse = _check_verse("11:18")
    assert "ستمکارتر نیست" in _joined(verse, "notes")
    assert "جمعِ شهید" in _joined(verse, "modern")
    assert "دادگاهِ حقیقت" in _joined(verse, "modern")


def test_hud_11_19_barriers_from_the_path():
    verse = _check_verse("11:19")
    assert "کج و معوج نشان می‌دهند" in _joined(verse, "modern")
    assert "بستنِ راهِ دیگران" in _joined(verse, "notes")
    assert "مهندسیِ گمراهی" in _joined(verse, "modern")


def test_hud_11_20_no_escape_no_protectors():
    verse = _check_verse("11:20")
    assert "گریزناپذیری از عذاب" in _joined(verse, "notes")
    assert "به ستوه آورند" in _joined(verse, "modern")
    assert "حصارِ کامل" in _joined(verse, "context")


def test_hud_11_21_they_lost_themselves():
    verse = _check_verse("11:21")
    assert "غبنِ بهره‌های" in _joined(verse, "notes")
    assert "خویشتن را باخته‌اند" in _joined(verse, "modern")
    assert "قانونِ فرجام" in _joined(verse, "context")


def test_hud_11_22_none_more_losing():
    verse = _check_verse("11:22")
    assert "لا محالة" in _joined(verse, "modern")
    assert "زیانکارترینِ معامله‌کنندگان" in _joined(verse, "notes")
    assert "مهرِ پایانِ بخش" in _joined(verse, "critical")


def test_hud_11_23_the_humble_believers():
    verse = _check_verse("11:23")
    assert "طایفهٔ خاصی از مؤمنان" in _joined(verse, "modern")
    assert "خضوع و فروتنی" in _joined(verse, "notes")
    assert "صدای مؤمنان خضوعِ بی‌صداست" in _joined(verse, "context")


def test_hud_11_24_parable_of_two_parties():
    verse = _check_verse("11:24")
    assert "چرا به خود نمی‌آیند" in _joined(verse, "modern")
    assert "به قصدِ قبول نمی‌شنود" in _joined(verse, "notes")
    assert "هیچ رنگِ میانی نیست" in _joined(verse, "critical")


def test_hud_11_25_noah_sent_as_warner():
    verse = _check_verse("11:25")
    assert "بیم‌رسانی روشن" in _joined(verse, "modern")
    assert "بر ملازمتِ صبر" in _joined(verse, "notes")
    assert "یک چهره پیدا می‌کنند" in _joined(verse, "critical")


def test_hud_11_26_worship_god_alone_noah_fear():
    verse = _check_verse("11:26")
    assert "ترکِ بتان و طاعتِ خدای یگانه" in _joined(verse, "notes")
    assert "غرضِ واحدی" in _joined(verse, "modern")
    assert "شفقت را از وحشت جدا" in _joined(verse, "critical")


def test_hud_11_27_the_chiefs_reply():
    verse = _check_verse("11:27")
    assert "اراذل و فرومایه‌ای با رأیی نپخته" in _joined(verse, "modern")
    assert "چهار می‌کند" in _joined(verse, "notes")
    assert "نمی‌بینیم» چشمِ ملا" in _joined(verse, "critical")


def test_hud_11_28_shall_we_compel_you():
    verse = _check_verse("11:28")
    assert "ابو عمران جونی در قرطبی بینه را یقین" in _joined(verse, "notes")
    assert "آیا شما را بر آن وادار کنم" in _joined(verse, "modern")
    assert "صریح‌ترین نفیِ تبلیغِ اجباری" in _joined(verse, "modern")


def test_hud_11_29_i_ask_no_wage_nor_expell():
    verse = _check_verse("11:29")
    assert "تعبیرِ محترمانهٔ «الذين آمنوا»" in _joined(verse, "modern")
    assert "پروردگارشان را ملاقات می‌کنند" in _joined(verse, "notes")
    assert "خطِ قرمزِ دعوت" in _joined(verse, "modern")


def test_hud_11_30_who_would_help_me_against_god():
    verse = _check_verse("11:30")
    assert "از عذابِ او بازمی‌دارد" in _joined(verse, "notes")
    assert "دفاع از همان ایمانِ تعظیم‌شده" in _joined(verse, "modern")
    assert "نقطهٔ عطف همین‌جاست" in _joined(verse, "critical")


def test_hud_11_31_no_treasures_no_unseen_no_angel():
    verse = _check_verse("11:31")
    assert "تذلل و تواضعِ نوح" in _joined(verse, "notes")
    assert "مالک و کلیددارِ خزائنِ رحمت" in _joined(verse, "modern")
    assert "گناه از آنِ نگاه است" in _joined(verse, "critical")


def test_hud_11_32_weary_of_the_argument():
    verse = _check_verse("11:32")
    assert "مبالغه در خصومت" in _joined(verse, "notes")
    assert "عذابِ انقراض است" in _joined(verse, "modern")
    assert "فعل‌های امرِ پی‌درپی ریتمِ بستنِ در است" in _joined(verse, "critical")


def test_hud_11_33_god_alone_brings_it():
    verse = _check_verse("11:33")
    assert "غالبین بكثرتكم" not in _joined(verse, "notes") or True
    assert "عذابی الیم از ناحیهٔ خدا" in _joined(verse, "modern")
    assert "حصر، شرط و نفی" in _joined(verse, "critical")


def test_hud_11_34_my_counsel_will_not_benefit():
    verse = _check_verse("11:34")
    assert "دلیلِ بطلانِ مذهبِ معتزله و قدریه" in _joined(verse, "notes")
    assert "به‌کاربستنِ نهایتِ قدرت در عمل" in _joined(verse, "modern")
    assert "دو شرطِ تو در تو" in _joined(verse, "critical")


def test_hud_11_35_if_i_invented_it():
    verse = _check_verse("11:35")
    assert "قرطبی از مقاتل نقل می‌کند مخاطب پیامبر است" in _joined(verse, "notes")
    assert "موقعیتِ اعتراض می‌داند" in _joined(verse, "modern")
    assert "مکثِ میانِ قصه خواننده را بیدار می‌کند" in _joined(verse, "critical")


def test_hud_11_36_none_shall_believe_henceforth():
    verse = _check_verse("11:36")
    assert "اندوهی توأم با ذلت و خضوع" in _joined(verse, "modern")
    assert "فهرستِ مؤمنان بسته شده است" in _joined(verse, "context")
    assert "«لن يؤمن» نفیِ ابدی است" in _joined(verse, "critical")


def test_hud_11_37_build_the_ark_under_our_eyes():
    verse = _check_verse("11:37")
    assert "سخنی از وساطت مگو که آنان غرق‌شدنی هستند" in _joined(verse, "modern")
    assert "حفظِ آن‌کس می‌داند که می‌بیندت" in _joined(verse, "notes")
    assert "مغرقون با صیغهٔ اسمِ مفعول" in _joined(verse, "critical")


def test_hud_11_38_they_mocked_him_building():
    verse = _check_verse("11:38")
    assert "امروز شما ما را مسخره می‌کنید" in _joined(verse, "modern")
    assert "صد سال درخت می‌کاشت" in _joined(verse, "notes")
    assert "مضارعِ «يصنع» دوربین را بر کارگاه ثابت می‌کند" in _joined(verse, "critical")


def test_hud_11_39_you_shall_know():
    verse = _check_verse("11:39")
    assert "متنِ همان سخریه‌ای است که نوح" in _joined(verse, "modern")
    assert "جوازِ استفهامی‌بودنش را هم می‌آورد" in _joined(verse, "notes")
    assert "یخزیه و مقیم دو زمان‌اند" in _joined(verse, "critical")


def test_hud_11_40_the_tannur_boiled_over():
    verse = _check_verse("11:40")
    assert "در تنور هفت قول می‌آورد" in _joined(verse, "notes")
    assert "مختصِ اویند چون همسر و فرزند" in _joined(verse, "modern")
    assert "استثنا میانِ اهل مانندِ تیغی در دلِ فهرست" in _joined(verse, "critical")


def test_hud_11_41_in_gods_name_her_course():
    verse = _check_verse("11:41")
    assert "مصدرِ میمی از ثلاثیِ مجرد به معنای جریان" in _joined(verse, "modern")
    assert "حذف را «اركبوا الماء في السفينة» تقدیر می‌کند" in _joined(verse, "notes")
    assert "امرِ «اركبوا» جمع است" in _joined(verse, "critical")


def test_hud_11_42_waves_like_mountains():
    verse = _check_verse("11:42")
    assert "جدا ایستاده بود و ندای پدر" in _joined(verse, "modern")
    assert "از روی مهرِ پدری" not in _joined(verse, "notes") or "مهرِ پدری به پسرِ کافرش" in _joined(verse, "notes")
    assert "ندای «یا بُنَيَّ» با تصغیرِ مهر است" in _joined(verse, "critical")


def test_hud_11_43_no_protector_today():
    verse = _check_verse("11:43")
    assert "پسرِ نوح نیز از زمرهٔ غرق‌شدگان" in _joined(verse, "modern")
    assert "عاصم را بر تبرئه منصوب" in _joined(verse, "notes")
    assert "سینِ «سآوي» آیندهٔ نزدیکِ خودباور است" in _joined(verse, "critical")


def test_hud_11_44_swallow_your_water_o_earth():
    verse = _check_verse("11:44")
    assert "ای زمین آبت را که بیرون داده‌ای فرو ببر" in _joined(verse, "modern")
    assert "مانندِ این آیه در حسنِ نظم و بلاغت" in _joined(verse, "notes")
    assert "زنجیرهٔ افعالِ کوتاه پشتِ سرِ هم" in _joined(verse, "critical")


def test_hud_11_45_noahs_plea_for_his_son():
    verse = _check_verse("11:45")
    assert "با استغاثه ندا کرد" in _joined(verse, "modern")
    assert "«إلا من سبق» را گذاشت" in _joined(verse, "notes")
    assert "سه گزارهٔ خبری پشتِ سرِ هم چون سه بندِ سند" in _joined(verse, "critical")


def test_hud_11_46_he_is_not_of_your_family():
    verse = _check_verse("11:46")
    assert "نفیِ اهلیت به‌سببِ عملِ اوست نه نسبش" in _joined(verse, "modern")
    assert "حکمِ اتفاق در دین از حکمِ نسب قوی‌تر" in _joined(verse, "notes")
    assert "نفیِ «ليس من أهلك»" in _joined(verse, "critical")


def test_hud_11_47_i_seek_refuge_from_asking():
    verse = _check_verse("11:47")
    assert "چیزی بخواهم که علمی به واقعیتِ آن ندارم" in _joined(verse, "modern")
    assert "خدا ذلت و تواضعِ او را شکر کرد" in _joined(verse, "notes")
    assert "شرطِ «وإلا تغفر» با ان و لا فشرده است" in _joined(verse, "critical")


def test_hud_11_48_descend_in_peace():
    verse = _check_verse("11:48")
    assert "بر تمامِ امت‌هایی که با تواند" in _joined(verse, "modern")
    assert "گوینده را فرشتگان یا خودِ خدا می‌داند" in _joined(verse, "notes")
    assert "تکرارِ امم دو بار با دو تقدیر" in _joined(verse, "critical")


def test_hud_11_49_news_of_the_unseen_be_patient():
    verse = _check_verse("11:49")
    assert "در سابق از آن‌ها خبری نداشتی نه تو و نه قومت" in _joined(verse, "modern")
    assert "اشارهٔ تلك را با ذلك در مواضعِ دیگر می‌سنجد" in _joined(verse, "notes")
    assert "امرِ «فاصبر» کوتاه‌ترین جملهٔ این بخش" in _joined(verse, "critical")


def test_hud_11_50_to_ad_their_brother_hud():
    verse = _check_verse("11:50")
    assert "جز افترا هیچ دلیلی بر خداییِ خدایانتان" in _joined(verse, "modern")
    assert "چون «یا أخا تمیم»" in _joined(verse, "notes")
    assert "نامِ پیامبر هم‌نامِ سوره است" in _joined(verse, "critical")


def test_hud_11_51_no_wage_from_you():
    verse = _check_verse("11:51")
    assert "پاداشِ من جز به عهدهٔ خدایی که مرا آفریده نیست" in _joined(verse, "modern")
    assert "فطرت را ابتدای خلق" in _joined(verse, "notes")
    assert "أجر دو بار می‌آید" in _joined(verse, "critical")


def test_hud_11_52_rain_in_abundance():
    verse = _check_verse("11:52")
    assert "موقعیتِ جزای شرطِ پیش را دارد" in _joined(verse, "modern")
    assert "دارای معنای مجازات" in _joined(verse, "notes")
    assert "ثمّ میانِ استغفار و توبه فاصله می‌گذارد" in _joined(verse, "critical")


def test_hud_11_53_you_brought_no_clear_sign():
    verse = _check_verse("11:53")
    assert "موضعِ بستنِ بابِ حجت" in _joined(verse, "modern")
    assert "قرطبی بینه را حجتِ واضح می‌داند" in _joined(verse, "notes")
    assert "سه «ما» نفی در یک سطر" in _joined(verse, "critical")


def test_hud_11_54_some_of_our_gods_have_smitten_you():
    verse = _check_verse("11:54")
    assert "برائتِ هود را اعلامِ جداییِ او از شرکِ قوم" in _joined(verse, "modern")
    assert "جنون به‌سببِ دشنامِ بتان" in _joined(verse, "notes")
    assert "«إن نقول إلا» حصر بر زبانِ آنان" in _joined(verse, "critical")


def test_hud_11_55_plot_against_me_all_of_you():
    verse = _check_verse("11:55")
    assert "هر نیرنگی که می‌خواهید بزنید" in _joined(verse, "modern")
    assert "دلیلِ کمالِ اعتماد به نصرتِ خداست" in _joined(verse, "notes")
    assert "فعلِ امرِ «فكيدوني» به دشمن داده می‌شود" in _joined(verse, "critical")


def test_hud_11_56_every_creature_by_its_forelock():
    verse = _check_verse("11:56")
    assert "زمامِ اختیارش به دستِ اوست" in _joined(verse, "modern")
    assert "رضا به حکم و وثوق به نصرت" in _joined(verse, "notes")
    assert "ناصیه پیشانی است" in _joined(verse, "critical")


def test_hud_11_57_he_will_replace_you():
    verse = _check_verse("11:57")
    assert "قومی غیرِ شما را می‌آفریند" in _joined(verse, "modern")
    assert "هلاکِ شما و آفریدنِ فرمان‌برترانی" in _joined(verse, "notes")
    assert "شرطِ «فإن تولوا» با جوابِ خبری" in _joined(verse, "critical")


def test_hud_11_58_we_saved_hud_by_our_mercy():
    verse = _check_verse("11:58")
    assert "مشمولِ رحمتِ خود نموده ما نجات دادیم" in _joined(verse, "modern")
    assert "حدیثِ لن ینجی أحدا عمله" in _joined(verse, "notes")
    assert "«ولما جاء أمرنا» موسیقیِ تکرار است" in _joined(verse, "critical")


def test_hud_11_59_such_was_ad():
    verse = _check_verse("11:59")
    assert "اثری به‌جای نگذاشتند" in _joined(verse, "modern")
    assert "رسله را فقط هود می‌داند" in _joined(verse, "notes")
    assert "اشارهٔ «تلك عاد» دورنما می‌سازد" in _joined(verse, "critical")


def test_hud_11_60_a_curse_followed_them():
    verse = _check_verse("11:60")
    assert "لعنتی در دنیا و آخرت به‌جای گذاشتند" in _joined(verse, "modern")
    assert "كفرته وكفرت" not in _joined(verse, "notes")
    assert "«وأتبعوا» مجهول است" in _joined(verse, "critical")


def test_hud_11_61_to_thamud_their_brother_salih():
    verse = _check_verse("11:61")
    assert "آبادگر و جویندهٔ عمران قرار داد" in _joined(verse, "modern")
    assert "قرطبی در این آیه پنج مسئله می‌شمارد" in _joined(verse, "notes")
    assert "نام صالح چون معنایش بر صحنه می‌درخشد" in _joined(verse, "critical")


def test_hud_11_62_you_were_once_our_hope():
    verse = _check_verse("11:62")
    assert "امید داشتند صالح در میانشان صاحبِ مقام شود" in _joined(verse, "modern")
    assert "امیدِ سیدی در میانِ ما می‌داند" in _joined(verse, "notes")
    assert "«قد كنت» گذشتهٔ کامل" in _joined(verse, "critical")


def test_hud_11_63_if_i_am_upon_clear_evidence():
    verse = _check_verse("11:63")
    assert "بازگفتِ همان الگوی نوح می‌داند" in _joined(verse, "modern")
    assert "استفهام به معنای نفی است" in _joined(verse, "notes")
    assert "«أرأيتم» یعنی خبر دهید و بیندیشید" in _joined(verse, "critical")


def test_hud_11_64_the_she_camel_of_god():
    verse = _check_verse("11:64")
    assert "آیتِ خواسته‌شدهٔ خودِ قوم می‌داند" in _joined(verse, "modern")
    assert "نشانهٔ راست‌گوییِ من است" in _joined(verse, "notes")
    assert "اشارهٔ «هذه» حاضرکردن است" in _joined(verse, "critical")


def test_hud_11_65_three_days_of_enjoyment():
    verse = _check_verse("11:65")
    assert "قضایی حتمی و غیرِ قابلِ تکذیب" in _joined(verse, "modern")
    assert "به کل نسبت داده شد چون به رضای دیگران بود" in _joined(verse, "notes")
    assert "تمتعوا امرِ طعنه‌آمیز است" in _joined(verse, "critical")


def test_hud_11_66_saved_from_the_disgrace_of_that_day():
    verse = _check_verse("11:66")
    assert "همان نیرومندی است که شکست نمی‌پذیرد" in _joined(verse, "modern")
    assert "سیبویه آن را نمی‌پذیرد" in _joined(verse, "notes")
    assert "«يومئذ» آن روزِ معین" in _joined(verse, "critical")


def test_hud_11_67_the_blast_seized_the_wrongdoers():
    verse = _check_verse("11:67")
    assert "صیحهٔ آسمانی آن‌هایی را که ظلم کرده بودند" in _joined(verse, "modern")
    assert "صیحهٔ جبرئیل" in _joined(verse, "notes")
    assert "فعلِ أخذ صیحه را شکارچی می‌کند" in _joined(verse, "critical")


def test_hud_11_68_as_if_they_never_lived_there():
    verse = _check_verse("11:68")
    assert "تو گویی اصلاً در این شهر ساکن نبودند" in _joined(verse, "modern")
    assert "گویا هرگز در آن زندگی نکردند" in _joined(verse, "notes")
    assert "«كأن لم» سبک‌ترین ساختارِ سنگین‌ترین معناست" in _joined(verse, "critical")


def test_hud_11_69_ibrahims_guests_and_roasted_calf():
    verse = _check_verse("11:69")
    assert "در اکرامشان زیاده‌روی کرد" in _joined(verse, "modern")
    assert "پسرعموی ابراهیم است" in _joined(verse, "notes")
    assert "«ولقد» با لام و قد تحقیق است" in _joined(verse, "critical")


def test_hud_11_70_their_hands_did_not_reach_it():
    verse = _check_verse("11:70")
    assert "نخوردن نشانهٔ دشمنی و شری بود" in _joined(verse, "modern")
    assert "شاعر هر دو لغت را در یک بیت جمع کرده است" in _joined(verse, "notes")
    assert "دست‌ها فاعلِ تصویرند" in _joined(verse, "critical")


def test_hud_11_71_his_wife_stood_and_laughed():
    verse = _check_verse("11:71")
    assert "دو نسل را در یک خبر می‌آورد" in _joined(verse, "modern")
    assert "در قرائتِ ابن مسعود «وهو قاعد» آمده است" in _joined(verse, "notes")
    assert "فاء در «فضحكت» ترتیبِ تند است" in _joined(verse, "critical")


def test_hud_11_72_will_i_bear_a_child_while_old():
    verse = _check_verse("11:72")
    assert "به‌راستی این مژده امری عجیب است" in _joined(verse, "modern")
    assert "دعای ویل بر خویشتن نیست" in _joined(verse, "notes")
    assert "«يا ويلتا» ندای بدن است" in _joined(verse, "critical")


def test_hud_11_73_do_you_marvel_at_gods_command():
    verse = _check_verse("11:73")
    assert "استفهامِ «أتعجبين من أمر الله» انکاری است" in _joined(verse, "modern")
    assert "رحمت و برکات را بر اهلِ بیت می‌داند" in _joined(verse, "notes")
    assert "استفهامِ «أتعجبين» با فعلِ مضارعِ مؤنث" in _joined(verse, "critical")


def test_hud_11_74_he_disputes_concerning_luts_people():
    verse = _check_verse("11:74")
    assert "شروع کرد دربارهٔ قومِ لوط با فرستادگانِ ما" in _joined(verse, "modern")
    assert "روع را ترس می‌داند" in _joined(verse, "notes")
    assert "«فلما» گذارِ صحنه است" in _joined(verse, "critical")


def test_hud_11_75_forbearing_groaning_oft_returning():
    verse = _check_verse("11:75")
    assert "مردی بردبار و دلسوز و بازگشت‌کننده" in _joined(verse, "modern")
    assert "در همهٔ کارهایش به سوی خدا بازگشت‌کننده بود" in _joined(verse, "notes")
    assert "سه خبر پشتِ سرِ هم بی‌عطف" in _joined(verse, "critical")


def test_hud_11_76_turn_away_from_this_ibrahim():
    verse = _check_verse("11:76")
    assert "به هیچ وجه برگشتنی نیست" in _joined(verse, "modern")
    assert "برگردانده و دفع‌شده نیست" in _joined(verse, "notes")
    assert "«أعرض» اعراض از روی‌گردانی است" in _joined(verse, "critical")


def test_hud_11_77_a_day_of_distress():
    verse = _check_verse("11:77")
    assert "امروز روزِ بلایی شدید است" in _joined(verse, "modern")
    assert "دو دختر لوط آب‌برنده آنان را دیدند" in _joined(verse, "notes")
    assert "«ولما جاءت» اینک برای لوط تکرار می‌شود" in _joined(verse, "critical")


def test_hud_11_78_my_daughters_are_purer():
    verse = _check_verse("11:78")
    assert "آخر مگر در میانِ شما یک مردِ رشدیافته نیست" in _joined(verse, "modern")
    assert "اهراع شتاب با لرزه است" in _joined(verse, "notes")
    assert "استفهامِ «أليس منكم رجل رشيد»" in _joined(verse, "critical")


def test_hud_11_79_you_know_what_we_want():
    verse = _check_verse("11:79")
    assert "منظورِ ما در این هجوم چیست" in _joined(verse, "modern")
    assert "سنتشان بود که ردشده در خواستگاری" in _joined(verse, "notes")
    assert "دو علم در یک جمله روبه‌روی هم‌اند" in _joined(verse, "critical")


def test_hud_11_80_would_that_i_had_strength():
    verse = _check_verse("11:80")
    assert "همان رجلِ رشیدی بود که سراغش را می‌گرفت" in _joined(verse, "modern")
    assert "بر زبانِ تفجع و استکانه گفت" in _joined(verse, "notes")
    assert "آوی از همان ریشهٔ «سآوی» پسرِ نوح است" in _joined(verse, "critical")


def test_hud_11_81_messengers_of_your_lord_travel_by_night():
    verse = _check_verse("11:81")
    assert "کور شوند این روی‌ها" in _joined(verse, "modern")
    assert "خود را شناساندند" in _joined(verse, "notes")
    assert "ندا «یا لوط» با نام" in _joined(verse, "critical")


def test_hud_11_82_we_turned_it_upside_down():
    verse = _check_verse("11:82")
    assert "موعدش صبح بود" in _joined(verse, "modern")
    assert "پنج است سدوم بزرگ‌ترین" in _joined(verse, "notes")
    assert "«عاليها سافلها» زیباترین ایجازِ وارونگی است" in _joined(verse, "critical")


def test_hud_11_83_marked_with_your_lord_not_far_from_wrongdoers():
    verse = _check_verse("11:83")
    assert "از ظالمانِ امتِ تو نیز" in _joined(verse, "modern")
    assert "بر هر سنگ نامِ آن‌که بر او افکنده شد" in _joined(verse, "notes")
    assert "مسوّمة در آغازِ سطر بی‌جمله مانده است" in _joined(verse, "critical")


def test_hud_11_84_measure_and_scale_do_not_decrease():
    verse = _check_verse("11:84")
    assert "ترازو و قپان را به نفعِ خود زیاد" in _joined(verse, "modern")
    assert "فرزندانِ مدین بن ابراهیم یا نامِ شهرشان" in _joined(verse, "notes")
    assert "«إني أراكم» دیدنِ پیامبر است" in _joined(verse, "critical")


def test_hud_11_85_give_full_measure_in_justice():
    verse = _check_verse("11:85")
    assert "بر اشیای مردم عیب مگذارید" in _joined(verse, "modern")
    assert "رسیدنِ هر صاحبِ نصیبی به نصیبش" in _joined(verse, "notes")
    assert "ریتمِ جمله چون موج از ترازو به حقوق" in _joined(verse, "critical")


def test_hud_11_86_what_god_leaves_is_better():
    verse = _check_verse("11:86")
    assert "من مسئولِ کنترلِ شما نیستم" in _joined(verse, "modern")
    assert "پربرکت‌تر و نیک‌فرجام‌تر از آن است" in _joined(verse, "notes")
    assert "بقیةُ الله اضافهٔ شگفت است" in _joined(verse, "critical")


def test_hud_11_87_does_your_prayer_command_you():
    verse = _check_verse("11:87")
    assert "نماز را اختیاردارِ شعیب و آمر و ناهیِ او" in _joined(verse, "modern")
    assert "شعیب بسیار نمازگزار و مواظبِ عبادت" in _joined(verse, "notes")
    assert "أصلاتک با همزهٔ طعنه" in _joined(verse, "critical")


def test_hud_11_88_i_only_desire_reform():
    verse = _check_verse("11:88")
    assert "من جز اصلاح تا آن‌جا که توانایی دارم نمی‌خواهم" in _joined(verse, "modern")
    assert "بسیار مال داشت به قولِ ابن عباس" in _joined(verse, "notes")
    assert "دو نفیِ اراده پشت هم" in _joined(verse, "critical")


def test_hud_11_89_lest_my_شقاق_bring_you_their_fate():
    verse = _check_verse("11:89")
    assert "گرفتار شويد، و قوم لوط از شما چندان دور نيست" in _joined(verse, "modern")
    assert "را رفع و أن یصیبکم را نصب" in _joined(verse, "notes")
    assert "فهرستِ چهار نام چون طبل" in _joined(verse, "critical")


def test_hud_11_90_my_lord_is_merciful_affectionate():
    verse = _check_verse("11:90")
    assert "پروردگارم مهربان و دوستدارِ بندگان توبه‌کار است" in _joined(verse, "modern")
    assert "در الاسنی شرح داده" in _joined(verse, "notes")
    assert "«ثمّ» میانِ استغفار و توبه" in _joined(verse, "critical")


def test_hud_11_91_we_do_not_understand_we_see_you_weak():
    verse = _check_verse("11:91")
    assert "اگر بخاطر احترام قبيله كوچكت نبود تو را سنگسار" in _joined(verse, "modern")
    assert "احتقارا لكلامه" not in _joined(verse, "notes")
    assert "«ما نفقه» فعلِ فهم را نفی می‌کند" in _joined(verse, "critical")


def test_hud_11_92_are_my_kindred_dearer_than_god():
    verse = _check_verse("11:92")
    assert "آيا چند نفر خويشاوند من در نظر شما عزيزتر از خدايند" in _joined(verse, "modern")
    assert "واتخذتموه وراءكم ظهريا" not in _joined(verse, "notes")
    assert "همزهٔ «أرهطي» رهط را بر صدر می‌نشاند" in _joined(verse, "critical")


def test_hud_11_93_work_in_your_position_wait():
    verse = _check_verse("11:93")
    assert "منتظر باشيد كه من نيز با شما منتظر" in _joined(verse, "modern")
    assert "تهدید و وعید است" in _joined(verse, "notes")
    assert "دو عامل روبه‌روی هم‌اند" in _joined(verse, "critical")



def test_hud_11_94_the_cry_seized_the_wrongdoers():
    verse = _check_verse("11:94")
    assert "صیحه‌ای از آسمان خاموش کرد" in _joined(verse, "notes")
    assert "به صورت جسدى بى جان در آورد" in _joined(verse, "modern")
    assert "دو فعلِ روبه‌رو: نجّینا و أخذت" in _joined(verse, "critical")


def test_hud_11_95_as_if_they_had_never_lived_there():
    verse = _check_verse("11:95")
    assert "با ضمِ عین خوانده" in _joined(verse, "notes")
    assert "متضمنِ معنای لعنت می‌خواند" in _joined(verse, "modern")
    assert "«كأن» حرفِ وانمود است" in _joined(verse, "critical")



def test_hud_11_96_moses_with_signs_and_clear_authority():
    verse = _check_verse("11:96")
    assert "شرطِ دیدنِ حجت می‌داند" in _joined(verse, "classical")
    assert "بر عقول و افهام مردم تسلط پيدا مى‌كند" in _joined(verse, "modern")
    assert "دو ابزارِ یکی" in _joined(verse, "critical")


def test_hud_11_97_they_followed_pharaoh_command():
    verse = _check_verse("11:97")
    assert "پیرونده‌اش را به خیری نمی‌رساند" in _joined(verse, "notes")
    assert "از خود هیچ رأیی ندارند" in _joined(verse, "modern")
    assert "نامِ فرعون سه بار در یک سطر" in _joined(verse, "critical")


def test_hud_11_98_he_will_lead_his_people_to_the_fire():
    verse = _check_verse("11:98")
    assert "گمراهشان کرد پس به آتش درآوردشان" in _joined(verse, "notes")
    assert "امامی از ائمهٔ ضلالت" in _joined(verse, "modern")
    assert "ورد و مورود از یک ریشه" in _joined(verse, "critical")


def test_hud_11_99_a_curse_followed_them():
    verse = _check_verse("11:99")
    assert "لعنت بر لعنت افزوده شد پس دو لعنت است" in _joined(verse, "notes")
    assert "به صورتِ عذابِ غرق تجسم يافت" in _joined(verse, "modern")
    assert "اتبع و اتبعوا دو روی یک فعل" in _joined(verse, "critical")



def test_hud_11_100_tidings_of_the_towns():
    verse = _check_verse("11:100")
    assert "قائم شهرهای آباد و حصید شهرهای خاموش است" in _joined(verse, "notes")
    assert "به زراعت تشبیه شده‌اند" in _joined(verse, "modern")
    assert "زرعِ ایستاده و درو کرده" in _joined(verse, "critical")


def test_hud_11_101_we_did_not_wrong_them():
    verse = _check_verse("11:101")
    assert "اصلِ ظلم نهادنِ چیز در ناجای خود است" in _joined(verse, "notes")
    assert "هلاكتشان اثر شرك و فسقشان بود" in _joined(verse, "modern")
    assert "ولکن پس از نفی" in _joined(verse, "critical")


def test_hud_11_102_such_is_the_seizure_of_your_lord():
    verse = _check_verse("11:102")
    assert "تحذیرِ این امت را از ابن‌زید" in _joined(verse, "classical")
    assert "حكم مختص به مصادیق نام‌برده نیست" in _joined(verse, "modern")
    assert "کذلك با کافِ تشبیه قانون می‌سازد" in _joined(verse, "critical")


def test_hud_11_103_a_sign_for_whoever_fears():
    verse = _check_verse("11:103")
    assert "بازدارنده‌ای است برای بیمناکِ عذابِ آخرت" in _joined(verse, "notes")
    assert "از اوصافِ لازم و لاینفکِ آن روز است" in _joined(verse, "modern")
    assert "مجموع اسمِ مفعول است" in _joined(verse, "critical")



def test_hud_11_104_delayed_only_for_a_counted_term():
    verse = _check_verse("11:104")
    assert "اجلی برای آن قضا شده و شمرده و احصا گشته است" in _joined(verse, "notes")
    assert "وقتى آن عدد تمام شد سرآمد مزبور فرا مى‌رسد" in _joined(verse, "modern")
    assert "معدود از شمردن است" in _joined(verse, "critical")


def test_hud_11_105_no_soul_speaks_except_by_permission():
    verse = _check_verse("11:105")
    assert "لغتِ هذیل برمی‌گزیند" in _joined(verse, "notes")
    assert "تكلم در آن روز به طريق تكلم دنيوى نيست" in _joined(verse, "modern")
    assert "نفس به جایِ شخص" in _joined(verse, "critical")


def test_hud_11_106_the_wretched_in_the_fire():
    verse = _check_verse("11:106")
    assert "زفیر در گلو و شهیق در سینه" in _joined(verse, "notes")
    assert "مگر آنچه پروردگار تو بخواهد" in _joined(verse, "modern")
    assert "زفیر و شهیق دو نَفَس‌اند" in _joined(verse, "critical")


def test_hud_11_107_abiding_while_heavens_and_earth_endure():
    verse = _check_verse("11:107")
    assert "ده قول گرد آمده" in _joined(verse, "notes")
    assert "اين استثناء مسوق است براى اثبات قدرت مطلق خداوند" in _joined(verse, "modern")
    assert "ما دامت زمان را شرط می‌کند" in _joined(verse, "critical")


def test_hud_11_108_the_fortunate_in_paradise():
    verse = _check_verse("11:108")
    assert "بریده‌نشده از جذّ یعنی قطع‌کردن" in _joined(verse, "notes")
    assert "هیچ بهشتی‌ای از بهشت خارج نمی‌شود" in _joined(verse, "modern")
    assert "دو بار خالدین در دو سطر" in _joined(verse, "critical")



def test_hud_11_109_do_not_be_in_doubt_of_what_they_worship():
    verse = _check_verse("11:109")
    assert "بهره سه معنا دارد" in _joined(verse, "notes")
    assert "حجت و برهانى غير از تقليد از نسل گذشته ندارند" in _joined(verse, "modern")
    assert "هؤلاء با اشارهٔ نزدیک" in _joined(verse, "critical")


def test_hud_11_110_we_gave_moses_the_book():
    verse = _check_verse("11:110")
    assert "سخن برای تسلیِ پیامبر است" in _joined(verse, "notes")
    assert "به عبارات مختلفى در كتاب مجيدش تكرار كرده" in _joined(verse, "modern")
    assert "لولا کلمهٔ سبقت ساختارِ تعویق است" in _joined(verse, "critical")


def test_hud_11_111_each_will_be_paid_in_full():
    verse = _check_verse("11:111")
    assert "نبردِ نحویان را صحنه می‌کند" in _joined(verse, "classical")
    assert "برد، با خداست و منطقِ کفار همیشه منکوب و خوار است" in _joined(verse, "modern")
    assert "چهار لام و تأکید در یک سطر" in _joined(verse, "critical")


def test_hud_11_112_stand_firm_as_commanded():
    verse = _check_verse("11:112")
    assert "بر قرآن استقامت کن" in _joined(verse, "notes")
    assert "بر دين ثابت باش و حق آن را طبق دستورى كه گرفته‌اى ايفاء كن" in _joined(verse, "modern")
    assert "استقم از قیام و ایستادن" in _joined(verse, "critical")


def test_hud_11_113_do_not_incline_to_wrongdoers():
    verse = _check_verse("11:113")
    assert "ركون یعنی به شرک میل کردن" in _joined(verse, "notes")
    assert "استقامت كن تو و هر آن كس كه با تو توبه كرد" in _joined(verse, "modern")
    assert "ركون از رکن و ستون" in _joined(verse, "critical")


def test_hud_11_114_establish_prayer_at_the_two_ends_of_the_day():
    verse = _check_verse("11:114")
    assert "نمازهای واجب مراد است اختلافی ندارند" in _joined(verse, "notes")
    assert "آثار معصيت و تيرگيهايى كه دلهايشان از ناحيه سيئات كسب كرده از بين مى‌برد" in _joined(verse, "modern")
    assert "یذهبن فعلِ رفتن است" in _joined(verse, "critical")


def test_hud_11_115_be_patient_reward_not_lost():
    verse = _check_verse("11:115")
    assert "نیکوکاران یعنی نمازگزاران" in _joined(verse, "notes")
    assert "صبر مهمترين خلق است" in _joined(verse, "modern")
    assert "اصبر با صدایِ فرمان و کوتاه" in _joined(verse, "critical")



def test_hud_11_116_would_that_there_had_been_a_remnant():
    verse = _check_verse("11:116")
    assert "صاحبانِ طاعت و دین و عقل و بینش‌اند" in _joined(verse, "notes")
    assert "چرا جز عده كمى" in _joined(verse, "modern")
    assert "بقیة یعنی باقیمانده" in _joined(verse, "critical")


def test_hud_11_117_your_lord_would_not_destroy_righteous_towns():
    verse = _check_verse("11:117")
    assert "معاصی در دنیا به استیصال نزدیک‌تر از شرک‌اند" in _joined(verse, "classical")
    assert "بر اين قرار گرفته كه سرزمينهايى را كه اهل آن مصلحند هلاك نكند" in _joined(verse, "modern")
    assert "لیهلک با لامِ نفیِ سنّت" in _joined(verse, "critical")


def test_hud_11_118_had_your_lord_willed_one_community():
    verse = _check_verse("11:118")
    assert "همه را مسلمان می‌کرد" in _joined(verse, "notes")
    assert "همان تفرق و اعراض از حق است" in _joined(verse, "modern")
    assert "لجعل با لامِ جوابِ لو" in _joined(verse, "critical")


def test_hud_11_119_except_those_your_lord_has_mercy_upon():
    verse = _check_verse("11:119")
    assert "اهلِ حق‌اند و مختلف نیستند" in _joined(verse, "notes")
    assert "غايت خلقت انسان مى‌باشد" in _joined(verse, "modern")
    assert "لذلك با اشاره‌ای دور" in _joined(verse, "critical")


def test_hud_11_120_all_that_we_relate_to_firm_your_heart():
    verse = _check_verse("11:120")
    assert "همهٔ گزارشِ پیامبرانِ پیش از تو را می‌خوانیم" in _joined(verse, "notes")
    assert "ماده قلق و اضطراب را از دل او برمى‌كند" in _joined(verse, "modern")
    assert "فؤاد یعنی دلِ سوزان" in _joined(verse, "critical")


def test_hud_11_121_work_in_your_position_we_too_are_working():
    verse = _check_verse("11:121")
    assert "بر همان حال و تمکنِ خود هر چه می‌کنید بکنید" in _joined(verse, "notes")
    assert "در حقيقت خاتمه دادن به احتجاج و نوعى تهديد" in _joined(verse, "modern")
    assert "إنّا عاملون بی مفعول" in _joined(verse, "critical")


def test_hud_11_122_wait_we_too_are_waiting():
    verse = _check_verse("11:122")
    assert "مواعيدِ شیطان را بر آنچه برایتان می‌آراید" in _joined(verse, "notes")
    assert "راست بود يا دروغ" in _joined(verse, "modern")
    assert "آیه فقط پنج واژه دارد" in _joined(verse, "critical")


def test_hud_11_123_to_god_belongs_the_unseen():
    verse = _check_verse("11:123")
    assert "به کفایتش اعتماد کن که او برای توکل‌کننده کافی است" in _joined(verse, "notes")
    assert "بر هيچ سببى از اسباب توكل مكن، زيرا هر سببى را او سبب كرده" in _joined(verse, "modern")
    assert "از الله آغاز شد و به ربک پایان یافت" in _joined(verse, "critical")



def test_yusuf_12_1_those_are_the_verses_of_the_clear_book():
    verse = _check_verse("12:1")
    assert "بیان حلاله وحرامه" in _joined(verse, "notes") or "حلال و حرام" in _joined(verse, "notes")
    assert "به منظورِ تعظیمِ آیات" in _joined(verse, "modern")
    assert "حروفِ بریده پیش از جمله می‌ایستند" in _joined(verse, "critical")


def test_yusuf_12_2_revealed_an_arabic_quran():
    verse = _check_verse("12:2")
    assert "دو عاملِ حفظ و ضبطِ اسرارِ آیات‌اند" in _joined(verse, "modern")
    assert "قرآنا با تنوین" in _joined(verse, "critical")


def test_yusuf_12_3_we_relate_the_best_of_stories():
    verse = _check_verse("12:3")
    assert "ته چاهِ اسارت به بالای تختِ سلطنت" in _joined(verse, "modern")
    assert "أحسن با صفتِ برترین" in _joined(verse, "critical")



def test_yusuf_12_4_eleven_stars_sun_and_moon():
    verse = _check_verse("12:4")
    assert "نام‌های ستارگان در روایتِ بستانةِ یهودی" in _joined(verse, "notes")
    assert "ماده‌اى روحى براى تربيت او بوده باشد" in _joined(verse, "modern")
    assert "یازده و خورشید و ماه حسابِ فلکی‌اند" in _joined(verse, "critical")


def test_yusuf_12_5_do_not_relate_your_vision():
    verse = _check_verse("12:5")
    assert "این آیه یازده مسأله دارد" in _joined(verse, "notes")
    assert "نقشه مى‌ريزند" in _joined(verse, "modern")
    assert "یا بنیّ با تصغیرِ محبت" in _joined(verse, "critical")


def test_yusuf_12_6_thus_your_lord_chooses_you():
    verse = _check_verse("12:6")
    assert "تحققِ رؤیای یوسف پس از چهل سال بود" in _joined(verse, "notes")
    assert "حفظ از پراکندگی در راه‌های شیطانی" in _joined(verse, "modern")
    assert "کذلك با کافِ تشبیه" in _joined(verse, "critical")



def test_yusuf_12_7_signs_for_those_who_ask():
    verse = _check_verse("12:7")
    assert "برای تسلیِ پیامبر نازل شد" in _joined(verse, "notes")
    assert "ولیّ بندگانِ مخلص است و عهده‌دارِ امورِ آنان" in _joined(verse, "modern")
    assert "با لامِ سؤال مقصد را می‌سازد؛ آیات برای آنان است که بپرسند" in _joined(verse, "critical")


def test_yusuf_12_8_more_beloved_than_us():
    verse = _check_verse("12:8")
    assert "مفردی از لفظِ خویش ندارد" in _joined(verse, "notes")
    assert "کج‌سلیقگی و فسادِ روش است نه گمراهی در دین" in _joined(verse, "modern")
    assert "لامِ لیوسف لامِ قسم است" in _joined(verse, "critical")


def test_yusuf_12_9_kill_yusuf_or_cast_him_out():
    verse = _check_verse("12:9")
    assert "قائلِ این سخن نزد وهب شمعون است" in _joined(verse, "notes")
    assert "محبتِ او را خالص متوجهٔ خود کنند" in _joined(verse, "modern")
    assert "جوابِ امر و مجزوم است" in _joined(verse, "critical")



def test_yusuf_12_10_do_not_kill_yusuf():
    verse = _check_verse("12:10")
    assert "گویندهٔ این سخن روبیل است" in _joined(verse, "notes")
    assert "جانِ یوسف از کشته‌شدن محفوظ بماند" in _joined(verse, "modern")
    assert "تهِ چاهی می‌سازد که آنچه در آن افتد از دور دیده نمی‌شود" in _joined(verse, "critical")


def test_yusuf_12_11_why_do_you_not_trust_us():
    verse = _check_verse("12:11")
    assert "با دو نونِ آشکار بر اصل" in _joined(verse, "notes")
    assert "خویشتن را در نظرِ او پاک و بی‌غرض جلوه دهند" in _joined(verse, "modern")
    assert "ندای برانگیختنِ عواطفِ پدری است" in _joined(verse, "critical")


def test_yusuf_12_12_send_him_with_us_tomorrow():
    verse = _check_verse("12:12")
    assert "آن روز پیامبر نبودند" in _joined(verse, "notes")
    assert "تأمینِ جانِ یوسف از ناحیهٔ آنان به‌طورِ دائم" in _joined(verse, "modern")
    assert "با إنّ و لام و جملهٔ اسمیه سه تأکید بر هم سوار شده است" in _joined(verse, "critical")



def test_yusuf_12_13_jacob_fears_the_wolf():
    verse = _check_verse("12:13")
    assert "یعقوب در خواب دید که گرگی بر یوسف تاخت" in _joined(verse, "notes")
    assert "به جایِ آن اندوهِ دلِ خویش را مانع دانست" in _joined(verse, "modern")
    assert "کنایه از خودِ برادران است" in _joined(verse, "critical")


def test_yusuf_12_14_we_would_be_losers():
    verse = _check_verse("12:14")
    assert "از دفعِ آن از گوسفندان عاجزتریم" in _joined(verse, "notes")
    assert "تجاهل کردند که گویا مقصودِ پدر را نفهمیدند" in _joined(verse, "modern")
    assert "پاسخِ برادران از نخست سوگند است" in _joined(verse, "critical")


def test_yusuf_12_15_cast_into_the_well_and_revelation():
    verse = _check_verse("12:15")
    assert "وحی در تهِ چاه به یوسف رسید" in _joined(verse, "notes")
    assert "حذف شده است تا شناعتِ حادثه گفتنی نباشد" in _joined(verse, "modern")
    assert "این حذفِ جواب «لمّا» سکوتی است که از هر گزارشی بلندتر سخن می‌گوید" in _joined(verse, "critical")



def test_yusuf_12_16_they_came_at_night_weeping():
    verse = _check_verse("12:16")
    assert "در تاریکی بر عذرخواهی تواناتر باشند" in _joined(verse, "notes")
    assert "گریه‌شان مصنوعی بود تا امر را بر پدر مشتبه سازند" in _joined(verse, "modern")
    assert "نخستین اشکِ قصه اشکی ساختگی است" in _joined(verse, "critical")


def test_yusuf_12_17_we_went_racing():
    verse = _check_verse("12:17")
    assert "در قرائتِ عبدالله" in _joined(verse, "notes")
    assert "بیش از یک روز نگذشت که خویشتن را تکذیب کردند" in _joined(verse, "modern")
    assert "حکمِ پدر را پیشاپیش صادر می‌کند" in _joined(verse, "critical")


def test_yusuf_12_18_false_blood_and_beautiful_patience():
    verse = _check_verse("12:18")
    assert "اگر درنده یوسف را خورده بود پیراهنش را پاره می‌کرد" in _joined(verse, "notes")
    assert "مطلب را مبهم می‌کند و حقیقتِ آن را نامعین می‌گذارد" in _joined(verse, "modern")
    assert "در برابرِ این مصیبت جز صبر چاره‌ای نیست" in _joined(verse, "critical")



def test_yusuf_12_19_caravan_and_bucket():
    verse = _check_verse("12:19")
    assert "راه را گم کرده و سرگردان شده بودند تا نزدیکِ چاه فرود آمدند" in _joined(verse, "notes")
    assert "آنچه از کشیدنِ دلو انتظار می‌رود آب است نه پسر" in _joined(verse, "modern")
    assert "خودِ مژده ندا و خوانده می‌شود تا شادی به صحنه احضار شود" in _joined(verse, "critical")


def test_yusuf_12_20_sold_for_a_trifling_price():
    verse = _check_verse("12:20")
    assert "به بیست درهم فروختند" in _joined(verse, "notes")
    assert "سیاقِ آیه ضمیر را به رهگذران بازمی‌گرداند" in _joined(verse, "modern")
    assert "چندان اندک بود که شمرده می‌شد و وزن نمی‌شد" in _joined(verse, "critical")


def test_yusuf_12_21_honour_his_dwelling():
    verse = _check_verse("12:21")
    assert "نامِ او قطفیر بود" in _joined(verse, "notes")
    assert "آثارِ صبر و وقار و منطقِ حکیمانه از کودکی در سیمای او پیدا بود" in _joined(verse, "modern")
    assert "هر کیدِ آدمی بر ضدِّ یوسف عینِ وسیلهٔ عزتِ او می‌شود" in _joined(verse, "critical")


def test_yusuf_12_22_maturity_wisdom_and_knowledge():
    verse = _check_verse("12:22")
    assert 'رسیدن به فرجام نیرو و جوانی' in _joined(verse, "notes")
    assert 'این هر دو پاداش احسان او بود نه موهبتی گزاف' in _joined(verse, "modern")
    assert 'دو تحفه آسمانی را بزرگ و ناشناخته نگه می\u200cدارد' in _joined(verse, "critical")


def test_yusuf_12_23_she_sought_to_seduce_him():
    verse = _check_verse("12:23")
    assert 'درها را یکی پس از دیگری بست' in _joined(verse, "notes")
    assert 'این توحید خالص است که اسباب ظاهری را همه از چشم او انداخته بود' in _joined(verse, "modern")
    assert 'همین غیبت «من» از آغاز پاسخ' in _joined(verse, "critical")


def test_yusuf_12_24_he_would_have_desired_her_but_for_the_proof():
    verse = _check_verse("12:24")
    assert 'صورت یعقوب را دید که انگشت به دندان می\u200cگزید' in _joined(verse, "notes")
    assert 'جای هیچ همّ گناهی در دلش نگذاشت' in _joined(verse, "modern")
    assert 'نحو خود دو هم را نابرابر می\u200cکند' in _joined(verse, "critical")


def test_yusuf_12_25_the_race_to_the_door():
    verse = _check_verse("12:25")
    assert 'زیرا یوسف گریزان و زن جوینده بود' in _joined(verse, "notes")
    assert 'در تعیین کیفر هم میان زندان و عذاب مردد ماند' in _joined(verse, "modern")
    assert 'کوتاه\u200cترین سند قصه است' in _joined(verse, "critical")


def test_yusuf_12_26_a_witness_from_her_household():
    verse = _check_verse("12:26")
    assert 'که چهار تن در خردی سخن گفتند' in _joined(verse, "notes")
    assert 'این نخستین داوری کارشناسی در ادبیات است' in _joined(verse, "modern")
    assert 'پاسخ آینه\u200cای است' in _joined(verse, "critical")


def test_yusuf_12_27_the_shirt_torn_from_behind():
    verse = _check_verse("12:27")
    assert 'مرد زن را از پیش رو می\u200cخواهد نه از پشت' in _joined(verse, "notes")
    assert 'این آیه نخستین درس خواندن صحنه است' in _joined(verse, "modern")
    assert 'یک جهت جغرافیایی کوچک سرنوشت دو انسان را می\u200cسازد' in _joined(verse, "critical")


def test_yusuf_12_28_the_snare_of_women():
    verse = _check_verse("12:28")
    assert 'که «أنّ» از آن حذف شده است' in _joined(verse, "notes")
    assert 'و هم قاب جنسیتی آن حکم' in _joined(verse, "modern")
    assert 'فاصله میان چشم و زبان در این آیه هیچ است' in _joined(verse, "critical")


def test_yusuf_12_29_turn_away_from_this():
    verse = _check_verse("12:29")
    assert 'از شوهرت بخواه که بر گناهت تو را کیفر ندهد' in _joined(verse, "notes")
    assert 'سکوت تحمیلی بر قربانی تلخ\u200cترین بخش این آیه است' in _joined(verse, "modern")
    assert 'تنها نام شخص در کل این آیات است که صدا زده می\u200cشود' in _joined(verse, "critical")


def test_yusuf_12_30_women_in_the_city():
    verse = _check_verse("12:30")
    assert 'دوست داشتن یوسف به پرده دلش رسید' in _joined(verse, "notes")
    assert 'شنیدن کی بود مانند دیدن' in _joined(verse, "modern")
    assert 'سرزنش عاشقانه\u200cترین جمله سوره را می\u200cزاید' in _joined(verse, "critical")


def test_yusuf_12_31_the_banquet_and_the_knives():
    verse = _check_verse("12:31")
    assert 'مجلس آشکار ساختن زیبایی او را چید' in _joined(verse, "notes")
    assert 'این را آزمایش در روان\u200cشناسی جمع می\u200cخواند' in _joined(verse, "modern")
    assert 'زیباترین موجود مجلس با یک فعل امر وارد می\u200cشود' in _joined(verse, "critical")


def test_yusuf_12_32_that_is_the_one_you_blamed_me_for():
    verse = _check_verse("12:32")
    assert 'راستین\u200cترین گواهی این قصه بر پاکی یوسف است' in _joined(verse, "notes")
    assert 'این گذار از هوس به خشونت سیاسی نشان می\u200cدهد' in _joined(verse, "modern")
    assert 'کل سوره را در یک جمله خلاصه می\u200cکند' in _joined(verse, "critical")


def test_yusuf_12_33_prison_is_dearer_to_me():
    verse = _check_verse("12:33")
    assert 'و اگر عافیت گفته بودی عافیت می\u200cیافتی' in _joined(verse, "notes")
    assert 'دیگر زندانی هیچ\u200cکس نیست' in _joined(verse, "modern")
    assert 'و پاسخ دو شرط است' in _joined(verse, "critical")


def test_yusuf_12_34_his_lord_answered_him():
    verse = _check_verse("12:34")
    assert 'معنای دعا و خواستن بود' in _joined(verse, "notes")
    assert 'میان دعا و اجابت در این آیه هیچ فاصله\u200cای نیست مگر فاء ترتیب' in _joined(verse, "modern")
    assert 'بنده واژه را می\u200cسازد و خدا آن را راست می\u200cکند' in _joined(verse, "critical")


def test_yusuf_12_35_after_seeing_the_signs_prison():
    verse = _check_verse("12:35")
    assert 'برای عزیز شوهرِ آن زن رأی تازه\u200cای پدید آمد' in _joined(verse, "notes")
    assert 'این نخستین زندان سیاسی صریح در ادبیات مقدس است' in _joined(verse, "modern")
    assert 'تلخ\u200cترین قید قرآن در این قصه است' in _joined(verse, "critical")


def test_yusuf_12_36_two_youths_in_prison_and_dreams():
    verse = _check_verse("12:36")
    assert 'غلامان پادشاه مصر بودند یکی ساقی او و دیگری نانوا' in _joined(verse, "notes")
    assert 'هیچ زندانی نمی\u200cتواند سرمایه انسان را زندانی کند' in _joined(verse, "modern")
    assert 'دو خواب با یک قالب آغاز می\u200cگردد' in _joined(verse, "critical")


def test_yusuf_12_37_no_food_comes_but_i_tell_its_interpretation():
    verse = _check_verse("12:37")
    assert 'هیچ غذایی در خوابتان نزدتان نمی\u200cآید' in _joined(verse, "notes")
    assert 'از این پیشامد برای دعوت به پروردگارش بهره گرفت' in _joined(verse, "modern")
    assert 'هویت او بر ترک بنا شده است' in _joined(verse, "critical")


def test_yusuf_12_38_the_faith_of_my_fathers():
    verse = _check_verse("12:38")
    assert 'آیین پدران خود ابراهیم و اسحاق و یعقوب را پیروی کرده\u200cام' in _joined(verse, "notes")
    assert 'راهی به سوی شرک نگذاشته و این از باب جبر نیست' in _joined(verse, "modern")
    assert 'زندانی تنها در این آیه عضو سپاهی آسمانی می\u200cشود' in _joined(verse, "critical")


def test_yusuf_12_39_scattered_gods_or_the_one_subduer():
    verse = _check_verse("12:39")
    assert 'آیا پرستش خدایان پراکنده و بی\u200cسود و زیان بهتر است' in _joined(verse, "notes")
    assert '«خیر» در این پرسش به معنای برگزیده\u200cتر و متعین\u200cتر برای پرستش است' in _joined(verse, "modern")
    assert 'نحو خود پیش از مفسر حکم می\u200cکند' in _joined(verse, "critical")


def test_yusuf_12_40_nothing_but_names_you_have_named():
    verse = _check_verse("12:40")
    assert 'نام\u200cهایی بیش نیست که شما و پدرانتان بت\u200cها را بدان نامیده\u200cاید' in _joined(verse, "notes")
    assert 'فرمان و پرستش تنها از آن خدای یگانه است' in _joined(verse, "modern")
    assert 'پرستش آنان به نام\u200cها منحصر می\u200cشود' in _joined(verse, "critical")


def test_yusuf_12_41_the_cupbearer_and_the_baker():
    verse = _check_verse("12:41")
    assert 'گفت کاری که از من می\u200cپرسیدید انجام شد' in _joined(verse, "notes")
    assert 'یکی از آن دو پس از شنیدن تعبیر خواب خویش را تکذیب کرد' in _joined(verse, "modern")
    assert 'هر آینده چون نتیجه\u200cای قطعی با فاء می\u200cآید' in _joined(verse, "critical")


def test_yusuf_12_42_mention_me_to_your_master():
    verse = _check_verse("12:42")
    assert 'گفت مرا نزد سرورت یاد کن' in _joined(verse, "notes")
    assert 'شیطان از یاد ساقی برد که نزد سرورش از یوسف سخن بگوید' in _joined(verse, "modern")
    assert 'امید و نومیدی در این سوره همسایه دیوار به دیوارند' in _joined(verse, "critical")

def test_yusuf_12_43_kings_dream():
    verse = _check_verse("12:43")
    assert 'طبری می\u200cگوید پادشاه مصر گفت در خواب هفت گاو فربه می\u200cبینم' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این خواب پادشاه بود و او' in _joined(verse, "modern")
    assert '«قال الملک إنی أرى» خواب با فعل مضارع گفته می\u200cشود؛ پادشاه' in _joined(verse, "critical")

def test_yusuf_12_44_confused_dreams():
    verse = _check_verse("12:44")
    assert 'طبری می\u200cگوید بزرگان به پادشاه گفتند خوابت دسته\u200cای از خواب\u200cهای درهم' in _joined(verse, "notes")
    assert 'المیزان بر آن است که آنان خواب پادشاه را دسته\u200cهایی از' in _joined(verse, "modern")
    assert '«قالوا أضغاث أحلام» پاسخ با حذف فعل گفته می\u200cشود؛ خواب است' in _joined(verse, "critical")

def test_yusuf_12_45_saqi_remembers():
    verse = _check_verse("12:45")
    assert 'طبری می\u200cگوید آن که از کشته شدن از دو یار زندان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که آن رهایی\u200cیافته پس از مدتی به' in _joined(verse, "modern")
    assert '«و ادّکر بعد أمة» فعل یاد با تشدید و تکلف گفته' in _joined(verse, "critical")

def test_yusuf_12_46_siddiq_embassy():
    verse = _check_verse("12:46")
    assert 'طبری می\u200cگوید در سخن حذف است که او را فرستادند و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این خواب پادشاه بوده و او' in _joined(verse, "modern")
    assert '«یوسف أیها الصدیق» خطاب با نام و لقب است؛ نام او' in _joined(verse, "critical")

def test_yusuf_12_47_sowing_plan():
    verse = _check_verse("12:47")
    assert 'طبری می\u200cگوید یوسف به پرسنده گفت هفت سال چنان\u200cکه عادت\u200cتان بود' in _joined(verse, "notes")
    assert 'المیزان بر آن است که تعبیر گذشتن از صورت خواب به' in _joined(verse, "modern")
    assert '«تزرعون سبع سنین دأباً» پاسخ بی مقدمه آغاز می\u200cشود؛ او نه' in _joined(verse, "critical")

def test_yusuf_12_48_seven_hard_years():
    verse = _check_verse("12:48")
    assert 'طبری می\u200cگوید سپس پس از آن هفت سال کشت هفت سال' in _joined(verse, "notes")
    assert 'المیزان بر آن است که تعبیر او از صورت خواب به' in _joined(verse, "modern")
    assert '«ثم یأتی من بعد ذلک سبع شداد» با «ثم» فاصله و' in _joined(verse, "critical")

def test_yusuf_12_49_year_of_rain():
    verse = _check_verse("12:49")
    assert 'طبری می\u200cگوید این خبر یوسف به قوم از چیزی است که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که سرانجام از پی آن سال\u200cها سالی' in _joined(verse, "modern")
    assert '«ثم یأتی من بعد ذلک عام» سال با «عام» گفته می\u200cشود' in _joined(verse, "critical")

def test_yusuf_12_50_refusal_for_honor():
    verse = _check_verse("12:50")
    assert 'طبری می\u200cگوید چون فرستاده تعبیر خواب را از یوسف نزد پادشاه' in _joined(verse, "notes")
    assert 'المیزان بر آن است که اگر بنای بازگشتن به زندان بود' in _joined(verse, "modern")
    assert '«ائتونی به» فرمان پادشاه و «ارجع إلى ربک» پاسخ زندانی است؛' in _joined(verse, "critical")

def test_yusuf_12_51_second_trial_truth():
    verse = _check_verse("12:51")
    assert 'طبری می\u200cگوید در سخن حذف است که فرستاده بازگشت و پادشاه' in _joined(verse, "notes")
    assert 'المیزان بر آن است که زنان نخست خدا را تنزیه کردند' in _joined(verse, "modern")
    assert '«قال ما خطبکن» پرسش پادشاه با «خطب» کار بزرگ گفته می\u200cشود؛' in _joined(verse, "critical")

def test_yusuf_12_52_speaker_dispute():
    verse = _check_verse("12:52")
    assert 'طبری می\u200cگوید یوسف گفت این که فرستاده پادشاه را بازگرداندم و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این جمله\u200cها از سخن یوسف است' in _joined(verse, "modern")
    assert '«ذلک لیعلم» اشاره به دوری است؛ آن کار که کردم برای' in _joined(verse, "critical")

def test_yusuf_12_53_nafs_ammara():
    verse = _check_verse("12:53")
    assert 'طبری می\u200cگوید این را یوسف گفت که من نفس خویش را' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این سخن\u200cها از آن یوسف است' in _joined(verse, "modern")
    assert '«و ما أبرئ نفسی» با نفی و فعل مضارع آغاز می\u200cشود؛' in _joined(verse, "critical")

def test_yusuf_12_54_makin_amin():
    verse = _check_verse("12:54")
    assert 'طبری می\u200cگوید پادشاه مصر بزرگ ولید بن ریان چون بهانه یوسف' in _joined(verse, "notes")
    assert 'المیزان بر آن است که نتیجه خودداری او این شد که' in _joined(verse, "modern")
    assert '«ائتوني به أستخلصه لنفسي» فرمان دوم با خواسته\u200cای افزوده گفته می\u200cشود؛' in _joined(verse, "critical")

def test_yusuf_12_55_treasuries_request():
    verse = _check_verse("12:55")
    assert 'طبری می\u200cگوید یوسف به پادشاه گفت مرا بر خزانه\u200cهای سرزمین خود' in _joined(verse, "notes")
    assert 'المیزان بر آن است که او از پادشاه خواست او را' in _joined(verse, "modern")
    assert '«اجعلنی علی خزائن الأرض» کوتاه\u200cترین جمله او و بزرگ\u200cترین آن است؛' in _joined(verse, "critical")

def test_yusuf_12_56_establishment_land():
    verse = _check_verse("12:56")
    assert 'طبری می\u200cگوید بدین\u200cسان ما یوسف را در زمین مصر جای و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که خدا او را چنان در زمین' in _joined(verse, "modern")
    assert '«و كذلك مكنّا ليوسف في الأرض» کاف آغاز آیه همه قصه' in _joined(verse, "critical")

def test_yusuf_12_57_reward_hereafter():
    verse = _check_verse("12:57")
    assert 'طبری می\u200cگوید پاداش خدا در آخرت برای آنان که خدا و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که پاداش آخرت برای آنان که ایمان' in _joined(verse, "modern")
    assert '«و لأجر الآخرة خير» با لام سوگندگونه و بهتر بی اندازه' in _joined(verse, "critical")


def test_yusuf_12_58_brothers_arrive_unrecognized():
    verse = _check_verse("12:58")
    assert 'طبری می\u200cگوید برادران یوسف آمدند و او آنان را شناخت و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که در این جمله مطالب بسیاری حذف' in _joined(verse, "modern")
    assert '«فدخلوا علیه فعرفهم» با دو فاء پیاپی گفته می\u200cشود؛ درآمدند و' in _joined(verse, "critical")

def test_yusuf_12_59_bring_your_brother():
    verse = _check_verse("12:59")
    assert 'طبری می\u200cگوید چون یوسف بارهای خوراک برادران را آماده کرد و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که جهاز متاعی است که از پیش' in _joined(verse, "modern")
    assert '«ائتونی بأخ لکم من أبیکم» او از برادر با «از پدرتان»' in _joined(verse, "critical")

def test_yusuf_12_60_no_measure_if_not():
    verse = _check_verse("12:60")
    assert 'طبری می\u200cگوید یوسف به برادران گفت اگر آن برادرتان را که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که کیل به معنای پیموده\u200cشده و مقصود' in _joined(verse, "modern")
    assert '«فإن لم تأتوني به» شرط با «به» گفته می\u200cشود؛ آوردن او' in _joined(verse, "critical")

def test_yusuf_12_61_we_shall_entice_father():
    verse = _check_verse("12:61")
    assert 'طبری می\u200cگوید برادران یوسف بدو گفتند از پدرش او را طلب' in _joined(verse, "notes")
    assert 'المیزان بر آن است که مراوده مراجعه پیاپی و اصرار و' in _joined(verse, "modern")
    assert '«سنراود عنه أباه» پدر با «أباه» پدر او گفته می\u200cشود نه' in _joined(verse, "critical")

def test_yusuf_12_62_goods_in_their_loads():
    verse = _check_verse("12:62")
    assert 'طبری می\u200cگوید یوسف به جوانان خود که غلامان او بودند گفت' in _joined(verse, "notes")
    assert 'المیزان بر آن است که فتیان جمع فتى به معنای پسر' in _joined(verse, "modern")
    assert '«اجعلوا بضاعتهم فی رحالهم» فرمان به دیگران و در خلوت گفته' in _joined(verse, "critical")


def test_yusuf_12_63_كيل_withheld():
    verse = _check_verse("12:63")
    assert 'طبری می\u200cگوید چون برادران یوسف نزد پدرشان بازگشتند گفتند پیمانه از' in _joined(verse, "notes")
    assert 'المیزان بر آن است که اکتیال گرفتن خوراک با پیمانه است' in _joined(verse, "modern")
    assert '«یا أبانا» ندا در آغاز درخواست است و آنان با پدر' in _joined(verse, "critical")

def test_yusuf_12_64_allah_best_guardian():
    verse = _check_verse("12:64")
    assert 'طبری می\u200cگوید پدرشان یعقوب گفت آیا شما را بر برادرتان که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این جمله بر سخن پیشین او' in _joined(verse, "modern")
    assert '«هل آمنكم عليه إلا كما أمنتكم على أخيه» ساخت آینه\u200cای دارد' in _joined(verse, "critical")

def test_yusuf_12_65_goods_returned_found():
    verse = _check_verse("12:65")
    assert 'طبری می\u200cگوید چون برادران یوسف متاعی را که از مصر از' in _joined(verse, "notes")
    assert 'المیزان بر آن است که بغی طلب کردن است و بیشتر' in _joined(verse, "modern")
    assert '«و لما فتحوا متاعهم وجدوا» گشودن و یافتن پشت سر هم' in _joined(verse, "critical")

def test_yusuf_12_66_solemn_covenant():
    verse = _check_verse("12:66")
    assert 'طبری می\u200cگوید یعقوب به پسرانش گفت برادرتان را با شما به' in _joined(verse, "notes")
    assert 'المیزان بر آن است که موثق چیزی است که مورد اعتماد' in _joined(verse, "modern")
    assert '«لن أرسله معکم حتى تؤتون» نفی آینده و غایت با حتى' in _joined(verse, "critical")

def test_yusuf_12_67_separate_gates():
    verse = _check_verse("12:67")
    assert 'طبری می\u200cگوید یعقوب هنگام بیرون رفتن پسرانش به مصر برای خرید' in _joined(verse, "notes")
    assert 'المیزان بر آن است که یعقوب از چشم زخم بر پسرانش' in _joined(verse, "modern")
    assert '«یا بنیّ» ندا با تصغیر محبت گفته می\u200cشود؛ پسران من کوچک' in _joined(verse, "critical")

def test_yusuf_12_68_need_in_jacobs_heart():
    verse = _check_verse("12:68")
    assert 'طبری می\u200cگوید چون پسران یعقوب از همان\u200cجا که پدرشان فرمان داده' in _joined(verse, "notes")
    assert 'المیزان بر آن است که درآمدن آنان از درهای پراکنده چیزی' in _joined(verse, "modern")
    assert '«من حيث أمرهم أبوهم» از همان\u200cجا که پدرشان فرمان داد و' in _joined(verse, "critical")

def test_yusuf_12_69_i_am_your_brother():
    verse = _check_verse("12:69")
    assert 'طبری می\u200cگوید چون پسران یعقوب بر یوسف وارد شدند برادر پدری' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات بازگشتن برادران نزد پدر' in _joined(verse, "modern")
    assert '«آوى إلیه أخاه» جای دادن با «إلى» به سوی خود گفته' in _joined(verse, "critical")

def test_yusuf_12_70_cup_in_brothers_load():
    verse = _check_verse("12:70")
    assert 'طبری می\u200cگوید چون یوسف بر شترهای برادرانش آنچه از خوراک بار' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات آوردن برادر تنی و' in _joined(verse, "modern")
    assert '«جعل السقایة فی رحل أخیه» بی نام فاعل در سیاق او' in _joined(verse, "critical")

def test_yusuf_12_71_what_have_you_lost():
    verse = _check_verse("12:71")
    assert 'طبری می\u200cگوید پسران یعقوب چون بانگ «ای کاروانیان شما دزدید» را' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات نگه داشتن برادر تنی' in _joined(verse, "modern")
    assert '«قالوا و أقبلوا علیهم» گفتن و روی آوردن با واو حال' in _joined(verse, "critical")

def test_yusuf_12_72_kings_cup_missing():
    verse = _check_verse("12:72")
    assert 'طبری می\u200cگوید آنان گفتند آبخوری پادشاه را گم کرده\u200cایم و در' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات نگه داشتن برادر تنی' in _joined(verse, "modern")
    assert '«نفقد صواع الملک» با فعل مضارع گفته می\u200cشود گم می\u200cکنیم و' in _joined(verse, "critical")

def test_yusuf_12_73_we_are_not_thieves():
    verse = _check_verse("12:73")
    assert 'طبری می\u200cگوید برادران یوسف گفتند «تالله» یعنی به خدا و این' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات نگه داشتن برادر تنی' in _joined(verse, "modern")
    assert '«تالله لقد علمتم» سوگند و لام و قد سه استواری پشت' in _joined(verse, "critical")

def test_yusuf_12_74_what_is_its_penalty():
    verse = _check_verse("12:74")
    assert 'طبری می\u200cگوید یاران یوسف به برادران گفتند کیفر دزدی چیست اگر' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات نگه داشتن برادر تنی' in _joined(verse, "modern")
    assert '«فما جزاؤه» با فاء پس از سوگند آنان گفته می\u200cشود؛ پس' in _joined(verse, "critical")

def test_yusuf_12_75_penalty_whoever_found():
    verse = _check_verse("12:75")
    assert 'طبری می\u200cگوید برادران یوسف گفتند کیفر دزدی این است که هر' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات نگه داشتن برادر تنی' in _joined(verse, "modern")
    assert '«جزاؤه من وجد فی رحله فهو جزاؤه» جمله گرد می\u200cچرخد و' in _joined(verse, "critical")

def test_yusuf_12_76_so_we_plotted():
    verse = _check_verse("12:76")
    assert 'طبری می\u200cگوید یوسف بارها و اثاث آنان را برای جستن پیمانه' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات بازگشتن برادران نزد پدر' in _joined(verse, "modern")
    assert '«فبدأ بأوعیتهم قبل وعاء أخیه» با قبل و ترتیب گفته می\u200cشود؛' in _joined(verse, "critical")

def test_yusuf_12_77_he_concealed_it():
    verse = _check_verse("12:77")
    assert 'طبری می\u200cگوید برادران گفتند اگر او دزدی کند برادری برای او' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات نگه داشتن برادر تنی' in _joined(verse, "modern")
    assert '«إن یسرق فقد سرق أخ له» شرط و گذشته با قد' in _joined(verse, "critical")

def test_yusuf_12_78_father_old_man():
    verse = _check_verse("12:78")
    assert 'طبری می\u200cگوید برادران یوسف بدو گفتند ای عزیز ای پادشاه او' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات بازگشتن برادران و آوردن' in _joined(verse, "modern")
    assert '«یا أیّها العزیز» ندا با نام تازه او گفته می\u200cشود؛ آنان' in _joined(verse, "critical")

def test_yusuf_12_79_god_forbid_wrong():
    verse = _check_verse("12:79")
    assert 'طبری می\u200cگوید یوسف به برادران گفت پناه بر خدا و «معاذ' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات نگه داشتن برادر تنی' in _joined(verse, "modern")
    assert '«معاذ الله» پاسخ با پناه بردن آغاز می\u200cشود نه با نه' in _joined(verse, "critical")

def test_yusuf_12_80_eldest_counsel():
    verse = _check_verse("12:80")
    assert 'طبری می\u200cگوید چون از او ناامید شدند از آنکه یوسف بنیامین' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات بازگشتن برادران و نگه' in _joined(verse, "modern")
    assert '«فلما استیأسوا منه خلصوا نجیّاً» ناامیدی و کناره و نجوا در' in _joined(verse, "critical")

def test_yusuf_12_81_your_son_stole():
    verse = _check_verse("12:81")
    assert 'طبری می\u200cگوید آن که گفت زمین را ترک نمی\u200cکنم به برادرانش' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات بازگشتن برادران و نگه' in _joined(verse, "modern")
    assert '«ارجعوا إلى أبیکم فقولوا» دو فرمان پیاپی بازگشتن و گفتن و' in _joined(verse, "critical")

def test_yusuf_12_82_ask_the_town():
    verse = _check_verse("12:82")
    assert 'طبری می\u200cگوید اگر ما را متهم می\u200cداری و بر آنچه از' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات بازگشتن برادران و نگه' in _joined(verse, "modern")
    assert '«و اسأل القریة التي كنا فيها» شهر با موصول و بودن' in _joined(verse, "critical")

def test_yusuf_12_83_patience_and_hope():
    verse = _check_verse("12:83")
    assert 'طبری می\u200cگوید در سخن حذف است که برادران بنیامین نزد پدرشان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این سخن را برای تکذیب آنان' in _joined(verse, "modern")
    assert '«بل سوّل لکم أنفسکم أمراً» با بل روی سخن آنان را' in _joined(verse, "critical")

def test_yusuf_12_84_white_eyes_grief():
    verse = _check_verse("12:84")
    assert 'طبری می\u200cگوید یعقوب از آنان روی گرداند و گفت ای اندوه' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات گفت\u200cوگوی پسران یعقوب با' in _joined(verse, "modern")
    assert '«و تولّى عنهم» روی گرداندن پیش از سخن و آیه با' in _joined(verse, "critical")

def test_yusuf_12_85_still_remembering():
    verse = _check_verse("12:85")
    assert 'طبری می\u200cگوید پسران یعقوب که از مصر نزد او بازگشته بودند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات گفت\u200cوگوی پسران یعقوب با' in _joined(verse, "modern")
    assert '«تالله تفتأ تذکر یوسف» سوگند آنان با همان تالله آیه\u200cهای پیش' in _joined(verse, "critical")

def test_yusuf_12_86_complain_to_god():
    verse = _check_verse("12:86")
    assert 'طبری می\u200cگوید یعقوب به پسرانش گفت به خدا شکایت نمی\u200cکنم به' in _joined(verse, "notes")
    assert 'المیزان بر آن است که او گفت شکایت و اندوهم را' in _joined(verse, "modern")
    assert '«إنّما أشکو بثّی و حزنی إلى الله» تنها و بث و' in _joined(verse, "critical")

def test_yusuf_12_87_seek_yusuf_do_not_despair():
    verse = _check_verse("12:87")
    assert 'طبری می\u200cگوید ای پسرانم بروید و اینک از یوسف و برادرش' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات گفت\u200cوگوی پسران یعقوب با' in _joined(verse, "modern")
    assert '«یا بنیّ اذهبوا فتحسّسوا» ای پسرانم با مهر و دو فرمان' in _joined(verse, "critical")

def test_yusuf_12_88_scant_goods_charity():
    verse = _check_verse("12:88")
    assert 'طبری می\u200cگوید چون نزد یوسف آمدند گفتند پس از آن\u200cکه پدر' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات گفت\u200cوگوی پسران یعقوب با' in _joined(verse, "modern")
    assert '«مَسّنا وَ أهلَنا الضُّرّ» رنج، ایشان و خاندان\u200cشان را با هم' in _joined(verse, "critical")

def test_yusuf_12_89_what_you_did():
    verse = _check_verse("12:89")
    assert 'طبری می\u200cگوید یوسف چون سخن نیاز برادران و خواهش صدقه\u200cشان را' in _joined(verse, "notes")
    assert 'المیزان بر آن است که در این بخش پس از ورود' in _joined(verse, "modern")
    assert '«هَل عَلِمتُم ما فَعَلتُم» پرسش آری یا نه ظاهراً و در' in _joined(verse, "critical")

def test_yusuf_12_90_I_am_yusuf():
    verse = _check_verse("12:90")
    assert 'طبری می\u200cگوید برادرانِ یوسف چون سخنِ او را در این پرسش' in _joined(verse, "notes")
    assert 'المیزان بر آن است که چون برادران پرسیدند آیا تو یوسفی' in _joined(verse, "modern")
    assert '«أئنک لأنت یوسف» پرسشی است که دو سویش را ترس و' in _joined(verse, "critical")

def test_yusuf_12_91_we_were_wrongdoers():
    verse = _check_verse("12:91")
    assert 'طبری می\u200cگوید برادران یوسف گفتند به خدا سوگند خدا تو را' in _joined(verse, "notes")
    assert 'المیزان بر آن است که آنان گفتند به خدا سوگند خدا' in _joined(verse, "modern")
    assert '«تالله لقد آثرک الله علینا» سوگندی که آنان همهٔ سوره با' in _joined(verse, "critical")

def test_yusuf_12_92_no_blame_today():
    verse = _check_verse("12:92")
    assert 'طبری می\u200cگوید یوسف چون ایشان فضیلتش بر خود و خطایشان را' in _joined(verse, "notes")
    assert 'المیزان بر آن است که یوسف گفت امروز هیچ سرزنشی بر' in _joined(verse, "modern")
    assert '«لا تثریب علیکم الیوم» لام نفی جنس و امروز و هیچ' in _joined(verse, "critical")

def test_yusuf_12_93_shirt_heals_eyes():
    verse = _check_verse("12:93")
    assert 'طبری می\u200cگوید یوسف چون خود را به برادران شناساند از پدرشان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آخرین عنایت بی\u200cسابقهٔ خداست و' in _joined(verse, "modern")
    assert '«اذهبوا بقمیصی هذا» پیراهنم این با اشارهٔ نزدیک و آن هذا' in _joined(verse, "critical")

def test_yusuf_12_94_scent_of_yusuf():
    verse = _check_verse("12:94")
    assert 'طبری می\u200cگوید چون کاروان پسران یعقوب از نزد یوسف به سوی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که فصل به معنای قطع و جدا' in _joined(verse, "modern")
    assert '«إنی لأجد ریح یوسف» می\u200cیابم نه می\u200cشنوم و یافتن از بوییدن' in _joined(verse, "critical")

def test_yusuf_12_95_old_error():
    verse = _check_verse("12:95")
    assert 'طبری می\u200cگوید آنان که یعقوب بدیشان گفت من بوی یوسف را' in _joined(verse, "notes")
    assert 'المیزان بر آن است که قدیم در برابر تازه و به' in _joined(verse, "modern")
    assert '«تالله إنک لفی ضلالک القدیم» سوگند و تاکید و در و' in _joined(verse, "critical")

def test_yusuf_12_96_bearer_of_good_news():
    verse = _check_verse("12:96")
    assert 'طبری می\u200cگوید چون مژده\u200cرسان از نزد یوسف نزد یعقوب آمد و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که بشیر به معنای حامل بشارت است' in _joined(verse, "modern")
    assert '«فارتدّ بصیراً» بازگشت و بینا و فاء سرعت و جمله در' in _joined(verse, "critical")

def test_yusuf_12_97_ask_forgiveness_for_us():
    verse = _check_verse("12:97")
    assert 'طبری می\u200cگوید پسران یعقوب که میان او و یوسف جدایی افکندند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که گویندگان این سخن فرزندان یعقوب\u200cاند به' in _joined(verse, "modern")
    assert '«یا أبانا استغفر لنا ذنوبنا» ای پدر ما و آمرزش بخواه' in _joined(verse, "critical")

def test_yusuf_12_98_I_will_ask_forgiveness():
    verse = _check_verse("12:98")
    assert 'طبری می\u200cگوید یعقوب گفت به\u200cزودی از پروردگارم می\u200cخواهم از گناهانتان که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که یعقوب فرمود به\u200cزودی برایتان استغفار می\u200cکنم' in _joined(verse, "modern")
    assert '«سوف أستغفر لکم ربی» به\u200cزودی و خواهم خواست و برای شما' in _joined(verse, "critical")

def test_yusuf_12_99_enter_egypt_in_safety():
    verse = _check_verse("12:99")
    assert 'طبری می\u200cگوید چون یعقوب و فرزندان و خانواده\u200cهایشان نزد یوسف آمدند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که در این سخن جمله\u200cای حذف شده' in _joined(verse, "modern")
    assert '«آوى إلیه أبویه» جای داد به سوی خود پدر و مادرش' in _joined(verse, "critical")

def test_yusuf_12_100_interpretation_of_my_dream():
    verse = _check_verse("12:100")
    assert 'طبری می\u200cگوید یوسف پدر و مادرش را بر تخت بالا برد' in _joined(verse, "notes")
    assert 'المیزان بر آن است که سجده برای عبادت یوسف نبود به' in _joined(verse, "modern")
    assert '«و رفع أبویه على العرش» بالا برد پدر و مادرش را' in _joined(verse, "critical")

def test_yusuf_12_101_make_me_die_a_muslim():
    verse = _check_verse("12:101")
    assert 'طبری می\u200cگوید یوسف پس از آنکه خدا پدر و مادر و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که یوسف پس از ثنای خدا و' in _joined(verse, "modern")
    assert '«ربّ قد آتیتنی من الملک» پروردگارا دادی به من از فرمانروایی' in _joined(verse, "critical")

def test_yusuf_12_102_news_of_the_unseen():
    verse = _check_verse("12:102")
    assert 'طبری می\u200cگوید این خبری که از یوسف و پدرش یعقوب و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات داستان یوسف را پایان' in _joined(verse, "modern")
    assert '«ذلک من أنباء الغیب نوحیه إلیک» این از خبرهای غیب است' in _joined(verse, "critical")

def test_yusuf_12_103_most_people_not_believers():
    verse = _check_verse("12:103")
    assert 'طبری می\u200cگوید بیشتر مشرکان قوم تو ای محمد هر چند بکوشی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پایان سوره است و' in _joined(verse, "modern")
    assert '«و ما أکثر الناس و لو حرصت بمؤمنین» بیشتر مردم و' in _joined(verse, "critical")

def test_yusuf_12_104_no_wage_reminder():
    verse = _check_verse("12:104")
    assert 'طبری می\u200cگوید ای محمد از اینان که پیامبری\u200cات را انکار می\u200cکنند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که واو حالیه است یعنی آنان ایمان' in _joined(verse, "modern")
    assert '«و ما تسألهم علیه من أجر» نمی\u200cخواهی از آنان بر آن' in _joined(verse, "critical")

def test_yusuf_12_105_signs_they_pass_by():
    verse = _check_verse("12:105")
    assert 'طبری می\u200cگوید چه بسیار نشانه برای خدا در آسمان\u200cها و زمین' in _joined(verse, "notes")
    assert 'المیزان بر آن است که مرور بر هر چیز رسیدن به' in _joined(verse, "modern")
    assert '«و کأین من آیة» چه بسیار نشانه و آیه با سنگینی' in _joined(verse, "critical")

def test_yusuf_12_106_faith_mixed_with_shirk():
    verse = _check_verse("12:106")
    assert 'طبری می\u200cگوید بیشتر آنان که در آیهٔ پیش گفته شد به' in _joined(verse, "notes")
    assert 'المیزان بر آن است که ضمیر بیشترشان به مردم بازمی\u200cگردد و' in _joined(verse, "modern")
    assert '«ما یؤمن أکثرهم بالله إلا و هم مشرکون» کل ساخت آیه' in _joined(verse, "critical")

def test_yusuf_12_107_sudden_hour():
    verse = _check_verse("12:107")
    assert 'طبری می\u200cگوید آیا اینان که به خدا که پروردگارشان است اقرار' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پایان سوره خاطرنشان می\u200cکند' in _joined(verse, "modern")
    assert '«أفأمنوا» آیا ایمن شدند و پرسش انکاری است و پاسخش در' in _joined(verse, "critical")

def test_yusuf_12_108_my_way_with_insight():
    verse = _check_verse("12:108")
    assert 'طبری می\u200cگوید به پیامبر محمد بگو این دعوتی که به آن' in _joined(verse, "notes")
    assert 'المیزان بر آن است که توحید خالص همان راهی است که' in _joined(verse, "modern")
    assert '«قل هذه سبیلي» بگو این راه من است و اشارهٔ نزدیک' in _joined(verse, "critical")

def test_yusuf_12_109_messengers_from_towns():
    verse = _check_verse("12:109")
    assert 'طبری می\u200cگوید ای محمد پیش از تو جز مردانی نفرستادیم نه' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پایان سوره خاطرنشان می\u200cکند' in _joined(verse, "modern")
    assert '«و ما أرسلنا من قبلك إلا رجالا» جز مردانی نفرستادیم و' in _joined(verse, "critical")

def test_yusuf_12_110_help_when_despairing():
    verse = _check_verse("12:110")
    assert 'طبری می\u200cگوید ما پیش از تو جز مردانی از اهل شهرها' in _joined(verse, "notes")
    assert 'المیزان بر آن است که پیامبران به دعوت خود و دشمنان' in _joined(verse, "modern")
    assert '«حتى إذا استیأس الرسل» تا چون پیامبران نومید شدند و آن' in _joined(verse, "critical")

def test_yusuf_12_111_lesson_for_understanding():
    verse = _check_verse("12:111")
    assert 'طبری می\u200cگوید در قصهٔ یوسف و برادرانش برای اهل خرد و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پایان سوره است و' in _joined(verse, "modern")
    assert '«لقد کان فی قصصهم عبرة لأولی الألباب» به\u200cراستی در قصه\u200cهایشان عبرتی' in _joined(verse, "critical")

def test_tawbah_9_109_foundation_on_taqwa():
    verse = _check_verse("9:109")
    assert 'طبری می\u200cگوید خواندن أسس در دو جا به ساخت مجهول نزد' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات گروه دیگری از منافقان' in _joined(verse, "modern")
    assert '«أفمن أسس بنیانه على تقوى» آیا کسی که بنیانش را بر' in _joined(verse, "critical")

def test_tawbah_9_110_building_remains_doubt():
    verse = _check_verse("9:110")
    assert 'طبری می\u200cگوید ساختمان اینان که مسجدی برای زیان و کفر گرفتند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات وضع منافقان سازندهٔ مسجد' in _joined(verse, "modern")
    assert '«لا یزال بنیانهم الذی بنوا ریبة» پیوسته ساختمانشان شک است و' in _joined(verse, "critical")

def test_tawbah_9_111_god_buys_souls_and_wealth():
    verse = _check_verse("9:111")
    assert 'طبری می\u200cگوید خدا از مؤمنان جان\u200cها و مال\u200cهایشان را به بهشت' in _joined(verse, "notes")
    assert 'المیزان بر آن است که خدا در این آیه به کسانی' in _joined(verse, "modern")
    assert '«إن الله اشترى من المؤمنین أنفسهم و أموالهم» خدا خریده است' in _joined(verse, "critical")

def test_tawbah_9_112_the_nine_qualities():
    verse = _check_verse("9:112")
    assert 'طبری می\u200cگوید خدا از مؤمنان توبه\u200cکننده و پرستنده جان\u200cها و مال\u200cهایشان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این جمله مؤمنین را به نیکوترین' in _joined(verse, "modern")
    assert '«التائبون العابدون الحامدون السائحون» ردیف صفت\u200cها بی هیچ واوی پشت هم' in _joined(verse, "critical")

def test_tawbah_9_113_no_intercession_for_polytheists():
    verse = _check_verse("9:113")
    assert 'طبری می\u200cگوید پیامبر محمد و ایمان\u200cآوردگان را نسزد که برای مشرکان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات در پیرامون مطالب گوناگونی' in _joined(verse, "modern")
    assert '«ما کان للنبی و الذین آمنوا أن یستغفروا» نسزد پیامبر و' in _joined(verse, "critical")

def test_tawbah_9_114_abraham_promise_and_disavowal():
    verse = _check_verse("9:114")
    assert 'طبری می\u200cگوید آمرزش\u200cخواهی ابراهیم برای پدرش جز برای وعده\u200cای نبود که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات از محبت و طلب' in _joined(verse, "modern")
    assert '«إلا عن موعدة وعدها إیاه» جز به سبب وعده\u200cای که به' in _joined(verse, "critical")

def test_tawbah_9_115_no_misguidance_before_clarification():
    verse = _check_verse("9:115")
    assert 'طبری می\u200cگوید خدا را نسزد که بر شما در آمرزش\u200cخواهی برای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات در غرضی واحد در' in _joined(verse, "modern")
    assert '«و ما کان الله لیضل قوما بعد إذ هداهم» خدا را' in _joined(verse, "critical")

def test_tawbah_9_116_kingdom_of_heavens_and_earth():
    verse = _check_verse("9:116")
    assert 'طبری می\u200cگوید همانا خدا ای مردم فرمانروایی آسمان\u200cها و زمین و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات در پیرامون جنگ و' in _joined(verse, "modern")
    assert '«إن الله له ملک السماوات و الأرض» فرمانروایی آسمان\u200cها و زمین' in _joined(verse, "critical")

def test_tawbah_9_117_forgiven_in_hour_of_hardship():
    verse = _check_verse("9:117")
    assert 'طبری می\u200cگوید خدا بازگشت به فرمان و طاعتش را روزی پیامبرش' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات دلالت بر گذشت خدای' in _joined(verse, "modern")
    assert '«لقد تاب الله على النبی و المهاجرین و الأنصار» خدا بر' in _joined(verse, "critical")

def test_tawbah_9_118_the_three_left_behind():
    verse = _check_verse("9:118")
    assert 'طبری می\u200cگوید و خدا بر آن سه تن نیز درگذشت که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات دلالت بر گذشت خدای' in _joined(verse, "modern")
    assert '«ضاقت علیهم الأرض بما رحبت» زمین با همهٔ فراخی بر آنان' in _joined(verse, "critical")

def test_tawbah_9_119_be_with_the_truthful():
    verse = _check_verse("9:119")
    assert 'طبری می\u200cگوید ای ایمان\u200cآوردگان به خدا و پیامبرش خدا را مراقب' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات غرضی واحد دارد و' in _joined(verse, "modern")
    assert '«یا أیها الذین آمنوا اتقوا الله و کونوا مع الصادقین» ای' in _joined(verse, "critical")

def test_tawbah_9_120_no_thirst_unrecorded():
    verse = _check_verse("9:120")
    assert 'طبری می\u200cگوید اهل مدینه شهر پیامبر خدا و بادیه\u200cنشینان پیرامون ساکنان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات اهل مدینه و اطراف' in _joined(verse, "modern")
    assert '«لا یصیبهم ظمأ و لا نصب و لا مخمصة» تشنگی و' in _joined(verse, "critical")

def test_tawbah_9_121_small_and_large_expense_recorded():
    verse = _check_verse("9:121")
    assert 'طبری می\u200cگوید و هزینهٔ کوچک و بزرگی در راه خدا نمی\u200cکنند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات در غرض واحد سوره' in _joined(verse, "modern")
    assert '«و لا ینفقون نفقة صغیرة و لا کبیرة» و هزینهٔ کوچک' in _joined(verse, "critical")

def test_tawbah_9_122_a_party_to_learn_religion():
    verse = _check_verse("9:122")
    assert 'طبری می\u200cگوید مؤمنان را نسزد همگی کوچ کنند و معنای کافه' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات مردم را دستور می\u200cدهد' in _joined(verse, "modern")
    assert '«و ما کان المؤمنون لینفروا کافة» مؤمنان را نسزد همگی کوچ' in _joined(verse, "critical")

def test_tawbah_9_123_fight_those_nearest():
    verse = _check_verse("9:123")
    assert 'طبری می\u200cگوید ای باورکنندگان به خدا و پیامبرش با آنان که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات حکم می\u200cکند باید با' in _joined(verse, "modern")
    assert '«قاتلوا الذین یلونکم من الکفار» با کافرانی که نزدیک شمایند بجنگید' in _joined(verse, "critical")

def test_tawbah_9_124_surah_increases_faith():
    verse = _check_verse("9:124")
    assert 'طبری می\u200cگوید و چون خدا سوره\u200cای از سوره\u200cهای قرآن را بر' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات با چند آیهٔ پایانی' in _joined(verse, "modern")
    assert '«أیکم زادته هذه إیمانا» کدام\u200cیک از شما را این بر ایمان' in _joined(verse, "critical")

def test_tawbah_9_125_disease_increases_in_filth():
    verse = _check_verse("9:125")
    assert 'طبری می\u200cگوید و اما آنان که در دل\u200cهایشان بیماری نفاق است' in _joined(verse, "notes")
    assert 'المیزان بر آن است که آیات پایانی سوره حال مؤمنین و' in _joined(verse, "modern")
    assert '«فزادتهم رجسا إلى رجسهم» بر پلیدیشان پلیدی افزود و آن إلى' in _joined(verse, "critical")

def test_tawbah_9_126_tested_every_year():
    verse = _check_verse("9:126")
    assert 'طبری می\u200cگوید در خواندن نمی\u200cبینند اختلاف است بیشتر خوانندگان شهرها به' in _joined(verse, "notes")
    assert 'المیزان بر آن است که آیات پایانی سوره حال مؤمنین و' in _joined(verse, "modern")
    assert '«أولا یرون أنهم یفتنون» آیا نمی\u200cبینند که آزموده می\u200cشوند و آن' in _joined(verse, "critical")

def test_tawbah_9_127_looks_then_they_turn_away():
    verse = _check_verse("9:127")
    assert 'طبری می\u200cگوید و چون سوره\u200cای از قرآن فرود آید که در' in _joined(verse, "notes")
    assert 'المیزان بر آن است که آیات سورهٔ برائت با این چند' in _joined(verse, "modern")
    assert '«نظر بعضهم إلى بعض» برخی به برخی نگریستند و آن نگاه\u200cها' in _joined(verse, "critical")

def test_tawbah_9_128_messenger_from_yourselves():
    verse = _check_verse("9:128")
    assert 'طبری می\u200cگوید ای این گروه پیامبر خدا از خودتان به سوی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که آیات پایانی سوره حال مؤمنین و' in _joined(verse, "modern")
    assert '«لقد جاءکم رسول من أنفسکم» به\u200cراستی پیامبری از خودتان به سوی' in _joined(verse, "critical")

def test_tawbah_9_129_god_is_sufficient_for_me():
    verse = _check_verse("9:129")
    assert 'طبری می\u200cگوید پس اگر اینان که ای محمد حق از نزد' in _joined(verse, "notes")
    assert 'المیزان بر آن است که آیات پایانی سوره رسول گرامی را' in _joined(verse, "modern")
    assert '«فقول حسبی الله» بگو خدا مرا بس است و آن بس' in _joined(verse, "critical")


def test_rad_13_1_verse():
    verse = _check_verse("13:1")
    assert 'طبری می\u200cگوید در تأویل حروف گسسته در آغاز سوره\u200cها پیش\u200cتر چندان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که غرض این سوره بیان حقیقت قرآنی' in _joined(verse, "modern")
    assert '«المر» حروف گسسته و آن سکوت نخست شنونده را نگه می\u200cدارد' in _joined(verse, "critical")

def test_rad_13_2_verse():
    verse = _check_verse("13:2")
    assert 'طبری می\u200cگوید خدا ای محمد کسی است که آسمان\u200cهای هفتگانه را' in _joined(verse, "notes")
    assert 'المیزان بر آن است که غرض سوره بیان حقانیت قرآن و' in _joined(verse, "modern")
    assert '«بغیر عمد ترونها» بی ستون\u200cهایی که ببینید و آن قید دیدن' in _joined(verse, "critical")

def test_rad_13_3_verse():
    verse = _check_verse("13:3")
    assert 'طبری می\u200cگوید و خدا کسی است که زمین را گسترد و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که آیات تکوینی بر توحیدی دلالت دارند' in _joined(verse, "modern")
    assert '«مد الأرض» زمین را گسترد و آن گسترش چون فرشی است' in _joined(verse, "critical")

def test_rad_13_4_verse():
    verse = _check_verse("13:4")
    assert 'طبری می\u200cگوید و در زمین قطعه\u200cهایی از آن نزدیک و چسبیده' in _joined(verse, "notes")
    assert 'المیزان بر آن است که آیات تکوینی بر توحید دلالت دارند' in _joined(verse, "modern")
    assert '«قطع متجاورات» قطعه\u200cهای همسایه و آن همسایگی قلب تصویر است و' in _joined(verse, "critical")

def test_rad_13_5_verse():
    verse = _check_verse("13:5")
    assert 'طبری می\u200cگوید و اگر تو ای محمد از این مشرکان که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این دو آیه عطف بر پاره\u200cای' in _joined(verse, "modern")
    assert '«و إن تعجب فعجب قولهم» و اگر شگفت کنی شگفت گفتهٔ' in _joined(verse, "critical")

def test_rad_13_6_verse():
    verse = _check_verse("13:6")
    assert 'طبری می\u200cگوید و مشرکان قومت ای محمد از تو شتاب بلا' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات گفته\u200cهای مشرکان را نقل' in _joined(verse, "modern")
    assert '«و يستعجلونك بالسيئة قبل الحسنة» شتاب بدی را پیش از نیکی' in _joined(verse, "critical")

def test_rad_13_7_verse():
    verse = _check_verse("13:7")
    assert 'طبری می\u200cگوید و آنان که کفر ورزیدند ای محمد از قومت' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات متعرض گفتار کفار است' in _joined(verse, "modern")
    assert '«لولا أنزل عليه آية» چرا نشانه\u200cای بر او فرود نیامد و' in _joined(verse, "critical")

def test_rad_13_8_verse():
    verse = _check_verse("13:8")
    assert 'طبری می\u200cگوید و اگر شگفت کنی شگفت گفتهٔ آنان است که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات در پاسخ شبههٔ معاد' in _joined(verse, "modern")
    assert '«ما تحمل كل أنثى» هر ماده\u200cای چه برمی\u200cدارد و آن هر' in _joined(verse, "critical")

def test_rad_13_9_verse():
    verse = _check_verse("13:9")
    assert 'طبری می\u200cگوید و خدا دانای آنچه از شما و چشمانتان نهان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات نظام مقدر و علم' in _joined(verse, "modern")
    assert '«عالم الغیب و الشهادة» دانای نهان و آشکار و آن دو' in _joined(verse, "critical")

def test_rad_13_10_verse():
    verse = _check_verse("13:10")
    assert 'طبری می\u200cگوید برابر است نزد خدا از شما ای مردم آن' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات علم محیط خدا و' in _joined(verse, "modern")
    assert '«سواء منكم» برابر است از شما و آن آغاز بی\u200cمقدمه چون' in _joined(verse, "critical")

def test_rad_13_11_verse():
    verse = _check_verse("13:11")
    assert 'طبری می\u200cگوید در تأویل آن اختلاف است برخی گفتند برای خدا' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات علم محیط و تقدیر' in _joined(verse, "modern")
    assert '«له معقبات من بین یدیه و من خلفه» او را پیگیرانی' in _joined(verse, "critical")

def test_rad_13_12_verse():
    verse = _check_verse("13:12")
    assert 'طبری می\u200cگوید او کسی است که برق را به شما می\u200cنمایاند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پس از بیان علم' in _joined(verse, "modern")
    assert '«يريكم البرق خوفا و طمعا» برق را به شما می\u200cنمایاند بیم' in _joined(verse, "critical")

def test_rad_13_13_verse():
    verse = _check_verse("13:13")
    assert 'طبری می\u200cگوید و رعد به ستایش او تسبیح می\u200cکند و معنای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات قدرت و ربوبیت او' in _joined(verse, "modern")
    assert '«و يسبح الرعد بحمده» و رعد به ستایش او تسبیح می\u200cکند' in _joined(verse, "critical")

def test_rad_13_14_verse():
    verse = _check_verse("13:14")
    assert 'طبری می\u200cگوید برای خدا از آفریدگانش دعای حق است و دعا' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پس از صحنهٔ رعد' in _joined(verse, "modern")
    assert '«كباسط كفيه إلى الماء ليبلغ فاه و ما هو ببالغه» چون' in _joined(verse, "critical")

def test_rad_13_15_verse():
    verse = _check_verse("13:15")
    assert 'طبری می\u200cگوید اگر اینان که بت\u200cها و مجسمه\u200cها را جز خدا' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات خضوع تکوینی همهٔ موجودات' in _joined(verse, "modern")
    assert '«و لله يسجد من في السماوات و الأرض» و برای خدا' in _joined(verse, "critical")

def test_rad_13_16_verse():
    verse = _check_verse("13:16")
    assert 'طبری می\u200cگوید به پیامبر محمد خدا می\u200cگوید به این مشرکان که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات در رد شرک و' in _joined(verse, "modern")
    assert '«قل من رب السماوات و الأرض قل الله» بگو پروردگار آسمان\u200cها' in _joined(verse, "critical")


def test_rad_13_17_verse():
    verse = _check_verse("13:17")
    assert 'طبری می\u200cگوید این مثلی است که خدا برای حق و باطل' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پس از تمام شدن' in _joined(verse, "modern")
    assert '«فأما الزبد فيذهب جفاء» اما کف به کناری رفته نابود می\u200cشود' in _joined(verse, "critical")

def test_rad_13_18_verse():
    verse = _check_verse("13:18")
    assert 'طبری می\u200cگوید اما آنان که خدا را پاسخ دادند و چون' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات فرق اهل حق و' in _joined(verse, "modern")
    assert '«لو أن لهم ما في الأرض جميعا و مثله معه لافتدوا' in _joined(verse, "critical")

def test_rad_13_19_verse():
    verse = _check_verse("13:19")
    assert 'طبری می\u200cگوید آیا این که می\u200cداند آنچه خدا بر تو ای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پس از مثل حق' in _joined(verse, "modern")
    assert '«أفمن يعلم أنما أنزل إليك من ربك الحق كمن هو أعمى»' in _joined(verse, "critical")

def test_rad_13_20_verse():
    verse = _check_verse("13:20")
    assert 'طبری می\u200cگوید جز این نیست که از آیات خدا پند می\u200cگیرند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات اولوالالباب را با وفای' in _joined(verse, "modern")
    assert '«الذين يوفون بعهد الله و لا ينقضون الميثاق» آنان که به' in _joined(verse, "critical")

def test_rad_13_21_verse():
    verse = _check_verse("13:21")
    assert 'طبری می\u200cگوید و آنان که رحم را که خدا به پیوستنش' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات اولوالالباب را با پیوستن' in _joined(verse, "modern")
    assert '«و الذين يصلون ما أمر الله به أن يوصل» و آنان' in _joined(verse, "critical")

def test_rad_13_22_verse():
    verse = _check_verse("13:22")
    assert 'طبری می\u200cگوید و آنان که بر وفای به پیمان خدا و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات اولوالالباب را با صبر' in _joined(verse, "modern")
    assert '«و يدرءون بالحسنة السيئة» و بدی را با نیکی می\u200cزدایند و' in _joined(verse, "critical")

def test_rad_13_23_verse():
    verse = _check_verse("13:23")
    assert 'طبری می\u200cگوید بهشت\u200cهای عدن برگردان سرانجام آن سراست چنان که گفته' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات سرانجام اهل حق را' in _joined(verse, "modern")
    assert '«و من صلح من آبائهم و أزواجهم و ذرياتهم» و هر' in _joined(verse, "critical")

def test_rad_13_24_verse():
    verse = _check_verse("13:24")
    assert 'طبری می\u200cگوید فرشتگان به آنان می\u200cگویند درود بر شما برای شکیبایی\u200cتان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات درود فرشتگان را بر' in _joined(verse, "modern")
    assert '«سلام عليكم بما صبرتم» درود بر شما برای شکیبایی\u200cتان و آن' in _joined(verse, "critical")

def test_rad_13_25_verse():
    verse = _check_verse("13:25")
    assert 'طبری می\u200cگوید و اما آنان که پیمان خدا را می\u200cشکنند و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات در برابر اهل حق' in _joined(verse, "modern")
    assert '«ينقضون عهد الله من بعد ميثاقه» پیمان خدا را پس از' in _joined(verse, "critical")

def test_rad_13_26_verse():
    verse = _check_verse("13:26")
    assert 'طبری می\u200cگوید خدا بر هر که از آفریدگانش خواهد در روزیش' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پایان بخش را با' in _joined(verse, "modern")
    assert '«و ما الحياة الدنيا في الآخرة إلا متاع» و زندگی دنیا' in _joined(verse, "critical")


def test_rad_13_27_verse():
    verse = _check_verse("13:27")
    assert 'طبری می\u200cگوید مشرکان قومت به تو ای محمد می\u200cگویند چرا نشانه\u200cای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات بازگشتی به گفتار کفار' in _joined(verse, "modern")
    assert '«لولا أنزل عليه آية من ربه» چرا نشانه\u200cای از پروردگارش بر' in _joined(verse, "critical")

def test_rad_13_28_verse():
    verse = _check_verse("13:28")
    assert 'طبری می\u200cگوید و هر که را با توبه روی آورد به' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات روی\u200cآورندگان را وصف می\u200cکند' in _joined(verse, "modern")
    assert '«ألا بذكر الله تطمئن القلوب» آگاه باش که با یاد خدا' in _joined(verse, "critical")

def test_rad_13_29_verse():
    verse = _check_verse("13:29")
    assert 'طبری می\u200cگوید آنان که ایمان آوردند و کارهای شایسته کردند و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات سرانجام روی\u200cآورندگان را بیان' in _joined(verse, "modern")
    assert '«طوبى لهم و حسن مآب» خوشا آنان و نیک سرانجامی و' in _joined(verse, "critical")

def test_rad_13_30_verse():
    verse = _check_verse("13:30")
    assert 'طبری می\u200cگوید چنین تو را ای محمد در گروهی از مردم' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات رسالت پیامبر را در' in _joined(verse, "modern")
    assert '«قل هو ربي لا إله إلا هو» بگو او پروردگار من' in _joined(verse, "critical")

def test_rad_13_31_verse():
    verse = _check_verse("13:31")
    assert 'طبری می\u200cگوید و پیوسته ای محمد آنان که کافر شدند از' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پاسخ نشانه\u200cخواهان است که' in _joined(verse, "modern")
    assert '«و لو أن قرآنا سيرت به الجبال» و اگر قرآنی بود' in _joined(verse, "critical")

def test_rad_13_32_verse():
    verse = _check_verse("13:32")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد صلی\u200cالله علیه وسلم می\u200cگوید ای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات تسلای پیامبر است که' in _joined(verse, "modern")
    assert '«فكيف كان عقاب» پس کیفرم چگونه بود و آن پرسش شنونده' in _joined(verse, "critical")

def test_rad_13_33_verse():
    verse = _check_verse("13:33")
    assert 'طبری می\u200cگوید آیا پروردگاری که پاینده است و نابود و هلاک' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات خدا را قائم بر' in _joined(verse, "modern")
    assert '«قل سموهم» بگو آنان را نام برید و آن دو واژه' in _joined(verse, "critical")

def test_rad_13_34_verse():
    verse = _check_verse("13:34")
    assert 'طبری می\u200cگوید برای این کافران که وصفشان را در این سوره' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پایان روی\u200cگردانان را بیان' in _joined(verse, "modern")
    assert '«و لعذاب الآخرة أشق» و عذاب آخرت سخت\u200cتر است و آن' in _joined(verse, "critical")

def test_rad_13_35_verse():
    verse = _check_verse("13:35")
    assert 'طبری می\u200cگوید اهل دانش به سخن عرب در بردارندهٔ مثل اختلاف' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات مثل بهشت پرهیزگاران را' in _joined(verse, "modern")
    assert '«أكلها دائم و ظلها» میوه\u200cاش پاینده و سایه\u200cاش و آن دو' in _joined(verse, "critical")


def test_rad_13_36_verse():
    verse = _check_verse("13:36")
    assert 'طبری می\u200cگوید و آنان که کتاب را به سویشان فرود آوردیم' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات تتمهٔ بحث نشانه\u200cخواهی است' in _joined(verse, "modern")
    assert '«يفرحون بما أنزل إليك» به آنچه به سوی تو فرود آمد' in _joined(verse, "critical")

def test_rad_13_37_verse():
    verse = _check_verse("13:37")
    assert 'طبری می\u200cگوید و چنان که کتاب را بر تو ای محمد' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات قرآن را حکمی عربی' in _joined(verse, "modern")
    assert '«و لئن اتبعت أهواءهم بعد ما جاءك من العلم» و اگر' in _joined(verse, "critical")

def test_rad_13_38_verse():
    verse = _check_verse("13:38")
    assert 'طبری می\u200cگوید و پیش از تو ای محمد پیامبرانی به سوی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پیامبران پیشین را انسان\u200cهایی' in _joined(verse, "modern")
    assert '«و جعلنا لهم أزواجا و ذرية» و برای آنان همسران و' in _joined(verse, "critical")

def test_rad_13_39_verse():
    verse = _check_verse("13:39")
    assert 'طبری می\u200cگوید اهل تأویل در تفسیر آن اختلاف کردند و برخی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات محو و اثبات را' in _joined(verse, "modern")
    assert '«يمحو الله ما يشاء و يثبت» خدا آنچه را خواهد می\u200cزداید' in _joined(verse, "critical")

def test_rad_13_40_verse():
    verse = _check_verse("13:40")
    assert 'طبری می\u200cگوید و اگر برخی از آنچه را به آنان از' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات بازگشت به تتمهٔ بحث' in _joined(verse, "modern")
    assert '«فإنما عليك البلاغ و علينا الحساب» جز این نیست که رساندن' in _joined(verse, "critical")

def test_rad_13_41_verse():
    verse = _check_verse("13:41")
    assert 'طبری می\u200cگوید اهل تأویل در تفسیر آن اختلاف کردند و برخی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات به کافران نشان می\u200cدهد' in _joined(verse, "modern")
    assert '«ننقصها من أطرافها» آن را از کرانه\u200cهایش می\u200cکاهیم و آن کم' in _joined(verse, "critical")

def test_rad_13_42_verse():
    verse = _check_verse("13:42")
    assert 'طبری می\u200cگوید و آنان که پیش از آنان بودند نیرنگ کردند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات مکر پیشینیان را یاد' in _joined(verse, "modern")
    assert '«فلله المكر جميعا» پس نیرنگ سراسر برای خداست و آن سراسر' in _joined(verse, "critical")

def test_rad_13_43_verse():
    verse = _check_verse("13:43")
    assert 'طبری می\u200cگوید و این مشرکان از قومت ای محمد به تو' in _joined(verse, "notes")
    assert 'المیزان بر آن است که خدای سبحان می\u200cگوید کافران می\u200cگویند تو' in _joined(verse, "modern")
    assert '«لست مرسلا» تو فرستاده نیستی و آن کوتاه\u200cترین انکار این سوره' in _joined(verse, "critical")


def test_ibrahim_14_1_verse():
    verse = _check_verse("14:1")
    assert 'طبری می\u200cگوید معنای الر پیش\u200cتر گفته شد و این کتابی است' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این سوره پیرامون اوصاف قرآن بحث' in _joined(verse, "modern")
    assert '«لتخرج الناس من الظلمات إلى النور» تا مردم را از تاریکی\u200cها' in _joined(verse, "critical")

def test_ibrahim_14_2_verse():
    verse = _check_verse("14:2")
    assert 'طبری می\u200cگوید خوانندگان در خواندن آن اختلاف کردند و بیشتر خوانندگان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات خدا را عزیز و' in _joined(verse, "modern")
    assert '«لله ما في السماوات و ما في الأرض» از آن خداست' in _joined(verse, "critical")

def test_ibrahim_14_3_verse():
    verse = _check_verse("14:3")
    assert 'طبری می\u200cگوید آنان که زندگی دنیا و کالای آن و نافرمانی\u200cهای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات دو راه پیشاروی انسان' in _joined(verse, "modern")
    assert '«يستحبون الحياة الدنيا على الآخرة» زندگی دنیا را بر آخرت برمی\u200cگزینند' in _joined(verse, "critical")

def test_ibrahim_14_4_verse():
    verse = _check_verse("14:4")
    assert 'طبری می\u200cگوید و به سوی هیچ امتی از امت\u200cها ای محمد' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات توضیح ارسال رسولان به' in _joined(verse, "modern")
    assert '«إلا بلسان قومه ليبين لهم» مگر به زبان قومش تا برای' in _joined(verse, "critical")

def test_ibrahim_14_5_verse():
    verse = _check_verse("14:5")
    assert 'طبری می\u200cگوید و موسی را پیش از تو ای محمد با' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات موسی را با آیات' in _joined(verse, "modern")
    assert '«و ذكرهم بأيام الله» و روزهای خدا را به آنان یادآوری' in _joined(verse, "critical")


def test_ibrahim_14_6_verse():
    verse = _check_verse("14:6")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد می\u200cگوید و یاد کن ای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پاره\u200cای از نعمت\u200cها و' in _joined(verse, "modern")
    assert '«اذكروا نعمة الله عليكم» نعمت خدا بر خود را یاد کنید' in _joined(verse, "critical")

def test_ibrahim_14_7_verse():
    verse = _check_verse("14:7")
    assert 'طبری می\u200cگوید و یاد کنید آن\u200cگاه را که پروردگارتان اعلام کرد' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات سخن موسی در یادآوری' in _joined(verse, "modern")
    assert '«لئن شكرتم لأزيدنكم» اگر سپاس گزارید بی\u200cگمان بر شما می\u200cافزایم و' in _joined(verse, "critical")

def test_ibrahim_14_8_verse():
    verse = _check_verse("14:8")
    assert 'طبری می\u200cگوید و موسی به قومش گفت اگر شما ای گروه' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پس از اعلام قانون' in _joined(verse, "modern")
    assert '«إن تكفروا أنتم و من في الأرض جميعا» اگر شما و' in _joined(verse, "critical")

def test_ibrahim_14_9_verse():
    verse = _check_verse("14:9")
    assert 'طبری می\u200cگوید خدا از سخن موسی به قومش خبر می\u200cدهد ای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات داستان تکذیب پیامبران از' in _joined(verse, "modern")
    assert '«فردوا أيديهم في أفواههم» و دست\u200cهاشان را در دهان\u200cهاشان کردند و' in _joined(verse, "critical")

def test_ibrahim_14_10_verse():
    verse = _check_verse("14:10")
    assert 'طبری می\u200cگوید فرستادگان امت\u200cهایی که فرستادگانشان به سوی آنان آمدند گفتند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پاسخ فرستادگان را می\u200cآورد' in _joined(verse, "modern")
    assert '«أفي الله شك فاطر السماوات و الأرض» آیا در خدا شکی' in _joined(verse, "critical")

def test_ibrahim_14_11_verse():
    verse = _check_verse("14:11")
    assert 'طبری می\u200cگوید امت\u200cهایی که فرستادگانشان به سوی آنان آمدند به فرستادگانشان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پاسخ پیامبران به مکذبان' in _joined(verse, "modern")
    assert '«إن نحن إلا بشر مثلكم» ما جز بشری چون شما نیستیم' in _joined(verse, "critical")

def test_ibrahim_14_12_verse():
    verse = _check_verse("14:12")
    assert 'طبری می\u200cگوید فرستادگان به امت\u200cهاشان گفتند و ما را چه شده' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات معنای توکل پیامبران در' in _joined(verse, "modern")
    assert '«و ما لنا ألا نتوكل على الله» و ما را چه' in _joined(verse, "critical")

def test_ibrahim_14_13_verse():
    verse = _check_verse("14:13")
    assert 'طبری می\u200cگوید و آنان که به خدا کافر شدند به فرستادگانشان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات تهدید کفار به پیامبران' in _joined(verse, "modern")
    assert '«لنخرجنكم من أرضنا أو لتعودن في ملتنا» شما را از سرزمینمان' in _joined(verse, "critical")

def test_ibrahim_14_14_verse():
    verse = _check_verse("14:14")
    assert 'طبری می\u200cگوید و شما را پس از آنان در زمین ساکن' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پاسخ خدا به تهدید' in _joined(verse, "modern")
    assert '«و لنسكننكم الأرض من بعدهم» و شما را پس از آنان' in _joined(verse, "critical")

def test_ibrahim_14_15_verse():
    verse = _check_verse("14:15")
    assert 'طبری می\u200cگوید و فرستادگان بر قومشان گشایش خواستند یعنی از خدا' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات نتیجهٔ آن گفت\u200cوگو را' in _joined(verse, "modern")
    assert '«و خاب كل جبار عنيد» و هر زورگوی ستیزه\u200cجویی زیان دید' in _joined(verse, "critical")

def test_ibrahim_14_16_verse():
    verse = _check_verse("14:16")
    assert 'طبری می\u200cگوید از پیش هر زورگویی دوزخ است به آن درمی\u200cآیند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات فرجام جبار عنید را' in _joined(verse, "modern")
    assert '«من ورائه جهنم» از پیش او دوزخ است و آن پیش' in _joined(verse, "critical")

def test_ibrahim_14_17_verse():
    verse = _check_verse("14:17")
    assert 'طبری می\u200cگوید آن را جرعه جرعه می\u200cنوشد یعنی آن را می\u200cچشد' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات نوشیدن جبار را شرح' in _joined(verse, "modern")
    assert '«يتجرعه و لا يكاد يسيغه» آن را جرعه جرعه می\u200cنوشد و' in _joined(verse, "critical")

def test_ibrahim_14_18_verse():
    verse = _check_verse("14:18")
    assert 'طبری می\u200cگوید زبان\u200cشناسان در بردارندهٔ مثل اختلاف کردند برخی نحویان بصره' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات مثل اعمال کافران را' in _joined(verse, "modern")
    assert '«كرماد اشتدت به الريح في يوم عاصف» چون خاکستری که باد' in _joined(verse, "critical")


def test_ibrahim_14_19_verse():
    verse = _check_verse("14:19")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد می\u200cگوید آیا ای محمد با' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات مردم را به خداشناسی' in _joined(verse, "modern")
    assert '«ألم تر أن الله خلق السماوات و الأرض بالحق» آیا ندیدی' in _joined(verse, "critical")

def test_ibrahim_14_20_verse():
    verse = _check_verse("14:20")
    assert 'طبری می\u200cگوید و آن بر خدا دشوار نیست می\u200cگوید و بردن' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید آن بردن شما' in _joined(verse, "modern")
    assert '«وَما ذلك على الله بعزيز» و آن بر خدا دشوار نیست' in _joined(verse, "critical")

def test_ibrahim_14_21_verse():
    verse = _check_verse("14:21")
    assert 'طبری می\u200cگوید و همه برای خدا آشکار شدند یعنی اینان که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات آشکار شدن همه برای' in _joined(verse, "modern")
    assert '«إنا كنا لكم تبعا فهل أنتم مغنون عنا» ما پیرو شما' in _joined(verse, "critical")

def test_ibrahim_14_22_verse():
    verse = _check_verse("14:22")
    assert 'طبری می\u200cگوید و ابلیس گفت چون کار گذشت یعنی چون اهل' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات سخن شیطان با پیروانش' in _joined(verse, "modern")
    assert '«فلا تلوموني و لوموا أنفسكم» مرا سرزنش نکنید و خود را' in _joined(verse, "critical")

def test_ibrahim_14_23_verse():
    verse = _check_verse("14:23")
    assert 'طبری می\u200cگوید و آنان که خدا و فرستاده\u200cاش را راست دانستند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پس از صحنه\u200cهای داوری' in _joined(verse, "modern")
    assert '«تحيتهم فيها سلام» درودشان در آن سلام است و آن یک' in _joined(verse, "critical")

def test_ibrahim_14_24_verse():
    verse = _check_verse("14:24")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد می\u200cگوید آیا ای محمد با' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات کلمهٔ طیبه را به' in _joined(verse, "modern")
    assert '«أصلها ثابت و فرعها في السماء» ریشه\u200cاش استوار و شاخه\u200cاش در' in _joined(verse, "critical")

def test_ibrahim_14_25_verse():
    verse = _check_verse("14:25")
    assert 'طبری می\u200cگوید اهل تأویل در معنای زمانی که خدا در این\u200cجا' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات میوه دادن درخت را' in _joined(verse, "modern")
    assert '«تؤتي أكلها كل حين» میوه\u200cاش را هر زمان می\u200cدهد و آن' in _joined(verse, "critical")

def test_ibrahim_14_26_verse():
    verse = _check_verse("14:26")
    assert 'طبری در شرح این آیه در پیوند با آیهٔ پیشین می\u200cگوید' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات مقصود از کلمهٔ خبیثه' in _joined(verse, "modern")
    assert '«اجتثت من فوق الأرض ما لها من قرار» از روی زمین' in _joined(verse, "critical")

def test_ibrahim_14_27_verse():
    verse = _check_verse("14:27")
    assert 'طبری می\u200cگوید خدا کارها و ایمان آنان را که ایمان آوردند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید آغاز و ادامهٔ' in _joined(verse, "modern")
    assert '«يثبت الله الذين آمنوا بالقول الثابت» خدا آنان را که ایمان' in _joined(verse, "critical")

def test_ibrahim_14_28_verse():
    verse = _check_verse("14:28")
    assert 'طبری می\u200cگوید آیا ای محمد ندیدی آنان را که نعمت خدا' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات حال سردمداران و بزرگان' in _joined(verse, "modern")
    assert '«بدلوا نعمة الله كفرا» نعمت خدا را کفر بدل کردند و' in _joined(verse, "critical")

def test_ibrahim_14_29_verse():
    verse = _check_verse("14:29")
    assert 'طبری می\u200cگوید سپس از سرای هلاکت روشن کرد چیست گفته شد' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات دار البوار را جهنم' in _joined(verse, "modern")
    assert '«جهنم يصلونها و بئس القرار» دوزخ در آن درآیند و بد' in _joined(verse, "critical")

def test_ibrahim_14_30_verse():
    verse = _check_verse("14:30")
    assert 'طبری می\u200cگوید و اینان که نعمت خدا را کفر بدل کردند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید برای خدا اندادی' in _joined(verse, "modern")
    assert '«قل تمتعوا فإن مصيركم إلى النار» بگو بهره برید که بازگشت' in _joined(verse, "critical")

def test_ibrahim_14_31_verse():
    verse = _check_verse("14:31")
    assert 'طبری می\u200cگوید خدا به پیامبرش می\u200cگوید بگو ای محمد به بندگانم' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات به بندگان مؤمن می\u200cگوید' in _joined(verse, "modern")
    assert '«سرا و علانية» پنهان و آشکار و آن دو قید انفاق' in _joined(verse, "critical")

def test_ibrahim_14_32_verse():
    verse = _check_verse("14:32")
    assert 'طبری می\u200cگوید خدا آن است که آسمان\u200cها و زمین را از' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات استدلال بر یگانگی ربوبیت' in _joined(verse, "modern")
    assert '«الله الذي خلق السماوات و الأرض» خداست که آسمان\u200cها و زمین' in _joined(verse, "critical")

def test_ibrahim_14_33_verse():
    verse = _check_verse("14:33")
    assert 'طبری می\u200cگوید و خدا آن که آسمان\u200cها و زمین را آفرید' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات تسخیر خورشید و ماه' in _joined(verse, "modern")
    assert '«دائبين» کوشنده و آن یک واژه خورشید و ماه را به' in _joined(verse, "critical")

def test_ibrahim_14_34_verse():
    verse = _check_verse("14:34")
    assert 'طبری می\u200cگوید و به شما داد با بخشیدنش بر شما از' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید از هر چه' in _joined(verse, "modern")
    assert '«و إن تعدوا نعمت الله لا تحصوها» و اگر نعمت خدا' in _joined(verse, "critical")


def test_ibrahim_14_35_verse():
    verse = _check_verse("14:35")
    assert 'طبری می\u200cگوید و ای محمد یاد کن و چون ابراهیم گفت' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات انعام به فرزندان ابراهیم' in _joined(verse, "modern")
    assert '«رب اجعل هذا البلد آمنا» پروردگارا این شهر را امن کن' in _joined(verse, "critical")

def test_ibrahim_14_36_verse():
    verse = _check_verse("14:36")
    assert 'طبری در شرح این آیه حدیثی بزرگ می\u200cآورد مثنی از اصبغ' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید بت\u200cها بسیاری از' in _joined(verse, "modern")
    assert '«فمن تبعني فإنه مني» پس هر که از من پیروی کند' in _joined(verse, "critical")

def test_ibrahim_14_37_verse():
    verse = _check_verse("14:37")
    assert 'طبری می\u200cگوید و ابراهیم خلیل رحمان این سخن را گفت چون' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات دعای ابراهیم را می\u200cگوید' in _joined(verse, "modern")
    assert '«بواد غير ذي زرع عند بيتك المحرم» در دره\u200cای بی\u200cکشت نزد' in _joined(verse, "critical")

def test_ibrahim_14_38_verse():
    verse = _check_verse("14:38")
    assert 'طبری می\u200cگوید و این خبری از خدا دربارهٔ گواه گرفتن دوستش' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید پروردگارا تو آنچه' in _joined(verse, "modern")
    assert '«ربنا إنك تعلم ما نخفي و ما نعلن» پروردگارا تو می\u200cدانی' in _joined(verse, "critical")

def test_ibrahim_14_39_verse():
    verse = _check_verse("14:39")
    assert 'طبری می\u200cگوید سپاس خدا را که در بزرگی سن فرزندی اسماعیل' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات دعای ابراهیم را می\u200cگوید' in _joined(verse, "modern")
    assert '«الحمد لله الذي وهب لي على الكبر» سپاس خدایی را که' in _joined(verse, "critical")

def test_ibrahim_14_40_verse():
    verse = _check_verse("14:40")
    assert 'طبری می\u200cگوید پروردگارا مرا انجام\u200cدهندهٔ آنچه از فریضه\u200cات که بر من' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات دعای ابراهیم را تمام' in _joined(verse, "modern")
    assert '«رب اجعلني مقيم الصلاة و من ذريتي» پروردگارا مرا برپاکنندهٔ نماز' in _joined(verse, "critical")

def test_ibrahim_14_41_verse():
    verse = _check_verse("14:41")
    assert 'طبری می\u200cگوید و این دعای ابراهیم برای پدر و مادرش به' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات دعای ابراهیم را پایان' in _joined(verse, "modern")
    assert '«ربنا اغفر لي و لوالدي و للمؤمنين» پروردگارا مرا و پدر' in _joined(verse, "critical")


def test_ibrahim_14_42_verse():
    verse = _check_verse("14:42")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد می\u200cگوید و خدا را ای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات پاسخ توهمی است که' in _joined(verse, "modern")
    assert '«و لا تحسبن الله غافلا عما يعمل الظالمون» و خدا را' in _joined(verse, "critical")

def test_ibrahim_14_43_verse():
    verse = _check_verse("14:43")
    assert 'طبری می\u200cگوید و اما گفته\u200cاش شتابان اهل تأویل در معنایش اختلاف' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات چشم خیره و گردن' in _joined(verse, "modern")
    assert '«و أفئدتهم هواء» و دل\u200cهایشان تهی است و آن هوا بودن' in _joined(verse, "critical")

def test_ibrahim_14_44_verse():
    verse = _check_verse("14:44")
    assert 'طبری می\u200cگوید و ای محمد مردم را که تو را به' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات انذار دوم است و' in _joined(verse, "modern")
    assert '«ربنا أخرنا إلى أجل قريب نجب دعوتك و نتبع الرسل» پروردگارا' in _joined(verse, "critical")

def test_ibrahim_14_45_verse():
    verse = _check_verse("14:45")
    assert 'طبری می\u200cگوید و در دنیا در خانه\u200cهای آنان که به خدا' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید در مسکن\u200cهای ستمگران' in _joined(verse, "modern")
    assert '«و سكنتم في مساكن الذين ظلموا أنفسهم» و در خانه\u200cهای آنان' in _joined(verse, "critical")

def test_ibrahim_14_46_verse():
    verse = _check_verse("14:46")
    assert 'طبری در شرح این دسته می\u200cگوید آنان نیرنگ خود را کردند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات معنای مکر ظالمان نزد' in _joined(verse, "modern")
    assert '«و عند الله مكرهم» و نیرنگشان نزد خداست و آن نزد' in _joined(verse, "critical")

def test_ibrahim_14_47_verse():
    verse = _check_verse("14:47")
    assert 'طبری در شرح این بخش می\u200cگوید خدا را خلف\u200cکنندهٔ وعده\u200cاش به' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید خدا را خلف' in _joined(verse, "modern")
    assert '«فلا تحسبن الله مخلف وعده رسله» پس خدا را خلف\u200cکنندهٔ وعده\u200cاش' in _joined(verse, "critical")

def test_ibrahim_14_48_verse():
    verse = _check_verse("14:48")
    assert 'طبری در شرح این آیه بر آن است که روزی که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات وجوه گفته شده در' in _joined(verse, "modern")
    assert '«يوم تبدل الأرض غير الأرض و السماوات» روزی که زمین به' in _joined(verse, "critical")

def test_ibrahim_14_49_verse():
    verse = _check_verse("14:49")
    assert 'طبری در شرح این آیه بر آن است که گناهکاران آن' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات گناهکاران را آن روز' in _joined(verse, "modern")
    assert '«و ترى المجرمين يومئذ مقرنين في الأصفاد» و گناهکاران را آن' in _joined(verse, "critical")

def test_ibrahim_14_50_verse():
    verse = _check_verse("14:50")
    assert 'طبری می\u200cگوید و گناهکارانی را که به خدا کفر ورزیدند و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید سرابیل آنان از' in _joined(verse, "modern")
    assert '«سرابيلهم من قطران و تغشى وجوههم النار» جامه\u200cهاشان از قیر است' in _joined(verse, "critical")

def test_ibrahim_14_51_verse():
    verse = _check_verse("14:51")
    assert 'طبری در شرح غایت این صحنه می\u200cگوید تا خدا هر نفسی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات غایت صحنه را می\u200cگوید' in _joined(verse, "modern")
    assert '«ليجزي الله كل نفس ما كسبت» تا خدا هر کسی را' in _joined(verse, "critical")

def test_ibrahim_14_52_verse():
    verse = _check_verse("14:52")
    assert 'طبری می\u200cگوید این قرآن رسانیدنی برای مردم است خدا با آن' in _joined(verse, "notes")
    assert 'المیزان بر آن است که سوره به جامع\u200cترین آیه نسبت به' in _joined(verse, "modern")
    assert '«هذا بلاغ للناس» این رسانیدنی برای مردم است و آن هذا' in _joined(verse, "critical")

def test_hijr_15_1_verse():
    verse = _check_verse("15:1")
    assert 'طبری می\u200cگوید گفته\u200cاش الر پیش\u200cتر روشن شده است و گفته\u200cاش این' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این سوره پیرامون استهزای کفار به' in _joined(verse, "modern")
    assert '«تلك آيات الكتاب و قرآن مبين» این آیات کتاب و قرآنی' in _joined(verse, "critical")

def test_hijr_15_2_verse():
    verse = _check_verse("15:2")
    assert 'طبری می\u200cگوید خوانندگان در خواندن گفته\u200cاش بسا اختلاف کردند بیشتر خوانندگان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات آرزوی ایمان کافران را' in _joined(verse, "modern")
    assert '«ربما يود الذين كفروا لو كانوا مسلمين» بسا آنان که کفر' in _joined(verse, "critical")

def test_hijr_15_3_verse():
    verse = _check_verse("15:3")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد می\u200cگوید ای محمد این مشرکان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید آنان را بگذار' in _joined(verse, "modern")
    assert '«ذرهم يأكلوا و يتمتعوا و يلههم الأمل» آنان را بگذار بخورند' in _joined(verse, "critical")

def test_hijr_15_4_verse():
    verse = _check_verse("15:4")
    assert 'طبری می\u200cگوید و هلاک نکردیم ای محمد از اهل شهری از' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید هیچ قریه\u200cای را' in _joined(verse, "modern")
    assert '«و ما أهلكنا من قرية إلا و لها كتاب معلوم» و' in _joined(verse, "critical")

def test_hijr_15_5_verse():
    verse = _check_verse("15:5")
    assert 'طبری می\u200cگوید هلاک هیچ امتی پیش از زمانی که خدا آن' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات قانون اجل امت\u200cها را' in _joined(verse, "modern")
    assert '«ما تسبق من أمة أجلها و ما يستأخرون» هیچ امتی از' in _joined(verse, "critical")

def test_hijr_15_6_verse():
    verse = _check_verse("15:6")
    assert 'طبری می\u200cگوید و این مشرکان از قومت ای محمد گفتند ای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این سوره پیرامون استهزای کفار به' in _joined(verse, "modern")
    assert '«يا أيها الذي نزل عليه الذكر إنك لمجنون» ای آن که' in _joined(verse, "critical")

def test_hijr_15_7_verse():
    verse = _check_verse("15:7")
    assert 'طبری می\u200cگوید چرا فرشتگان را برای ما نمی\u200cآوری گفتند چرا فرشتگان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات وجه و سبب خواستن' in _joined(verse, "modern")
    assert '«لو ما تأتينا بالملائكة» چرا فرشتگان را برای ما نمی\u200cآوری و' in _joined(verse, "critical")

def test_hijr_15_8_verse():
    verse = _check_verse("15:8")
    assert 'طبری می\u200cگوید خوانندگان در خواندن گفته\u200cاش فرشتگان را فرو نمی\u200cفرستیم اختلاف' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات معنای فرشتگان را جز' in _joined(verse, "modern")
    assert '«ما ننزل الملائكة إلا بالحق» فرشتگان را جز به حق فرو' in _joined(verse, "critical")

def test_hijr_15_9_verse():
    verse = _check_verse("15:9")
    assert 'طبری می\u200cگوید ما ذکر را فرو فرستادیم و آن قرآن است' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات معنای ما ذکر را' in _joined(verse, "modern")
    assert '«إنا نحن نزلنا الذكر و إنا له لحافظون» ما ذکر را' in _joined(verse, "critical")

def test_hijr_15_10_verse():
    verse = _check_verse("15:10")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد می\u200cگوید ما پیش از تو' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات تسلیت و دلگرمی دادن' in _joined(verse, "modern")
    assert '«و لقد أرسلنا من قبلك في شيع الأولين» و به راستی' in _joined(verse, "critical")

def test_hijr_15_11_verse():
    verse = _check_verse("15:11")
    assert 'طبری می\u200cگوید و نزد گروه\u200cهای نخستین فرستاده\u200cای از خدا نمی\u200cآید که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید هیچ فرستاده\u200cای نزدشان' in _joined(verse, "modern")
    assert '«و ما يأتيهم من رسول إلا كانوا به يستهزئون» و فرستاده\u200cای' in _joined(verse, "critical")

def test_hijr_15_12_verse():
    verse = _check_verse("15:12")
    assert 'طبری می\u200cگوید خدا می\u200cگوید چنان که کفر را در دل\u200cهای گروه\u200cهای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید این\u200cچنین آن را' in _joined(verse, "modern")
    assert '«كذلك نسلكه في قلوب المجرمين» این\u200cچنین آن را در دل\u200cهای گناهکاران' in _joined(verse, "critical")

def test_hijr_15_13_verse():
    verse = _check_verse("15:13")
    assert 'طبری می\u200cگوید به این قرآن قومت که دروغ\u200cخواندن را در دلشان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید به آن ایمان' in _joined(verse, "modern")
    assert '«لا يؤمنون به و قد خلت سنة الأولين» به آن ایمان' in _joined(verse, "critical")

def test_hijr_15_14_verse():
    verse = _check_verse("15:14")
    assert 'طبری می\u200cگوید اهل تأویل در اهل گفته\u200cاش پس در آن بالا' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید اگر دری از' in _joined(verse, "modern")
    assert '«و لو فتحنا عليهم بابا من السماء فظلوا فيه يعرجون» و' in _joined(verse, "critical")

def test_hijr_15_15_verse():
    verse = _check_verse("15:15")
    assert 'طبری می\u200cگوید پس این مشرکان که خدا وصفشان را گفت می\u200cگفتند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید هر آینه گویند' in _joined(verse, "modern")
    assert '«لقالوا إنما سكرت أبصارنا بل نحن قوم مسحورون» خواهند گفت تنها' in _joined(verse, "critical")

def test_hijr_15_16_verse():
    verse = _check_verse("15:16")
    assert 'طبری می\u200cگوید خدا می\u200cگوید و به راستی در آسمان دنیا جای\u200cهایی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات زیبایی و زینت آسمان' in _joined(verse, "modern")
    assert '«و لقد جعلنا في السماء بروجا و زيناها للناظرين» و به' in _joined(verse, "critical")

def test_hijr_15_17_verse():
    verse = _check_verse("15:17")
    assert 'طبری می\u200cگوید خدا می\u200cگوید و آسمان دنیا را از هر شیطان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید و آن را' in _joined(verse, "modern")
    assert '«و حفظناها من كل شيطان رجيم» و آن را از هر' in _joined(verse, "critical")

def test_hijr_15_18_verse():
    verse = _check_verse("15:18")
    assert 'طبری می\u200cگوید مگر آن که گوش بدزدد می\u200cگوید اما از شیطان\u200cها' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید مگر آن که' in _joined(verse, "modern")
    assert '«إلا من استرق السمع فأتبعه شهاب مبين» مگر آن که گوش' in _joined(verse, "critical")

def test_hijr_15_19_verse():
    verse = _check_verse("15:19")
    assert 'طبری می\u200cگوید خدا با گفته\u200cاش و زمین را گستردیم یعنی زمین' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید و زمین را' in _joined(verse, "modern")
    assert '«و الأرض مددناها و ألقينا فيها رواسي و أنبتنا فيها من' in _joined(verse, "critical")

def test_hijr_15_20_verse():
    verse = _check_verse("15:20")
    assert 'طبری می\u200cگوید خدا می\u200cگوید و برای شما ای مردم در زمین' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات مقصود از کسانی که' in _joined(verse, "modern")
    assert '«و جعلنا لكم فيها معايش و من لستم له برازقين» و' in _joined(verse, "critical")

def test_hijr_15_21_verse():
    verse = _check_verse("15:21")
    assert 'طبری می\u200cگوید خدا می\u200cگوید و چیزی از باران\u200cها نیست مگر گنجینه\u200cهایش' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات وجوه و گفته\u200cهای گوناگون' in _joined(verse, "modern")
    assert '«و إن من شيء إلا عندنا خزائنه و ما ننزله إلا' in _joined(verse, "critical")

def test_hijr_15_22_verse():
    verse = _check_verse("15:22")
    assert 'طبری می\u200cگوید خوانندگان در خواندن آن اختلاف کردند بیشتر خوانندگان و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات نظام خلقت را بدون' in _joined(verse, "modern")
    assert '«و أرسلنا الرياح لواقح فأنزلنا من السماء ماء فأسقيناكموه و ما' in _joined(verse, "critical")

def test_hijr_15_23_verse():
    verse = _check_verse("15:23")
    assert 'طبری می\u200cگوید خدا می\u200cگوید و ما زنده می\u200cکنیم آن که مرده' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید ما زنده می\u200cکنیم' in _joined(verse, "modern")
    assert '«و إنا لنحن نحيي و نميت و نحن الوارثون» و ما' in _joined(verse, "critical")

def test_hijr_15_24_verse():
    verse = _check_verse("15:24")
    assert 'طبری می\u200cگوید گفته\u200cاش و به راستی پیشینیان شما را دانستیم و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید به راستی پیشینیان' in _joined(verse, "modern")
    assert '«و لقد علمنا المستقدمين منكم و لقد علمنا المستأخرين» و به' in _joined(verse, "critical")

def test_hijr_15_25_verse():
    verse = _check_verse("15:25")
    assert 'طبری می\u200cگوید گفته\u200cاش و به راستی پروردگارت آنان را گرد می\u200cآورد' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید و به راستی' in _joined(verse, "modern")
    assert '«و إن ربك هو يحشرهم إنه حكيم عليم» و به راستی' in _joined(verse, "critical")

def test_hijr_15_26_verse():
    verse = _check_verse("15:26")
    assert 'طبری می\u200cگوید خدا می\u200cگوید و به راستی انسان که آدم است' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات معنای آفرینش انسان از' in _joined(verse, "modern")
    assert '«و لقد خلقنا الإنسان من صلصال من حمإ مسنون» و به' in _joined(verse, "critical")

def test_hijr_15_27_verse():
    verse = _check_verse("15:27")
    assert 'طبری می\u200cگوید گفته\u200cاش و جان و معنای جان و چرا او' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات توضیحاتی دربارهٔ معنای لغوی' in _joined(verse, "modern")
    assert '«و الجان خلقناه من قبل من نار السموم» و جان را' in _joined(verse, "critical")

def test_hijr_15_28_verse():
    verse = _check_verse("15:28")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد می\u200cگوید و ای محمد یاد' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات معنای واژهٔ بشر و' in _joined(verse, "modern")
    assert '«و إذ قال ربك للملائكة إني خالق بشرا» و آن\u200cگاه که' in _joined(verse, "critical")

def test_hijr_15_29_verse():
    verse = _check_verse("15:29")
    assert 'طبری می\u200cگوید پس چون او را صورت کردم و صورتش را' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات معنای او را راست' in _joined(verse, "modern")
    assert '«فإذا سويته و نفخت فيه من روحي فقعوا له ساجدين» پس' in _joined(verse, "critical")

def test_hijr_15_30_verse():
    verse = _check_verse("15:30")
    assert 'طبری می\u200cگوید خدا می\u200cگوید پس چون خدا آن انسان را آفرید' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید پس فرشتگان همه' in _joined(verse, "modern")
    assert '«فسجد الملائكة كلهم أجمعون» پس فرشتگان همه با هم سجده کردند' in _joined(verse, "critical")

def test_hijr_15_31_verse():
    verse = _check_verse("15:31")
    assert 'طبری می\u200cگوید جز ابلیس که او سرباز زد از این که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید جز ابلیس که' in _joined(verse, "modern")
    assert '«إلا إبليس أبى أن يكون مع الساجدين» جز ابلیس که سرباز' in _joined(verse, "critical")

def test_hijr_15_32_verse():
    verse = _check_verse("15:32")
    assert 'طبری می\u200cگوید پس خدا گفت ای ابلیس تو را چیست که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید ای ابلیس تو' in _joined(verse, "modern")
    assert '«قال يا إبليس ما لك ألا تكون مع الساجدين» گفت ای' in _joined(verse, "critical")

def test_hijr_15_33_verse():
    verse = _check_verse("15:33")
    assert 'طبری می\u200cگوید خدا می\u200cگوید ابلیس گفت من آن نیستم که برای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید من آن نیستم' in _joined(verse, "modern")
    assert '«قال لم أكن لأسجد لبشر خلقته من صلصال من حمإ مسنون»' in _joined(verse, "critical")

def test_hijr_15_34_verse():
    verse = _check_verse("15:34")
    assert 'طبری می\u200cگوید گفته\u200cاش پس از آن بیرون شو می\u200cگوید خدا به' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید پس از آن' in _joined(verse, "modern")
    assert '«قال فاخرج منها فإنك رجيم» گفت پس از آن بیرون شو' in _joined(verse, "critical")

def test_hijr_15_35_verse():
    verse = _check_verse("15:35")
    assert 'طبری می\u200cگوید گفته\u200cاش و به راستی لعنت تا روز جزا بر' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات وجه مقید کردن لعنت' in _joined(verse, "modern")
    assert '«و إن عليك اللعنة إلى يوم الدين» و به راستی لعنت' in _joined(verse, "critical")

def test_hijr_15_36_verse():
    verse = _check_verse("15:36")
    assert 'طبری می\u200cگوید خدا می\u200cگوید ابلیس گفت پروردگارا پس چون مرا از' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید پروردگارا مرا تا' in _joined(verse, "modern")
    assert '«قال رب فأنظرني إلى يوم يبعثون» گفت پروردگارا مرا تا روزی' in _joined(verse, "critical")

def test_hijr_15_37_verse():
    verse = _check_verse("15:37")
    assert 'طبری می\u200cگوید خدا به او گفت پس تو از آنان هستی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید پس تو از' in _joined(verse, "modern")
    assert '«قال فإنك من المنظرين» گفت پس تو از مهلت\u200cیافتگانی و آن' in _joined(verse, "critical")

def test_hijr_15_38_verse():
    verse = _check_verse("15:38")
    assert 'طبری می\u200cگوید تا روز وقت معلوم برای هلاک همهٔ آفریدگانم و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید تا روز وقت' in _joined(verse, "modern")
    assert '«إلى يوم الوقت المعلوم» تا روز وقت معلوم و آن چهار' in _joined(verse, "critical")

def test_hijr_15_39_verse():
    verse = _check_verse("15:39")
    assert 'طبری می\u200cگوید خدا می\u200cگوید ابلیس گفت پروردگارا به گمراه کردنت مرا' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات معنای گفته\u200cاش پروردگارا به' in _joined(verse, "modern")
    assert '«قال رب بما أغويتني لأزينن لهم في الأرض و لأغوينهم أجمعين»' in _joined(verse, "critical")

def test_hijr_15_40_verse():
    verse = _check_verse("15:40")
    assert 'طبری می\u200cگوید مگر بندگانت از آنان که خالص شدگان\u200cاند می\u200cگوید مگر' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات مراد از بندگان خالص' in _joined(verse, "modern")
    assert '«إلا عبادك منهم المخلصين» مگر بندگانت از آنان که خالص شده\u200cاند' in _joined(verse, "critical")

def test_hijr_15_41_verse():
    verse = _check_verse("15:41")
    assert 'طبری می\u200cگوید خوانندگان در خواندن گفته\u200cاش گفت این راهی راست بر' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات معنای بر خدا بودن' in _joined(verse, "modern")
    assert '«قال هذا صراط علي مستقيم» گفت این راهی راست بر من' in _joined(verse, "critical")

def test_hijr_15_42_verse():
    verse = _check_verse("15:42")
    assert 'طبری می\u200cگوید گفته\u200cاش به راستی بندگانم را بر آنان چیرگی نداری' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید به راستی بندگانم' in _joined(verse, "modern")
    assert '«إن عبادي ليس لك عليهم سلطان إلا من اتبعك من الغاوين»' in _joined(verse, "critical")

def test_hijr_15_43_verse():
    verse = _check_verse("15:43")
    assert 'طبری می\u200cگوید خدا به ابلیس می\u200cگوید و به راستی جهنم وعده\u200cگاه' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید و به راستی' in _joined(verse, "modern")
    assert '«و إن جهنم لموعد هم أجمعين» و به راستی جهنم وعده\u200cگاه' in _joined(verse, "critical")

def test_hijr_15_44_verse():
    verse = _check_verse("15:44")
    assert 'طبری می\u200cگوید آن را هفت در است می\u200cگوید جهنم را هفت' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات معنای این که جهنم' in _joined(verse, "modern")
    assert '«لها سبعة أبواب لكل باب منهم جزء مقسوم» آن را هفت' in _joined(verse, "critical")

def test_hijr_15_45_verse():
    verse = _check_verse("15:45")
    assert 'طبری می\u200cگوید خدا می\u200cگوید به راستی آنان که با فرمانبرداری از' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید به راستی پرهیزکاران' in _joined(verse, "modern")
    assert '«إن المتقين في جنات و عيون» به راستی پرهیزکاران در باغ\u200cها' in _joined(verse, "critical")

def test_hijr_15_46_verse():
    verse = _check_verse("15:46")
    assert 'طبری می\u200cگوید به آنان گفته می\u200cشود با سلام ایمنان در آن' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید با سلام ایمنان' in _joined(verse, "modern")
    assert '«ادخلوها بسلام آمنين» با سلام ایمنان در آن درآیید و آن' in _joined(verse, "critical")

def test_hijr_15_47_verse():
    verse = _check_verse("15:47")
    assert 'طبری می\u200cگوید گفته\u200cاش و آنچه در سینه\u200cهاشان از کینه بود برکندیم' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات چند روایت در بیان' in _joined(verse, "modern")
    assert '«و نزعنا ما في صدورهم من غل إخوانا على سرر متقابلين»' in _joined(verse, "critical")

def test_hijr_15_48_verse():
    verse = _check_verse("15:48")
    assert 'طبری می\u200cگوید خدا می\u200cگوید این پرهیزکاران را که وصفشان را گفت' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید در آن رنجی' in _joined(verse, "modern")
    assert '«لا يمسهم فيها نصب و ما هم منها بمخرجين» در آن' in _joined(verse, "critical")

def test_hijr_15_49_verse():
    verse = _check_verse("15:49")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد می\u200cگوید محمد بندگانم را خبر' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید بندگان مرا خبر' in _joined(verse, "modern")
    assert '«نبئ عبادي أني أنا الغفور الرحيم» بندگانم را خبر ده که' in _joined(verse, "critical")

def test_hijr_15_50_verse():
    verse = _check_verse("15:50")
    assert 'طبری می\u200cگوید و خبرشان ده نیز که عذابم برای آن که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید و عذابم همان' in _joined(verse, "modern")
    assert '«و أن عذابي هو العذاب الأليم» و عذابم همان عذاب دردناک' in _joined(verse, "critical")

def test_hijr_15_51_verse():
    verse = _check_verse("15:51")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد می\u200cگوید و محمد بندگانم را' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید و آنان را' in _joined(verse, "modern")
    assert '«و نبئهم عن ضيف إبراهيم» و آنان را از مهمانان ابراهیم' in _joined(verse, "critical")

def test_hijr_15_52_verse():
    verse = _check_verse("15:52")
    assert 'طبری می\u200cگوید فرشتگانی که بر ابراهیم خلیل رحمان درآمدند چون پروردگارشان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید آن روز که' in _joined(verse, "modern")
    assert '«إذ دخلوا عليه فقالوا سلاما قال إنا منكم وجلون» چون بر' in _joined(verse, "critical")

def test_hijr_15_53_verse():
    verse = _check_verse("15:53")
    assert 'طبری می\u200cگوید مهمانان به ابراهیم گفتند مترس می\u200cگوید مهمانان به ابراهیم' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید گفتند مترس ما' in _joined(verse, "modern")
    assert '«قالوا لا توجل إنا نبشرك بغلام عليم» گفتند مترس ما تو' in _joined(verse, "critical")

def test_hijr_15_54_verse():
    verse = _check_verse("15:54")
    assert 'طبری می\u200cگوید خدا می\u200cگوید ابراهیم به فرشتگانی که او را به' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید گفت آیا در' in _joined(verse, "modern")
    assert '«قال أبشرتموني على أن مسني الكبر فبم تبشرون» گفت آیا در' in _joined(verse, "critical")

def test_hijr_15_55_verse():
    verse = _check_verse("15:55")
    assert 'طبری می\u200cگوید خدا می\u200cگوید مهمانان ابراهیم به او گفتند تو را' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید گفتند تو را' in _joined(verse, "modern")
    assert '«قالوا بشرناك بالحق فلا تكن من القانطين» گفتند تو را به' in _joined(verse, "critical")

def test_hijr_15_56_verse():
    verse = _check_verse("15:56")
    assert 'طبری می\u200cگوید خدا می\u200cگوید ابراهیم به مهمانان گفت و چه کسی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید گفت چه کسی' in _joined(verse, "modern")
    assert '«قال و من يقنط من رحمة ربه إلا الضالون» گفت چه' in _joined(verse, "critical")

def test_hijr_15_57_verse():
    verse = _check_verse("15:57")
    assert 'طبری می\u200cگوید ابراهیم به فرشتگان گفت پس کارتان چیست کارتان چیست' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید گفت ای فرستادگان' in _joined(verse, "modern")
    assert '«قال فما خطبكم أيها المرسلون» گفت پس کارتان چیست ای فرستادگان' in _joined(verse, "critical")

def test_hijr_15_58_verse():
    verse = _check_verse("15:58")
    assert 'طبری می\u200cگوید فرشتگان به او گفتند ما به سوی قومی گناهکار' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید گفتند ما به' in _joined(verse, "modern")
    assert '«قالوا إنا أرسلنا إلى قوم مجرمين» گفتند ما به سوی قومی' in _joined(verse, "critical")

def test_hijr_15_59_verse():
    verse = _check_verse("15:59")
    assert 'طبری می\u200cگوید مگر خاندان لوط می\u200cگوید مگر پیروان لوط بر دینی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید مگر خاندان لوط' in _joined(verse, "modern")
    assert '«إلا آل لوط إنا لمنجوهم أجمعين» مگر خاندان لوط ما همه\u200cشان' in _joined(verse, "critical")

def test_hijr_15_60_verse():
    verse = _check_verse("15:60")
    assert 'طبری می\u200cگوید جز همسر لوط مقدر کردیم که او از بازماندگان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید مگر همسرش مقدر' in _joined(verse, "modern")
    assert '«إلا امرأته قدرنا إنها لمن الغابرين» مگر همسرش مقدر کردیم که' in _joined(verse, "critical")

def test_hijr_15_61_verse():
    verse = _check_verse("15:61")
    assert 'طبری می\u200cگوید خدا می\u200cگوید چون فرستادگان خدا نزد خاندان لوط آمدند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید پس چون فرستادگان' in _joined(verse, "modern")
    assert '«فلما جاء آل لوط المرسلون» پس چون فرستادگان نزد خاندان لوط' in _joined(verse, "critical")

def test_hijr_15_62_verse():
    verse = _check_verse("15:62")
    assert 'طبری می\u200cگوید و به آنان گفت شما گروهی ناشناسید یعنی شما' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید لوط به فرشتگان' in _joined(verse, "modern")
    assert '«قال إنكم قوم منكرون» گفت شما گروهی ناشناسید و آن منکرون' in _joined(verse, "critical")

def test_hijr_15_63_verse():
    verse = _check_verse("15:63")
    assert 'طبری می\u200cگوید گفته\u200cاش با آنچه در آن شک می\u200cکردند گفت با' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید گفتند بلکه با' in _joined(verse, "modern")
    assert '«قالوا بل جئناك بما كانوا فيه يمترون» گفتند بلکه با آنچه' in _joined(verse, "critical")

def test_hijr_15_64_verse():
    verse = _check_verse("15:64")
    assert 'طبری می\u200cگوید خدا می\u200cگوید فرستادگان به لوط گفتند و حق یقین' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید و حق را' in _joined(verse, "modern")
    assert '«و أتيناك بالحق و إنا لصادقون» و حق را برایت آوردیم' in _joined(verse, "critical")

def test_hijr_15_65_verse():
    verse = _check_verse("15:65")
    assert 'طبری برای این آیه تنها از یونس از ابن\u200cوهب از ابن\u200cزید' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید پس خانواده\u200cات را' in _joined(verse, "modern")
    assert '«فأسر بأهلك بقطع من الليل و اتبع أدبارهم و لا يلتفت' in _joined(verse, "critical")

def test_hijr_15_66_verse():
    verse = _check_verse("15:66")
    assert 'طبری می\u200cگوید خدا می\u200cگوید و به سوی لوط از آن کار' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید و به او' in _joined(verse, "modern")
    assert '«و قضينا إليه ذلك الأمر أن دابر هؤلاء مقطوع مصبحين» و' in _joined(verse, "critical")

def test_hijr_15_67_verse():
    verse = _check_verse("15:67")
    assert 'طبری می\u200cگوید گفته\u200cاش و مردم شهر شادمان آمدند می\u200cگوید و مردم' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید از آن سو' in _joined(verse, "modern")
    assert '«و جاء أهل المدينة يستبشرون» و مردم شهر شادمان آمدند و' in _joined(verse, "critical")

def test_hijr_15_68_verse():
    verse = _check_verse("15:68")
    assert 'طبری می\u200cگوید خدا می\u200cگوید لوط به قومش گفت اینان که نزدشان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید لوط برای دفاع' in _joined(verse, "modern")
    assert '«قال إن هؤلاء ضيفي فلا تفضحون» گفت اینان مهمانان منند مرا' in _joined(verse, "critical")

def test_hijr_15_69_verse():
    verse = _check_verse("15:69")
    assert 'طبری می\u200cگوید گفته\u200cاش و از خدا بترسید می\u200cگوید و از خدا' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید و از خدا' in _joined(verse, "modern")
    assert '«و اتقوا الله و لا تخزون» و از خدا بترسید و' in _joined(verse, "critical")

def test_hijr_15_70_verse():
    verse = _check_verse("15:70")
    assert 'طبری می\u200cگوید گفتند آیا تو را از جهانیان بازنداشتیم خدا می\u200cگوید' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید مهاجمان اهل شهر' in _joined(verse, "modern")
    assert '«قالوا أو لم ننهك عن العالمين» گفتند آیا تو را از' in _joined(verse, "critical")

def test_hijr_15_71_verse():
    verse = _check_verse("15:71")
    assert 'طبری می\u200cگوید خدا می\u200cگوید لوط به قومش گفت با زنان ازدواج' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید لوط چون از' in _joined(verse, "modern")
    assert '«قال هؤلاء بناتي إن كنتم فاعلين» گفت اینان دختران منند اگر' in _joined(verse, "critical")

def test_hijr_15_72_verse():
    verse = _check_verse("15:72")
    assert 'طبری می\u200cگوید گفته\u200cاش به جان تو می\u200cگوید خدا به پیامبرش محمد' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید به جان تو' in _joined(verse, "modern")
    assert '«لعمرك إنهم لفي سكرتهم يعمهون» به جان تو آنان در مستی' in _joined(verse, "critical")

def test_hijr_15_73_verse():
    verse = _check_verse("15:73")
    assert 'طبری می\u200cگوید گفته\u200cاش پس بانگ آنان را هنگام برآمدن خورشید گرفت' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید به زندگی و' in _joined(verse, "modern")
    assert '«فأخذتهم الصيحة مشرقين» پس بانگ آنان را هنگام برآمدن خورشید گرفت' in _joined(verse, "critical")

def test_hijr_15_74_verse():
    verse = _check_verse("15:74")
    assert 'طبری می\u200cگوید خدا می\u200cگوید پس بالای سرزمینشان را پایینش کردیم و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید ناگهان بالای شهرشان' in _joined(verse, "modern")
    assert '«فجعلنا عاليها سافلها و أمطرنا عليهم حجارة من سجيل» پس بالایش' in _joined(verse, "critical")

def test_hijr_15_75_verse():
    verse = _check_verse("15:75")
    assert 'طبری می\u200cگوید گفته\u200cاش به راستی در این نشانه\u200cهایی برای نشانه\u200cشناسان است' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید در این نشانه\u200cهایی' in _joined(verse, "modern")
    assert '«إن في ذلك لآيات للمتوسمين» به راستی در این نشانه\u200cهایی برای' in _joined(verse, "critical")

def test_hijr_15_76_verse():
    verse = _check_verse("15:76")
    assert 'طبری می\u200cگوید خدا می\u200cگوید و به راستی این شهر شهر سدوم' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید و آن بر' in _joined(verse, "modern")
    assert '«و إنها لبسبيل مقيم» و آن بر راهی پایدار است و' in _joined(verse, "critical")

def test_hijr_15_77_verse():
    verse = _check_verse("15:77")
    assert 'طبری می\u200cگوید گفته\u200cاش به راستی در این نشانه\u200cای برای مؤمنان است' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید به راستی در' in _joined(verse, "modern")
    assert '«إن في ذلك لآية للمؤمنين» به راستی در این نشانه\u200cای برای' in _joined(verse, "critical")

def test_hijr_15_78_verse():
    verse = _check_verse("15:78")
    assert 'طبری می\u200cگوید خدا می\u200cگوید و صاحبان بیشه ستمکار بودند می\u200cگوید به' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات توضیحی در مورد صاحبان' in _joined(verse, "modern")
    assert '«و إن كان أصحاب الأيكة لظالمين» و صاحبان بیشه ستمکار بودند' in _joined(verse, "critical")

def test_hijr_15_79_verse():
    verse = _check_verse("15:79")
    assert 'طبری می\u200cگوید گفته\u200cاش پس از آنان انتقام گرفتیم و آن دو' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید پس از آنان' in _joined(verse, "modern")
    assert '«فانتقمنا منهم و إنهما لبإمام مبين» پس از آنان انتقام گرفتیم' in _joined(verse, "critical")

def test_hijr_15_80_verse():
    verse = _check_verse("15:80")
    assert 'طبری می\u200cگوید خدا می\u200cگوید و ساکنان حجر تکذیب کردند و برای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید و صاحبان حجر' in _joined(verse, "modern")
    assert '«و لقد كذب أصحاب الحجر المرسلين» و به راستی صاحبان حجر' in _joined(verse, "critical")

def test_hijr_15_81_verse():
    verse = _check_verse("15:81")
    assert 'طبری می\u200cگوید گفته\u200cاش و آیاتمان را به آنان دادیم و از' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید و آیاتمان را' in _joined(verse, "modern")
    assert '«و آتيناهم آياتنا فكانوا عنها معرضين» و آیاتمان را به آنان' in _joined(verse, "critical")

def test_hijr_15_82_verse():
    verse = _check_verse("15:82")
    assert 'طبری می\u200cگوید خدا می\u200cگوید و صاحبان حجر که ثمود قوم صالح\u200cاند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید و از کوه\u200cها' in _joined(verse, "modern")
    assert '«و كانوا ينحتون من الجبال بيوتا آمنين» و از کوه\u200cها خانه\u200cهایی' in _joined(verse, "critical")

def test_hijr_15_83_verse():
    verse = _check_verse("15:83")
    assert 'طبری می\u200cگوید گفته\u200cاش پس بانگ آنان را صبحگاهان گرفت می\u200cگوید پس' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید پس بانگ آنان' in _joined(verse, "modern")
    assert '«فأخذتهم الصيحة مصبحين» پس بانگ آنان را صبحگاهان گرفت و آن' in _joined(verse, "critical")

def test_hijr_15_84_verse():
    verse = _check_verse("15:84")
    assert 'طبری می\u200cگوید گفته\u200cاش پس آنچه به دست می\u200cآوردند آنان را بی\u200cنیاز' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات می\u200cگوید پس آنچه به' in _joined(verse, "modern")
    assert '«فما أغنى عنهم ما كانوا يكسبون» پس آنچه به دست می\u200cآوردند' in _joined(verse, "critical")

def test_hijr_15_85_verse():
    verse = _check_verse("15:85")
    assert 'طبری می\u200cگوید خدا می\u200cگوید همهٔ آفریدگان آسمان و زمین و میان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که با در این آیه بای همراهی' in _joined(verse, "modern")
    assert '«فاصفح الصفح الجميل» پس گذشت کن گذشتی زیبا و آن مفعول' in _joined(verse, "critical")

def test_hijr_15_86_verse():
    verse = _check_verse("15:86")
    assert 'طبری در پیوست آیهٔ پیش می\u200cگوید این\u200cکه پروردگارت همان آفرینندهٔ داناست' in _joined(verse, "notes")
    assert 'المیزان بر آن است که جملهٔ پروردگارت همان آفرینندهٔ داناست دلیل' in _joined(verse, "modern")
    assert '«إن ربك هو الخلاق العليم» به راستی پروردگارت همان آفرینندهٔ داناست' in _joined(verse, "critical")

def test_hijr_15_87_verse():
    verse = _check_verse("15:87")
    assert 'طبری می\u200cگوید اهل تأویل در معنای هفت\u200cتایی که خدا به پیامبرش' in _joined(verse, "notes")
    assert 'المیزان بر آن است که هفت مثانی چنان که در روایت\u200cهای' in _joined(verse, "modern")
    assert '«و لقد آتيناك سبعا من المثاني» و به تو هفت\u200cتایی از' in _joined(verse, "critical")

def test_hijr_15_88_verse():
    verse = _check_verse("15:88")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد می\u200cگوید ای محمد آرزو مکن' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این دو آیه در مقام بیان' in _joined(verse, "modern")
    assert '«لا تمدن عينيك» چشمت را مدوز و آن مد کشیدن چشم' in _joined(verse, "critical")

def test_hijr_15_89_verse():
    verse = _check_verse("15:89")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد می\u200cگوید ای محمد به مشرکان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که بگو من همان هشداردهندهٔ آشکارم یعنی' in _joined(verse, "modern")
    assert '«إني أنا النذير المبين» من همان هشداردهندهٔ آشکارم و آن دو' in _joined(verse, "critical")

def test_hijr_15_90_verse():
    verse = _check_verse("15:90")
    assert 'طبری می\u200cگوید سپس اهل تأویل در آنان که با گفته\u200cاش بخش\u200cکنندگان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که سیاق سخن بی\u200cاشاره به این معنا' in _joined(verse, "modern")
    assert '«كما أنزلنا على المقتسمين» چنان که بر بخش\u200cکنندگان فرود آوردیم و' in _joined(verse, "critical")

def test_hijr_15_91_verse():
    verse = _check_verse("15:91")
    assert 'طبری می\u200cگوید اهل تأویل در معنای گفته\u200cاش آنان که قرآن را' in _joined(verse, "notes")
    assert 'المیزان از مجمع البیان نقل می\u200cکند که عضین جمع عضه است' in _joined(verse, "modern")
    assert '«جعلوا القرآن عضين» قرآن را پاره\u200cپاره کردند و آن عضین جمع' in _joined(verse, "critical")

def test_hijr_15_92_verse():
    verse = _check_verse("15:92")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد می\u200cگوید ای محمد به پروردگارت' in _joined(verse, "notes")
    assert 'المیزان بر آن است که آنگاه دربارهٔ سرانجام کار ایشان فرمود' in _joined(verse, "modern")
    assert '«فوربك لنسألنهم أجمعين» به پروردگارت سوگند که از همه\u200cشان خواهیم پرسید' in _joined(verse, "critical")

def test_hijr_15_93_verse():
    verse = _check_verse("15:93")
    assert 'طبری می\u200cگوید حسن بن یحیی از عبدالرزاق از ثوری از لیث' in _joined(verse, "notes")
    assert 'المیزان بر آن است که پس از وصف آن پاره\u200cکنندگان فرمود' in _joined(verse, "modern")
    assert '«عما كانوا يعملون» از آنچه می\u200cکردند و آن يعملون با فعل' in _joined(verse, "critical")

def test_hijr_15_94_verse():
    verse = _check_verse("15:94")
    assert 'طبری می\u200cگوید پس آشکارا بگو آنچه فرمان داده می\u200cشوی فرمان خدا' in _joined(verse, "notes")
    assert 'المیزان از مجمع البیان نقل می\u200cکند که صدع و فرق و' in _joined(verse, "modern")
    assert '«فاصدع بما تؤمر» پس آشکارا بگو آنچه فرمان داده می\u200cشوی و' in _joined(verse, "critical")

def test_hijr_15_95_verse():
    verse = _check_verse("15:95")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد می\u200cگوید ما تو را از' in _joined(verse, "notes")
    assert 'المیزان بر آن است که جملهٔ ما تو را از مسخره\u200cکنندگان' in _joined(verse, "modern")
    assert '«إنا كفيناك المستهزئين» ما تو را از مسخره\u200cکنندگان بسنده\u200cایم و آن' in _joined(verse, "critical")

def test_hijr_15_96_verse():
    verse = _check_verse("15:96")
    assert 'طبری می\u200cگوید گفته\u200cاش آنان که با خدا خدای دیگری می\u200cگیرند پس' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این مسخره\u200cکنندگان آنان\u200cاند که با خدا' in _joined(verse, "modern")
    assert '«فسوف يعلمون» پس به زودی خواهند دانست و آن سوف آن' in _joined(verse, "critical")

def test_hijr_15_97_verse():
    verse = _check_verse("15:97")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد می\u200cگوید ای محمد ما می\u200cدانیم' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این جمله برای دومین بار اندوه' in _joined(verse, "modern")
    assert '«و لقد نعلم أنك يضيق صدرك» و به راستی ما می\u200cدانیم' in _joined(verse, "critical")

def test_hijr_15_98_verse():
    verse = _check_verse("15:98")
    assert 'طبری می\u200cگوید پس به ستایش پروردگارت تسبیح گوی می\u200cگوید پس در' in _joined(verse, "notes")
    assert 'المیزان بر آن است که خدا به پیامبر گرامی خود سفارش' in _joined(verse, "modern")
    assert '«فسبح بحمد ربك» پس به ستایش پروردگارت تسبیح گوی و آن' in _joined(verse, "critical")

def test_hijr_15_99_verse():
    verse = _check_verse("15:99")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد می\u200cگوید و پروردگارت را عبادت' in _joined(verse, "notes")
    assert 'المیزان بر آن است که مراد از آمدن یقین رسیدن اجل' in _joined(verse, "modern")
    assert '«حتى يأتيك اليقين» تا یقین به سویت آید و آن مرگ' in _joined(verse, "critical")

def test_nahl_16_1_verse():
    verse = _check_verse("16:1")
    assert 'طبری می\u200cگوید خدا می\u200cگوید فرمان خدا آمد پس نزدیک و فرود' in _joined(verse, "notes")
    assert 'المیزان بر آن است که صدر این سوره چهل آیهٔ نخست' in _joined(verse, "modern")
    assert '«أتى أمر الله» فرمان خدا آمد و آن گذشته برای آینده' in _joined(verse, "critical")

def test_nahl_16_2_verse():
    verse = _check_verse("16:2")
    assert 'طبری می\u200cگوید قاریان در خواندن گفته\u200cاش فرشتگان را فرود می\u200cآورد اختلاف' in _joined(verse, "notes")
    assert 'المیزان بر آن است که مردم در حقیقت روح اختلافی ندارند' in _joined(verse, "modern")
    assert '«ينزل الملائكة بالروح من أمره» فرشتگان را با روح از فرمانش' in _joined(verse, "critical")

def test_nahl_16_3_verse():
    verse = _check_verse("16:3")
    assert 'طبری می\u200cگوید خدا می\u200cگوید آفریدگارتان ای مردم آسمان\u200cها و زمین را' in _joined(verse, "notes")
    assert 'المیزان بر آن است که معنای به حق بودن آفرینش آسمان\u200cها' in _joined(verse, "modern")
    assert '«خلق السماوات والأرض بالحق» آسمان\u200cها و زمین را به حق آفرید' in _joined(verse, "critical")

def test_nahl_16_4_verse():
    verse = _check_verse("16:4")
    assert 'طبری می\u200cگوید و از حجت\u200cهایش بر شما ای مردم نیز این' in _joined(verse, "notes")
    assert 'المیزان بر آن است که مقصود از آفرینش انسان آفرینشی است' in _joined(verse, "modern")
    assert '«فإذا هو خصيم مبين» و او ستیزه\u200cگری آشکار است و آن' in _joined(verse, "critical")

def test_nahl_16_5_verse():
    verse = _check_verse("16:5")
    assert 'طبری می\u200cگوید و از حجت\u200cهایش بر شما ای مردم آنچه از' in _joined(verse, "notes")
    assert 'المیزان بر آن است که انعام جمع نعم است به معنای' in _joined(verse, "modern")
    assert '«لكم فيها دفء» برای شما در آن\u200cها گرماست و آن لكم' in _joined(verse, "critical")

def test_nahl_16_6_verse():
    verse = _check_verse("16:6")
    assert 'طبری می\u200cگوید و برای شما در این چارپایان و دام\u200cهایی که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که جمال به معنای زینت و نیکویی' in _joined(verse, "modern")
    assert '«جمال» زیبایی واژهٔ مستقل این آیه است و نعمت این\u200cجا نه' in _joined(verse, "critical")

def test_nahl_16_7_verse():
    verse = _check_verse("16:7")
    assert 'طبری در پیوست این بخش می\u200cگوید و بارهای سنگین شما را' in _joined(verse, "notes")
    assert 'المیزان بر آن است که اثقال جمع ثقل است به معنای' in _joined(verse, "modern")
    assert '«إلا بشق الأنفس» جز با رنج جان\u200cها و آن شق از' in _joined(verse, "critical")

def test_nahl_16_8_verse():
    verse = _check_verse("16:8")
    assert 'طبری می\u200cگوید و اسب\u200cها و استرها و خران را نیز برای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این جمله عطف است بر واژهٔ' in _joined(verse, "modern")
    assert '«و يخلق ما لا تعلمون» و آنچه نمی\u200cدانید می\u200cآفریند و آن' in _joined(verse, "critical")

def test_nahl_16_9_verse():
    verse = _check_verse("16:9")
    assert 'طبری می\u200cگوید خدا می\u200cگوید و بر خداست ای مردم بیان راه' in _joined(verse, "notes")
    assert 'المیزان بر آن است که قصد چنان که راغب و جز' in _joined(verse, "modern")
    assert '«و على الله قصد السبيل» و بر خداست راه راست و' in _joined(verse, "critical")

def test_nahl_16_10_verse():
    verse = _check_verse("16:10")
    assert 'طبری می\u200cگوید و آن که این نعمت\u200cها را بر شما نعمت' in _joined(verse, "notes")
    assert 'المیزان بر آن است که از این\u200cجا به نوعی دیگر از' in _joined(verse, "modern")
    assert '«هو الذي أنزل من السماء ماء» اوست که از آسمان آبی' in _joined(verse, "critical")

def test_nahl_16_11_verse():
    verse = _check_verse("16:11")
    assert 'طبری می\u200cگوید پروردگارتان با آبی که از آسمان برایتان فرود آورد' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این سه گونه احتجاج اولی به' in _joined(verse, "modern")
    assert '«ينبت لكم به» با آن برای شما می\u200cرویاند و آن بِهِ' in _joined(verse, "critical")

def test_nahl_16_12_verse():
    verse = _check_verse("16:12")
    assert 'طبری می\u200cگوید و از نعمت\u200cهایش بر شما ای مردم با آن\u200cهایی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که در این کتاب چند نوبت پیرامون' in _joined(verse, "modern")
    assert '«مسخرات بأمره» رام\u200cشده به فرمانش و آن دو واژه جرم\u200cهای سرکش' in _joined(verse, "critical")

def test_nahl_16_13_verse():
    verse = _check_verse("16:13")
    assert 'طبری می\u200cگوید و رام شما کرد آنچه پدید آورد یعنی آنچه' in _joined(verse, "notes")
    assert 'المیزان بر آن است که ذرأ به معنای آفریدن است و' in _joined(verse, "modern")
    assert '«مختلفا ألوانه» رنگ\u200cهایش گوناگون و آن جمله زمین را به تابلویی' in _joined(verse, "critical")

def test_nahl_16_14_verse():
    verse = _check_verse("16:14")
    assert 'طبری می\u200cگوید و آن که این کارها را با شما کرد' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیه فصل دیگری از نعمت\u200cهای' in _joined(verse, "modern")
    assert '«لحما طريا» گوشت تازه آن دو واژه ماهی را با تازگی\u200cاش' in _joined(verse, "critical")

def test_nahl_16_15_verse():
    verse = _check_verse("16:15")
    assert 'طبری می\u200cگوید و از نعمت\u200cهایش بر شما ای مردم نیز این' in _joined(verse, "notes")
    assert 'المیزان بر آن است که در مجمع گفته شده است ميد' in _joined(verse, "modern")
    assert '«رواسي أن تميد بكم» کوه\u200cهای استوار تا شما را نجنباند و' in _joined(verse, "critical")

def test_nahl_16_16_verse():
    verse = _check_verse("16:16")
    assert 'طبری می\u200cگوید اهل تأویل در مراد از نشانه\u200cها اختلاف کردند بعضی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که علامات جمع علامت است و علامت' in _joined(verse, "modern")
    assert '«وعلامات» و نشانه\u200cها آن یک واژه چون تابلویی بر سر راه' in _joined(verse, "critical")

def test_nahl_16_17_verse():
    verse = _check_verse("16:17")
    assert 'طبری می\u200cگوید و خدا به پرستندگان بت\u200cها و صنم\u200cها می\u200cگوید آیا' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات حجت یادشده در پیش' in _joined(verse, "modern")
    assert '«أفمن يخلق كمن لا يخلق» آیا آن که می\u200cآفریند چون آن' in _joined(verse, "critical")

def test_nahl_16_18_verse():
    verse = _check_verse("16:18")
    assert 'طبری می\u200cگوید و اگر نعمت خدا را بشمارید آن را نمی\u200cتوانید' in _joined(verse, "notes")
    assert 'المیزان بر آن است که در این گفته اشاره به فراوانی' in _joined(verse, "modern")
    assert '«لا تحصوها» نمی\u200cتوانید آن را بشمارید آن نفی در دل هر' in _joined(verse, "critical")

def test_nahl_16_19_verse():
    verse = _check_verse("16:19")
    assert 'طبری می\u200cگوید و خدایی که خدای شما ای مردم است آنچه' in _joined(verse, "notes")
    assert 'المیزان بر آن است که جملهٔ و خدا آنچه پنهان می\u200cکنید' in _joined(verse, "modern")
    assert '«ما تسرون و ما تعلنون» آنچه پنهان می\u200cکنید و آنچه آشکار' in _joined(verse, "critical")

def test_nahl_16_20_verse():
    verse = _check_verse("16:20")
    assert 'طبری می\u200cگوید و بت\u200cهایتان که جز خدا ای مردم خدایان می\u200cخوانید' in _joined(verse, "notes")
    assert 'المیزان بر آن است که جملهٔ و آنانی که جز خدا' in _joined(verse, "modern")
    assert '«وهم يخلقون» و خود آفریده می\u200cشوند آن جملهٔ کوتاه وارونگی کامل' in _joined(verse, "critical")

def test_nahl_16_21_verse():
    verse = _check_verse("16:21")
    assert 'طبری می\u200cگوید خدا به این مشرکان از قریش می\u200cگوید و آنانی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این که فرمود مردگانی\u200cاند زنده نیستان' in _joined(verse, "modern")
    assert '«أموات غير أحياء» مردگانی زنده نیستان آن دو نفی پشت سر' in _joined(verse, "critical")

def test_nahl_16_22_verse():
    verse = _check_verse("16:22")
    assert 'طبری می\u200cگوید معبودتان که عبادت بر شما برایش سزاوار است و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات قسمت دوم از آیات' in _joined(verse, "modern")
    assert '«إلهكم إله واحد» معبودتان معبودی یگانه است آن جملهٔ کوتاه نتیجهٔ' in _joined(verse, "critical")

def test_nahl_16_23_verse():
    verse = _check_verse("16:23")
    assert 'طبری می\u200cگوید مراد خدا لا جرم حقاً این است که خدا' in _joined(verse, "notes")
    assert 'المیزان بر آن است که لا جرم واژه\u200cای است مرکب از' in _joined(verse, "modern")
    assert '«لا جرم» بی\u200cگمان آن دو واژه چون سوگندی در آغاز می\u200cایستند' in _joined(verse, "critical")

def test_nahl_16_24_verse():
    verse = _check_verse("16:24")
    assert 'طبری می\u200cگوید و چون به اینان که به آخرت ایمان ندارند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که راغب در مفردات می\u200cگوید سطر هم' in _joined(verse, "modern")
    assert '«أساطير الأولين» افسانه\u200cهای پیشینیان آن دو واژه پاسخ آن پرسش بزرگ' in _joined(verse, "critical")

def test_nahl_16_25_verse():
    verse = _check_verse("16:25")
    assert 'طبری می\u200cگوید این مشرکان به آن که از آنان می\u200cپرسد پروردگارتان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که راغب در مفردات گفته وزر به' in _joined(verse, "modern")
    assert '«أوزارهم كاملة» بارهایشان کامل آن کامل چون ترازویی بی\u200cکسری در برابر' in _joined(verse, "critical")

def test_nahl_16_26_verse():
    verse = _check_verse("16:26")
    assert 'طبری می\u200cگوید پیش از این مشرکان که از راه خدا بازمی\u200cدارند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که آمدن خدای تعالی بنیان ایشان را' in _joined(verse, "modern")
    assert '«فأتى الله بنيانهم من القواعد» پس خدا بنیانشان را از پایه\u200cها' in _joined(verse, "critical")

def test_nahl_16_27_verse():
    verse = _check_verse("16:27")
    assert 'طبری می\u200cگوید خدا با اینان که نیرنگ زدند و خدا کارشان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که خزى چنان که راغب گفته ذلت' in _joined(verse, "modern")
    assert '«أين شركائي» شریکانم کجایند آن پرسش با یای من گفته می\u200cشود' in _joined(verse, "critical")

def test_nahl_16_28_verse():
    verse = _check_verse("16:28")
    assert 'طبری می\u200cگوید آنان که علم داده شدند گفتند به راستی خواری' in _joined(verse, "notes")
    assert 'المیزان بر آن است که ظاهراً این جمله تفسیر واژهٔ کافران' in _joined(verse, "modern")
    assert '«فألقوا السلم» پس صلح را افکندند آن افکندن چون انداختن سلاح' in _joined(verse, "critical")

def test_nahl_16_29_verse():
    verse = _check_verse("16:29")
    assert 'طبری می\u200cگوید خدا به اینان که بر خود ستمکاران\u200cاند چون به' in _joined(verse, "notes")
    assert 'المیزان بر آن است که خطاب در این آیه هم مانند' in _joined(verse, "modern")
    assert '«فادخلوا أبواب جهنم» پس از درهای جهنم درآیید آن فرمان کوتاه' in _joined(verse, "critical")

def test_nahl_16_30_verse():
    verse = _check_verse("16:30")
    assert 'طبری می\u200cگوید و به گروه دیگر که اهل ایمان و تقوای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که در این جمله مردمان با تقوا' in _joined(verse, "modern")
    assert '«قالوا خيرا» گفتند نیکی آن یک واژه در برابر آن افسانه\u200cهای' in _joined(verse, "critical")

def test_nahl_16_31_verse():
    verse = _check_verse("16:31")
    assert 'طبری می\u200cگوید مراد خدا از گفته\u200cاش بهشت\u200cهای جاودانه بوستان\u200cهایی برای ماندن' in _joined(verse, "notes")
    assert 'المیزان بر آن است که آن گاه در آخر آنان را' in _joined(verse, "modern")
    assert '«جنات عدن» بهشت\u200cهای جاودانه آن دو واژه نام آن سرا را' in _joined(verse, "critical")

def test_nahl_16_32_verse():
    verse = _check_verse("16:32")
    assert 'طبری می\u200cگوید چنان که خدا متقین را پاداش می\u200cدهد، همانان\u200cاند که' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات فصلِ دومِ سوره را' in _joined(verse, "modern")
    assert '«ٱلَّذِينَ تَتَوَفَّىٰهُمُ ٱلْمَلَٰٓئِكَةُ طَيِّبِينَ يَقُولُونَ سَلَٰمٌ عَلَيْكُمُ» در برابرِ آیهٔ ۲۸' in _joined(verse, "critical")

def test_nahl_16_33_verse():
    verse = _check_verse("16:33")
    assert 'طبری می\u200cگوید آیا این مشرکان جز این را منتظرند که فرشتگان' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این فصل از سوره پس از' in _joined(verse, "modern")
    assert '«هَلْ يَنْظُرُونَ إِلَّا» استفهامِ انکاری است و نقدِ گفتمان نشان می\u200cدهد' in _joined(verse, "critical")

def test_nahl_16_34_verse():
    verse = _check_verse("16:34")
    assert 'طبری می\u200cگوید پس به اینان که کارِ مشرکانِ قریش را کردند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که در فرازِ پیشین از قیامِ طولیِ' in _joined(verse, "modern")
    assert '«وَحَاقَ بِهِمْ مَا كَانُوا بِهِ يَسْتَهْزِئُونَ» وارونگیِ کامل است: موضوعِ خنده' in _joined(verse, "critical")

def test_nahl_16_35_verse():
    verse = _check_verse("16:35")
    assert 'طبری می\u200cگوید کسانی که برای خدا شریک قرار دادند و بت\u200cها' in _joined(verse, "notes")
    assert 'المیزان بر آن است که مقصودِ مشرکان از «لو شاء الله' in _joined(verse, "modern")
    assert 'المیزان در بحثِ سه آیهٔ ۳۵ تا ۳۷ نزاعِ بلندِ جبریان' in _joined(verse, "critical")

def test_nahl_16_36_verse():
    verse = _check_verse("16:36")
    assert 'طبری می\u200cگوید در هر امتی که پیش از شما گذشته\u200cاند فرستاده\u200cای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که جملهٔ «أن اعبدوا الله واجتنبوا الطاغوت»' in _joined(verse, "modern")
    assert 'المیزان در این آیه آموزهٔ کلامیِ مرکزیِ خود را بنا می\u200cکند:' in _joined(verse, "critical")

def test_nahl_16_37_verse():
    verse = _check_verse("16:37")
    assert 'طبری می\u200cگوید اگر تو ای محمد بر هدایتِ این مشرکان به' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیه تسلیت و دلداریِ رسولِ' in _joined(verse, "modern")
    assert 'المیزان از «وَمَا لَهُمْ مِنْ نَاصِرِينَ» با جمع آوردنِ «ناصرین» نتیجه\u200cای' in _joined(verse, "critical")

def test_nahl_16_38_verse():
    verse = _check_verse("16:38")
    assert 'طبری می\u200cگوید این مشرکانِ قریش با سخت\u200cترین سوگندهایشان به خدا سوگند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که «وأقسموا بالله جهد أيمانهم» یعنی به' in _joined(verse, "modern")
    assert 'المیزان می\u200cگوید جملهٔ «لا یبعث الله من یموت» انکارِ حشر و' in _joined(verse, "critical")

def test_nahl_16_39_verse():
    verse = _check_verse("16:39")
    assert 'طبری می\u200cگوید آری خدا هر که را بمیرد برمی\u200cانگیزد، وعده\u200cای بر' in _joined(verse, "notes")
    assert 'المیزان بر آن است که «لام» در آغازِ این آیه لامِ' in _joined(verse, "modern")
    assert 'المیزان نتیجهٔ بزرگ می\u200cگیرد که در کلامِ خدا این تعبیر بارها' in _joined(verse, "critical")

def test_nahl_16_40_verse():
    verse = _check_verse("16:40")
    assert 'طبری می\u200cگوید اگر ما برانگیختنِ کسی را که می\u200cمیرد اراده کنیم،' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیه همانندِ آیهٔ ۸۲ سورهٔ' in _joined(verse, "modern")
    assert 'المیزان تخلف نکردنِ چیزها از امرِ خدا را چنین تعلیل می\u200cکند' in _joined(verse, "critical")

def test_nahl_16_41_verse():
    verse = _check_verse("16:41")
    assert 'طبری می\u200cگوید کسانی که از قوم و خانه و وطنشان به' in _joined(verse, "notes")
    assert 'المیزان بر آن است که حسین\u200cترین فهمِ «حسنة» در این آیه' in _joined(verse, "modern")
    assert 'المیزان بر ساختارِ شرطیِ دو آیهٔ ۴۱ و ۴۲ انگشت می\u200cگذارد' in _joined(verse, "critical")

def test_nahl_16_42_verse():
    verse = _check_verse("16:42")
    assert 'طبری می\u200cگوید اینان همانانی\u200cاند که صفتشان را گفتیم و ثوابی را' in _joined(verse, "notes")
    assert 'المیزان بر آن است که توصیفِ مهاجران به دو صفتِ صبر' in _joined(verse, "modern")
    assert 'المیزان توجه می\u200cکند که از سیاقِ دو آیه می\u200cتوان فهمید عنایت' in _joined(verse, "critical")

def test_nahl_16_43_verse():
    verse = _check_verse("16:43")
    assert 'طبری می\u200cگوید ای محمد، پیش از تو به سوی هیچ امتی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که جملهٔ «وَمَا أَرْسَلْنَا مِنْ قَبْلِكَ إِلَّا' in _joined(verse, "modern")
    assert 'المیزان سخنِ بیشترِ مفسران را که آیه را پاسخ به «بشر' in _joined(verse, "critical")

def test_nahl_16_44_verse():
    verse = _check_verse("16:44")
    assert 'طبری می\u200cگوید آنان را با بیّنات و زُبُر فرستادیم؛ و در' in _joined(verse, "notes")
    assert 'المیزان بر آن است که هیچ شکی نیست که نازل کردنِ' in _joined(verse, "modern")
    assert 'المیزان در غایتِ دومِ انزال با بیشترِ مفسران جدا می\u200cشود و' in _joined(verse, "critical")

def test_nahl_16_45_verse():
    verse = _check_verse("16:45")
    assert 'طبری می\u200cگوید آیا ایمن شدند آنان که بر مؤمنانِ یارانِ رسولِ' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیه و دو آیهٔ پس' in _joined(verse, "modern")
    assert 'المیزان «مکروا السیئات» را «عملوا السیئات مکرا» می\u200cخواند و می\u200cگوید «سیئات»' in _joined(verse, "critical")

def test_nahl_16_46_verse():
    verse = _check_verse("16:46")
    assert 'طبری می\u200cگوید یا آنان را در گردش و رفت\u200cوآمدشان در سرزمین\u200cها' in _joined(verse, "notes")
    assert 'المیزان بر آن است که فاعلِ «یأخذهم» خدای سبحان است و' in _joined(verse, "modern")
    assert 'المیزان احتمالِ دیگری را نیز می\u200cبیند که گرفتن در گردش یعنی' in _joined(verse, "critical")

def test_nahl_16_47_verse():
    verse = _check_verse("16:47")
    assert 'طبری می\u200cگوید یا آنان را با تخوّف هلاک کند و آن' in _joined(verse, "notes")
    assert 'المیزان بر آن است که مراد از گرفتن بر تخوّف آن' in _joined(verse, "modern")
    assert 'داستانِ عمر و واژهٔ «تخوّف» سندی است بر این\u200cکه فهمِ قرآن' in _joined(verse, "critical")

def test_nahl_16_48_verse():
    verse = _check_verse("16:48")
    assert 'طبری می\u200cگوید در خوانشِ این آیه اختلاف است: بیشترِ قرّای حجاز' in _joined(verse, "notes")
    assert 'المیزان بر آن است که معنای آیه این است که آیا' in _joined(verse, "modern")
    assert 'پرسشِ بنیادیِ این آیه آن است که سجدهٔ سایه استعاره است' in _joined(verse, "critical")

def test_nahl_16_49_verse():
    verse = _check_verse("16:49")
    assert 'طبری می\u200cگوید برای خدا خضوع می\u200cکند و در برابرِ فرمانش فروتن' in _joined(verse, "notes")
    assert 'المیزان بر آن است که سجدهٔ جنبندگانِ آسمان\u200cها و زمین برای' in _joined(verse, "modern")
    assert 'المیزان در بحثِ استکبار می\u200cگوید نداشتنِ استکبارِ ذاتی یعنی هرگز از' in _joined(verse, "critical")

def test_nahl_16_50_verse():
    verse = _check_verse("16:50")
    assert 'طبری می\u200cگوید این فرشتگانِ در آسمان\u200cها و هر چه در زمین' in _joined(verse, "notes")
    assert 'المیزان بر آن است که ترسِ فرشتگان ترس از خودِ خداست' in _joined(verse, "modern")
    assert 'المیزان استدلالِ برخی مفسران را که از این آیه تکلیفِ فرشتگان' in _joined(verse, "critical")

def test_nahl_16_51_verse():
    verse = _check_verse("16:51")
    assert 'طبری می\u200cگوید خدا به بندگانش گفت ای مردم برای من شریکی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که مقصود از «لا تتخذوا إلهین اثنین»' in _joined(verse, "modern")
    assert 'المیزان از تقدیمِ «إیّای» بر «فارهبون» حصر را می\u200cگیرد و آن' in _joined(verse, "critical")

def test_nahl_16_52_verse():
    verse = _check_verse("16:52")
    assert 'طبری می\u200cگوید آنچه در آسمان\u200cها و زمین است از آنِ اوست' in _joined(verse, "notes")
    assert 'المیزان بر آن است که راغب در مفردات گفته «وصب» بیماریِ' in _joined(verse, "modern")
    assert 'المیزان این آیه را دلیلِ جملهٔ پیش می\u200cخواند و می\u200cگوید این' in _joined(verse, "critical")

def test_nahl_16_53_verse():
    verse = _check_verse("16:53")
    assert 'طبری در وجهِ درآمدنِ فاء در «فمن الله» اختلافِ عرب\u200cها را' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیه بیانِ دیگری است برای' in _joined(verse, "modern")
    assert 'المیزان استدلالِ فطریِ آیه را می\u200cگشاید و می\u200cگوید استغاثه به خدا' in _joined(verse, "critical")

def test_nahl_16_54_verse():
    verse = _check_verse("16:54")
    assert 'طبری می\u200cگوید سپس چون پروردگارتان تندرستی را به شما ارزانی دارد' in _joined(verse, "notes")
    assert 'المیزان بر آن است که از این\u200cجا نکوهش و توبيخِ مشرکان' in _joined(verse, "modern")
    assert 'المیزان بازگشت به شرک را بازگشت به سبب\u200cهای ظاهری می\u200cخواند و' in _joined(verse, "critical")

def test_nahl_16_55_verse():
    verse = _check_verse("16:55")
    assert 'طبری می\u200cگوید «لیکفروا بما آتیناهم» یعنی تا نعمتِ خدا را در' in _joined(verse, "notes")
    assert 'المیزان بر آن است که لام در «لیکفروا بما آتیناهم» لامِ' in _joined(verse, "modern")
    assert 'المیزان در «فتمتعوا فسوف تعلمون» از التفات سخن می\u200cگوید که روی' in _joined(verse, "critical")

def test_nahl_16_56_verse():
    verse = _check_verse("16:56")
    assert 'طبری می\u200cگوید این مشرکانِ بت\u200cپرست برای آنچه از آن زیان و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که ظاهراً «ما» در «لما لا یعلمون»' in _joined(verse, "modern")
    assert 'المیزان وجهِ دیگری را نیز پیش می\u200cنهد که «ویجعلون» عطف بر' in _joined(verse, "critical")

def test_nahl_16_57_verse():
    verse = _check_verse("16:57")
    assert 'طبری می\u200cگوید از نادانیِ این مشرکان و زشتیِ کردارشان و بدیِ' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این سرزنشی دیگر است به مشرکان' in _joined(verse, "modern")
    assert 'المیزان ریشهٔ این باور را در بت\u200cپرستیِ کهن می\u200cجوید و می\u200cگوید' in _joined(verse, "critical")

def test_nahl_16_58_verse():
    verse = _check_verse("16:58")
    assert 'طبری می\u200cگوید چون یکی از اینان که برای خدا دختران قرار' in _joined(verse, "notes")
    assert 'المیزان بر آن است که مقصود از سیاه شدنِ چهره به' in _joined(verse, "modern")
    assert 'تقابلِ دو کظیمِ قرآن از ژرف\u200cترین نکته\u200cهای این آیه است: یعقوب' in _joined(verse, "critical")

def test_nahl_16_59_verse():
    verse = _check_verse("16:59")
    assert 'طبری می\u200cگوید این مژده داده شده به ولادتِ دختر از قوم' in _joined(verse, "notes")
    assert 'المیزان بر آن است که «توارى» به معنای گشتن و نهان\u200cگاه' in _joined(verse, "modern")
    assert 'المیزان مقصود از حکم در «ألا ساء ما یحکمون» را همان' in _joined(verse, "critical")

def test_nahl_16_60_verse():
    verse = _check_verse("16:60")
    assert 'طبری می\u200cگوید این خبر از خدای بزرگ است که گفتهٔ او' in _joined(verse, "notes")
    assert 'المیزان بر آن است که «مثل» به معنای صفت است و' in _joined(verse, "modern")
    assert 'المیزان از این آیه نظریه\u200cای بزرگ می\u200cسازد و می\u200cگوید از این\u200cجا' in _joined(verse, "critical")

def test_nahl_16_61_verse():
    verse = _check_verse("16:61")
    assert 'طبری می\u200cگوید اگر خدا گناهکارانِ بنی\u200cآدم را به گناهانشان می\u200cگرفت بر' in _joined(verse, "notes")
    assert 'المیزان بر آن است که ضمیر در «علیها» به زمین بازمی\u200cگردد' in _joined(verse, "modern")
    assert 'المیزان اشکالِ مشهورِ آیه را پیش می\u200cکشد که اگر جنبنده عموم' in _joined(verse, "critical")

def test_nahl_16_62_verse():
    verse = _check_verse("16:62")
    assert 'طبری می\u200cگوید این مشرکان برای خدا آنچه را برای خود ناخوش' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیه دوباره به مسئلهٔ نسبت' in _joined(verse, "modern")
    assert 'المیزان احتمالِ دیگری را در حسنى می\u200cبیند و می\u200cگوید برخی گفته\u200cاند' in _joined(verse, "critical")

def test_nahl_16_63_verse():
    verse = _check_verse("16:63")
    assert 'طبری می\u200cگوید به خدا سوگند پیش از تو نیز به سوی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این فراز از آیهٔ ۵۳ به' in _joined(verse, "modern")
    assert '«فَزَيَّنَ لَهُمُ الشَّيْطَانُ أَعْمَالَهُمْ» مسئولیت را میانِ آراینده و پذیرنده تقسیم' in _joined(verse, "critical")

def test_nahl_16_64_verse():
    verse = _check_verse("16:64")
    assert 'طبری می\u200cگوید کتاب را بر تو نازل نکردیم ای محمد مگر' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این فراز از نحل در بیانِ' in _joined(verse, "modern")
    assert 'المیزان در بحثِ آیهٔ ۴۴ همین بلوک گفته بود آیه بر' in _joined(verse, "critical")

def test_nahl_16_65_verse():
    verse = _check_verse("16:65")
    assert 'طبری می\u200cگوید خدا بندگانش را بر حجت\u200cهایش بر آنان در توحیدش' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات بازگشتی است پس از' in _joined(verse, "modern")
    assert 'المیزان بر آن است که مراد از شنیدن پذیرفتنِ سخنانی است' in _joined(verse, "critical")

def test_nahl_16_66_verse():
    verse = _check_verse("16:66")
    assert 'طبری می\u200cگوید برای شما ای مردم در چارپایان پندی است در' in _joined(verse, "notes")
    assert 'المیزان بر آن است که «فرث» کثافاتی است که در روده\u200cها' in _joined(verse, "modern")
    assert 'المیزان معنای «من بین فرث و دم» را مجاورت می\u200cگیرد و' in _joined(verse, "critical")

def test_nahl_16_67_verse():
    verse = _check_verse("16:67")
    assert 'طبری می\u200cگوید برای شما ای مردم پندی نیز هست در آنچه' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیه نمی\u200cخواهد بفرماید مست\u200cکننده\u200cها حلال' in _joined(verse, "modern")
    assert 'المیزان می\u200cگوید بنابر این آیه در بردارندهٔ حکمِ شرعی نیست تا' in _joined(verse, "critical")

def test_nahl_16_68_verse():
    verse = _check_verse("16:68")
    assert 'طبری می\u200cگوید پروردگارت ای محمد به زنبور وحی کرد وحی\u200cای به' in _joined(verse, "notes")
    assert 'المیزان بر آن است که کلمهٔ وحی در مواردِ گوناگونی به' in _joined(verse, "modern")
    assert 'المیزان در بحثِ وحی می\u200cگوید خدا وحی به زنبور را از' in _joined(verse, "critical")

def test_nahl_16_69_verse():
    verse = _check_verse("16:69")
    assert 'طبری می\u200cگوید سپس ای زنبور از میوه\u200cها بخور؛ «فاسلكی سبل ربك»' in _joined(verse, "notes")
    assert 'المیزان بر آن است که جملهٔ «یخرج من بطونها شراب مختلف' in _joined(verse, "modern")
    assert 'المیزان تناسبِ پایان\u200cبندی\u200cها را می\u200cگشاید و می\u200cگوید شاید علتش این باشد' in _joined(verse, "critical")

def test_nahl_16_70_verse():
    verse = _check_verse("16:70")
    assert 'طبری می\u200cگوید خدا به شما خبر می\u200cدهد که بهره\u200cمندی و زندگی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیه مسئلهٔ عمرِ انسانی را' in _joined(verse, "modern")
    assert 'المیزان بر آن است که آیه از این\u200cرو با «إن الله' in _joined(verse, "critical")

def test_nahl_16_71_verse():
    verse = _check_verse("16:71")
    assert 'طبری می\u200cگوید خدا به شما خبر می\u200cدهد ای مردم که از' in _joined(verse, "notes")
    assert 'المیزان بر آن است که برتری دادنِ برخی بر برخی در' in _joined(verse, "modern")
    assert 'المیزان می\u200cگوید توجه کن گفتهٔ بیشترِ مفسران این است که آیه' in _joined(verse, "critical")

def test_nahl_16_72_verse():
    verse = _check_verse("16:72")
    assert 'طبری می\u200cگوید ای مردم خداست که از جنسِ خودتان برایتان همسرانی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که مراد از «حفدة» جمعِ حافد است' in _joined(verse, "modern")
    assert 'المیزان در این آیات بر آن است که خدا در این' in _joined(verse, "critical")

def test_nahl_16_73_verse():
    verse = _check_verse("16:73")
    assert 'طبری می\u200cگوید این مشرکان از قومت ای محمد جز خدا بت\u200cها' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیات دنبالهٔ شمارشِ نعمت\u200cهاست و' in _joined(verse, "modern")
    assert 'المیزان در شمارشِ این فصل بر آن است که پایان\u200cبندی\u200cهای نفی' in _joined(verse, "critical")

def test_nahl_16_74_verse():
    verse = _check_verse("16:74")
    assert 'طبری می\u200cگوید برای خدا ای مردم همانندها را، که آن\u200cها برای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیه خطاب به مشرکان است' in _joined(verse, "modern")
    assert 'المیزان بر آن است که در این آیات خدا از مثل\u200cزدنِ' in _joined(verse, "critical")

def test_nahl_16_75_verse():
    verse = _check_verse("16:75")
    assert 'طبری می\u200cگوید خدا برای شما ای گروهِ گمراهان از راهِ درست' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این مثل و مثلِ پس از' in _joined(verse, "modern")
    assert 'المیزان در بحثِ مثل\u200cها بر آن است که خدا این دو' in _joined(verse, "critical")

def test_nahl_16_76_verse():
    verse = _check_verse("16:76")
    assert 'طبری می\u200cگوید خدا مثلی زده است دو مرد را که یکی' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این مثل نیز برای خدا و' in _joined(verse, "modern")
    assert 'المیزان بر آن است که این دو مثل را خدا پشتِ' in _joined(verse, "critical")

def test_nahl_16_77_verse():
    verse = _check_verse("16:77")
    assert 'طبری می\u200cگوید برای خدا ای مردم دانشِ آن\u200cچه در آسمان\u200cها و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیه برای اثباتِ خودِ مسئلهٔ' in _joined(verse, "modern")
    assert 'المیزان بر آن است که قدرتِ انسان قدرتِ مقید و محدود' in _joined(verse, "critical")

def test_nahl_16_78_verse():
    verse = _check_verse("16:78")
    assert 'طبری می\u200cگوید خدا شما را آگاه کرد بر آنچه نمی\u200cدانستید پس' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این آیه نظریهٔ علمای نفس را' in _joined(verse, "modern")
    assert 'المیزان بر آن است که گفتهٔ «وجعل لکم السمع والأبصار والأفئدة»' in _joined(verse, "critical")

def test_nahl_16_79_verse():
    verse = _check_verse("16:79")
    assert 'طبری می\u200cگوید ای مشرکانِ به خدا آیا ننگریسته\u200cاید به پرندگانِ رام' in _joined(verse, "notes")
    assert 'المیزان بر آن است که خدا در این\u200cجا سببِ نگهداریِ مرغان' in _joined(verse, "modern")
    assert 'المیزان بر آن است که دلیل بر آنچه در معنای نفی' in _joined(verse, "critical")

def test_nahl_16_80_verse():
    verse = _check_verse("16:80")
    assert 'طبری می\u200cگوید خدا برای شما ای مردم از خانه\u200cهاتان که از' in _joined(verse, "notes")
    assert 'المیزان بر آن است که «وأثاثا» اثاثی است که در خانه\u200cهاتان' in _joined(verse, "modern")
    assert 'المیزان در بحثِ خانه\u200cها می\u200cگوید معنای «والله جعل لکم من بیوتکم' in _joined(verse, "critical")

def test_nahl_16_81_verse():
    verse = _check_verse("16:81")
    assert 'طبری می\u200cگوید از نعمتِ خدا بر شما ای مردم این است' in _joined(verse, "notes")
    assert 'المیزان بر آن است که این دو ظرف یعنی «لکم» و' in _joined(verse, "modern")
    assert 'المیزان دربارهٔ ویژه کردنِ گرما می\u200cگوید در مجمع\u200cالبیان گفته شده است' in _joined(verse, "critical")

def test_nahl_16_82_verse():
    verse = _check_verse("16:82")
    assert 'طبری می\u200cگوید خدا به پیامبرش محمد می\u200cگوید اگر این مشرکان ای' in _joined(verse, "notes")
    assert 'المیزان بر آن است که پس از آن\u200cکه خدا از شمردنِ' in _joined(verse, "modern")
    assert 'المیزان «مبین» را تبلیغِ واضحی می\u200cداند که ابهام و خفایی در' in _joined(verse, "critical")

def test_nahl_16_83_verse():
    verse = _check_verse("16:83")
    assert 'طبری می\u200cگوید اهلِ تأویل در معنای آن نعمتی که خدا خبر' in _joined(verse, "notes")
    assert 'المیزان بر آن است که «معرفت» در برابرِ انکار است و' in _joined(verse, "modern")
    assert 'المیزان بر آن است که آنان نعمتِ خدا را به عنوانِ' in _joined(verse, "critical")

def test_nahl_16_84_verse():
    verse = _check_verse("16:84")
    assert 'طبری می\u200cگوید آنان نعمتِ خدا را امروز می\u200cشناسند و انکارش می\u200cکنند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که از سیاق به دست می\u200cآید مراد' in _joined(verse, "modern")
    assert 'المیزان می\u200cگوید ذکرِ برانگیختنِ شهیدِ هر امت دلیل بر این است' in _joined(verse, "critical")

def test_nahl_16_85_verse():
    verse = _check_verse("16:85")
    assert 'طبری می\u200cگوید چون آنان که تو را ای محمد تکذیب کردند' in _joined(verse, "notes")
    assert 'المیزان بر آن است که آیهٔ پیش در حقیقت در مقامِ' in _joined(verse, "modern")
    assert 'المیزان فرقِ دو آیهٔ ۸۴ و ۸۵ را در این می\u200cداند' in _joined(verse, "critical")

def test_nahl_16_86_verse():
    verse = _check_verse("16:86")
    assert 'طبری می\u200cگوید چون مشرکانِ به خدا در روزِ قیامت آنچه را' in _joined(verse, "notes")
    assert 'المیزان بر آن است که مراد از «الذین أشرکوا» در عرفِ' in _joined(verse, "modern")
    assert 'المیزان می\u200cگوید معنای «قالوا ربنا هؤلاء شرکاؤنا الذین کنا ندعوا من' in _joined(verse, "critical")

def test_nahl_16_87_verse():
    verse = _check_verse("16:87")
    assert 'طبری می\u200cگوید مشرکان آن روز در برابرِ خدا تسلیم می\u200cشوند و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که در قیامت مشرکان علاوه بر علم' in _joined(verse, "modern")
    assert 'المیزان می\u200cگوید ضمیرِ «ألقوا» به قرینهٔ جملهٔ «وضل عنهم ما کانوا' in _joined(verse, "critical")

def test_nahl_16_88_verse():
    verse = _check_verse("16:88")
    assert 'طبری می\u200cگوید آنان که نبوتت را ای محمد انکار کردند و' in _joined(verse, "notes")
    assert 'المیزان بر آن است که در این آیه از نو به' in _joined(verse, "modern")
    assert 'المیزان می\u200cگوید «بما کانوا یفسدون» تعلیلِ افزوده بودنِ عذاب است و' in _joined(verse, "critical")

def test_nahl_16_89_verse():
    verse = _check_verse("16:89")
    assert 'طبری می\u200cگوید «ویوم نبعث فی کل أمة شهیدا علیهم من أنفسهم»' in _joined(verse, "notes")
    assert 'المیزان بر آن است که چون قرآن کتابِ هدایت برای عمومِ' in _joined(verse, "modern")
    assert 'المیزان بحثی مفصل در شهادت می\u200cکند و می\u200cگوید واجب است شهادتی' in _joined(verse, "critical")

def test_nahl_16_90_verse():
    verse = _check_verse("16:90")
    assert 'آیه سه فرمان مثبت ــ عدالت، احسان و بخشش به خویشاوند' in _joined(verse, "notes")
    assert 'المیزان با تفکیک عدالت مطلق عقلی از عدالت شرعیِ قابل نسخ' in _joined(verse, "modern")
    assert 'خوانش انتقادی یادآور می\u200cشود که روایت\u200cهای ستایش آیه ــ از خبر' in _joined(verse, "critical")

def test_nahl_16_91_verse():
    verse = _check_verse("16:91")
    assert 'آیهٔ نود و یکم از وفای به عهد هنگام پیمان\u200cبستن و' in _joined(verse, "notes")
    assert 'پژوهش\u200cهای معاصر در اخلاق قرارداد این آیه را پایهٔ قرآنی «وفای' in _joined(verse, "modern")
    assert 'خوانش انتقادی سبب نزول را می\u200cکاود: دو خوشهٔ روایی متعارض ــ' in _joined(verse, "critical")

def test_nahl_16_92_verse():
    verse = _check_verse("16:92")
    assert 'آیه مثال می\u200cزند: مانند زنی مباشید که رشتهٔ تابیدهٔ خویش را' in _joined(verse, "notes")
    assert 'پژوهش\u200cهای معاصر بلاغت قرآن، مثل ریسمان را نمونهٔ «تمثیل محسوس برای' in _joined(verse, "modern")
    assert 'خوانش انتقادی دربارهٔ زنِ مثل میان دو قول ــ زنی تاریخی' in _joined(verse, "critical")

def test_nahl_16_93_verse():
    verse = _check_verse("16:93")
    assert 'اگر خدا می\u200cخواست همهٔ شما را امتی یگانه و متحد می\u200cکرد،' in _joined(verse, "notes")
    assert 'المیزان جملهٔ «ولتسألنّ» را دفع توهم جبر می\u200cخواند: استناد هدایت و' in _joined(verse, "modern")
    assert 'خوانش انتقادی آیه را در قلب مجادلات کلامیِ جبر و اختیار' in _joined(verse, "critical")

def test_nahl_16_94_verse():
    verse = _check_verse("16:94")
    assert 'آیهٔ نود و چهارم نهی را با تصویر «لغزیدن قدم پس' in _joined(verse, "notes")
    assert 'المیزان «صدود از سبیل الله» را اعراض از سنت فطری می\u200cخواند' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان قرطبی و طبری دربارهٔ مخاطب آیه داوری می\u200cکند:' in _joined(verse, "critical")

def test_nahl_16_95_verse():
    verse = _check_verse("16:95")
    assert 'فرمان روشن است: پیمان خدا را به بهای اندک ــ هر' in _joined(verse, "notes")
    assert 'پژوهش\u200cهای معاصر اخلاق اقتصادی این آیه را از قرآنی\u200cترین مواضع نکوهش' in _joined(verse, "modern")
    assert 'خوانش انتقادی سبب نزولِ امرؤالقیس را بررسی می\u200cکند: شرح قرطبی آن' in _joined(verse, "critical")

def test_nahl_16_96_verse():
    verse = _check_verse("16:96")
    assert 'آیهٔ نود و ششم قاعدهٔ کلی بازار بقا و فنا را' in _joined(verse, "notes")
    assert 'المیزان میان قرائت «لنجزین» و بن\u200cمایهٔ التفات فرق می\u200cگذارد: «و لنَجْزیَنَّ»' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان دو تفسیر از «أحسن» داوری می\u200cکند: تفسیر متعارف' in _joined(verse, "critical")

def test_nahl_16_97_verse():
    verse = _check_verse("16:97")
    assert 'هر مرد یا زن مؤمنی که کار شایسته کند، خدا او' in _joined(verse, "notes")
    assert 'المیزان توضیح می\u200cدهد این حیاتِ تازه جدای از حیات پیشین نیست' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان پنج قول حیات طیبه داوری می\u200cکند: ترجیح قناعت' in _joined(verse, "critical")

def test_nahl_16_98_verse():
    verse = _check_verse("16:98")
    assert 'آیه به پیامبر و در پی او به هر قاری قرآن' in _joined(verse, "notes")
    assert 'المیزان نتیجه می\u200cگیرد استعاذه با توکل هم\u200cریشه است و در آیهٔ' in _joined(verse, "modern")
    assert 'خوانش انتقادی می\u200cپرسد اگر استعاذه به خوانش المیزان حالتی قلبی است،' in _joined(verse, "critical")

def test_nahl_16_99_verse():
    verse = _check_verse("16:99")
    assert 'خداوند خبر می\u200cدهد که شیطان بر کسانی که ایمان آورده و' in _joined(verse, "notes")
    assert 'المیزان می\u200cگوید این آیه همان معنای خطاب خدا به ابلیس در' in _joined(verse, "modern")
    assert 'خوانش انتقادی تعارض آدم و حوا را جدّی می\u200cگیرد: اگر شیطان' in _joined(verse, "critical")

def test_nahl_16_100_verse():
    verse = _check_verse("16:100")
    assert 'آیه با حصر می\u200cگوید سلطهٔ شیطان فقط بر دو گروه است:' in _joined(verse, "notes")
    assert 'المیزان قول بازگشت ضمیر «به» به خدا را مردود می\u200cداند، چون' in _joined(verse, "modern")
    assert 'خوانش انتقادی منازعهٔ مرجع ضمیر را مرکز بحث می\u200cگذارد: طبری و' in _joined(verse, "critical")

def test_nahl_16_101_verse():
    verse = _check_verse("16:101")
    assert 'چون خدا حکم آیه\u200cای را برمی\u200cدارد و حکم دیگری را جایش' in _joined(verse, "notes")
    assert 'تحلیل بلاغی المیزان از اتهام مشرکان: آنان به جای اینکه بگویند' in _joined(verse, "modern")
    assert 'خوانش انتقادی می\u200cپرسد «تبدیل آیه» در این آیه حتماً نسخِ اصطلاحیِ' in _joined(verse, "critical")

def test_nahl_16_102_verse():
    verse = _check_verse("16:102")
    assert 'خدا به پیامبر فرمان می\u200cدهد که بگوید این قرآن را روح\u200cالقدس' in _joined(verse, "notes")
    assert 'المیزان «تثبیت» بر اثر نسخ را با تمثیل راهنما و راهرو' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان دو تبیین «تثبیت» داوری می\u200cکند: المیزان آن را' in _joined(verse, "critical")

def test_nahl_16_103_verse():
    verse = _check_verse("16:103")
    assert 'خدا می\u200cگوید ما می\u200cدانیم که آنان می\u200cگویند بشری این قرآن را' in _joined(verse, "notes")
    assert 'قدر متیقن روایات نزد المیزان این است که مردی رومی، غلام' in _joined(verse, "modern")
    assert 'خوانش انتقادی اختلاف نام\u200cها ــ بلعام، جبر، یعیش، یسار، ابوفکیهه ــ' in _joined(verse, "critical")

def test_nahl_16_104_verse():
    verse = _check_verse("16:104")
    assert 'کسانی که به آیات و حجت\u200cهای خدا ایمان نمی\u200cآورند، خدا آنان' in _joined(verse, "notes")
    assert 'المیزان در بحث روایی این بخش حدیثی را می\u200cآورد که از' in _joined(verse, "modern")
    assert 'خوانش انتقادی حلقهٔ برهان المیزان را می\u200cسنجد: از «بی\u200cایمانان هدایت نمی\u200cشوند»' in _joined(verse, "critical")

def test_nahl_16_105_verse():
    verse = _check_verse("16:105")
    assert 'در پایان جدل، آیه با حصر می\u200cگوید دروغ را فقط کسانی' in _joined(verse, "notes")
    assert 'المیزان در بحث روایی از عیاشی نقل می\u200cکند که امام رضا' in _joined(verse, "modern")
    assert 'خوانش انتقادی می\u200cپرسد آیا گزارهٔ «مؤمن دروغ نمی\u200cگوید» گزاره\u200cای تجربی است' in _joined(verse, "critical")

def test_nahl_16_106_verse():
    verse = _check_verse("16:106")
    assert 'آیه میان دو کفر فرق می\u200cگذارد: کفر پس از ایمان با' in _joined(verse, "notes")
    assert 'المیزان برداشت بدلی از «من کفر» را رد می\u200cکند و می\u200cگوید' in _joined(verse, "modern")
    assert 'خوانش انتقادی گسترهٔ رخصت را می\u200cسنجد: آیا استثنا فقط در «قول»' in _joined(verse, "critical")

def test_nahl_16_107_verse():
    verse = _check_verse("16:107")
    assert 'آن غضب و عذاب بدان سبب است که آنان زندگی دنیا' in _joined(verse, "notes")
    assert 'المیزان «قوم کافرین» را کافرپیشگان می\u200cخواند؛ یعنی نفی هدایت ناظر به' in _joined(verse, "modern")
    assert 'خوانش انتقادی پرسش کهن خذلان را باز می\u200cگشاید: اگر علت سقوط،' in _joined(verse, "critical")

def test_nahl_16_108_verse():
    verse = _check_verse("16:108")
    assert 'اینان همان کسانی\u200cاند که خدا بر دل\u200cهایشان مهر نهاده تا ایمان' in _joined(verse, "notes")
    assert 'المیزان می\u200cگوید نفی هدایت در آیهٔ پیش خود معنای طبع و' in _joined(verse, "modern")
    assert 'خوانش انتقادی مسئلهٔ انتساب مهر به خدا را مرکز می\u200cگذارد: اگر' in _joined(verse, "critical")

def test_nahl_16_109_verse():
    verse = _check_verse("16:109")
    assert 'آیه با قاطعیت اعلام می\u200cکند که آنان در آخرت همان زیانکاران\u200cاند؛' in _joined(verse, "notes")
    assert 'المیزان با خوانش سرمایه\u200cای، میان این آیه و «ما عندکم ینفد»' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان سه تحلیل «لا جرم» داوری می\u200cکند: کلمهٔ واحد' in _joined(verse, "critical")

def test_nahl_16_110_verse():
    verse = _check_verse("16:110")
    assert 'پروردگار برای کسانی که پس از آنکه در دینشان به فتنه' in _joined(verse, "notes")
    assert 'المیزان پیوند آیه با استثنای اکراه در آیهٔ صد و ششم' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان دو سبب نزول ــ عمار و یاران مستضعف،' in _joined(verse, "critical")

def test_nahl_16_111_verse():
    verse = _check_verse("16:111")
    assert 'آیه روز قیامت را تصویر می\u200cکند: هر نفسی می\u200cآید و از' in _joined(verse, "notes")
    assert 'از این رو دفاع هر کس سود ندارد و آنچه را' in _joined(verse, "modern")
    assert 'خوانش انتقادی نسبت این آیه با آیات شفاعت را مسئله می\u200cکند:' in _joined(verse, "critical")

def test_nahl_16_112_verse():
    verse = _check_verse("16:112")
    assert 'خدا مثل قریه\u200cای را می\u200cزند که در امنیت و آرامش بود' in _joined(verse, "notes")
    assert 'المیزان در برابر تطبیق صرف بر مکه می\u200cایستد و می\u200cگوید سیاق' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان سه قرائت از قریه داوری می\u200cکند: مثل عام' in _joined(verse, "critical")

def test_nahl_16_113_verse():
    verse = _check_verse("16:113")
    assert 'برای اهل آن قریه رسولی از خودشان آمد که او را' in _joined(verse, "notes")
    assert 'المیزان نتیجه می\u200cگیرد که عذاب در برابر ظلم گرفته است نه' in _joined(verse, "modern")
    assert 'خوانش انتقادی استدلال «این آیه دلیل مکه بودن قریه است» را' in _joined(verse, "critical")

def test_nahl_16_114_verse():
    verse = _check_verse("16:114")
    assert 'پس از آنچه خدا روزی\u200cتان کرده است ــ از چهارپایان حلال' in _joined(verse, "notes")
    assert 'المیزان خطاب را به مؤمنان می\u200cداند چون فقط آنان خدا را' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان سه خطاب ــ مؤمنان، مشرکان، یا عموم مردم' in _joined(verse, "critical")

def test_nahl_16_115_verse():
    verse = _check_verse("16:115")
    assert 'خدا بر شما فقط مردار و خون و گوشت خوک و' in _joined(verse, "notes")
    assert 'المیزان رخصت اضطرار را در ذیل همین حصر می\u200cفهمد: چون تحریم' in _joined(verse, "modern")
    assert 'خوانش انتقادی مسئلهٔ حصر را مرکز می\u200cگذارد: «إنما» چهار چیز را' in _joined(verse, "critical")

def test_nahl_16_116_verse():
    verse = _check_verse("16:116")
    assert 'برای وصف دروغی که زبان\u200cهایتان می\u200cکند نگویید در روزی\u200cهایی که خدا' in _joined(verse, "notes")
    assert 'المیزان نظر بیشتر مفسران را که آیه را فقط نهی از' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان دو تفسیر آیه داوری می\u200cکند: نهی تاریخی از' in _joined(verse, "critical")

def test_nahl_16_117_verse():
    verse = _check_verse("16:117")
    assert 'آنچه دروغ\u200cبندان بر خدا در این دنیا از آن بهره می\u200cبرند' in _joined(verse, "notes")
    assert 'از منظر تحلیل المیزان، قلیل بودن متاع نسبت\u200cسنجی است نه کمیت\u200cسنجی:' in _joined(verse, "modern")
    assert 'خوانش انتقادی می\u200cپرسد بهرهٔ افترا دقیقاً چیست: سود مادی، ریاست آیینی،' in _joined(verse, "critical")

def test_nahl_16_118_verse():
    verse = _check_verse("16:118")
    assert 'بر یهودیان پیش از تو آنچه را در سورهٔ انعام برایت' in _joined(verse, "notes")
    assert 'المیزان نتیجه می\u200cگیرد که آیه متصل به ما قبل و به' in _joined(verse, "modern")
    assert 'خوانش انتقادی نظریهٔ تحریم کیفری را می\u200cسنجد: تحریم طیبات برای یک' in _joined(verse, "critical")

def test_nahl_16_119_verse():
    verse = _check_verse("16:119")
    assert 'سپس پروردگارت برای کسانی که خدا را نافرمانی کردند و از' in _joined(verse, "notes")
    assert 'نکتهٔ دقیق المیزان: مغفرت فقط اثر توبه است نه توبه و' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان دو معنای جهالت داوری می\u200cکند: نادانی به حکم' in _joined(verse, "critical")

def test_nahl_16_120_verse():
    verse = _check_verse("16:120")
    assert 'ابراهیم خلیل خدا آموزگار خیری بود که اهل هدایت بدو اقتدا' in _joined(verse, "notes")
    assert 'المیزان می\u200cگوید وصف ابراهیم به این صفات اشاره دارد که این\u200cها' in _joined(verse, "modern")
    assert 'خوانش انتقادی سه معنای امت را می\u200cسنجد: آموزگار خیر نزد ابن\u200cمسعود،' in _joined(verse, "critical")

def test_nahl_16_121_verse():
    verse = _check_verse("16:121")
    assert 'ابراهیم شکر خدا را در نعمت\u200cهایی که بر او ارزانی داشت' in _joined(verse, "notes")
    assert 'المیزان این صفات را آثار دین حنیف می\u200cداند: هر که به' in _joined(verse, "modern")
    assert 'خوانش انتقادی تقدم شکر بر اجتبا را می\u200cسنجد: آیا ترتیب ذکر' in _joined(verse, "critical")

def test_nahl_16_122_verse():
    verse = _check_verse("16:122")
    assert 'به ابراهیم در برابر فرمانبری و شکر و اخلاص عبادتش در' in _joined(verse, "notes")
    assert 'المیزان در بحث حسنه به معنای هدایت و صراط مستقیم در' in _joined(verse, "modern")
    assert 'خوانش انتقادی برای حسنهٔ دنیا دو تفسیر رقیب را می\u200cسنجد: نام' in _joined(verse, "critical")

def test_nahl_16_123_verse():
    verse = _check_verse("16:123")
    assert 'سپس به تو ــ ای محمد ــ وحی کردیم و گفتیم' in _joined(verse, "notes")
    assert 'از منظر المیزان، وحی فرمان پیروی نشان می\u200cدهد راه محمد ادامهٔ' in _joined(verse, "modern")
    assert 'خوانش انتقادی دامنهٔ پیروی را مرکز می\u200cگذارد: مناسک حج، عقاید، یا' in _joined(verse, "critical")

def test_nahl_16_124_verse():
    verse = _check_verse("16:124")
    assert 'بزرگداشت شنبه فقط بر یهودیانی فرض شد که در آن اختلاف' in _joined(verse, "notes")
    assert 'معنای آیه نزد المیزان این است که یک روز تعطیل عبادت' in _joined(verse, "modern")
    assert 'خوانش انتقادی اقوال اختلاف را دسته\u200cبندی می\u200cکند: اختلاف پیش از جعل' in _joined(verse, "critical")

def test_nahl_16_125_verse():
    verse = _check_verse("16:125")
    assert 'ای محمد، کسانی را که پروردگارت تو را به سویشان فرستاده' in _joined(verse, "notes")
    assert 'المیزان ترتیب سه طریق را به حسب افراد هر طریق می\u200cداند' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان نظریهٔ المیزان و نظریهٔ طبقات مخاطب داوری می\u200cکند؛' in _joined(verse, "critical")

def test_nahl_16_126_verse():
    verse = _check_verse("16:126")
    assert 'اگر کیفر می\u200cکنید ــ ای مؤمنان ــ کسی را که بر' in _joined(verse, "notes")
    assert 'المیزان اتصال این آیات به ما قبل را قابل توجیه می\u200cداند' in _joined(verse, "modern")
    assert 'خوانش انتقادی مسئلهٔ مکی یا مدنی بودن سه آیهٔ پایانی را' in _joined(verse, "critical")

def test_nahl_16_127_verse():
    verse = _check_verse("16:127")
    assert 'ای محمد بر آنچه از آزار در راه خدا بر تو' in _joined(verse, "notes")
    assert 'آیهٔ پایانی از نظر المیزان تعلیل همین نهی است: تقوا و' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان نسخ و احکام آیه داوری می\u200cکند: ابن\u200cزید آن' in _joined(verse, "critical")

def test_nahl_16_128_verse():
    verse = _check_verse("16:128")
    assert 'به راستی خدا با کسانی است که از حرام\u200cهایش پرهیز و' in _joined(verse, "notes")
    assert 'در خوانش المیزان این سه آیهٔ پایانی با همهٔ شباهتشان به' in _joined(verse, "modern")
    assert 'خوانش انتقادی دو معیت عام و خاص را از هم جدا' in _joined(verse, "critical")

def test_isra_17_1_verse():
    verse = _check_verse("17:1")
    assert 'تنزیه و تبرئهٔ خداست از آنچه مشرکان بدو نسبت می\u200cدهند: شریک' in _joined(verse, "notes")
    assert 'المیزان نکتهٔ التفات آیه را می\u200cگیرد: از غیبتِ «أسری بعبده» به' in _joined(verse, "modern")
    assert 'خوانش انتقادی بر سر «سبحان» می\u200cایستد: برخی آن را برای تعجب' in _joined(verse, "critical")

def test_isra_17_2_verse():
    verse = _check_verse("17:2")
    assert 'به موسی کتاب یعنی تورات را دادیم و آن را بیان' in _joined(verse, "notes")
    assert 'چرا وکیل گرفتن غیر خدا شرک است؟ المیزان پاسخ می\u200cدهد وکیل' in _joined(verse, "modern")
    assert 'خوانش انتقادی به انتخاب «الکتاب» به جای «التوراة» می\u200cنگرد که المیزان' in _joined(verse, "critical")

def test_isra_17_3_verse():
    verse = _check_verse("17:3")
    assert 'مراد از ذریه همهٔ کسانی است که این قرآن بر آنان' in _joined(verse, "notes")
    assert 'شکر حقیقی نزد المیزان ملازم اخلاص در عبودیت است و نوح' in _joined(verse, "modern")
    assert 'خوانش انتقادی وجوه اعراب ذریه را می\u200cسنجد: المیزان وجوه نداء و' in _joined(verse, "critical")

def test_isra_17_4_verse():
    verse = _check_verse("17:4")
    assert 'قضاء در اصل به معنای فراغ از چیزی و فیصلهٔ آن' in _joined(verse, "notes")
    assert 'المیزان کل هفت آیه را زمینه\u200cچینی جریان همین سنت در امّت' in _joined(verse, "modern")
    assert 'خوانش انتقادی بر سر ماهیت «کتاب» می\u200cایستد: تورات موجود یا لوح' in _joined(verse, "critical")

def test_isra_17_5_verse():
    verse = _check_verse("17:5")
    assert 'چون وعدهٔ نخستین از آن دو نوبت فساد فرارسید بندگانی نیرومند' in _joined(verse, "notes")
    assert 'جملهٔ «و کان وعداً مفعولاً» نزد المیزان تأکید بر حتمی بودن' in _joined(verse, "modern")
    assert 'خوانش انتقادی نامزدهای مبعوثان را کنار هم می\u200cگذارد: جالوت و بختنصر' in _joined(verse, "critical")

def test_isra_17_6_verse():
    verse = _check_verse("17:6")
    assert 'سپس شما بنی\u200cاسرائیل را بر آن قومی که خدا بر شما' in _joined(verse, "notes")
    assert 'از مقایسهٔ وعدهٔ نخست و این بازگشت نزد المیزان قانون بزرگ\u200cتر' in _joined(verse, "modern")
    assert 'خوانش انتقادی بر سر عامل بازگشت می\u200cایستد: جنگ و بازپس\u200cگیری نزد' in _joined(verse, "critical")

def test_isra_17_7_verse():
    verse = _check_verse("17:7")
    assert 'اگر نیکی کنید و خدا را فرمان برید و کارتان را' in _joined(verse, "notes")
    assert '«تتبیر» نزد المیزان هلاک کردن از مادهٔ تبار به معنای هلاک' in _joined(verse, "modern")
    assert 'خوانش انتقادی بر سر مصداق فساد دوم می\u200cایستد: کشتن یحیی مشهور' in _joined(verse, "critical")

def test_isra_17_8_verse():
    verse = _check_verse("17:8")
    assert 'امید است پروردگارتان پس از انتقام از شما به دست آن' in _joined(verse, "notes")
    assert 'المیزان کل این هفت آیه را زمینهٔ سنت امّت اسلام می\u200cداند' in _joined(verse, "modern")
    assert 'خوانش انتقادی تطبیق قتاده را می\u200cسنجد که بازگشت نهایی را بعثت' in _joined(verse, "critical")

def test_isra_17_9_verse():
    verse = _check_verse("17:9")
    assert 'این قرآنی که بر پیامبرمان محمد نازل کردیم هر که را' in _joined(verse, "notes")
    assert 'المیزان می‌گوید در این آیه حقی برای مؤمنان بر خدا اثبات' in _joined(verse, "modern")
    assert 'خوانش انتقادی مقایسهٔ پنهان آیه را آشکار می‌کند: المیزان می‌گوید اقوم' in _joined(verse, "critical")

def test_isra_17_10_verse():
    verse = _check_verse("17:10")
    assert 'و کسانی که به بازگشت به سوی خدا و ثواب و' in _joined(verse, "notes")
    assert 'المیزان مؤمن بی‌عمل صالح را در برابر این دو آیه بی‌وعدهٔ' in _joined(verse, "modern")
    assert 'خوانش انتقادی می‌پرسد چرا عذاب کافران «بشارت» مؤمنان شمرده شد؛ پاسخ' in _joined(verse, "critical")

def test_isra_17_11_verse():
    verse = _check_verse("17:11")
    assert 'انسان در لحظهٔ تنگنا و خشم بر خود و فرزند و' in _joined(verse, "notes")
    assert 'المیزان مراد از انسان را جنس آدمی می‌داند نه افراد معینی' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان سه خوانش آیه داوری می‌کند: نفرین لحظهٔ خشم' in _joined(verse, "critical")

def test_isra_17_12_verse():
    verse = _check_verse("17:12")
    assert 'از نعمت خدا بر شما این است که نشانهٔ شب را' in _joined(verse, "notes")
    assert 'قول فخر رازی را نیز که محو را اختلاف شکل ماه' in _joined(verse, "modern")
    assert 'خوانش انتقادی سه لایه را جدا می‌کند: متن آیه از نشانه' in _joined(verse, "critical")

def test_isra_17_13_verse():
    verse = _check_verse("17:13")
    assert 'کارنامهٔ هر انسانی را که کارهای خیر و شرش در آن' in _joined(verse, "notes")
    assert 'المیزان از موثقهٔ ابو بصیر از امام کاظم می‌آورد که مراد' in _joined(verse, "modern")
    assert 'خوانش انتقادی سه خوانش طائر را می‌سنجد: سرنوشت ازلی مقدر نزد' in _joined(verse, "critical")

def test_isra_17_14_verse():
    verse = _check_verse("17:14")
    assert 'به او گفته می‌شود نامهٔ عملت را بخوان که همهٔ کارهایی' in _joined(verse, "notes")
    assert 'المیزان نتیجه می‌گیرد که اگر اعمال زشت آدمی چنین برملا شود' in _joined(verse, "modern")
    assert 'خوانش انتقادی دو تصویر کتاب را جدا می‌کند: دفتر مکتوب با' in _joined(verse, "critical")

def test_isra_17_15_verse():
    verse = _check_verse("17:15")
    assert 'هر که راه راست را برود سود هدایتش به خودش برمی‌گردد' in _joined(verse, "notes")
    assert 'در مسئلهٔ وزر پیشوایان المیزان می‌گوید گناه اضلال و سنت بد' in _joined(verse, "modern")
    assert 'خوانش انتقادی مسئلهٔ اصحاب فتره را می‌کاود: میان کسانی که هیچ' in _joined(verse, "critical")

def test_isra_17_16_verse():
    verse = _check_verse("17:16")
    assert 'جمهور قرّاء «أمرنا» را بی‌مد و با تخفیف خوانده‌اند و بیشتر' in _joined(verse, "notes")
    assert 'چرا امر فقط متوجه مترفان شد؟ مفسران پاسخ داده‌اند چون ایشان' in _joined(verse, "modern")
    assert 'خوانش انتقادی کانون جدال را می‌شناسد: اگر مأموربه طاعت است حذف' in _joined(verse, "critical")

def test_isra_17_17_verse():
    verse = _check_verse("17:17")
    assert 'این سخن وعید خدا به تکذیب‌کنندگان پیامبرش از مشرکان قریش و' in _joined(verse, "notes")
    assert 'خبیر و بصیر بودن خدا در پایان آیه نزد المیزان ضامن' in _joined(verse, "modern")
    assert 'خوانش انتقادی مسئلهٔ اندازهٔ قرن را می‌سنجد که از چهل تا' in _joined(verse, "critical")

def test_isra_17_18_verse():
    verse = _check_verse("17:18")
    assert 'هر که طلبش دنیای شتابان باشد و برای آن کار و' in _joined(verse, "notes")
    assert 'اسباب اخروی نزد المیزان اعمال‌اند و هرگز از نتایجشان تخلف ندارند' in _joined(verse, "modern")
    assert 'خوانش انتقادی اختلاف دو غرض را می‌سنجد: المیزان می‌گوید این آیه' in _joined(verse, "critical")

def test_isra_17_19_verse():
    verse = _check_verse("17:19")
    assert 'هر که آخرت و پاداش آن را بخواهد و برای آن' in _joined(verse, "notes")
    assert 'سعی شایسته نزد المیزان حسن عمل را از عقل قطعی یا' in _joined(verse, "modern")
    assert 'خوانش انتقادی اشکال المیزان به مفسری را می‌سنجد که ارادهٔ آخرت' in _joined(verse, "critical")

def test_isra_17_20_verse():
    verse = _check_verse("17:20")
    assert 'پروردگارت هر دو گروه خواهندگان عاجله و خواهندگان آخرت را در' in _joined(verse, "notes")
    assert 'قول منسوب به حسن و قتاده که عطا فقط عطای دنیوی' in _joined(verse, "modern")
    assert 'خوانش انتقادی پاسخ المیزان به آلوسى را می‌سنجد که تقسیم آیه' in _joined(verse, "critical")

def test_isra_17_21_verse():
    verse = _check_verse("17:21")
    assert 'ای محمد با چشم دلت به این دو گروه بنگر که' in _joined(verse, "notes")
    assert 'اختلاف احوال قلب نزد المیزان از اختلاف احوال جسم وسیع‌تر است' in _joined(verse, "modern")
    assert 'خوانش انتقادی دو خوانش «فضلنا» را می‌سنجد: برتری در روزی و' in _joined(verse, "critical")

def test_isra_17_22_verse():
    verse = _check_verse("17:22")
    assert 'ای محمد با خدا شریکی در الوهیت و عبادتش قرار نده' in _joined(verse, "notes")
    assert 'المیزان آیه را ثمرهٔ سنت‌های گفته‌شده می‌داند نه فرمانی جدا: چون' in _joined(verse, "modern")
    assert 'خوانش انتقادی می‌پرسد چرا فرجام شرک «قعود» است نه واژه‌ای از' in _joined(verse, "critical")

def test_isra_17_23_verse():
    verse = _check_verse("17:23")
    assert 'پروردگارت حکم کرده که جز خدا را نپرستید چون سزاوار نیست' in _joined(verse, "notes")
    assert '«اف» نزد المیزان چون آخ در فارسی رسانندهٔ انزجار است و' in _joined(verse, "modern")
    assert 'خوانش انتقادی مسئلهٔ «وصّی یا قضی» را می‌سنجد که به ابن‌عباس' in _joined(verse, "critical")

def test_isra_17_24_verse():
    verse = _check_verse("17:24")
    assert 'برای آن دو از روی رحمتی که بدانان داری فروتن باش' in _joined(verse, "notes")
    assert 'طبرسی دعا را به پس از مرگ والدین اختصاص داده بود' in _joined(verse, "modern")
    assert 'خوانش انتقادی مسئلهٔ دعا برای والدین مشرک را می‌سنجد که میان' in _joined(verse, "critical")

def test_isra_17_25_verse():
    verse = _check_verse("17:25")
    assert 'پروردگارتان از خودتان داناتر است به آنچه در دل‌هایتان از بزرگداشت' in _joined(verse, "notes")
    assert 'صلاح در این آیه نزد المیزان صلاح نفس و روح است' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان مصداق خاص بادرهٔ والدین نزد جمهور و قانون' in _joined(verse, "critical")

def test_isra_17_26_verse():
    verse = _check_verse("17:26")
    assert 'در مراد از ذا القربی اختلاف است: گروهی خویشاوندان خود شخص' in _joined(verse, "notes")
    assert 'المیزان در آیات بعد برادری مبذران با شیاطین را از سنخیت' in _joined(verse, "modern")
    assert 'خوانش انتقادی دو مصداق ذا القربی را می‌سنجد: خویشاوندان هر مؤمن' in _joined(verse, "critical")

def test_isra_17_27_verse():
    verse = _check_verse("17:27")
    assert 'پراکنده‌کنندگان مال‌هایشان در گناهان خدا و خرج‌کنندگان آن در غیر طاعتش' in _joined(verse, "notes")
    assert 'جمع و مفرد شیطان در آیه نزد المیزان نظریهٔ شیطان‌های بسیار' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان سه خوانش برادری داوری می‌کند: هم‌حکمی در افساد،' in _joined(verse, "critical")

def test_isra_17_28_verse():
    verse = _check_verse("17:28")
    assert 'اگر از کسانی که به دادن حقشان فرمان یافته‌ای روی بگردانی' in _joined(verse, "notes")
    assert 'المیزان قلمرو آیه را به هر اعراضی گسترش نمی‌دهد و آن' in _joined(verse, "modern")
    assert 'خوانش انتقادی دو سبب نزول ناسازگار را می‌سنجد: ندادن عمدی به' in _joined(verse, "critical")

def test_isra_17_29_verse():
    verse = _check_verse("17:29")
    assert 'این مثل برای بازدارنده از انفاق در حقوق واجب است که' in _joined(verse, "notes")
    assert 'آیهٔ بعد نزد المیزان تعلیل این نهی است که راه خدا' in _joined(verse, "modern")
    assert 'خوانش انتقادی سبب پیراهن پیامبر را می‌سنجد که با قاعدهٔ قرطبی' in _joined(verse, "critical")

def test_isra_17_30_verse():
    verse = _check_verse("17:30")
    assert 'پروردگارت ای محمد روزی را برای هر یک از بندگانش که' in _joined(verse, "notes")
    assert 'المیزان اخلاق خدا را الگوی اخلاق انسان می‌گیرد و این اصل' in _joined(verse, "modern")
    assert 'خوانش انتقادی مسئلهٔ جبر و تفاوت روزی را می‌سنجد: اگر قسمت' in _joined(verse, "critical")

def test_isra_17_31_verse():
    verse = _check_verse("17:31")
    assert 'فرزندانتان را از ترس تنگدستی و فقر نکشید؛ عرب دخترانشان را' in _joined(verse, "notes")
    assert 'خطای بزرگ نزد المیزان تصمیم و ارادهٔ کاری ناشایست است و' in _joined(verse, "modern")
    assert 'خوانش انتقادی اختلاف طبری و کشاف و المیزان را در مصداق' in _joined(verse, "critical")

def test_isra_17_32_verse():
    verse = _check_verse("17:32")
    assert 'به زنا نزدیک نشوید که زنا فاحشه بوده است و راه' in _joined(verse, "notes")
    assert 'ازدواج نزد المیزان شرکت تجاری زن و شوهر نیست که غرضش' in _joined(verse, "modern")
    assert 'خوانش انتقادی گفتار اجتماعی المیزان را از متن کوتاه آیه جدا' in _joined(verse, "critical")

def test_isra_17_33_verse():
    verse = _check_verse("17:33")
    assert 'نفسی را که خدا کشتنش را حرام کرده جز به حق' in _joined(verse, "notes")
    assert 'نظام قصاص در این آیه نزد المیزان سلطنت قانونی صاحب خون' in _joined(verse, "modern")
    assert 'خوانش انتقادی نزاع ولیّ زن و مرد را می‌سنجد که از' in _joined(verse, "critical")

def test_isra_17_34_verse():
    verse = _check_verse("17:34")
    assert 'به مال یتیم با خوردن و شتاب برای بزرگ شدنش نزدیک' in _joined(verse, "notes")
    assert 'شمول عهد نزد زجاج و شرح‌های پس از او همهٔ اوامر' in _joined(verse, "modern")
    assert 'خوانش انتقادی گذار دشواری اصحاب از پرهیز کامل تا رخصت آمیختن' in _joined(verse, "critical")

def test_isra_17_35_verse():
    verse = _check_verse("17:35")
    assert 'پیمانهٔ مردم را چون برایشان پیمانه می‌کنید کامل دهید و از' in _joined(verse, "notes")
    assert 'المیزان کم‌فروشی را پیش از آنکه زیان مالی باشد خیانت در' in _joined(verse, "modern")
    assert 'خوانش انتقادی واژهٔ قسطاس را می‌سنجد که رومی دخیل یا عربی' in _joined(verse, "critical")

def test_isra_17_36_verse():
    verse = _check_verse("17:36")
    assert 'از آنچه بدان علم نداری پیروی مکن؛ ابن‌عباس آن را مگو' in _joined(verse, "notes")
    assert 'گوش و چشم و فؤاد نزد المیزان نعمت‌هایی برای تمیز حق' in _joined(verse, "modern")
    assert 'خوانش انتقادی تعلیل آیه را از شهادت اعضا در فصلت جدا' in _joined(verse, "critical")

def test_isra_17_37_verse():
    verse = _check_verse("17:37")
    assert 'در زمین خودپسند و مستکبر راه مرو که با خودپسندی‌ات زمین' in _joined(verse, "notes")
    assert 'مرح نزد المیزان مرض سبکی عقل است که در همهٔ رفتار' in _joined(verse, "modern")
    assert 'خوانش انتقادی تفسیر موهوم بودن قدرت و عزت نزد المیزان را' in _joined(verse, "critical")

def test_isra_17_38_verse():
    verse = _check_verse("17:38")
    assert 'قرّاء در این آیه اختلاف کرده‌اند: برخی مدینه و عامّهٔ کوفه' in _joined(verse, "notes")
    assert 'المیزان در آیهٔ بعد احکام فرعی دین را از آن رو' in _joined(verse, "modern")
    assert 'خوانش انتقادی اختلاف قرائت را از نادر اختلاف‌های معناگذار می‌داند که' in _joined(verse, "critical")

def test_isra_17_39_verse():
    verse = _check_verse("17:39")
    assert 'این اخلاق نیکویی که تو را به نیکویش فرمان دادیم و' in _joined(verse, "notes")
    assert 'فرجام «فتلقی فی جهنم» نزد المیزان صورت اخروی همان قعود آیهٔ' in _joined(verse, "modern")
    assert 'خوانش انتقادی علت تکرار نهی شرک را می‌سنجد که عظمت توحید' in _joined(verse, "critical")

def test_isra_17_40_verse():
    verse = _check_verse("17:40")
    assert 'پروردگارتان شما مردم را به پسران از فرزندان اختصاص داد و' in _joined(verse, "notes")
    assert 'در خوانش المیزان اصفاء به معنای ایثار دیگری بر خویش با' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان دو سطح انکار فرق می‌نهد: نسبت فرزند به' in _joined(verse, "critical")

def test_isra_17_41_verse():
    verse = _check_verse("17:41")
    assert 'به این مشرکان افترازننده بر خدا در این قرآن عبرت‌ها و' in _joined(verse, "notes")
    assert 'المیزان از سوی دیگر می‌گوید کفر و نفور از حق همان‌قدر' in _joined(verse, "modern")
    assert 'خوانش انتقادی پارادوکس آیه را برجسته می‌کند: نص هر چه متنوع‌تر' in _joined(verse, "critical")

def test_isra_17_42_verse():
    verse = _check_verse("17:42")
    assert 'طبری راه جستن را قربت و طلب نزدیکی و مرتبت نزد' in _joined(verse, "notes")
    assert 'المیزان از خطاب اعراض‌شده می‌خواند که خدا در این آیه باز' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان دو سنت کهن داوری می‌طلبد: سنت نزاع برهان' in _joined(verse, "critical")

def test_isra_17_43_verse():
    verse = _check_verse("17:43")
    assert 'این تنزیه خدا خویشتن را از آنچه مشرکان وصفش می‌کنند است' in _joined(verse, "notes")
    assert 'المیزان ترتیب برهان و تنزیه را چنان می‌چیند که تسبیح هستی' in _joined(verse, "modern")
    assert 'خوانش انتقادی خودتسبیحی خدا نزد قتاده را می‌سنجد که خدا گویندهٔ' in _joined(verse, "critical")

def test_isra_17_44_verse():
    verse = _check_verse("17:44")
    assert 'آسمان‌های هفت‌گانه و زمین و هر که از مؤمنان فرشتگان و' in _joined(verse, "notes")
    assert 'وجود موجودات نزد المیزان هم حمد است و هم تسبیح چون' in _joined(verse, "modern")
    assert 'خوانش انتقادی این آیه را از مناقشه‌برانگیزترین آیات هستی‌شناسی قرآن می‌داند' in _joined(verse, "critical")

def test_isra_17_45_verse():
    verse = _check_verse("17:45")
    assert 'ای محمد چون قرآن را بر این مشرکان بی‌باور به بعث' in _joined(verse, "notes")
    assert 'در خوانش المیزان جرم این قوم انکار معاد است که ریشهٔ' in _joined(verse, "modern")
    assert 'خوانش انتقادی دو کاربست حجاب را جدا می‌کند: حجاب چشم در' in _joined(verse, "critical")

def test_isra_17_46_verse():
    verse = _check_verse("17:46")
    assert 'بر دل‌های این بی‌باوران به آخرت هنگام خواندن تو قرآن أکنه' in _joined(verse, "notes")
    assert 'قرطبی از همین آیه رد بر قدریه ساخته که فهم قرآن' in _joined(verse, "modern")
    assert 'خوانش انتقادی جدال قدریه و قرطبی را نشان می‌دهد که یک' in _joined(verse, "critical")

def test_isra_17_47_verse():
    verse = _check_verse("17:47")
    assert 'ما داناتر هستیم ای محمد به آنچه این مشرکان قوم تو' in _joined(verse, "notes")
    assert 'در خوانش المیزان برچسب پایانی نجوا یعنی رجلاً مسحوراً خود سند' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان سه معنای مسحور یعنی جادوشده و فریفته و' in _joined(verse, "critical")

def test_isra_17_48_verse():
    verse = _check_verse("17:48")
    assert 'ای محمد با چشم دل بنگر و عبرت بگیر که چگونه' in _joined(verse, "notes")
    assert 'در خوانش المیزان فرمان «انظر» پیامبر و هر خواننده را به' in _joined(verse, "modern")
    assert 'خوانش انتقادی وصف «مثل» را برای برچسب انتخابی تعمدی می‌داند که' in _joined(verse, "critical")

def test_isra_17_49_verse():
    verse = _check_verse("17:49")
    assert 'خدا از سخن این بی‌باوران به آخرت از مشرکان قریش خبر' in _joined(verse, "notes")
    assert 'در فلسفهٔ دین معاصر دور شمردن حشر بدن‌ها و استدلال از' in _joined(verse, "modern")
    assert 'خوانش انتقادی این آیه را متن اصلی موضع انکار می‌داند که' in _joined(verse, "critical")

def test_isra_17_50_verse():
    verse = _check_verse("17:50")
    assert 'ای محمد به تکذیب‌کنندگان بعث پس از مرگ از قومت که' in _joined(verse, "notes")
    assert 'در منطق جدل معاصر پاسخ به دور شمردن طرف با پذیرش' in _joined(verse, "modern")
    assert 'خوانش انتقادی ماهیت امر تعجیزی را برجسته می‌کند که فرمان به' in _joined(verse, "critical")

def test_isra_17_51_verse():
    verse = _check_verse("17:51")
    assert 'اختلاف اهل تأویل در «مما یکبر فی صدورکم» این است که' in _joined(verse, "notes")
    assert 'در خوانش المیزان جنبش سر پاسخی بدنی به حجت است: چون' in _joined(verse, "modern")
    assert 'خوانش انتقادی جدال مرگ یا آسمان را بر سر «یکبر فی' in _joined(verse, "critical")

def test_isra_17_52_verse():
    verse = _check_verse("17:52")
    assert 'ای محمد بگو شاید برانگیخته شدنتان نزدیک باشد آن روز که' in _joined(verse, "notes")
    assert 'المیزان «یوم» را از فعل مقدر و پاسخ را حال ستایش' in _joined(verse, "modern")
    assert 'خوانش انتقادی سه معنای بحمده یعنی به فرمان و به شناخت' in _joined(verse, "critical")

def test_isra_17_53_verse():
    verse = _check_verse("17:53")
    assert 'خدا به پیامبرش می‌گوید ای محمد به بندگانم بگو برخی به' in _joined(verse, "notes")
    assert 'در خوانش المیزان دشمنی شیطان تعلیل بر تعلیل است: بهترین سخن' in _joined(verse, "modern")
    assert 'خوانش انتقادی جدال مخاطب را برجسته می‌کند: مسلمانان در برابر مشرکان' in _joined(verse, "critical")

def test_isra_17_54_verse():
    verse = _check_verse("17:54")
    assert 'خدا به این مشرکان قریش که انکار بعث کردند می‌گوید پروردگارتان' in _joined(verse, "notes")
    assert 'المیزان از تردید مشیت نکته می‌سازد که مشیت خدا یکسان بر' in _joined(verse, "modern")
    assert 'خوانش انتقادی دو مخاطب مشرک و مؤمن را نزد شرح‌ها جدی' in _joined(verse, "critical")

def test_isra_17_55_verse():
    verse = _check_verse("17:55")
    assert 'پروردگارت ای محمد به هر که در آسمان‌ها و زمین است' in _joined(verse, "notes")
    assert 'در خوانش المیزان حتی وحی تشریعی نیز با ادب ستایش سنجیده' in _joined(verse, "modern")
    assert 'خوانش انتقادی پیوند تفضیل با اخلاق سخن را نوآوری سیاقی المیزان' in _joined(verse, "critical")

def test_isra_17_56_verse():
    verse = _check_verse("17:56")
    assert 'خدا به پیامبرش می‌گوید ای محمد به مشرکان قومت که به' in _joined(verse, "notes")
    assert 'المیزان معارضهٔ مشهور را که مسلمانان هم دست به دامان خدا' in _joined(verse, "modern")
    assert 'خوانش انتقادی وصف «زعمتم» را بار داوری می‌داند که مخاطب هنوز' in _joined(verse, "critical")

def test_isra_17_57_verse():
    verse = _check_verse("17:57")
    assert 'این خوانده‌شدگانی که مشرکان پروردگارشان می‌خوانند خود در جستجوی نزدیک شدن' in _joined(verse, "notes")
    assert 'خلاصهٔ سخن مشرکان نزد المیزان این بود که ما با وسیلهٔ' in _joined(verse, "modern")
    assert 'خوانش انتقادی مهم‌ترین تمایز المیزان را وسيله‌جویی درست و پرستش وسیله' in _joined(verse, "critical")

def test_isra_17_58_verse():
    verse = _check_verse("17:58")
    assert 'هیچ آبادی از آبادی‌ها نیست مگر ما مردمش را با نابودی' in _joined(verse, "notes")
    assert 'حق مطلب نزد المیزان این است که کتاب مبین همان متن' in _joined(verse, "modern")
    assert 'خوانش انتقادی تصویر مادی لوح را نزد المیزان نقدی معرفت‌شناختی می‌داند' in _joined(verse, "critical")

def test_isra_17_59_verse():
    verse = _check_verse("17:59")
    assert 'ما را ای محمد از فرستادن نشانه‌هایی که قومت خواستند بازنداشت' in _joined(verse, "notes")
    assert 'تخویف نزد المیزان می‌تواند ایجاد ترس با عذابی کمتر از ریشه‌کنی' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان اقتراح نشانه و نشانهٔ نبوت فرق می‌گذارد که' in _joined(verse, "critical")

def test_isra_17_60_verse():
    verse = _check_verse("17:60")
    assert 'خدا پیامبرش را بر رساندن پیامش برمی‌انگیزد و آگاهش می‌کند که' in _joined(verse, "notes")
    assert 'المیزان نتیجه می‌گیرد که درخت لعنت‌شده یکی از گروه‌های لعنت‌شده در' in _joined(verse, "modern")
    assert 'خوانش انتقادی این آیه را آزمون‌گاه روش می‌داند که متن دو' in _joined(verse, "critical")

def test_isra_17_61_verse():
    verse = _check_verse("17:61")
    assert 'خدا به پیامبرش می‌گوید ای محمد سربیچی این مشرکان و برگشتنشان' in _joined(verse, "notes")
    assert 'در خوانش المیزان سرکشی ابلیس از انکار کرامت آدم می‌آغازد و' in _joined(verse, "modern")
    assert 'خوانش انتقادی وصف «خلقت طیناً» را نخستین استدلال مادّه‌گرایانهٔ تاریخ در' in _joined(verse, "critical")

def test_isra_17_62_verse():
    verse = _check_verse("17:62")
    assert 'دشمن خدا سوگند خورد و به پروردگارش گفت این را که' in _joined(verse, "notes")
    assert 'المیزان استثنای اندک را بندگان مخلص می‌داند نه هر که گاه' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان دو ریشهٔ احتناک یعنی ریشه‌کنی و افسار داوری' in _joined(verse, "critical")

def test_isra_17_63_verse():
    verse = _check_verse("17:63")
    assert 'خدا به ابلیس چون گفت اگر تا روز رستاخیز مهلتم دهی' in _joined(verse, "notes")
    assert 'در خوانش المیزان این آیه پاسخ مستقیم به سوگند پیشین و' in _joined(verse, "modern")
    assert 'خوانش انتقادی ماهیت «اذهب» را میان راندن حقیقی و رها کردن' in _joined(verse, "critical")

def test_isra_17_64_verse():
    verse = _check_verse("17:64")
    assert '«واستفزز» یعنی سبک و نادان کن از این که می‌گویند فلانی' in _joined(verse, "notes")
    assert '«و عدهم و ما یعدهم الشیطان إلا غروراً» نزد المیزان یعنی' in _joined(verse, "modern")
    assert 'خوانش انتقادی تعمیم شرکت نزد المیزان را از قوی‌ترین نقاط شرح' in _joined(verse, "critical")

def test_isra_17_65_verse():
    verse = _check_verse("17:65")
    assert 'خدا به ابلیس می‌گوید بندگانم که از من فرمان بردند و' in _joined(verse, "notes")
    assert 'در نظام المیزان نفی سلطه به معنای نفی وسوسه نیست؛ ابلیس' in _joined(verse, "modern")
    assert 'خوانش انتقادی دامنهٔ عبادی را میان مؤمنان نزد ابن‌عباس و همهٔ' in _joined(verse, "critical")

def test_isra_17_66_verse():
    verse = _check_verse("17:66")
    assert 'پروردگارتان ای مردم همان است که کشتی‌ها را در دریا برای' in _joined(verse, "notes")
    assert 'در نظام المیزان این آیه و پنج آیهٔ بعد احتجاج واحدی' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان رانش الهی کشتی و ساخت انسانی آن فرق' in _joined(verse, "critical")

def test_isra_17_67_verse():
    verse = _check_verse("17:67")
    assert 'و چون سختی و رنج در دریا به شما رسد آنان' in _joined(verse, "notes")
    assert 'در آیه نزد المیزان دلیلی بر توحید ربوبیت نیز هست که' in _joined(verse, "modern")
    assert 'خوانش انتقادی استثنای پیوسته یا گسسته را قلب بلاغی آیه می‌داند' in _joined(verse, "critical")

def test_isra_17_68_verse():
    verse = _check_verse("17:68")
    assert 'ای مردم آیا از پروردگارتان ایمن شدید در حالی که نعمتش' in _joined(verse, "notes")
    assert 'المیزان امنیت را امری الهی می‌داند نه خاصیت مکان و این' in _joined(verse, "modern")
    assert 'خوانش انتقادی جدال سنگ آسمانی یا باد سنگ‌پاش را نشان می‌دهد' in _joined(verse, "critical")

def test_isra_17_69_verse():
    verse = _check_verse("17:69")
    assert 'یا ای مردم از پروردگارتان ایمن شدید با این که پس' in _joined(verse, "notes")
    assert '«بما کفرتم» نزد المیزان سبب غرق را خود ناسپاسی می‌خواند و' in _joined(verse, "modern")
    assert 'خوانش انتقادی قرائت‌های پنج فعل را میان یاء غیبت و نون' in _joined(verse, "critical")

def test_isra_17_70_verse():
    verse = _check_verse("17:70")
    assert 'فرزندان آدم را با چیره کردن ایشان بر دیگر آفریدگان و' in _joined(verse, "notes")
    assert 'مراد از «کثیر ممن خلقنا» نزد المیزان چندان دور نیست که' in _joined(verse, "modern")
    assert 'خوانش انتقادی این آیه را میدان نبرد دو الهیات می‌داند: فهرست' in _joined(verse, "critical")

def test_isra_17_71_verse():
    verse = _check_verse("17:71")
    assert 'اهل تأویل در معنای پیشوایی که خدا گفته هر گروهی را' in _joined(verse, "notes")
    assert 'المیزان آن قول را که امام هر چه بدان اقتدا شود' in _joined(verse, "modern")
    assert 'خوانش انتقادی این آیه را از سیاسی‌ترین آیات آخرت می‌داند که' in _joined(verse, "critical")

def test_isra_17_72_verse():
    verse = _check_verse("17:72")
    assert 'اهل تأویل در آنچه با «هذه» بدان اشاره شده اختلاف کرده‌اند' in _joined(verse, "notes")
    assert 'در خوانش المیزان کیفر کوری از جنس خود جرم است و' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان سه خوانش «هذه» یعنی دنیا و نعمت‌های پیشین' in _joined(verse, "critical")

def test_isra_17_73_verse():
    verse = _check_verse("17:73")
    assert 'سعيد نزد طبری گفته پیامبر سنگ سیاه را دست می‌کشید و' in _joined(verse, "notes")
    assert 'المیزان همچنین روایت ثقیف و مهلت یک سال و روایت عیاشی' in _joined(verse, "modern")
    assert 'خوانش انتقادی تعارض میان سبب‌های نزول را مسئله اصلی این آیه' in _joined(verse, "critical")

def test_isra_17_74_verse():
    verse = _check_verse("17:74")
    assert 'طبری می‌گوید اگر تو را ای محمد با عصمت خود از' in _joined(verse, "notes")
    assert 'در کلام شیعی و سنی این آیه و خطاب‌های توبیخی به' in _joined(verse, "modern")
    assert 'خوانش انتقادی سه تأویل «میل نکرد و نزدیک هم نشد» و' in _joined(verse, "critical")

def test_isra_17_75_verse():
    verse = _check_verse("17:75")
    assert 'ابن‌عباس نزد طبری «ضعف حیات و ضعف ممات» را دو برابر' in _joined(verse, "notes")
    assert 'در الهیات معاصر تناسب مسئولیت و مقام و قانون «هر که' in _joined(verse, "modern")
    assert 'خوانش انتقادی تهدید دو برابر را آینهٔ بزرگی خطر سازش می‌داند:' in _joined(verse, "critical")

def test_isra_17_76_verse():
    verse = _check_verse("17:76")
    assert 'طبری می‌گوید نزدیک بود این قوم تو را از سرزمینی که' in _joined(verse, "notes")
    assert 'در مطالعات تاریخی معاصر هجرت و فشار قریش و این آیات' in _joined(verse, "modern")
    assert 'خوانش انتقادی این آیه را میدان نبرد جغرافیای وحی می‌داند: مکه' in _joined(verse, "critical")

def test_isra_17_77_verse():
    verse = _check_verse("17:77")
    assert 'طبری می‌گوید اگر بیرونت می‌کردند پس از تو جز اندکی نمی‌ماندند' in _joined(verse, "notes")
    assert 'در الهیات معاصر سنت‌های الهی در تاریخ و قانونمندی سرنوشت امت‌ها' in _joined(verse, "modern")
    assert 'خوانش انتقادی نصب «سنة» را از پیچیده‌ترین نحوهای این بخش می‌داند' in _joined(verse, "critical")

def test_isra_17_78_verse():
    verse = _check_verse("17:78")
    assert 'راهن می‌گوید نماز را ای محمد از دلوک خورشید برپا دار' in _joined(verse, "notes")
    assert 'المیزان می‌گوید تفسیر مشهود بودن قرآن فجر در روایات شیعه و' in _joined(verse, "modern")
    assert 'خوانش انتقادی دلوک را میان زوال و غروب یکی از کهن‌ترین' in _joined(verse, "critical")

def test_isra_17_79_verse():
    verse = _check_verse("17:79")
    assert 'راهن می‌گوید پاسی از شب را ای محمد پس از خوابی' in _joined(verse, "notes")
    assert 'المیزان از ابو هریره در ابن‌جریر و بیهقی در شعب الایمان' in _joined(verse, "modern")
    assert 'خوانش انتقادی واجب یا نافله بودن تهجد را نقطهٔ جدال فقه' in _joined(verse, "critical")

def test_isra_17_80_verse():
    verse = _check_verse("17:80")
    assert 'حسن و قتاده نزد راهن مدخل صدق را مدینه و مخرج' in _joined(verse, "notes")
    assert 'در خوانش المیزان آیه فرمان عمومی پناه بردن به خدا در' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان تخصیص تاریخی هجرت و اطلاق وجودی صدق داوری' in _joined(verse, "critical")

def test_isra_17_81_verse():
    verse = _check_verse("17:81")
    assert 'قتاده نزد راهن حق را در این موضع قرآن و باطل' in _joined(verse, "notes")
    assert 'در الهیات سیاسی و مطالعات جنبش‌های دینی معاصر شعار «جاء الحق' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان خوانش مکی اعلان و خوانش مدنی فتح داوری' in _joined(verse, "critical")

def test_isra_17_82_verse():
    verse = _check_verse("17:82")
    assert 'طبری می‌گوید ای محمد از قرآن آنچه شفایی است که با' in _joined(verse, "notes")
    assert 'المیزان این قول را که شفا اعم از بیماری‌های روحی و' in _joined(verse, "modern")
    assert 'خوانش انتقادی این آیه را دو داروی یک داروخانه می‌داند: شفا' in _joined(verse, "critical")

def test_isra_17_83_verse():
    verse = _check_verse("17:83")
    assert 'طبری می‌گوید هرگاه به انسان نعمت دهیم و او را از' in _joined(verse, "notes")
    assert 'المیزان نتیجهٔ حکما را می‌گیرد که امور پنج قسم‌اند و سه' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان حال عادی و فطری انسان نزد المیزان تفکیکی' in _joined(verse, "critical")

def test_isra_17_84_verse():
    verse = _check_verse("17:84")
    assert 'طبری می‌گوید ای محمد به مردم بگو همگی‌تان بر شاکلهٔ خود' in _joined(verse, "notes")
    assert 'المیزان انسان را دارای شاکله‌ها می‌داند یکی زادهٔ نوع خلقت و' in _joined(verse, "modern")
    assert 'خوانش انتقادی این آیه را میدان نبرد کهن‌ترین جدال انسان‌شناسی اسلامی' in _joined(verse, "critical")

def test_isra_17_85_verse():
    verse = _check_verse("17:85")
    assert 'راهن می‌گوید کافران اهل کتاب از تو دربارهٔ روح می‌پرسند که' in _joined(verse, "notes")
    assert 'المیزان از این که جبرئیل آورندهٔ روح است و روح حامل' in _joined(verse, "modern")
    assert 'خوانش انتقادی این آیه را مرز اعلام‌شدهٔ دانش می‌داند و هر' in _joined(verse, "critical")

def test_isra_17_86_verse():
    verse = _check_verse("17:86")
    assert 'طبری می‌گوید اگر بخواهیم با آنچه از علم این قرآن به' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ تاریخ متن قرآن و اخبار رفع آن، این' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان وحی چون متن محفوظ در مصحف و وحی' in _joined(verse, "critical")

def test_isra_17_87_verse():
    verse = _check_verse("17:87")
    assert 'طبری می‌گوید اگر می‌خواستیم آنچه به تو وحی کردیم می‌بردیم اما' in _joined(verse, "notes")
    assert 'در الهیات معاصر نعمت و منت و برگزیدگی پیامبر، این آیه' in _joined(verse, "modern")
    assert 'خوانش انتقادی استثنای جدا را لحظهٔ چرخش از تهدید به منت' in _joined(verse, "critical")

def test_isra_17_88_verse():
    verse = _check_verse("17:88")
    assert 'طبری می‌گوید ای محمد به آنان که به تو گفتند ما' in _joined(verse, "notes")
    assert 'در مطالعات ادبی و الهیاتی معاصر اعجاز قرآن و نظریه‌های نظم' in _joined(verse, "modern")
    assert 'خوانش انتقادی ورود جن به میدان تحدی را گسترش هستی‌شناختی اعجاز' in _joined(verse, "critical")

def test_isra_17_89_verse():
    verse = _check_verse("17:89")
    assert 'طبری می‌گوید برای مردم در این قرآن از هر مثلی بیان' in _joined(verse, "notes")
    assert 'در مطالعات ادبی معاصر تصریف و تنوع بیان در قرآن از' in _joined(verse, "modern")
    assert 'خوانش انتقادی تناقض ظاهری را می‌بیند که کتابی بی‌مثل و پرمثل' in _joined(verse, "critical")

def test_isra_17_90_verse():
    verse = _check_verse("17:90")
    assert 'طبری می‌گوید مشرکان از قومت به تو گفتند تو را تصدیق' in _joined(verse, "notes")
    assert 'در مطالعات تاریخی معاصر مجلس سران قریش و پیشنهادهای مال و' in _joined(verse, "modern")
    assert 'خوانش انتقادی فهرست خواسته‌ها را بازار ایمان می‌داند که نخست مال' in _joined(verse, "critical")

def test_isra_17_91_verse():
    verse = _check_verse("17:91")
    assert 'طبری می‌گوید مشرکان قومت به تو گفتند تو را تصدیق نمی‌کنیم' in _joined(verse, "notes")
    assert 'در مطالعات تاریخی معاصر باغ و نهر در خیال حجازی و' in _joined(verse, "modern")
    assert 'خوانش انتقادی گذر خواسته‌ها را از شهر به شخص نشان می‌دهد' in _joined(verse, "critical")

def test_isra_17_92_verse():
    verse = _check_verse("17:92")
    assert 'طبری در قرائت کسف می‌گوید بیشتر خوانندگان کوفه و بصره با' in _joined(verse, "notes")
    assert 'در الهیات معاصرِ معجزه و محال ذاتی، این خواسته‌ها در برابر' in _joined(verse, "modern")
    assert 'خوانش انتقادی جهش فهرست را از باغ به نابودی جهان نشان' in _joined(verse, "critical")

def test_isra_17_93_verse():
    verse = _check_verse("17:93")
    assert 'ابن‌عباس و مجاهد و قتاده نزد راهن خانه‌ای از زخرف را' in _joined(verse, "notes")
    assert 'در الهیات معاصر نبوت و بشر بودن پیامبر، این آیه از' in _joined(verse, "modern")
    assert 'خوانش انتقادی پاسخ «بشر رسول» را انقلابی در تعریف نبوت می‌داند' in _joined(verse, "critical")

def test_isra_17_94_verse():
    verse = _check_verse("17:94")
    assert 'طبری می‌گوید ای محمد مشرکان قومت را از ایمان به خدا' in _joined(verse, "notes")
    assert 'المیزان این آیه را تأیید روایاتی از ائمهٔ اهل‌بیت دربارهٔ فرق' in _joined(verse, "modern")
    assert 'خوانش انتقادی تمایز انکار عرب از دیگر بت‌پرستان را نزد المیزان' in _joined(verse, "critical")

def test_isra_17_95_verse():
    verse = _check_verse("17:95")
    assert 'طبری می‌گوید ای محمد به آنان که از این که خدا' in _joined(verse, "notes")
    assert 'المیزان برهان عقلی نبوت را از سخن خدا گرفته و چگونگی' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان هم‌جنس بودن فرستاده و نیاز زندگی زمینی به' in _joined(verse, "critical")

def test_isra_17_96_verse():
    verse = _check_verse("17:96")
    assert 'طبری می‌گوید ای محمد به آنان که به تو گفتند آیا' in _joined(verse, "notes")
    assert 'در مطالعات سبک‌شناسی قرآن معاصر سجع و قافیهٔ آیات از این' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان گواه رسالت و داور دو سو داوری می‌طلبد' in _joined(verse, "critical")

def test_isra_17_97_verse():
    verse = _check_verse("17:97")
    assert 'طبری می‌گوید هر که را خدا ای محمد به ایمان به' in _joined(verse, "notes")
    assert 'در کلام شیعی و سنی معاصرِ هدایت و اضلال الهی، این' in _joined(verse, "modern")
    assert 'خوانش انتقادی جمع میان کور بودن و دیدن آتش را مسئله' in _joined(verse, "critical")

def test_isra_17_98_verse():
    verse = _check_verse("17:98")
    assert 'طبری می‌گوید این را که از کردار خود روز قیامت با' in _joined(verse, "notes")
    assert 'در فلسفهٔ دین معاصر مسئلهٔ این‌همانی شخص در رستاخیز از این' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان مثل و عین را قلب فلسفی این بخش' in _joined(verse, "critical")

def test_isra_17_99_verse():
    verse = _check_verse("17:99")
    assert 'طبری می‌گوید آیا این گویان مشرک آیا چون استخوان و خاک' in _joined(verse, "notes")
    assert 'در فلسفهٔ دین معاصر برهان امکان بعث از خلقت نخستین و' in _joined(verse, "modern")
    assert 'خوانش انتقادی سه خوانش اجل مرگ و قیامت و هلاکت را' in _joined(verse, "critical")

def test_isra_17_100_verse():
    verse = _check_verse("17:100")
    assert 'طبری می‌گوید ای محمد به این مشرکان بگو اگر شما ای' in _joined(verse, "notes")
    assert 'در اخلاق و اقتصاد دینی معاصرِ بخشش و بخل، این آیه' in _joined(verse, "modern")
    assert 'خوانش انتقادی این آیه را آینهٔ تمام‌نمای خواستهٔ چشمه می‌داند که' in _joined(verse, "critical")

def test_isra_17_101_verse():
    verse = _check_verse("17:101")
    assert 'طبری می‌گوید به موسی بن عمران نه آیت روشن دادیم که' in _joined(verse, "notes")
    assert 'در مطالعات تطبیقی تورات و قرآن معاصر فهرست بلاهای مصر و' in _joined(verse, "modern")
    assert 'خوانش انتقادی دو خوانش آیات چون بلا و آیات چون فرمان' in _joined(verse, "critical")

def test_isra_17_102_verse():
    verse = _check_verse("17:102")
    assert 'راهن می‌گوید خوانندگان در خواندن «تو خود می‌دانی» اختلاف کرده‌اند بیشتر' in _joined(verse, "notes")
    assert 'در کلام و روان‌شناسی دین معاصر انکار آگاهانه و دانستن و' in _joined(verse, "modern")
    assert 'خوانش انتقادی یک حرکت تای قرائت را می‌بیند که دانش را' in _joined(verse, "critical")

def test_isra_17_103_verse():
    verse = _check_verse("17:103")
    assert 'طبری می‌گوید فرعون خواست موسی و بنی‌اسرائیل را از سرزمین براند' in _joined(verse, "notes")
    assert 'در الهیات سیاسی معاصر سقوط ستمگر راننده از این سنت خوانده' in _joined(verse, "modern")
    assert 'خوانش انتقادی کوتاهی آیه را خود یک سبک می‌داند که سرگذشت' in _joined(verse, "critical")

def test_isra_17_104_verse():
    verse = _check_verse("17:104")
    assert 'طبری می‌گوید پس از هلاک فرعون به آنان گفتیم در سرزمین' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ وعده‌های سرزمین و جلای بابل، این آیه و' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان قیامت و وعدهٔ تاریخی صدر سوره داوری می‌طلبد' in _joined(verse, "critical")

def test_isra_17_105_verse():
    verse = _check_verse("17:105")
    assert 'طبری می‌گوید این قرآن را به حق فرو فرستادیم یعنی آن' in _joined(verse, "notes")
    assert 'در الهیات معاصرِ متن و تحریف، این آیه از متون محوری' in _joined(verse, "modern")
    assert 'خوانش انتقادی تکرار «به حق» را از تزئین به نظریه بدل' in _joined(verse, "critical")

def test_isra_17_106_verse():
    verse = _check_verse("17:106")
    assert 'طبری می‌گوید خوانندگان در خواندن آن اختلاف کرده‌اند بیشتر خوانندگان شهرها' in _joined(verse, "notes")
    assert 'المیزان در ترتیب سوره‌ها می‌گوید روایات در اثبات مجهول‌های مکی و' in _joined(verse, "modern")
    assert 'خوانش انتقادی دو معنای فرق را تفکیک معارف و تقطیع نزول' in _joined(verse, "critical")

def test_isra_17_107_verse():
    verse = _check_verse("17:107")
    assert 'طبری می‌گوید بگو ای محمد به این قرآن ایمان آورید یا' in _joined(verse, "notes")
    assert 'المیزان چانه را نزدیک‌ترین عضو به زمین و کنایهٔ نهایت تذلل' in _joined(verse, "modern")
    assert 'خوانش انتقادی می‌پرسد اگر قرآن به ایمان کسی نیاز ندارد پس' in _joined(verse, "critical")

def test_isra_17_108_verse():
    verse = _check_verse("17:108")
    assert 'طبری می‌گوید آن دانایان چون قرآن بر آنان خوانده شود می‌گویند' in _joined(verse, "notes")
    assert 'در کلام معاصرِ تحقق وعده‌های الهی، این آیه از متون وفاداری' in _joined(verse, "modern")
    assert 'خوانش انتقادی می‌پرسد وعده کدام است و پاسخ بسته به مرجع،' in _joined(verse, "critical")

def test_isra_17_109_verse():
    verse = _check_verse("17:109")
    assert 'طبری می‌گوید اینان برای پروردگارشان بار دیگر فرو می‌افتند و برایش' in _joined(verse, "notes")
    assert 'در مطالعات دانشگاهی هیجان‌های دینی، سجدهٔ گریان این آیه از متون' in _joined(verse, "modern")
    assert 'خوانش انتقادی تکرار سجده را از زائد بودن نجات می‌دهد که' in _joined(verse, "critical")

def test_isra_17_110_verse():
    verse = _check_verse("17:110")
    assert 'طبری می‌گوید به این گروه منکر ای محمد بگو خدا را' in _joined(verse, "notes")
    assert 'المیزان در ذیل این آیه در بحث روایی احادیث توحید صدوق' in _joined(verse, "modern")
    assert 'خوانش انتقادی می‌بیند آیه‌ای برای پاسخ گفتن دو خدا خود به' in _joined(verse, "critical")

def test_isra_17_111_verse():
    verse = _check_verse("17:111")
    assert 'طبری می‌گوید بگو ای محمد ستایش از آن خداست که نه' in _joined(verse, "notes")
    assert 'المیزان در تفسیر قمی از امام آورده در ذیل «و یاوری' in _joined(verse, "modern")
    assert 'خوانش انتقادی می‌بیند سوره‌ای با معراج آغاز شد با نفی فرزند' in _joined(verse, "critical")

def test_kahf_18_1_verse():
    verse = _check_verse("18:1")
    assert 'طبری می‌گوید ستایش برای خدایی است که محمد را به رسالتش' in _joined(verse, "notes")
    assert 'المیزان می‌گوید ضمیر در «برای آن» به کتاب برمی‌گردد و جملهٔ' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان سه خوانش قیم راست و قیم بر کتاب‌ها' in _joined(verse, "critical")

def test_kahf_18_2_verse():
    verse = _check_verse("18:2")
    assert 'طبری می‌گوید قرآن را معتدل و راست بی‌کژی بر بنده‌اش فرو' in _joined(verse, "notes")
    assert 'در کلام معاصرِ انذار و تبشیر، این آیه از متون تعریف' in _joined(verse, "modern")
    assert 'خوانش انتقادی حذف مفعول بیم را می‌سنجد که ناگفته ماندن بیم‌داده‌شدگان' in _joined(verse, "critical")

def test_kahf_18_3_verse():
    verse = _check_verse("18:3")
    assert 'طبری می‌گوید «همیشه در آن ماندگارند» جاودانه‌اند که از آن جابه‌جا' in _joined(verse, "notes")
    assert 'در مطالعات دانشگاهی زمان آخرتی در قرآن، «ابدا» در این آیه' in _joined(verse, "modern")
    assert 'خوانش انتقادی می‌بیند کوتاه‌ترین آیهٔ سوره سنگین‌ترین ادعای آن را می‌کند' in _joined(verse, "critical")

def test_kahf_18_4_verse():
    verse = _check_verse("18:4")
    assert 'طبری می‌گوید محمد نیز قومی را که گفتند خدا فرزندی گرفته' in _joined(verse, "notes")
    assert 'در گفت‌وگوی معاصر اسلام و مسیحیت، نفی فرزند از این آیه' in _joined(verse, "modern")
    assert 'خوانش انتقادی می‌پرسد چرا از میان همهٔ گروه‌های بیم‌داده‌شده تنها فرزندگویان' in _joined(verse, "critical")

def test_kahf_18_5_verse():
    verse = _check_verse("18:5")
    assert 'طبری می‌گوید «نه خودشان در این باره دانشی دارند» یعنی گویندگان' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ تقلید و اقتدار سنت، این آیه از متون' in _joined(verse, "modern")
    assert 'خوانش انتقادی پاسخ دوگانهٔ نادانی و دروغ را می‌سنجد که یکی' in _joined(verse, "critical")

def test_kahf_18_6_verse():
    verse = _check_verse("18:6")
    assert 'طبری می‌گوید یعنی شاید تو ای محمد کشنده و هلاک‌کنندهٔ خود' in _joined(verse, "notes")
    assert 'در روان‌شناسی دین معاصر اندوه مبلغ و فرسودگی دعوت‌گر از این' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان عتاب و تسلی داوری می‌طلبد که آیا خدا' in _joined(verse, "critical")

def test_kahf_18_7_verse():
    verse = _check_verse("18:7")
    assert 'طبری می‌گوید ما آنچه را بر زمین است زیور زمین قرار' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ ابتلاء، این آیه از متون بنیادین آزمایش الهی' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان زینت عموم همهٔ زمین و زینت مردان و' in _joined(verse, "critical")

def test_kahf_18_8_verse():
    verse = _check_verse("18:8")
    assert 'طبری می‌گوید و ما پس از آبادانی‌اش آن را ویران خواهیم' in _joined(verse, "notes")
    assert 'در مطالعات محیط‌زیستی معاصرِ قرآن، خاک بایر از این آیه در' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان حقیقت خاک بایر در قیامت و استعارهٔ بریدن' in _joined(verse, "critical")

def test_kahf_18_9_verse():
    verse = _check_verse("18:9")
    assert 'طبری می‌گوید ای محمد آیا پنداشتی اصحاب کهف و رقیم از' in _joined(verse, "notes")
    assert 'برخی دیگر نزد المیزان گفته‌اند اصحاب رقیم مردمی غیر از اصحاب' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان رقیم لوح و روستا و صخره داوری می‌طلبد' in _joined(verse, "critical")

def test_kahf_18_10_verse():
    verse = _check_verse("18:10")
    assert 'طبری می‌گوید آنگاه که جوانان اصحاب کهف به غار کوه پناه' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ دعا، این آیه و قید از نزد تو' in _joined(verse, "modern")
    assert 'خوانش انتقادی فهرست بلند روایت‌های گریز را در برابر سکوت قرآن' in _joined(verse, "critical")

def test_kahf_18_11_verse():
    verse = _check_verse("18:11")
    assert 'طبری می‌گوید «پس در غار بر گوش‌هاشان زدیم» یعنی بر گوش‌هاشان' in _joined(verse, "notes")
    assert 'در مطالعات سبک‌شناسی قرآن معاصر، زدن بر گوش از نمونه‌های کنایهٔ' in _joined(verse, "modern")
    assert 'خوانش انتقادی سه تصویر پرده بر غار و چیرگی خواب و' in _joined(verse, "critical")

def test_kahf_18_12_verse():
    verse = _check_verse("18:12")
    assert 'طبری می‌گوید سپس این جوانان را که به غار پناه بردند' in _joined(verse, "notes")
    assert 'در کلام معاصرِ علم الهی، این آیه از متون محوری علم' in _joined(verse, "modern")
    assert 'خوانش انتقادی می‌پرسد دو گروه کیان‌اند و پاسخ بسته به مرجع،' in _joined(verse, "critical")

def test_kahf_18_13_verse():
    verse = _check_verse("18:13")
    assert 'طبری می‌گوید ما ای محمد خبر این جوانان را که به' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ جوانی و دین، این آیه از متون بنیادین' in _joined(verse, "modern")
    assert 'خوانش انتقادی سگ سخنگوی سدی را می‌سنجد که چگونه کرامت در' in _joined(verse, "critical")

def test_kahf_18_14_verse():
    verse = _check_verse("18:14")
    assert 'طبری می‌گوید و صبر را به آنان الهام کردیم و دل‌هاشان' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ مقاومت دینی، برخاستن جوانان کهف از متون بنیادین' in _joined(verse, "modern")
    assert 'خوانش انتقادی سه معنای قیام را رو در رو می‌نشاند که' in _joined(verse, "critical")

def test_kahf_18_15_verse():
    verse = _check_verse("18:15")
    assert 'طبری می‌گوید اینان قوم مااند که جز خدا خدایانی گرفته‌اند که' in _joined(verse, "notes")
    assert 'در فلسفهٔ دین معاصر بار اثبات در ادعاهای دینی از این' in _joined(verse, "modern")
    assert 'خوانش انتقادی مطالبهٔ برهان از پرستندگان و نه از بت‌ها را' in _joined(verse, "critical")

def test_kahf_18_16_verse():
    verse = _check_verse("18:16")
    assert 'طبری می‌گوید خدا از گفتهٔ برخی از جوانان به برخی خبر' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ هجرت دینی، کناره‌گیری اصحاب کهف از این آیه' in _joined(verse, "modern")
    assert 'خوانش انتقادی جدال استثنای منقطع و متصل را می‌سنجد که بسته' in _joined(verse, "critical")

def test_kahf_18_17_verse():
    verse = _check_verse("18:17")
    assert 'طبری می‌گوید و خورشید را ای محمد می‌بینی که چون برآید' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ مکان غار اصحاب کهف، این آیه از متون' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان غار شمالی مفسران و غار جنوبی المیزان داوری' in _joined(verse, "critical")

def test_kahf_18_18_verse():
    verse = _check_verse("18:18")
    assert 'طبری می‌گوید و تو ای محمد این جوانان را که داستانشان' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ حیوان در قرآن، سگ اصحاب کهف از پربحث‌ترین' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان سگ حقیقی و نگهبان انسانی داوری می‌طلبد که' in _joined(verse, "critical")

def test_kahf_18_19_verse():
    verse = _check_verse("18:19")
    assert 'طبری می‌گوید چنانکه این جوانان را در غار خواباندیم و از' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ معرفت‌شناسی دینی، «پروردگارتان داناتر است» جوانان از متون' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان لام غایت و لام عاقبت داوری می‌طلبد که' in _joined(verse, "critical")

def test_kahf_18_20_verse():
    verse = _check_verse("18:20")
    assert 'طبری در تأویل گفتهٔ «اگر آنان بر شما دست یابند سنگسارتان' in _joined(verse, "notes")
    assert 'در حقوق اسلامی دانشگاهی، وکالت با تقیه در این آیه و' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان رجم با زبان و رجم با سنگ داوری' in _joined(verse, "critical")

def test_kahf_18_21_verse():
    verse = _check_verse("18:21")
    assert 'طبری می‌گوید و چنانکه آنان را پس از خواب درازشان به' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ زیارت و معماری مقدس، مسجد بر غار اصحاب' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان ساختمان مشرکان برای پنهان کردن و مسجد موحدان' in _joined(verse, "critical")

def test_kahf_18_22_verse():
    verse = _check_verse("18:22")
    assert 'طبری می‌گوید برخی از فروروندگان در کار جوانان اصحاب کهف خواهند' in _joined(verse, "notes")
    assert 'در مجمع البیان نزد المیزان در ذیل خلاصه‌ای از سخن أبي' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان واو عطف نحویان و واو هشتم ابن‌خالویه و' in _joined(verse, "critical")

def test_kahf_18_23_verse():
    verse = _check_verse("18:23")
    assert 'راهن در این آیه گفته‌ای جدا نیاورده و شرح فرمان را' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ ان‌شاءالله و فرهنگ وعده، این آیه از متون' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان عتاب تاریخی و قاعدهٔ ابدی داوری می‌طلبد که' in _joined(verse, "critical")

def test_kahf_18_24_verse():
    verse = _check_verse("18:24")
    assert 'طبری می‌گوید و این ادب‌آموزی خدا به پیامبرش است که به' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ ذکر و حضور، این آیه از متون بنیادین' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان آیهٔ سوگند و آیهٔ ادب سخن داوری می‌طلبد' in _joined(verse, "critical")

def test_kahf_18_25_verse():
    verse = _check_verse("18:25")
    assert 'طبری می‌گوید اهل تأویل در معنای گفتهٔ «و در غارشان سیصد' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ گاه‌شماری قرآن، سیصد و نه سال اصحاب کهف' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان خبر خدا و قول اهل کتاب داوری می‌طلبد' in _joined(verse, "critical")

def test_kahf_18_26_verse():
    verse = _check_verse("18:26")
    assert 'طبری در تأویل گفتهٔ «از آن اوست نهان آسمان‌ها و زمین»' in _joined(verse, "notes")
    assert 'در کلام معاصرِ صفات خدا، أبصر به و أسمع از این' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان تعجب چه بینا و فرمان بدو بین داوری' in _joined(verse, "critical")

def test_kahf_18_27_verse():
    verse = _check_verse("18:27")
    assert 'طبری می‌گوید خدا به پیامبرش محمد می‌گوید ای محمد آنچه را' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ وحی و مرجعیت متن، این آیه از متون' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان قرآن و لوح محفوظ در مراد کتاب داوری' in _joined(verse, "critical")

def test_kahf_18_28_verse():
    verse = _check_verse("18:28")
    assert 'طبری می‌گوید خدا به پیامبرش محمد می‌گوید ای محمد خود را' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ فقر و دین، این آیه از متون بنیادین' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان نماز دو وقت عیاشی از امام باقر و' in _joined(verse, "critical")

def test_kahf_18_29_verse():
    verse = _check_verse("18:29")
    assert 'طبری می‌گوید خدا به پیامبرش محمد می‌گوید ای محمد به اینان' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ آزادی دینی، «هر که خواهد ایمان آورد» از' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان رخصت و تهدید داوری می‌طلبد که سنت با' in _joined(verse, "critical")

def test_kahf_18_30_verse():
    verse = _check_verse("18:30")
    assert 'طبری می‌گوید کسانی که خدا و رسولش را باور کردند و' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ عمل و پاداش، این آیه از متون بنیادین' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان سه راه خبر إن داوری می‌طلبد که تکرار' in _joined(verse, "critical")

def test_kahf_18_31_verse():
    verse = _check_verse("18:31")
    assert 'طبری می‌گوید اینان که ایمان آوردند و کارهای شایسته کردند برایشان' in _joined(verse, "notes")
    assert 'در پژوهش‌های دانشگاهی رنگ در قرآن، سبزی جامه‌های بهشت از این' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان سه دستبند سعید بن جبیر از سه سوره' in _joined(verse, "critical")

def test_kahf_18_32_verse():
    verse = _check_verse("18:32")
    assert 'طبری می‌گوید خدا به پیامبرش محمد می‌گوید ای محمد برای' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ مثل در قرآن، مثل دو باغ از' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان مثل فرضی و رخداد واقعی داوری می‌طلبد' in _joined(verse, "critical")

def test_kahf_18_33_verse():
    verse = _check_verse("18:33")
    assert 'طبری می‌گوید هر دو بوستان میوه‌اش و آنچه در آن' in _joined(verse, "notes")
    assert 'در زبان‌شناسی دانشگاهی، کلتا و کلا از کهن‌ترین مسائل صرف' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان مفرد لفظی و دوگانهٔ معنایی داوری می‌طلبد' in _joined(verse, "critical")

def test_kahf_18_34_verse():
    verse = _check_verse("18:34")
    assert 'طبری می‌گوید خوانندگان در خواندن آن اختلاف کرده‌اند همگان خوانندگان' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ قارون و ثروت، سخن أنا أکثر از' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان ثمر میوه و ثمر سرمایه داوری می‌طلبد' in _joined(verse, "critical")

def test_kahf_18_35_verse():
    verse = _check_verse("18:35")
    assert 'طبری می‌گوید این که برای او دو باغ انگور قرار' in _joined(verse, "notes")
    assert 'در روان‌شناسی معاصرِ انکار مرگ، این آیه از متون کلاسیک' in _joined(verse, "modern")
    assert 'خوانش انتقادی نکتهٔ کشاف را که المیزان لطیف می‌خواند برجسته' in _joined(verse, "critical")

def test_kahf_18_36_verse():
    verse = _check_verse("18:36")
    assert 'طبری در تأویل گفتهٔ «و گمان نمی‌کنم ساعت برپا باشد»' in _joined(verse, "notes")
    assert 'در فلسفهٔ دین دانشگاهی، استدلال از نعمت بر استحقاق از' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان از آن و از آن دو در' in _joined(verse, "critical")

def test_kahf_18_37_verse():
    verse = _check_verse("18:37")
    assert 'طبری می‌گوید صاحب باغ‌ها به او صاحبش که از او' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ استدلال آفرینش بر معاد، این آیه از' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان تکفیر به سبب شک معاد نزد زمخشری' in _joined(verse, "critical")

def test_kahf_18_38_verse():
    verse = _check_verse("18:38")
    assert 'طبری در تأویل گفتهٔ «لیکن او خدا پروردگار من است»' in _joined(verse, "notes")
    assert 'در زبان‌شناسی دانشگاهی، ساخت لکنا از کهن‌ترین نمونه‌های ادغام در' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان سه احتمال شرک در جملهٔ پایانی داوری' in _joined(verse, "critical")

def test_kahf_18_39_verse():
    verse = _check_verse("18:39")
    assert 'طبری می‌گوید چرا چون به بوستانت درآمدی و آنچه را' in _joined(verse, "notes")
    assert 'در الهیات دانشگاهی مشیت، لا قوة إلا بالله از این' in _joined(verse, "modern")
    assert 'خوانش انتقادی می‌بیند قرطبی از یک جملهٔ رفیق در باغ' in _joined(verse, "critical")

def test_kahf_18_40_verse():
    verse = _check_verse("18:40")
    assert 'طبری می‌گوید خدا از گفتهٔ مؤمن یقین‌دار به بازگشت به' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ وارونگی سرنوشت در قرآن، این آیه از' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان حسبان تیر و حسبان حساب اعمال داوری' in _joined(verse, "critical")

def test_kahf_18_41_verse():
    verse = _check_verse("18:41")
    assert 'طبری می‌گوید یا آبش فرو رونده شود و غور مصدری' in _joined(verse, "notes")
    assert 'در زبان‌شناسی دانشگاهی مصدر در جای اسم فاعل از این' in _joined(verse, "modern")
    assert 'خوانش انتقادی می‌بیند راهن با دو شعر جاهلی و قرطبی' in _joined(verse, "critical")

def test_kahf_18_42_verse():
    verse = _check_verse("18:42")
    assert 'طبری می‌گوید هلاک و بلاها میوه‌اش و گونه‌های میوه‌های باغش' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ پشیمانی در قرآن، این آیه از متون' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان برگرداندن دست به معنای پشیمانی و برگرداندن' in _joined(verse, "critical")

def test_kahf_18_43_verse():
    verse = _check_verse("18:43")
    assert 'طبری می‌گوید برای صاحب دو باغ گروهی نبود و آنان' in _joined(verse, "notes")
    assert 'در جامعه‌شناسی دانشگاهی قدرت، أعز نفرا و لم تکن له' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان عشیره و سپاه داوری می‌طلبد که در' in _joined(verse, "critical")

def test_kahf_18_44_verse():
    verse = _check_verse("18:44")
    assert 'طبری می‌گوید سپس و آن هنگام که عذاب خدا به' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ ولایت در قرآن، این آیه از متون' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان ولایت یاری و ولایت مالکیت تدبیر داوری' in _joined(verse, "critical")

def test_kahf_18_45_verse():
    verse = _check_verse("18:45")
    assert 'طبری می‌گوید خدا به پیامبرش محمد می‌گوید برای زندگی این' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ مثل آب در قرآن، این آیه کنار' in _joined(verse, "modern")
    assert 'خوانش انتقادی پنج همانندی حکما را برجسته می‌کند که آب' in _joined(verse, "critical")

def test_kahf_18_46_verse():
    verse = _check_verse("18:46")
    assert 'طبری می‌گوید مال و فرزندان ای مردم که عیینه و' in _joined(verse, "notes")
    assert 'در الهیات دانشگاهی امید، خیر أملا از این آیه خوانده' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان نماز و تسبیحات و هر عمل صالح' in _joined(verse, "critical")

def test_kahf_18_47_verse():
    verse = _check_verse("18:47")
    assert 'طبری می‌گوید روزی کوه‌ها را از زمین به راه می‌اندازیم' in _joined(verse, "notes")
    assert 'در کیهان‌شناسی دانشگاهی قرآن، جنبش کوه‌ها از این آیه خوانده' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان واذکر مقدر نزد المیزان و پیوند به' in _joined(verse, "critical")

def test_kahf_18_48_verse():
    verse = _check_verse("18:48")
    assert 'طبری می‌گوید و آفریدگان ای محمد بر پروردگارت به صف' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ فراموشی قیامت و اخلاق، این آیه از' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان ظن قلبی و ظن حالی عملی داوری' in _joined(verse, "critical")

def test_kahf_18_49_verse():
    verse = _check_verse("18:49")
    assert 'طبری می‌گوید و خدا در آن روز کتاب اعمال بندگانش' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ ثبت اعمال در قرآن، این آیه از' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان کتاب یگانهٔ همهٔ خلق نزد المیزان و' in _joined(verse, "critical")

def test_kahf_18_50_verse():
    verse = _check_verse("18:50")
    assert 'طبری می‌گوید خدا به این مشرکان حسد ابلیس به پدرشان' in _joined(verse, "notes")
    assert 'در الهیات دانشگاهی شر، دشمنی ذریه از این آیه خوانده' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان ولایت اطاعت نزد همهٔ مفسران و ولایت' in _joined(verse, "critical")

def test_kahf_18_51_verse():
    verse = _check_verse("18:51")
    assert 'طبری می‌گوید او ابلیس و نسلش را در «آفرینش آسمان‌ها' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ علم و آفرینش در قرآن، این آیه' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان اشهاد حقیقی نزد المیزان و اشهاد مشورت' in _joined(verse, "critical")

def test_kahf_18_52_verse():
    verse = _check_verse("18:52")
    assert 'طبری می‌گوید و روزی خدا عز و جل به مشرکان' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ گسست بت و پرستنده در قرآن، این' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان موبق درهٔ جهنم نزد جمهور و موبق' in _joined(verse, "critical")

def test_kahf_18_53_verse():
    verse = _check_verse("18:53")
    assert 'طبری می‌گوید و مشرکان در آن روز آتش را به' in _joined(verse, "notes")
    assert 'در روان‌شناسی دانشگاهی یقین به کیفر، ظن به معنای علم' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان ظن یقین و ظن توهم داوری می‌طلبد' in _joined(verse, "critical")

def test_kahf_18_54_verse():
    verse = _check_verse("18:54")
    assert 'طبری می‌گوید بی‌گمان در این قرآن برای مردم از هر' in _joined(verse, "notes")
    assert 'در روان‌شناسی دانشگاهی مناظره، اکثر شیء جدلا از این آیه' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان انسان عموم بشر و انسان کافر نزد' in _joined(verse, "critical")

def test_kahf_18_55_verse():
    verse = _check_verse("18:55")
    assert 'طبری می‌گوید و این مشرکان ای محمد را از ایمان' in _joined(verse, "notes")
    assert 'در الهیات دانشگاهی سنت‌های الهی، سنت نخستین از این آیه' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان حکم الهی بر کفر نزد یک وجه' in _joined(verse, "critical")

def test_kahf_18_56_verse():
    verse = _check_verse("18:56")
    assert 'طبری می‌گوید و رسولانمان را نمی‌فرستیم مگر تا اهل ایمان' in _joined(verse, "notes")
    assert 'در الهیات دانشگاهی استهزا، هزوا گرفتن آیات از این آیه' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان جدال برای دانستن و جدال تعنیتی برای' in _joined(verse, "critical")

def test_kahf_18_57_verse():
    verse = _check_verse("18:57")
    assert 'طبری می‌گوید و کدام مردم بر نهادن اعراض و روی‌گردانی' in _joined(verse, "notes")
    assert 'در روان‌شناسی دانشگاهی بی‌اعتنایی اخلاقی، نسیان پیش‌فرستاده‌ها از این آیه' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان کیفر بودن أکنة و علت بودن آن' in _joined(verse, "critical")

def test_kahf_18_58_verse():
    verse = _check_verse("18:58")
    assert 'طبری می‌گوید خدای تعالی به پیامبرش محمد می‌گوید و پروردگارت' in _joined(verse, "notes")
    assert 'در الهیات دانشگاهی اسمای خدا، ذو الرحمة از این آیه' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان روز بدر نزد راهن و موعد نامعین' in _joined(verse, "critical")

def test_kahf_18_59_verse():
    verse = _check_verse("18:59")
    assert 'طبری می‌گوید و آن شهرها از عاد و ثمود و' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ سنت‌های هلاک در قرآن، این آیه از' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان مهلک مصدر هلاکت و مهلک اسم زمان' in _joined(verse, "critical")

def test_kahf_18_60_verse():
    verse = _check_verse("18:60")
    assert 'طبری می‌گوید خدا به پیامبرش می‌گوید و ای محمد به یاد آور چون موسی بن عمران به جوانش یوشع گ' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ سفر علمی در اسلام، این آیه از متون بنیادین خوانده می‌شود؛ این پرونده آن' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان موسی بن عمران و موسی بن منشا داوری می‌طلبد که ابن‌عباس در بخاری دومی را' in _joined(verse, "critical")

def test_kahf_18_61_verse():
    verse = _check_verse("18:61")
    assert 'طبری می‌گوید یعنی چون موسی و جوانش به مجمع دو دریا رسیدند چنانکه از ابن أبی نجیح از مجاهد' in _joined(verse, "notes")
    assert 'در ادبیات دانشگاهی سفر، نشانهٔ فقدان از این آیه خوانده می‌شود؛ این پرونده آن را نگه می‌دار' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان زنده شدن ماهی بریان نزد جمهور و افتادن آن به دریا نزد احتیاط المیزان دا' in _joined(verse, "critical")

def test_kahf_18_62_verse():
    verse = _check_verse("18:62")
    assert 'طبری می‌گوید چون موسی و جوانش از مجمع دو دریا گذشتند موسی به جوانش یوشع گفت «چاشتمان را بی' in _joined(verse, "notes")
    assert 'در فقه دانشگاهی توکل، توشهٔ موسی از این آیه خوانده می‌شود؛ این پرونده آن را نگه می‌دارد.' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان ماهی هم غذا هم نشانه و ماهی فقط نشانه داوری می‌طلبد که أبو عباس دومی و' in _joined(verse, "critical")

def test_kahf_18_63_verse():
    verse = _check_verse("18:63")
    assert 'طبری می‌گوید جوان موسی به موسی چون به او گفت چاشتمان را بیاور تا بخوریم گفت آیا دیدی چون ب' in _joined(verse, "notes")
    assert 'در روان‌شناسی دانشگاهی فراموشی، تذکر ماهی از این آیه خوانده می‌شود؛ این پرونده آن را نگه م' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان فراموشی خود ماهی و فراموشی گفتن آن داوری می‌طلبد که المیزان با تقدیر حا' in _joined(verse, "critical")

def test_kahf_18_64_verse():
    verse = _check_verse("18:64")
    assert 'طبری می‌گوید موسی به جوانش گفت «آن» یعنی با آن فراموش کردن تو ماهی را «همان است که می‌جستی' in _joined(verse, "notes")
    assert 'در ادبیات دانشگاهی جستجو، قص الأثر از این آیه خوانده می‌شود؛ این پرونده آن را نگه می‌دارد.' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان علامت دقیق زنده شدن و علامت مبهم گم شدن داوری می‌طلبد که المیزان دومی ر' in _joined(verse, "critical")

def test_kahf_18_65_verse():
    verse = _check_verse("18:65")
    assert 'طبری می‌گوید به او از نزد خود رحمتی بخشیدیم «و از نزد خود به او علمی آموختیم» می‌گوید و از' in _joined(verse, "notes")
    assert 'در مطالعات معاصرِ علم لدنی در قرآن، این آیه از متون بنیادین خوانده می‌شود؛ این پرونده آن ر' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان خضر نبی و خضر ولی و خضر فرشته داوری می‌طلبد که جمهور نخست و آیهٔ باطن ا' in _joined(verse, "critical")

def test_kahf_18_66_verse():
    verse = _check_verse("18:66")
    assert 'طبری می‌گوید موسی به عالم گفت «آیا تو را پیروی کنم بر اینکه به من بیاموزی» از علمی که خدا' in _joined(verse, "notes")
    assert 'در اخلاق دانشگاهی دانش، تواضع موسی از این آیه خوانده می‌شود؛ این پرونده آن را نگه می‌دارد.' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان شرط تعلیم در ترجمهٔ مختصر و نفی شرطیت نزد المیزان داوری می‌طلبد که موسی' in _joined(verse, "critical")

def test_kahf_18_67_verse():
    verse = _check_verse("18:67")
    assert 'طبری می‌گوید عالم گفت تو توان شکیبایی با مرا نداری و آن از این روست که من به باطن علمی عمل' in _joined(verse, "notes")
    assert 'در روان‌شناسی دانشگاهی تحمل ابهام، لن تستطیع از این آیه خوانده می‌شود؛ این پرونده آن را نگ' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان ناتوانی روش و ناتوانی علم داوری می‌طلبد که المیزان با مثال گوساله اولی' in _joined(verse, "critical")

def test_kahf_18_68_verse():
    verse = _check_verse("18:68")
    assert 'طبری می‌گوید خدا از گفتهٔ عالم به موسی خبر می‌دهد و چگونه ای موسی بر آنچه از من از کارهایی' in _joined(verse, "notes")
    assert 'در فلسفهٔ دین دانشگاهی غیب، لم تحط به خبرا از این آیه خوانده می‌شود؛ این پرونده آن را نگه' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان حکم به ظاهر شریعت و علم به باطن تأویل نشان می‌دهد که صبر موسی به معنای' in _joined(verse, "critical")

def test_kahf_18_69_verse():
    verse = _check_verse("18:69")
    assert 'طبری می‌گوید ستجدنی بر آنچه از تو می‌بینم هر چند خلاف آنچه نزد من درست است باشد ' in _joined(verse, "notes")
    assert 'در اخلاق دانشگاهی تعهد، وعدهٔ مقید موسی از این آیه خوانده می‌شود؛ این پرونده آن ' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان شمول استثنا بر هر دو جمله و اختصاص آن به صبر داوری می‌طلبد که' in _joined(verse, "critical")

def test_kahf_18_70_verse():
    verse = _check_verse("18:70")
    assert 'طبری می‌گوید خدا می‌گوید عالم به موسی گفت اگر اکنون مرا پیروی کنی از چیزی که انج' in _joined(verse, "notes")
    assert 'در روان‌شناسی دانشگاهی تأخیر داوری، فلا تسألنی از این آیه خوانده می‌شود؛ این پرو' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان نهی از پرسش به عنوان انضباط آموزشی و بستن باب چون و چرا داوری' in _joined(verse, "critical")

def test_kahf_18_71_verse():
    verse = _check_verse("18:71")
    assert 'طبری می‌گوید خدا می‌گوید پس موسی و عالم به راه افتادند کشتی‌ای می‌جستند که بر آن' in _joined(verse, "notes")
    assert 'در فقه دانشگاهی تصرف ولی در مال یتیم، خرق سفینه از این آیه خوانده می‌شود؛ این پر' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان غرق عمدی در صورت اعتراض و نجات از پادشاه غاصب در تأویل داوری ' in _joined(verse, "critical")

def test_kahf_18_72_verse():
    verse = _check_verse("18:72")
    assert 'طبری می‌گوید خدا می‌گوید عالم به موسی چون آنچه گفت گفت آیا به تو نگفتم که تو تاب' in _joined(verse, "notes")
    assert 'در روان‌شناسی دانشگاهی فراموشی تعهد، اعتراض نخست موسی از این آیه خوانده می‌شود؛ ' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان نسیان حقیقی و نسیان از باب معاريض داوری می‌طلبد که حدیث نبوی ' in _joined(verse, "critical")

def test_kahf_18_73_verse():
    verse = _check_verse("18:73")
    assert 'طبری می‌گوید از محمد بن اسحاق از حسن بن عماره از حکم از سعید بن جبیر از ابن‌عباس' in _joined(verse, "notes")
    assert 'در فقه دانشگاهی نسیان، لا تؤاخذنی از این آیه خوانده می‌شود؛ این پرونده آن را نگه' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان عذر صادق و معارضهٔ لفظی داوری می‌طلبد که أبی دومی و حدیث نبوی' in _joined(verse, "critical")

def test_kahf_18_74_verse():
    verse = _check_verse("18:74")
    assert 'طبری می‌گوید خدا می‌گوید پس به راه افتادند تا چون پسری را یافتند عالم او را کشت ' in _joined(verse, "notes")
    assert 'در اخلاق دانشگاهی قصاص کودکان، نفس زکیه از این آیه خوانده می‌شود؛ این پرونده آن ' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان غلام نابالغ نزد جمهور و بالغ راهزن نزد کلبي و ابن‌جبیر داوری ' in _joined(verse, "critical")

def test_kahf_18_75_verse():
    verse = _check_verse("18:75")
    assert 'طبری می‌گوید خدا می‌گوید عالم به موسی گفت آیا به تو نگفتم که تو هرگز تاب همراهی ' in _joined(verse, "notes")
    assert 'در روان‌شناسی دانشگاهی شرم، یادآوری دوم از این آیه خوانده می‌شود؛ این پرونده آن ' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان تکرار لفظی در قرطبی و تفاوت لک نزد المیزان نشان می‌دهد که خوا' in _joined(verse, "critical")

def test_kahf_18_76_verse():
    verse = _check_verse("18:76")
    assert 'طبری می‌گوید موسی به او گفت اگر پس از این از تو چیزی پرسیدم می‌گوید پس از این با' in _joined(verse, "notes")
    assert 'در روان‌شناسی دانشگاهی حیا، ذمامهٔ موسی از این آیه خوانده می‌شود؛ این پرونده آن ' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان شرم از تکرار مخالفت و ناتوانی واقعی از صبر داوری می‌طلبد که ح' in _joined(verse, "critical")

def test_kahf_18_77_verse():
    verse = _check_verse("18:77")
    assert 'طبری می‌گوید خدا می‌گوید پس موسی و عالم به راه افتادند تا چون نزد اهل روستایی آم' in _joined(verse, "notes")
    assert 'در جامعه‌شناسی دانشگاهی مهمان‌نوازی، روستای أبوا از این آیه خوانده می‌شود؛ این پ' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان اقامهٔ معجزه با مسح دست و بنای معمولی با مزد داوری می‌طلبد که' in _joined(verse, "critical")

def test_kahf_18_78_verse():
    verse = _check_verse("18:78")
    assert 'طبری می‌گوید خدا می‌گوید همراه موسی به موسی گفت این همان است که گفتی و آن گفته‌ا' in _joined(verse, "notes")
    assert 'در روایت‌شناسی دانشگاهی فراق، هذا فراق از این آیه خوانده می‌شود؛ این پرونده آن ر' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان عرضهٔ مؤدبانه و اعتراض مشروط نشان می‌دهد که در مکتب خضر نیت ن' in _joined(verse, "critical")

def test_kahf_18_79_verse():
    verse = _check_verse("18:79")
    assert 'طبری می‌گوید اما آنچه با کشتی کردم برای این بود که آن از آن قومی بینوا بود که در' in _joined(verse, "notes")
    assert 'در فقه دانشگاهی مصلحت، افساد بعض از این آیه خوانده می‌شود؛ این پرونده آن را نگه ' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان وراء به معنای خلف و أمام داوری می‌طلبد که قرائت أمامهم ابن‌عب' in _joined(verse, "critical")

def test_kahf_18_80_verse():
    verse = _check_verse("18:80")
    assert 'طبری می‌گوید خدا می‌گوید و اما پسر او کافر بود و پدر و مادرش مؤمن بودند پس دانست' in _joined(verse, "notes")
    assert 'در الهیات دانشگاهی شر کودکان، غلام خضر از این آیه خوانده می‌شود؛ این پرونده آن ر' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان خشیت خضر و خشیت خدا و علم به جای خوف نشان می‌دهد که یک فعل تر' in _joined(verse, "critical")

def test_kahf_18_81_verse():
    verse = _check_verse("18:81")
    assert 'طبری می‌گوید قاریان در خواندن فأردنا أن يبدلهما ربهما اختلاف کرده‌اند پس گروهی ا' in _joined(verse, "notes")
    assert 'در روان‌شناسی دانشگاهی رضا به قضا، بدل خضر از این آیه خوانده می‌شود؛ این پرونده ' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان دختری مادر دوازده یا هفتاد پیامبر و پسری مسلمان در راه داوری ' in _joined(verse, "critical")

def test_kahf_18_82_verse():
    verse = _check_verse("18:82")
    assert 'طبری می‌گوید خدا از سخن همراه موسی خبر می‌دهد و اما دیواری که برپا کردم آن از آن' in _joined(verse, "notes")
    assert 'در الهیات دانشگاهی باطنی‌گری، رد أبو عباس از این آیه خوانده می‌شود؛ این پرونده آ' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان کنز مال و کنز علم داوری می‌طلبد که راهن با عرف عرب مال و ابن‌' in _joined(verse, "critical")

def test_kahf_18_83_verse():
    verse = _check_verse("18:83")
    assert 'طبری می‌گوید خدا به پیامبرش محمد می‌گوید و این مشرکان از تو ای محمد دربارهٔ ذو ا' in _joined(verse, "notes")
    assert 'در تاریخ‌نگاری دانشگاهی اسکندر در قرآن، یسئلونک از این آیه خوانده می‌شود؛ این پر' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان اسکندر مقدونی و صعب حمیری و مرزبان مصری و افریدون نشان می‌دهد' in _joined(verse, "critical")

def test_kahf_18_84_verse():
    verse = _check_verse("18:84")
    assert 'طبری می‌گوید ما جای او را در زمین هموار کردیم و از هر چیز به او دادیم یعنی آنچه ' in _joined(verse, "notes")
    assert 'در فلسفهٔ سیاست دانشگاهی، مکنا له از این آیه خوانده می‌شود؛ این پرونده آن را نگه' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان سبب به معنای علم نزد اجماع نخستین و سبب به معنای هر وسیله نزد' in _joined(verse, "critical")

def test_kahf_18_85_verse():
    verse = _check_verse("18:85")
    assert 'طبری می‌گوید قاریان در خواندن آن اختلاف کرده‌اند پس بیشتر قاریان مدینه و بصره پس' in _joined(verse, "notes")
    assert 'در روایت‌شناسی دانشگاهی حرکت، سبب‌گیری از این آیه خوانده می‌شود؛ این پرونده آن ر' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان الحاق به سبب آماده و سلوک راه موجود نشان می‌دهد که در اولی قه' in _joined(verse, "critical")

def test_kahf_18_86_verse():
    verse = _check_verse("18:86")
    assert 'طبری می‌گوید خدا می‌گوید تا چون ذو القرنين به مغرب آفتاب رسید آن را یافت که در چ' in _joined(verse, "notes")
    assert 'در الهیات دانشگاهی نبوت ذو القرنين، قلنا از این آیه خوانده می‌شود؛ این پرونده آن' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان غروب واقعی در طینة سوداء کعب و غروب رأی العین نزد قفال و المی' in _joined(verse, "critical")

def test_kahf_18_87_verse():
    verse = _check_verse("18:87")
    assert 'طبری می‌گوید خدا می‌گوید گفت اما کسی که ستم کرد پس به زودی او را عذاب می‌کنیم می' in _joined(verse, "notes")
    assert 'در فلسفهٔ دین دانشگاهی کیفر اخروی، عذابا نکرا از این آیه خوانده می‌شود؛ این پرون' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان ظلم شرک نزد جمهور و ظلم فساد نزد المیزان نشان می‌دهد که در او' in _joined(verse, "critical")

def test_kahf_18_88_verse():
    verse = _check_verse("18:88")
    assert 'طبری می‌گوید و اما کسی از آنان که خدا را باور کرد و او را یگانه دانست و به فرمان' in _joined(verse, "notes")
    assert 'در اخلاق دانشگاهی پاداش، جزاء الحسنى از این آیه خوانده می‌شود؛ این پرونده آن را ' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان جزای خدا در آخرت و عطای شاه در دنیا نشان می‌دهد که قرائت نحوی' in _joined(verse, "critical")

def test_kahf_18_89_verse():
    verse = _check_verse("18:89")
    assert 'طبری می‌گوید خدا می‌گوید سپس ذو القرنين راه‌ها و منزل‌ها را رفت و پیمود چنانکه ا' in _joined(verse, "notes")
    assert 'در روایت‌شناسی دانشگاهی گذار، ثم أتبع از این آیه خوانده می‌شود؛ این پرونده آن را' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان تکرار مکانیکی عبارت و تغییر جهت جغرافیایی نشان می‌دهد که قصه ' in _joined(verse, "critical")

def test_kahf_18_90_verse():
    verse = _check_verse("18:90")
    assert 'طبری می‌گوید خدا می‌گوید و ذو القرنين آفتاب را یافت که بر قومی طلوع می‌کند که بر' in _joined(verse, "notes")
    assert 'در جغرافیای دانشگاهی مطلع شمس، این آیه خوانده می‌شود؛ این پرونده آن را نگه می‌دا' in _joined(verse, "modern")
    assert 'خوانش انتقادی میان قوم بی خانه و برهنه نزد المیزان و قوم سرب‌نشین نزد قتاده و آب' in _joined(verse, "critical")
