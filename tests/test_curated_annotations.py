import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CuratedAnnotationTests(unittest.TestCase):
    def test_reviewed_range_has_complete_dossiers_and_valid_source_ids(self):
        static = ROOT / "static"
        data = json.loads((static / "verse-study-annotations.json").read_text(encoding="utf-8"))
        registry = json.loads((static / "tafsir-sources.json").read_text(encoding="utf-8"))
        source_ids = {source["id"] for source in registry["sources"]}
        expected = {f"1:{n}" for n in range(1, 8)} | {f"2:{n}" for n in range(1, 181)}
        self.assertEqual(set(data["verses"]), expected)
        for verse_id, annotation in data["verses"].items():
            for section in ("notes", "messages", "principles", "framework", "thematic", "context", "network"):
                self.assertTrue(annotation.get(section), f"{verse_id}: missing {section}")
            for model in ("izutsu", "fillmore", "cognitive"):
                for field in ("input", "operation", "meaning", "limit"):
                    self.assertTrue(annotation["framework"][model].get(field), f"{verse_id}: {model}.{field}")
            self.assertTrue(set(annotation["sources"]) <= source_ids, verse_id)

    def test_ui_loads_and_renders_curated_fields_and_service_worker_caches_them(self):
        app = (ROOT / "static/app.js").read_text(encoding="utf-8")
        worker = (ROOT / "static/sw.js").read_text(encoding="utf-8")
        for part in ("VERSE_STUDIES_URL", "curatedStudyItems", "curatedStudyBadge", "curated.framework", "curated.thematic", "curated.context", "curated.network"):
            self.assertIn(part, app)
        for kind in ("notes", "principles", "messages"):
            self.assertIn(f'proposalContributionForm(verse, "{kind}")', app)
        self.assertIn("/static/verse-study-annotations.json", worker)


if __name__ == "__main__":
    unittest.main()
