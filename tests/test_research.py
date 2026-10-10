import unittest

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

    def test_blank_query_is_rejected(self):
        with self.assertRaises(HTTPException):
            main.analyze("   ", 12, True)


if __name__ == "__main__":
    unittest.main()
