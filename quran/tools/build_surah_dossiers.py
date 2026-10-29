# -*- coding: utf-8 -*-
"""Build source-bound, offline surah dossiers from the repository's Quran data."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"

DIACRITICS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u08d4-\u08ff]")
NON_WORD = re.compile(r"[^\w\s\u0600-\u06ff]")
ARABIC_RUN = re.compile(r"[\u0600-\u06ff]+")
LETTER_MAP = str.maketrans({
    "ٱ": "ا", "أ": "ا", "إ": "ا", "آ": "ا",
    "ى": "ی", "ي": "ی", "ئ": "ی", "ؤ": "و",
    "ة": "ه", "ك": "ک", "ـ": " ", "‌": " ",
})

STOP_WORDS = {
    "و", "ف", "ب", "ل", "ک", "فی", "فى", "من", "عن", "على", "الى", "إلى",
    "أن", "إن", "او", "أو", "ام", "أم", "ثم", "بل", "قد", "لقد", "لم", "لن",
    "لا", "ما", "مما", "هل", "يا", "هو", "هي", "هم", "هن", "نحن", "انا", "أنا",
    "انت", "أنت", "الذی", "الذي", "الذين", "التی", "التي", "هذا", "هذه", "ذلك",
    "تلك", "كان", "كانت", "كانوا", "يكون", "تكون", "ليس", "لما", "بما", "حيث",
    "كل", "بين", "بعد", "قبل", "حتى", "اذ", "اذا", "إذ", "إذا", "بسم", "الله",
}

PREFIXES = ("وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ك", "ل")
SUFFIXES = ("هما", "هم", "هن", "كما", "كم", "كن", "ها", "ه", "نا", "ني", "ون", "ين", "ان", "ات", "وا", "ون", "ت")
DEBT_CONTEXT = {"تداين", "تداينتم", "قرض", "قرضا", "اجل", "اجلا", "رهان", "تجارة", "بيع", "اموال", "مال", "تكتب", "كاتب", "اكتبوه", "فاكتبوه"}
PARENT_TERMS = {
    "والد", "والده", "والدي", "والدين", "والدينا", "والدان", "والدة", "والدته",
    "اب", "ابو", "ابوه", "اباه", "ابي", "ابيه", "ابانا", "اباكم", "ابائكم",
    "ابائهم", "اباء", "آباء", "امها", "امه", "امهما", "امهات", "امهاتهم",
    "امك", "امي", "والدتهما", "والدتي", "والدكم", "والدهم",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value: str) -> str:
    value = DIACRITICS.sub("", str(value)).translate(LETTER_MAP)
    value = NON_WORD.sub(" ", value).lower()
    return " ".join(value.split())


def tokens_with_surfaces(text: str) -> list[tuple[str, str]]:
    result = []
    for raw in ARABIC_RUN.findall(text):
        key = normalize(raw)
        if key and " " not in key:
            result.append((raw, key))
    return result


def token_variants(token: str) -> set[str]:
    """Match only whole Quranic forms and transparent clitic variants, not substrings."""
    variants = {token}
    frontier = {token}
    for _ in range(2):
        next_frontier: set[str] = set()
        for current in frontier:
            for prefix in PREFIXES:
                if current.startswith(prefix) and len(current) - len(prefix) >= 3:
                    candidate = current[len(prefix):]
                    if candidate not in variants:
                        variants.add(candidate)
                        next_frontier.add(candidate)
        frontier = next_frontier
        if not frontier:
            break
    for current in tuple(variants):
        if len(current) < 5:
            continue
        for suffix in SUFFIXES:
            if current.endswith(suffix) and len(current) - len(suffix) >= 3:
                variants.add(current[:-len(suffix)])
    return variants


def make_concepts() -> list[dict[str, Any]]:
    legacy = read_json(STATIC / "concept-lexicon.json").get("concepts", [])
    catalog = read_json(STATIC / "topic-catalog.json").get("concepts", [])
    grouped: dict[str, dict[str, Any]] = {}
    for concept in [*legacy, *catalog]:
        title = str(concept.get("title", "")).strip()
        if not title:
            continue
        entry = grouped.setdefault(title, {"title": title, "ids": set(), "terms": set()})
        entry["ids"].add(str(concept.get("id", "")))
        for pair in concept.get("equivalents", []):
            if isinstance(pair, (list, tuple)) and pair:
                term = str(pair[0]).strip()
                normalized = normalize(term)
                if normalized:
                    entry["terms"].add((term, normalized))
    return [
        {"title": item["title"], "ids": item["ids"], "terms": sorted(item["terms"])}
        for item in grouped.values()
    ]


def topic_matches(concept: dict[str, Any], record: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return matched lexicon forms and exact surface witnesses for one verse."""
    tokens = record["tokens"]
    token_forms = [token for _, token in tokens]
    variants = [token_variants(token) for token in token_forms]
    all_forms = set(token_forms).union(*(item for item in variants))
    normalized_text = record["normalizedArabic"]
    ids = concept["ids"]
    matched_terms: list[str] = []
    matched_words: list[str] = []
    for original, term in concept["terms"]:
        term_parts = term.split()
        if not term_parts:
            continue
        # Known homographs need contextual evidence before they can label a topic.
        if "debt" in ids and term == normalize("دين"):
            debt_context = {normalize(item) for item in DEBT_CONTEXT}
            if not (debt_context & set(token_forms)):
                continue
        if "angels" in ids and term == normalize("ملك"):
            angel_markers = {normalize(item) for item in ("ملائكة", "جبريل", "ميكائيل")}
            if not (angel_markers & all_forms):
                continue
        if "afterlife" in ids and term == normalize("جنة") and {normalize("الناس"), normalize("ناس")} & all_forms:
            afterlife_markers = {normalize(item) for item in ("النار", "القيامة", "بعث", "حساب", "ثواب")}
            if not (afterlife_markers & all_forms):
                continue
        if "parents" in ids and term in {normalize("ام"), normalize("اب")}:
            parent_terms = {normalize(item) for item in PARENT_TERMS}
            if not any(normalize(surface) in parent_terms for surface, _ in tokens):
                continue
        if len(term_parts) == 1:
            key = term_parts[0]
            if key in STOP_WORDS and len(key) <= 3:
                continue
            if any(key in form_variants for form_variants in variants):
                matched_terms.append(original)
                for (surface, _), form_variants in zip(tokens, variants):
                    if key in form_variants and surface not in matched_words:
                        matched_words.append(surface)
        else:
            for start in range(len(token_forms) - len(term_parts) + 1):
                if token_forms[start:start + len(term_parts)] == term_parts:
                    matched_terms.append(original)
                    for surface, _ in tokens[start:start + len(term_parts)]:
                        if surface not in matched_words:
                            matched_words.append(surface)
                    break
            # Some source terms are complete phrases with punctuation/spacing variants.
            if original not in matched_terms and f" {term} " in f" {normalized_text} ":
                matched_terms.append(original)
    return list(dict.fromkeys(matched_terms)), matched_words


