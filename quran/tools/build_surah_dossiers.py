# -*- coding: utf-8 -*-
"""Build source-attributed, verse-traceable dossiers for all 114 surahs.

The large source corpora are intentionally kept outside this checkout. Pass
--sources-dir pointing at a local extraction of the pinned tafsir JSON files.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"

SOURCE_FILES = {
    "tabari": "arabic-tabari-quran-com-api-1.1.json",
    "qurtubi": "arabic-qurtubi-quran-com-api-1.1.json",
    "mizan": "persian-mizan-furqan-2026.json",
    "muyassar": "arabic-moyassar-quranenc-1.0.0.json",
}
SOURCE_IDS = {
    "tabari": "ar_tabari_qurancom",
    "qurtubi": "ar_qurtubi_qurancom",
    "mizan": "fa_mizan_furqan",
    "muyassar": "ar_qe_arabic_moyassar",
}

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
SUFFIXES = ("هما", "هم", "هن", "كما", "كم", "كن", "ها", "ه", "نا", "ني", "ون", "ين", "ان", "ات", "وا", "ت")
DEBT_CONTEXT = {"تداين", "تداينتم", "قرض", "قرضا", "اجل", "اجلا", "رهان", "تجارة", "بيع", "اموال", "مال", "تكتب", "كاتب", "اكتبوه", "فاكتبوه"}
PARENT_TERMS = {
    "والد", "والده", "والدي", "والدين", "والدينا", "والدان", "والدة", "والدته",
    "اب", "ابو", "ابوه", "اباه", "ابي", "ابيه", "ابانا", "اباكم", "ابائكم",
    "ابائهم", "اباء", "آباء", "امها", "امه", "امهما", "امهات", "امهاتهم",
    "امك", "امي", "والدتهما", "والدتي", "والدكم", "والدهم",
}

LEXICAL_HEADING_START = re.compile(
    r"^\s*[\[（(]?\s*(?:\d+\s*[-.)]\s*)?(?:معنى|معناى|معنای|مفردات|"
    r"توضيح\s+كلمات|توضيح\s+لفظ|توضيح\s+كلمه|توضیح\s+کلمات|توضیح\s+لفظ|"
    r"توضیح\s+کلمه|معناى\s+لغوى|معنى\s+كلمه|معنای\s+کلمه|موارد\s+استعمال|"
    r"وجه\s+استعمال|شرح\s+كلمه|شرح\s+لفظ|فرق\s+آن\s+دو|فرق\s+بين)",
    re.IGNORECASE,
)
LEXICAL_MARKER = re.compile(
    r"(?:يعني|معناه|معنى|المراد|في اللغة|أصل|اللغة|تفسيره|تأويله|بمعنى)",
    re.IGNORECASE,
)
CHAIN_START = re.compile(r"^(?:\d+\s*[-.)]\s*)?(?:حدثنا|حدثني|أخبرنا|أنبأنا|ذكر من قال|روى|وروى|رُوي|أثر|حَدَّثَنَا)\b")
PAGE_MARKER = re.compile(r"\[\s*ص\s*[:：]", re.IGNORECASE)
CITATION_MARKER = re.compile(r"\(\s*\d{1,4}\s*\)")
POETRY_MARKER = re.compile(r"(?:قال\s+(?:الشاعر|الراجز)|وقال\s+(?:الشاعر|الراجز)|أنشد|البيت|قصيدة)")
REFERENCE_BACK = re.compile(r"(?:فيما مضى من كتابنا|كما تقدم|قد تقدم|كما ذكرنا|سبق أن بينا|بينا فيما مضى)")


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
    """Match whole Quranic forms and a limited set of transparent clitics."""
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


def prefix_variants(token: str) -> set[str]:
    """Prefix-only matching for explicit lexical headings, avoiding stem guesses."""
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
    return variants


def contiguous_ranges(values: list[int]) -> list[tuple[int, int]]:
    ordered = sorted(set(values))
    if not ordered:
        return []
    ranges = []
    start = previous = ordered[0]
    for value in ordered[1:]:
        if value != previous + 1:
            ranges.append((start, previous))
            start = value
        previous = value
    ranges.append((start, previous))
    return ranges


def format_reference(surah: int, start: int, end: int | None = None) -> str:
    if end is None or end == start:
        return f"{surah}:{start}"
    return f"{surah}:{start}-{end}"


def reference_start(reference: str) -> int:
    try:
        return int(str(reference).split(":", 1)[1].split("-", 1)[0])
    except (IndexError, ValueError):
        return 0


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
            if original not in matched_terms and f" {term} " in f" {normalized_text} ":
                matched_terms.append(original)
    return list(dict.fromkeys(matched_terms)), matched_words


def parse_markdown_sections(text: str) -> list[dict[str, Any]]:
    matches = list(re.finditer(r"(?m)^(#{2,6})[ \t]*(.*?)[ \t]*\r?$", text))
    sections = []
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append({
            "level": len(match.group(1)),
            "title": match.group(2).strip(),
            "body": text[match.end():next_start],
        })
    return sections


def is_surah_range_heading(title: str) -> bool:
    value = normalize(title).strip()
    return value.startswith("سوره ") or value.startswith("سوره") or value.startswith("سورهٔ")


def is_translation_heading(title: str) -> bool:
    value = normalize(title)
    return value.startswith("ترجمه") or value.startswith("ترجمه آيات")


def is_generic_heading(title: str) -> bool:
    value = normalize(title).replace(" ", "")
    generic = {
        normalize(candidate).replace(" ", "")
        for candidate in (
            "بيان", "بیان", "بيان آيات", "بیان آیات", "بحث روايتي", "بحث روایتی",
            "بحث تاريخي", "بحث تاریخی",
        )
    }
    return value in generic


def source_headings(sections: list[dict[str, Any]]) -> list[str]:
    output = []
    for section in sections:
        title = section["title"]
        if not title or is_surah_range_heading(title) or is_translation_heading(title) or is_generic_heading(title):
            continue
        if title not in output:
            output.append(title)
    return output


def exact_paragraphs(body: str) -> list[str]:
    paragraphs = []
    for raw in re.split(r"\n[ \t]*\n+", body):
        paragraph = raw.strip()
        if not paragraph:
            continue
        if paragraph.startswith("```") or paragraph.startswith("<span") or paragraph.startswith("<div"):
            continue
        if re.fullmatch(r"[\s*_`#-]+", paragraph):
            continue
        paragraphs.append(paragraph)
    return paragraphs


def clip_verbatim(text: str, limit: int = 640) -> tuple[str, bool]:
    """Return an exact source substring, never a rewritten or ellipsized quote."""
    text = str(text).strip()
    if len(text) <= limit:
        return text, False
    prefix = text[:limit]
    boundaries = [match.end() for match in re.finditer(r"[.!؟؛](?:\s|$)", prefix)]
    boundary = boundaries[-1] if boundaries and boundaries[-1] >= min(120, limit // 3) else 0
    if not boundary:
        boundary = prefix.rfind(" ")
    if boundary <= 0:
        boundary = limit
    return prefix[:boundary].rstrip(), True


def first_source_excerpt(sections: list[dict[str, Any]], limit: int = 640) -> tuple[str, bool]:
    candidates = []
    for section in sections:
        title = section["title"]
        if section["level"] == 3 and normalize(title).startswith("بيان") and not is_translation_heading(title):
            candidates.append(section)
    if not candidates:
        candidates = [
            section for section in sections
            if section["level"] >= 3 and not is_translation_heading(section["title"])
            and not is_surah_range_heading(section["title"])
        ]
    for section in candidates:
        for paragraph in exact_paragraphs(section["body"]):
            if len(paragraph) < 55 or PAGE_MARKER.search(paragraph):
                continue
            return clip_verbatim(paragraph, limit)
    # If the overview paragraph is absent, use the first substantive Mizan note
    # rather than manufacture a summary from a translation or another corpus.
    for section in sections:
        if section["level"] < 3 or is_translation_heading(section["title"]):
            continue
        for paragraph in exact_paragraphs(section["body"]):
            if len(paragraph) >= 55 and not PAGE_MARKER.search(paragraph):
                return clip_verbatim(paragraph, limit)
    return "", False


def build_mizan_units(mizan: dict[str, Any], chapters: list[dict[str, Any]]) -> tuple[dict[int, list[dict[str, Any]]], dict[int, list[dict[str, Any]]]]:
    mapping = mizan.get("ayahMapping", {})
    contents = mizan.get("contents", {})
    by_surah: dict[int, list[dict[str, Any]]] = defaultdict(list)
    sections_by_surah: dict[int, list[dict[str, Any]]] = defaultdict(list)
    chapter_by_id = {int(item["id"]): item for item in chapters}
    for surah_key, ayah_map in mapping.items():
        surah = int(surah_key)
        if surah not in chapter_by_id:
            raise ValueError(f"المیزان برای سورهٔ خارج از پیکره نگاشت دارد: {surah}")
        by_content: dict[str, list[int]] = defaultdict(list)
        for ayah, content_id in ayah_map.items():
            by_content[str(content_id)].append(int(ayah))
        covered = sorted(int(ayah) for ayah in ayah_map)
        expected = list(range(1, int(chapter_by_id[surah]["total_verses"]) + 1))
        if covered != expected:
            raise ValueError(f"نگاشت آیه‌های المیزان برای سورهٔ {surah} پیوسته و کامل نیست.")
        for content_id, ayahs in by_content.items():
            ranges = contiguous_ranges(ayahs)
            if len(ranges) != 1:
                raise ValueError(f"قطعهٔ المیزان {content_id} برای سورهٔ {surah} بازهٔ ناپیوسته دارد.")
            start, end = ranges[0]
            payload = contents.get(content_id)
            if not payload or not isinstance(payload.get("text"), str):
                raise ValueError(f"متن قطعهٔ المیزان پیدا نشد: سورهٔ {surah}، شناسهٔ {content_id}")
            sections = parse_markdown_sections(payload["text"])
            titles = source_headings(sections)
            excerpt, truncated = first_source_excerpt(sections)
            if not excerpt:
                raise ValueError(f"گزیدهٔ تفسیریِ المیزان برای {surah}:{start}-{end} خالی است.")
            primary = next((
                section["title"] for section in sections
                if section["title"] in titles and section["level"] >= 3
            ), "")
            unit = {
                "reference": format_reference(surah, start, end),
                "start": start,
                "end": end,
                "title": primary,
                "headings": titles,
                "excerpt": excerpt,
                "excerptTruncated": truncated,
                "sourceId": SOURCE_IDS["mizan"],
                "sourceRecordId": content_id,
                "_sections": sections,
            }
            by_surah[surah].append(unit)
            sections_by_surah[surah].extend({**section, "_start": start, "_end": end, "_contentId": content_id} for section in sections)
        by_surah[surah].sort(key=lambda item: (item["start"], item["end"]))
    if set(by_surah) != set(chapter_by_id):
        raise ValueError("نگاشت المیزان برای هر ۱۱۴ سوره در دسترس نیست.")
    return by_surah, sections_by_surah


def find_mizan_word_matches(surah: int, heading: str, start: int, end: int, records_by_surah: dict[int, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Resolve explicit lexical terms in a Mizan heading to exact Quranic forms."""
    if not LEXICAL_HEADING_START.search(heading):
        return []
    quoted_terms = re.findall(r"[«\"]([^»\"]+)[»\"]", heading)
    raw_candidates = []
    if quoted_terms:
        # A short quoted headword is explicit. Long quoted verse fragments are
        # not expanded into many supposed dictionary entries.
        for quoted in quoted_terms:
            quoted_words = ARABIC_RUN.findall(quoted)
            raw_candidates.extend(quoted_words if len(quoted_words) <= 2 else quoted_words[:1])
    else:
        marker = LEXICAL_HEADING_START.search(heading)
        if marker:
            tail = heading[marker.end():].split("﴿", 1)[0].split("(", 1)[0]
            raw_candidates.extend(ARABIC_RUN.findall(tail))
    candidate_keys = list(dict.fromkeys(normalize(item) for item in raw_candidates if normalize(item)))
    candidates = []
    for record in records_by_surah.get(surah, []):
        if not start <= record["ayah"] <= end:
            continue
        for surface, key in record["tokens"]:
            if len(key) < 3 or key in STOP_WORDS:
                continue
            variants = prefix_variants(key)
            matched = next((
                candidate for candidate in candidate_keys
                if candidate in variants or (candidate == normalize("اسم") and key in {normalize("بسم"), normalize("باسم")})
            ), None)
            if matched:
                candidates.append({
                    "word": surface,
                    "normalized": key,
                    "reference": record["reference"],
                    "frequency": record["frequency"].get(key, 0),
                    "candidate": matched,
                    "ayah": record["ayah"],
                })
    # Prefer terms closest to the heading's explicit lexical anchor and avoid
    # returning several inflected forms of the same lemma-like surface.
    output = []
    seen = set()
    for item in sorted(candidates, key=lambda row: (row["frequency"], -len(row["normalized"]), row["ayah"], row["normalized"])):
        if item["normalized"] in seen:
            continue
        output.append(item)
        seen.add(item["normalized"])
        if len(output) == 3:
            break
    return output


