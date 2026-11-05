# -*- coding: utf-8 -*-
"""Targeted validation for the source-scoped An-Nisa 4:169–176 batch."""
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


def test_nisa_4_169_176_has_scoped_complete_dossiers_and_source_balance():
    expected = {f"4:{ayah}" for ayah in range(169, 177)}
    assert expected <= set(DOSSIER["verses"])
    assert len(DOSSIER["verses"]) >= 705
    batch = next(item for item in DOSSIER["batches"] if item["id"] == "dossier-46")
    assert batch["range"] == "4:169–176" and batch["count"] == 8
    assert "پیش‌نویسِ نیازمندِ داوریِ تخصصی" in batch["status"]
    assert "نساء ۴:۱–۱۷۶ اکنون پوشش دارد" in batch["status"]
    assert sum(item["count"] for item in DOSSIER["batches"]) == len(DOSSIER["verses"])
    assert "نساء در این checkout بازهٔ ۴:۱–۱۷۶ را پوشش می‌دهد" in DOSSIER["notice"]
    assert "بسته‌های مائده ۵:۱–۶، ۵:۷–۱۲، ۵:۱۳–۱۸، ۵:۱۹–۲۴، ۵:۲۵–۳۰، ۵:۳۱–۳۶، ۵:۳۷–۴۲، ۵:۴۳–۴۸، ۵:۴۹–۵۴، ۵:۵۵–۶۰، ۵:۶۱–۱۱۰ و ۵:۱۱۱–۱۲۰ افزوده شده‌اند" in DOSSIER["notice"]

    registry_by_id = {item["id"]: item for item in REGISTRY["sources"]}
    for ayah in range(169, 177):
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


def test_nisa_4_169_176_preserves_actual_source_ranges_and_note_scopes():
    tusi_groups = {169: (169, "۴:۱۶۸–۱۶۹"), **{ayah: (ayah, f"۴:{str(ayah).translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))}") for ayah in range(170, 177)}}
    fayd_groups = {
        **{ayah: (169, "۴:۱۶۵–۱۷۱") for ayah in range(169, 172)},
        **{ayah: (172, "۴:۱۷۲–۱۷۶") for ayah in range(172, 177)},
    }
    tafheem_groups = {
        **{ayah: ("۴:۱۶۳–۱۷۱", "verse=163&to=171") for ayah in range(169, 172)},
        **{ayah: ("۴:۱۷۲–۱۷۶", "verse=172&to=176") for ayah in range(172, 177)},
    }
    tafheem_notes = {
        169: "ترجمهٔ گروهی، بدونِ یادداشتِ مستقل",
        170: "یادداشت‌های ۲۰۹–۲۱۰",
        171: "یادداشت‌های ۲۱۱–۲۱۸",
        172: "ترجمهٔ گروهی، بدونِ یادداشتِ مستقل",
        173: "ترجمهٔ گروهی، بدونِ یادداشتِ مستقل",
        174: "ترجمهٔ گروهی، بدونِ یادداشتِ مستقل",
        175: "ترجمهٔ گروهی، بدونِ یادداشتِ مستقل",
        176: "یادداشت‌های ۲۱۹–۲۲۳",
    }
    for ayah in range(169, 177):
        entry = DOSSIER["verses"][f"4:{ayah}"]
        classical = _by_source(entry["classical"])
        for sid, mapping, tafsir_no in (
            ("ar_tusi_tibyan", tusi_groups, 39), ("ar_fayd_safi", fayd_groups, 41),
        ):
            page, scope = mapping[ayah]
            record = classical[sid]
            assert f"TafsirNo={tafsir_no}&SoraNo=4&AyahNo={page}&LanguageID=1" in record["sourceUrl"]
            assert scope in record["cite"] and scope in record["evidence"]
        tafheem = _by_source(entry["modern"])["en_tafheem_ul_quran"]
        scope, query = tafheem_groups[ayah]
        assert query in tafheem["sourceUrl"]
        assert scope in tafheem["cite"] and scope in tafheem["evidence"]
        assert tafheem_notes[ayah] in tafheem["cite"]

    collection = next(item for item in CATALOG["collections"] if item["id"] == "nisa-4-169-176-cited")
    assert CATALOG["version"] >= 22
    assert collection["comparativeCore"]["scope"] == "هر آیهٔ نساء ۴:۱۶۹–۱۷۶"
    assert set(collection["comparativeCore"]["sunniSourceIds"]) == SUNNI
    assert set(collection["comparativeCore"]["shiaSourceIds"]) == SHIA
    assert all(item["scope"] == "نساء ۴:۱۶۹–۱۷۶" for item in collection["items"])
    by_id = {item["id"]: item for item in collection["items"]}
    assert len(by_id["ar_tabari_qurancom"]["sourceUrls"]) == 8
    assert len(by_id["ar_ibn_kathir_qurancom"]["sourceUrls"]) == 8
    assert len(by_id["ar_jalalayn_qurancom"]["sourceUrls"]) == 8
    assert len(by_id["ar_tusi_tibyan"]["sourceUrls"]) == 8
    assert len(by_id["ar_fayd_safi"]["sourceUrls"]) == 2
    assert len(by_id["en_tafheem_ul_quran"]["sourceUrls"]) == 2


