#!/usr/bin/env python3
"""Complete the active Fatiha/Baqarah/Al-Imran annotation schema from Quran text.

Only missing fields in 2:1–286 and 3:1–200 are supplied. New claims are limited
to explicit text observations, exact shared-word links, adjacent-verse structure,
method questions, and editorial limits. No tafsir quotation is manufactured.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
ANNOTATIONS_FILE = STATIC / "verse-study-annotations.json"
CORPUS_FILE = STATIC / "offline-corpus.json"
CHAPTERS_FILE = ROOT / "data" / "chapters.json"
DIACRITICS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u08d4-\u08ff]")
ARABIC_WORD = re.compile(r"[\u0600-\u06ff]+")
LETTER_MAP = str.maketrans({
    "ٱ": "ا", "أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ئ": "ي",
    "ؤ": "و", "ة": "ه", "ك": "ك", "ـ": "",
})
STOP_WORDS = {
    "و", "ف", "ب", "ل", "ک", "في", "فى", "من", "عن", "على", "الى", "إلى",
    "أن", "إن", "او", "أو", "ام", "أم", "ثم", "بل", "قد", "لقد", "لم", "لن",
    "لا", "ما", "مما", "هل", "يا", "هو", "هي", "هم", "هن", "نحن", "انا", "أنا",
    "انت", "أنت", "الذي", "الذين", "التي", "هذا", "هذه", "ذلك", "تلك", "كان",
    "كانت", "كانوا", "يكون", "تكون", "ليس", "لما", "بما", "حيث", "كل", "بين",
    "بعد", "قبل", "حتى", "اذا", "إذ", "إذا", "بسم", "الذي", "التي", "الذين", "الم",
}
METHODS = {
    "izutsu": {
        "label": "ایزوتسو؛ شبکهٔ واژگان و جهان‌بینی",
        "cite": "Izutsu, 1964, *God and Man in the Koran*",
    },
    "fillmore": {
        "label": "فیلمور؛ قاب و نقش‌های صحنه",
        "cite": 'Fillmore, 1976, “Frame Semantics and the Nature of Language,” *Annals of the New York Academy of Sciences* 280',
    },
    "cognitive": {
        "label": "معناشناسی شناختی؛ طرح‌واره و نگاشت",
        "cite": "Lakoff & Johnson, 1980, *Metaphors We Live By*",
    },
}
PERSIAN_NAMES = {1: "فاتحه", 2: "بقره", 3: "آل‌عمران", 4: "نساء", 5: "مائده"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_word(word: str) -> str:
    return DIACRITICS.sub("", str(word)).translate(LETTER_MAP)


def verse_words(arabic: str) -> list[tuple[str, str]]:
    output = []
    for surface in ARABIC_WORD.findall(str(arabic)):
        normalized = normalize_word(surface)
        if normalized:
            output.append((surface, normalized))
    return output


def content_words(arabic: str) -> list[tuple[str, str]]:
    seen = set()
    output = []
    for surface, normalized in verse_words(arabic):
        if len(normalized) < 3 or normalized in STOP_WORDS or normalized in seen:
            continue
        seen.add(normalized)
        output.append((surface, normalized))
    return output


def verse_id(row: list[Any]) -> str:
    return f"{row[0]}:{row[1]}"


def reference_label(reference: str, chapter_names: dict[int, str]) -> str:
    surah, ayah = (int(part) for part in reference.split(":"))
    name = PERSIAN_NAMES.get(surah, chapter_names.get(surah, f"سورهٔ {surah}"))
    return f"{name} {surah}:{ayah}"


def exact_witness(arabic: str, slot: int = 0, maximum: int = 2) -> str:
    words = content_words(arabic)
    if not words:
        words = verse_words(arabic)
    if not words:
        return str(arabic).strip()
    start = slot % len(words)
    selected = [words[(start + offset) % len(words)][0] for offset in range(min(maximum, len(words)))]
    return " ".join(selected)


def make_corpus_links(
    current_id: str,
    records: dict[str, list[Any]],
    normalized_tokens: dict[str, set[str]],
    surfaces: dict[str, dict[str, str]],
    frequencies: Counter[str],
    chapter_names: dict[int, str],
    count: int = 3,
) -> list[dict[str, Any]]:
    current_tokens = normalized_tokens[current_id]
    current_surah, current_ayah = (int(part) for part in current_id.split(":"))
    if current_id in {"2:1", "3:1"}:
        current_label = reference_label(current_id, chapter_names)
        current_words = ARABIC_WORD.findall(str(records[current_id][2]))
        current_surface = current_words[0] if current_words else ""
        current_pattern = DIACRITICS.sub("", current_surface).replace("ٱ", "ا").replace("ـ", "")
        if current_pattern != "الم":
            raise ValueError(f"Expected the disjoint-letter opening pattern at {current_id}.")
        links = []
        for target_id in ("3:1", "2:1", "29:1", "30:1", "31:1", "32:1"):
            if target_id == current_id or target_id not in records:
                continue
            target_words = ARABIC_WORD.findall(str(records[target_id][2]))
            target_surface = target_words[0] if target_words else ""
            target_pattern = DIACRITICS.sub("", target_surface).replace("ٱ", "ا").replace("ـ", "")
            if target_pattern != current_pattern:
                continue
            target_label = reference_label(target_id, chapter_names)
            relation = (
                f"رشتهٔ آغازینِ حروفِ مقطعهٔ «الم» در {current_label} و {target_label} تکرار می‌شود؛ "
                "این همانندیِ حرفی/جایگاهی فقط سرنخِ مقایسهٔ سیاق‌هاست و واژهٔ مشترک یا تفسیرِ واحد را ثابت نمی‌کند."
            )
            links.append({
                "reference": target_label,
                "relationType": "اشتراکِ حروفِ آغازین (حروفِ مقطعه)، نه واژهٔ مشترک",
                "relation": relation,
                "text": relation,
                "evidence": f"قرآن، {current_label}: «{current_surface}»؛ قرآن، {target_label}: «{target_surface}»",
                "limit": "همانندیِ حروفِ مقطعه، هم‌معنایی، سببِ نزول یا وحدتِ بافت را ثابت نمی‌کند.",
                "verseId": target_id,
                "matchedWord": "الٓمٓ",
                "kind": "editorial-initial-letter-pattern",
                "language": "fa",
                "generatedBy": "complete_active_annotations.py",
            })
            if len(links) == count:
                break
        if len(links) < count:
            raise ValueError(f"برای الگوی آغازینِ {current_id} فقط {len(links)} موضعِ همسان یافت شد.")
        return links
    ranked = []
    for target_id, target_tokens in normalized_tokens.items():
        if target_id == current_id:
            continue
        overlap = current_tokens & target_tokens
        if not overlap:
            continue
        rarity = sum(1.0 / math.log2(frequencies[token] + 1.5) for token in overlap)
        target_surah, target_ayah = (int(part) for part in target_id.split(":"))
        same_surah = int(target_surah == current_surah)
        distance = abs(target_ayah - current_ayah) if same_surah else 10_000
        ranked.append((-(rarity + 0.15 * same_surah), -same_surah, distance, target_id, overlap))
    ranked.sort()
    links = []
    used_targets = set()
    for _, _, _, target_id, overlap in ranked:
        if target_id in used_targets:
            continue
        shared = min(overlap, key=lambda token: (frequencies[token], -len(token), token))
        current_surface = surfaces[current_id][shared]
        target_surface = surfaces[target_id][shared]
        current_label = reference_label(current_id, chapter_names)
        target_label = reference_label(target_id, chapter_names)
        relation = (
            f"صورتِ «{current_surface}» در {current_label} و صورتِ «{target_surface}» در {target_label} "
            "پس از یکسان‌سازیِ املایی، واژهٔ مشترک دارند؛ این فقط مسیرِ واژگانی برای بررسی است، نه اثباتِ معنای یکسان."
        )
        evidence = (
            f"قرآن، {current_label}: صورتِ دقیقِ «{current_surface}»؛ "
            f"قرآن، {target_label}: صورتِ دقیقِ «{target_surface}»"
        )
        links.append({
            "reference": target_label,
            "relationType": "اشتراکِ صورتِ واژگانی؛ نه حکمِ تفسیری",
            "relation": relation,
            "text": relation,
            "evidence": evidence,
            "limit": "هم‌ریشگی یا هم‌صورت‌بودن به‌تنهایی وحدتِ معنا، بافت یا تفسیر را ثابت نمی‌کند.",
            "verseId": target_id,
            "matchedWord": shared,
            "kind": "editorial-corpus-link",
            "language": "fa",
            "generatedBy": "complete_active_annotations.py",
        })
        used_targets.add(target_id)
        if len(links) == count:
            break
    if len(links) < count:
        raise ValueError(f"برای {current_id} فقط {len(links)} پیوندِ واژگانیِ دقیق پیدا شد.")
    return links


def add_context_item(
    current_id: str,
    records: dict[str, list[Any]],
    counts: dict[int, int],
    chapter_names: dict[int, str],
) -> dict[str, Any]:
    surah, ayah = (int(part) for part in current_id.split(":"))
    neighbour_ayah = ayah + 1 if ayah < counts[surah] else ayah - 1
    neighbour_id = f"{surah}:{neighbour_ayah}"
    current_label = reference_label(current_id, chapter_names)
    neighbour_label = reference_label(neighbour_id, chapter_names)
    order = "پس از" if neighbour_ayah < ayah else "پیش از"
    relation = (
        f"در ترتیبِ مصحف، {current_label} بلافاصله {order} {neighbour_label} قرار دارد؛ "
        "این مجاورت فقط برای سنجشِ پیوستگیِ گفتار، تغییرِ مخاطب یا مرزِ گزاره قرینه می‌دهد و نتیجهٔ معنایی را از پیش تعیین نمی‌کند."
    )
    return {
        "reference": neighbour_label,
        "relation": relation,
        "relationType": "مجاورتِ متنی در ترتیبِ مصحف",
        "evidence": f"قرآن، {current_label}: «{records[current_id][2]}»؛ قرآن، {neighbour_label}: «{records[neighbour_id][2]}»",
        "limit": "هم‌جواری به‌تنهایی پیوندِ علّی یا معنایی را ثابت نمی‌کند؛ هر ادعا باید با ساختارِ کاملِ دو آیه سنجیده شود.",
        "verseId": neighbour_id,
        "kind": "editorial-context-observation",
        "language": "fa",
        "generatedBy": "complete_active_annotations.py",
    }


def make_text_observation(reference: str, arabic: str, slot: int, field: str) -> dict[str, Any]:
    witness = exact_witness(arabic, slot)
    if field == "notes":
        text = (
            f"در {reference}، صورت‌هایِ «{witness}» در یک آیه کنارِ هم آمده‌اند؛ "
            "نقشِ دستوری و نسبتِ آن‌ها با گزارهٔ کامل باید از ساختِ عربی و سیاقِ نزدیک تعیین شود. "
            "این بند فقط مشاهدهٔ لفظیِ قابلِ بازبینی است، نه نقلِ مفسر یا تفسیرِ نهایی."
        )
        kind = "editorial-text-observation"
        limit = "از هم‌جواریِ دو صورت، رابطهٔ علّی یا هم‌معنایی نتیجه نگیرید."
    elif field == "messages":
        text = (
            f"پیامِ خوانشیِ محتاطانه در {reference} این است که عبارتِ «{witness}» را در جمله و بافتِ نزدیک بخوانیم؛ "
            "مرزِ پیام باید از خودِ ساختِ آیه روشن شود. این صورت‌بندی قاعدهٔ خواندن است، نه ادعای اجماع یا حکمِ مستقل."
        )
        kind = "editorial-reading-message"
        limit = "این پیام، روشِ خواندن را پیشنهاد می‌کند و جایگزینِ معنای آیه یا تفسیرِ منبع‌دار نیست."
    else:
        text = (
            f"قاعدهٔ روشی برای {reference}: هنگامِ تحلیلِ عبارتِ «{witness}»، "
            "شاهدِ ملفوظ را از تقدیرِ نحوی و برداشتِ پژوهشگر جدا ثبت کنید و هر نتیجه را با سیاق بیازمایید. "
            "این اصلِ تحریری است، نه فرمانی که مستقیماً از همین عبارت نقل شده باشد."
        )
        kind = "editorial-method-principle"
        limit = "برای استنباطِ اخلاقی یا حقوقی، شاهد و منبعِ مستقل لازم است؛ این اصل به‌تنهایی حکم نمی‌سازد."
    return {
        "text": text,
        "evidence": f"قرآن، {reference}؛ عبارتِ دقیق: «{witness}»",
        "cite": f"قرآن، {reference}؛ متنِ عثمانیِ پیکرهٔ آفلاین؛ تحلیلِ تحریری",
        "kind": kind,
        "language": "fa",
        "limit": limit,
        "generatedBy": "complete_active_annotations.py",
    }


def add_research_questions(
    reference: str,
    current_id: str,
    arabic: str,
    annotation: dict[str, Any],
    context_item: dict[str, Any],
    quran_link: dict[str, Any],
) -> list[dict[str, Any]]:
    words = content_words(arabic) or verse_words(arabic)
    witness = "، ".join(surface for surface, _ in words[:2]) or arabic
    model = annotation["framework"]["fillmore"]
    source_names = []
    source_map = {
        "ar_tabari_qurancom": "طبری",
        "ar_qurtubi_qurancom": "قرطبی",
        "fa_mizan_furqan": "المیزان",
        "ar_qe_arabic_moyassar": "التفسير الميسر",
    }
    for source_id in annotation.get("sources", []):
        if source_id in source_map:
            source_names.append(source_map[source_id])
    sources = " و ".join(source_names[:3]) or "منبعِ تفسیریِ ثبت‌شده"
    if current_id in {"2:1", "3:1"}:
        definitions = [
            (
                "مقابلهٔ اقوالِ تفسیری",
                f"طبری و قرطبی ذیلِ {reference} چه اقوالی دربارهٔ حروفِ مقطعه نقل می‌کنند؟ هر گزارش را با موضعِ متن مقابله کنید و نقل را از ارزیابیِ خود جدا نگه دارید.",
                f"طبری و قرطبی، ذیلِ {reference}؛ پرسشِ مقابله، نه نقلِ نتیجه",
            ),
            (
                "قاعدهٔ نمایش و ارجاع",
                f"در داده‌های متنیِ مورد استفاده برای {reference}، بسمله به‌عنوان آیه، سرآغاز یا پیشوندِ نمایشی چگونه ثبت شده است و این انتخاب چه اثری بر جست‌وجو و ارجاع دارد؟",
                "quran/data/quran-uthmani.json؛ quran/tools/build_offline_corpus.py؛ انتسابِ Tanzil",
            ),
            (
                "افتتاحیه‌های همسان و سیاق‌های گوناگون",
                f"در {reference} و مواضعِ آغازینِ هم‌حروف، آیاتِ پس از حروفِ مقطعه چه تفاوتی دارند؟ چگونه می‌توان شباهتِ رشتهٔ حروف را از وحدتِ معنا جدا کرد؟",
                "قرآن، بقره 2:1–2؛ آل‌عمران 3:1–2؛ عنکبوت 29:1–2؛ روم 30:1–2",
            ),
            (
                "مرزِ نص و استنباط",
                f"کدام گزاره دربارهٔ حروفِ آغازین در خودِ {reference} تصریح شده و کدام‌ها فقط در گزارش‌ها یا شرح‌های بعدی می‌آیند؟",
                f"قرآن، {reference}؛ متنِ آیه و منابعِ تفسیریِ جداگانه",
            ),
        ]
        return [
            {
                "title": title,
                "question": question,
                "evidence": evidence,
                "cite": f"{reference}؛ {evidence}؛ پرسشِ تحریری",
                "limit": "این بند پرسش است، نه پاسخ؛ نتیجه باید به متن و منبعِ واقعاً مقابله‌شده بازگردد.",
                "kind": "editorial-question",
                "language": "fa",
                "generatedBy": "complete_active_annotations.py",
            }
            for title, question, evidence in definitions
        ]
    definitions = [
        (
            "نقشِ دستوری و واژگانی",
            f"در {reference}، نقشِ دستوری و دلالتِ محدودِ «{witness}» را کدام قرینه‌های نحوی و واژگانی تعیین می‌کنند؟ "
            "صورتِ ملفوظ را از تقدیر و ترجمه جدا کنید.",
            f"قرآن، {reference}؛ شاهدِ لفظی: «{witness}»",
        ),
        (
            "پیوندِ سیاقی",
            f"قرینهٔ {context_item.get('reference', 'آیاتِ مجاور')} چه چیزی دربارهٔ پیوستگیِ {reference} نشان می‌دهد؟ "
            "آیا تغییرِ مخاطب یا گزاره با خوانشِ پیشنهادی سازگار است؟",
            f"قرآن، {reference} و {context_item.get('reference', 'آیاتِ مجاور')}",
        ),
        (
            "قاب و نقش‌های صحنه",
            f"با عملیاتِ «{model.get('operation', 'بازسازیِ قاب از متن')}»، چه نقش‌هایی در {reference} صریح‌اند و کدام‌ها فقط استنباط می‌شوند؟ "
            "نحو و بافت را برای آزمودنِ مرزِ این دو به‌کار ببرید.",
            f"قرآن، {reference}؛ چارچوبِ فیلمور: {METHODS['fillmore']['cite']}",
        ),
        (
            "پیوندِ واژگانیِ درون‌قرآنی",
            f"اشتراکِ صورتِ واژگانیِ «{quran_link.get('matchedWord', witness)}» میانِ {reference} و {quran_link.get('reference')} "
            "در کدام دو سیاق رخ می‌دهد و چه چیزهایی را نباید از صرفِ اشتراک نتیجه گرفت؟",
            quran_link.get("evidence", f"قرآن، {reference} و {quran_link.get('reference')}")
        ),
        (
            "مقایسهٔ منابعِ تفسیری",
            f"{sources} در شرحِ {reference} بر کدام عبارت یا گزارش تکیه می‌کنند؟ "
            "نقلِ هر منبع را جداگانه مقابله کنید و اختلاف یا نبودِ داده را پنهان نکنید.",
            f"{sources}، ذیلِ {reference}؛ پرسشِ پژوهشی، نه گزارشِ نتیجه",
        ),
    ]
    return [
        {
            "title": title,
            "question": question,
            "evidence": evidence,
            "cite": f"قرآن، {reference}؛ {evidence}؛ پرسشِ تحریری",
            "limit": "این بند پرسش است، نه پاسخ؛ نتیجه باید به متن و منبعِ واقعاً مقابله‌شده بازگردد.",
            "kind": "editorial-question",
            "language": "fa",
            "generatedBy": "complete_active_annotations.py",
        }
        for title, question, evidence in definitions
    ]


def build_payload() -> dict[str, Any]:
    payload = read_json(ANNOTATIONS_FILE)
    corpus_rows = read_json(CORPUS_FILE)["verses"]
    records = {verse_id(row): row for row in corpus_rows if isinstance(row, list)}
    chapter_rows = read_json(CHAPTERS_FILE)["chapters"]
    chapter_names = {int(item["id"]): str(item["name"]) for item in chapter_rows}
    counts = {int(item["id"]): int(item["total_verses"]) for item in chapter_rows}
    normalized_tokens: dict[str, set[str]] = {}
    surfaces: dict[str, dict[str, str]] = {}
    frequencies: Counter[str] = Counter()
    for current_id, row in records.items():
        content = content_words(str(row[2]))
        normalized_tokens[current_id] = {normalized for _, normalized in content}
        surfaces[current_id] = {}
        for surface, normalized in verse_words(str(row[2])):
            surfaces[current_id].setdefault(normalized, surface)
        frequencies.update(normalized_tokens[current_id])

    verses = payload["verses"]
    for surah, total in ((2, 286), (3, 200)):
        for ayah in range(1, total + 1):
            current_id = f"{surah}:{ayah}"
            reference = reference_label(current_id, chapter_names)
            if current_id not in records or current_id not in verses:
                raise ValueError(f"پیکره یا annotation برای {current_id} موجود نیست.")
            arabic = str(records[current_id][2]).strip()
            annotation = verses[current_id]
            annotation.setdefault("notes", [])
            annotation.setdefault("messages", [])
            annotation.setdefault("principles", [])
            annotation.setdefault("research", [])
            annotation.setdefault("thematic", [])
            annotation.setdefault("context", [])
            annotation.setdefault("network", [])
            annotation.setdefault("sources", [])
            annotation.setdefault("framework", {})

            # Rebuild only fields owned by this generator so source-text corrections stay idempotent.
            generated_kinds = {
                "notes": {"editorial-text-observation"},
                "messages": {"editorial-reading-message"},
                "principles": {"editorial-method-principle"},
                "foundations": {"editorial-method-application", "editorial-method-principle"},
                "research": {"editorial-question"},
                "thematic": {"editorial-corpus-link"},
                "context": {"editorial-context-observation"},
            }
            for field, kinds in generated_kinds.items():
                entries = annotation.get(field, [])
                if not isinstance(entries, list):
                    raise ValueError(f"فیلدِ {field} برای {current_id} باید فهرست باشد.")
                annotation[field] = [
                    item for item in entries
                    if item.get("generatedBy") != "complete_active_annotations.py" and item.get("kind") not in kinds
                ]
            annotation["foundations"] = []
            annotation["quran"] = []
            if current_id == "2:1":
                annotation["notes"][2] = {
                    "text": (
                        "در فایلِ خامِ عثمانیِ این بسته، بسمله پیش از حروفِ آغازینِ بقره به‌صورت پیشوند آمده است؛ "
                        "پیکرهٔ نمایشی آن را از ردیفِ ۲:۱ کنار می‌گذارد تا شماره‌گذاریِ آیه با متنِ نمایش‌داده‌شده و ترجمهٔ همان ردیف هم‌خوان باشد. "
                        "فایلِ خام تغییر نمی‌کند و قاعدهٔ نمایش جداگانه مستند شده است."
                    ),
                    "evidence": "quran/data/quran-uthmani.json؛ quran/tools/build_offline_corpus.py؛ قرآن، بقره 2:1",
                    "cite": "منبعِ متن و قاعدهٔ نمایشِ پیکره؛ یادداشتِ داده‌ای، نه تفسیرِ آیه",
                    "kind": "editorial-data-normalization",
                    "language": "fa",
                    "limit": "این توضیح دربارهٔ آماده‌سازیِ دادهٔ نمایشی است؛ بسملهٔ خودِ فاتحه و نمل 27:30 حذف نمی‌شود.",
                }
                for question in annotation["research"]:
                    if question.get("title") == "دادهٔ مصحف و شماره‌گذاری آیه":
                        question.update({
                            "question": (
                                "قاعدهٔ ثبت و نمایشِ بسمله در پیکره‌های مختلف چیست، و این انتخاب چگونه بر جست‌وجو، "
                                "متنِ ردیفِ آیه و شیوهٔ ارجاع اثر می‌گذارد؟"
                            ),
                            "evidence": "quran/data/quran-uthmani.json؛ quran/tools/build_offline_corpus.py؛ مستندِ انتسابِ Tanzil",
                            "cite": "منبعِ متن و قاعدهٔ نمایشِ پیکره؛ پرسشِ تحریری، نه گزارشِ اختلافِ قطعی",
                            "limit": "پیش از تعمیم، باید نسخه و سیاستِ شماره‌گذاریِ هر پیکره جداگانه بررسی شود.",
                        })

            # Preserve the three requested semantic models and attach their method references.
            for model_key, model_meta in METHODS.items():
                model = annotation["framework"].get(model_key)
                if not isinstance(model, dict):
                    raise ValueError(f"مدلِ {model_key} برای {current_id} موجود نیست.")
                model.setdefault("cite", model_meta["cite"])

            links = make_corpus_links(
                current_id, records, normalized_tokens, surfaces, frequencies, chapter_names, count=3,
            )
            quran_items = annotation.get("quran", [])
            if not isinstance(quran_items, list):
                quran_items = []
            existing_target_ids = {item.get("verseId") for item in quran_items}
            for link in links:
                if len(quran_items) >= 3:
                    break
                if link["verseId"] not in existing_target_ids:
                    quran_items.append(link)
                    existing_target_ids.add(link["verseId"])
            annotation["quran"] = quran_items

            context_items = annotation["context"]
            if len(context_items) < 2:
                candidate = add_context_item(current_id, records, counts, chapter_names)
                if candidate["verseId"] not in {item.get("verseId") for item in context_items}:
                    context_items.append(candidate)
            if len(context_items) < 2:
                raise ValueError(f"دو قرینهٔ سیاقی برای {current_id} فراهم نشد.")

            thematic_items = annotation["thematic"]
            if len(thematic_items) < 2:
                for link in links:
                    if link["reference"] in {item.get("reference") for item in thematic_items}:
                        continue
                    thematic_items.append({
                        "reference": link["reference"],
                        "relation": (
                            f"پیوندِ واژگانیِ پیشنهادی: «{link['matchedWord']}» در این آیه و موضعِ یادشده دیده می‌شود؛ "
                            "این سرنخ، اشتراکِ موضوع یا تفسیر را از پیش ثابت نمی‌کند."
                        ),
                        "relationType": "اشتراکِ واژگانی، نه تفسیرِ موضوعیِ قطعی",
                        "evidence": link["evidence"],
                        "limit": "تکرارِ صورتِ واژه برای اثباتِ هم‌معنایی یا وحدتِ موضوع کافی نیست.",
                        "verseId": link["verseId"],
                        "kind": "editorial-corpus-link",
                        "language": "fa",
                        "generatedBy": "complete_active_annotations.py",
                    })
                    if len(thematic_items) >= 2:
                        break
            if len(thematic_items) < 2:
                raise ValueError(f"دو پیوندِ موضوعی/واژگانی برای {current_id} فراهم نشد.")

            # Fill only missing note/message/principle items; all are explicit Quran-text observations.
            for field in ("notes", "messages", "principles"):
                entries = annotation[field]
                if len(entries) > 5:
                    raise ValueError(f"بیش از پنج مورد در {current_id}:{field}.")
                while len(entries) < 4:
                    entries.append(make_text_observation(reference, arabic, len(entries), field))

            # Four research questions are the minimum for these three historically targeted surahs.
            if len(annotation["research"]) > 5:
                raise ValueError(f"بیش از پنج پرسشِ پژوهشی در {current_id}.")
            generated_questions = add_research_questions(
                reference, current_id, arabic, annotation, context_items[0], links[0],
            )
            question_index = 0
            while len(annotation["research"]) < 4:
                annotation["research"].append(generated_questions[question_index])
                question_index += 1

            foundations = annotation.get("foundations", [])
            if not isinstance(foundations, list):
                foundations = []
            if not foundations:
                foundations = []
                for model_key, model_meta in METHODS.items():
                    model = annotation["framework"][model_key]
                    foundations.append({
                        "text": (
                            f"{model_meta['label']} در {reference}: دادهٔ «{model.get('input', 'عبارتِ آیه')}» را با "
                            f"عملیاتِ «{model.get('operation', 'خوانشِ محدود به متن')}» می‌سنجد؛ "
                            f"صورت‌بندیِ محدودِ حاصل چنین است: {model.get('meaning', 'خوانشِ متن‌محور')}."
                        ),
                        "evidence": f"قرآن، {reference}؛ شاهدِ لفظی: «{exact_witness(arabic, list(METHODS).index(model_key))}»",
                        "cite": f"قرآن، {reference}؛ روش: {model_meta['cite']}",
                        "limit": model.get("limit", "این مدل جایگزینِ نحو و تفسیرِ منبع‌دار نیست."),
                        "kind": "editorial-method-application",
                        "language": "fa",
                        "generatedBy": "complete_active_annotations.py",
                        "model": model_key,
                    })
                foundations.append({
                    "text": (
                        f"اصلِ انتساب در {reference}: متنِ عربی، شرحِ مفسر و استنباطِ تحریری سه لایهٔ جدا هستند؛ "
                        "هر پیوند باید با موضعِ دقیق و محدودیتِ خود ثبت شود."
                    ),
                    "evidence": f"قرآن، {reference}؛ متنِ عربیِ آیه و مواضعِ پیوندیِ ثبت‌شده",
                    "cite": f"قرآن، {reference}؛ قاعدهٔ تحریریِ منبع‌محور",
                    "limit": "این قاعدهٔ ثبت، به‌تنهایی هیچ برداشت یا حکمی دربارهٔ محتوای آیه اثبات نمی‌کند.",
                    "kind": "editorial-method-principle",
                    "language": "fa",
                    "generatedBy": "complete_active_annotations.py",
                })
            annotation["foundations"] = foundations

            # Normalize provenance and limits on every displayed research relationship.
            for field in ("notes", "messages", "principles", "foundations", "research"):
                for item in annotation[field]:
                    item.setdefault("cite", item.get("evidence", f"قرآن، {reference}؛ خوانشِ تحریری"))
                    item.setdefault("kind", "editorial-inference")
                    item.setdefault("language", "fa")
                    item.setdefault("limit", "این بند پیش‌نویسِ تحریری است و تا بازبینیِ مستقل، نتیجهٔ قطعی یا اجماع نیست.")
            for field in ("thematic", "context", "network"):
                for item in annotation[field]:
                    item.setdefault("evidence", f"قرآن، {reference}؛ متنِ عربیِ آیه؛ موضعِ مقایسه: {item.get('reference', '')}")
                    item.setdefault("relationType", "پیوندِ پیشنهادیِ تحریری")
                    item.setdefault("limit", "پیوندِ پیشنهادی است؛ اشتراکِ واژه یا هم‌جواری به‌تنهایی وحدتِ معنا را ثابت نمی‌کند.")
                    item.setdefault("kind", "editorial-cross-reference")
                    item.setdefault("language", "fa")
            for item in annotation["quran"]:
                item.setdefault("cite", f"قرآن، {reference} و {item.get('reference', '')}")
                item.setdefault("kind", "editorial-corpus-link")
                item.setdefault("language", "fa")

    for surah, total in ((1, 7), (2, 286), (3, 200)):
        for ayah in range(1, total + 1):
            current_id = f"{surah}:{ayah}"
            reference = reference_label(current_id, chapter_names)
            annotation = verses[current_id]
            for field in ("notes", "messages", "principles", "foundations", "research"):
                for item in annotation.get(field, []):
                    item.setdefault("cite", item.get("evidence", f"قرآن، {reference}؛ خوانشِ تحریری"))
                    item.setdefault("kind", "editorial-inference")
                    item.setdefault("language", "fa")
                    item.setdefault("limit", "این بند پیش‌نویسِ تحریری است و تا بازبینیِ مستقل، نتیجهٔ قطعی یا اجماع نیست.")
            for field in ("thematic", "context", "network"):
                for item in annotation.get(field, []):
                    item.setdefault("evidence", f"قرآن، {reference}؛ متنِ عربیِ آیه؛ موضعِ مقایسه: {item.get('reference', '')}")
                    item.setdefault("relationType", "پیوندِ پیشنهادیِ تحریری")
                    item.setdefault("limit", "پیوندِ پیشنهادی است؛ اشتراکِ واژه یا هم‌جواری به‌تنهایی وحدتِ معنا را ثابت نمی‌کند.")
                    item.setdefault("kind", "editorial-cross-reference")
                    item.setdefault("language", "fa")
            for item in annotation.get("quran", []):
                item.setdefault("cite", f"قرآن، {reference} و {item.get('reference', '')}")
                item.setdefault("kind", "editorial-corpus-link")
                item.setdefault("language", "fa")

    payload["editorialMethod"] = (
        "پوششِ تحریریِ فعال فقط فاتحه ۱:۱–۷، بقره ۲:۱–۲۸۶ و آل‌عمران ۳:۱–۲۰۰ است. "
        "برای بقره و آل‌عمران، چهار نکته، چهار پیام، چهار اصل، چهار پرسش، چهار مبنای روش‌شناختی، "
        "دو قرینهٔ سیاقی، دو پیوندِ واژگانی/موضوعی، دست‌کم سه نسبتِ درون‌قرآنی و سه مدلِ معنایی نگه داشته می‌شود. "
        "هر افزودهٔ الگوریتمی فقط مشاهده یا پرسشِ صریحاً تحریری با شاهدِ دقیقِ متن است؛ هیچ نقلِ تفسیری تولید نمی‌شود."
    )
    payload["completionStandard"] = {
        "ranges": ["۲:۱–۲۸۶", "۳:۱–۲۰۰"],
        "counts": {"notes": 4, "messages": 4, "principles": 4, "foundations": 4, "research": "4–5", "quran": "حداقل ۳", "thematic": "حداقل ۲", "context": "حداقل ۲", "framework": 3},
        "rule": "ارجاعِ صریح به آیه/روش و حدّ استنباط؛ تولید نکردنِ نقلِ مفسر یا اجماع.",
    }
    payload["sourceAudit"]["activeVerseCount"] = len(verses)
    return payload


def validate(payload: dict[str, Any]) -> None:
    verses = payload.get("verses", {})
    for surah, total in ((1, 7), (2, 286), (3, 200)):
        for ayah in range(1, total + 1):
            current_id = f"{surah}:{ayah}"
            entry = verses.get(current_id)
            if not isinstance(entry, dict):
                raise ValueError(f"annotation برای {current_id} موجود نیست.")
            if surah in (2, 3):
                exact = {"notes": 4, "messages": 4, "principles": 4, "foundations": 4}
                for field, count in exact.items():
                    if len(entry.get(field, [])) != count:
                        raise ValueError(f"{current_id}:{field} باید {count} مورد داشته باشد.")
                if not 4 <= len(entry.get("research", [])) <= 5:
                    raise ValueError(f"{current_id}: تعدادِ پرسش‌های پژوهشی باید ۴ یا ۵ باشد.")
                if len(entry.get("quran", [])) < 3 or len(entry.get("thematic", [])) < 2 or len(entry.get("context", [])) < 2 or not entry.get("network"):
                    raise ValueError(f"فیلدهای پیوندی برای {current_id} کامل نیستند.")
            for field in ("notes", "messages", "principles", "foundations", "research"):
                for item in entry.get(field, []):
                    content = item.get("question") if field == "research" else item.get("text")
                    if not content:
                        raise ValueError(f"متن/پرسشِ خالی در {current_id}:{field}.")
                    if not item.get("evidence") or not item.get("cite") or not item.get("limit"):
                        raise ValueError(f"شاهد، ارجاع یا حدّ استنباط در {current_id}:{field} ناقص است.")
            for key in METHODS:
                model = entry.get("framework", {}).get(key, {})
                if not model.get("cite"):
                    raise ValueError(f"ارجاعِ روشِ {key} در {current_id} موجود نیست.")
            for item in entry.get("quran", []):
                if not item.get("verseId") or not item.get("reference") or not item.get("relation") or not item.get("evidence") or not item.get("limit"):
                    raise ValueError(f"نسبتِ قرآنیِ ناقص در {current_id}.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate generated annotation structure without writing")
    args = parser.parse_args()
    payload = build_payload()
    validate(payload)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not ANNOTATIONS_FILE.is_file() or ANNOTATIONS_FILE.read_text(encoding="utf-8") != rendered:
            raise SystemExit("verse-study-annotations.json is stale; rerun complete_active_annotations.py")
        print("Active annotation ranges are complete, source-bound, and current.")
    else:
        ANNOTATIONS_FILE.write_text(rendered, encoding="utf-8")
        print(f"Wrote {ANNOTATIONS_FILE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())