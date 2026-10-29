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


def test_batch_one_has_fifty_verses():
    assert len(APP["verses"]) == 50, f"شمارش بسته: {len(APP['verses'])}"
    assert APP["batches"][0]["count"] == 50


def test_batch_range_is_exactly_fatiha_and_baqara_start():
    expected = {f"1:{i}" for i in range(1, 8)} | {f"2:{i}" for i in range(1, 44)}
    assert set(APP["verses"]) == expected


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
