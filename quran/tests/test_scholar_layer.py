# -*- coding: utf-8 -*-
"""اعتبارسنجیِ بانک و لایهٔ پژوهشی: هیچ ارجاعِ بی‌منبع و هیچ شناسهٔ گم‌شده‌ای نباشد."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = json.loads((ROOT / "static" / "scholar-bank.json").read_text(encoding="utf-8"))
PILOT = json.loads((ROOT / "static" / "scholar-pilot.json").read_text(encoding="utf-8"))["verses"]
LAYER = json.loads((ROOT / "static" / "verse-scholar-layer.json").read_text(encoding="utf-8"))
CORPUS = json.loads((ROOT / "static" / "offline-corpus.json").read_text(encoding="utf-8"))["verses"]

REQUIRED = {"id", "kind", "field", "claim", "cite", "limit", "question"}
PILOT_FIELDS = {"finding", "witness", "classical", "modern", "critique", "question", "anchors"}


def verse_ids():
    return {f"{r[0]}:{r[1]}" for r in CORPUS if isinstance(r, list)}


def test_anchor_ids_are_unique_and_complete():
    ids = [anchor["id"] for anchor in BANK["anchors"]]
    assert len(ids) == len(set(ids)), "شناسهٔ تکراری در بانک"
    for anchor in BANK["anchors"]:
        assert REQUIRED <= set(anchor), f"کلید ناقص: {anchor.get('id')}"
        assert anchor["kind"] in {"کهن", "معاصر"}
        assert len(anchor["cite"].strip()) > 8, f"ارجاع کوتاه/خالی: {anchor['id']}"
        assert anchor["question"].strip().endswith("؟"), f"پرسش بی‌علامت: {anchor['id']}"


def test_topics_only_reference_existing_anchors():
    ids = {anchor["id"] for anchor in BANK["anchors"]}
    for topic, refs in BANK["topics"].items():
        assert refs, f"موضوعِ بی‌لنگر: {topic}"
        for ref in refs:
            assert ref in ids, f"{topic} → {ref} در بانک نیست"


def test_layer_covers_every_verse_with_valid_anchors():
    ids = {anchor["id"] for anchor in BANK["anchors"]}
    missing = verse_ids() - set(LAYER["anchors"])
    assert not missing, f"آیهٔ بی‌لنگر: {sorted(missing)[:5]}"
    for vid, refs in LAYER["anchors"].items():
        assert refs, f"فهرستِ خالی برای {vid}"
        for ref in refs:
            assert ref in ids, f"{vid} → {ref}"
        assert len(refs) <= 4


def test_pilot_entries_are_complete_and_known_verses():
    known = verse_ids()
    for vid, entry in PILOT.items():
        assert vid in known, f"آیهٔ ناشناخته در نمونه: {vid}"
        assert PILOT_FIELDS <= set(entry), f"کلید ناقص در نمونه: {vid}"
        for key in ("finding", "witness", "classical", "modern", "critique", "question"):
            assert entry[key].strip(), f"{vid}:{key} خالی است"
        assert entry["question"].strip().endswith("؟")
        for ref in entry["anchors"]:
            assert ref in {anchor["id"] for anchor in BANK["anchors"]}, f"{vid} → {ref}"
    assert set(PILOT) <= set(LAYER["pilot"])
