# -*- coding: utf-8 -*-
"""هر آیهٔ دامنه باید هر فیلد Standard 3 را با وضعیت و پیگیریِ روشن داشته باشد."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
TARGET_VERSES = {f"8:{ayah}" for ayah in range(51, 76)} | {f"9:{ayah}" for ayah in range(1, 93)}


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
    assert "سوره کامل نیست" in scope["9:1–129"]


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
    assert "overlay اکنون تا ۹:۹۲ می‌رسد (۱۱۷ رکورد" in scope["9:1–129"]
    assert "۹:۹۳–۱۲۹ هنوز وارد نشده" in scope["9:1–129"]
    assert "به‌طورِ کامل واردِ overlay شده" in scope["9:32–81"]
    assert "۹:۷۵–۸۱ در سطحِ core" in scope["9:32–81"]
    assert "۹:۴۲–۹۲" in scope["9:42–129"]
    assert "۹:۴۷–۹۲" in scope["9:42–46"]
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
    assert "overlay اکنون تا ۹:۹۲" in scope["9:1–129"]


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
    assert "overlay اکنون تا ۹:۹۲" in scope["9:1–129"]


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
    assert "۹:۹۳ به بعد باقی است" in scope["9:42–46"]
