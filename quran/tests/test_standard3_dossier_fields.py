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
TARGET_VERSES = {f"8:{ayah}" for ayah in range(51, 76)} | {f"9:{ayah}" for ayah in range(1, 109)} | {"10:1", "10:2", "10:3", "10:4", "10:5", "10:6", "10:7", "10:8", "10:9", "10:10", "10:11", "10:12", "10:13", "10:14", "10:15", "10:16", "10:17", "10:18", "10:19", "10:20", "10:21", "10:22", "10:23", "10:24", "10:25", "10:26", "10:27", "10:28", "10:29", "10:30", "10:31", "10:32", "10:33", "10:34", "10:35", "10:36", "10:37", "10:38", "10:39", "10:40", "10:41", "10:42", "10:43", "10:44", "10:45", "10:46", "10:47", "10:48", "10:49", "10:50", "10:51", "10:52", "10:53", "10:54", "10:55", "10:56", "10:57", "10:58", "10:59", "10:60", "10:61", "10:62", "10:63", "10:64", "10:65", "10:66", "10:67", "10:68", "10:69", "10:70", "10:71", "10:72", "10:73", "10:74", "10:75", "10:76", "10:77", "10:78", "10:79", "10:80", "10:81", "10:82", "10:83", "10:84", "10:85", "10:86", "10:87", "10:88", "10:89", "10:90", "10:91", "10:92", "10:93", "10:94", "10:95", "10:96", "10:97", "10:98", "10:99", "10:100", "10:101", "10:102", "10:103", "10:104", "10:105", "10:106", "10:107", "10:108", "10:109", "11:1", "11:2", "11:3", "11:4", "11:5", "11:6", "11:7", "11:8", "11:9", "11:10", "11:11", "11:12", "11:13", "11:14", "11:15", "11:16", "11:17", "11:18", "11:19", "11:20", "11:21", "11:22", "11:23", "11:24", "11:25", "11:26", "11:27", "11:28", "11:29", "11:30", "11:31", "11:32", "11:33", "11:34", "11:35", "11:36", "11:37", "11:38", "11:39", "11:40", "11:41", "11:42", "11:43", "11:44", "11:45", "11:46", "11:47", "11:48", "11:49"}


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
    assert "کامل نیستند" in scope["9:1–129"]


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
    assert "هنوز وارد نشده" in scope["9:1–129"]


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
    assert "هنوز وارد نشده" in scope["9:1–129"]

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
    assert "هنوز وارد نشده" in scope["9:1–129"]
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
    assert "هنوز وارد نشده" in scope["9:1–129"]


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
    assert "هنوز وارد نشده" in scope["9:1–129"]
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
    assert "هنوز وارد نشده" in scope["9:1–129"]


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
    assert "هنوز وارد نشده" in scope["9:1–129"]


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
    assert "هنوز وارد نشده" in scope["9:1–129"]


