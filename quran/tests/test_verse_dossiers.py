# -*- coding: utf-8 -*-
"""اعتبارسنجیِ پروندهٔ آیه: پوششِ بسته‌ها، کامل‌بودنِ فیلدها، ارجاع و نبودِ تکرار."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = json.loads((ROOT / "static" / "verse-dossiers.json").read_text(encoding="utf-8"))
CORPUS = json.loads((ROOT / "static" / "offline-corpus.json").read_text(encoding="utf-8"))["verses"]

FIELDS = ("notes", "context", "classical", "modern", "critical", "research")
CLASSICAL_MARK = "ق،"
MIN_WORDS = 14


def verse_ids():
    return {f"{r[0]}:{r[1]}" for r in CORPUS if isinstance(r, list)}


def entries():
    return DOSSIER["verses"].items()


def find_revision(revision, target_range):
    while isinstance(revision, dict):
        if revision.get("range") == target_range:
            return revision
        revision = revision.get("previousRevision")
    return None


def test_editorial_method_and_batches_are_declared():
    assert DOSSIER["editorialMethod"].strip()
    assert DOSSIER["batches"], "بستهٔ پرونده ثبت نشده است"
    total = sum(batch["count"] for batch in DOSSIER["batches"])
    assert total == len(DOSSIER["verses"]), f"جمع بسته‌ها {total} ≠ مدخل‌ها {len(DOSSIER['verses'])}"
    assert all(batch["status"].strip() for batch in DOSSIER["batches"])


def test_every_verse_exists_in_corpus():
    unknown = set(DOSSIER["verses"]) - verse_ids()
    assert not unknown, f"آیهٔ ناموجود: {sorted(unknown)}"


def test_every_entry_has_all_fields_with_text_and_citation():
    for vid, entry in entries():
        assert entry.get("title", "").strip(), f"{vid}: عنوان خالی است"
        for field in FIELDS:
            items = entry.get(field)
            assert isinstance(items, list) and items, f"{vid}:{field} خالی است"
            for item in items:
                assert item.get("text", "").strip(), f"{vid}:{field} متن ندارد"
                assert len(item["text"].split()) >= MIN_WORDS, f"{vid}:{field} بندِ کوتاه"
                assert item.get("cite", "").strip(), f"{vid}:{field} ارجاع ندارد"


def test_each_verse_mixes_classical_and_modern_scholarship():
    for vid, entry in entries():
        cites = [item["cite"] for field in FIELDS for item in entry[field]]
        assert any(CLASSICAL_MARK in cite or "ق،" in cite for cite in cites), f"{vid}: ارجاعِ کهن ندارد"
        assert any("ق،" not in cite for cite in cites), f"{vid}: ارجاعِ معاصر ندارد"


def test_classical_and_modern_fields_are_independently_sourced():
    """خوانش‌های کهن و متن‌های معاصر باید مستقل و نسخه‌دار ارجاع شوند."""
    for vid, entry in entries():
        assert len(entry["classical"]) >= 2, f"{vid}: خوانش کهن کم است"
        if vid.startswith("3:"):
            # برای آل‌عمران فقط برشِ مستقیم و موضع‌دارِ المیزان در کنارِ المیسر افزوده می‌شود؛
            # نبودِ برشِ مستقیم نباید با نقلِ نامرتبط پُر شود.
            assert 1 <= len(entry["modern"]) <= 5, f"{vid}: شمارِ متن‌های معاصر نامعتبر است"
        else:
            assert 2 <= len(entry["modern"]) <= 5, f"{vid}: پژوهش معاصر کم است"
        for item in entry["classical"]:
            assert "ق،" in item["cite"] or "Izutsu" in item["cite"], f"{vid}: خوانش کهن ارجاعِ کهن ندارد"
        for item in entry["modern"]:
            cite = item["cite"]
            has_publication_marker = any(token in cite for token in ("ق،", "، ۱۳", "، ۱۴", ", 19", ", 20", "resolution 2200A", "resolution 44/25", "resolution 70/186"))
            has_versioned_local_source = (
                "QuranEnc" in cite and "نسخهٔ 1.0.0" in cite and "ذیل" in cite
            ) or ("Furqan 2026.0" in cite and "ذیل" in cite) or (
                "Furqan Apps" in cite and "نسخهٔ 2026.0" in cite and "قطعهٔ" in cite and "موضعِ" in cite
            )
            assert has_publication_marker or has_versioned_local_source, (
                f"{vid}: ارجاعِ معاصر مشخص نیست"
            )


def test_no_foreign_script_leaks_into_persian_text():
    import re

    pattern = re.compile(r"[A-Za-zÀ-ÿ]+")
    allowed = {"Izutsu", "Neuwirth", "Hirsch", "Gadamer", "Kahneman", "Nickerson", "Hart", "Motzki", "Nöldeke"}
    for vid, entry in entries():
        for field in FIELDS:
            for item in entry[field]:
                prose = re.sub(r"«[^»]*»", "", item["text"])  # واژهٔ خارجیِ نقل‌شده مجاز است
                leaks = set(pattern.findall(prose)) - allowed
                assert not leaks, f"{vid}:{field} واژهٔ غیرفارسی در متن: {leaks}"


def test_critical_reading_is_substantive():
    for vid, entry in entries():
        assert len(entry["critical"]) >= 3, f"{vid}: خوانش انتقادی کم‌تر از سه بند است"
        joined = " ".join(item["text"] for item in entry["critical"])
        assert any(word in joined for word in ("خطر", "پرسش", "نقد", "خطای خوانش", "تبار")), f"{vid}: بندِ انتقادی جهت ندارد"


def test_no_text_is_repeated_across_fields_or_verses():
    seen = {}
    for vid, entry in entries():
        for field in FIELDS:
            for item in entry[field]:
                key = item["text"].strip()
                assert key not in seen, f"تکرارِ متن: {vid}:{field} و {seen[key]}"
                seen[key] = f"{vid}:{field}"


def test_citations_do_not_claim_unverified_pagination():
    """ارجاعِ کهن باید موضع داشته باشد؛ ارجاعِ معاصر صفحه یا اثرِ مشخص."""
    for vid, entry in entries():
        for field in FIELDS:
            for item in entry[field]:
                cite = item["cite"]
                assert "*" in cite or any(ch.isdigit() for ch in cite), f"{vid}:{field} ارجاعِ بی‌مشخص"


def test_baqarah_2_282_uses_versioned_tafsir_sources_without_unverified_pages():
    entry = DOSSIER["verses"]["2:282"]
    modern = [item["cite"] for item in entry["modern"]]
    classical = [item["cite"] for item in entry["classical"]]
    assert len(modern) == 2
    assert any("Furqan Apps" in cite and "نسخهٔ 2026.0" in cite and "قطعهٔ 72" in cite and "بقره ۲:۲۸۲" in cite for cite in modern)
    assert any("QuranEnc" in cite and "نسخهٔ 1.0.0" in cite and "التفسير الميسر" in cite and "بقره ۲:۲۸۲" in cite for cite in modern)
    assert len(set(modern)) == 2
    assert any("طبری" in cite and "ذیل بقره ۲:۲۸۲" in cite for cite in classical)
    assert any("قرطبی" in cite and "ذیل بقره ۲:۲۸۲" in cite for cite in classical)
    assert all("صص." not in cite and "ص." not in cite for cite in modern + classical)


def test_baqarah_9_to_286_has_primary_classical_and_versioned_modern_sources():
    for ayah in range(9, 287):
        verse_id = f"2:{ayah}"
        entry = DOSSIER["verses"][verse_id]
        assert 4 <= len(entry["notes"]) <= 5, verse_id
        assert len(entry["classical"]) == 2, verse_id
        assert 2 <= len(entry["modern"]) <= 5, verse_id
        assert len(entry["critical"]) == 3, verse_id
        assert 4 <= len(entry["research"]) <= 5, verse_id
        classical = [item["cite"] for item in entry["classical"]]
        modern = [item["cite"] for item in entry["modern"]]
        assert any("طبری" in cite and "ذیل بقره" in cite for cite in classical), verse_id
        assert any("قرطبی" in cite and "ذیل بقره" in cite for cite in classical), verse_id
        assert any("Furqan Apps" in cite and "نسخهٔ 2026.0" in cite and "بقره" in cite and "قطعهٔ" in cite for cite in modern), verse_id
        assert any("QuranEnc" in cite and "نسخهٔ 1.0.0" in cite and "ذیل بقره" in cite and "التفسير الميسر" in cite for cite in modern), verse_id
        assert len(set(modern)) == 2, verse_id
        assert all(item["cite"].strip() for item in entry["research"]), verse_id
        assert all(any(term in item["text"] for term in ("خطر", "پرسش", "نقد")) for item in entry["critical"]), verse_id


def test_baqarah_notes_and_context_keep_cross_domain_claims_tied_to_the_text():
    b = DOSSIER["verses"]
    assert "انگیزهٔ سیاسی" not in b["2:14"]["notes"][3]["text"]
    assert "بازارِ سیاست" not in b["2:16"]["notes"][4]["text"]
    assert "روان‌شناختی" not in b["2:19"]["notes"][4]["text"]
    assert "سیاستِ حمایت" not in b["2:220"]["notes"][0]["text"]
    assert "دو اقتصادِ روانی" not in b["2:268"]["notes"][2]["text"]
    assert "شبکه‌های حمایتی" not in b["2:270"]["notes"][2]["text"]
    assert "سلامتِ اقتصادی" not in b["2:188"]["context"][0]["text"]
    assert "تعبیرِ تجارت" in b["2:16"]["context"][0]["text"]
    assert "مقابلهٔ کاملِ همهٔ ادعاها" in DOSSIER["revision"]["caveat"]


def test_fatiha_1_1_qualifies_the_report_about_al_rahman():
    text = DOSSIER["verses"]["1:1"]["critical"][1]["text"]
    assert "گروهی" in text
    assert "ناآشناییِ همگانی" in text
    assert "فرقان ۲۵:۶۰" in DOSSIER["verses"]["1:1"]["critical"][1]["cite"]


def test_tabaris_preference_on_baqarah_disjoint_letters_is_reported():
    item = DOSSIER["verses"]["2:1"]["classical"][0]
    assert "طبری" in item["cite"]
    assert "الصواب عندي" in item["text"]
    assert "بی‌طرفِ محض" in item["text"]


def test_opening_dossiers_respect_the_item_count_limits():
    for verse_id in ("1:1", "2:1"):
        entry = DOSSIER["verses"][verse_id]
        assert 4 <= len(entry["notes"]) <= 5, verse_id
        assert 4 <= len(entry["modern"]) <= 5, verse_id
        assert 4 <= len(entry["research"]) <= 5, verse_id


def test_plural_and_passive_forms_are_not_given_unstated_social_intent():
    plural = DOSSIER["verses"]["1:5"]["notes"][2]["text"]
    passive = DOSSIER["verses"]["1:7"]["notes"][1]["text"]
    assert "به‌تنهایی" in plural and "حضور در جماعت" in plural
    assert "نمی‌توان" in passive and "قصدِ جلوگیری" in passive


def test_baqarah_2_4_keeps_the_imperfect_verb_analysis_accurate():
    text = DOSSIER["verses"]["2:4"]["notes"][2]["text"]
    assert "۲:۴ نیز دو فعلِ مضارع دارد" in text
    assert "نه تغییرِ زمان یا ساختِ فعل" in text


def test_tabari_2_7_preference_is_reported_with_its_scope():
    text = DOSSIER["verses"]["2:7"]["classical"][0]["text"]
    assert "طبری" in text
    assert "ترجیح می‌دهد" in text
    assert "در هر مسئله جداگانه" in text


def test_opening_review_batch_has_four_source_bound_studies_and_questions():
    verse_ids = [f"1:{n}" for n in range(1, 8)] + [f"2:{n}" for n in range(1, 9)]
    for verse_id in verse_ids:
        entry = DOSSIER["verses"][verse_id]
        assert len(entry["modern"]) == 4, verse_id
        assert len(entry["research"]) == 4, verse_id
        mizan_quotes = [item for item in entry["modern"] if item.get("sourceId") == "fa_mizan_furqan"]
        assert len(mizan_quotes) == 1, verse_id
        assert mizan_quotes[0].get("sourceRecordId") and mizan_quotes[0].get("referenceRange"), verse_id
        assert "2026.0" in mizan_quotes[0]["cite"], verse_id
        assert all(item["cite"].strip() and ("ذیل" in item["cite"] or "قرآن،" in item["cite"]) for item in entry["research"]), verse_id
        assert len(entry["critical"]) >= 3, verse_id
    method = DOSSIER["editorialMethod"]
    assert "عنوان و کارکردِ فیلد" in method
    assert "تناسبِ محتوایی" in method


def test_al_imran_3_1_to_200_has_source_bound_comprehensive_dossiers():
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-28")
    assert batch["range"] == "3:1–200" and batch["count"] == 200
    al_imran_revision = find_revision(DOSSIER["revision"], "3:1–3:200")
    assert al_imran_revision and al_imran_revision["count"] == 200
    for ayah in range(1, 201):
        verse_id = f"3:{ayah}"
        entry = DOSSIER["verses"][verse_id]
        assert 4 <= len(entry["notes"]) <= 5, verse_id
        assert len(entry["context"]) == 2, verse_id
        assert len(entry["classical"]) == 2, verse_id
        assert 1 <= len(entry["modern"]) <= 5, verse_id
        assert len(entry["critical"]) == 3, verse_id
        assert 4 <= len(entry["research"]) <= 5, verse_id
        assert entry["reviewStatus"].startswith("پیش‌نویس"), verse_id
        assert {item["sourceId"] for item in entry["classical"]} == {
            "ar_tabari_qurancom", "ar_qurtubi_qurancom"
        }, verse_id
        assert all(f"آل‌عمران ۳:{str(ayah).translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))}" in item["cite"]
                   for item in entry["classical"]), verse_id
        assert any(item.get("sourceId") == "ar_qe_arabic_moyassar"
                   and "نسخهٔ 1.0.0" in item["cite"] for item in entry["modern"]), verse_id
        for item in entry["modern"]:
            if item.get("sourceId") == "fa_mizan_furqan":
                assert item.get("sourceRecordId") and item.get("referenceRange"), verse_id
                assert "نسخهٔ 2026.0" in item["cite"] and "قطعهٔ" in item["cite"], verse_id
                assert item.get("sourceExcerptTruncated") in (True, False), verse_id


def test_nisa_4_1_to_176_has_five_source_bound_items_in_every_dossier_field():
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-29")
    assert batch["range"] == "4:1–176" and batch["count"] == 176
    nisa_revision = find_revision(DOSSIER["revision"], "4:1–4:176")
    assert nisa_revision and nisa_revision["count"] == 176
    mizan_count = 0
    for ayah in range(1, 177):
        verse_id = f"4:{ayah}"
        entry = DOSSIER["verses"][verse_id]
        for field in FIELDS:
            assert len(entry[field]) == 5, f"{verse_id}:{field}"
        assert entry["reviewStatus"].startswith("پیش‌نویس"), verse_id
        assert [item["sourceId"] for item in entry["classical"]].count("ar_tabari_qurancom") == 3, verse_id
        assert [item["sourceId"] for item in entry["classical"]].count("ar_qurtubi_qurancom") == 2, verse_id
        assert all("Quran.com API v4" in item["cite"] and "نسخهٔ 1.1" in item["cite"] for item in entry["classical"])
        assert any(item.get("sourceId") == "ar_qe_arabic_moyassar" and "نسخهٔ 1.0.0" in item["cite"] for item in entry["modern"]), verse_id
        mizan_quotes = [item for item in entry["modern"] if item.get("sourceId") == "fa_mizan_furqan"]
        assert len(mizan_quotes) <= 1, verse_id
        if mizan_quotes:
            mizan_count += 1
            item = mizan_quotes[0]
            assert item.get("sourceRecordId") and item.get("referenceRange"), verse_id
            assert "نسخهٔ 2026.0" in item["cite"] and "قطعهٔ" in item["cite"] and "موضعِ" in item["cite"], verse_id
            assert item.get("sourceExcerptTruncated") in (True, False), verse_id
        assert all(item["cite"].strip() and "ص." not in item["cite"] and "صص." not in item["cite"]
                   for field in FIELDS for item in entry[field]), verse_id
    assert mizan_count == 152


def test_maida_5_1_to_120_has_five_cited_items_and_only_direct_mizan_quotes():
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-30")
    assert batch["range"] == "5:1–120" and batch["count"] == 120
    maida_revision = find_revision(DOSSIER["revision"], "5:1–5:120")
    assert maida_revision and maida_revision["count"] == 120
    mizan_count = 0
    for ayah in range(1, 121):
        verse_id = f"5:{ayah}"
        entry = DOSSIER["verses"][verse_id]
        for field in FIELDS:
            assert len(entry[field]) == 5, f"{verse_id}:{field}"
            assert all(item["cite"].strip() and "ص." not in item["cite"] and "صص." not in item["cite"] for item in entry[field])
        assert [item["sourceId"] for item in entry["classical"]].count("ar_tabari_qurancom") == (4 if ayah == 36 else 3), verse_id
        assert [item["sourceId"] for item in entry["classical"]].count("ar_qurtubi_qurancom") == (1 if ayah == 36 else 2), verse_id
        assert all("Quran.com API v4" in item["cite"] and "نسخهٔ 1.1" in item["cite"] for item in entry["classical"])
        assert len(entry["modern"]) == 5, verse_id
        assert any(item.get("sourceId") == "ar_qe_arabic_moyassar" and "نسخهٔ 1.0.0" in item["cite"] for item in entry["modern"]), verse_id
        mizan_quotes = [item for item in entry["modern"] if item.get("sourceId") == "fa_mizan_furqan"]
        assert len(mizan_quotes) <= 1, verse_id
        if mizan_quotes:
            mizan_count += 1
            item = mizan_quotes[0]
            assert item.get("sourceRecordId") and item.get("referenceRange"), verse_id
            assert "نسخهٔ 2026.0" in item["cite"] and "قطعهٔ" in item["cite"] and "موضعِ" in item["cite"], verse_id
            assert item.get("sourceExcerptTruncated") in (True, False), verse_id
    assert mizan_count == 109
    missing = DOSSIER["verses"]["5:36"]["classical"][-1]
    assert "لا يوجد تفسير" in missing["text"]
    assert "هیچ دیدگاهی از قرطبی به آیه نسبت نمی‌دهد" in missing["text"]
    assert "قرطبی" in missing["cite"]


def test_al_anam_6_1_to_165_has_five_cited_items_and_only_direct_mizan_quotes():
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-31")
    assert batch["range"] == "6:1–165" and batch["count"] == 165
    anam_revision = find_revision(DOSSIER["revision"], "6:1–6:165")
    assert anam_revision and anam_revision["count"] == 165
    assert DOSSIER["revision"]["range"] == "9:1–9:129"
    assert DOSSIER["revision"]["count"] == 129
    assert DOSSIER["revision"]["previousRevision"]["range"] == "8:1–8:75"
    assert DOSSIER["revision"]["previousRevision"]["count"] == 75
    assert DOSSIER["revision"]["previousRevision"]["previousRevision"]["range"] == "7:1–7:206"
    assert DOSSIER["revision"]["previousRevision"]["previousRevision"]["count"] == 206
    assert anam_revision["previousRevision"]["count"] == 120
    no_direct_mizan = {4, 10, 11, 32, 42, 48, 49, 55, 78, 85, 87, 92, 97, 101, 105, 106, 111, 127, 130, 132, 144, 147, 148, 155, 156, 161}
    mizan_count = 0
    for ayah in range(1, 166):
        verse_id = f"6:{ayah}"
        entry = DOSSIER["verses"][verse_id]
        for field in FIELDS:
            assert len(entry[field]) == 5, f"{verse_id}:{field}"
            assert all(item["cite"].strip() and "ص." not in item["cite"] and "صص." not in item["cite"] for item in entry[field])
        assert entry["reviewStatus"].startswith("پیش‌نویس"), verse_id
        assert [item["sourceId"] for item in entry["classical"]].count("ar_tabari_qurancom") == 3, verse_id
        assert [item["sourceId"] for item in entry["classical"]].count("ar_qurtubi_qurancom") == 2, verse_id
        assert all("Quran.com API v4" in item["cite"] and "نسخهٔ 1.1" in item["cite"] for item in entry["classical"])
        assert len(entry["modern"]) == 5, verse_id
        assert any(item.get("sourceId") == "ar_qe_arabic_moyassar" and "نسخهٔ 1.0.0" in item["cite"] for item in entry["modern"]), verse_id
        mizan_quotes = [item for item in entry["modern"] if item.get("sourceId") == "fa_mizan_furqan"]
        assert len(mizan_quotes) == (0 if ayah in no_direct_mizan else 1), verse_id
        if mizan_quotes:
            mizan_count += 1
            item = mizan_quotes[0]
            assert item.get("sourceRecordId") and item.get("referenceRange"), verse_id
            assert "نسخهٔ 2026.0" in item["cite"] and "قطعهٔ" in item["cite"] and "موضعِ" in item["cite"], verse_id
            assert item.get("sourceExcerptTruncated") in (True, False), verse_id
    assert mizan_count == 139


def test_araf_7_1_to_206_has_five_cited_items_and_direct_mizan_only():
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-32")
    assert batch["range"] == "7:1–206" and batch["count"] == 206
    revision = find_revision(DOSSIER["revision"], "7:1–7:206")
    assert revision and revision["count"] == 206
    mizan_count = 0
    for ayah in range(1, 207):
        verse_id = f"7:{ayah}"
        entry = DOSSIER["verses"][verse_id]
        for field in FIELDS:
            assert len(entry[field]) == 5, f"{verse_id}:{field}"
            assert all(item["cite"].strip() and "ص." not in item["cite"] and "صص." not in item["cite"] for item in entry[field])
        assert entry["reviewStatus"].startswith("پیش‌نویس"), verse_id
        assert len(entry["classical"]) == 5
        assert len(entry["modern"]) == 5
        mizan_quotes = [item for item in entry["modern"] if item.get("sourceId") == "fa_mizan_furqan"]
        assert len(mizan_quotes) <= 1, verse_id
        if mizan_quotes:
            mizan_count += 1
            assert mizan_quotes[0].get("sourceRecordId") and mizan_quotes[0].get("referenceRange"), verse_id
            assert "نسخهٔ 2026.0" in mizan_quotes[0]["cite"] and "موضعِ" in mizan_quotes[0]["cite"], verse_id
    assert mizan_count == 144


def test_anfal_8_1_to_75_has_five_cited_items_and_direct_mizan_only():
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-33")
    assert batch["range"] == "8:1–75" and batch["count"] == 75
    revision = find_revision(DOSSIER["revision"], "8:1–8:75")
    assert revision and revision["count"] == 75
    mizan_count = 0
    for ayah in range(1, 76):
        verse_id = f"8:{ayah}"
        entry = DOSSIER["verses"][verse_id]
        for field in FIELDS:
            assert len(entry[field]) == 5, f"{verse_id}:{field}"
            assert all(item["cite"].strip() and "ص." not in item["cite"] and "صص." not in item["cite"] for item in entry[field])
        assert entry["reviewStatus"].startswith("پیش‌نویس"), verse_id
        assert len(entry["classical"]) == len(entry["modern"]) == 5
        mizan_quotes = [item for item in entry["modern"] if item.get("sourceId") == "fa_mizan_furqan"]
        assert len(mizan_quotes) <= 1, verse_id
        if mizan_quotes:
            mizan_count += 1
            assert mizan_quotes[0].get("sourceRecordId") and mizan_quotes[0].get("referenceRange"), verse_id
            assert "نسخهٔ 2026.0" in mizan_quotes[0]["cite"] and "موضعِ" in mizan_quotes[0]["cite"], verse_id
    assert mizan_count == 62


def test_tawbah_9_1_to_129_has_five_cited_items_and_direct_mizan_only():
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-34")
    assert batch["range"] == "9:1–129" and batch["count"] == 129
    revision = find_revision(DOSSIER["revision"], "9:1–9:129")
    assert revision and revision["count"] == 129
    assert DOSSIER["revision"]["previousRevision"]["count"] == 75
    mizan_count = 0
    for ayah in range(1, 130):
        verse_id = f"9:{ayah}"
        entry = DOSSIER["verses"][verse_id]
        for field in FIELDS:
            assert len(entry[field]) == 5, f"{verse_id}:{field}"
            assert all(item["cite"].strip() and "ص." not in item["cite"] and "صص." not in item["cite"] for item in entry[field])
        assert entry["reviewStatus"].startswith("پیش‌نویس"), verse_id
        assert len(entry["classical"]) == len(entry["modern"]) == 5
        assert [item.get("sourceId") for item in entry["classical"]].count("ar_tabari_qurancom") == 3, verse_id
        assert [item.get("sourceId") for item in entry["classical"]].count("ar_qurtubi_qurancom") == 2, verse_id
        assert all("Quran.com API v4" in item["cite"] and "نسخهٔ 1.1" in item["cite"] for item in entry["classical"]), verse_id
        assert any(item.get("sourceId") == "ar_qe_arabic_moyassar" and "نسخهٔ 1.0.0" in item["cite"] for item in entry["modern"]), verse_id
        mizan_quotes = [item for item in entry["modern"] if item.get("sourceId") == "fa_mizan_furqan"]
        assert len(mizan_quotes) <= 1, verse_id
        if mizan_quotes:
            mizan_count += 1
            item = mizan_quotes[0]
            assert item.get("sourceRecordId") and item.get("referenceRange"), verse_id
            assert "نسخهٔ 2026.0" in item["cite"] and "قطعهٔ" in item["cite"] and "موضعِ" in item["cite"], verse_id
            assert item.get("sourceExcerptTruncated") in (True, False), verse_id
    assert mizan_count == 26


def test_tawbah_mizan_gap_does_not_claim_absence_of_tafsir():
    entry = DOSSIER["verses"]["9:9"]
    item = next(item for item in entry["modern"] if item.get("sourceRecordId") == "210")
    assert item.get("sourceId") is None
    assert "برشِ مستقیمِ قابلِ انتساب بازیابی نشد" in item["text"]
    assert "نه ادعایِ نبودِ تفسیر" in item["text"]