def test_nisa_4_169_176_keeps_theological_and_legal_disagreements_attributed():
    verses = DOSSIER["verses"]
    v169 = verses["4:169"]
    assert "آلِ محمد" in _by_source(v169["classical"])["ar_fayd_safi"]["text"]
    assert "متنِ معیارِ قرآن" in " ".join(record["text"] for record in v169["critical"])

    v170 = verses["4:170"]
    assert "ولایتِ علی" in _by_source(v170["classical"])["ar_fayd_safi"]["text"]
    assert "نحوی" in _by_source(v170["classical"])["ar_tusi_tibyan"]["text"]

    v171 = verses["4:171"]
    assert "شش قول" in _by_source(v171["classical"])["ar_tusi_tibyan"]["text"]
    assert "یادداشت‌های ۲۱۱–۲۱۸" in _by_source(v171["modern"])["en_tafheem_ul_quran"]["cite"]
    assert "تاریخی" in " ".join(record["text"] for record in v171["critical"])

    v172 = verses["4:172"]
    assert "مکان" in _by_source(v172["classical"])["ar_tusi_tibyan"]["text"]
    assert "برتریِ فرشتگان" in _by_source(v172["classical"])["ar_ibn_kathir_qurancom"]["text"]

    v173 = verses["4:173"]
    assert "سندِ مرفوع" in _by_source(v173["classical"])["ar_ibn_kathir_qurancom"]["text"]
    assert "ظاهر المعنى" in _by_source(v173["classical"])["ar_fayd_safi"]["text"]

    v174 = verses["4:174"]
    assert "حدوثِ کلام" in _by_source(v174["classical"])["ar_tusi_tibyan"]["text"]
    assert "ولایتِ علی" in _by_source(v174["classical"])["ar_fayd_safi"]["text"]

    v175 = verses["4:175"]
    assert "ولایت" in _by_source(v175["classical"])["ar_fayd_safi"]["text"]
    assert "مرجعِ «به»" in " ".join(record["text"] for record in v175["critical"])

    v176 = verses["4:176"]
    assert "باقیمانده" in _by_source(v176["classical"])["ar_tusi_tibyan"]["text"]
    assert "عصبه" in _by_source(v176["classical"])["ar_ibn_kathir_qurancom"]["text"]
    assert "یادداشت‌های ۲۱۹–۲۲۳" in _by_source(v176["modern"])["en_tafheem_ul_quran"]["cite"]

    assert "در بستهٔ نساء ۴:۱۶۹–۱۷۶" in DOSSIER["editorialMethod"]
