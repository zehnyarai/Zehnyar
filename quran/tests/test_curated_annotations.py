import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REMAINING_SURAH_COUNTS = {
    52: 49, 53: 62, 54: 55, 55: 78, 56: 96, 57: 29, 58: 22, 59: 24, 60: 13,
    61: 14, 62: 11, 63: 11, 64: 18, 65: 12, 66: 12, 67: 30, 68: 52, 69: 52,
    70: 44, 71: 28, 72: 28, 73: 20, 74: 56, 75: 40, 76: 31, 77: 50, 78: 40,
    79: 46, 80: 42, 81: 29, 82: 19, 83: 36, 84: 25, 85: 22, 86: 17, 87: 19,
    88: 26, 89: 30, 90: 20, 91: 15, 92: 21, 93: 11, 94: 8, 95: 8, 96: 19,
    97: 5, 98: 8, 99: 8, 100: 11, 101: 11, 102: 8, 103: 3, 104: 9, 105: 5,
    106: 4, 107: 7, 108: 3, 109: 6, 110: 3, 111: 5,
}


class CuratedAnnotationTests(unittest.TestCase):
    def test_restored_and_new_dossiers_are_complete(self):
        static = ROOT / "static"
        data = json.loads((static / "verse-study-annotations.json").read_text(encoding="utf-8"))
        registry = json.loads((static / "tafsir-sources.json").read_text(encoding="utf-8"))
        source_ids = {source["id"] for source in registry["sources"]}
        expected = (
            {f"1:{n}" for n in range(1, 8)}
            | {f"2:{n}" for n in range(1, 287)}
            | {f"3:{n}" for n in range(1, 201)}
            | {f"4:{n}" for n in range(1, 177)}
            | {f"5:{n}" for n in range(1, 121)}
            | {f"6:{n}" for n in range(1, 166)}
            | {f"7:{n}" for n in range(1, 207)}
            | {f"8:{n}" for n in range(1, 76)}
            | {f"9:{n}" for n in range(1, 130)}
            | {f"10:{n}" for n in range(1, 110)}
            | {f"11:{n}" for n in range(1, 124)}
            | {f"12:{n}" for n in range(1, 112)}
            | {f"13:{n}" for n in range(1, 44)}
            | {f"14:{n}" for n in range(1, 53)}
            | {f"15:{n}" for n in range(1, 100)}
            | {f"16:{n}" for n in range(1, 129)}
            | {f"17:{n}" for n in range(1, 112)}
            | {f"18:{n}" for n in range(1, 111)}
            | {f"19:{n}" for n in range(1, 99)}
            | {f"20:{n}" for n in range(1, 136)}
            | {f"21:{n}" for n in range(1, 113)}
            | {f"22:{n}" for n in range(1, 79)}
            | {f"23:{n}" for n in range(1, 119)}
            | {f"24:{n}" for n in range(1, 65)}
            | {f"25:{n}" for n in range(1, 78)}
            | {f"26:{n}" for n in range(1, 228)}
            | {f"27:{n}" for n in range(1, 94)}
            | {f"28:{n}" for n in range(1, 89)}
            | {f"29:{n}" for n in range(1, 70)}
            | {f"30:{n}" for n in range(1, 61)}
            | {f"31:{n}" for n in range(1, 35)}
            | {f"32:{n}" for n in range(1, 31)}
            | {f"33:{n}" for n in range(1, 74)}
            | {f"34:{n}" for n in range(1, 55)}
            | {f"35:{n}" for n in range(1, 46)}
            | {f"36:{n}" for n in range(1, 84)}
            | {f"37:{n}" for n in range(1, 183)}
            | {f"38:{n}" for n in range(1, 89)}
            | {f"39:{n}" for n in range(1, 76)}
            | {f"40:{n}" for n in range(1, 86)}
            | {f"41:{n}" for n in range(1, 55)}
            | {f"42:{n}" for n in range(1, 54)}
            | {f"43:{n}" for n in range(1, 90)}
            | {f"44:{n}" for n in range(1, 60)}
            | {f"45:{n}" for n in range(1, 38)}
            | {f"46:{n}" for n in range(1, 36)}
            | {f"47:{n}" for n in range(1, 39)}
            | {f"48:{n}" for n in range(1, 30)}
            | {f"49:{n}" for n in range(1, 19)}
            | {f"50:{n}" for n in range(1, 46)}
            | {f"51:{n}" for n in range(1, 61)}
            | {f"{surah}:{n}" for surah, count in REMAINING_SURAH_COUNTS.items() for n in range(1, count + 1)}
            | {f"112:{n}" for n in range(1, 5)}
            | {f"113:{n}" for n in range(1, 6)}
            | {f"114:{n}" for n in range(1, 7)}
        )
        self.assertEqual(set(data["verses"]), expected)
        for verse_id, annotation in data["verses"].items():
            for section in ("notes", "messages", "principles", "framework", "thematic", "context", "network"):
                self.assertTrue(annotation.get(section), f"{verse_id}: missing {section}")
            if verse_id.startswith(("4:", "5:", "6:", "7:", "8:", "9:")):
                self.assertTrue(annotation.get("research"), f"{verse_id}: missing research")
            models = ("izutsu", "fillmore", "cognitive", "historical", "interdisciplinary") if verse_id.startswith(("4:", "5:", "6:", "7:", "8:", "9:")) else ("izutsu", "fillmore", "cognitive")
            for model in models:
                for field in ("input", "operation", "meaning", "limit"):
                    self.assertTrue(annotation["framework"][model].get(field), f"{verse_id}: {model}.{field}")
            self.assertTrue(set(annotation["sources"]) <= source_ids, verse_id)
        status_ranges = ((5, 120), (6, 165), (7, 206), (8, 75), (9, 129), (10, 109), (11, 123), (12, 111), (13, 43), (14, 52), (15, 99), (16, 128), (17, 111), (18, 110), (19, 98), (20, 135), (21, 112), (22, 78), (23, 118), (24, 64), (25, 77), (26, 227), (27, 93), (28, 88), (29, 69), (30, 60), (31, 34), (32, 30), (33, 73), (34, 54), (35, 45), (36, 83), (37, 182), (38, 88), (39, 75), (40, 85), (41, 54), (42, 53), (43, 89), (44, 59), (45, 37), (46, 35), (47, 38), (48, 29), (49, 18), (50, 45), (51, 60), (112, 4), (113, 5), (114, 6))
        for surah, count in (*status_ranges, *REMAINING_SURAH_COUNTS.items()):
            for n in range(1, count + 1):
                self.assertEqual(data["verses"][f"{surah}:{n}"]["status"], "پیش‌نویس تحریری؛ نیازمند بازبینی تخصصی")

    def test_fatiha_editorial_batch_has_four_cited_items_in_each_requested_field(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        corpus = json.loads((ROOT / "static/offline-corpus.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(1, 8):
            entry = data[f"1:{ayah}"]
            for field in ("notes", "principles", "messages"):
                self.assertGreaterEqual(len(entry[field]), 4, f"1:{ayah} needs four {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
            self.assertGreaterEqual(len(entry["research"]), 4)
            self.assertLessEqual(len(entry["research"]), 5)
            self.assertTrue(all(item.get("title") and item.get("question") and item.get("evidence") for item in entry["research"]))
            tuple_record = next(row for row in corpus if f"{row[0]}:{row[1]}" == f"1:{ayah}")
            translation = tuple_record[3].strip()
            for field in ("notes", "principles", "messages"):
                self.assertTrue(all(item["text"].strip() != translation for item in entry[field]))

    def test_opening_fatiha_and_baqarah_verses_have_four_source_bound_research_questions(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        verse_ids = [f"1:{ayah}" for ayah in range(1, 8)] + [f"2:{ayah}" for ayah in range(1, 9)]
        for verse_id in verse_ids:
            research = data[verse_id]["research"]
            self.assertEqual(len(research), 4, verse_id)
            self.assertTrue(all(item.get("title") and item.get("question") and item.get("evidence") for item in research))

    def test_baqarah_first_ten_have_distinct_cited_sections_and_research_prompts(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(1, 11):
            entry = data[f"2:{ayah}"]
            for field in ("notes", "messages", "principles"):
                self.assertEqual(len(entry[field]), 4, f"2:{ayah} {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
                texts = [" ".join(item["text"].split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"2:{ayah} {field} repeats")
            self.assertEqual(len(entry["research"]), 4 if ayah <= 8 else 3)
            self.assertTrue(all(item.get("question") and item.get("evidence") for item in entry["research"]))

    def test_baqarah_verses_eleven_to_twenty_have_distinct_cited_sections_and_research_prompts(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(11, 21):
            entry = data[f"2:{ayah}"]
            for field in ("notes", "messages", "principles"):
                self.assertEqual(len(entry[field]), 4, f"2:{ayah} {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
                texts = [" ".join(item["text"].split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"2:{ayah} {field} repeats")
            self.assertEqual(len(entry["research"]), 3)
            self.assertTrue(all(item.get("question") and item.get("evidence") for item in entry["research"]))

    def test_baqarah_verses_twenty_one_to_thirty_have_distinct_cited_sections_and_research_prompts(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(21, 31):
            entry = data[f"2:{ayah}"]
            for field in ("notes", "messages", "principles"):
                self.assertEqual(len(entry[field]), 4, f"2:{ayah} {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
                texts = [" ".join(item["text"].split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"2:{ayah} {field} repeats")
            self.assertEqual(len(entry["research"]), 3)
            self.assertTrue(all(item.get("question") and item.get("evidence") for item in entry["research"]))

    def test_baqarah_verses_thirty_one_to_fifty_have_distinct_cited_sections_and_research_prompts(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(31, 51):
            entry = data[f"2:{ayah}"]
            for field in ("notes", "messages", "principles"):
                self.assertEqual(len(entry[field]), 4, f"2:{ayah} {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
                texts = [" ".join(item["text"].split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"2:{ayah} {field} repeats")
            self.assertEqual(len(entry["research"]), 3)
            self.assertTrue(all(item.get("question") and item.get("evidence") for item in entry["research"]))

    def test_baqarah_verses_fifty_one_to_seventy_have_distinct_cited_sections_and_research_prompts(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(51, 71):
            entry = data[f"2:{ayah}"]
            for field in ("notes", "messages", "principles"):
                self.assertEqual(len(entry[field]), 4, f"2:{ayah} {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
                texts = [" ".join(item["text"].split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"2:{ayah} {field} repeats")
            self.assertEqual(len(entry["research"]), 3)
            self.assertTrue(all(item.get("question") and item.get("evidence") for item in entry["research"]))

    def test_baqarah_verses_fifty_one_to_eighty_have_distinct_cited_sections_and_research_prompts(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(51, 81):
            entry = data[f"2:{ayah}"]
            for field in ("notes", "messages", "principles"):
                self.assertEqual(len(entry[field]), 4, f"2:{ayah} {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
                texts = [" ".join(item["text"].split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"2:{ayah} {field} repeats")
            self.assertEqual(len(entry["research"]), 3)
            self.assertTrue(all(item.get("question") and item.get("evidence") for item in entry["research"]))

    def test_baqarah_verses_eighty_one_to_one_hundred_have_distinct_cited_sections_and_research_prompts(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(81, 101):
            entry = data[f"2:{ayah}"]
            for field in ("notes", "messages", "principles"):
                self.assertEqual(len(entry[field]), 4, f"2:{ayah} {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
                texts = [" ".join(item["text"].split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"2:{ayah} {field} repeats")
            self.assertEqual(len(entry["research"]), 3)
            self.assertTrue(all(item.get("question") and item.get("evidence") for item in entry["research"]))

    def test_baqarah_verses_one_hundred_one_to_one_hundred_ten_have_distinct_cited_sections_and_research_prompts(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(101, 111):
            entry = data[f"2:{ayah}"]
            for field in ("notes", "messages", "principles"):
                self.assertEqual(len(entry[field]), 4, f"2:{ayah} {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
                texts = [" ".join(item["text"].split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"2:{ayah} {field} repeats")
            self.assertEqual(len(entry["research"]), 3)
            self.assertTrue(all(item.get("question") and item.get("evidence") for item in entry["research"]))

    def test_baqarah_verses_one_hundred_eleven_to_one_hundred_twenty_have_distinct_cited_sections_and_research_prompts(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(111, 121):
            entry = data[f"2:{ayah}"]
            for field in ("notes", "messages", "principles"):
                self.assertEqual(len(entry[field]), 4, f"2:{ayah} {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
                texts = [" ".join(item["text"].split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"2:{ayah} {field} repeats")
            self.assertEqual(len(entry["research"]), 3)
            self.assertTrue(all(item.get("question") and item.get("evidence") for item in entry["research"]))

    def test_baqarah_verses_one_hundred_twenty_one_to_one_hundred_forty_have_distinct_cited_sections_and_research_prompts(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(121, 141):
            entry = data[f"2:{ayah}"]
            for field in ("notes", "messages", "principles"):
                self.assertEqual(len(entry[field]), 4, f"2:{ayah} {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
                texts = [" ".join(item["text"].split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"2:{ayah} {field} repeats")
            self.assertEqual(len(entry["research"]), 3)
            self.assertTrue(all(item.get("question") and item.get("evidence") for item in entry["research"]))

    def test_baqarah_verses_one_hundred_forty_one_to_one_hundred_fifty_have_distinct_cited_sections_and_research_prompts(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(141, 151):
            entry = data[f"2:{ayah}"]
            for field in ("notes", "messages", "principles"):
                self.assertEqual(len(entry[field]), 4, f"2:{ayah} {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
                texts = [" ".join(item["text"].split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"2:{ayah} {field} repeats")
            self.assertEqual(len(entry["research"]), 3)
            self.assertTrue(all(item.get("question") and item.get("evidence") for item in entry["research"]))

    def test_baqarah_verses_one_hundred_fifty_one_to_one_hundred_seventy_have_distinct_cited_sections_and_research_prompts(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(151, 171):
            entry = data[f"2:{ayah}"]
            for field in ("notes", "messages", "principles"):
                self.assertEqual(len(entry[field]), 4, f"2:{ayah} {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
                texts = [" ".join(item["text"].split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"2:{ayah} {field} repeats")
            self.assertEqual(len(entry["research"]), 3)
            self.assertTrue(all(item.get("question") and item.get("evidence") for item in entry["research"]))

    def test_baqarah_verses_one_hundred_seventy_one_to_two_hundred_have_distinct_cited_sections_and_research_prompts(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(171, 201):
            entry = data[f"2:{ayah}"]
            for field in ("notes", "messages", "principles"):
                self.assertEqual(len(entry[field]), 4, f"2:{ayah} {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
                texts = [" ".join(item["text"].split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"2:{ayah} {field} repeats")
            self.assertEqual(len(entry["research"]), 3)
            self.assertTrue(all(item.get("question") and item.get("evidence") for item in entry["research"]))

    def test_baqarah_verses_two_hundred_one_to_two_hundred_fifty_have_distinct_cited_sections_and_research_prompts(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(201, 251):
            entry = data[f"2:{ayah}"]
            for field in ("notes", "messages", "principles"):
                self.assertEqual(len(entry[field]), 4, f"2:{ayah} {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
                texts = [" ".join(item["text"].split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"2:{ayah} {field} repeats")
            self.assertEqual(len(entry["research"]), 3)
            self.assertTrue(all(item.get("question") and item.get("evidence") for item in entry["research"]))

    def test_baqarah_verses_two_hundred_fifty_one_to_two_hundred_eighty_six_have_distinct_cited_sections_and_research_prompts(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(251, 287):
            entry = data[f"2:{ayah}"]
            for field in ("notes", "messages", "principles"):
                self.assertEqual(len(entry[field]), 4, f"2:{ayah} {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
                texts = [" ".join(item["text"].split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"2:{ayah} {field} repeats")
            self.assertEqual(len(entry["research"]), 3)
            self.assertTrue(all(item.get("question") and item.get("evidence") for item in entry["research"]))

    def test_baqarah_tafsir_citations_are_backed_by_linked_source_metadata(self):
        verses = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(1, 287):
            entry = verses[f"2:{ayah}"]
            claims = " ".join(
                item.get("text", "") + " " + item.get("evidence", "")
                for field in ("notes", "principles", "messages", "research")
                for item in entry.get(field, [])
            )
            if "طبری" in claims:
                self.assertIn("ar_tabari_qurancom", entry["sources"], f"2:{ayah} Tabari source")
            if "قرطبی" in claims:
                self.assertIn("ar_qurtubi_qurancom", entry["sources"], f"2:{ayah} Qurtubi source")

    def test_al_imran_verses_one_to_two_hundred_have_four_distinct_cited_items_and_research_prompts(self):
        verses = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        for ayah in range(1, 201):
            entry = verses[f"3:{ayah}"]
            for field in ("notes", "messages", "principles"):
                self.assertEqual(len(entry[field]), 4, f"3:{ayah} {field}")
                self.assertTrue(all(item.get("evidence") for item in entry[field]))
                texts = [" ".join(item["text"].split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"3:{ayah} {field} repeats")
            self.assertEqual(len(entry["research"]), 3)
            self.assertTrue(all(item.get("question") and item.get("evidence") for item in entry["research"]))

    def test_nisa_verses_one_to_one_hundred_seventy_six_have_five_distinct_cited_items_and_research_prompts(self):
        verses = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        list_fields = ("notes", "messages", "principles", "thematic", "context", "network", "research")
        models = ("izutsu", "fillmore", "cognitive", "historical", "interdisciplinary")
        for ayah in range(1, 177):
            verse_id = f"4:{ayah}"
            entry = verses[verse_id]
            for field in list_fields:
                self.assertEqual(len(entry[field]), 5, f"{verse_id} {field}")
                texts = [" ".join((item.get("text") or item.get("relation") or item.get("question") or "").split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"{verse_id} {field} repeats")
                self.assertTrue(all(item.get("evidence") for item in entry[field]), f"{verse_id} {field} lacks evidence")
            self.assertEqual(set(entry["framework"]), set(models), verse_id)
            for model in models:
                self.assertTrue(entry["framework"][model].get("cite"), f"{verse_id} framework.{model}.cite")
            self.assertEqual(set(entry["sources"]), {"ar_qe_arabic_moyassar", "ar_tabari_qurancom", "ar_qurtubi_qurancom", "fa_mizan_furqan"}, verse_id)

    def test_maida_verses_one_to_one_hundred_twenty_have_five_distinct_cited_items_and_models(self):
        verses = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        list_fields = ("notes", "messages", "principles", "thematic", "context", "network", "research")
        models = ("izutsu", "fillmore", "cognitive", "historical", "interdisciplinary")
        expected_sources = {"ar_qe_arabic_moyassar", "ar_tabari_qurancom", "ar_qurtubi_qurancom", "fa_mizan_furqan"}
        for ayah in range(1, 121):
            verse_id = f"5:{ayah}"
            entry = verses[verse_id]
            for field in list_fields:
                self.assertEqual(len(entry[field]), 5, f"{verse_id} {field}")
                texts = [" ".join((item.get("text") or item.get("relation") or item.get("question") or "").split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"{verse_id} {field} repeats")
                self.assertTrue(all(item.get("evidence") for item in entry[field]), f"{verse_id} {field} lacks evidence")
            self.assertEqual(set(entry["framework"]), set(models), verse_id)
            self.assertTrue(all(entry["framework"][model].get("cite") for model in models), verse_id)
            self.assertEqual(set(entry["sources"]), expected_sources, verse_id)

    def test_al_anam_verses_one_to_one_hundred_sixty_five_have_five_distinct_cited_items_and_models(self):
        verses = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        list_fields = ("notes", "messages", "principles", "thematic", "context", "network", "research")
        models = {"izutsu", "fillmore", "cognitive", "historical", "interdisciplinary"}
        expected_sources = {"ar_qe_arabic_moyassar", "ar_tabari_qurancom", "ar_qurtubi_qurancom", "fa_mizan_furqan"}
        for ayah in range(1, 166):
            verse_id = f"6:{ayah}"
            entry = verses[verse_id]
            for field in list_fields:
                self.assertEqual(len(entry[field]), 5, f"{verse_id} {field}")
                texts = [" ".join((item.get("text") or item.get("relation") or item.get("question") or "").split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"{verse_id} {field} repeats")
                self.assertTrue(all(item.get("evidence") for item in entry[field]), f"{verse_id} {field} lacks evidence")
            self.assertEqual(set(entry["framework"]), models, verse_id)
            self.assertTrue(all(entry["framework"][model].get("cite") for model in models), verse_id)
            self.assertEqual(set(entry["sources"]), expected_sources, verse_id)
            self.assertTrue(all(item["text"].startswith("پیشنهادِ من") for item in entry["messages"]), verse_id)
            for field in ("notes", "messages"):
                self.assertFalse(any(item.get("sourceId") == "fa_mizan_furqan" or "نقلِ عینِ متنِ المیزان" in item.get("text", "") for item in entry[field]), (verse_id, field))
        self.assertTrue(all(item.get("title") and item.get("question") and item.get("evidence") for item in verses["6:1"]["research"]))
        self.assertIn("resolution 70/186", verses["6:152"]["framework"]["interdisciplinary"]["cite"])
        self.assertIn("para. 32", verses["6:152"]["framework"]["interdisciplinary"]["cite"])

    def test_baqarah_9_to_286_annotation_research_stays_quranic_and_source_bound(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))
        verses = data["verses"]
        required_sources = {"ar_tabari_qurancom", "ar_qurtubi_qurancom", "ar_qe_arabic_moyassar"}
        tangents = ("شاخص‌های اعتمادِ نهادی", "شبکه‌های اجتماعی", "مدیریتِ تصویر", "سیاست‌گذاریِ امروز", "بازارِ امروز")
        for ayah in range(9, 287):
            verse_id = f"2:{ayah}"
            entry = verses[verse_id]
            self.assertEqual(len(entry["research"]), 3, verse_id)
            self.assertTrue(required_sources <= set(entry["sources"]), verse_id)
            for item in entry["research"]:
                self.assertTrue(item.get("title") and item.get("question") and item.get("evidence"), verse_id)
                self.assertFalse(any(term in item["question"] for term in tangents), (verse_id, item["question"]))

    def test_baqarah_annotation_applications_use_explicit_verse_scope(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        self.assertIn("نظارتِ اجتماعی", data["2:234"]["notes"][2]["text"])
        self.assertIn("نتیجه نمی‌شود", data["2:234"]["notes"][2]["text"])
        self.assertIn("قیاسی محدود", data["2:60"]["principles"][0]["text"])
        self.assertIn("نه حکمِ مستقیمِ آیه", data["2:60"]["principles"][0]["text"])
        self.assertIn("وعدهٔ سودِ مالیِ تضمینی", data["2:245"]["principles"][3]["text"])
        self.assertIn("آیه به‌تنهایی نظریهٔ سیاسیِ عام نمی‌سازد", data["2:246"]["principles"][1]["text"])
        self.assertNotIn("در تحلیلِ اقتصاد", data["2:276"]["principles"][3]["text"])

    def test_user_suggestions_remain_under_verse_notes_messages_and_principles(self):
        app = (ROOT / "static/app.js").read_text(encoding="utf-8")
        for kind in ("notes", "messages", "principles"):
            self.assertIn(f'${{proposalForm(verse, "{kind}")}}', app)
        self.assertIn("پیشنهادِ پژوهشگر", app)
        html = (ROOT / "static/index.html").read_text(encoding="utf-8")
        self.assertIn('id="admin-dialog"', html)
        self.assertIn('id="admin-token" type="password"', html)
        self.assertNotIn("ZEHNYAR_ADMIN_TOKEN", app)

    def test_brand_sources_and_per_section_notes_are_wired(self):
        html = (ROOT / "static/index.html").read_text(encoding="utf-8")
        app = (ROOT / "static/app.js").read_text(encoding="utf-8")
        manifest = json.loads((ROOT / "static/manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertIn("قرآن‌پژوهه", html)
        self.assertEqual(manifest["short_name"], "قرآن‌پژوهه")
        self.assertNotIn('data-detail-tab="notebook"', html)
        self.assertIn("data-field-note", app)
        self.assertIn("FIELD_NOTES_KEY", app)
        self.assertIn("loadDeferredTafsir", app)
        self.assertIn("data-load-tafsir", app)
        self.assertIn('data-detail-tab="research"', html)
        self.assertIn('field === "research" ? "research"', app)
        self.assertIn("QURANIC_RESEARCH_LENSES", app)
        for off_topic in ("اقتصاد و توزیع منابع", "گفتار عمومی و مسئولیت رسانه‌ای", "تجربهٔ انسانی و سلامت روان"):
            self.assertNotIn(off_topic, app)
        for host in ("quran.inoor.ir", "noorlib.ir", "noormags.ir", "ensani.ir"):
            self.assertIn(host, html)

    def test_every_nonverse_page_has_local_notes_and_verse_bound_proposals(self):
        html = (ROOT / "static/index.html").read_text(encoding="utf-8")
        app = (ROOT / "static/app.js").read_text(encoding="utf-8")
        for screen in ("search", "results", "library", "surah", "story"):
            self.assertIn(f'id="{screen}-page-workspace" data-page-workspace', html)
        for marker in (
            'data-field-note="note"', 'data-field-note="proposal"', 'name="verse_id"',
            'name="witness"', 'data-page-proposal-form',
        ):
            self.assertIn(marker, app)
        self.assertIn("localStorage.setItem(FIELD_NOTES_KEY", app)
        self.assertIn("canonicalPageVerseId", app)
        self.assertIn("state.corpus.find((item) => item.id === verseId)", app)
        self.assertIn("validateVerseProposal(verse, claim, witness)", app)
        self.assertIn("verse_id: verse.id", app)
        self.assertIn("witness: witness.trim()", app)
        research = app.split("function detailPanelResearch", 1)[1].split("function detailPanelTafsir", 1)[0]
        self.assertIn(".slice(0, 5)", research)
        self.assertIn("pageScope: scope", app)

    def test_unreviewed_modern_and_critical_panels_do_not_reuse_generic_anchors(self):
        app = (ROOT / "static/app.js").read_text(encoding="utf-8")
        modern = app.split("function detailPanelModern", 1)[1].split("function detailPanelCritical", 1)[0]
        critical = app.split("function detailPanelCritical", 1)[1].split("function detailPanelResearch", 1)[0]
        self.assertNotIn("dossierAnchors(", modern)
        self.assertNotIn("dossierAnchors(", critical)
        self.assertIn("state.scholarPilotData?.[verse.id]", modern)
        self.assertIn("state.scholarPilotData?.[verse.id]", critical)
        self.assertIn("خوانشِ معاصرِ اختصاصی نوشته نشده است", modern)
        self.assertIn("هیچ لنگرِ عمومی یا قیاسِ بیرونی", critical)

    def test_advanced_search_stays_collapsed_without_removing_fields(self):
        html = (ROOT / "static/index.html").read_text(encoding="utf-8")
        self.assertIn('<details class="advanced-search">', html)
        self.assertNotIn('<details class="advanced-search" open', html)
        for field_id in ("keyword-query", "concept-query", "topic-query", "quranic-equivalent-query", "translation-equivalent-query", "semantic-query", "synonym-query", "root-query"):
            self.assertIn(f'id="{field_id}"', html)

    def test_ui_and_service_worker_load_curated_studies(self):
        app = (ROOT / "static/app.js").read_text(encoding="utf-8")
        worker = (ROOT / "static/sw.js").read_text(encoding="utf-8")
        for part in ("VERSE_STUDIES_URL", "reviewedStudyFor", "reviewedStudyField", "state.verseStudies", "annotation.status"):
            self.assertIn(part, app)
        for field in ("framework", "thematic", "context", "network"):
            self.assertIn(f'reviewedStudyField(verse, "{field}")', app)
        self.assertIn("/static/verse-study-annotations.json", worker)

    def test_opening_research_prompts_stay_with_quranic_text_and_tafsir(self):
        data = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))
        verses = data["verses"]
        opening = [f"1:{n}" for n in range(1, 8)] + [f"2:{n}" for n in range(1, 9)]
        tangents = ("اقتصاد", "رفاه", "سیاستِ رفاهی", "نظریه‌های ارتباطی", "روان‌شناختی", "شاخص‌های مدرن")
        required_sources = {"ar_tabari_qurancom", "ar_qurtubi_qurancom", "fa_mizan_furqan", "ar_qe_arabic_moyassar"}
        for verse_id in opening:
            entry = verses[verse_id]
            self.assertEqual(len(entry["research"]), 4, verse_id)
            self.assertTrue(required_sources <= set(entry["sources"]), verse_id)
            for prompt in entry["research"]:
                combined = prompt["title"] + " " + prompt["question"]
                self.assertFalse(any(term in combined for term in tangents), (verse_id, combined))
        method = data["editorialMethod"]
        self.assertIn("سیاقِ سوره", method)
        self.assertIn("گواهِ بازبینیِ علمی نیست", method)
        self.assertIn("coverageRange", data)
        self.assertNotIn("reviewedRange", data)


    def test_araf_and_anfal_have_five_cited_annotation_items_and_five_models(self):
        verses = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        list_fields = ("notes", "messages", "principles", "thematic", "context", "network", "research")
        models = {"izutsu", "fillmore", "cognitive", "historical", "interdisciplinary"}
        expected_sources = {"ar_qe_arabic_moyassar", "ar_tabari_qurancom", "ar_qurtubi_qurancom", "fa_mizan_furqan"}
        for surah, count in ((7, 206), (8, 75)):
            for ayah in range(1, count + 1):
                verse_id = f"{surah}:{ayah}"
                entry = verses[verse_id]
                for field in list_fields:
                    self.assertEqual(len(entry[field]), 5, f"{verse_id} {field}")
                    texts = [" ".join((item.get("text") or item.get("relation") or item.get("question") or "").split()) for item in entry[field]]
                    self.assertEqual(len(texts), len(set(texts)), f"{verse_id} {field} repeats")
                    self.assertTrue(all(item.get("evidence") for item in entry[field]), f"{verse_id} {field} lacks evidence")
                self.assertEqual(set(entry["framework"]), models, verse_id)
                self.assertTrue(all(entry["framework"][model].get("cite") for model in models), verse_id)
                self.assertEqual(set(entry["sources"]), expected_sources, verse_id)
                self.assertTrue(any(item.get("text", "").startswith("پیشنهادِ من") for item in entry["messages"]), verse_id)

    def test_araf_tabari_gap_is_recorded_as_missing_not_a_commentary_quote(self):
        verses = json.loads((ROOT / "static/verse-dossiers.json").read_text(encoding="utf-8"))["verses"]
        for ayah in (96, 97, 98):
            entry = verses[f"7:{ayah}"]
            self.assertEqual(len(entry["classical"]), 5)
            self.assertFalse(any(item["text"].startswith("نقلِ مستقیمِ عربیِ طبری") for item in entry["classical"]))
            gap = next(item for item in entry["classical"] if item.get("sourceRecordId") == "99")
            self.assertIn("سقط تفسير هذه الآيات الثلاث", gap["text"])
            self.assertIn("اعراف ۷:۹۹", gap["cite"])
            self.assertEqual([item["sourceId"] for item in entry["classical"]].count("ar_qurtubi_qurancom"), 4)
            self.assertIn("شرحِ جداگانه ندارد", entry["critical"][0]["text"])

    def test_tawbah_9_1_to_129_has_five_distinct_cited_annotation_items_and_models(self):
        verses = json.loads((ROOT / "static/verse-study-annotations.json").read_text(encoding="utf-8"))["verses"]
        list_fields = ("notes", "messages", "principles", "thematic", "context", "network", "research")
        models = {"izutsu", "fillmore", "cognitive", "historical", "interdisciplinary"}
        expected_sources = {"ar_qe_arabic_moyassar", "ar_tabari_qurancom", "ar_qurtubi_qurancom", "fa_mizan_furqan"}
        for ayah in range(1, 130):
            verse_id = f"9:{ayah}"
            entry = verses[verse_id]
            for field in list_fields:
                self.assertEqual(len(entry[field]), 5, f"{verse_id} {field}")
                texts = [" ".join((item.get("text") or item.get("relation") or item.get("question") or "").split()) for item in entry[field]]
                self.assertEqual(len(texts), len(set(texts)), f"{verse_id} {field} repeats")
                self.assertTrue(all(item.get("evidence") for item in entry[field]), f"{verse_id} {field} lacks evidence")
            self.assertEqual(set(entry["framework"]), models, verse_id)
            self.assertTrue(all(entry["framework"][model].get("cite") for model in models), verse_id)
            self.assertEqual(set(entry["sources"]), expected_sources, verse_id)
            self.assertTrue(all(item.get("title") and item.get("question") and item.get("evidence") for item in entry["research"]), verse_id)
            self.assertTrue(any(item.get("text", "").startswith("پیشنهادِ من") for item in entry["messages"]), verse_id)
        comparison = verses["9:6"]["research"][4]["evidence"]
        self.assertIn("resolution 2200A (XXI)", comparison)
        self.assertIn("art. 18", comparison)


if __name__ == "__main__":
    unittest.main()
