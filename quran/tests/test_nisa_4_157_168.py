# -*- coding: utf-8 -*-
"""Targeted validation for the source-scoped An-Nisa 4:157–168 batch."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = json.loads((ROOT / "static" / "verse-dossiers.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "static" / "tafsir-sources.json").read_text(encoding="utf-8"))
CATALOG = json.loads((ROOT / "static" / "tafsir-catalog.json").read_text(encoding="utf-8"))

SUNNI = {"ar_tabari_qurancom", "ar_ibn_kathir_qurancom", "ar_jalalayn_qurancom"}
SHIA = {"ar_tusi_tibyan", "ar_fayd_safi"}
FIELDS = ("notes", "context", "classical", "modern", "critical", "research")


def _by_source(items):
    return {item["sourceId"]: item for item in items if item.get("sourceId")}


def test_nisa_4_157_168_has_scoped_complete_dossiers_and_source_balance():
    expected = {f"4:{ayah}" for ayah in range(157, 169)}
    assert expected <= set(DOSSIER["verses"])
    assert len(DOSSIER["verses"]) >= 697
    batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-45")
    assert batch["range"] == "4:157–168" and batch["count"] == 12
    assert "پیش‌نویسِ نیازمندِ بازبینیِ تخصصی" in batch["status"]
    assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])

    registry_by_id = {item["id"]: item for item in REGISTRY["sources"]}
    for ayah in range(157, 169):
        vid = f"4:{ayah}"
        entry = DOSSIER["verses"][vid]
        assert entry["status"].startswith("پیش‌نویس")
        assert "بازبینیِ تخصصی انجام نشده" in entry["status"]
        assert entry["standard"] == 2
        assert all(len(entry[field]) == 5 for field in FIELDS), vid
        assert {item["sourceId"] for item in entry["classical"]} == SUNNI | SHIA
        assert sum(item["tradition"] == "اهل‌سنت" for item in entry["classical"]) == 3
        assert sum(item["tradition"] == "شیعهٔ امامیه" for item in entry["classical"]) == 2
        assert {item["sourceId"] for item in entry["modern"] if item.get("kind") == "source-summary"} == {
            "ar_qe_arabic_moyassar", "en_tafheem_ul_quran",
        }
        assert {item["model"] for item in entry["modern"] if item.get("model")} == {
            "izutsu", "fillmore", "cognitive",
        }
        assert any("فولادوند/Tanzil" in item["cite"] for item in entry["notes"]), vid

        for field in FIELDS:
            for item in entry[field]:
                assert len(item["text"].split()) >= 14, f"{vid}:{field}: بند کوتاه"
                assert item["cite"].strip(), f"{vid}:{field}: ارجاع خالی"
                if item.get("sourceUrl"):
                    assert item["sourceUrl"].startswith("https://")

        for item in entry["classical"] + [x for x in entry["modern"] if x.get("kind") == "source-summary"]:
            sid = item["sourceId"]
            assert sid in registry_by_id
            assert item["tradition"] == registry_by_id[sid]["tradition"]
            assert item["evidence"].strip() and item["limit"].strip()


def test_nisa_4_157_168_preserves_actual_source_ranges_and_page_groups():
    tusi_groups = {
        157: (157, "۴:۱۵۷–۱۵۸"), 158: (157, "۴:۱۵۷–۱۵۸"), 159: (159, "۴:۱۵۹"),
        160: (161, "۴:۱۶۰–۱۶۱"), 161: (161, "۴:۱۶۰–۱۶۱"), 162: (162, "۴:۱۶۲"),
        163: (163, "۴:۱۶۳"), 164: (164, "۴:۱۶۴"), 165: (165, "۴:۱۶۵"),
        166: (166, "۴:۱۶۶"), 167: (167, "۴:۱۶۷"), 168: (169, "۴:۱۶۸–۱۶۹"),
    }
    fayd_groups = {
        157: (152, "۴:۱۵۲–۱۵۷"), 158: (158, "۴:۱۵۸–۱۵۹"), 159: (158, "۴:۱۵۸–۱۵۹"),
        **{ayah: (160, "۴:۱۶۰–۱۶۴") for ayah in range(160, 165)},
        **{ayah: (165, "۴:۱۶۵–۱۷۱") for ayah in range(165, 169)},
    }
    tafheem_groups = {
        157: ("۴:۱۵۷–۱۵۸", "verse=157&to=158"), 158: ("۴:۱۵۷–۱۵۸", "verse=157&to=158"),
        **{ayah: ("۴:۱۵۹–۱۶۲", "verse=159&to=162") for ayah in range(159, 163)},
        **{ayah: ("۴:۱۶۳–۱۷۱", "verse=163&to=171") for ayah in range(163, 169)},
    }
    tafheem_notes = {
        157: "یادداشت‌های ۱۹۱–۱۹۴", 158: "یادداشتِ ۱۹۵", 159: "یادداشت‌های ۱۹۶–۱۹۷",
        160: "یادداشت‌های ۱۹۸–۲۰۰", 161: "یادداشت‌های ۲۰۱–۲۰۲", 162: "یادداشتِ ۲۰۳",
        163: "یادداشت‌های ۲۰۴–۲۰۵", 164: "یادداشتِ ۲۰۶", 165: "یادداشت‌های ۲۰۷–۲۰۸",
        166: "ترجمهٔ گروهی، بدونِ یادداشتِ مستقل",
        167: "ترجمهٔ گروهی، بدونِ یادداشتِ مستقل",
        168: "ترجمهٔ گروهی، بدونِ یادداشتِ مستقل",
    }
    for ayah in range(157, 169):
        entry = DOSSIER["verses"][f"4:{ayah}"]
        classical = _by_source(entry["classical"])
        for sid, mapping, tafsir_no in (
            ("ar_tusi_tibyan", tusi_groups, 39), ("ar_fayd_safi", fayd_groups, 41),
        ):
            page, scope = mapping[ayah]
            item = classical[sid]
            assert f"TafsirNo={tafsir_no}&SoraNo=4&AyahNo={page}&LanguageID=1" in item["sourceUrl"]
            assert scope in item["cite"] and scope in item["evidence"]
        tafheem = _by_source(entry["modern"])["en_tafheem_ul_quran"]
        scope, query = tafheem_groups[ayah]
        assert query in tafheem["sourceUrl"]
        assert scope in tafheem["cite"] and scope in tafheem["evidence"]
        assert tafheem_notes[ayah] in tafheem["cite"]

    fayd_168 = _by_source(DOSSIER["verses"]["4:168"]["classical"])["ar_fayd_safi"]
    assert "شرحِ مستقلِ ۴:۱۶۸" in fayd_168["evidence"]
    assert "نشان نمی‌دهد" in fayd_168["evidence"]

    collection = next(item for item in CATALOG["collections"] if item["id"] == "nisa-4-157-168-cited")
    assert CATALOG["version"] >= 21
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ نساء ۴:۱۵۷–۱۶۸"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == SUNNI
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == SHIA
    assert all(item["scope"] == "نساء ۴:۱۵۷–۱۶۸" for item in collection["items"])
    by_id = {item["id"]: item for item in collection["items"]}
    assert len(by_id["ar_tabari_qurancom"]["sourceUrls"]) == 12
    assert len(by_id["ar_ibn_kathir_qurancom"]["sourceUrls"]) == 12
    assert len(by_id["ar_jalalayn_qurancom"]["sourceUrls"]) == 12
    assert len(by_id["ar_tusi_tibyan"]["sourceUrls"]) == 10
    assert len(by_id["ar_fayd_safi"]["sourceUrls"]) == 4
    assert set(by_id["en_tafheem_ul_quran"]["sourceUrls"]) == {
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=157&to=158",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=159&to=162",
        "https://www.islamicstudies.info/tafheem.php?sura=4&verse=163&to=171",
    }


def test_nisa_4_157_168_keeps_disagreement_and_editorial_limits_visible():
    v157 = DOSSIER["verses"]["4:157"]
    assert any("نامِ فردِ جایگزین" in item["text"] for item in v157["critical"])
    assert "گمانه‌زنیِ بی‌منبع" in _by_source(v157["modern"])["en_tafheem_ul_quran"]["text"]
    assert "جسم و روح" in _by_source(DOSSIER["verses"]["4:158"]["modern"])["ar_qe_arabic_moyassar"]["text"]

    v159 = DOSSIER["verses"]["4:159"]
    assert "سه مرجع" in _by_source(v159["classical"])["ar_tusi_tibyan"]["text"]
    assert "دو احتمال" in _by_source(v159["classical"])["ar_jalalayn_qurancom"]["text"]
    assert "مرگِ عیسی" in _by_source(v159["modern"])["en_tafheem_ul_quran"]["text"]
    assert "مرگِ هر کتابی" in _by_source(v159["modern"])["en_tafheem_ul_quran"]["text"]

    v162 = DOSSIER["verses"]["4:162"]
    assert "اعراب" in _by_source(v162["classical"])["ar_tabari_qurancom"]["text"]
    assert "قرائتِ رفع" in _by_source(v162["classical"])["ar_jalalayn_qurancom"]["text"]

    v160 = DOSSIER["verses"]["4:160"]
    assert any("تعمیم‌دهنده" in item["text"] for item in v160["critical"])
    assert "یادداشت‌های ۱۹۸–۲۰۰" in _by_source(v160["modern"])["en_tafheem_ul_quran"]["cite"]

    v168 = DOSSIER["verses"]["4:168"]
    assert "آلِ محمد" in _by_source(v168["classical"])["ar_fayd_safi"]["text"]
    assert "معنای ظاهریِ عبارت" in " ".join(item["text"] for item in v168["critical"])
    assert "در بستهٔ نساء ۴:۱۵۷–۱۶۸" in DOSSIER["editorialMethod"]
    assert "نساء در این checkout بازهٔ ۴:۱–۱۷۶ را پوشش می‌دهد" in DOSSIER["notice"]
    assert "پوششِ آیه‌ایِ نساء به معنای تکمیلِ پژوهشِ تفسیری نیست" in DOSSIER["notice"]