def lexical_excerpt_candidates(source_text: str, record: dict[str, Any], source_id: str, frequency: Counter[str]) -> list[dict[str, Any]]:
    candidates = []
    seen_for_verse = set()
    for sentence in re.split(r"(?<=[.!؟؛])\s+|\n+", str(source_text)):
        sentence = sentence.strip()
        if len(sentence) < 45 or len(sentence) > 1400 or PAGE_MARKER.search(sentence):
            continue
        if not LEXICAL_MARKER.search(sentence):
            continue
        if CHAIN_START.search(sentence) or POETRY_MARKER.search(sentence) or REFERENCE_BACK.search(sentence):
            continue
        if CITATION_MARKER.search(sentence):
            continue
        marker = LEXICAL_MARKER.search(sentence)
        if not marker:
            continue
        source_tokens = [(normalize(match.group()), match.start()) for match in ARABIC_RUN.finditer(sentence)]
        matches = []
        for surface, key in record["tokens"]:
            if len(key) < 3 or key in STOP_WORDS or key in seen_for_verse:
                continue
            variants = prefix_variants(key)
            distances = [
                abs(position - marker.start())
                for source_key, position in source_tokens
                if source_key in variants or key in prefix_variants(source_key)
            ]
            if distances and min(distances) <= 180:
                matches.append((min(distances), frequency[key], -len(key), key, surface))
        if not matches:
            continue
        _, _, _, key, surface = min(matches)
        excerpt, truncated = clip_verbatim(sentence, 640)
        if not excerpt:
            continue
        seen_for_verse.add(key)
        candidates.append({
            "words": [{"word": surface, "surface": surface, "reference": record["reference"], "frequency": frequency[key]}],
            "reference": record["reference"],
            "focus": surface,
            "excerpt": excerpt,
            "excerptTruncated": truncated,
            "sourceId": source_id,
            "kind": "source-lexical-excerpt",
            "_ayah": record["ayah"],
            "_position": record["ayah"],
            "_wordKey": key,
        })
    return candidates


