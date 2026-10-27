import os
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException

import main


class ProposalModerationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "proposals.sqlite3")
        self.previous_db = os.environ.get("ZEHNYAR_DB_PATH")
        self.previous_token = os.environ.get("ZEHNYAR_ADMIN_TOKEN")
        os.environ["ZEHNYAR_DB_PATH"] = self.db_path
        os.environ["ZEHNYAR_ADMIN_TOKEN"] = "unit-test-admin-token"

    def tearDown(self):
        if self.previous_db is None:
            os.environ.pop("ZEHNYAR_DB_PATH", None)
        else:
            os.environ["ZEHNYAR_DB_PATH"] = self.previous_db
        if self.previous_token is None:
            os.environ.pop("ZEHNYAR_ADMIN_TOKEN", None)
        else:
            os.environ["ZEHNYAR_ADMIN_TOKEN"] = self.previous_token
        self.temp_dir.cleanup()

    def test_proposals_require_admin_review_before_publication_and_can_be_edited_or_deleted(self):
        proposal = main.VerseProposalCreate(
            verse_id="1:1",
            kind="notes",
            claim="الله نامِ آفریننده و پروردگارِ مهربانی است.",
            witness="الله",
        )
        created = main.submit_verse_proposal(proposal)
        self.assertEqual(created["status"], "pending")
        self.assertEqual(main.public_verse_proposals()["proposals"], [])

        with self.assertRaises(HTTPException) as denied:
            main.admin_verse_proposals(authorization="Bearer wrong-token")
        self.assertEqual(denied.exception.status_code, 401)

        auth = "Bearer unit-test-admin-token"
        pending = main.admin_verse_proposals(authorization=auth)["proposals"]
        self.assertEqual(len(pending), 1)
        proposal_id = pending[0]["id"]
        revised = main.VerseProposalModeration(
            claim="الله در آغازِ این آیه به‌عنوان نامِ پروردگار آمده است.",
            witness="الله",
            status="approved",
        )
        updated = main.moderate_verse_proposal(proposal_id, revised, authorization=auth)
        self.assertEqual(updated["proposal"]["status"], "approved")
        self.assertEqual(len(main.public_verse_proposals()["proposals"]), 1)

        main.delete_verse_proposal(proposal_id, authorization=auth)
        self.assertEqual(main.public_verse_proposals()["proposals"], [])

    def test_admin_routes_fail_closed_without_a_configured_token(self):
        os.environ.pop("ZEHNYAR_ADMIN_TOKEN", None)
        with self.assertRaises(HTTPException) as unavailable:
            main.admin_verse_proposals(authorization=None)
        self.assertEqual(unavailable.exception.status_code, 503)

    def test_proposals_need_an_exact_verse_witness_and_relevant_word_overlap(self):
        with self.assertRaises(HTTPException) as invalid:
            main.submit_verse_proposal(main.VerseProposalCreate(
                verse_id="1:1", kind="messages",
                claim="این ادعای طولانی اما بی‌ارتباط است.", witness="شاهدی بیرون از آیه",
            ))
        self.assertEqual(invalid.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
