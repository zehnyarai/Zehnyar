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
            for model in ("izutsu", "fillmore", "cognitive"):
                for field in ("input", "operation", "meaning", "limit"):
                    self.assertTrue(annotation["framework"][model].get(field), f"{verse_id}: {model}.{field}")
            self.assertTrue(set(annotation["sources"]) <= source_ids, verse_id)
        status_ranges = ((5, 120), (6, 165), (7, 206), (8, 75), (9, 129), (10, 109), (11, 123), (12, 111), (13, 43), (14, 52), (15, 99), (16, 128), (17, 111), (18, 110), (19, 98), (20, 135), (21, 112), (22, 78), (23, 118), (24, 64), (25, 77), (26, 227), (27, 93), (28, 88), (29, 69), (30, 60), (31, 34), (32, 30), (33, 73), (34, 54), (35, 45), (36, 83), (37, 182), (38, 88), (39, 75), (40, 85), (41, 54), (42, 53), (43, 89), (44, 59), (45, 37), (46, 35), (47, 38), (48, 29), (49, 18), (50, 45), (51, 60), (112, 4), (113, 5), (114, 6))
        for surah, count in (*status_ranges, *REMAINING_SURAH_COUNTS.items()):
            for n in range(1, count + 1):
                self.assertEqual(data["verses"][f"{surah}:{n}"]["status"], "پیش‌نویس تحریری؛ نیازمند بازبینی تخصصی")

    def test_user_suggestions_remain_under_verse_notes_messages_and_principles(self):
        app = (ROOT / "static/app.js").read_text(encoding="utf-8")
        for kind in ("notes", "messages", "principles"):
            self.assertIn(f'${{proposalForm(verse, "{kind}")}}', app)
        self.assertIn("پیشنهادِ پژوهشگر", app)
        html = (ROOT / "static/index.html").read_text(encoding="utf-8")
        self.assertIn('id="admin-dialog"', html)
        self.assertIn('id="admin-token" type="password"', html)
        self.assertNotIn("ZEHNYAR_ADMIN_TOKEN", app)

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


if __name__ == "__main__":
    unittest.main()