def choose_evenly(candidates: list[dict[str, Any]], amount: int, total: int, seen_quotes: set[str] | None = None) -> list[dict[str, Any]]:
    if amount <= 0 or not candidates:
        return []
    seen_quotes = seen_quotes if seen_quotes is not None else set()
    unique = []
    local = set()
    for item in candidates:
        quote_key = normalize(item.get("quote") or item.get("excerpt", ""))
        if not quote_key or quote_key in local or quote_key in seen_quotes:
            continue
        local.add(quote_key)
        unique.append(item)
    if not unique:
        return []
    unique.sort(key=lambda item: (item.get("_position", _ayah_from_item(item)), -item.get("_score", 0)))
    selected = []
    remaining = list(unique)
    for index in range(min(amount, len(unique))):
        target = (index + 0.5) * max(1, total) / min(amount, len(unique))
        best = max(remaining, key=lambda item: (
            item.get("_score", 0) - abs(item.get("_position", _ayah_from_item(item)) - target) / max(1, total) * 5,
            -abs(item.get("_position", _ayah_from_item(item)) - target),
        ))
        selected.append(best)
        remaining.remove(best)
        quote_key = normalize(best.get("quote") or best.get("excerpt", ""))
        seen_quotes.add(quote_key)
    return selected


def _ayah_from_item(item: dict[str, Any]) -> int:
    return reference_start(str(item.get("reference", "")))