def build_payload() -> dict[str, Any]:
    corpus = read_json(STATIC / "offline-corpus.json")
    chapters = read_json(ROOT / "data" / "chapters.json").get("chapters", [])
    annotations = read_json(STATIC / "verse-study-annotations.json").get("verses", {})
    tafsir_sources = read_json(STATIC / "tafsir-sources.json").get("sources", [])
    tafsir_payload = read_json(STATIC / "tafsir" / "persian-mokhtasar-quranenc-1.0.0.json")
    commentary = tafsir_payload.get("verses", {})
    commentary_source = next((item for item in tafsir_sources if item.get("id") == "fa_qe_persian_mokhtasar"), None)
    if not commentary_source:
        raise ValueError("منبع المختصر در فهرست منابع پیدا نشد.")

    records: list[dict[str, Any]] = []
    by_surah: dict[int, list[dict[str, Any]]] = defaultdict(list)
    frequency: Counter[str] = Counter()
    for row in corpus.get("verses", []):
        if not isinstance(row, list) or len(row) < 6:
            continue
        surah, ayah, arabic, persian, surah_name, revelation = row[:6]
        tokens = tokens_with_surfaces(arabic)
        for _, key in tokens:
            frequency[key] += 1
        record = {
            "surah": int(surah), "ayah": int(ayah), "arabic": arabic,
            "persian": persian, "surahName": surah_name, "revelation": revelation,
            "reference": f"{int(surah)}:{int(ayah)}", "tokens": tokens,
            "normalizedArabic": normalize(arabic),
        }
        records.append(record)
        by_surah[int(surah)].append(record)

    concepts = make_concepts()
    output_surahs: dict[str, Any] = {}
    globally_used_overview_texts: set[str] = set()
    for chapter in chapters:
        sid = int(chapter["id"])
        rows = by_surah[sid]
        if not rows:
            raise ValueError(f"سورهٔ {sid} در پیکره نیست.")
        rows.sort(key=lambda item: item["ayah"])
        total = len(rows)
        if total != int(chapter["total_verses"]):
            raise ValueError(f"تعداد آیه‌های سورهٔ {sid} با فراداده نمی‌خواند: {total} ≠ {chapter['total_verses']}")

        # Overview anchors sample the opening, midpoint and end. The opening/end
        # can move a few verses to avoid repeating generic commentary on disjoint
        # surahs; each item still points to its exact source note and evidence.
        midpoint = (total + 1) // 2
        middle_window = sorted(range(max(1, midpoint - 3), min(total, midpoint + 3) + 1), key=lambda ayah: (abs(ayah - midpoint), ayah))
        positions = [
            ("آغاز", list(range(1, min(total, 6) + 1))),
            ("میانه", middle_window),
            ("پایان", list(range(total, max(0, total - 6), -1))),
        ]
        overview = []
        seen_messages: set[str] = set()
        seen_references: set[str] = set()
        for stage, ayah_candidates in positions:
            selection = None
            local_fallback = None
            for ayah in ayah_candidates:
                reference = f"{sid}:{ayah}"
                if reference in seen_references:
                    continue
                messages = annotations.get(reference, {}).get("messages", [])
                for message_index, message in enumerate(messages):
                    text = str(message.get("text", "")).strip()
                    if not text or not str(message.get("evidence", "")).strip():
                        continue
                    candidate = (reference, message_index, text)
                    if text not in seen_messages:
                        local_fallback = local_fallback or candidate
                        if text not in globally_used_overview_texts:
                            selection = candidate
                            break
                if selection:
                    break
            selection = selection or local_fallback
            if not selection:
                raise ValueError(f"شاهدِ نمای کلی برای {sid}:{stage} کامل نیست.")
            reference, message_index, text = selection
            seen_messages.add(text)
            seen_references.add(reference)
            globally_used_overview_texts.add(text)
            overview.append({"stage": stage, "reference": reference, "messageIndex": message_index})

        theme_rows: dict[str, dict[str, Any]] = {}
        per_verse_theme_matches: dict[str, set[str]] = defaultdict(set)
        for concept in concepts:
            matches_by_ref: dict[str, dict[str, list[str]]] = {}
            for record in rows:
                terms, witnesses = topic_matches(concept, record)
                if terms:
                    matches_by_ref[record["reference"]] = {"terms": terms, "witnesses": witnesses}
                    per_verse_theme_matches[record["reference"]].add(concept["title"])
            if not matches_by_ref:
                continue
            title = concept["title"]
            aggregate = theme_rows.setdefault(title, {"title": title, "count": 0, "terms": [], "witnesses": [], "references": [], "_allReferences": set()})
            for reference, evidence in matches_by_ref.items():
                if reference not in aggregate["_allReferences"]:
                    aggregate["count"] += 1
                    aggregate["_allReferences"].add(reference)
                    if len(aggregate["references"]) < 4:
                        aggregate["references"].append(reference)
                if reference in aggregate["references"]:
                    for term in evidence["terms"]:
                        if term not in aggregate["terms"] and len(aggregate["terms"]) < 6:
                            aggregate["terms"].append(term)
                    for word in evidence["witnesses"]:
                        if word not in aggregate["witnesses"] and len(aggregate["witnesses"]) < 5:
                            aggregate["witnesses"].append(word)
        themes = sorted(theme_rows.values(), key=lambda item: (-item["count"], item["title"]))[:6]
        for theme in themes:
            theme.pop("_allReferences", None)

        vocabulary_candidates: dict[str, dict[str, Any]] = {}
        for record in rows:
            for raw, key in record["tokens"]:
                if len(key) < 3 or key in STOP_WORDS or frequency[key] > 5:
                    continue
                candidate = {"word": raw, "normalized": key, "reference": record["reference"], "frequency": frequency[key], "ayah": record["ayah"]}
                current = vocabulary_candidates.get(key)
                if current is None or candidate["ayah"] < current["ayah"]:
                    vocabulary_candidates[key] = candidate
        ranked_vocabulary = sorted(vocabulary_candidates.values(), key=lambda item: (item["frequency"], -len(item["normalized"]), item["ayah"], item["normalized"]))
        if len(ranked_vocabulary) < 3:
            raise ValueError(f"برای سورهٔ {sid} سه صورتِ کم‌تکرارِ قابل استناد پیدا نشد.")
        vocabulary = [{key: item[key] for key in ("word", "reference", "frequency")} for item in ranked_vocabulary[:3]]

        # Two exact, unaltered commentary entries are selected from different
        # halves where possible. Selection follows lexical coverage, not a claim
        # that these are the only or universally agreed important readings.
        commentary_chapter = commentary.get(str(sid), {})
        split = max(1, total // 2)
        windows = [(1, split), (split + 1, total)]
        reflections = []
        selected_refs: set[str] = set()
        for low, high in windows:
            candidates = []
            for record in rows:
                ayah = record["ayah"]
                if not low <= ayah <= high:
                    continue
                entry = commentary_chapter.get(str(ayah), {})
                text = str(entry.get("text", "")).strip()
                if not text or len(text) > 360:
                    continue
                score = len(per_verse_theme_matches.get(record["reference"], set()))
                candidates.append((score, abs(len(text) - 190), abs(ayah - ((low + high) / 2)), ayah, text))
            if not candidates:
                for record in rows:
                    ayah = record["ayah"]
                    entry = commentary_chapter.get(str(ayah), {})
                    text = str(entry.get("text", "")).strip()
                    if low <= ayah <= high and text and len(text) <= 600:
                        candidates.append((len(per_verse_theme_matches.get(record["reference"], set())), abs(len(text) - 190), abs(ayah - ((low + high) / 2)), ayah, text))
            if candidates:
                _, _, _, ayah, _ = min(candidates, key=lambda item: (-item[0], item[1], item[2], item[3]))
                reference = f"{sid}:{ayah}"
                if reference not in selected_refs:
                    reflections.append({"reference": reference, "sourceId": commentary_source["id"]})
                    selected_refs.add(reference)
        if len(reflections) < 2:
            candidates = []
            for record in rows:
                reference = record["reference"]
                if reference in selected_refs:
                    continue
                text = str(commentary_chapter.get(str(record["ayah"]), {}).get("text", "")).strip()
                if text:
                    candidates.append((len(per_verse_theme_matches.get(reference, set())), abs(len(text) - 190), record["ayah"]))
            for _, _, ayah in sorted(candidates, key=lambda item: (-item[0], item[1], item[2])):
                reference = f"{sid}:{ayah}"
                reflections.append({"reference": reference, "sourceId": commentary_source["id"]})
                selected_refs.add(reference)
                if len(reflections) == 2:
                    break
        if len(reflections) != 2:
            raise ValueError(f"برای سورهٔ {sid} دو نقلِ تفسیریِ متمایز پیدا نشد.")

        output_surahs[str(sid)] = {
            "name": chapter["name"],
            "revelation": "مکی" if chapter["type"] == "meccan" else "مدنی",
            "verseCount": total,
            "overview": overview,
            "themes": themes,
            "vocabulary": vocabulary,
            "reflections": reflections,
        }

    translation_attribution = str(corpus.get("attribution", ""))
    return {
        "version": 1,
        "editorialMethod": {
            "overview": "نمای کلی، سه ایستگاهِ آغاز/میانه/پایان را از یادداشتِ همان آیه برمی‌گزیند؛ متنِ هر یادداشت با وضعیت و شاهد خودش نمایش داده می‌شود و خلاصهٔ نهاییِ کل سوره ادعا نمی‌شود.",
            "themes": "موضوعات از تطابقِ صورت‌های واژگانیِ صریح در پیکره ساخته می‌شوند؛ پیوندهای مرتبط و ریشه‌سازیِ خودکار وارد فهرست نشده‌اند. هر محور با واژهٔ شاهد و شمارهٔ آیه قابل بازبینی است.",
            "vocabulary": "سه صورتِ کم‌تکرارِ هر سوره بر پایهٔ بسامدِ صورتِ واژه در کل متن انتخاب می‌شوند. این بسامد، دشواری را به‌تنهایی تعیین نمی‌کند؛ ترجمهٔ همان آیه فقط بافت معنایی است، نه معادلِ قطعیِ تک‌واژه.",
            "reflections": "دو نقلِ دقیق از ترجمهٔ فارسی المختصر برای مطالعهٔ آغازین انتخاب شده‌اند؛ گزیده‌بودن به معنای اجماع یا برتریِ مطلق نیست و نقل با متنِ منبع تغییر داده نمی‌شود.",
        },
        "sources": {
            "quran": "متن عربیِ مصحف: Tanzil Uthmani؛ انتساب و شرایط بازنشر در data/ATTRIBUTION.md.",
            "translation": {
                "title": "ترجمهٔ فارسی قرآن",
                "translator": "Ihsan Elahi Zaheer",
                "source": "QuranEnc؛ انتساب و شرایط بازنشر در data/ATTRIBUTION.md.",
                "attribution": translation_attribution,
            },
            "commentary": {
                "id": commentary_source["id"],
                "title": commentary_source["title"],
                "version": commentary_source["version"],
                "source": commentary_source["source"],
                "sourceUrl": commentary_source["sourceUrl"],
                "attribution": commentary_source.get("attribution", ""),
            },
        },
        "surahs": output_surahs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the committed JSON is stale")
    args = parser.parse_args()
    output_path = STATIC / "surah-dossiers.json"
    rendered = json.dumps(build_payload(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not output_path.exists() or output_path.read_text(encoding="utf-8") != rendered:
            print(f"{output_path.relative_to(ROOT)} is stale; run python3 tools/build_surah_dossiers.py", file=sys.stderr)
            return 1
        print(f"OK: {len(json.loads(rendered)['surahs'])} source-bound surah dossiers")
        return 0
    output_path.write_text(rendered, encoding="utf-8")
    print(f"Wrote {output_path.relative_to(ROOT)} ({len(json.loads(rendered)['surahs'])} surahs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
