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
            assert (
                "ق،" in item["cite"] or "Izutsu" in item["cite"] or "OpenITI" in item["cite"]
            ), f"{vid}: خوانش کهن ارجاعِ کهن ندارد"
        source_ids = {source["id"] for source in json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))["sources"]}
        for item in entry["modern"]:
            if item.get("sourceId"):
                assert item["sourceId"] in source_ids, f"{vid}: شناسهٔ منبعِ معاصر در رجیستری نیست"
            if item.get("sourceUrl"):
                assert item["sourceUrl"].startswith("https://"), f"{vid}: پیوندِ منبع امن نیست"
            assert any(token in item["cite"] for token in ("ق،", "درگذشته", "، ۱۳", "، ۱۴", ", 19", ", 20", "2026.0", "1.0.0")) or item.get("sourceId") or item.get("sourceUrl"), (
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
        assert any(word in joined for word in ("خطر", "پرسش", "نقد", "خطای خوانش", "تبار", "مرز", "فرق", "جدا", "مأخذ")), f"{vid}: بندِ انتقادی جهت ندارد"


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


def test_fatiha_classical_and_modern_sources_are_categorized_distinctly():
    for ayah in range(1, 8):
        entry = DOSSIER["verses"][f"1:{ayah}"]
        classical = " ".join(item["cite"] for item in entry["classical"])
        modern = " ".join(item["cite"] for item in entry["modern"])
        assert "طبری" in classical and "قرطبی" in classical
        assert "المیزان" not in classical
        assert "المیزان" in modern and "Izutsu" in modern and "Sinai" in modern
        assert len(entry["classical"]) == 2
        assert len(entry["modern"]) == 3


def test_al_imran_has_200_source_bound_dossiers_and_three_distinct_models():
    snapshots = DOSSIER["sourceSnapshots"]
    assert snapshots["tabari"]["sourceId"] == "ar_tabari_qurancom"
    assert snapshots["qurtubi"]["sourceId"] == "ar_qurtubi_qurancom"
    for name in ("tabari", "qurtubi"):
        snapshot = snapshots[name]
        assert len(snapshot["fileSha256"]) == 64
        assert snapshot["version"] == "1.1"
    for ayah in range(1, 201):
        vid = f"3:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert {field: len(entry[field]) for field in FIELDS} == {
            "notes": 4, "context": 2, "classical": 2, "modern": 3, "critical": 3, "research": 4,
        }, vid
        assert [item["sourceId"] for item in entry["classical"]] == [
            "ar_tabari_qurancom", "ar_qurtubi_qurancom",
        ], vid
        for item in entry["classical"]:
            assert item.get("sourceText")
            assert item["sourceText"] in item["text"]
        assert {item["model"] for item in entry["modern"]} == {"izutsu", "fillmore", "cognitive"}, vid
        assert all(item["kind"] == "editorial-inference" for item in entry["notes"] + entry["context"])


def test_yunus_10_49_60_is_a_scoped_draft_with_five_real_tafsir_readings_per_verse():
    expected = {f"10:{ayah}" for ayah in range(49, 61)}
    assert expected <= set(DOSSIER["verses"])
    assert not ({f"10:{ayah}" for ayah in range(1, 49)} & set(DOSSIER["verses"]))
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-29")
    assert batch["range"] == "10:49–60" and batch["count"] == 12
    assert "نیازمندِ بازبینیِ تخصصی" in batch["status"]
    source_ids = {source["id"] for source in json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))["sources"]}
    for ayah in range(49, 61):
        vid = f"10:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس") and "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert all(len(entry[field]) >= 5 for field in FIELDS), vid
        assert len(entry["modern"]) >= 5, vid
        models = {item.get("model") for item in entry["modern"] if item.get("model")}
        assert models == {"izutsu", "fillmore", "cognitive"}, vid
        genuine = {
            item["sourceId"]
            for field in ("classical", "modern")
            for item in entry[field]
            if item.get("sourceId") in source_ids and item.get("kind") == "source-summary"
        }
        assert len(genuine) >= 5, f"{vid}: only {sorted(genuine)}"
        for field in FIELDS:
            for item in entry[field]:
                if item.get("sourceId"):
                    assert item["sourceId"] in source_ids, f"{vid}:{field}: unknown source ID"
                if item.get("sourceUrl"):
                    assert item["sourceUrl"].startswith("https://"), f"{vid}:{field}: unsafe source URL"
    for ayah in (55, 56):
        baghawi = next(item for item in DOSSIER["verses"][f"10:{ayah}"]["classical"] if item["sourceId"] == "ar_baghawi_qurancom")
        assert baghawi["kind"] == "source-coverage-note"
        assert "شرحِ مستقل" in baghawi["text"]
    disagreement = " ".join(item["text"] for item in DOSSIER["verses"]["10:54"]["modern"] + DOSSIER["verses"]["10:54"]["critical"])
    assert "پنهان‌کردن" in disagreement and "آشکار" in disagreement
    medical = " ".join(item["text"] for item in DOSSIER["verses"]["10:57"]["critical"])
    assert "بالینی" in medical and "پزشکی" in medical