def choose_vocabulary_items(candidates: list[dict[str, Any]], amount: int, total: int) -> list[dict[str, Any]]:
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in candidates:
        by_source[item["sourceId"]].append(item)
    available = [source_id for source_id in (SOURCE_IDS["mizan"], SOURCE_IDS["tabari"], SOURCE_IDS["qurtubi"], SOURCE_IDS["muyassar"]) if by_source.get(source_id)]
    if not available:
        return []
    weights = {
        SOURCE_IDS["mizan"]: 0.35,
        SOURCE_IDS["tabari"]: 0.30,
        SOURCE_IDS["qurtubi"]: 0.25,
        SOURCE_IDS["muyassar"]: 0.10,
    }
    quotas = {source_id: 1 for source_id in available}
    while sum(quotas.values()) < amount:
        source_id = max(available, key=lambda key: weights[key] / quotas[key])
        quotas[source_id] += 1
    seen_quotes: set[str] = set()
    selected = []
    for source_id in available:
        selected.extend(choose_evenly(by_source[source_id], quotas[source_id], total, seen_quotes))
    if len(selected) < amount:
        selected.extend(choose_evenly(candidates, amount - len(selected), total, seen_quotes))
    return selected[:amount]


def source_commentary_candidates(source_id: str, source_verses: dict[str, Any], surah: int, rows: list[dict[str, Any]], frequency: Counter[str]) -> list[dict[str, Any]]:
    candidates = []
    chapter = source_verses.get(str(surah), {})
    source_key = next((key for key, value in SOURCE_IDS.items() if value == source_id), "")
    for record in rows:
        entry = chapter.get(str(record["ayah"]), {})
        text = str(entry.get("text", "")).strip()
        if not text:
            continue
        if source_key == "muyassar":
            if len(text) < 35:
                continue
            quote, truncated = clip_verbatim(text, 640)
            candidates.append({
                "reference": record["reference"], "sourceId": source_id,
                "quote": quote, "quoteTruncated": truncated,
                "focus": "", "kind": "source-quote", "_position": record["ayah"],
                "_score": max(0, 350 - abs(len(text) - 260)),
            })
            continue
        for paragraph in re.split(r"\n[ \t]*\n+", text):
            for sentence in re.split(r"(?<=[.!؟؛])\s+|\n+", paragraph):
                sentence = sentence.strip()
                if len(sentence) < 85 or len(sentence) > 1800 or PAGE_MARKER.search(sentence):
                    continue
                if CHAIN_START.search(sentence) or POETRY_MARKER.search(sentence) or REFERENCE_BACK.search(sentence):
                    continue
                if CITATION_MARKER.search(sentence):
                    continue
                normalized = normalize(sentence)
                if not normalized:
                    continue
                score = 0
                if source_key == "tabari":
                    score += 7 if "والصواب" in sentence or "أولى الأقوال" in sentence else 0
                    score += 4 if "اختلف" in sentence or "اختلاف" in sentence else 0
                    score += 2 if "قال أبو جعفر" in sentence else 0
                    score += 1 if any(term in sentence for term in ("يعني", "معنى", "القول")) else 0
                elif source_key == "qurtubi":
                    score += 4 if "اختلف" in sentence or "قلت" in sentence else 0
                    score += 2 if "قوله تعالى" in sentence or "والمعنى" in sentence else 0
                    score += 1 if any(term in sentence for term in ("يعني", "معنى", "قال")) else 0
                score += max(0, 260 - abs(len(sentence) - 300)) / 260
                quote, truncated = clip_verbatim(sentence, 640)
                if len(quote) < 80:
                    continue
                candidates.append({
                    "reference": record["reference"], "sourceId": source_id,
                    "quote": quote, "quoteTruncated": truncated,
                    "focus": "", "kind": "source-quote", "_position": record["ayah"],
                    "_score": score,
                })
    return candidates


