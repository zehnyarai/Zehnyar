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
        for label in ("نکات", "پیام‌ها", "اصول زندگی", "چارچوب معنایی", "تفسیر موضوعی", "سیاق آیات", "نظم شبکه‌ای"):
            self.assertIn(label, script + html)
        self.assertIn("tafsirExcerptItems", script)
        self.assertIn("semanticModelCards", script)
        self.assertIn("تفسیرهای بارگیری‌شده", script)
        self.assertNotIn("VERSE_FOUNDATION_AXES", script)
        self.assertIn("VERSE_STUDIES_URL", script)
        self.assertIn("تأمل در داستان‌های قرآنی", html)
        studies = json.loads((static_dir / "verse-study-annotations.json").read_text(encoding="utf-8"))
        self.assertEqual(
            set(studies["verses"]),
            {f"1:{n}" for n in range(1, 8)}
            | {f"2:{n}" for n in range(1, 287)}
            | {f"3:{n}" for n in range(1, 201)},
        )
        for annotation in studies["verses"].values():
            for field in ("notes", "messages", "principles", "framework", "thematic", "context", "network"):
                self.assertTrue(annotation[field], f"missing {field}")

    def test_sources_dialog_separates_the_requested_research_source_fields(self):
        html = (Path(main.STATIC_DIR) / "index.html").read_text(encoding="utf-8")
        script = (Path(main.STATIC_DIR) / "app.js").read_text(encoding="utf-8")
        for label in ("متن قرآن", "تفاسیر جامع", "کتب علوم قرآنی", "مقالات قرآنی", "مقالات تفسیری"):
            self.assertIn(label, html)
        self.assertIn("در تحلیلِ آیه به‌کار می‌رود", html)
        self.assertIn("sourceTradition = source?.tradition || item.tradition", script)

    def test_broad_topic_catalog_is_grouped_and_lexically_traceable(self):
        catalog = json.loads((Path(main.STATIC_DIR) / "topic-catalog.json").read_text(encoding="utf-8"))
        concepts = {concept["id"]: concept for concept in catalog["concepts"]}
        category_ids = [topic for category in catalog["categories"] for topic in category["topics"]]
        self.assertGreaterEqual(len(concepts), 90)
        self.assertEqual(len(category_ids), len(set(category_ids)))
        self.assertEqual(set(category_ids), set(concepts))
        self.assertTrue(all(concept["equivalents"] for concept in concepts.values()))
        self.assertTrue(all(concept["related"] for concept in concepts.values()))

    def test_tafsir_source_registry_reports_local_availability_and_provenance(self):
        static_dir = Path(main.STATIC_DIR)
        registry = json.loads((static_dir / "tafsir-sources.json").read_text(encoding="utf-8"))
        source_ids = {source["id"] for source in registry["sources"]}
        core_ids = {"ar_qe_arabic_moyassar", "ar_tabari_qurancom", "ar_qurtubi_qurancom", "fa_mizan_furqan"}
        external_ids = {
            "ar_ibn_kathir_qurancom", "ar_baghawi_qurancom", "ar_jalalayn_qurancom",
            "ar_ibn_ashur", "en_tafheem_ul_quran", "en_maarif_ul_quran",
            "en_enlightening_commentary_vol7", "ar_tusi_tibyan", "ar_fayd_safi",
        }
        self.assertGreaterEqual(len(source_ids), 13)
        self.assertTrue(core_ids <= source_ids)
        self.assertTrue(external_ids <= source_ids)
        for source in registry["sources"]:
            source_file = source.get("file")
            path = Path(main.BASE_DIR) / source_file if source_file else None
            self.assertEqual(source["localAvailable"], bool(path and path.is_file()), source["id"])
            self.assertTrue(source["sourceUrl"].startswith("https://"))
            self.assertTrue(source.get("attribution"))
            if path and path.is_file():
                payload = json.loads(path.read_text(encoding="utf-8"))
                verse_total = sum(len(ayahs) for ayahs in payload.get("verses", {}).values())
                verse_total = verse_total or sum(len(ayahs) for ayahs in payload.get("ayahMapping", {}).values())
                self.assertEqual(verse_total, 6236, source["id"])
                self.assertEqual(payload["edition"]["version"], source["version"])
            elif not source_file:
                self.assertFalse(source["localAvailable"], source["id"])
                self.assertFalse(source.get("preload", True), source["id"])

    def test_yunus_external_tafsir_catalog_resolves_to_linked_registry_sources(self):
        static_dir = Path(main.STATIC_DIR)
        catalog = json.loads((static_dir / "tafsir-catalog.json").read_text(encoding="utf-8"))
        collection = next(group for group in catalog["collections"] if group["id"] == "yunus-10-49-60-cited")
        registry = json.loads((static_dir / "tafsir-sources.json").read_text(encoding="utf-8"))
        registry_by_id = {source["id"]: source for source in registry["sources"]}
        items = {item["id"]: item for item in collection["items"]}
        self.assertEqual(len(items), 11)
        self.assertTrue(set(items) <= set(registry_by_id))
        self.assertEqual(items["fa_mizan_furqan"]["status"], "linked-only")
        self.assertIn("بازنشر نشده", items["fa_mizan_furqan"]["basis"])
        for source_id, item in items.items():
            self.assertTrue(item["sourceUrl"].startswith("https://"), source_id)
            self.assertEqual(item["sourceUrl"], registry_by_id[source_id]["sourceUrl"], source_id)
            self.assertEqual(item["scope"], "یونس ۱۰:۴۹–۶۰", source_id)

    def test_yunus_10_61_72_external_tafsir_catalog_resolves_to_linked_registry_sources(self):
        static_dir = Path(main.STATIC_DIR)
        catalog = json.loads((static_dir / "tafsir-catalog.json").read_text(encoding="utf-8"))
        collection = next(group for group in catalog["collections"] if group["id"] == "yunus-10-61-72-cited")
        registry = json.loads((static_dir / "tafsir-sources.json").read_text(encoding="utf-8"))
        registry_by_id = {source["id"]: source for source in registry["sources"]}
        items = {item["id"]: item for item in collection["items"]}
        expected_ids = {
            "ar_qe_arabic_moyassar", "ar_tabari_qurancom", "ar_qurtubi_qurancom",
            "ar_ibn_kathir_qurancom", "ar_baghawi_qurancom", "ar_jalalayn_qurancom",
            "ar_tusi_tibyan", "ar_fayd_safi", "en_tafheem_ul_quran",
            "en_maarif_ul_quran", "en_enlightening_commentary_vol7",
        }
        self.assertEqual(set(items), expected_ids)
        self.assertTrue(set(items) <= set(registry_by_id))
        self.assertEqual(items["ar_qe_arabic_moyassar"]["status"], "available")
        self.assertEqual(
            {source_id for source_id, item in items.items() if item["status"] == "available"},
            {"ar_qe_arabic_moyassar"},
        )
        expected_urls = {
            "ar_jalalayn_qurancom": "https://quran.com/yunus/61/tafsirs/ar-tafsir-jalalayn",
            "ar_tusi_tibyan": "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=39&SoraNo=10&AyahNo=61&LanguageID=1",
            "ar_fayd_safi": "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=41&SoraNo=10&AyahNo=61&LanguageID=1",
            "en_tafheem_ul_quran": "https://www.islamicstudies.info/tafheem.php?sura=10&verse=61&to=72",
            "en_maarif_ul_quran": "https://quran.com/yunus/61/tafsirs/en-tafsir-maarif-ul-quran",
            "en_enlightening_commentary_vol7": "https://al-islam.org/enlightening-commentary-light-holy-quran-vol-7/section-7-no-fear-or-grief-friends-allah",
        }
        for source_id, item in items.items():
            registry_source = registry_by_id[source_id]
            self.assertTrue(item["sourceUrl"].startswith("https://"), source_id)
            self.assertEqual(item["sourceUrl"], expected_urls.get(source_id, registry_source["sourceUrl"]), source_id)
            self.assertEqual(item["title"], registry_source["title"], source_id)
            self.assertEqual(item["author"], registry_source["author"], source_id)
            self.assertEqual(item["language"], registry_source["language"], source_id)
            self.assertEqual(item["scope"], "یونس ۱۰:۶۱–۷۲", source_id)
            self.assertEqual(item["tradition"], registry_source["tradition"], source_id)
        self.assertGreaterEqual(catalog["version"], 8)
        comparative_core = collection["comparativeCore"]
        self.assertEqual(comparative_core["scope"], "هر آیهٔ یونس ۱۰:۶۱–۷۲")
        self.assertEqual(
            set(comparative_core["sunniSourceIds"]),
            {"ar_tabari_qurancom", "ar_qurtubi_qurancom", "ar_ibn_kathir_qurancom"},
        )
        self.assertEqual(
            set(comparative_core["shiaSourceIds"]),
            {"ar_tusi_tibyan", "ar_fayd_safi", "en_enlightening_commentary_vol7"},
        )
        self.assertIn("خلاصهٔ منسوب", comparative_core["note"])
        self.assertEqual(
            items["en_enlightening_commentary_vol7"]["version"],
            "جلد ۷، بخش‌های ۷ و ۸؛ صفحه‌بندیِ چاپی ثبت نشده",
        )

    def test_yunus_10_73_84_tafsir_catalog_keeps_the_explicit_comparative_core(self):
        static_dir = Path(main.STATIC_DIR)
        catalog = json.loads((static_dir / "tafsir-catalog.json").read_text(encoding="utf-8"))
        registry = json.loads((static_dir / "tafsir-sources.json").read_text(encoding="utf-8"))
        registry_by_id = {source["id"]: source for source in registry["sources"]}
        collection = next(group for group in catalog["collections"] if group["id"] == "yunus-10-73-84-cited")
        items = {item["id"]: item for item in collection["items"]}
        expected_ids = {
            "ar_qe_arabic_moyassar", "ar_tabari_qurancom", "ar_qurtubi_qurancom",
            "ar_ibn_kathir_qurancom", "ar_baghawi_qurancom", "ar_jalalayn_qurancom",
            "ar_tusi_tibyan", "ar_fayd_safi", "en_tafheem_ul_quran",
            "en_maarif_ul_quran", "en_enlightening_commentary_vol7",
        }
        self.assertEqual(set(items), expected_ids)
        self.assertTrue(set(items) <= set(registry_by_id))
        self.assertEqual({item["scope"] for item in items.values()}, {"یونس ۱۰:۷۳–۸۴"})
        self.assertGreaterEqual(catalog["version"], 8)
        self.assertEqual(collection["comparativeCore"]["scope"], "هر آیهٔ یونس ۱۰:۷۳–۸۴")
        self.assertEqual(
            set(collection["comparativeCore"]["sunniSourceIds"]),
            {"ar_tabari_qurancom", "ar_qurtubi_qurancom", "ar_ibn_kathir_qurancom"},
        )
        self.assertEqual(
            set(collection["comparativeCore"]["shiaSourceIds"]),
            {"ar_tusi_tibyan", "ar_fayd_safi", "en_enlightening_commentary_vol7"},
        )
        self.assertIn("خلاصهٔ منسوب", collection["comparativeCore"]["note"])
        self.assertEqual(
            items["ar_tusi_tibyan"]["sourceUrl"],
            "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=39&SoraNo=10&AyahNo=73&LanguageID=1",
        )
        self.assertEqual(
            items["ar_fayd_safi"]["sourceUrl"],
            "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=41&SoraNo=10&AyahNo=83&LanguageID=1",
        )
        self.assertEqual(
            items["en_tafheem_ul_quran"]["sourceUrl"],
            "https://www.islamicstudies.info/tafheem.php?sura=10&verse=71&to=82",
        )
        self.assertEqual(
            items["en_enlightening_commentary_vol7"]["sourceUrl"],
            "https://al-islam.org/enlightening-commentary-light-holy-quran-vol-7/section-8-ministries-noah-and-moses-referred",
        )
        self.assertEqual(items["en_enlightening_commentary_vol7"]["version"], "جلد ۷، بخش‌های ۸ و ۹؛ صفحه‌بندیِ چاپی ثبت نشده")
        expected_urls = {
            "ar_jalalayn_qurancom": "https://quran.com/yunus/73/tafsirs/ar-tafsir-jalalayn",
            "ar_tusi_tibyan": "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=39&SoraNo=10&AyahNo=73&LanguageID=1",
            "ar_fayd_safi": "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1&MadhabNo=4&TafsirNo=41&SoraNo=10&AyahNo=83&LanguageID=1",
            "en_tafheem_ul_quran": "https://www.islamicstudies.info/tafheem.php?sura=10&verse=71&to=82",
            "en_maarif_ul_quran": "https://quran.com/yunus/73/tafsirs/en-tafsir-maarif-ul-quran",
            "en_enlightening_commentary_vol7": "https://al-islam.org/enlightening-commentary-light-holy-quran-vol-7/section-8-ministries-noah-and-moses-referred",
        }
        for source_id, item in items.items():
            source = registry_by_id[source_id]
            self.assertTrue(item["sourceUrl"].startswith("https://"), source_id)
            self.assertEqual(item["sourceUrl"], expected_urls.get(source_id, source["sourceUrl"]), source_id)
            self.assertEqual(item["title"], source["title"], source_id)
            self.assertEqual(item["author"], source["author"], source_id)
            self.assertEqual(item["tradition"], source["tradition"], source_id)
            self.assertEqual(item["scope"], "یونس ۱۰:۷۳–۸۴", source_id)
        self.assertEqual(
            {source_id for source_id, item in items.items() if item["status"] == "available"},
            {"ar_qe_arabic_moyassar"},
        )

    def test_tafsir_catalog_counts_are_derived_dynamically_in_the_interface(self):
        app_js = (Path(main.STATIC_DIR) / "app.js").read_text(encoding="utf-8")
        self.assertIn("const total = collection.items.length;", app_js)
        self.assertIn("faNumber(items.length)", app_js)
        self.assertIn("${faNumber(total)} تفسیر جامع منتخب", app_js)
        self.assertNotIn('title: "پنج تفسیر شیعهٔ امامیه"', app_js)
        self.assertNotIn('title: "پنج تفسیر اهل‌سنت"', app_js)

    def test_requested_tafsir_catalog_is_explicit_without_claiming_unloaded_texts(self):
        static_dir = Path(main.STATIC_DIR)
        catalog = json.loads((static_dir / "tafsir-catalog.json").read_text(encoding="utf-8"))
        requested = next(group for group in catalog["collections"] if group["id"] == "requested-comparative")
        self.assertEqual(len(requested["items"]), 10)
        titles = " ".join(item["title"] for item in requested["items"])
        for title in ("طبری", "زمخشری", "قرطبی", "الميزان", "من هدى", "من وحي", "الكاشف", "مفاتيح الغيب", "نمونه", "تسنیم"):
            self.assertIn(title, titles)
        source_availability = {
            source["id"]: source["localAvailable"]
            for source in json.loads((static_dir / "tafsir-sources.json").read_text(encoding="utf-8"))["sources"]
        }
        aliases = {"tabari": "ar_tabari_qurancom", "qurtubi": "ar_qurtubi_qurancom", "mizan": "fa_mizan_furqan"}
        expected_available = {alias for alias, source_id in aliases.items() if source_availability[source_id]}
        self.assertEqual(
            {item["id"] for item in requested["items"] if item["status"] == "available"},
            expected_available,
        )
        for item in requested["items"]:
            if item["id"] in aliases:
                expected_status = "available" if source_availability[aliases[item["id"]]] else "excerpt-only"
                self.assertEqual(item["status"], expected_status, item["id"])
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