def test_yunus_10_61_72_uses_three_shia_and_three_sunni_tafsirs_per_verse():
    expected = {f"10:{ayah}" for ayah in range(61, 73)}
    assert expected <= set(DOSSIER["verses"])
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-30")
    assert batch["range"] == "10:61–72" and batch["count"] == 12
    assert "سه تفسیرِ اهل‌سنت و سه تفسیرِ شیعهٔ امامیه" in batch["status"]
    registry = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
    registry_by_id = {item["id"]: item for item in registry["sources"]}
    registry_ids = set(registry_by_id)
    sunni_core = {
        "ar_tabari_qurancom", "ar_qurtubi_qurancom", "ar_ibn_kathir_qurancom",
    }
    shia_core = {
        "ar_tusi_tibyan", "ar_fayd_safi", "en_enlightening_commentary_vol7",
    }
    classical_ids = sunni_core | {
        "ar_tusi_tibyan", "ar_fayd_safi", "ar_baghawi_qurancom", "ar_jalalayn_qurancom",
    }
    tradition_by_core = {
        **{source_id: "اهل‌سنت" for source_id in sunni_core},
        **{source_id: "شیعهٔ امامیه" for source_id in shia_core},
    }
    for source_id, tradition in tradition_by_core.items():
        assert registry_by_id[source_id]["tradition"] == tradition
    for ayah in range(61, 73):
        vid = f"10:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس") and "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert all(len(entry[field]) >= 5 for field in FIELDS), vid
        actual_classical = {
            item.get("sourceId") for item in entry["classical"]
            if item.get("kind") == "source-summary"
        }
        assert actual_classical == classical_ids, f"{vid}: {sorted(actual_classical)}"
        source_summaries = [
            item
            for field in ("classical", "modern")
            for item in entry[field]
            if item.get("kind") == "source-summary"
        ]
        used_ids = {item["sourceId"] for item in source_summaries}
        assert sunni_core <= used_ids, f"{vid}: Sunni core missing: {sorted(sunni_core - used_ids)}"
        assert shia_core <= used_ids, f"{vid}: Shia core missing: {sorted(shia_core - used_ids)}"
        for item in source_summaries:
            assert item["sourceId"] in registry_ids, f"{vid}: unregistered source"
            assert item.get("tradition") == registry_by_id[item["sourceId"]].get("tradition"), item["sourceId"]
            assert item.get("sourceUrl", "").startswith("https://"), item["sourceId"]
            assert item.get("cite", "").strip(), item["sourceId"]
        for source_id, tradition in tradition_by_core.items():
            item = next(item for item in source_summaries if item["sourceId"] == source_id)
            assert item["tradition"] == tradition
            assert item["text"].strip() and item["cite"].strip() and item["sourceUrl"].startswith("https://")
        if ayah == 62:
            baghawi = next(item for item in entry["classical"] if item["sourceId"] == "ar_baghawi_qurancom")
            assert "شرحِ گروهیِ یونس ۱۰:۶۲–۶۳" in baghawi["cite"]
            assert "/yunus/63/tafsirs/ar-tafsir-al-baghawi" in baghawi["sourceUrl"]
        if ayah == 63:
            ibn_kathir = next(item for item in entry["classical"] if item["sourceId"] == "ar_ibn_kathir_qurancom")
            assert "شرحِ آیهٔ ۱۰:۶۲" in ibn_kathir["cite"]
            assert "/yunus/62/tafsirs/ar-tafsir-ibn-kathir" in ibn_kathir["sourceUrl"]
        if ayah in (62, 63, 64):
            tafheem = next(item for item in entry["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
            assert "یادداشتِ ۶۸" in tafheem["cite"]
            assert "نه شرحِ" in tafheem["text"]
        tibyan = next(item for item in source_summaries if item["sourceId"] == "ar_tusi_tibyan")
        assert f"TafsirNo=39&SoraNo=10&AyahNo={ayah}&LanguageID=1" in tibyan["sourceUrl"]
        assert "التبيان الجامع لعلوم القرآن" in tibyan["cite"]
        safi = next(item for item in source_summaries if item["sourceId"] == "ar_fayd_safi")
        assert "الصافي في تفسير كلام الله الوافي" in safi["cite"]
        if ayah <= 64:
            assert "۱۰:۶۱–۶۴" in safi["cite"]
            assert "TafsirNo=41&SoraNo=10&AyahNo=61&LanguageID=1" in safi["sourceUrl"]
        elif ayah <= 71:
            assert "۱۰:۶۵–۷۱" in safi["cite"]
            assert "TafsirNo=41&SoraNo=10&AyahNo=65&LanguageID=1" in safi["sourceUrl"]
        else:
            assert "ذیلِ یونس ۱۰:72" in safi["cite"]
            assert "TafsirNo=41&SoraNo=10&AyahNo=72&LanguageID=1" in safi["sourceUrl"]
        model_citations = " ".join(item["cite"] for item in entry["modern"])
        assert all(name in model_citations for name in ("Izutsu", "Fillmore", "Lakoff")), vid
        assert "God and Man in the Koran: Semantics of the Koranic Weltanschauung" in model_citations, vid
        assert "Fillmore" in model_citations and "1982" in model_citations, vid
        for field in FIELDS:
            for item in entry[field]:
                if item.get("sourceId"):
                    assert item["sourceId"] in registry_ids, f"{vid}:{field}: unknown source ID"
                if item.get("sourceUrl"):
                    assert item["sourceUrl"].startswith("https://"), f"{vid}:{field}: unsafe source URL"
    for ayah in range(65, 73):
        maarif = next(
            item for item in DOSSIER["verses"][f"10:{ayah}"]["modern"]
            if item.get("sourceId") == "en_maarif_ul_quran"
        )
        assert maarif["kind"] == "source-coverage-note"
        assert "خوانشِ تفسیری" in maarif["limit"]

def test_tusi_yunus_10_64_attributes_bushra_report_to_abu_jafar_not_jafar_al_sadiq():
    tusi = next(
        item for item in DOSSIER["verses"]["10:64"]["classical"]
        if item.get("sourceId") == "ar_tusi_tibyan"
    )
    assert "ابوجعفر (امام باقر)" in tusi["text"]
    assert "امام صادق" not in tusi["text"]


def test_yunus_10_73_84_uses_three_shia_and_three_sunni_tafsirs_per_verse():
    expected = {f"10:{ayah}" for ayah in range(73, 85)}
    assert expected <= set(DOSSIER["verses"])
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-31")
    assert batch["range"] == "10:73–84" and batch["count"] == 12
    assert "سه تفسیرِ اهل‌سنت و سه تفسیرِ شیعهٔ امامیه" in batch["status"]
    assert "۱۰:۱–۴۸ در این checkout نیست" in batch["status"]
    assert not ({f"10:{ayah}" for ayah in range(1, 49)} & set(DOSSIER["verses"]))
    assert "نیازمندِ بازبینیِ تخصصی" in batch["status"]
    registry = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
    registry_by_id = {item["id"]: item for item in registry["sources"]}
    registry_ids = set(registry_by_id)
    sunni_core = {
        "ar_tabari_qurancom", "ar_qurtubi_qurancom", "ar_ibn_kathir_qurancom",
    }
    shia_core = {
        "ar_tusi_tibyan", "ar_fayd_safi", "en_enlightening_commentary_vol7",
    }
    classical_ids = sunni_core | {
        "ar_tusi_tibyan", "ar_fayd_safi", "ar_baghawi_qurancom", "ar_jalalayn_qurancom",
    }
    for source_id in sunni_core | {"ar_baghawi_qurancom", "ar_jalalayn_qurancom"}:
        assert registry_by_id[source_id]["tradition"] == "اهل‌سنت"
    for source_id in shia_core:
        assert registry_by_id[source_id]["tradition"] == "شیعهٔ امامیه"
    for ayah in range(73, 85):
        vid = f"10:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس") and "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert all(len(entry[field]) >= 5 for field in FIELDS), vid
        assert len(entry["modern"]) >= 5, vid
        assert all("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid
        actual_classical = {
            item.get("sourceId") for item in entry["classical"]
            if item.get("kind") == "source-summary"
        }
        assert actual_classical == classical_ids, f"{vid}: {sorted(actual_classical)}"
        source_summaries = [
            item
            for field in ("classical", "modern")
            for item in entry[field]
            if item.get("kind") == "source-summary"
        ]
        used_ids = {item["sourceId"] for item in source_summaries}
        assert sunni_core <= used_ids, f"{vid}: Sunni core missing: {sorted(sunni_core - used_ids)}"
        assert shia_core <= used_ids, f"{vid}: Shia core missing: {sorted(shia_core - used_ids)}"
        for item in source_summaries:
            assert item["sourceId"] in registry_ids, f"{vid}: unregistered source"
            assert item.get("tradition") == registry_by_id[item["sourceId"]].get("tradition"), item["sourceId"]
            assert item.get("sourceUrl", "").startswith("https://"), item["sourceId"]
            assert item.get("cite", "").strip(), item["sourceId"]
            assert "خلاصهٔ تحریری و منتسب" in item.get("limit", ""), item["sourceId"]
        for source_id in sunni_core | shia_core:
            item = next(item for item in source_summaries if item["sourceId"] == source_id)
            assert item["text"].strip() and item["cite"].strip() and item["sourceUrl"].startswith("https://")
        tibyan = next(item for item in source_summaries if item["sourceId"] == "ar_tusi_tibyan")
        assert f"TafsirNo=39&SoraNo=10&AyahNo={ayah}&LanguageID=1" in tibyan["sourceUrl"]
        safi = next(item for item in source_summaries if item["sourceId"] == "ar_fayd_safi")
        assert "شرحِ گروهیِ یونس ۱۰:۷۲–۸۴" in safi["cite"]
        assert "TafsirNo=41&SoraNo=10&AyahNo=83&LanguageID=1" in safi["sourceUrl"]
        enlightening = next(item for item in source_summaries if item["sourceId"] == "en_enlightening_commentary_vol7")
        expected_section = "section-8-ministries-noah-and-moses-referred" if ayah <= 82 else "section-9-moses-takes-away-children-israel"
        assert expected_section in enlightening["sourceUrl"]
        tafheem = next(item for item in source_summaries if item["sourceId"] == "en_tafheem_ul_quran")
        tafheem_group = "verse=83&to=92" if ayah in (83, 84) else "verse=71&to=82"
        assert tafheem_group in tafheem["sourceUrl"]
        expected_note = {78: "۷۶", 81: "۷۷", 83: "۷۸", 84: "۸۱"}.get(ayah)
        if expected_note:
            assert f"یادداشتِ {expected_note}" in tafheem["cite"] or f"یادداشت‌هایِ {expected_note}" in tafheem["cite"]
        models = " ".join(item["cite"] for item in entry["modern"])
        assert all(name in models for name in ("Izutsu", "Fillmore", "Lakoff")), vid
        maarif = next(item for item in entry["modern"] if item.get("sourceId") == "en_maarif_ul_quran")
        assert maarif["kind"] == "source-coverage-note"
        assert "خوانشِ تفسیری" in maarif["limit"]
        for field in FIELDS:
            for item in entry[field]:
                if item.get("sourceId"):
                    assert item["sourceId"] in registry_ids, f"{vid}:{field}: unknown source ID"
                if item.get("sourceUrl"):
                    assert item["sourceUrl"].startswith("https://"), f"{vid}:{field}: unsafe source URL"
    quote = next(item["text"] for item in DOSSIER["verses"]["10:83"]["classical"] if item.get("sourceId") == "ar_tusi_tibyan")
    assert "چند احتمال" in quote and "قومِ موسی یا قومِ فرعون" in quote
    two_conditions = next(item["text"] for item in DOSSIER["verses"]["10:84"]["classical"] if item.get("sourceId") == "ar_tusi_tibyan")
    assert "الزامِ توکل" in two_conditions and "تحققِ آن" in two_conditions


def test_public_fooladvand_copy_omits_license_condition_but_keeps_metadata():
    visible = (ROOT / "static" / "app.js").read_text(encoding="utf-8") + (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert "غیرتجاری" not in visible
    assert "non-commercial" not in visible.casefold()
    translation = json.loads((ROOT / "data" / "TRANSLATION_SOURCE.json").read_text(encoding="utf-8"))
    attribution = (ROOT / "data" / "ATTRIBUTION.md").read_text(encoding="utf-8")
    assert "non-commercial" in translation["sourceTerms"].casefold()
    assert "غیرتجاری" in attribution


def test_nisa_4_1_12_is_a_scoped_source_linked_batch():
    expected = {f"4:{ayah}" for ayah in range(1, 13)}
    assert expected <= set(DOSSIER["verses"])
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-32")
    assert batch["range"] == "4:1–12" and batch["count"] == 12
    assert "نیازمندِ بازبینیِ تخصصی" in batch["status"]
    assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]
    registry = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
    registry_by_id = {source["id"]: source for source in registry["sources"]}
    classical_ids = {
        "ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom",
        "ar_tusi_tibyan", "ar_fayd_safi",
    }
    for ayah in range(1, 13):
        vid = f"4:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert all(len(entry[field]) >= 5 for field in FIELDS), vid
        assert {item.get("sourceId") for item in entry["classical"]} == classical_ids
        source_summaries = [
            item for field in ("classical", "modern") for item in entry[field]
            if item.get("kind") == "source-summary"
        ]
        assert len({item["sourceId"] for item in source_summaries}) == 7
        for item in source_summaries:
            assert item["sourceId"] in registry_by_id
            assert item["tradition"] == registry_by_id[item["sourceId"]].get("tradition")
            assert item["sourceUrl"].startswith("https://")
        models = {item.get("model") for item in entry["modern"] if item.get("model")}
        assert models == {"izutsu", "fillmore", "cognitive"}
        assert any("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid
        tusi = next(item for item in entry["classical"] if item["sourceId"] == "ar_tusi_tibyan")
        fayd = next(item for item in entry["classical"] if item["sourceId"] == "ar_fayd_safi")
        assert f"TafsirNo=39&SoraNo=4&AyahNo={ayah}&LanguageID=1" in tusi["sourceUrl"]
        assert f"TafsirNo=41&SoraNo=4&AyahNo={ayah}&LanguageID=1" in fayd["sourceUrl"]
        if ayah in (3, 4):
            assert "شرحِ گروهیِ نساء ۴:۳–۴" in tusi["cite"]
            assert "شرحِ گروهیِ نساء ۴:۳–۴" in fayd["cite"]
        if ayah in (11, 12):
            assert "شرحِ گروهیِ نساء ۴:۱۱–۱۲" in tusi["cite"]
            assert "شرحِ گروهیِ نساء ۴:۱۱–۱۲" in fayd["cite"]
        tafheem = next(item for item in entry["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
        if ayah <= 10:
            assert "۴:۱–۱۰" in tafheem["cite"] and "verse=1&to=10" in tafheem["sourceUrl"]
        else:
            assert "۴:۱۱–۱۴" in tafheem["cite"] and "verse=11&to=14" in tafheem["sourceUrl"]
    catalog = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
    collection = next(item for item in catalog["collections"] if item["id"] == "nisa-4-1-12-cited")
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ نساء ۴:۱–۱۲"
    assert {item["id"] for item in collection["items"]} == classical_ids | {
        "ar_qe_arabic_moyassar", "en_tafheem_ul_quran",
    }
    assert all(item["scope"] == "نساء ۴:۱–۱۲" for item in collection["items"])


def test_nisa_4_13_24_is_a_scoped_draft_with_five_classical_readings_per_verse():
    expected = {f"4:{ayah}" for ayah in range(13, 25)}
    assert expected <= set(DOSSIER["verses"])
    assert "4:25" in DOSSIER["verses"]
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-33")
    assert batch["range"] == "4:13–24" and batch["count"] == 12
    assert "پیش‌نویسِ نیازمندِ بازبینیِ تخصصی" in batch["status"]
    assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]

    registry = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
    registry_by_id = {source["id"]: source for source in registry["sources"]}
    sunni = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
    shia = {"ar_tusi_tibyan", "ar_fayd_safi"}
    classical_ids = sunni | shia
    group_for_verse = {
        **{ayah: ("۴:۱۱–۱۴", "verse=11&to=14") for ayah in (13, 14)},
        **{ayah: ("۴:۱۵–۲۲", "verse=15&to=22") for ayah in range(15, 23)},
        **{ayah: ("۴:۲۳–۲۵", "verse=23&to=25") for ayah in (23, 24)},
    }

    for ayah in range(13, 25):
        vid = f"4:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) >= 5 for field in FIELDS), vid
        assert {item["sourceId"] for item in entry["classical"]} == classical_ids
        assert len(entry["classical"]) == 5
        assert sum(item["kind"] == "source-summary" for item in entry["modern"]) == 2
        assert {item["model"] for item in entry["modern"] if item.get("model")} == {
            "izutsu", "fillmore", "cognitive",
        }
        assert any("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid

        source_summaries = [
            item for field in ("classical", "modern") for item in entry[field]
            if item.get("kind") == "source-summary"
        ]
        assert len({item["sourceId"] for item in source_summaries}) == 7
        for item in source_summaries:
            source = registry_by_id[item["sourceId"]]
            assert item["tradition"] == source.get("tradition")
            assert item["text"].strip() and item["cite"].strip()
            assert item["sourceUrl"].startswith("https://")
            assert item["kind"] == "source-summary"

        for source_id in sunni:
            item = next(item for item in entry["classical"] if item["sourceId"] == source_id)
            assert f"/an-nisa/{ayah}/tafsirs/" in item["sourceUrl"]
            if source_id == "ar_jalalayn_qurancom":
                assert item["sourceUrl"].endswith("/ar-tafsir-jalalayn")
        for source_id, tafsir_no in (("ar_tusi_tibyan", 39), ("ar_fayd_safi", 41)):
            item = next(item for item in entry["classical"] if item["sourceId"] == source_id)
            assert f"TafsirNo={tafsir_no}&SoraNo=4&AyahNo={ayah}&LanguageID=1" in item["sourceUrl"]

        tafheem = next(item for item in entry["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
        group_label, group_query = group_for_verse[ayah]
        assert group_query in tafheem["sourceUrl"]
        assert group_label in tafheem["cite"]
        assert group_label in tafheem["evidence"]

        for field in FIELDS:
            assert len(entry[field]) >= 5, f"{vid}:{field}: fewer than five sourced items"
            for item in entry[field]:
                assert item.get("text", "").strip() and item.get("cite", "").strip()
                assert len(item["text"].split()) >= MIN_WORDS, f"{vid}:{field}: short item"
                if item.get("sourceUrl"):
                    assert item["sourceUrl"].startswith("https://")

    catalog = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
    assert catalog["version"] >= 9
    collection = next(item for item in catalog["collections"] if item["id"] == "nisa-4-13-24-cited")
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ نساء ۴:۱۳–۲۴"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == sunni
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == shia
    assert {item["id"] for item in collection["items"]} == classical_ids | {
        "ar_qe_arabic_moyassar", "en_tafheem_ul_quran",
    }
    assert all(item["scope"] == "نساء ۴:۱۳–۲۴" for item in collection["items"])
    tafheem_catalog = next(item for item in collection["items"] if item["id"] == "en_tafheem_ul_quran")
    assert set(tafheem_catalog["sourceUrls"]) == {
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=11&to=14",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=15&to=22",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=23&to=25",
    }

    # اختلاف‌های محوری باید نام‌به‌نام بمانند، نه اینکه در یک خوانش حل شوند.
    verse16 = DOSSIER["verses"]["4:16"]["classical"]
    tabari16 = next(item["text"] for item in verse16 if item["sourceId"] == "ar_tabari_qurancom")
    jalalayn16 = next(item["text"] for item in verse16 if item["sourceId"] == "ar_jalalayn_qurancom")
    tusi16 = next(item["text"] for item in verse16 if item["sourceId"] == "ar_tusi_tibyan")
    fayd16 = next(item["text"] for item in verse16 if item["sourceId"] == "ar_fayd_safi")
    assert "دو نامحصنِ زن و مرد" in tabari16
    assert "زنا یا لواط" in jalalayn16
    assert "نسخِ قرآن با سنت" in tusi16
    assert "از اهل‌بیت ثابت نشده" in fayd16

    verse24 = DOSSIER["verses"]["4:24"]
    tabari24 = next(item["text"] for item in verse24["classical"] if item["sourceId"] == "ar_tabari_qurancom")
    ibn_kathir24 = next(item["text"] for item in verse24["classical"] if item["sourceId"] == "ar_ibn_kathir_qurancom")
    jalalayn24 = next(item["text"] for item in verse24["classical"] if item["sourceId"] == "ar_jalalayn_qurancom")
    tusi24 = next(item["text"] for item in verse24["classical"] if item["sourceId"] == "ar_tusi_tibyan")
    fayd24 = next(item["text"] for item in verse24["classical"] if item["sourceId"] == "ar_fayd_safi")
    tafheem24 = next(item["text"] for item in verse24["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
    assert "ترجیح" in tabari24 and "متعه" in tabari24
    assert "نسخ" in ibn_kathir24 and "متعه" in ibn_kathir24
    assert "مهر" in jalalayn24
    assert "متعه" in tusi24 and "قرائت" in tusi24
    assert "متعه" in fayd24 and "امامی" in fayd24
    assert "یادداشتِ ۴۴" in tafheem24 and "برده‌دارانه" in tafheem24


def test_nisa_4_25_36_is_a_scoped_draft_with_five_classical_readings_per_verse():
    expected = {f"4:{ayah}" for ayah in range(25, 37)}
    assert expected <= set(DOSSIER["verses"])
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-34")
    assert batch["range"] == "4:25–36" and batch["count"] == 12
    assert "پیش‌نویسِ نیازمندِ بازبینیِ تخصصی" in batch["status"]
    assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]

    registry = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
    registry_by_id = {source["id"]: source for source in registry["sources"]}
    sunni = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
    shia = {"ar_tusi_tibyan", "ar_fayd_safi"}
    classical_ids = sunni | shia
    tafheem_group = {
        **{ayah: ("۴:۲۳–۲۵", "verse=23&to=25") for ayah in (25,)},
        **{ayah: ("۴:۲۶–۳۳", "verse=26&to=33") for ayah in range(26, 34)},
        **{ayah: ("۴:۳۴–۴۲", "verse=34&to=42") for ayah in range(34, 37)},
    }
    fayd_group = {
        25: (25, None),
        **{ayah: (26, "۴:۲۶–۲۹") for ayah in range(26, 30)},
        **{ayah: (30, "۴:۳۰–۳۱") for ayah in (30, 31)},
        **{ayah: (32, "۴:۳۲–۳۳") for ayah in (32, 33)},
        **{ayah: (34, "۴:۳۴–۳۶") for ayah in (34, 35, 36)},
    }

    for ayah in range(25, 37):
        vid = f"4:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) >= 5 for field in FIELDS), vid
        assert {item.get("sourceId") for item in entry["classical"]} == classical_ids
        assert len(entry["classical"]) == 5
        assert sum(item.get("kind") == "source-summary" for item in entry["modern"]) == 2
        assert {item.get("model") for item in entry["modern"] if item.get("model")} == {
            "izutsu", "fillmore", "cognitive",
        }
        assert any("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid

        source_summaries = [
            item for field in ("classical", "modern") for item in entry[field]
            if item.get("kind") == "source-summary"
        ]
        assert len({item["sourceId"] for item in source_summaries}) == 7
        for item in source_summaries:
            source = registry_by_id[item["sourceId"]]
            assert item["tradition"] == source.get("tradition")
            assert item["text"].strip() and item["cite"].strip()
            assert item["sourceUrl"].startswith("https://")
            assert item.get("limit")
        for source_id in sunni:
            item = next(item for item in entry["classical"] if item["sourceId"] == source_id)
            assert f"/an-nisa/{ayah}/tafsirs/" in item["sourceUrl"]
        for source_id, tafsir_no in (("ar_tusi_tibyan", 39), ("ar_fayd_safi", 41)):
            item = next(item for item in entry["classical"] if item["sourceId"] == source_id)
            assert f"TafsirNo={tafsir_no}&SoraNo=4&AyahNo=" in item["sourceUrl"]
        fayd = next(item for item in entry["classical"] if item["sourceId"] == "ar_fayd_safi")
        fayd_verse, fayd_label = fayd_group[ayah]
        assert f"TafsirNo=41&SoraNo=4&AyahNo={fayd_verse}&LanguageID=1" in fayd["sourceUrl"]
        if fayd_label:
            assert f"شرحِ گروهیِ نساء {fayd_label}" in fayd["cite"]
            assert fayd_label in fayd["evidence"]

        tafheem = next(item for item in entry["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
        group_label, group_query = tafheem_group[ayah]
        assert group_query in tafheem["sourceUrl"]
        assert group_label in tafheem["cite"]
        assert group_label in tafheem["evidence"]

        for field in FIELDS:
            for item in entry[field]:
                assert item["text"].strip() and item["cite"].strip()
                assert len(item["text"].split()) >= MIN_WORDS, f"{vid}:{field}: short item"
                if item.get("sourceUrl"):
                    assert item["sourceUrl"].startswith("https://")

    catalog = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
    assert catalog["version"] >= 10
    collection = next(item for item in catalog["collections"] if item["id"] == "nisa-4-25-36-cited")
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ نساء ۴:۲۵–۳۶"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == sunni
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == shia
    assert {item["id"] for item in collection["items"]} == classical_ids | {
        "ar_qe_arabic_moyassar", "en_tafheem_ul_quran",
    }
    assert all(item["scope"] == "نساء ۴:۲۵–۳۶" for item in collection["items"])
    tafheem_catalog = next(item for item in collection["items"] if item["id"] == "en_tafheem_ul_quran")
    assert set(tafheem_catalog["sourceUrls"]) == {
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=23&to=25",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=26&to=33",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=34&to=42",
    }
    assert "پیش‌نویس" in collection["notice"] and "بازبینیِ تخصصی" in collection["notice"]
    catalog_by_id = {item["id"]: item for item in collection["items"]}
    for source_id in ("ar_tabari_qurancom", "ar_ibn_kathir_qurancom"):
        digest = registry_by_id[source_id]["upstreamZipSha256"]
        assert len(digest) == 64 and digest in catalog_by_id[source_id]["basis"]
        assert len([url for url in catalog_by_id[source_id]["sourceUrls"] if f"/an-nisa/" in url]) == 12
        assert "مقابلهٔ کاملِ همهٔ روایات و اسانید نیست" in catalog_by_id[source_id]["basis"]
    assert "۱–۳ از ۱۱" in catalog_by_id["en_tafheem_ul_quran"]["basis"]

    # Preserve important disagreements and avoid presenting historical rulings as current advice.
    tabari25 = next(item["text"] for item in DOSSIER["verses"]["4:25"]["classical"] if item["sourceId"] == "ar_tabari_qurancom")
    tusi25 = next(item["text"] for item in DOSSIER["verses"]["4:25"]["classical"] if item["sourceId"] == "ar_tusi_tibyan")
    ibn_kathir25 = next(item["text"] for item in DOSSIER["verses"]["4:25"]["classical"] if item["sourceId"] == "ar_ibn_kathir_qurancom")
    assert "قرائت" in tabari25 and "کنیزِ اهلِ کتاب" in tabari25
    assert "احصان" in tusi25 and "داود و ابوثور" in ibn_kathir25
    assert "یادداشتِ ۴۴" in " ".join(item["text"] for item in DOSSIER["verses"]["4:25"]["context"])
    assert "۴:۲۴ است" in " ".join(item["text"] for item in DOSSIER["verses"]["4:25"]["context"])

    tusi29 = next(item["text"] for item in DOSSIER["verses"]["4:29"]["classical"] if item["sourceId"] == "ar_tusi_tibyan")
    assert "خودکشی" in tusi29 and "تباهی" in tusi29
    tabari31 = next(item["text"] for item in DOSSIER["verses"]["4:31"]["classical"] if item["sourceId"] == "ar_tabari_qurancom")
    tusi31 = next(item["text"] for item in DOSSIER["verses"]["4:31"]["classical"] if item["sourceId"] == "ar_tusi_tibyan")
    assert "ابن‌مسعود" in tabari31 and "معتزله" in tusi31
    tabari30 = next(item["text"] for item in DOSSIER["verses"]["4:30"]["classical"] if item["sourceId"] == "ar_tabari_qurancom")
    assert "۴:۱۹–۲۹" in tabari30
    tabari32 = next(item["text"] for item in DOSSIER["verses"]["4:32"]["classical"] if item["sourceId"] == "ar_tabari_qurancom")
    assert "پاداش و کیفر" in tabari32 and "نه به میراث" in tabari32
    jalalayn32 = next(item["text"] for item in DOSSIER["verses"]["4:32"]["classical"] if item["sourceId"] == "ar_jalalayn_qurancom")
    tusi32 = next(item["text"] for item in DOSSIER["verses"]["4:32"]["classical"] if item["sourceId"] == "ar_tusi_tibyan")
    assert "جهاد" in jalalayn32 and "ارث اکتساب نیست" in tusi32
    jalalayn33 = next(item["text"] for item in DOSSIER["verses"]["4:33"]["classical"] if item["sourceId"] == "ar_jalalayn_qurancom")
    fayd33 = next(item["text"] for item in DOSSIER["verses"]["4:33"]["classical"] if item["sourceId"] == "ar_fayd_safi")
    assert "منسوخ" in jalalayn33 and "نصرتِ بی‌ارث" in fayd33
    tabari33 = next(item["text"] for item in DOSSIER["verses"]["4:33"]["classical"] if item["sourceId"] == "ar_tabari_qurancom")
    assert "نه میراثِ منسوخ‌شده" in tabari33

    ibn_kathir34 = next(item["text"] for item in DOSSIER["verses"]["4:34"]["classical"] if item["sourceId"] == "ar_ibn_kathir_qurancom")
    critical34 = " ".join(item["text"] for item in DOSSIER["verses"]["4:34"]["critical"])
    assert "برتریِ مرد" in ibn_kathir34
    assert "توصیهٔ خشونت" in critical34 and "خشونتِ خانگی" in critical34
    tusi35 = next(item["text"] for item in DOSSIER["verses"]["4:35"]["classical"] if item["sourceId"] == "ar_tusi_tibyan")
    ibn_kathir35 = next(item["text"] for item in DOSSIER["verses"]["4:35"]["classical"] if item["sourceId"] == "ar_ibn_kathir_qurancom")
    assert "اذن" in tusi35 and "جمهور" in ibn_kathir35
    tabari35 = next(item["text"] for item in DOSSIER["verses"]["4:35"]["classical"] if item["sourceId"] == "ar_tabari_qurancom")
    assert "بی‌رضایت" in tabari35 and "سلطان" in tabari35
    tabari36 = next(item["text"] for item in DOSSIER["verses"]["4:36"]["classical"] if item["sourceId"] == "ar_tabari_qurancom")
    tusi36 = next(item["text"] for item in DOSSIER["verses"]["4:36"]["classical"] if item["sourceId"] == "ar_tusi_tibyan")
    fayd36 = next(item["text"] for item in DOSSIER["verses"]["4:36"]["classical"] if item["sourceId"] == "ar_fayd_safi")
    assert "جار ذي القربى" in tabari36 and "خویشاوند" in tabari36 and "مسلمان، مشرک" in tabari36
    assert "اقوالِ لغوی" in tusi36 and "چهل خانه" in fayd36


def test_nisa_4_37_48_has_five_tafsirs_two_modern_sources_and_three_models_per_verse():
    expected = {f"4:{ayah}" for ayah in range(37, 49)}
    assert expected <= set(DOSSIER["verses"])
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-35")
    assert batch["range"] == "4:37–48" and batch["count"] == 12
    assert "پیش‌نویسِ نیازمندِ بازبینیِ تخصصی" in batch["status"]
    assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]

    registry = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
    registry_by_id = {source["id"]: source for source in registry["sources"]}
    sunni = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
    shia = {"ar_tusi_tibyan", "ar_fayd_safi"}
    classical_ids = sunni | shia
    fayd_groups = {
        **{ayah: (37, "۴:۳۷–۴۱") for ayah in range(37, 42)},
        **{ayah: (43, "۴:۴۲–۴۳") for ayah in (42, 43)},
        **{ayah: (48, "۴:۴۴–۴۸") for ayah in range(44, 49)},
    }

    for ayah in range(37, 49):
        vid = f"4:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) >= 5 for field in FIELDS), vid
        assert len(entry["classical"]) == 5
        assert {item["sourceId"] for item in entry["classical"]} == classical_ids
        assert sum(item["kind"] == "source-summary" for item in entry["modern"]) == 2
        assert {item["model"] for item in entry["modern"] if item.get("model")} == {
            "izutsu", "fillmore", "cognitive",
        }
        assert any("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid

        source_summaries = [
            item for field in ("classical", "modern") for item in entry[field]
            if item.get("kind") == "source-summary"
        ]
        assert len({item["sourceId"] for item in source_summaries}) == 7
        for source in source_summaries:
            assert source["sourceId"] in registry_by_id
            assert source["tradition"] == registry_by_id[source["sourceId"]].get("tradition")
            assert source["sourceUrl"].startswith("https://")
            assert source["cite"].strip() and source["evidence"].strip() and source["limit"].strip()

        tabari = next(item for item in entry["classical"] if item["sourceId"] == "ar_tabari_qurancom")
        ibn_kathir = next(item for item in entry["classical"] if item["sourceId"] == "ar_ibn_kathir_qurancom")
        jalalayn = next(item for item in entry["classical"] if item["sourceId"] == "ar_jalalayn_qurancom")
        assert f"/an-nisa/{ayah}/tafsirs/ar-tafsir-al-tabari" in tabari["sourceUrl"]
        assert f"/an-nisa/{ayah}/tafsirs/ar-tafsir-ibn-kathir" in ibn_kathir["sourceUrl"]
        assert jalalayn["sourceUrl"].endswith("/ar-tafsir-jalalayn")
        for source_id, tafsir_no in (("ar_tusi_tibyan", 39), ("ar_fayd_safi", 41)):
            source = next(item for item in entry["classical"] if item["sourceId"] == source_id)
            assert f"TafsirNo={tafsir_no}&SoraNo=4&AyahNo=" in source["sourceUrl"]
        fayd = next(item for item in entry["classical"] if item["sourceId"] == "ar_fayd_safi")
        fayd_page, fayd_label = fayd_groups[ayah]
        assert f"TafsirNo=41&SoraNo=4&AyahNo={fayd_page}&LanguageID=1" in fayd["sourceUrl"]
        assert f"شرحِ گروهیِ نساء {fayd_label}" in fayd["cite"]
        assert fayd_label in fayd["evidence"]

        tafheem = next(item for item in entry["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
        if ayah <= 42:
            tafheem_group, query = "۴:۳۴–۴۲", "verse=34&to=42"
        else:
            tafheem_group, query = "۴:۴۳–۵۷", "verse=43&to=57"
        assert query in tafheem["sourceUrl"]
        assert tafheem_group in tafheem["cite"] and tafheem_group in tafheem["evidence"]
        for field in FIELDS:
            for item in entry[field]:
                assert len(item["text"].split()) >= MIN_WORDS, f"{vid}:{field}: short item"
                assert item["cite"].strip()
                if item.get("sourceUrl"):
                    assert item["sourceUrl"].startswith("https://")

    catalog = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
    assert catalog["version"] >= 11
    collection = next(item for item in catalog["collections"] if item["id"] == "nisa-4-37-48-cited")
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ نساء ۴:۳۷–۴۸"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == sunni
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == shia
    assert {item["id"] for item in collection["items"]} == classical_ids | {
        "ar_qe_arabic_moyassar", "en_tafheem_ul_quran",
    }
    assert all(item["scope"] == "نساء ۴:۳۷–۴۸" for item in collection["items"])
    catalog_by_id = {item["id"]: item for item in collection["items"]}
    for source_id in ("ar_tabari_qurancom", "ar_ibn_kathir_qurancom"):
        digest = registry_by_id[source_id]["upstreamZipSha256"]
        source = catalog_by_id[source_id]
        assert len(digest) == 64 and digest in source["basis"]
        assert len([url for url in source["sourceUrls"] if "/an-nisa/" in url]) == 12
        assert "مقابلهٔ کاملِ همهٔ روایات و اسانید" in source["basis"]
    tafheem_catalog = catalog_by_id["en_tafheem_ul_quran"]
    assert set(tafheem_catalog["sourceUrls"]) == {
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=34&to=42",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=43&to=57",
    }
    assert "یادداشت‌های ۶۳–۶۴" in tafheem_catalog["basis"]
    assert "یادداشت‌های ۶۵–۸۰" in tafheem_catalog["basis"]
    for source_id in ("ar_tabari_qurancom", "ar_ibn_kathir_qurancom"):
        collection_25 = next(item for item in catalog["collections"] if item["id"] == "nisa-4-25-36-cited")
        source_25 = next(item for item in collection_25["items"] if item["id"] == source_id)
        assert registry_by_id[source_id]["upstreamZipSha256"] in source_25["basis"]
        assert "مقابلهٔ کاملِ همهٔ روایات و اسانید نیست" in source_25["basis"]

    # Keep consequential source disagreements visible and specifically attributed.
    tabari37 = next(item["text"] for item in DOSSIER["verses"]["4:37"]["classical"] if item["sourceId"] == "ar_tabari_qurancom")
    ibn_kathir37 = next(item["text"] for item in DOSSIER["verses"]["4:37"]["classical"] if item["sourceId"] == "ar_ibn_kathir_qurancom")
    assert "کتمانِ دانش" in tabari37 and "بخلِ مالی" in ibn_kathir37
    assert "منافقان" in next(item["text"] for item in DOSSIER["verses"]["4:38"]["classical"] if item["sourceId"] == "ar_tabari_qurancom")
    assert "جبر" in next(item["text"] for item in DOSSIER["verses"]["4:39"]["classical"] if item["sourceId"] == "ar_tusi_tibyan")
    assert "دو برابر" in " ".join(item["text"] for item in DOSSIER["verses"]["4:40"]["modern"])
    assert "هفتصد" in next(item["text"] for item in DOSSIER["verses"]["4:40"]["classical"] if item["sourceId"] == "ar_jalalayn_qurancom")
    assert "امام" in next(item["text"] for item in DOSSIER["verses"]["4:41"]["classical"] if item["sourceId"] == "ar_fayd_safi")
    assert "فتحِ تا" in next(item["text"] for item in DOSSIER["verses"]["4:42"]["classical"] if item["sourceId"] == "ar_tabari_qurancom")
    assert "خواب‌آلودگی" in next(item["text"] for item in DOSSIER["verses"]["4:43"]["classical"] if item["sourceId"] == "ar_tusi_tibyan")
    assert "رشوه" in next(item["text"] for item in DOSSIER["verses"]["4:44"]["classical"] if item["sourceId"] == "ar_tusi_tibyan")
    tafheem45 = next(item for item in DOSSIER["verses"]["4:45"]["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
    assert "یادداشتِ جداگانه‌ای" in tafheem45["text"]
    assert "سه صورتِ تحریف" in next(item["text"] for item in DOSSIER["verses"]["4:46"]["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
    assert "احتمال" in " ".join(item["text"] for item in DOSSIER["verses"]["4:47"]["critical"])
    assert "ولایتِ علی" in next(item["text"] for item in DOSSIER["verses"]["4:48"]["classical"] if item["sourceId"] == "ar_fayd_safi")

    for batch in DOSSIER["batches"]:
        if batch.get("range", "").startswith("4:"):
            assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]
    assert "نساء در این checkout بازهٔ ۴:۱–۱۷۶ را پوشش می‌دهد" in DOSSIER["notice"]


def test_nisa_4_49_60_has_five_tafsirs_two_modern_sources_and_three_models_per_verse():
    expected = {f"4:{ayah}" for ayah in range(49, 61)}
    assert expected <= set(DOSSIER["verses"])
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-36")
    assert batch["range"] == "4:49–60" and batch["count"] == 12
    assert "پیش‌نویسِ نیازمندِ بازبینیِ تخصصی" in batch["status"]
    assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]

    registry = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
    registry_by_id = {source["id"]: source for source in registry["sources"]}
    sunni = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
    shia = {"ar_tusi_tibyan", "ar_fayd_safi"}
    fayruz = "ar_fayruzabadi_greattafsirs"
    assert registry_by_id[fayruz]["tradition"] == "اهل‌سنت"
    fayd_groups = {
        **{ayah: (49, "۴:۴۹–۵۳") for ayah in range(49, 54)},
        **{ayah: (54, "۴:۵۴–۵۸") for ayah in range(54, 59)},
        59: (59, "۴:۵۹"),
        60: (60, "۴:۶۰–۶۶"),
    }

    for ayah in range(49, 61):
        vid = f"4:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) >= 5 for field in FIELDS), vid
        assert len(entry["classical"]) == 5
        expected_classical = (sunni - {"ar_ibn_kathir_qurancom"}) | shia | {fayruz} if ayah == 52 else sunni | shia
        assert {item["sourceId"] for item in entry["classical"]} == expected_classical, vid
        assert sum(item["kind"] == "source-summary" for item in entry["modern"]) == 2
        assert {item["model"] for item in entry["modern"] if item.get("model")} == {
            "izutsu", "fillmore", "cognitive",
        }
        assert any("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid

        source_summaries = [
            item for field in ("classical", "modern") for item in entry[field]
            if item.get("kind") == "source-summary"
        ]
        assert len({item["sourceId"] for item in source_summaries}) == 7
        traditions = [item["tradition"] for item in entry["classical"]]
        assert traditions.count("اهل‌سنت") == 3, vid
        assert traditions.count("شیعهٔ امامیه") == 2, vid
        for source in source_summaries:
            assert source["sourceId"] in registry_by_id
            assert source["tradition"] == registry_by_id[source["sourceId"]].get("tradition")
            assert source["sourceUrl"].startswith("https://")
            assert source["cite"].strip() and source["evidence"].strip() and source["limit"].strip()

        tusi = next(item for item in entry["classical"] if item["sourceId"] == "ar_tusi_tibyan")
        fayd = next(item for item in entry["classical"] if item["sourceId"] == "ar_fayd_safi")
        assert f"TafsirNo=39&SoraNo=4&AyahNo={ayah}&LanguageID=1" in tusi["sourceUrl"]
        fayd_page, fayd_label = fayd_groups[ayah]
        assert f"TafsirNo=41&SoraNo=4&AyahNo={fayd_page}&LanguageID=1" in fayd["sourceUrl"]
        assert fayd_label in fayd["cite"] and fayd_label in fayd["evidence"]

        tafheem = next(item for item in entry["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
        if ayah <= 50:
            tafheem_group, query = "۴:۴۳–۵۰", "verse=43&to=50"
        elif ayah <= 56:
            tafheem_group, query = "۴:۵۱–۵۶", "verse=51&to=56"
        else:
            tafheem_group, query = "۴:۵۷–۷۰", "verse=57&to=70"
        assert query in tafheem["sourceUrl"]
        assert tafheem_group in tafheem["cite"] and tafheem_group in tafheem["evidence"]
        for field in FIELDS:
            for item in entry[field]:
                assert len(item["text"].split()) >= MIN_WORDS, f"{vid}:{field}: short item"
                assert item["cite"].strip()
                if item.get("sourceUrl"):
                    assert item["sourceUrl"].startswith("https://")

    ibn52 = DOSSIER["verses"]["4:52"]["classical"]
    assert "ar_ibn_kathir_qurancom" not in {item["sourceId"] for item in ibn52}
    fayruz52 = next(item for item in ibn52 if item["sourceId"] == fayruz)
    assert "۴:۴۸–۵۴" in fayruz52["cite"] and fayruz52["sourceUrl"].endswith("TafsirNo=5&SoraNo=4&AyahNo=52&LanguageID=1")
    assert "جزیه" in fayruz52["text"]
    assert "صدیق، فاروق و ذوالنورین" in next(
        item["text"] for item in DOSSIER["verses"]["4:49"]["classical"] if item["sourceId"] == "ar_fayd_safi"
    )
    assert "فلان و فلان" in next(
        item["text"] for item in DOSSIER["verses"]["4:51"]["classical"] if item["sourceId"] == "ar_fayd_safi"
    )
    assert "امامت و خلافت" in next(
        item["text"] for item in DOSSIER["verses"]["4:53"]["classical"] if item["sourceId"] == "ar_fayd_safi"
    )
    assert "ابن‌ابی‌العوجاء" in next(
        item["text"] for item in DOSSIER["verses"]["4:56"]["classical"] if item["sourceId"] == "ar_fayd_safi"
    )
    tafheem60 = next(item for item in DOSSIER["verses"]["4:60"]["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
    assert "یادداشتِ ۹۱" in tafheem60["cite"] and "مودودی" in tafheem60["text"]
    assert "نظامِ حقوقی" in tafheem60["text"]

    catalog = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
    assert catalog["version"] >= 13
    collection = next(item for item in catalog["collections"] if item["id"] == "nisa-4-49-60-cited")
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ نساء ۴:۴۹–۶۰"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == sunni
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == shia
    assert collection["comparativeCore"]["substitutions"][0]["replacementSourceId"] == fayruz
    assert {item["id"] for item in collection["items"]} == sunni | shia | {fayruz, "ar_qe_arabic_moyassar", "en_tafheem_ul_quran"}
    assert all(item["scope"] == "نساء ۴:۴۹–۶۰" for item in collection["items"])
    by_id = {item["id"]: item for item in collection["items"]}
    assert set(by_id["en_tafheem_ul_quran"]["sourceUrls"]) == {
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=43&to=50",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=51&to=56",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=57&to=70",
    }
    assert len([url for url in by_id["ar_tabari_qurancom"]["sourceUrls"] if "/an-nisa/" in url]) == 12
    assert len([url for url in by_id["ar_ibn_kathir_qurancom"]["sourceUrls"] if "/an-nisa/" in url]) == 12
    assert "فقط متنِ آیه" in by_id["ar_ibn_kathir_qurancom"]["basis"]
    assert by_id[fayruz]["sourceUrls"] == [fayruz52["sourceUrl"]]
    assert "۴:۵۲" in by_id[fayruz]["basis"]
    for batch in DOSSIER["batches"]:
        if batch.get("range", "").startswith("4:"):
            assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]
    assert "نساء در این checkout بازهٔ ۴:۱–۱۷۶ را پوشش می‌دهد" in DOSSIER["notice"]


def test_nisa_4_61_72_has_five_tafsirs_two_modern_sources_and_three_models_per_verse():
    expected = {f"4:{ayah}" for ayah in range(61, 73)}
    assert expected <= set(DOSSIER["verses"])
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-37")
    assert batch["range"] == "4:61–72" and batch["count"] == 12
    assert "پیش‌نویسِ نیازمندِ بازبینیِ تخصصی" in batch["status"]
    assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]

    registry = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
    registry_by_id = {source["id"]: source for source in registry["sources"]}
    sunni = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
    shia = {"ar_tusi_tibyan", "ar_fayd_safi"}
    fayd_groups = {
        **{ayah: (61, "۴:۶۰–۶۶") for ayah in range(61, 67)},
        **{ayah: (67, "۴:۶۷–۷۲") for ayah in range(67, 73)},
    }

    for ayah in range(61, 73):
        vid = f"4:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) >= 5 for field in FIELDS), vid
        assert len(entry["classical"]) == 5
        assert {item["sourceId"] for item in entry["classical"]} == sunni | shia, vid
        assert sum(item["kind"] == "source-summary" for item in entry["modern"]) == 2
        assert {item["model"] for item in entry["modern"] if item.get("model")} == {
            "izutsu", "fillmore", "cognitive",
        }
        assert any("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid

        source_summaries = [
            item for field in ("classical", "modern") for item in entry[field]
            if item.get("kind") == "source-summary"
        ]
        assert len({item["sourceId"] for item in source_summaries}) == 7
        traditions = [item["tradition"] for item in entry["classical"]]
        assert traditions.count("اهل‌سنت") == 3, vid
        assert traditions.count("شیعهٔ امامیه") == 2, vid
        for source in source_summaries:
            assert source["sourceId"] in registry_by_id
            assert source["tradition"] == registry_by_id[source["sourceId"]].get("tradition")
            assert source["sourceUrl"].startswith("https://")
            assert source["cite"].strip() and source["evidence"].strip() and source["limit"].strip()

        tusi = next(item for item in entry["classical"] if item["sourceId"] == "ar_tusi_tibyan")
        fayd = next(item for item in entry["classical"] if item["sourceId"] == "ar_fayd_safi")
        assert f"TafsirNo=39&SoraNo=4&AyahNo={ayah}&LanguageID=1" in tusi["sourceUrl"]
        fayd_page, fayd_label = fayd_groups[ayah]
        assert f"TafsirNo=41&SoraNo=4&AyahNo={fayd_page}&LanguageID=1" in fayd["sourceUrl"]
        assert fayd_label in fayd["cite"] and fayd_label in fayd["evidence"]

        tafheem = next(item for item in entry["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
        if ayah <= 70:
            tafheem_group, query = "۴:۵۷–۷۰", "verse=57&to=70"
        else:
            tafheem_group, query = "۴:۷۱–۷۶", "verse=71&to=76"
        assert query in tafheem["sourceUrl"]
        assert tafheem_group in tafheem["cite"] and tafheem_group in tafheem["evidence"]
        for field in FIELDS:
            for source_item in entry[field]:
                assert len(source_item["text"].split()) >= MIN_WORDS, f"{vid}:{field}: short item"
                assert source_item["cite"].strip()
                if source_item.get("sourceUrl"):
                    assert source_item["sourceUrl"].startswith("https://")

    assert "دعوت‌کننده" in next(
        item["text"] for item in DOSSIER["verses"]["4:61"]["classical"]
        if item["sourceId"] == "ar_tabari_qurancom"
    )
    assert "حکایتِ عتبی" in next(
        item["text"] for item in DOSSIER["verses"]["4:64"]["classical"]
        if item["sourceId"] == "ar_ibn_kathir_qurancom"
    )
    assert "علی" in next(
        item["text"] for item in DOSSIER["verses"]["4:65"]["classical"]
        if item["sourceId"] == "ar_fayd_safi"
    )
    qe_67 = next(
        item for item in DOSSIER["verses"]["4:67"]["modern"]
        if item.get("sourceId") == "ar_qe_arabic_moyassar"
    )
    assert "تکرار" in qe_67["evidence"] and "سه مدخل" in qe_67["evidence"]
    assert "تضعیفِ روحیه" in next(
        item["text"] for item in DOSSIER["verses"]["4:72"]["modern"]
        if item.get("sourceId") == "en_tafheem_ul_quran"
    )

    catalog = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
    assert catalog["version"] >= 13
    collection = next(item for item in catalog["collections"] if item["id"] == "nisa-4-61-72-cited")
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ نساء ۴:۶۱–۷۲"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == sunni
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == shia
    assert {item["id"] for item in collection["items"]} == sunni | shia | {
        "ar_qe_arabic_moyassar", "en_tafheem_ul_quran",
    }
    assert all(item["scope"] == "نساء ۴:۶۱–۷۲" for item in collection["items"])
    catalog_by_id = {item["id"]: item for item in collection["items"]}
    assert set(catalog_by_id["en_tafheem_ul_quran"]["sourceUrls"]) == {
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=57&to=70",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=71&to=76",
    }
    assert len([url for url in catalog_by_id["ar_tabari_qurancom"]["sourceUrls"] if "/an-nisa/" in url]) == 12
    assert len([url for url in catalog_by_id["ar_ibn_kathir_qurancom"]["sourceUrls"] if "/an-nisa/" in url]) == 12
    assert len([url for url in catalog_by_id["ar_tusi_tibyan"]["sourceUrls"] if "TafsirNo=39" in url]) == 12
    assert set(catalog_by_id["ar_fayd_safi"]["sourceUrls"]) == {
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=41&SoraNo=4&AyahNo=61&LanguageID=1",
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=41&SoraNo=4&AyahNo=67&LanguageID=1",
    }
    for source_id in ("ar_tabari_qurancom", "ar_ibn_kathir_qurancom"):
        assert registry_by_id[source_id]["upstreamZipSha256"] in catalog_by_id[source_id]["basis"]
        assert "مقابلهٔ کامل" in catalog_by_id[source_id]["basis"]

    for batch in DOSSIER["batches"]:
        if batch.get("range", "").startswith("4:"):
            assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]
    assert "نساء در این checkout بازهٔ ۴:۱–۱۷۶ را پوشش می‌دهد" in DOSSIER["notice"]


def test_nisa_4_73_84_has_five_tafsirs_two_modern_sources_and_three_models_per_verse():
    expected = {f"4:{ayah}" for ayah in range(73, 85)}
    assert expected <= set(DOSSIER["verses"])
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-38")
    assert batch["range"] == "4:73–84" and batch["count"] == 12
    assert "پیش‌نویسِ نیازمندِ بازبینیِ تخصصی" in batch["status"]
    assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]

    registry = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
    registry_by_id = {source["id"]: source for source in registry["sources"]}
    sunni = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
    shia = {"ar_tusi_tibyan", "ar_fayd_safi"}
    fayd_groups = {
        **{ayah: (73, "۴:۷۳–۷۷") for ayah in range(73, 78)},
        **{ayah: (81, "۴:۷۸–۸۱") for ayah in range(78, 82)},
        **{ayah: (82, "۴:۸۲–۸۵") for ayah in range(82, 85)},
    }

    for ayah in range(73, 85):
        vid = f"4:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) >= 5 for field in FIELDS), vid
        assert len(entry["classical"]) == 5
        assert {item["sourceId"] for item in entry["classical"]} == sunni | shia, vid
        assert sum(item["kind"] == "source-summary" for item in entry["modern"]) == 2
        assert {item["model"] for item in entry["modern"] if item.get("model")} == {
            "izutsu", "fillmore", "cognitive",
        }
        assert any("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid

        source_summaries = [
            item for field in ("classical", "modern") for item in entry[field]
            if item.get("kind") == "source-summary"
        ]
        assert len({item["sourceId"] for item in source_summaries}) == 7
        traditions = [item["tradition"] for item in entry["classical"]]
        assert traditions.count("اهل‌سنت") == 3, vid
        assert traditions.count("شیعهٔ امامیه") == 2, vid
        for source in source_summaries:
            assert source["sourceId"] in registry_by_id
            assert source["tradition"] == registry_by_id[source["sourceId"]].get("tradition")
            assert source["sourceUrl"].startswith("https://")
            assert source["cite"].strip() and source["evidence"].strip() and source["limit"].strip()
            assert len(source["text"].split()) >= MIN_WORDS

        tusi = next(item for item in entry["classical"] if item["sourceId"] == "ar_tusi_tibyan")
        fayd = next(item for item in entry["classical"] if item["sourceId"] == "ar_fayd_safi")
        assert f"TafsirNo=39&SoraNo=4&AyahNo={ayah}&LanguageID=1" in tusi["sourceUrl"]
        fayd_page, fayd_label = fayd_groups[ayah]
        assert f"TafsirNo=41&SoraNo=4&AyahNo={fayd_page}&LanguageID=1" in fayd["sourceUrl"]
        assert fayd_label in fayd["cite"] and fayd_label in fayd["evidence"]

        tafheem = next(item for item in entry["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
        if ayah <= 76:
            tafheem_group, query = "۴:۷۱–۷۶", "verse=71&to=76"
        else:
            tafheem_group, query = "۴:۷۷–۸۷", "verse=77&to=87"
        assert query in tafheem["sourceUrl"]
        assert tafheem_group in tafheem["cite"] and tafheem_group in tafheem["evidence"]
        for field in FIELDS:
            for item in entry[field]:
                assert len(item["text"].split()) >= MIN_WORDS, f"{vid}:{field}: short item"
                assert item["cite"].strip()
                if item.get("sourceUrl"):
                    assert item["sourceUrl"].startswith("https://")

    assert "قولِ دیگر" in next(
        item["text"] for item in DOSSIER["verses"]["4:77"]["classical"]
        if item["sourceId"] == "ar_tusi_tibyan"
    )
    assert "امامانِ معصوم" in next(
        item["text"] for item in DOSSIER["verses"]["4:83"]["classical"]
        if item["sourceId"] == "ar_fayd_safi"
    )
    assert "مجوزِ اقدامِ فردی" in " ".join(
        item["text"] for item in DOSSIER["verses"]["4:84"]["critical"]
    )

    catalog = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
    assert catalog["version"] >= 14
    collection = next(item for item in catalog["collections"] if item["id"] == "nisa-4-73-84-cited")
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ نساء ۴:۷۳–۸۴"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == sunni
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == shia
    assert {item["id"] for item in collection["items"]} == sunni | shia | {
        "ar_qe_arabic_moyassar", "en_tafheem_ul_quran",
    }
    assert all(item["scope"] == "نساء ۴:۷۳–۸۴" for item in collection["items"])
    catalog_by_id = {item["id"]: item for item in collection["items"]}
    assert set(catalog_by_id["en_tafheem_ul_quran"]["sourceUrls"]) == {
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=71&to=76",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=77&to=87",
    }
    assert len([url for url in catalog_by_id["ar_tabari_qurancom"]["sourceUrls"] if "/an-nisa/" in url]) == 12
    assert len([url for url in catalog_by_id["ar_ibn_kathir_qurancom"]["sourceUrls"] if "/an-nisa/" in url]) == 12
    assert len([url for url in catalog_by_id["ar_tusi_tibyan"]["sourceUrls"] if "TafsirNo=39" in url]) == 12
    assert len(catalog_by_id["ar_fayd_safi"]["sourceUrls"]) == 3
    assert "پوششِ آیه‌ایِ نساء به معنای تکمیلِ پژوهشِ تفسیری نیست" in DOSSIER["notice"]


def test_nisa_4_85_96_has_five_tafsirs_two_modern_sources_and_three_models_per_verse():
    expected = {f"4:{ayah}" for ayah in range(85, 97)}
    assert expected <= set(DOSSIER["verses"])
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-39")
    assert batch["range"] == "4:85–96" and batch["count"] == 12
    assert "پیش‌نویسِ نیازمندِ بازبینیِ تخصصی" in batch["status"]
    assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]

    registry = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
    registry_by_id = {source["id"]: source for source in registry["sources"]}
    sunni = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
    shia = {"ar_tusi_tibyan", "ar_fayd_safi"}
    fayd_groups = {
        85: (85, "۴:۸۲–۸۵"),
        86: (86, "۴:۸۶"),
        **{ayah: (87, "۴:۸۷–۹۰") for ayah in range(87, 91)},
        91: (91, "۴:۹۱"),
        92: (92, "۴:۹۲"),
        93: (93, "۴:۹۳–۹۴"),
        94: (93, "۴:۹۳–۹۴"),
        95: (95, "۴:۹۵–۹۶"),
        96: (95, "۴:۹۵–۹۶"),
    }

    for ayah in range(85, 97):
        vid = f"4:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) >= 5 for field in FIELDS), vid
        assert len(entry["classical"]) == 5
        assert {item["sourceId"] for item in entry["classical"]} == sunni | shia, vid
        assert sum(item["kind"] == "source-summary" for item in entry["modern"]) == 2
        assert {item["model"] for item in entry["modern"] if item.get("model")} == {
            "izutsu", "fillmore", "cognitive",
        }
        assert any("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid

        source_summaries = [
            item for field in ("classical", "modern") for item in entry[field]
            if item.get("kind") == "source-summary"
        ]
        assert len({item["sourceId"] for item in source_summaries}) == 7
        traditions = [item["tradition"] for item in entry["classical"]]
        assert traditions.count("اهل‌سنت") == 3, vid
        assert traditions.count("شیعهٔ امامیه") == 2, vid
        for source in source_summaries:
            assert source["sourceId"] in registry_by_id
            assert source["tradition"] == registry_by_id[source["sourceId"]].get("tradition")
            assert source["sourceUrl"].startswith("https://")
            assert source["cite"].strip() and source["evidence"].strip() and source["limit"].strip()
            assert len(source["text"].split()) >= MIN_WORDS

        tusi = next(item for item in entry["classical"] if item["sourceId"] == "ar_tusi_tibyan")
        fayd = next(item for item in entry["classical"] if item["sourceId"] == "ar_fayd_safi")
        assert f"TafsirNo=39&SoraNo=4&AyahNo={ayah}&LanguageID=1" in tusi["sourceUrl"]
        fayd_page, fayd_label = fayd_groups[ayah]
        assert f"TafsirNo=41&SoraNo=4&AyahNo={fayd_page}&LanguageID=1" in fayd["sourceUrl"]
        assert fayd_label in fayd["cite"] and fayd_label in fayd["evidence"]

        tafheem = next(item for item in entry["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
        if ayah <= 87:
            tafheem_group, query = "۴:۷۷–۸۷", "verse=77&to=87"
        elif ayah <= 91:
            tafheem_group, query = "۴:۸۸–۹۱", "verse=88&to=91"
        else:
            tafheem_group, query = "۴:۹۲–۹۶", "verse=92&to=96"
        assert query in tafheem["sourceUrl"]
        assert tafheem_group in tafheem["cite"] and tafheem_group in tafheem["evidence"]
        for field in FIELDS:
            for item in entry[field]:
                assert len(item["text"].split()) >= MIN_WORDS, f"{vid}:{field}: short item"
                assert item["cite"].strip()
                if item.get("sourceUrl"):
                    assert item["sourceUrl"].startswith("https://")

    assert "قرائتِ «السلام/السلم»" in next(
        item["text"] for item in DOSSIER["verses"]["4:94"]["classical"]
        if item["sourceId"] == "ar_tusi_tibyan"
    )
    assert "مشارکت‌کننده در خصومت" in next(
        item["text"] for item in DOSSIER["verses"]["4:89"]["modern"]
        if item.get("sourceId") == "en_tafheem_ul_quran"
    )
    assert "خلود" in " ".join(
        item["text"] for item in DOSSIER["verses"]["4:93"]["critical"]
    )
    assert "قرائت‌های رفع و نصب" in next(
        item["text"] for item in DOSSIER["verses"]["4:95"]["classical"]
        if item["sourceId"] == "ar_tusi_tibyan"
    )
    assert "صد درجه" in next(
        item["text"] for item in DOSSIER["verses"]["4:96"]["classical"]
        if item["sourceId"] == "ar_ibn_kathir_qurancom"
    )

    catalog = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
    assert catalog["version"] >= 15
    collection = next(item for item in catalog["collections"] if item["id"] == "nisa-4-85-96-cited")
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ نساء ۴:۸۵–۹۶"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == sunni
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == shia
    assert {item["id"] for item in collection["items"]} == sunni | shia | {
        "ar_qe_arabic_moyassar", "en_tafheem_ul_quran",
    }
    assert all(item["scope"] == "نساء ۴:۸۵–۹۶" for item in collection["items"])
    catalog_by_id = {item["id"]: item for item in collection["items"]}
    assert set(catalog_by_id["en_tafheem_ul_quran"]["sourceUrls"]) == {
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=77&to=87",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=88&to=91",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=92&to=96",
    }
    assert len([url for url in catalog_by_id["ar_tabari_qurancom"]["sourceUrls"] if "/an-nisa/" in url]) == 12
    assert len([url for url in catalog_by_id["ar_ibn_kathir_qurancom"]["sourceUrls"] if "/an-nisa/" in url]) == 12
    assert len([url for url in catalog_by_id["ar_tusi_tibyan"]["sourceUrls"] if "TafsirNo=39" in url]) == 12
    assert len(catalog_by_id["ar_fayd_safi"]["sourceUrls"]) == 7
    assert "پوششِ آیه‌ایِ نساء به معنای تکمیلِ پژوهشِ تفسیری نیست" in DOSSIER["notice"]


def test_nisa_4_97_108_is_a_scoped_source_linked_batch_with_indexing_note():
    expected = {f"4:{ayah}" for ayah in range(97, 109)}
    assert expected <= set(DOSSIER["verses"])
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-40")
    assert batch["range"] == "4:97–108" and batch["count"] == 12
    assert "پیش‌نویسِ نیازمندِ بازبینیِ تخصصی" in batch["status"]
    assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])

    registry = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
    registry_by_id = {source["id"]: source for source in registry["sources"]}
    sunni = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
    shia = {"ar_tusi_tibyan", "ar_fayd_safi"}
    expected_classical = sunni | shia
    tusi_pages = {
        **{ayah: 97 for ayah in range(97, 100)}, 100: 100, 101: 101, 102: 102,
        103: 103, 104: 104, 105: 105, 106: 105, 107: 107, 108: 108,
    }
    fayd_groups = {
        97: (97, "۴:۹۷"),
        **{ayah: (100, "۴:۹۸–۱۰۰") for ayah in range(98, 101)},
        **{ayah: (101, "۴:۱۰۱–۱۰۲") for ayah in range(101, 103)},
        **{ayah: (103, "۴:۱۰۳–۱۰۴") for ayah in range(103, 105)},
        **{ayah: (105, "۴:۱۰۵–۱۰۸") for ayah in range(105, 109)},
    }
    tafheem_groups = {
        **{ayah: ("۴:۹۷–۱۰۰", "verse=97&to=100") for ayah in range(97, 101)},
        **{ayah: ("۴:۱۰۱–۱۰۴", "verse=101&to=104") for ayah in range(101, 105)},
        **{ayah: ("۴:۱۰۵–۱۱۲", "verse=105&to=112") for ayah in range(105, 109)},
    }

    for ayah in range(97, 109):
        vid = f"4:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) >= 5 for field in FIELDS), vid
        assert {item["sourceId"] for item in entry["classical"]} == expected_classical, vid
        assert sum(item.get("kind") == "source-summary" for item in entry["modern"]) == 2
        assert {item.get("model") for item in entry["modern"] if item.get("model")} == {
            "izutsu", "fillmore", "cognitive",
        }
        assert any("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid

        for field in FIELDS:
            for item in entry[field]:
                assert len(item["text"].split()) >= MIN_WORDS, f"{vid}:{field}: short item"
                assert item["cite"].strip()
                if item.get("sourceUrl"):
                    assert item["sourceUrl"].startswith("https://")

        summaries = [
            item for field in ("classical", "modern") for item in entry[field]
            if item.get("kind") == "source-summary"
        ]
        assert len({item["sourceId"] for item in summaries}) == 7
        assert sum(item["tradition"] == "اهل‌سنت" for item in entry["classical"]) == 3
        assert sum(item["tradition"] == "شیعهٔ امامیه" for item in entry["classical"]) == 2
        for item in summaries:
            assert item["sourceId"] in registry_by_id
            assert item["tradition"] == registry_by_id[item["sourceId"]].get("tradition")
            assert item["evidence"].strip() and item["limit"].strip()

        tusi = next(item for item in entry["classical"] if item["sourceId"] == "ar_tusi_tibyan")
        assert f"TafsirNo=39&SoraNo=4&AyahNo={tusi_pages[ayah]}&LanguageID=1" in tusi["sourceUrl"]
        fayd = next(item for item in entry["classical"] if item["sourceId"] == "ar_fayd_safi")
        fayd_page, fayd_scope = fayd_groups[ayah]
        assert f"TafsirNo=41&SoraNo=4&AyahNo={fayd_page}&LanguageID=1" in fayd["sourceUrl"]
        assert fayd_scope in fayd["cite"] and fayd_scope in fayd["evidence"]
        tafheem = next(item for item in entry["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
        tafheem_scope, query = tafheem_groups[ayah]
        assert query in tafheem["sourceUrl"]
        assert tafheem_scope in tafheem["cite"] and tafheem_scope in tafheem["evidence"]
        assert "صفحهٔ رسمیِ ۴:۴:" not in tafheem["evidence"]

    tabari108 = next(
        item for item in DOSSIER["verses"]["4:108"]["classical"]
        if item["sourceId"] == "ar_tabari_qurancom"
    )
    assert tabari108["sourceUrl"] == "https://quran.com/an-nisa/107/tafsirs/ar-tafsir-al-tabari"
    assert "صفحهٔ آیه‌محورِ ۴:۱۰۷" in tabari108["cite"]
    assert "بخشِ پیوستهٔ ۴:۱۰۸" in tabari108["cite"]
    assert "صفحهٔ ۴:۱۰۸" in tabari108["evidence"]

    catalog = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
    assert catalog["version"] >= 16
    collection = next(item for item in catalog["collections"] if item["id"] == "nisa-4-97-108-cited")
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ نساء ۴:۹۷–۱۰۸"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == sunni
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == shia
    assert all(item["scope"] == "نساء ۴:۹۷–۱۰۸" for item in collection["items"])
    catalog_by_id = {item["id"]: item for item in collection["items"]}
    assert set(catalog_by_id) == expected_classical | {
        "ar_qe_arabic_moyassar", "en_tafheem_ul_quran",
    }
    assert "https://quran.com/an-nisa/107/tafsirs/ar-tafsir-al-tabari" in catalog_by_id[
        "ar_tabari_qurancom"
    ]["sourceUrls"]
    assert "https://quran.com/an-nisa/108/tafsirs/ar-tafsir-al-tabari" not in catalog_by_id[
        "ar_tabari_qurancom"
    ]["sourceUrls"]
    assert set(catalog_by_id["en_tafheem_ul_quran"]["sourceUrls"]) == {
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=97&to=100",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=101&to=104",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=105&to=112",
    }
    assert "نساء در این checkout بازهٔ ۴:۱–۱۷۶ را پوشش می‌دهد" in DOSSIER["notice"]
    assert "پوششِ آیه‌ایِ نساء به معنای تکمیلِ پژوهشِ تفسیری نیست" in DOSSIER["notice"]
    assert "در بستهٔ نساء ۴:۹۷–۱۰۸" in DOSSIER["editorialMethod"]


def test_nisa_4_109_120_is_a_source_scoped_draft_batch():
    expected = {f"4:{ayah}" for ayah in range(109, 121)}
    assert expected <= set(DOSSIER["verses"])
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-41")
    assert batch["range"] == "4:109–120" and batch["count"] == 12
    assert "پیش‌نویسِ نیازمندِ بازبینیِ تخصصی" in batch["status"]
    assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])

    registry = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
    registry_by_id = {source["id"]: source for source in registry["sources"]}
    sunni = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
    shia = {"ar_tusi_tibyan", "ar_fayd_safi"}
    expected_classical = sunni | shia
    fayd_groups = {
        **{ayah: (109, "۴:۱۰۹–۱۱۴") for ayah in range(109, 115)},
        **{ayah: (115, "۴:۱۱۵–۱۲۰") for ayah in range(115, 121)},
    }
    tafheem_groups = {
        **{ayah: ("۴:۱۰۵–۱۱۲", "verse=105&to=112") for ayah in range(109, 113)},
        **{ayah: ("۴:۱۱۳–۱۲۰", "verse=113&to=120") for ayah in range(113, 121)},
    }
    note_map = {
        109: "بی‌یادداشتِ مستقل", 110: "بی‌یادداشتِ مستقل",
        111: "بی‌یادداشتِ مستقل", 112: "بی‌یادداشتِ مستقل",
        113: "یادداشتِ ۱۴۲", 114: "بی‌یادداشتِ مستقل", 115: "یادداشتِ ۱۴۳",
        116: "یادداشتِ ۱۴۴", 117: "یادداشتِ ۱۴۵", 118: "یادداشتِ ۱۴۶",
        119: "یادداشت‌های ۱۴۷–۱۴۸", 120: "یادداشتِ ۱۴۹",
    }

    for ayah in range(109, 121):
        vid = f"4:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) >= 5 for field in FIELDS), vid
        assert {item["sourceId"] for item in entry["classical"]} == expected_classical, vid
        assert sum(item.get("kind") == "source-summary" for item in entry["modern"]) == 2
        assert {item.get("model") for item in entry["modern"] if item.get("model")} == {
            "izutsu", "fillmore", "cognitive",
        }
        assert any("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid

        for field in FIELDS:
            for item in entry[field]:
                assert len(item["text"].split()) >= MIN_WORDS, f"{vid}:{field}: short item"
                assert item["cite"].strip()
                if item.get("sourceUrl"):
                    assert item["sourceUrl"].startswith("https://")

        summaries = [
            item for field in ("classical", "modern") for item in entry[field]
            if item.get("kind") == "source-summary"
        ]
        assert len({item["sourceId"] for item in summaries}) == 7
        assert sum(item["tradition"] == "اهل‌سنت" for item in entry["classical"]) == 3
        assert sum(item["tradition"] == "شیعهٔ امامیه" for item in entry["classical"]) == 2
        for item in summaries:
            assert item["sourceId"] in registry_by_id
            assert item["tradition"] == registry_by_id[item["sourceId"]].get("tradition")
            assert item["evidence"].strip() and item["limit"].strip()

        tabari = next(item for item in entry["classical"] if item["sourceId"] == "ar_tabari_qurancom")
        expected_tabari_page = 120 if ayah == 120 else min(ayah - 1, 118)
        assert f"/an-nisa/{expected_tabari_page}/tafsirs/ar-tafsir-al-tabari" in tabari["sourceUrl"]
        assert f"ذیلِ نساء ۴:{str(ayah).translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))}" in tabari["cite"]
        if ayah == 119:
            assert "/an-nisa/119/tafsirs/ar-tafsir-al-tabari" in tabari["relatedSourceUrls"][0]
            assert "۴:۱۱۸" in tabari["cite"] and "۴:۱۱۹" in tabari["cite"]
        elif ayah < 120:
            assert f"۴:{str(expected_tabari_page).translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))}" in tabari["evidence"]

        tusi = next(item for item in entry["classical"] if item["sourceId"] == "ar_tusi_tibyan")
        assert f"TafsirNo=39&SoraNo=4&AyahNo={ayah}&LanguageID=1" in tusi["sourceUrl"]
        assert f"۴:{str(ayah).translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))}" in tusi["cite"]
        fayd = next(item for item in entry["classical"] if item["sourceId"] == "ar_fayd_safi")
        fayd_page, fayd_scope = fayd_groups[ayah]
        assert f"TafsirNo=41&SoraNo=4&AyahNo={fayd_page}&LanguageID=1" in fayd["sourceUrl"]
        assert fayd_scope in fayd["cite"] and fayd_scope in fayd["evidence"]
        tafheem = next(item for item in entry["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
        tafheem_scope, query = tafheem_groups[ayah]
        assert query in tafheem["sourceUrl"]
        assert tafheem_scope in tafheem["cite"] and tafheem_scope in tafheem["evidence"]
        assert note_map[ayah] in tafheem["cite"]
        if ayah <= 112:
            assert "یادداشت‌های ۱۴۰ و ۱۴۱ ذیلِ ۴:۱۰۵ و ۴:۱۰۷" in tafheem["cite"]
        if ayah == 119:
            assert "یادداشت‌های ۱۴۷–۱۴۸" in tafheem["cite"]

    tabari_119 = next(item for item in DOSSIER["verses"]["4:119"]["classical"] if item["sourceId"] == "ar_tabari_qurancom")
    assert tabari_119["sourceUrl"] == "https://quran.com/an-nisa/118/tafsirs/ar-tafsir-al-tabari"
    assert "https://quran.com/an-nisa/119/tafsirs/ar-tafsir-al-tabari" in tabari_119["relatedSourceUrls"]
    assert "ومن يتخذ الشيطان ولياً" in tabari_119["evidence"]

    catalog = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
    assert catalog["version"] >= 17
    collection = next(item for item in catalog["collections"] if item["id"] == "nisa-4-109-120-cited")
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ نساء ۴:۱۰۹–۱۲۰"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == sunni
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == shia
    assert {item["id"] for item in collection["items"]} == expected_classical | {
        "ar_qe_arabic_moyassar", "en_tafheem_ul_quran",
    }
    assert all(item["scope"] == "نساء ۴:۱۰۹–۱۲۰" for item in collection["items"])
    catalog_by_id = {item["id"]: item for item in collection["items"]}
    assert len(catalog_by_id["ar_tabari_qurancom"]["sourceUrls"]) == 13
    assert len(catalog_by_id["ar_ibn_kathir_qurancom"]["sourceUrls"]) == 12
    assert len(catalog_by_id["ar_jalalayn_qurancom"]["sourceUrls"]) == 12
    assert len(catalog_by_id["ar_tusi_tibyan"]["sourceUrls"]) == 12
    assert len(catalog_by_id["ar_fayd_safi"]["sourceUrls"]) == 2
    assert set(catalog_by_id["en_tafheem_ul_quran"]["sourceUrls"]) == {
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=105&to=112",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=113&to=120",
    }
    assert "نساء در این checkout بازهٔ ۴:۱–۱۷۶ را پوشش می‌دهد" in DOSSIER["notice"]
    assert "پوششِ آیه‌ایِ نساء به معنای تکمیلِ پژوهشِ تفسیری نیست" in DOSSIER["notice"]
    assert "در بستهٔ نساء ۴:۱۰۹–۱۲۰" in DOSSIER["editorialMethod"]


def test_nisa_4_121_132_is_a_source_scoped_draft_batch():
    expected = {f"4:{ayah}" for ayah in range(121, 133)}
    assert expected <= set(DOSSIER["verses"])
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-42")
    assert batch["range"] == "4:121–132" and batch["count"] == 12
    assert "پیش‌نویسِ نیازمندِ بازبینیِ تخصصی" in batch["status"]
    assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])

    registry = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
    registry_by_id = {source["id"]: source for source in registry["sources"]}
    sunni = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
    shia = {"ar_tusi_tibyan", "ar_fayd_safi"}
    expected_classical = sunni | shia
    fayd_groups = {
        **{ayah: (121, "۴:۱۲۱–۱۲۵") for ayah in range(121, 126)},
        126: (126, "۴:۱۲۶"),
        **{ayah: (127, "۴:۱۲۷–۱۲۹") for ayah in range(127, 130)},
        **{ayah: (130, "۴:۱۳۰–۱۳۴") for ayah in range(130, 133)},
    }
    tafheem_groups = {
        **{ayah: ("۴:۱۱۶–۱۲۶", "verse=116&to=126") for ayah in range(121, 127)},
        **{ayah: ("۴:۱۲۷–۱۳۴", "verse=127&to=134") for ayah in range(127, 133)},
    }
    tafheem_notes = {
        **{ayah: "بی‌یادداشتِ مستقل" for ayah in range(121, 126)},
        126: "یادداشت‌های ۱۵۰–۱۵۱",
        127: "یادداشت‌های ۱۵۲–۱۵۶",
        128: "یادداشت‌های ۱۵۷–۱۶۰",
        129: "یادداشت‌های ۱۶۱–۱۶۲",
        **{ayah: "یادداشتِ ۱۶۳ ذیلِ ۴:۱۳۴ و بیرون از بسته" for ayah in range(130, 133)},
    }

    for ayah in range(121, 133):
        vid = f"4:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) >= 5 for field in FIELDS), vid
        assert len(entry["classical"]) == 5
        assert {item["sourceId"] for item in entry["classical"]} == expected_classical
        assert sum(item.get("kind") == "source-summary" for item in entry["modern"]) == 2
        assert {item.get("model") for item in entry["modern"] if item.get("model")} == {
            "izutsu", "fillmore", "cognitive",
        }
        assert any("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid

        for field in FIELDS:
            for item in entry[field]:
                assert len(item["text"].split()) >= MIN_WORDS, f"{vid}:{field}: short item"
                assert item["cite"].strip()
                if item.get("sourceUrl"):
                    assert item["sourceUrl"].startswith("https://")

        summaries = [
            item for field in ("classical", "modern") for item in entry[field]
            if item.get("kind") == "source-summary"
        ]
        assert len({item["sourceId"] for item in summaries}) == 7
        assert sum(item["tradition"] == "اهل‌سنت" for item in entry["classical"]) == 3
        assert sum(item["tradition"] == "شیعهٔ امامیه" for item in entry["classical"]) == 2
        for source in summaries:
            assert source["sourceId"] in registry_by_id
            assert source["tradition"] == registry_by_id[source["sourceId"]].get("tradition")
            assert source["evidence"].strip() and source["limit"].strip()

        for source_id, slug in (
            ("ar_tabari_qurancom", "ar-tafsir-al-tabari"),
            ("ar_ibn_kathir_qurancom", "ar-tafsir-ibn-kathir"),
            ("ar_jalalayn_qurancom", "ar-tafsir-jalalayn"),
        ):
            item = next(item for item in entry["classical"] if item["sourceId"] == source_id)
            assert f"/an-nisa/{ayah}/tafsirs/{slug}" in item["sourceUrl"]

        tusi = next(item for item in entry["classical"] if item["sourceId"] == "ar_tusi_tibyan")
        assert f"TafsirNo=39&SoraNo=4&AyahNo={ayah}&LanguageID=1" in tusi["sourceUrl"]
        if ayah == 121:
            assert "۴:۱۱۹–۱۲۱" in tusi["cite"] and "۴:۱۱۹–۱۲۱" in tusi["evidence"]
        elif ayah in (131, 132):
            assert "۴:۱۳۱–۱۳۴" in tusi["cite"] and "۴:۱۳۱–۱۳۴" in tusi["evidence"]
        else:
            persian_ayah = str(ayah).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
            assert f"۴:{persian_ayah}" in tusi["cite"]

        fayd = next(item for item in entry["classical"] if item["sourceId"] == "ar_fayd_safi")
        fayd_page, fayd_scope = fayd_groups[ayah]
        assert f"TafsirNo=41&SoraNo=4&AyahNo={fayd_page}&LanguageID=1" in fayd["sourceUrl"]
        assert fayd_scope in fayd["cite"] and fayd_scope in fayd["evidence"]

        tafheem = next(item for item in entry["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
        tafheem_scope, query = tafheem_groups[ayah]
        assert query in tafheem["sourceUrl"]
        assert tafheem_scope in tafheem["cite"] and tafheem_scope in tafheem["evidence"]
        assert tafheem_notes[ayah] in tafheem["cite"]

        moyassar = next(item for item in entry["modern"] if item.get("sourceId") == "ar_qe_arabic_moyassar")
        assert "1.0.0" in moyassar["cite"]
        assert "۴:" in moyassar["cite"]

    catalog = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
    assert catalog["version"] >= 18
    collection = next(item for item in catalog["collections"] if item["id"] == "nisa-4-121-132-cited")
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ نساء ۴:۱۲۱–۱۳۲"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == sunni
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == shia
    assert {item["id"] for item in collection["items"]} == expected_classical | {
        "ar_qe_arabic_moyassar", "en_tafheem_ul_quran",
    }
    assert all(item["scope"] == "نساء ۴:۱۲۱–۱۳۲" for item in collection["items"])
    catalog_by_id = {item["id"]: item for item in collection["items"]}
    assert len(catalog_by_id["ar_tabari_qurancom"]["sourceUrls"]) == 12
    assert len(catalog_by_id["ar_ibn_kathir_qurancom"]["sourceUrls"]) == 12
    assert len(catalog_by_id["ar_jalalayn_qurancom"]["sourceUrls"]) == 12
    assert len(catalog_by_id["ar_tusi_tibyan"]["sourceUrls"]) == 12
    assert len(catalog_by_id["ar_fayd_safi"]["sourceUrls"]) == 4
    assert set(catalog_by_id["en_tafheem_ul_quran"]["sourceUrls"]) == {
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=116&to=126",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=127&to=134",
    }
    assert "نساء در این checkout بازهٔ ۴:۱–۱۷۶ را پوشش می‌دهد" in DOSSIER["notice"]
    assert "پوششِ آیه‌ایِ نساء به معنای تکمیلِ پژوهشِ تفسیری نیست" in DOSSIER["notice"]
    assert "یادداشتِ ۱۶۳ ذیلِ ۴:۱۳۴" in DOSSIER["notice"] or "یادداشتِ ۱۶۳" in DOSSIER["editorialMethod"]
    assert "در بستهٔ نساء ۴:۱۲۱–۱۳۲" in DOSSIER["editorialMethod"]


def test_nisa_4_133_144_is_a_source_scoped_draft_batch():
    expected = {f"4:{ayah}" for ayah in range(133, 145)}
    assert expected <= set(DOSSIER["verses"])
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-43")
    assert batch["range"] == "4:133–144" and batch["count"] == 12
    assert "پیش‌نویسِ نیازمندِ بازبینیِ تخصصی" in batch["status"]
    assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])

    registry = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
    registry_by_id = {source["id"]: source for source in registry["sources"]}
    sunni = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
    shia = {"ar_tusi_tibyan", "ar_fayd_safi"}
    expected_classical = sunni | shia
    tusi_groups = {
        133: (133, "۴:۱۳۱–۱۳۴"), 134: (133, "۴:۱۳۱–۱۳۴"),
        135: (135, "۴:۱۳۵"), 136: (136, "۴:۱۳۶"), 137: (137, "۴:۱۳۷"),
        138: (138, "۴:۱۳۸–۱۳۹"), 139: (138, "۴:۱۳۸–۱۳۹"),
        140: (140, "۴:۱۴۰"), 141: (141, "۴:۱۴۱"),
        142: (142, "۴:۱۴۰–۱۴۳"), 143: (142, "۴:۱۴۰–۱۴۳"), 144: (144, "۴:۱۴۴"),
    }
    fayd_groups = {
        133: (133, "۴:۱۳۰–۱۳۴"), 134: (133, "۴:۱۳۰–۱۳۴"),
        **{ayah: (135, "۴:۱۳۵–۱۳۹") for ayah in range(135, 140)},
        **{ayah: (142, "۴:۱۴۰–۱۴۳") for ayah in range(140, 144)},
        144: (144, "۴:۱۴۴–۱۵۱"),
    }
    tafheem_groups = {
        **{ayah: ("۴:۱۲۷–۱۳۴", "verse=127&to=134") for ayah in (133, 134)},
        **{ayah: ("۴:۱۳۵–۱۴۱", "verse=135&to=141") for ayah in range(135, 142)},
        **{ayah: ("۴:۱۴۲–۱۵۲", "verse=142&to=152") for ayah in range(142, 145)},
    }
    tafheem_notes = {
        133: "یادداشتِ ۱۶۳ ذیلِ ۴:۱۳۴ و مرتبط با ۴:۱۳۳ در سیاق",
        134: "یادداشتِ ۱۶۳",
        135: "یادداشت‌های ۱۶۴–۱۶۵",
        136: "یادداشت‌های ۱۶۶–۱۶۷",
        137: "یادداشتِ ۱۶۸",
        138: "ترجمهٔ گروهی، بدونِ یادداشتِ مستقل",
        139: "یادداشتِ ۱۶۹",
        140: "یادداشتِ ۱۷۰",
        141: "یادداشتِ ۱۷۱",
        142: "یادداشتِ ۱۷۲",
        143: "یادداشتِ ۱۷۳",
        144: "ترجمهٔ گروهی، بدونِ یادداشتِ مستقل؛ یادداشتِ ۱۷۴ ذیلِ ۴:۱۴۶ است",
    }

    for ayah in range(133, 145):
        vid = f"4:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) == 5 for field in FIELDS), vid
        assert len(entry["classical"]) == 5
        assert {item["sourceId"] for item in entry["classical"]} == expected_classical
        assert sum(item.get("kind") == "source-summary" for item in entry["modern"]) == 2
        assert {item.get("model") for item in entry["modern"] if item.get("model")} == {
            "izutsu", "fillmore", "cognitive",
        }
        assert any("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid

        for field in FIELDS:
            for item in entry[field]:
                assert len(item["text"].split()) >= MIN_WORDS, f"{vid}:{field}: short item"
                assert item["cite"].strip()
                if item.get("sourceUrl"):
                    assert item["sourceUrl"].startswith("https://")

        summaries = [
            item for field in ("classical", "modern") for item in entry[field]
            if item.get("kind") == "source-summary"
        ]
        assert len({item["sourceId"] for item in summaries}) == 7
        assert sum(item["tradition"] == "اهل‌سنت" for item in entry["classical"]) == 3
        assert sum(item["tradition"] == "شیعهٔ امامیه" for item in entry["classical"]) == 2
        for source in summaries:
            assert source["sourceId"] in registry_by_id
            assert source["tradition"] == registry_by_id[source["sourceId"]].get("tradition")
            assert source["evidence"].strip() and source["limit"].strip()

        for source_id, slug in (
            ("ar_tabari_qurancom", "ar-tafsir-al-tabari"),
            ("ar_ibn_kathir_qurancom", "ar-tafsir-ibn-kathir"),
            ("ar_jalalayn_qurancom", "ar-tafsir-jalalayn"),
        ):
            item = next(item for item in entry["classical"] if item["sourceId"] == source_id)
            assert f"/an-nisa/{ayah}/tafsirs/{slug}" in item["sourceUrl"]

        tusi = next(item for item in entry["classical"] if item["sourceId"] == "ar_tusi_tibyan")
        tusi_page, tusi_scope = tusi_groups[ayah]
        assert f"TafsirNo=39&SoraNo=4&AyahNo={tusi_page}&LanguageID=1" in tusi["sourceUrl"]
        assert tusi_scope in tusi["cite"] and tusi_scope in tusi["evidence"]

        fayd = next(item for item in entry["classical"] if item["sourceId"] == "ar_fayd_safi")
        fayd_page, fayd_scope = fayd_groups[ayah]
        assert f"TafsirNo=41&SoraNo=4&AyahNo={fayd_page}&LanguageID=1" in fayd["sourceUrl"]
        assert fayd_scope in fayd["cite"] and fayd_scope in fayd["evidence"]

        tafheem = next(item for item in entry["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
        tafheem_scope, query = tafheem_groups[ayah]
        assert query in tafheem["sourceUrl"]
        assert tafheem_scope in tafheem["cite"] and tafheem_scope in tafheem["evidence"]
        assert tafheem_notes[ayah] in tafheem["cite"]

        moyassar = next(item for item in entry["modern"] if item.get("sourceId") == "ar_qe_arabic_moyassar")
        assert "1.0.0" in moyassar["cite"]

    tabari_134 = next(item for item in DOSSIER["verses"]["4:134"]["classical"] if item["sourceId"] == "ar_tabari_qurancom")
    ibn_134 = next(item for item in DOSSIER["verses"]["4:134"]["classical"] if item["sourceId"] == "ar_ibn_kathir_qurancom")
    assert "منافق" in tabari_134["text"] and "منافق" in ibn_134["text"]
    assert "فراگیر" in ibn_134["text"]
    tabari_141 = next(item for item in DOSSIER["verses"]["4:141"]["classical"] if item["sourceId"] == "ar_tabari_qurancom")
    ibn_141 = next(item for item in DOSSIER["verses"]["4:141"]["classical"] if item["sourceId"] == "ar_ibn_kathir_qurancom")
    assert "حجتِ آخرت" in tabari_141["text"]
    assert "سلطهٔ نهایی" in ibn_141["text"]

    catalog = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
    assert catalog["version"] >= 19
    collection = next(item for item in catalog["collections"] if item["id"] == "nisa-4-133-144-cited")
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ نساء ۴:۱۳۳–۱۴۴"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == sunni
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == shia
    assert {item["id"] for item in collection["items"]} == expected_classical | {
        "ar_qe_arabic_moyassar", "en_tafheem_ul_quran",
    }
    assert all(item["scope"] == "نساء ۴:۱۳۳–۱۴۴" for item in collection["items"])
    catalog_by_id = {item["id"]: item for item in collection["items"]}
    assert len(catalog_by_id["ar_tabari_qurancom"]["sourceUrls"]) == 12
    assert len(catalog_by_id["ar_ibn_kathir_qurancom"]["sourceUrls"]) == 12
    assert len(catalog_by_id["ar_jalalayn_qurancom"]["sourceUrls"]) == 12
    assert len(catalog_by_id["ar_tusi_tibyan"]["sourceUrls"]) == 9
    assert len(catalog_by_id["ar_fayd_safi"]["sourceUrls"]) == 4
    assert set(catalog_by_id["en_tafheem_ul_quran"]["sourceUrls"]) == {
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=127&to=134",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=135&to=141",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=142&to=152",
    }
    assert "نساء در این checkout بازهٔ ۴:۱–۱۷۶ را پوشش می‌دهد" in DOSSIER["notice"]
    assert "پوششِ آیه‌ایِ نساء به معنای تکمیلِ پژوهشِ تفسیری نیست" in DOSSIER["notice"]
    assert "در بستهٔ نساء ۴:۱۳۳–۱۴۴" in DOSSIER["editorialMethod"]


def test_nisa_4_145_156_preserves_source_ranges_and_disagreement():
    expected = {f"4:{ayah}" for ayah in range(145, 157)}
    assert expected <= set(DOSSIER["verses"])
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(batch for batch in DOSSIER["batches"] if batch["id"] == "dossier-44")
    assert batch["range"] == "4:145–156" and batch["count"] == 12
    assert "پیش‌نویسِ نیازمندِ بازبینیِ تخصصی" in batch["status"]
    assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])

    registry = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
    registry_by_id = {source["id"]: source for source in registry["sources"]}
    sunni = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
    shia = {"ar_tusi_tibyan", "ar_fayd_safi"}
    expected_classical = sunni | shia
    tusi_groups = {
        145: (145, "۴:۱۴۵–۱۴۶"), 146: (145, "۴:۱۴۵–۱۴۶"),
        147: (147, "۴:۱۴۷"), 148: (148, "۴:۱۴۸"), 149: (149, "۴:۱۴۹"),
        150: (150, "۴:۱۵۰–۱۵۱"), 151: (150, "۴:۱۵۰–۱۵۱"),
        152: (152, "۴:۱۵۲"), 153: (153, "۴:۱۵۳"), 154: (154, "۴:۱۵۴"),
        155: (156, "۴:۱۵۵–۱۵۶"), 156: (156, "۴:۱۵۵–۱۵۶"),
    }
    fayd_groups = {
        **{ayah: (144, "۴:۱۴۴–۱۵۱") for ayah in range(145, 152)},
        **{ayah: (152, "۴:۱۵۲–۱۵۷") for ayah in range(152, 157)},
    }
    tafheem_groups = {
        **{ayah: ("۴:۱۴۲–۱۵۲", "verse=142&to=152") for ayah in range(145, 153)},
        **{ayah: ("۴:۱۵۳–۱۶۲", "verse=153&to=162") for ayah in range(153, 157)},
    }
    tafheem_notes = {
        145: "ترجمهٔ گروهی، بدونِ یادداشتِ مستقل",
        146: "یادداشتِ ۱۷۴",
        147: "یادداشت‌های ۱۷۵–۱۷۶",
        148: "ترجمهٔ گروهی، بدونِ یادداشتِ مستقل",
        149: "یادداشتِ ۱۷۷",
        150: "ترجمهٔ گروهی، بدونِ یادداشتِ مستقل",
        151: "یادداشتِ ۱۷۸",
        152: "یادداشت‌های ۱۷۹–۱۸۰",
        153: "یادداشت‌های ۱۸۱–۱۸۳",
        154: "یادداشت‌های ۱۸۴–۱۸۶",
        155: "یادداشت‌های ۱۸۷–۱۸۸",
        156: "یادداشت‌های ۱۸۹–۱۹۰",
    }

    for ayah in range(145, 157):
        vid = f"4:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) == 5 for field in FIELDS), vid
        assert len(entry["classical"]) == 5
        assert {item["sourceId"] for item in entry["classical"]} == expected_classical
        assert sum(item.get("kind") == "source-summary" for item in entry["modern"]) == 2
        assert {item.get("model") for item in entry["modern"] if item.get("model")} == {
            "izutsu", "fillmore", "cognitive",
        }
        assert any("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid

        for field in FIELDS:
            for item in entry[field]:
                assert len(item["text"].split()) >= MIN_WORDS, f"{vid}:{field}: short item"
                assert item["cite"].strip()
                if item.get("sourceUrl"):
                    assert item["sourceUrl"].startswith("https://")

        summaries = [
            item for field in ("classical", "modern") for item in entry[field]
            if item.get("kind") == "source-summary"
        ]
        assert len({item["sourceId"] for item in summaries}) == 7
        assert sum(item["tradition"] == "اهل‌سنت" for item in entry["classical"]) == 3
        assert sum(item["tradition"] == "شیعهٔ امامیه" for item in entry["classical"]) == 2
        for source in summaries:
            assert source["sourceId"] in registry_by_id
            assert source["tradition"] == registry_by_id[source["sourceId"]].get("tradition")
            assert source["evidence"].strip() and source["limit"].strip()

        tusi = next(item for item in entry["classical"] if item["sourceId"] == "ar_tusi_tibyan")
        tusi_page, tusi_scope = tusi_groups[ayah]
        assert f"TafsirNo=39&SoraNo=4&AyahNo={tusi_page}&LanguageID=1" in tusi["sourceUrl"]
        assert tusi_scope in tusi["cite"] and tusi_scope in tusi["evidence"]

        fayd = next(item for item in entry["classical"] if item["sourceId"] == "ar_fayd_safi")
        fayd_page, fayd_scope = fayd_groups[ayah]
        assert f"TafsirNo=41&SoraNo=4&AyahNo={fayd_page}&LanguageID=1" in fayd["sourceUrl"]
        assert fayd_scope in fayd["cite"] and fayd_scope in fayd["evidence"]

        tafheem = next(item for item in entry["modern"] if item.get("sourceId") == "en_tafheem_ul_quran")
        tafheem_scope, query = tafheem_groups[ayah]
        assert query in tafheem["sourceUrl"]
        assert tafheem_scope in tafheem["cite"] and tafheem_scope in tafheem["evidence"]
        assert tafheem_notes[ayah] in tafheem["cite"]

        moyassar = next(item for item in entry["modern"] if item.get("sourceId") == "ar_qe_arabic_moyassar")
        assert "1.0.0" in moyassar["cite"]

    catalog = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))
    assert catalog["version"] >= 20
    collection = next(item for item in catalog["collections"] if item["id"] == "nisa-4-145-156-cited")
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ نساء ۴:۱۴۵–۱۵۶"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == sunni
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == shia
    assert all(item["scope"] == "نساء ۴:۱۴۵–۱۵۶" for item in collection["items"])
    catalog_by_id = {item["id"]: item for item in collection["items"]}
    assert set(catalog_by_id) == expected_classical | {"ar_qe_arabic_moyassar", "en_tafheem_ul_quran"}
    assert len(catalog_by_id["ar_tabari_qurancom"]["sourceUrls"]) == 12
    assert len(catalog_by_id["ar_ibn_kathir_qurancom"]["sourceUrls"]) == 12
    assert len(catalog_by_id["ar_jalalayn_qurancom"]["sourceUrls"]) == 12
    assert len(catalog_by_id["ar_tusi_tibyan"]["sourceUrls"]) == 9
    assert len(catalog_by_id["ar_fayd_safi"]["sourceUrls"]) == 2
    assert set(catalog_by_id["en_tafheem_ul_quran"]["sourceUrls"]) == {
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=142&to=152",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=153&to=162",
    }

    ta = DOSSIER["verses"]["4:148"]["classical"]
    tabari_148 = next(item for item in ta if item["sourceId"] == "ar_tabari_qurancom")
    assert "قرائتِ مشهور" in tabari_148["text"] and "ظُلِم" in tabari_148["text"]
    tusi_148 = next(item for item in ta if item["sourceId"] == "ar_tusi_tibyan")
    fayd_148 = next(item for item in ta if item["sourceId"] == "ar_fayd_safi")
    assert "قرائت" in tusi_148["text"] and "روایت" in fayd_148["text"]

    ta = DOSSIER["verses"]["4:151"]["classical"]
    assert "قمی" in next(item for item in ta if item["sourceId"] == "ar_fayd_safi")["text"]
    ta = DOSSIER["verses"]["4:153"]["classical"]
    assert "رؤیت" in next(item for item in ta if item["sourceId"] == "ar_tusi_tibyan")["text"]
    ta = DOSSIER["verses"]["4:155"]["classical"]
    assert "اندک" in next(item for item in ta if item["sourceId"] == "ar_tabari_qurancom")["text"]
    assert "نیاکان" in next(item for item in ta if item["sourceId"] == "ar_fayd_safi")["text"]
    ta = DOSSIER["verses"]["4:156"]["classical"]
    assert "یوسفِ نجار" in next(item for item in ta if item["sourceId"] == "ar_fayd_safi")["text"]
    assert "نساء در این checkout بازهٔ ۴:۱–۱۷۶ را پوشش می‌دهد" in DOSSIER["notice"]
    assert "پوششِ آیه‌ایِ نساء به معنای تکمیلِ پژوهشِ تفسیری نیست" in DOSSIER["notice"]
    assert "در بستهٔ نساء ۴:۱۴۵–۱۵۶" in DOSSIER["editorialMethod"]
