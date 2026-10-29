# -*- coding: utf-8 -*-
"""اعتبارسنجیِ بستهٔ «کاربست امروز»: شمارش، پوششِ آیه‌ها، ارجاع و مرزِ سوءاستفاده."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = json.loads((ROOT / "static" / "scholar-application.json").read_text(encoding="utf-8"))
BANK = json.loads((ROOT / "static" / "scholar-bank.json").read_text(encoding="utf-8"))
CORPUS = json.loads((ROOT / "static" / "offline-corpus.json").read_text(encoding="utf-8"))["verses"]

REQUIRED = {"field", "text", "basis", "cite", "guard", "anchors"}


def ids():
    return {f"{r[0]}:{r[1]}" for r in CORPUS if isinstance(r, list)}


BATCH_ONE = {f"1:{i}" for i in range(1, 8)} | {f"2:{i}" for i in range(1, 44)}
BATCH_TWO = {f"2:{i}" for i in range(44, 94)}


def test_batches_have_fifty_verses_each():
    total = sum(batch["count"] for batch in APP["batches"])
    assert total == len(APP["verses"]), f"جمع بسته‌ها {total} ≠ مدخل‌ها {len(APP['verses'])}"
    assert all(batch["count"] == 50 for batch in APP["batches"])
    assert len(APP["batches"]) * 50 == len(APP["verses"])


def test_batch_ranges_are_exactly_as_declared():
    assert BATCH_ONE <= set(APP["verses"])
    assert BATCH_TWO <= set(APP["verses"])
    assert set(APP["verses"]) == BATCH_ONE | BATCH_TWO


def test_every_entry_is_complete_and_cited():
    anchor_ids = {a["id"] for a in BANK["anchors"]}
    for vid, entry in APP["verses"].items():
        assert REQUIRED <= set(entry), f"کلید ناقص: {vid}"
        for key in ("field", "text", "basis", "cite", "guard"):
            assert entry[key].strip(), f"{vid}:{key} خالی است"
        assert len(entry["cite"]) > 8, f"ارجاعِ کوتاه: {vid}"
        assert len(entry["text"].split()) >= 15, f"کاربستِ بسیار کوتاه: {vid}"
        for ref in entry["anchors"]:
            assert ref in anchor_ids, f"{vid} → لنگرِ ناموجود: {ref}"


def test_method_has_three_gates_and_a_testable_rule():
    method = APP["method"]
    assert len(method["steps"]) == 3
    assert "شرط" in method["rule"]
    assert method["cite"].strip()


def test_fields_cover_more_than_one_domain():
    fields = {entry["field"] for entry in APP["verses"].values()}
    assert len(fields) >= 8, f"تنوعِ میدان‌ها کم است: {len(fields)}"