def mizan_quote_candidates(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for unit in units:
        used_excerpt = normalize(unit["excerpt"])
        for section in unit["_sections"]:
            title = section["title"]
            if section["level"] < 3 or not title or is_translation_heading(title) or is_surah_range_heading(title):
                continue
            if is_generic_heading(title) or not title.strip():
                continue
            for paragraph in exact_paragraphs(section["body"]):
                if len(paragraph) < 90 or PAGE_MARKER.search(paragraph):
                    continue
                if normalize(paragraph) == used_excerpt:
                    continue
                quote, truncated = clip_verbatim(paragraph, 640)
                if len(quote) < 80:
                    continue
                score = 1
                normalized_title = normalize(title)
                if any(term in normalized_title for term in ("معنى", "معناى", "آهنگ", "غرض", "اختلاف", "پاسخ", "بحث")):
                    score += 3
                candidates.append({
                    "reference": unit["reference"],
                    "sourceId": SOURCE_IDS["mizan"],
                    "quote": quote,
                    "quoteTruncated": truncated,
                    "focus": title,
                    "kind": "source-quote",
                    "_position": (unit["start"] + unit["end"]) / 2,
                    "_score": score,
                })
                break
    return candidates


def reflection_quotas(total: int) -> dict[str, int]:
    amount = min(24, max(4, math.ceil(total / 14)))
    quotas = {
        "mizan": max(1, round(amount * 0.35)),
        "tabari": max(1, round(amount * 0.25)),
        "qurtubi": max(1, round(amount * 0.25)),
    }
    quotas["muyassar"] = max(1, amount - sum(quotas.values()))
    while sum(quotas.values()) > amount:
        key = max((key for key in quotas if quotas[key] > 1), key=lambda item: quotas[item])
        quotas[key] -= 1
    while sum(quotas.values()) < amount:
        key = max(quotas, key=lambda item: (0.35 if item == "mizan" else 0.25 if item in {"tabari", "qurtubi"} else 0.15) - quotas[item] / amount)
        quotas[key] += 1
    return quotas


def modern_research_notes(surah: int, total: int, dossiers: dict[str, Any]) -> list[dict[str, Any]]:
    if surah not in (1, 2):
        return []
    rows = []
    for reference, payload in dossiers.items():
        if not reference.startswith(f"{surah}:"):
            continue
        for note in payload.get("modern", []):
            text = str(note.get("text", "")).strip()
            citation = str(note.get("cite", "")).strip()
            if text and citation:
                rows.append({
                    "reference": reference,
                    "text": text,
                    "citation": citation,
                    "sourceId": "verse-dossier-research",
                    "kind": "modern-research-note",
                    "verbatim": False,
                    "_position": reference_start(reference),
                })
    if not rows:
        return []
    # Up to five distinct, existing study references, spread over the surah.
    selected = []
    used_cites = set()
    for index in range(5):
        target = (index + 0.5) * total / 5
        candidates = [item for item in rows if item["citation"] not in used_cites]
        if not candidates:
            break
        chosen = min(candidates, key=lambda item: (abs(item["_position"] - target), item["_position"], item["citation"]))
        selected.append(chosen)
        used_cites.add(chosen["citation"])
    for item in selected:
        item.pop("_position", None)
    return selected


def clean_source_metadata(registry: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_id = {str(source.get("id")): source for source in registry}
    output = {}
    for key, source_id in SOURCE_IDS.items():
        source = by_id.get(source_id)
        if not source:
            raise ValueError(f"فرادادهٔ منبع {source_id} در tafsir-sources.json پیدا نشد.")
        output[source_id] = {
            field: source[field]
            for field in ("id", "title", "author", "language", "version", "source", "sourceUrl", "permissionUrl", "policyUrl", "attribution", "license", "upstreamCommit", "upstreamRepository", "upstreamCompressedSha256", "upstreamZipSha256", "upstreamDbSha256")
            if field in source and source[field]
        }
    output["verse-dossier-research"] = {
        "id": "verse-dossier-research",
        "title": "یادداشت‌های پژوهشیِ معاصر در پرونده‌های آیه‌ای",
        "author": "بازگویی تحریری؛ ارجاعِ هر مطالعه در همان یادداشت",
        "language": "fa",
        "version": "static/verse-dossiers.json",
        "source": "پرونده‌های آیه‌ایِ موجود در همین پروژه",
        "attribution": "متنِ نمایش‌داده‌شده بازگویی تحریری است، نه نقل مستقیم؛ ارجاعِ کتاب‌شناختیِ ثبت‌شده حفظ شده است.",
    }
    return output


def build_payload(sources_dir: Path) -> dict[str, Any]:
    corpus = read_json(STATIC / "offline-corpus.json")
    chapters = read_json(ROOT / "data" / "chapters.json").get("chapters", [])
    registry = read_json(STATIC / "tafsir-sources.json").get("sources", [])
    verse_dossiers = read_json(STATIC / "verse-dossiers.json").get("verses", {})

    source_payloads = {}
    for key, filename in SOURCE_FILES.items():
        path = sources_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"منبعِ لازم پیدا نشد: {path}; مسیر پوشه را با --sources-dir بدهید.")
        source_payloads[key] = read_json(path)
        expected_id = SOURCE_IDS[key]
        actual_id = source_payloads[key].get("edition", {}).get("id")
        if actual_id and actual_id != expected_id:
            raise ValueError(f"شناسهٔ نسخهٔ {filename} ناهماهنگ است: {actual_id} ≠ {expected_id}")

    records: list[dict[str, Any]] = []
    by_surah: dict[int, list[dict[str, Any]]] = defaultdict(list)
    frequency: Counter[str] = Counter()
    for row in corpus.get("verses", []):
        if not isinstance(row, list) or len(row) < 3:
            continue
        surah, ayah, arabic = int(row[0]), int(row[1]), str(row[2])
        tokens = tokens_with_surfaces(arabic)
        for _, key in tokens:
            frequency[key] += 1
        record = {
            "surah": surah,
            "ayah": ayah,
            "arabic": arabic,
            "reference": f"{surah}:{ayah}",
            "tokens": tokens,
            "normalizedArabic": normalize(arabic),
            "frequency": frequency,
        }
        records.append(record)
        by_surah[surah].append(record)
    for rows in by_surah.values():
        rows.sort(key=lambda item: item["ayah"])

    # Source text for lexicon references is resolved only after corpus-wide
    # normalized form frequencies are known.
    mizan_units, _ = build_mizan_units(source_payloads["mizan"], chapters)
    concepts = make_concepts()
    source_verses = {
        key: source_payloads[key].get("verses", {})
        for key in ("tabari", "qurtubi", "muyassar")
    }
    output_surahs: dict[str, Any] = {}

    for chapter in chapters:
        surah = int(chapter["id"])
        rows = by_surah[surah]
        total = len(rows)
        if total != int(chapter["total_verses"]):
            raise ValueError(f"تعداد آیه‌های سورهٔ {surah} با فراداده نمی‌خواند: {total} ≠ {chapter['total_verses']}")
        units = mizan_units[surah]

        overview = []
        for unit in units:
            overview.append({
                key: unit[key]
                for key in ("reference", "title", "headings", "excerpt", "excerptTruncated", "sourceId", "sourceRecordId")
            })

        # The first two substantive headings in each mapped Mizan passage form
        # an attributed thematic index; the longer outline above preserves every
        # available heading for readers who want the full structure.
        theme_rows: dict[str, dict[str, Any]] = {}
        for unit in units:
            selected_headings = []
            for section in unit["_sections"]:
                title = section["title"]
                if not title or is_surah_range_heading(title) or is_translation_heading(title) or is_generic_heading(title):
                    continue
                if title not in selected_headings:
                    selected_headings.append(title)
                if len(selected_headings) == 2:
                    break
            for title in selected_headings:
                key = normalize(title)
                item = theme_rows.setdefault(key, {
                    "kind": "source-heading",
                    "title": title,
                    "sourceId": SOURCE_IDS["mizan"],
                    "references": [],
                    "_first": unit["start"],
                })
                if unit["reference"] not in item["references"]:
                    item["references"].append(unit["reference"])
                item["_first"] = min(item["_first"], unit["start"])

        lexical_themes = []
        for concept in concepts:
            references = []
            terms = []
            witnesses = []
            matched_verse_count = 0
            for record in rows:
                matched_terms, matched_words = topic_matches(concept, record)
                if not matched_terms:
                    continue
                matched_verse_count += 1
                if record["reference"] not in references and len(references) < 6:
                    references.append(record["reference"])
                if record["reference"] in references:
                    for term in matched_terms:
                        if term not in terms and len(terms) < 6:
                            terms.append(term)
                    for word in matched_words:
                        if word not in witnesses and len(witnesses) < 6:
                            witnesses.append(word)
            if references and witnesses:
                lexical_themes.append({
                    "kind": "lexical-witness",
                    "title": concept["title"],
                    "count": matched_verse_count,
                    "terms": terms,
                    "witnesses": witnesses,
                    "references": references,
                })
        lexical_themes.sort(key=lambda item: (-item["count"], item["title"]))
        themes = sorted(theme_rows.values(), key=lambda item: (item["_first"], item["title"]))
        for item in themes:
            item.pop("_first", None)
        themes.extend(lexical_themes[:8])
        if not themes:
            raise ValueError(f"هیچ محورِ قابل استنادی برای سورهٔ {surah} ساخته نشد.")

        # Vocabulary entries are sourced from explicit lexical headings or from
        # short source passages containing an explicit gloss marker. No verse
        # translation or frequency-only guess is presented as a definition.
        vocabulary_candidates: list[dict[str, Any]] = []
        mizan_seen_words: set[str] = set()
        for unit in units:
            lexical_sections = [
                section for section in unit["_sections"]
                if LEXICAL_HEADING_START.search(section["title"])
                and section["level"] >= 3
                and not is_translation_heading(section["title"])
            ]
            for section in lexical_sections:
                words = [
                    word for word in find_mizan_word_matches(surah, section["title"], unit["start"], unit["end"], by_surah)
                    if word["normalized"] not in mizan_seen_words
                ]
                if not words:
                    continue
                excerpt = next((
                    paragraph for paragraph in exact_paragraphs(section["body"])
                    if len(paragraph) >= 45 and not PAGE_MARKER.search(paragraph)
                ), "")
                if not excerpt:
                    continue
                excerpt, truncated = clip_verbatim(excerpt, 720)
                vocabulary_candidates.append({
                    "kind": "lexical-heading",
                    "words": [
                        {
                            "word": word["candidate"],
                            "surface": word["word"],
                            "reference": word["reference"],
                            "frequency": word["frequency"],
                        }
                        for word in words
                    ],
                    "reference": unit["reference"],
                    "focus": section["title"],
                    "excerpt": excerpt,
                    "excerptTruncated": truncated,
                    "sourceId": SOURCE_IDS["mizan"],
                    "_priority": 0,
                    "_position": unit["start"],
                    "_wordKeys": [word["normalized"] for word in words],
                })
                mizan_seen_words.update(word["normalized"] for word in words)

        lexical_seen = set(mizan_seen_words)
        source_priority = {SOURCE_IDS["tabari"]: 1, SOURCE_IDS["qurtubi"]: 2, SOURCE_IDS["muyassar"]: 3}
        for source_key in ("tabari", "qurtubi", "muyassar"):
            source_id = SOURCE_IDS[source_key]
            for record in rows:
                entry = source_verses[source_key].get(str(surah), {}).get(str(record["ayah"]), {})
                text = str(entry.get("text", "")).strip()
                for item in lexical_excerpt_candidates(text, record, source_id, frequency):
                    word_keys = [key for surface, key in record["tokens"] if normalize(surface) == normalize(item["words"][0]["word"])]
                    key = item.get("_wordKey") or (word_keys[0] if word_keys else "")
                    if not key or key in lexical_seen:
                        continue
                    lexical_seen.add(key)
                    item["_priority"] = source_priority[source_id]
                    item["_wordKeys"] = [key]
                    vocabulary_candidates.append(item)

        vocabulary_candidates.sort(key=lambda item: (item["_position"], item["_priority"], item["focus"]))
        target_vocab = min(60, max(5, math.ceil(total / 8)))
        # Preserve both chapter-wide coverage and source diversity. Each word
        # remains tied to a direct lexical discussion, never frequency alone.
        vocabulary = choose_vocabulary_items(vocabulary_candidates, target_vocab, total)
        for item in vocabulary:
            for key in list(item):
                if key.startswith("_"):
                    item.pop(key, None)
        if len(vocabulary) < 3:
            raise ValueError(f"کمتر از سه مدخلِ واژگانیِ صریح و منبع‌دار برای سورهٔ {surah} پیدا شد: {len(vocabulary)}")

        reflection_pools = {
            "mizan": mizan_quote_candidates(units),
            "tabari": source_commentary_candidates(SOURCE_IDS["tabari"], source_verses["tabari"], surah, rows, frequency),
            "qurtubi": source_commentary_candidates(SOURCE_IDS["qurtubi"], source_verses["qurtubi"], surah, rows, frequency),
            "muyassar": source_commentary_candidates(SOURCE_IDS["muyassar"], source_verses["muyassar"], surah, rows, frequency),
        }
        quotas = reflection_quotas(total)
        used_quotes: set[str] = set()
        reflections = []
        for source_key in ("mizan", "tabari", "qurtubi", "muyassar"):
            selected = choose_evenly(reflection_pools[source_key], quotas[source_key], total, used_quotes)
            reflections.extend(selected)
        if len(reflections) < sum(quotas.values()):
            all_candidates = [item for pool in reflection_pools.values() for item in pool]
            reflections.extend(choose_evenly(all_candidates, sum(quotas.values()) - len(reflections), total, used_quotes))
        if len(reflections) < min(4, sum(quotas.values())):
            raise ValueError(f"برای سورهٔ {surah} کمتر از چهار نقلِ منبع‌دار و متمایز پیدا شد.")
        research_notes = modern_research_notes(surah, total, verse_dossiers)
        reflections.extend(research_notes)
        reflections.sort(key=lambda item: (reference_start(item["reference"]), item.get("sourceId", "")))
        for item in reflections:
            for key in ("_position", "_score"):
                item.pop(key, None)

        output_surahs[str(surah)] = {
            "name": chapter["name"],
            "revelation": "مکی" if chapter["type"] == "meccan" else "مدنی",
            "verseCount": total,
            "overview": overview,
            "themes": themes,
            "vocabulary": vocabulary,
            "reflections": reflections,
        }

    sources = clean_source_metadata(registry)
    return {
        "version": 2,
        "editorialMethod": {
            "overview": "نقشهٔ نمای کلی از ayahMapping المیزان ساخته شده است؛ بازه‌ها از نگاشت واقعیِ آیه به قطعه می‌آیند و گزیده‌ها زیرمجموعهٔ عینِ متن منبع‌اند، نه خلاصه‌سازی یا شماره‌صفحهٔ حدسی.",
            "themes": "عنوان‌های تفسیری عینِ عنوان‌بندیِ المیزان‌اند و به همان اثر نسبت داده می‌شوند؛ نقشهٔ واژگانیِ تکمیلی فقط صورت‌ها و مواضعِ صریح را نشان می‌دهد و به‌تنهایی تفسیر یا اجماع نمی‌سازد.",
            "vocabulary": "مدخل فقط هنگامی درج می‌شود که در عنوانِ لغویِ المیزان یا جملهٔ دارای نشانگرِ شرحِ واژه در متنِ طبری، قرطبی یا المیسر شاهد داشته باشد؛ صورتِ قرآنی و موضعِ دقیق حفظ می‌شود و ترجمهٔ آیه جای مدخل لغوی را نمی‌گیرد.",
            "reflections": "گزیده‌های طبری، قرطبی، المیزان و المیسر نقل‌های مستقل و منتسب به همان اثرند؛ کنار هم بودنشان به‌معنای توافق یا اختلافِ اثبات‌شده نیست. یادداشت‌های پژوهشیِ معاصر، در صورت وجود، بازگوییِ تحریری‌اند نه نقل‌قول؛ ارجاعِ ثبت‌شده حفظ می‌شود.",
        },
        "notice": "پروندهٔ سوره جایگزینِ مراجعه به متن کامل و سنجش اختلاف اقوال نیست؛ ادعای اجماع، فتوا، یا رتبه‌بندی قطعیِ تفسیرها نمی‌کند.",
        "sources": sources,
        "surahs": output_surahs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the committed JSON is stale")
    parser.add_argument(
        "--sources-dir",
        type=Path,
        default=STATIC / "tafsir",
        help="folder holding the pinned Tabari, Qurtubi, Mizan and Muyassar JSON files",
    )
    args = parser.parse_args()
    output_path = STATIC / "surah-dossiers.json"
    try:
        payload = build_payload(args.sources_dir)
    except (FileNotFoundError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not output_path.exists() or output_path.read_text(encoding="utf-8") != rendered:
            print(
                f"{output_path.relative_to(ROOT)} is stale; run python3 tools/build_surah_dossiers.py --sources-dir {args.sources_dir}",
                file=sys.stderr,
            )
            return 1
        print(f"OK: {len(payload['surahs'])} multi-source surah dossiers")
        return 0
    output_path.write_text(rendered, encoding="utf-8")
    print(f"Wrote {output_path.relative_to(ROOT)} ({len(payload['surahs'])} surahs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