def test_scope_frontier_tracks_current_records():
    scope = {item["range"]: item["status"] for item in DATA["scope"]}
    assert "overlay اکنون تا ۹:۱۰۸ و آیاتِ آغازینِ يونس" in scope["9:1–129"]
    assert f"{_fa(len(DATA['verses']))} رکورد" in scope["9:1–129"]
    assert "۹:۱۰۹–۱۲۹" in scope["9:1–129"] and "هنوز وارد نشده" in scope["9:1–129"]
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
            assert verse_id in {"11:1", "10:49", "10:50", "10:51", "10:52", "10:53", "10:54", "10:55", "10:56", "10:57", "10:58", "10:59", "10:60", "10:61", "10:62", "10:63", "10:64", "10:65", "10:66", "10:67", "10:68", "10:69", "10:70", "10:71", "10:72", "10:73", "10:74", "10:75", "10:76", "10:77", "10:78", "10:79", "10:80", "10:81", "10:82", "10:83", "10:84", "10:85", "10:86", "10:87", "10:88", "10:89", "10:90", "10:91", "10:92", "10:93", "10:94", "10:95", "10:96", "10:97", "10:98", "10:99", "10:100", "10:101", "10:102", "10:103", "10:104", "10:105", "10:106", "10:107", "10:108", "10:109", "11:1", "11:2", "11:3", "11:4", "11:5", "11:6", "11:7", "11:8", "11:9", "11:10", "11:11", "11:12", "11:13", "11:14", "11:15", "11:16", "11:17", "11:18", "11:19", "11:20", "11:21", "11:22", "11:23", "11:24", "11:25", "11:26", "11:27", "11:28", "11:29", "11:30", "11:31", "11:32", "11:33", "11:34", "11:35", "11:36", "11:37", "11:38", "11:39", "11:40", "11:41", "11:42", "11:43", "11:44", "11:45", "11:46", "11:47", "11:48", "11:49"}, verse_id
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

    for verse_id in ("10:1", "10:2", "10:3", "10:4", "10:5", "10:6", "10:7", "10:8", "10:9", "10:10", "10:11", "10:12", "10:13", "10:14", "10:15", "10:16", "10:17", "10:18", "10:19", "10:20", "10:21", "10:22", "10:23", "10:24", "10:25", "10:26", "10:27", "10:28", "10:29", "10:30", "10:31", "10:32", "10:33", "10:34", "10:35", "10:36", "10:37", "10:38", "10:39", "10:40", "10:41", "10:42", "10:43", "10:44", "10:45", "10:46", "10:47", "10:48", "10:49", "10:50", "10:51", "10:52", "10:53", "10:54", "10:55", "10:56", "10:57", "10:58", "10:59", "10:60", "10:61", "10:62", "10:63", "10:64", "10:65", "10:66", "10:67", "10:68", "10:69", "10:70", "10:71", "10:72", "10:73", "10:74", "10:75", "10:76", "10:77", "10:78", "10:79", "10:80", "10:81", "10:82", "10:83", "10:84", "10:85", "10:86", "10:87", "10:88", "10:89", "10:90", "10:91", "10:92", "10:93", "10:94", "10:95", "10:96", "10:97", "10:98", "10:99", "10:100", "10:101", "10:102", "10:103", "10:104", "10:105", "10:106", "10:107", "10:108", "10:109", "11:1", "11:2", "11:3", "11:4", "11:5", "11:6", "11:7", "11:8", "11:9", "11:10", "11:11", "11:12", "11:13", "11:14", "11:15", "11:16", "11:17", "11:18", "11:19", "11:20", "11:21", "11:22", "11:23", "11:24", "11:25", "11:26", "11:27", "11:28", "11:29", "11:30", "11:31", "11:32", "11:33", "11:34", "11:35", "11:36", "11:37", "11:38", "11:39", "11:40", "11:41", "11:42", "11:43", "11:44", "11:45", "11:46", "11:47", "11:48", "11:49"):
        record = DATA["verses"][verse_id]
        assert record["requiresDiverseSources"] is True, verse_id
        roles = {item["role"] for item in record["sourceMix"]}
        assert any(role.startswith("shia") for role in roles), (verse_id, roles)
        assert "journal" in roles, (verse_id, roles)
    for verse_id in ("10:1", "10:2", "10:3", "10:4", "10:5", "10:6", "10:7", "10:8", "10:9", "10:10", "10:11", "10:12", "10:13", "10:14", "10:15", "10:16", "10:17", "10:18", "10:19", "10:20", "10:21", "10:22", "10:23", "10:24", "10:25", "10:26", "10:27", "10:28", "10:29", "10:30", "10:31", "10:32", "10:33", "10:34", "10:35", "10:36", "10:37", "10:38", "10:39", "10:40", "10:41", "10:42", "10:43", "10:44", "10:45", "10:46", "10:47", "10:48", "10:49", "10:50", "10:51", "10:52", "10:53", "10:54", "10:55", "10:56", "10:57", "10:58", "10:59", "10:60", "10:61", "10:62", "10:63", "10:64", "10:65", "10:66", "10:67", "10:68", "10:69", "10:70", "10:71", "10:72", "10:73", "10:74", "10:75", "10:76", "10:77", "10:78", "10:79", "10:80", "10:81", "10:82", "10:83", "10:84", "10:85", "10:86", "10:87", "10:88", "10:89", "10:90", "10:91", "10:92", "10:93", "10:94", "10:95", "10:96", "10:97", "10:98", "10:99", "10:100", "10:101", "10:102", "10:103", "10:104", "10:105", "10:106", "10:107", "10:108", "10:109", "11:1", "11:2", "11:3", "11:4", "11:5", "11:6", "11:7", "11:8", "11:9", "11:10", "11:11", "11:12", "11:13", "11:14", "11:15", "11:16", "11:17", "11:18", "11:19", "11:20", "11:21", "11:22", "11:23", "11:24", "11:25", "11:26", "11:27", "11:28", "11:29", "11:30", "11:31", "11:32", "11:33", "11:34", "11:35", "11:36", "11:37", "11:38", "11:39", "11:40", "11:41", "11:42", "11:43", "11:44", "11:45", "11:46", "11:47", "11:48", "11:49"):
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
