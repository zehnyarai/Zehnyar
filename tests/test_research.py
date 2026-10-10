import json
import unittest
from pathlib import Path

from fastapi import HTTPException

import main


class QuranResearchTests(unittest.TestCase):
    def test_full_local_corpus_is_loaded(self):
        self.assertEqual(len(main.CORPUS), 6236)
        self.assertEqual(len(main.VERSE_MAP), 6236)

    def test_normalization_keeps_search_equivalents_together(self):
        self.assertEqual(main.normalize("إِنَّ اللَّهَ عَلِيمٌ"), "ان الله علیم")
        self.assertEqual(main.normalize("مي‌كند"), "می کند")

    def test_topic_search_separates_direct_and_thematic_evidence(self):
        result = main.analyze("عدل", 10, True)
        self.assertEqual(result["canonical_topic"], "عدالت")
        self.assertGreater(result["stats"]["direct"], 0)
        self.assertTrue(result["verses"])
        self.assertTrue(any("مستقیم" in item["relation"] for item in result["verses"]))
        self.assertTrue(result["context"])

    def test_multiword_topic_does_not_label_a_component_as_direct_phrase(self):
        result = main.analyze("آزادی و اختیار", 8, True)
        self.assertEqual(result["stats"]["direct"], 0)
        self.assertGreater(result["stats"]["thematic"], 0)

    def test_literal_mode_has_no_implicit_topic_expansion(self):
        result = main.analyze("عدالت", 8, True, "literal")
        self.assertEqual(result["mode"]["id"], "literal")
        self.assertEqual(result["stats"]["thematic"], 0)
        self.assertTrue(all(item["relation"] == "ذکر / ترجمهٔ مستقیم" for item in result["verses"]))

    def test_evidence_trace_and_structure_are_returned(self):
        result = main.analyze("عدالت", 8, True)
        self.assertTrue(result["verses"][0]["evidence"])
        self.assertIn(result["verses"][0]["evidence"][0]["source"], {"متن عربی", "ترجمهٔ فارسی", "هر دو متن"})
        structure_total = sum(item["total"] for item in result["structure"]["revelation"].values())
        self.assertEqual(structure_total, result["stats"]["direct"] + result["stats"]["thematic"])

    def test_framework_categories_cover_every_curated_topic_once(self):
        categorized = [topic for category in main.TOPIC_CATEGORIES for topic in category["topics"]]
        self.assertEqual(set(categorized), set(main.TOPICS))
        self.assertEqual(len(categorized), len(set(categorized)))
        self.assertEqual(len(main.READING_PROTOCOL), 6)

    def test_structural_map_keeps_every_involved_surah_available(self):
        result = main.analyze("عدالت", 12, True, "topic")
        distribution = result["structure"]["distribution"]
        self.assertEqual(len(distribution), result["stats"]["surahs"])
        self.assertGreater(len(distribution), 7)
        self.assertEqual(sum(item["total"] for item in distribution), result["page"]["total"])

    def test_offline_topic_registry_matches_the_reviewed_server_lexicon(self):
        registry_path = Path(main.STATIC_DIR) / "offline-topics.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        self.assertEqual(set(registry["topics"]), set(main.TOPICS))
        self.assertEqual(
            registry["topics"]["عدالت"]["terms"],
            [list(item) for item in main.TOPICS["عدالت"]["terms"]],
        )

    def test_narrative_paths_are_bounded_and_separate_from_lexical_hits(self):
        result = main.analyze("عدالت", 8, True, "topic")
        paths = result["narrative"]["paths"]
        self.assertGreaterEqual(len(paths), 2)
        self.assertEqual(result["stats"]["narrative"], len(paths))
        self.assertTrue(all(item["relation"] == "نشانهٔ رواییِ بازبینی‌شده" for item in paths))
        self.assertTrue(all((item["surah"], item["ayah"]) in main.VERSE_MAP for item in paths))

    def test_literal_mode_does_not_add_narrative_paths(self):
        result = main.analyze("عدالت", 8, True, "literal")
        self.assertEqual(result["narrative"]["paths"], [])
        self.assertEqual(result["stats"]["narrative"], 0)

    def test_network_is_traceable_and_reflection_is_guarded(self):
        result = main.analyze("عدالت", 12, True, "topic")
        node_kinds = {node["kind"] for node in result["graph"]["nodes"]}
        self.assertTrue({"topic", "term", "surah", "story", "verse"}.issubset(node_kinds))
        self.assertEqual(len(result["graph"]["reading_arc"]), 5)
        self.assertEqual(result["graph"]["layout"], "concentric-evidence")
        self.assertIn("نه حکم شخصی", result["reflection"]["notice"])
        self.assertEqual(len(result["reflection"]["prompts"]), 2)

    def test_markdown_registry_exports_all_lexical_evidence(self):
        registry = main.research_markdown("عدالت", "topic")
        self.assertIn("# دفتر کامل شواهد ذهن‌یار", registry)
        self.assertIn("## شواهد واژگانی", registry)
        self.assertIn("## مسیرهای رواییِ پیشنهادی", registry)
        self.assertIn("ص 38:21", registry)

    def test_pagination_keeps_the_full_evidence_registry_reachable(self):
        first = main.analyze("رحمت", 12, True, "topic", 0)
        self.assertEqual(first["page"]["offset"], 0)
        self.assertEqual(first["page"]["limit"], 12)
        self.assertEqual(first["page"]["total"], first["stats"]["direct"] + first["stats"]["thematic"])
        self.assertGreater(first["page"]["total"], len(first["verses"]))
        self.assertEqual(first["page"]["next_offset"], len(first["verses"]))

        second = main.analyze("رحمت", 12, True, "topic", first["page"]["next_offset"])
        self.assertTrue({verse["id"] for verse in first["verses"]}.isdisjoint({verse["id"] for verse in second["verses"]}))
        self.assertEqual(second["page"]["offset"], 12)

    def test_blank_query_is_rejected(self):
        with self.assertRaises(HTTPException):
            main.analyze("   ", 12, True)


if __name__ == "__main__":
    unittest.main()
