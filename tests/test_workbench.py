import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("study_workbench", ROOT / "tools/study_workbench.py")
workbench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workbench)


class StudyWorkbenchTests(unittest.TestCase):
    def test_prepare_follows_quran_order_and_bundles_both_local_tafsirs(self):
        batch = workbench.prepare("2:41", 10)
        self.assertEqual([x["id"] for x in batch["verses"]], [f"2:{n}" for n in range(41, 51)])
        first = batch["verses"][0]
        self.assertIn("وَءَامِنُوا", first["sourceMaterial"]["arabic"])
        self.assertEqual(set(first["sourceMaterial"]["tafsir"]), set(workbench.SOURCE_FILES))
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
        a.update({"notes":[{"text":"observation","evidence":"2:41"}], "messages":[{"text":"message","evidence":"2:41"}],
                  "principles":[{"text":"principle","evidence":"2:41"}], "thematic":[{"reference":"2:40","relation":"context"}],
                  "context":[{"reference":"2:40-42","relation":"near"}], "network":[{"reference":"2:40-42","relation":"network"}]})
        for model in workbench.MODELS:
            a["framework"][model] = {field:"filled" for field in ("input","operation","meaning","limit")}
        self.assertEqual(workbench.validate_batch(batch), [])


if __name__ == "__main__":
    unittest.main()
