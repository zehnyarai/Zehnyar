import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("study_workbench", ROOT / "tools/study_workbench.py")
workbench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workbench)


class StudyWorkbenchTests(unittest.TestCase):
    def test_prepare_follows_quran_order_and_bundles_all_five_local_tafsirs(self):
        batch = workbench.prepare("2:41", 10)
        self.assertEqual([x["id"] for x in batch["verses"]], [f"2:{n}" for n in range(41, 51)])
        first = batch["verses"][0]
        self.assertIn("وَءَامِنُوا", first["sourceMaterial"]["arabic"])
        self.assertEqual(set(first["sourceMaterial"]["tafsir"]), set(workbench.SOURCE_FILES))
        self.assertTrue(all(text.strip() for text in first["sourceMaterial"]["tafsir"].values()))
        self.assertFalse(first["annotation"]["notes"], "the workbench must not invent editorial notes")

    def test_prepare_can_bundle_fifty_consecutive_verses_for_faster_editorial_batches(self):
        batch = workbench.prepare("2:41", 50)
        self.assertEqual(len(batch["verses"]), 50)
        self.assertEqual(batch["verses"][-1]["id"], "2:90")

    def test_prepare_rejects_a_range_past_the_end_of_the_corpus(self):
        with self.assertRaises(ValueError):
            workbench.prepare("114:6", 2)

    def test_validator_rejects_empty_drafts_and_accepts_completed_structure(self):
        batch = workbench.prepare("2:41", 1)
        errors = workbench.validate_batch(batch)
        self.assertTrue(any("notes is empty" in error for error in errors))
        a = batch["verses"][0]["annotation"]
        a["notes"] = [{"text":f"observation {n}","evidence":"2:41 source"} for n in range(3)]
        self.assertTrue(any("notes needs at least four" in error for error in workbench.validate_batch(batch)))
        a.update({"notes":[{"text":f"observation {n}","evidence":"2:41 source"} for n in range(4)],
                  "messages":[{"text":f"message {n}","evidence":"2:41 source"} for n in range(4)],
                  "principles":[{"text":f"principle {n}","evidence":"2:41 source"} for n in range(4)],
                  "thematic":[{"reference":"2:40","relation":"context"}],
                  "context":[{"reference":"2:40-42","relation":"near"}], "network":[{"reference":"2:40-42","relation":"network"}]})
        for model in workbench.MODELS:
            a["framework"][model] = {field:"filled" for field in ("input","operation","meaning","limit")}
        self.assertEqual(workbench.validate_batch(batch), [])
        a["notes"].append(dict(a["notes"][0]))
        self.assertTrue(any("notes[5] duplicates" in error for error in workbench.validate_batch(batch)))

    def test_merge_records_coverage_without_claiming_scholarly_review(self):
        annotation = {
            "notes": [{"text":f"note {n}","evidence":"2:41 source"} for n in range(4)],
            "messages": [{"text":f"message {n}","evidence":"2:41 source"} for n in range(4)],
            "principles": [{"text":f"principle {n}","evidence":"2:41 source"} for n in range(4)],
            "framework": {model:{field:"filled" for field in ("input","operation","meaning","limit")} for model in workbench.MODELS},
            "thematic": [{"reference":"2:40","relation":"context"}],
            "context": [{"reference":"2:40-42","relation":"near"}],
            "network": [{"reference":"2:40-42","relation":"network"}],
            "sources": list(workbench.SOURCE_FILES),
        }
        batch = {"start":[2,41],"end":[2,41],"verses":[{"id":"2:41","annotation":annotation}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "annotations.json"
            path.write_text(json.dumps({"verses":{},"reviewedRange":"1:1-1:7"}),encoding="utf-8")
            original = workbench.ANNOTATIONS
            try:
                workbench.ANNOTATIONS = path
                self.assertEqual(workbench.merge(batch),1)
            finally:
                workbench.ANNOTATIONS = original
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["coverageRange"],"1:1-1:7; 2:41-2:41")
            self.assertNotIn("reviewedRange",saved)
            self.assertIn("2:41",saved["verses"])


if __name__ == "__main__":
    unittest.main()
