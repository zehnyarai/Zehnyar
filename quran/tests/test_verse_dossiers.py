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
    """هر آیه باید دست‌کم دو خوانشِ کهن و دو پژوهشِ معاصر با ارجاع داشته باشد."""
    for vid, entry in entries():
        assert len(entry["classical"]) >= 2, f"{vid}: خوانش کهن کم است"
        assert len(entry["modern"]) >= 2, f"{vid}: پژوهش معاصر کم است"
        for item in entry["classical"]:
            assert "ق،" in item["cite"] or "Izutsu" in item["cite"], f"{vid}: خوانش کهن ارجاعِ کهن ندارد"
        for item in entry["modern"]:
            assert any(token in item["cite"] for token in ("ق،", "، ۱۳", "، ۱۴", ", 19", ", 20")), (
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


def test_baqarah_2_282_article_page_ranges_are_not_conflated():
    citations = [item["cite"] for item in DOSSIER["verses"]["2:282"]["modern"]]
    rezai = next(cite for cite in citations if "رضایی‌کرمانی" in cite)
    tayeb = next(cite for cite in citations if "طیب‌حسینی" in cite)
    assert "صص. ۸۱–۱۲۱" in rezai
    assert "صص. ۱۱۳–۱۳۸" not in rezai
    assert "صص. ۱۱۳–۱۳۸" in tayeb
