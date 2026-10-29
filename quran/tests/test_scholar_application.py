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
BATCH_THREE = {f"2:{i}" for i in range(94, 144)}
BATCH_FOUR = {f"2:{i}" for i in range(165, 177)}


def test_batches_cover_every_entry_once():
    total = sum(batch["count"] for batch in APP["batches"])
    assert total == len(APP["verses"]), f"جمع بسته‌ها {total} ≠ مدخل‌ها {len(APP['verses'])}"
    assert all(batch["count"] > 0 and batch["status"].strip() for batch in APP["batches"])
    assert [batch["count"] for batch in APP["batches"][:3]] == [50, 50, 50]
    assert sum(batch["count"] for batch in APP["batches"][3:]) == 12


def test_batch_ranges_are_exactly_as_declared():
    assert BATCH_ONE <= set(APP["verses"])
    assert BATCH_TWO <= set(APP["verses"])
    assert BATCH_THREE <= set(APP["verses"])
    assert BATCH_FOUR <= set(APP["verses"])
    assert set(APP["verses"]) == BATCH_ONE | BATCH_TWO | BATCH_THREE | BATCH_FOUR


def iter_uses(v2=None):
    for vid, entry in APP["verses"].items():
        if "uses" in entry:
            for use in entry["uses"]:
                yield vid, use, True
        elif v2 is not True:
            yield vid, entry, False


def test_every_entry_is_complete():
    for vid, entry in APP["verses"].items():
        if "uses" in entry:
            assert entry["uses"], f"{vid}: فهرستِ کاربست خالی است"
            continue
        assert REQUIRED <= set(entry), f"کلید ناقص: {vid}"
        for key in ("field", "text", "basis", "cite", "guard"):
            assert entry[key].strip(), f"{vid}:{key} خالی است"


def test_every_v2_use_carries_text_evidence_citation_and_guard():
    for vid, use, v2 in iter_uses():
        for key in ("field", "text", "basis", "cite", "guard"):
            assert use.get(key, "").strip(), f"{vid}: کاربست بی‌{key}"
        assert len(use["cite"]) > 8, f"ارجاعِ کوتاه: {vid}"
        assert len(use["text"].split()) >= 15, f"کاربستِ بسیار کوتاه: {vid}"
        if v2:
            assert len(use["guard"].split()) >= 8, f"{vid}: مرزِ سوءاستفاده کوتاه است"


def test_no_verse_exceeds_four_applications():
    for vid, entry in APP["verses"].items():
        if "uses" in entry:
            assert len(entry["uses"]) <= 4, f"{vid}: بیش از چهار کاربست"


def test_revised_batch_has_exactly_four_documented_uses():
    revised = APP["revision"]
    assert revised["standard"] == "v2"
    covered = [vid for vid, entry in APP["verses"].items() if "uses" in entry]
    assert len(covered) == revised["count"], f"پوششِ بازنویسی‌شده {len(covered)} ≠ {revised['count']}"
    for vid, entry in APP["verses"].items():
        if "uses" in entry:
            assert len(entry["uses"]) == 4, f"{vid}: کاربست‌ها چهارتا نیستند"


def test_use_texts_are_unique_and_fields_vary():
    seen = {}
    for vid, use, _ in iter_uses():
        key = use["text"].strip()
        assert key not in seen, f"تکرارِ کاربست: {vid} و {seen[key]}"
        seen[key] = vid
    fields = {use["field"] for _, use, _ in iter_uses()}
    assert len(fields) >= 20, f"تنوعِ میدان‌ها کم است: {len(fields)}"


def test_no_foreign_script_leaks_into_application_prose():
    import re

    pattern = re.compile(r"[A-Za-z\u0400-\u04FF]+")
    for vid, use, v2 in iter_uses(v2=True):
        for key in ("field", "text", "guard"):
            leaks = pattern.findall(use[key])
            assert not leaks, f"{vid}:{key} واژهٔ غیرفارسی: {leaks}"


def test_method_has_three_gates_and_a_testable_rule():
    method = APP["method"]
    assert len(method["steps"]) == 3
    assert "شرط" in method["rule"]
    assert method["cite"].strip()


def test_fields_cover_more_than_one_domain():
    fields = {use["field"] for _, use, _ in iter_uses()}
    assert len(fields) >= 40, f"تنوعِ میدان‌ها کم است: {len(fields)}"
