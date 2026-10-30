# -*- coding: utf-8 -*-
"""اعتبارسنجیِ بستهٔ «کاربست امروز»: شمارش، پوششِ آیه‌ها، ارجاع و مرزِ سوءاستفاده."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = json.loads((ROOT / "static" / "scholar-application.json").read_text(encoding="utf-8"))
BANK = json.loads((ROOT / "static" / "scholar-bank.json").read_text(encoding="utf-8"))
CORPUS = json.loads((ROOT / "static" / "offline-corpus.json").read_text(encoding="utf-8"))["verses"]

REQUIRED = {"field", "text", "basis", "cite", "guard", "anchors"}


def ids():
    return {f"{r[0]}:{r[1]}" for r in CORPUS if isinstance(r, list)}


def seg_ids(segment):
    surah, first = segment[0].split(":")
    _, last = segment[1].split(":")
    return {f"{surah}:{i}" for i in range(int(first), int(last) + 1)}


def declared_ids():
    ids = set()
    for batch in APP["batches"]:
        for segment in batch["segments"]:
            ids |= seg_ids(segment)
    return ids


def test_batches_cover_every_entry_once():
    total = sum(batch["count"] for batch in APP["batches"])
    assert total == len(APP["verses"]), f"جمع بسته‌ها {total} ≠ مدخل‌ها {len(APP['verses'])}"
    assert all(batch["count"] > 0 and batch["status"].strip() for batch in APP["batches"])
    for batch in APP["batches"]:
        covered = set()
        for segment in batch["segments"]:
            covered |= seg_ids(segment)
        assert batch["count"] == len(covered), f"{batch['id']}: شمارش با بازه نمی‌خواند"


def test_batch_ranges_are_exactly_as_declared():
    expected = declared_ids()
    assert set(APP["verses"]) == expected, "بازهٔ بسته‌ها با مدخل‌ها نمی‌خواند"


def iter_uses(v2=None):
    for vid, entry in APP["verses"].items():
        if "uses" in entry:
            for use in entry["uses"]:
                yield vid, use, True
        elif v2 is not True:
            yield vid, entry, False


def test_every_entry_is_complete():
    for vid, entry in APP["verses"].items():
        if "uses" in entry:
            assert entry["uses"], f"{vid}: فهرستِ کاربست خالی است"
            continue
        assert REQUIRED <= set(entry), f"کلید ناقص: {vid}"
        for key in ("field", "text", "basis", "cite", "guard"):
            assert entry[key].strip(), f"{vid}:{key} خالی است"


def test_every_v2_use_carries_text_evidence_citation_and_guard():
    for vid, use, v2 in iter_uses():
        for key in ("field", "text", "basis", "cite", "guard"):
            assert use.get(key, "").strip(), f"{vid}: کاربست بی‌{key}"
        assert len(use["cite"]) > 8, f"ارجاعِ کوتاه: {vid}"
        assert len(use["text"].split()) >= 15, f"کاربستِ بسیار کوتاه: {vid}"
        if v2:
            assert len(use["guard"].split()) >= 8, f"{vid}: مرزِ سوءاستفاده کوتاه است"


def test_historical_verses_keep_four_applications_and_later_surahs_use_five():
    for vid, entry in APP["verses"].items():
        if "uses" in entry:
            surah = int(vid.split(":",1)[0])
            assert len(entry["uses"]) == (5 if surah >= 4 else 4), f"{vid}: شمارِ کاربست‌ها با استانداردِ بازه نمی‌خواند"


def test_revised_batch_has_four_historical_uses_and_five_from_nisa_onward():
    revised = APP["revision"]
    assert revised["standard"] == "v3"
    covered = [vid for vid, entry in APP["verses"].items() if "uses" in entry]
    assert len(covered) == revised["count"] == 1235, f"پوششِ بازنویسی‌شده {len(covered)} ≠ {revised['count']}"
    assert revised["range"] == "۱:۱–۷ و ۲:۱–۲۸۶ و ۳:۱–۲۰۰ و ۴:۱–۱۷۶ و ۵:۱–۱۲۰ و ۶:۱–۱۶۵ و ۷:۱–۲۰۶ و ۸:۱–۷۵"
    assert revised["previousRevision"]["count"] == 1160
    assert revised["previousRevision"]["previousRevision"]["count"] == 954
    for vid, entry in APP["verses"].items():
        if "uses" in entry:
            expected = 5 if int(vid.split(":", 1)[0]) >= 4 else 4
            assert len(entry["uses"]) == expected, f"{vid}: کاربست‌ها با استانداردِ تاریخی/نساءِ این بسته نمی‌خوانند"


def test_use_texts_are_unique_and_fields_vary():
    seen = {}
    for vid, use, _ in iter_uses():
        key = use["text"].strip()
        assert key not in seen, f"تکرارِ کاربست: {vid} و {seen[key]}"
        seen[key] = vid
    fields = {use["field"] for _, use, _ in iter_uses()}
    assert len(fields) >= 20, f"تنوعِ میدان‌ها کم است: {len(fields)}"


def test_no_foreign_script_leaks_into_application_prose():
    import re

    pattern = re.compile(r"[A-Za-z\u0400-\u04FF]+")
    for vid, use, v2 in iter_uses(v2=True):
        for key in ("field", "text", "guard"):
            leaks = pattern.findall(use[key])
            assert not leaks, f"{vid}:{key} واژهٔ غیرفارسی: {leaks}"


def test_method_has_three_gates_and_a_testable_rule():
    method = APP["method"]
    assert len(method["steps"]) == 3
    assert "شرط" in method["rule"]
    assert method["cite"].strip()


def test_fields_cover_more_than_one_domain():
    fields = {use["field"] for _, use, _ in iter_uses()}
    assert len(fields) >= 40, f"تنوعِ میدان‌ها کم است: {len(fields)}"


def test_opening_review_applications_are_quran_study_not_generic_advice():
    reviewed = [f"1:{n}" for n in range(1, 8)] + [f"2:{n}" for n in range(1, 9)]
    unrelated_sources = ("Bourdieu", "Kahneman", "Tufekci", "Gadamer", "Hirsch", "Goldziher", "Nöldeke")
    for verse_id in reviewed:
        uses = APP["verses"][verse_id]["uses"]
        assert len(uses) == 4, verse_id
        for use in uses:
            assert any(source in use["cite"] for source in ("قرآن", "طبری", "قرطبی", "المیزان", "QuranEnc", "Izutsu", "Neuwirth", "Sells", "Sinai", "Rahman")), verse_id
            assert not any(source in use["cite"] for source in unrelated_sources), (verse_id, use["cite"])
    assert "فهم" in APP["notice"] and "قرآن" in APP["notice"]


def test_opening_translation_and_tafsir_tasks_name_source_types_accurately():
    samples = {
        "1:2": APP["verses"]["1:2"]["uses"][3],
        "1:4": APP["verses"]["1:4"]["uses"][3],
        "1:6": APP["verses"]["1:6"]["uses"][0],
        "1:7": APP["verses"]["1:7"]["uses"][2],
        "2:3a": APP["verses"]["2:3"]["uses"][1],
        "2:3b": APP["verses"]["2:3"]["uses"][2],
        "2:5": APP["verses"]["2:5"]["uses"][1],
        "2:6": APP["verses"]["2:6"]["uses"][2],
    }
    assert "سه ترجمهٔ فارسی" not in samples["1:2"]["text"]
    assert "شرحِ عربیِ التفسير الميسر" in samples["1:2"]["text"]
    assert not samples["1:4"]["cite"].lstrip().startswith("و ")
    assert "قرائت‌های" in samples["1:4"]["text"]
    assert "ضمیرِ جمع" in samples["1:6"]["text"]
    assert "مصداق" in samples["1:7"]["text"]
    assert "مِن" in samples["2:3b"]["text"]
    assert "QuranEnc" in samples["2:5"]["cite"] and "نسخهٔ 1.0.0" in samples["2:5"]["cite"]
    assert "دو تفسیرِ معاصر" not in samples["2:6"]["text"]
    assert all("Furqan Apps" in item["cite"] and "قطعهٔ" in item["cite"] for item in samples.values())


def test_baqarah_9_to_286_applications_are_four_source_bound_quran_study_tasks():
    expected_fields = ["واژه‌کاوی و ساخت", "سیاق و پیوند قرآنی", "مقایسهٔ اقوال تفسیری", "تمرین ترجمه و دلالت"]
    tangential_sources = ("Bourdieu", "Kahneman", "Goffman", "Bandura", "Rothstein", "Turkle", "Sunstein")

    corpus_by_id = {f"{row[0]}:{row[1]}": row for row in CORPUS if isinstance(row, list)}
    for ayah in range(9, 287):
        verse_id = f"2:{ayah}"
        uses = APP["verses"][verse_id]["uses"]
        assert len(uses) == 4, verse_id
        assert [use["field"] for use in uses] == expected_fields, verse_id
        verse_text = corpus_by_id[verse_id][2]
        for use in uses:
            assert use["basis"] in verse_text, (verse_id, use["basis"])
            assert use["cite"].strip() and len(use["guard"].split()) >= 8
            assert not any(source in use["cite"] for source in tangential_sources), (verse_id, use["cite"])
        assert any("طبری" in uses[0]["cite"] and "قرطبی" in uses[0]["cite"] for _ in (0,))
        assert "قرآن" in uses[1]["cite"]
        assert "QuranEnc" in uses[3]["cite"]


def test_al_imran_3_1_to_200_has_exactly_four_source_bound_study_uses():
    expected_fields = ["واژه‌کاوی و ساخت", "سیاق و پیوند قرآنی", "مقایسهٔ اقوال تفسیری", "تمرین ترجمه و دلالت"]
    corpus_by_id = {f"{row[0]}:{row[1]}": row for row in CORPUS if isinstance(row, list)}
    batch = next(batch for batch in APP["batches"] if batch["id"] == "batch-9")
    assert batch["segments"] == [["3:1", "3:200"]]
    assert batch["count"] == 200
    assert APP["revision"]["count"] == 1235
    assert "۳:۱–۲۰۰" in APP["revision"]["ranges"]

    for ayah in range(1, 201):
        verse_id = f"3:{ayah}"
        uses = APP["verses"][verse_id]["uses"]
        assert len(uses) == 4, verse_id
        assert [use["field"] for use in uses] == expected_fields, verse_id
        verse_text = corpus_by_id[verse_id][2]
        for use in uses:
            assert use["basis"] in verse_text, (verse_id, use["basis"])
            assert use["cite"].strip() and len(use["guard"].split()) >= 8
        assert "طبری" in uses[0]["cite"] and "قرطبی" in uses[0]["cite"]
        assert "قرآن" in uses[1]["cite"]
        assert "التفسير الميسر" in uses[2]["cite"] and "QuranEnc" in uses[2]["cite"]
        assert "fa.fooladvand" in uses[3]["cite"] and "Tanzil" in uses[3]["cite"]
        assert "اجماع" not in uses[1]["text"]


def test_nisa_4_1_to_176_has_five_source_bound_study_uses():
    expected_fields = ["واژه‌کاوی و ساخت", "سیاق و پیوند قرآنی", "مقایسهٔ اقوال تفسیری", "تمرین ترجمه و دلالت", "آزمون میان‌رشته‌ای و مرزِ کاربرد"]
    corpus_by_id = {f"{row[0]}:{row[1]}": row for row in CORPUS if isinstance(row, list)}
    batch = next(batch for batch in APP["batches"] if batch["id"] == "batch-10")
    assert batch["segments"] == [["4:1", "4:176"]]
    assert batch["count"] == 176
    for ayah in range(1, 177):
        verse_id = f"4:{ayah}"
        uses = APP["verses"][verse_id]["uses"]
        assert len(uses) == 5, verse_id
        assert [use["field"] for use in uses] == expected_fields, verse_id
        verse_text = corpus_by_id[verse_id][2]
        for use in uses:
            assert use["basis"] in verse_text, (verse_id, use["basis"])
            assert use["cite"].strip() and len(use["text"].split()) >= 15 and len(use["guard"].split()) >= 8, verse_id
        assert "طبری" in uses[0]["cite"] and "قرطبی" in uses[0]["cite"]
        assert "قرآن" in uses[1]["cite"]
        assert "التفسير الميسر" in uses[2]["cite"]
        assert "fa.fooladvand" in uses[3]["cite"] and "Tanzil" in uses[3]["cite"]
        assert "اجماع" not in uses[1]["text"]



def test_maida_5_1_to_120_has_five_source_bound_study_uses():
    expected_fields = ["واژه‌کاوی و ساخت", "سیاق و پیوند قرآنی", "مقایسهٔ اقوال تفسیری", "تمرین ترجمه و دلالت", "آزمون میان‌رشته‌ای و مرزِ کاربرد"]
    corpus_by_id = {f"{row[0]}:{row[1]}": row for row in CORPUS if isinstance(row, list)}
    batch = next(batch for batch in APP["batches"] if batch["id"] == "batch-11")
    assert batch["segments"] == [["5:1", "5:120"]]
    assert batch["count"] == 120
    assert APP["revision"]["count"] == 1235
    assert "۵:۱–۱۲۰" in APP["revision"]["ranges"]
    for ayah in range(1, 121):
        verse_id = f"5:{ayah}"
        uses = APP["verses"][verse_id]["uses"]
        assert len(uses) == 5, verse_id
        assert [use["field"] for use in uses] == expected_fields, verse_id
        verse_text = corpus_by_id[verse_id][2]
        for use in uses:
            assert use["basis"] in verse_text, (verse_id, use["basis"])
            assert use["cite"].strip() and len(use["text"].split()) >= 15 and len(use["guard"].split()) >= 8, verse_id
        assert "طبری" in uses[0]["cite"] and "قرطبی" in uses[0]["cite"]
        assert "قرآن" in uses[1]["cite"]
        assert "التفسير الميسر" in uses[2]["cite"]
        assert "fa.fooladvand" in uses[3]["cite"] and "Tanzil" in uses[3]["cite"]
        assert "اجماع" not in uses[1]["text"]
    missing_record = APP["verses"]["5:36"]["uses"][2]
    assert "تهی از تفسیر" in missing_record["text"]
    assert "لا يوجد تفسير" in missing_record["cite"]


def test_al_anam_6_1_to_165_has_five_source_bound_study_uses():
    expected_fields = ["واژه‌کاوی و ساخت", "سیاق و پیوند قرآنی", "مقایسهٔ اقوال تفسیری", "تمرین ترجمه و دلالت", "آزمون میان‌رشته‌ای و مرزِ کاربرد"]
    corpus_by_id = {f"{row[0]}:{row[1]}": row for row in CORPUS if isinstance(row, list)}
    batch = next(batch for batch in APP["batches"] if batch["id"] == "batch-12")
    assert batch["segments"] == [["6:1", "6:165"]]
    assert batch["count"] == 165
    assert APP["revision"]["count"] == 1235
    assert "۶:۱–۱۶۵" in APP["revision"]["ranges"]
    assert APP["revision"]["previousRevision"]["count"] == 1160
    assert "resolution 70/186" in APP["verses"]["6:152"]["uses"][4]["cite"]
    assert "para. 32" in APP["verses"]["6:152"]["uses"][4]["cite"]
    assert "بندِ ۳۲" in APP["verses"]["6:152"]["uses"][4]["guard"]
    for ayah in range(1, 166):
        verse_id = f"6:{ayah}"
        uses = APP["verses"][verse_id]["uses"]
        assert len(uses) == 5, verse_id
        assert [use["field"] for use in uses] == expected_fields, verse_id
        verse_text = corpus_by_id[verse_id][2]
        for use in uses:
            assert use["basis"] in verse_text, (verse_id, use["basis"])
            assert use["cite"].strip() and len(use["text"].split()) >= 15 and len(use["guard"].split()) >= 8, verse_id
        assert "طبری" in uses[0]["cite"] and "قرطبی" in uses[0]["cite"]
        assert "قرآن" in uses[1]["cite"]
        assert "التفسير الميسر" in uses[2]["cite"]
        assert "fa.fooladvand" in uses[3]["cite"] and "Tanzil" in uses[3]["cite"]
        assert "اجماع" not in uses[1]["text"]


def test_araf_7_1_to_206_has_five_source_bound_applications():
    expected_fields = ["واژه‌کاوی و ساخت", "سیاق و پیوند قرآنی", "مقایسهٔ اقوال تفسیری", "تمرین ترجمه و دلالت", "آزمون میان‌رشته‌ای و مرزِ کاربرد"]
    corpus_by_id = {f"{row[0]}:{row[1]}": row for row in CORPUS if isinstance(row, list)}
    batch = next(batch for batch in APP["batches"] if batch["id"] == "batch-13")
    assert batch["segments"] == [["7:1", "7:206"]] and batch["count"] == 206
    assert APP["revision"]["count"] == 1235
    assert "۷:۱–۲۰۶" in APP["revision"]["ranges"]
    for ayah in range(1, 207):
        verse_id = f"7:{ayah}"
        uses = APP["verses"][verse_id]["uses"]
        assert len(uses) == 5 and [use["field"] for use in uses] == expected_fields, verse_id
        for use in uses:
            assert use["basis"] in corpus_by_id[verse_id][2], (verse_id, use["basis"])
            assert use["cite"].strip() and len(use["guard"].split()) >= 8, verse_id
    for ayah in (96, 97, 98, 120):
        uses = APP["verses"][f"7:{ayah}"]["uses"]
        assert "رکوردِ طبری شرحِ جداگانه ندارد" in uses[0]["text"]
        assert "رکوردِ طبری شرحِ جداگانه ندارد" in uses[2]["text"]


def test_anfal_8_1_to_75_has_five_source_bound_applications():
    expected_fields = ["واژه‌کاوی و ساخت", "سیاق و پیوند قرآنی", "مقایسهٔ اقوال تفسیری", "تمرین ترجمه و دلالت", "آزمون میان‌رشته‌ای و مرزِ کاربرد"]
    corpus_by_id = {f"{row[0]}:{row[1]}": row for row in CORPUS if isinstance(row, list)}
    batch = next(batch for batch in APP["batches"] if batch["id"] == "batch-14")
    assert batch["segments"] == [["8:1", "8:75"]] and batch["count"] == 75
    assert APP["revision"]["count"] == 1235
    assert "۸:۱–۷۵" in APP["revision"]["ranges"]
    for ayah in range(1, 76):
        verse_id = f"8:{ayah}"
        uses = APP["verses"][verse_id]["uses"]
        assert len(uses) == 5 and [use["field"] for use in uses] == expected_fields, verse_id
        for use in uses:
            assert use["basis"] in corpus_by_id[verse_id][2], (verse_id, use["basis"])
            assert use["cite"].strip() and len(use["guard"].split()) >= 8, verse_id
