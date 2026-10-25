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

    def test_concept_lexicon_separates_quranic_equivalents_from_related_terms(self):
        lexicon_path = Path(main.STATIC_DIR) / "concept-lexicon.json"
        lexicon = json.loads(lexicon_path.read_text(encoding="utf-8"))
        concepts = {concept["id"]: concept for concept in lexicon["concepts"]}
        love = concepts["love"]
        self.assertIn("عشق", love["aliases"])
        self.assertIn(["حب", "حُبّ و دوست‌داشتن"], love["equivalents"])
        self.assertIn(["رحمة", "رحمت"], love["related"])
        self.assertTrue(all(concept["equivalents"] for concept in concepts.values()))
        self.assertTrue(all("related" in concept for concept in concepts.values()))

    def test_love_concept_has_arabic_quranic_witnesses_without_searching_persian(self):
        lexicon = json.loads((Path(main.STATIC_DIR) / "concept-lexicon.json").read_text(encoding="utf-8"))
        love = next(concept for concept in lexicon["concepts"] if concept["id"] == "love")
        equivalent_terms = {main.normalize(term) for term, _ in love["equivalents"]}
        arabic_matches = [
            record for record in main.CORPUS
            if any(term in record["arabic_normalized"] for term in equivalent_terms)
        ]
        self.assertGreater(len(arabic_matches), 0)
        self.assertFalse(any(main.normalize("عشق") in record["arabic_normalized"] for record in main.CORPUS))

    def test_simple_home_search_has_all_requested_distinct_paths(self):
        static_dir = Path(main.STATIC_DIR)
        html = (static_dir / "index.html").read_text(encoding="utf-8")
        script = (static_dir / "app.js").read_text(encoding="utf-8")
        for field_id in (
            "keyword-query", "concept-query", "topic-query", "quranic-equivalent-query",
            "translation-equivalent-query", "semantic-query", "synonym-query", "root-query",
        ):
            self.assertIn(f'id="{field_id}"', html)
        for label in ("نکات مهم آیه", "پیام‌های آیه", "اصول و قواعد زندگی", "مبانی اندیشهٔ قرآنی"):
            self.assertIn(label, script)
        for required_design in ("نکته‌های شماره‌دار با شاهدِ آیه", "اصل‌های شماره‌دارِ متن‌پایه", "پیام‌های شماره‌دار، مقید به نص و سیاق", "مدل ایزوتسو", "مدل فیلمور", "معناشناسی شناختی", "ظرف این بخش تا ۲۰ اصل", "فیلتر محلی فقط وقتی پیشنهاد را می‌پذیرد", "validateVerseProposal"):
            self.assertIn(required_design, script)
        self.assertIn("inlineTafsirEvidence", script)
        self.assertIn("نقلِ بدون بازنویسی", script)
        self.assertIn("تأمل در داستان‌های قرآنی", html)

        self.assertIn('id="concept-query"', html)
        self.assertIn('details class="advanced-search"', html)
        self.assertIn("جست‌وجوی پیشرفته با فیلدهای دیگر", html)

    def test_sources_dialog_separates_the_requested_research_source_fields(self):
        html = (Path(main.STATIC_DIR) / "index.html").read_text(encoding="utf-8")
        for label in ("متن قرآن", "تفاسیر جامع", "کتب علوم قرآنی", "مقالات قرآنی", "مقالات تفسیری"):
            self.assertIn(label, html)
        self.assertIn("در تحلیلِ آیه به‌کار می‌رود", html)

    def test_broad_topic_catalog_is_grouped_and_lexically_traceable(self):
        catalog = json.loads((Path(main.STATIC_DIR) / "topic-catalog.json").read_text(encoding="utf-8"))
        concepts = {concept["id"]: concept for concept in catalog["concepts"]}
        category_ids = [topic for category in catalog["categories"] for topic in category["topics"]]
        self.assertGreaterEqual(len(concepts), 90)
        self.assertEqual(len(category_ids), len(set(category_ids)))
        self.assertEqual(set(category_ids), set(concepts))
        self.assertTrue(all(concept["equivalents"] for concept in concepts.values()))
        self.assertTrue(all(concept["related"] for concept in concepts.values()))

    def test_full_cited_tafsir_sources_cover_the_complete_corpus(self):
        static_dir = Path(main.STATIC_DIR)
        registry = json.loads((static_dir / "tafsir-sources.json").read_text(encoding="utf-8"))
        self.assertEqual(len(registry["sources"]), 5)
        expected_ids = {"fa_qe_persian_mokhtasar", "ar_qe_arabic_moyassar", "fa_mizan_furqan", "ar_tabari_qurancom", "ar_qurtubi_qurancom"}
        self.assertEqual({source["id"] for source in registry["sources"]}, expected_ids)
        for source in registry["sources"]:
            payload = json.loads((static_dir / source["file"].removeprefix("static/")).read_text(encoding="utf-8"))
            verse_total = sum(len(ayahs) for ayahs in (payload.get("verses") or payload.get("ayahMapping")).values())
            self.assertEqual(verse_total, 6236)
            self.assertEqual(payload["edition"]["version"], source["version"])
            if source["id"].startswith("ar_") and source["id"].endswith("_qurancom"):
                self.assertTrue(source["sourceUrl"].startswith("https://github.com/zeeyado/quran-ebook/"))
                self.assertIn("upstreamZipSha256", payload["edition"])
            elif source["id"] == "fa_mizan_furqan":
                self.assertTrue(source["sourceUrl"].startswith("https://github.com/app-furqan/quran-app-data/"))
                self.assertTrue(payload["contents"])
                self.assertIn("upstreamDbSha256", payload["edition"])
            else:
                self.assertTrue(source["sourceUrl"].startswith("https://quranenc.com/"))

    def test_requested_tafsir_catalog_is_explicit_without_claiming_unloaded_texts(self):
        static_dir = Path(main.STATIC_DIR)
        catalog = json.loads((static_dir / "tafsir-catalog.json").read_text(encoding="utf-8"))
        requested = next(group for group in catalog["collections"] if group["id"] == "requested-comparative")
        self.assertEqual(len(requested["items"]), 10)
        titles = " ".join(item["title"] for item in requested["items"])
        for title in ("طبری", "زمخشری", "قرطبی", "الميزان", "من هدى", "من وحي", "الكاشف", "مفاتيح الغيب", "نمونه", "تسنیم"):
            self.assertIn(title, titles)
        active_ids = {item["id"] for item in requested["items"] if item["status"] == "available"}
        self.assertEqual(active_ids, {"tabari", "qurtubi", "mizan"})
        self.assertTrue(all(item["basis"] for item in requested["items"]))

    def test_all_initial_story_dossiers_have_anchored_material(self):
        static_dir = Path(main.STATIC_DIR)
        story_index = json.loads((static_dir / "story-index.json").read_text(encoding="utf-8"))
        dossiers = json.loads((static_dir / "story-dossiers.json").read_text(encoding="utf-8"))["dossiers"]
        self.assertEqual(set(dossiers), {story["id"] for story in story_index["stories"]})
        required_lists = ("stages", "keyConcepts", "topics", "subtleties", "lifePrinciples", "wonders", "charactersDetailed", "semiotics")
        for dossier in dossiers.values():
            for field in required_lists:
                self.assertTrue(dossier[field], field)
            self.assertTrue(dossier["applications"])
            self.assertEqual(set(dossier["narratology"]), {"opening", "tension", "turn", "closure"})
            self.assertTrue(dossier["elements"]["characters"])

    def test_story_screen_exposes_all_requested_research_fields(self):
        html = (Path(main.STATIC_DIR) / "index.html").read_text(encoding="utf-8")
        for label in ("همهٔ آیات", "مفاهیم کلیدی", "شخصیت‌ها", "موضوعات", "نکات و ظرایف", "اصول زندگی", "شگفتی‌ها", "روایت‌شناسی", "عناصر داستان", "نشانه‌شناسی"):
            self.assertIn(label, html)

    def test_initial_story_library_uses_valid_quran_ranges(self):
        story_index = json.loads((Path(main.STATIC_DIR) / "story-index.json").read_text(encoding="utf-8"))
        self.assertEqual(len(story_index["stories"]), len(main.STORY_RANGES))
        for story in story_index["stories"]:
            for passage in story["passages"]:
                self.assertIn((passage["surah"], passage["start"]), main.VERSE_MAP)
                self.assertIn((passage["surah"], passage["end"]), main.VERSE_MAP)

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
        self.assertIn("# دفتر کامل شواهد قرآن‌پژوهه", registry)
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
