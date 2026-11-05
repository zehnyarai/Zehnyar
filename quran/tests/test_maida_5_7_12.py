# -*- coding: utf-8 -*-
"""Targeted validation for the source-scoped Al-Ma'idah 5:7–12 batch."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = json.loads((ROOT / "static" / "verse-dossiers.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))

SUNNI = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
SHIA = {"ar_tusi_tibyan", "ar_fayd_safi"}
MODERN_COMMON = {"ar_qe_arabic_moyassar", "en_tafheem_ul_quran"}
MODERN_WITH_WASIT = {"ar_qe_arabic_moyassar", "ar_wasit_qurancom"}
MODELS = {"izutsu", "fillmore", "cognitive"}
FIELDS = ("notes", "context", "classical", "modern", "critical", "research")


def _by_source(items):
    return {item["sourceId"]: item for item in items if item.get("sourceId")}


def test_maida_5_7_12_has_six_complete_drafts_and_balanced_source_families():
    expected = {f"5:{ayah}" for ayah in range(7, 13)}
    assert expected <= set(DOSSIER["verses"])
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-48")
    assert batch["range"] == "5:7–12" and batch["count"] == 6
    assert "پیش‌نویسِ نیازمندِ داوریِ تخصصی" in batch["status"]
    assert "در زمانِ ثبتِ این بسته، مائده تا ۵:۱۲ پوشش داشت" in batch["status"]
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    assert "بسته‌های مائده ۵:۱–۶، ۵:۷–۱۲، ۵:۱۳–۱۸، ۵:۱۹–۲۴، ۵:۲۵–۳۰، ۵:۳۱–۳۶، ۵:۳۷–۴۲، ۵:۴۳–۴۸، ۵:۴۹–۵۴، ۵:۵۵–۶۰، ۵:۶۱–۱۱۰ و ۵:۱۱۱–۱۲۰ افزوده شده‌اند" in DOSSIER["notice"]
    assert "انعام بازهٔ ۶:۱–۱۶۵ را پوشش می‌دهد و اکنون کامل است" in DOSSIER["notice"]

    registry_by_id = {item["id"]: item for item in REGISTRY["sources"]}
    for ayah in range(7, 13):
        vid = f"5:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) == 5 for field in FIELDS), vid
        assert {item["sourceId"] for item in entry["classical"]} == SUNNI | SHIA
        assert sum(item["tradition"] == "اهل‌سنت" for item in entry["classical"]) == 3
        assert sum(item["tradition"] == "شیعهٔ امامیه" for item in entry["classical"]) == 2
        expected_modern = MODERN_WITH_WASIT if ayah in (9, 10) else MODERN_COMMON
        assert {item["sourceId"] for item in entry["modern"] if item.get("kind") == "source-summary"} == expected_modern
        assert {item["model"] for item in entry["modern"] if item.get("model")} == MODELS
        assert any("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid
        for field in FIELDS:
            for record in entry[field]:
                assert len(record["text"].split()) >= 14, f"{vid}:{field}: بند کوتاه"
                assert record["cite"].strip(), f"{vid}:{field}: ارجاع خالی"
                if record.get("sourceUrl"):
                    assert record["sourceUrl"].startswith("https://")
        for record in entry["classical"] + [x for x in entry["modern"] if x.get("kind") == "source-summary"]:
            sid = record["sourceId"]
            assert sid in registry_by_id
            assert record["tradition"] == registry_by_id[sid]["tradition"]
            assert record["evidence"].strip() and record["limit"].strip()


def test_maida_5_7_12_records_direct_verses_and_real_grouped_page_ranges():
    fayd_groups = {
        7: (7, "۵:۶–۷"),
        **{ayah: (ayah, "۵:۸–۱۴") for ayah in range(8, 13)},
    }
    tafheem_groups = {
        **{ayah: ("۵:۶–۱۱", "verse=6&to=11") for ayah in range(7, 12)},
        12: ("۵:۱۲–۱۹", "verse=12&to=19"),
    }
    tafheem_note_labels = {
        7: "یادداشتِ ۲۸",
        8: "یادداشتِ ۲۹",
        9: "ترجمهٔ آیه؛ بی‌یادداشتِ مستقل",
        10: "ترجمهٔ آیه؛ بی‌یادداشتِ مستقل",
        11: "یادداشتِ ۳۰",
        12: "یادداشت‌های ۳۱–۳۵",
    }
    for ayah in range(7, 13):
        entry = DOSSIER["verses"][f"5:{ayah}"]
        classical = _by_source(entry["classical"])
        for sid, tafsir_no in (("ar_tusi_tibyan", 39), ("ar_fayd_safi", 41)):
            record = classical[sid]
            page = ayah if sid == "ar_tusi_tibyan" else fayd_groups[ayah][0]
            assert f"TafsirNo={tafsir_no}&SoraNo=5&AyahNo={page}&LanguageID=1" in record["sourceUrl"]
        assert f"AyahNo={ayah}" in classical["ar_tusi_tibyan"]["cite"]
        fayd_scope = fayd_groups[ayah][1]
        assert fayd_scope in classical["ar_fayd_safi"]["cite"]
        assert fayd_scope in classical["ar_fayd_safi"]["evidence"]
        for sid in SUNNI:
            assert f"/al-maidah/{ayah}/tafsirs/" in classical[sid]["sourceUrl"]

        range_label, query = tafheem_groups[ayah]
        if ayah in (9, 10):
            wasit = _by_source(entry["modern"])["ar_wasit_qurancom"]
            assert wasit["sourceUrl"] == f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-al-wasit"
            assert "طنطاوی" in wasit["cite"] and range_label not in wasit["cite"]
            assert "التفسير الوسيط" in wasit["text"] or "طنطاوی" in wasit["text"]
            assert any(
                "بی‌یادداشتِ مستقل" in record["cite"] and "مودودی" in record["cite"]
                for field in FIELDS for record in entry[field]
            )
            assert "en_tafheem_ul_quran" not in _by_source(entry["modern"])
        else:
            tafheem = _by_source(entry["modern"])["en_tafheem_ul_quran"]
            assert query in tafheem["sourceUrl"]
            assert range_label in tafheem["cite"] and tafheem_note_labels[ayah] in tafheem["cite"]
            assert range_label in tafheem["evidence"]

    collection = next(item for item in CATALOG["collections"] if item["id"] == "maida-5-7-12-cited")
    assert CATALOG["version"] >= 25
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ مائده ۵:۷–۱۲"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == SUNNI
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == SHIA
    assert all(
        item["scope"] == ("مائده ۵:۹–۱۰" if item["id"] == "ar_wasit_qurancom" else "مائده ۵:۷–۱۲")
        for item in collection["items"]
    )
    by_id = {item["id"]: item for item in collection["items"]}
    for sid in SUNNI | SHIA:
        assert len(by_id[sid]["sourceUrls"]) == 6
    assert len(by_id["en_tafheem_ul_quran"]["sourceUrls"]) == 2
    assert len(by_id["ar_qe_arabic_moyassar"]["sourceUrls"]) == 1
    assert set(by_id["ar_wasit_qurancom"]["sourceUrls"]) == {
        f"https://quran.com/al-maidah/{ayah}/tafsirs/ar-tafsir-al-wasit" for ayah in (9, 10)
    }
    assert by_id["ar_wasit_qurancom"]["basis"] and by_id["ar_wasit_qurancom"]["scope"] == "مائده ۵:۹–۱۰"
    assert next(item for item in REGISTRY["sources"] if item["id"] == "ar_wasit_qurancom")["sourceType"] == "modern-tafsir"
    assert "دو شرحِ معاصر" in collection["comparativeCore"]["note"]
    assert "ترجمهٔ مستقیم فقط به‌عنوان شاهدِ مکمل می‌آید" in by_id["en_tafheem_ul_quran"]["basis"]


def test_maida_5_7_12_keeps_differences_in_attribution_and_does_not_overclaim():
    verses = DOSSIER["verses"]
    s7 = verses["5:7"]["classical"]
    assert "عهدِ ذرّ" in _by_source(s7)["ar_tabari_qurancom"]["text"]
    assert "ولایت" in _by_source(s7)["ar_fayd_safi"]["text"]
    s8 = verses["5:8"]["classical"]
    assert "خیبر" in _by_source(s8)["ar_tabari_qurancom"]["text"]
    assert "بنی‌قریظه" in _by_source(s8)["ar_tusi_tibyan"]["text"]
    s9 = verses["5:9"]["classical"]
    assert "ساختِ نحوی" in _by_source(s9)["ar_tabari_qurancom"]["text"]
    assert "رحمت و فضل" in _by_source(s9)["ar_ibn_kathir_qurancom"]["text"]
    s10 = verses["5:10"]["classical"]
    assert "کفرِ ردّه" in _by_source(s10)["ar_tusi_tibyan"]["text"]
    s11 = verses["5:11"]["classical"]
    assert "بنی‌نضیر" in _by_source(s11)["ar_tabari_qurancom"]["text"]
    assert "غورث بن حارث" in _by_source(s11)["ar_ibn_kathir_qurancom"]["text"]
    assert "قریش" in _by_source(s11)["ar_jalalayn_qurancom"]["text"]
    assert "اهلِ مکه" in _by_source(s11)["ar_fayd_safi"]["text"]
    s12 = verses["5:12"]["classical"]
    assert "کفیِل" in _by_source(s12)["ar_tabari_qurancom"]["text"]
    assert "ضامن، امین، شاهد و رئیس" in _by_source(s12)["ar_tusi_tibyan"]["text"]
    assert "دوازده خلیفه" in _by_source(s12)["ar_ibn_kathir_qurancom"]["text"]
    assert "در بستهٔ مائده ۵:۷–۱۲" in DOSSIER["editorialMethod"]
