#!/usr/bin/env python3
"""One-off, source-bound builder for Tawbah 9:1–129 review data.

Requires the four allowlisted source snapshots in /tmp/zehnyar-quran-sources.
All editorial annotations remain explicitly marked as drafts.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
SRC = Path("/tmp/zehnyar-quran-sources/static/tafsir")
ARABIC_TRANSLATION = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي", "ء": ""})
DIACRITICS = re.compile(r"[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")
PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
ARABIC_TOKEN = re.compile(r"[\u0621-\u064A\u0671][\u0621-\u064A\u0671\u064B-\u065F\u0670\u06D6-\u06ED\u0640]*")
STOP = set("و ف ب ل ک ك من عن الي علي في ان انما ثم قد لا ما لم لن لو يا اي ها الذين الذي التي هو هي هم هن نحن هذا هذه كل ذو بما كما اذا اذ او حتي لقد قال يقول قوله تعالى الله رسول رسوله الرسول المشركين مشركين المؤمنين مؤمنون الناس الايات ايات ايه القرآن كتاب رب يوم كفر الكافرين توبه المنافقين الحق الرحمن الرحيم".split())


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fa_num(value: int | str) -> str:
    return str(value).translate(PERSIAN_DIGITS)


def norm_arabic(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = DIACRITICS.sub("", text).translate(ARABIC_TRANSLATION)
    text = re.sub(r"[^\u0621-\u064A\u0671]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_with_offsets(text: str):
    out, offsets = [], []
    for index, source_char in enumerate(text):
        if DIACRITICS.fullmatch(source_char) or source_char == "ـ":
            continue
        normalized = unicodedata.normalize("NFKC", source_char).translate(ARABIC_TRANSLATION)
        for char in normalized:
            if "\u0621" <= char <= "\u064A" or char == "\u0671":
                out.append(char)
                offsets.append(index)
            elif out and out[-1] != " ":
                out.append(" ")
                offsets.append(index)
    while out and out[0] == " ":
        out.pop(0)
        offsets.pop(0)
    while out and out[-1] == " ":
        out.pop()
        offsets.pop()
    return "".join(out), offsets


def collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def clip(text: str, limit: int):
    text = collapse(text)
    if len(text) <= limit:
        return text, False
    end = text.rfind(" ", 0, limit)
    if end < limit // 2:
        end = limit
    return text[:end].rstrip(), True


def citation_tanzil(n: int) -> str:
    return f"قرآن، توبه ۹:{fa_num(n)}؛ ترجمهٔ پایهٔ فولادوند، شناسهٔ fa.fooladvand در Tanzil"


def citation_tabari(n: int) -> str:
    return f"طبری، ۳۱۰ق، *جامع البيان عن تأويل آي القرآن*، ذیل توبه ۹:{fa_num(n)}؛ Quran.com API v4، نسخهٔ 1.1"


def citation_qurtubi(n: int) -> str:
    return f"قرطبی، ۶۷۱ق، *الجامع لأحكام القرآن*، ذیل توبه ۹:{fa_num(n)}؛ Quran.com API v4، نسخهٔ 1.1"


def citation_moyassar(n: int) -> str:
    return f"التفسير الميسر، QuranEnc، نسخهٔ 1.0.0، ذیل توبه ۹:{fa_num(n)}"


def citation_mizan(record_id: str, ref_range: str, n: int) -> str:
    return f"المیزان، ترجمهٔ فارسیِ Furqan Apps، نسخهٔ 2026.0، قطعهٔ {record_id}، نگاشتِ {ref_range}، موضعِ توبه ۹:{fa_num(n)}"


def arabic_basis(arabic: str, n_words: int = 4) -> str:
    matches = list(ARABIC_TOKEN.finditer(arabic))
    if not matches:
        return arabic.strip()[:50]
    last = matches[min(n_words - 1, len(matches) - 1)]
    return arabic[matches[0].start():last.end()]


def body_after_title(text: str) -> str:
    chunks = text.split("\n\n", 1)
    return chunks[1] if len(chunks) > 1 else text


def source_fragments(text: str, wanted: int, limit: int = 250, source_name: str = "tabari"):
    body = body_after_title(text)
    if source_name == "qurtubi":
        # Quran.com records often prepend the full verse, then the numbered commentary sections.
        # Start after that source marker so the excerpt is commentary, not merely the quoted verse.
        marker = re.search(r"فيه.{0,80}?مس(?:ألة|ائل)\s*[:：]?", body)
        if marker and marker.end() < len(body):
            body = body[marker.end():]
        else:
            openings = [match.start() for match in re.finditer("قوله تعالى", body)]
            if len(openings) >= 2:
                body = body[openings[1]:]

    blocks = re.split(r"\n\s*\n", body)
    fragments = []
    for block in blocks:
        block = block.strip()
        if not block or block.startswith(("القول في تأويل قوله", "الهوامش", "الهوامش :", "* * *", "-----", "----")):
            continue
        if "الهوامش" in block[:40] or re.fullmatch(r"[\d\s()،.\-]+", block):
            continue
        compact = collapse(block)
        cursor = 0
        while cursor < len(compact) and len(fragments) < wanted:
            if len(compact) - cursor <= limit:
                end = len(compact)
            else:
                end = compact.rfind(" ", cursor + limit // 2, cursor + limit)
                if end <= cursor:
                    end = cursor + limit
            fragment = compact[cursor:end].strip()
            if len(fragment.split()) >= 8:
                fragments.append((fragment, cursor > 0, end < len(compact)))
            cursor = end + 1
            while cursor < len(compact) and compact[cursor].isspace():
                cursor += 1
    return fragments[:wanted]


def mizan_direct_excerpt(raw_text: str, verse_arabic: str):
    marker = raw_text.find("### بيان آيات")
    if marker < 0:
        return None
    body_start = marker
    body = raw_text[body_start:]
    normalized_body, offsets = normalize_with_offsets(body)
    words = norm_arabic(verse_arabic).split()
    candidates = []
    for i, (left, right) in enumerate(zip(words, words[1:])):
        if len(left) < 2 or len(right) < 2 or (left in STOP and right in STOP):
            continue
        candidates.append((left + " " + right, i))
    # Prefer a two-word anchor not made solely of particles; do not treat the verse list or translation
    # above the commentary heading as a direct commentary excerpt.
    candidates.sort(key=lambda pair: (0 if pair[0].split()[0] not in STOP and pair[0].split()[1] not in STOP else 1, pair[1]))
    for phrase, _ in candidates:
        cursor = 0
        while True:
            found = normalized_body.find(phrase, cursor)
            if found < 0:
                break
            cursor = found + len(phrase)
            if found + len(phrase) - 1 >= len(offsets):
                continue
            local_start = offsets[found]
            local_end = offsets[found + len(phrase) - 1] + 1
            para_start = body.rfind("\n\n", 0, local_start) + 2
            para_end = body.find("\n\n", local_end)
            if para_end < 0:
                para_end = len(body)
            paragraph = body[para_start:para_end].strip()
            if not paragraph or paragraph.startswith(("#", "* * *", "```")):
                continue
            # A quoted Qur'anic phrase alone is not commentary. Require visible Persian prose in
            # the same source paragraph before labelling the excerpt as a direct tafsir passage.
            persian_prose_chars = len(re.findall(r"[پچژکگی]", paragraph))
            if persian_prose_chars < 12:
                continue
            if "```arabic" in paragraph or "```farsi" in paragraph:
                continue
            if local_end - local_start < 4:
                continue
            start = para_start
            end = para_end
            if end - start > 320:
                start = max(para_start, local_start - 110)
                end = min(para_end, local_start + 220)
                if start > para_start:
                    previous_space = body.rfind(" ", para_start, start)
                    if previous_space >= para_start:
                        start = previous_space + 1
                if end < para_end:
                    next_space = body.find(" ", end, para_end)
                    if next_space >= 0:
                        end = next_space
            excerpt = collapse(body[start:end])
            if len(excerpt.split()) >= 8:
                return {
                    "excerpt": excerpt,
                    "truncated": start > para_start or end < para_end,
                    "truncated_start": start > para_start,
                    "truncated_end": end < para_end,
                    "anchor": phrase,
                    "raw_excerpt": collapse(body[start:end]),
                }
    return None


def source_item(source_name: str, n: int, fragment: str, truncated_start: bool, truncated_end: bool, index: int):
    if source_name == "tabari":
        cite, sid, author = citation_tabari(n), "ar_tabari_qurancom", "طبری"
    else:
        cite, sid, author = citation_qurtubi(n), "ar_qurtubi_qurancom", "قرطبی"
    quote = f"{'…' if truncated_start else ''}«{fragment}»{'…' if truncated_end else ''}"
    text = f"نقلِ مستقیمِ عربیِ {author} برای توبه ۹:{fa_num(n)}، برشِ {fa_num(index)}: {quote}. این عبارت از رکوردِ همان آیه است؛ ترجمه یا اجماعِ تفسیری نیست."
    return {
        "text": text,
        "cite": cite,
        "sourceId": sid,
        "sourceRecordId": str(n),
        "sourceExcerptTruncated": bool(truncated_start or truncated_end),
    }


def source_gap_item(n: int, source_name: str, raw_text: str, index: int):
    if source_name == "tabari":
        cite, sid, author = citation_tabari(n), "ar_tabari_qurancom", "طبری"
    else:
        cite, sid, author = citation_qurtubi(n), "ar_qurtubi_qurancom", "قرطبی"
    body = collapse(body_after_title(raw_text))
    if body:
        fragment, truncated = clip(body, 85)
        ellipsis = "…" if truncated else ""
        description = f"در رکوردِ {author} برای توبه ۹:{fa_num(n)} تنها برشِ کوتاهِ «{fragment}»{ellipsis} در این موضع انتخاب شد؛"
    else:
        description = f"در رکوردِ {author} برای توبه ۹:{fa_num(n)} شرحِ جداگانه‌ای بازیابی نشد؛"
    text = f"یادداشتِ محدودیتِ منبع، موردِ {fa_num(index)}: {description} آن را شرحِ جامع یا اجماع نخوان و خلأِ داده را با نقلِ ساخته‌شده پُر نکن."
    return {
        "text": text,
        "cite": cite,
        "sourceId": sid,
        "sourceRecordId": str(n),
        "sourceExcerptTruncated": True,
    }


def get_source_items(source_payload, source_name: str, n: int, count: int):
    record = source_payload["verses"]["9"][str(n)]
    raw_text = record.get("text", "")
    source_text = collapse(raw_text)
    fragments = source_fragments(raw_text, count, source_name=source_name)
    assert all(collapse(fragment) in source_text for fragment, _, _ in fragments), (source_name, n)
    items = [source_item(source_name, n, fragment, truncated_start, truncated_end, i + 1) for i, (fragment, truncated_start, truncated_end) in enumerate(fragments)]
    while len(items) < count:
        items.append(source_gap_item(n, source_name, record.get("text", ""), len(items) + 1))
    return items, record


def mizan_reference(record_id: str, raw: str, overview_by_id: dict):
    segment = overview_by_id.get(record_id)
    if segment:
        raw_range = segment["reference"]
        # Preserve the source's range; render its digits in Persian for display.
        return segment, raw_range.translate(PERSIAN_DIGITS).replace("-", "–")
    match = re.search(r"آيات\s+(\d+)\s+تا\s+(\d+)", raw)
    if match:
        raw_range = f"9:{match.group(1)}-{match.group(2)}"
        return {"reference": raw_range, "title": "بازهٔ ثبت‌شده در قطعهٔ منبع"}, raw_range.translate(PERSIAN_DIGITS).replace("-", "–")
    return {"reference": "9:1-129", "title": "بازهٔ ثبت‌شده در قطعهٔ منبع"}, "۹:۱–۱۲۹"


def find_related_verse(n: int, tokens_by_verse: dict):
    current = tokens_by_verse[n]
    candidates = [word for word in current if word not in STOP and len(word) >= 4 and word != "الله"]
    for word in candidates:
        matches = [other for other in range(1, 130) if other != n and word in tokens_by_verse[other]]
        if matches:
            other = min(matches, key=lambda value: (abs(value - n), value))
            return word, other
    return None


def main(source_dir: Path = SRC):
    corpus = load_json(STATIC / "offline-corpus.json")["verses"]
    corpus9 = {int(row[1]): row for row in corpus if isinstance(row, list) and int(row[0]) == 9}
    assert set(corpus9) == set(range(1, 130))
    tabari = load_json(source_dir / "arabic-tabari-quran-com-api-1.1.json")
    qurtubi = load_json(source_dir / "arabic-qurtubi-quran-com-api-1.1.json")
    moyassar = load_json(source_dir / "arabic-moyassar-quranenc-1.0.0.json")
    mizan = load_json(source_dir / "persian-mizan-furqan-2026-all.json")
    overview = load_json(STATIC / "surah-dossiers.json")["surahs"]["9"]["overview"]
    overview_by_id = {str(section["sourceRecordId"]): section for section in overview}
    # The mapping is authoritative; overview rows carry the same immutable source record IDs.
    if set(overview_by_id) != set(mizan["ayahMapping"]["9"].values()):
        # Keep the exact mapping's range even if the overview metadata is incomplete.
        overview_by_id = {str(section["sourceRecordId"]): section for section in overview}

    tokens_by_verse = {n: norm_arabic(corpus9[n][2]).split() for n in range(1, 130)}
    new_dossiers, new_applications = {}, {}
    new_annotations = {}
    direct_mizan_count = 0
    mizan_missing = []
    tabari_direct_count = tabari_gap_count = 0
    qurtubi_direct_count = qurtubi_gap_count = 0

    for n in range(1, 130):
        row = corpus9[n]
        _, _, arabic, translation, surah_name, revelation = row
        verse_id = f"9:{n}"
        verse_ref = f"توبه ۹:{fa_num(n)}"
        basis = arabic_basis(arabic, 4)
        basis_clean = collapse(basis)
        translation_excerpt, translation_truncated = clip(translation, 210)
        assert translation_excerpt == collapse(translation)[:len(translation_excerpt)], verse_id
        trans_quote = f"«{translation_excerpt}{'…' if translation_truncated else ''}»"
        tanzil_cite = citation_tanzil(n)
        mizan_record_id = str(mizan["ayahMapping"]["9"][str(n)])
        mizan_record = mizan["contents"][mizan_record_id]
        section, reference_range = mizan_reference(mizan_record_id, mizan_record.get("text", ""), overview_by_id)
        mizan_result = mizan_direct_excerpt(mizan_record.get("text", ""), arabic)
        mizan_cite = citation_mizan(mizan_record_id, reference_range, n)
        if mizan_result:
            assert mizan_result["excerpt"] in collapse(mizan_record.get("text", "")), (verse_id, mizan_record_id)
            direct_mizan_count += 1
            mizan_modern = {
                "text": f"نقلِ مستقیمِ فارسیِ المیزان در توبه ۹:{fa_num(n)}: {'…' if mizan_result['truncated_start'] else ''}«{mizan_result['excerpt']}»{'…' if mizan_result['truncated_end'] else ''}. این گزیده از متنِ همان شرح است؛ نه اجماع یا تأییدِ مستقل.",
                "cite": mizan_cite,
                "sourceId": "fa_mizan_furqan",
                "sourceRecordId": mizan_record_id,
                "referenceRange": reference_range,
                "sourceExcerptTruncated": bool(mizan_result["truncated"]),
            }
        else:
            mizan_missing.append(n)
            mizan_modern = {
                "text": f"در قطعهٔ {mizan_record_id} با نگاشتِ {reference_range}، در بخشِ شرحِ المیزان برای عبارتِ توبه ۹:{fa_num(n)} برشِ مستقیمِ قابلِ انتساب بازیابی نشد؛ این گزارشِ محدودیتِ گزیده است، نه ادعایِ نبودِ تفسیر.",
                "cite": mizan_cite,
                "sourceRecordId": mizan_record_id,
                "referenceRange": reference_range,
                "sourceExcerptTruncated": False,
            }

        tabari_items, tabari_record = get_source_items(tabari, "tabari", n, 3)
        qurtubi_items, qurtubi_record = get_source_items(qurtubi, "qurtubi", n, 2)
        tabari_direct_count += sum(item["text"].startswith("نقلِ مستقیمِ عربیِ") for item in tabari_items)
        tabari_gap_count += sum(item["text"].startswith("یادداشتِ محدودیتِ منبع") for item in tabari_items)
        qurtubi_direct_count += sum(item["text"].startswith("نقلِ مستقیمِ عربیِ") for item in qurtubi_items)
        qurtubi_gap_count += sum(item["text"].startswith("یادداشتِ محدودیتِ منبع") for item in qurtubi_items)
        classical = tabari_items + qurtubi_items
        moyassar_record = moyassar["verses"]["9"][str(n)]
        moyassar_excerpt, moyassar_truncated = clip(moyassar_record.get("text", ""), 520)
        assert moyassar_excerpt == collapse(moyassar_record.get("text", ""))[:len(moyassar_excerpt)], verse_id
        modern_moyassar = {
            "text": f"نقلِ مستقیمِ عربیِ التفسير الميسر برای توبه ۹:{fa_num(n)}: «{moyassar_excerpt}{'…' if moyassar_truncated else ''}». این متن از نسخهٔ منبع است؛ ترجمه یا خلاصهٔ فارسیِ برنامه نیست.",
            "cite": citation_moyassar(n),
            "sourceId": "ar_qe_arabic_moyassar",
            "sourceRecordId": str(n),
            "sourceExcerptTruncated": bool(moyassar_truncated),
        }
        modern = [
            modern_moyassar,
            mizan_modern,
            {
                "text": f"در {verse_ref}، هم‌نشینیِ عبارتِ «{basis_clean}» را با سیاقِ نزدیک و واژه‌های همان سوره بررسی کن؛ این پرسشِ روش‌شناختی است، نه نتیجه‌ای که از یک واژه قطعی شود.",
                "cite": "Izutsu, *God and Man in the Koran*, 1964",
            },
            {
                "text": f"برای {verse_ref}، نقش‌های گفتار یا رویدادِ نهفته در «{basis_clean}» را به‌صورت پرسش ثبت کن؛ قابِ زبانی جایِ نحوِ عربی یا تفسیرِ منبع‌دار را نمی‌گیرد.",
                "cite": "Fillmore, “Frame Semantics and the Nature of Language,” *Annals of the New York Academy of Sciences* 280 (1976), 20–32",
            },
            {
                "text": f"در خوانشِ تاریخیِ {verse_ref}، گزارشِ منبع، ترتیبِ مصحف و فرضیهٔ زمینه را از هم جدا نگه دار؛ بدون شاهدِ مستقل، سببِ نزول یا تاریخِ قطعی نساز.",
                "cite": "Sinai, *The Qur’an: A Historical-Critical Introduction*, Edinburgh University Press, 2017",
            },
        ]

        previous_n = max(1, n - 1)
        next_n = min(129, n + 1)
        window = f"توبه ۹:{fa_num(previous_n)}–{fa_num(next_n)}"
        related = find_related_verse(n, tokens_by_verse)
        if related:
            repeated_word, related_n = related
            repeated_relation = f"صورتِ «{repeated_word}» پس از یکسان‌سازیِ حرکات در توبه ۹:{fa_num(n)} و توبه ۹:{fa_num(related_n)} دیده می‌شود؛ این هم‌نماییِ لفظی به‌تنهایی هم‌معنایی یا وحدتِ حکم را ثابت نمی‌کند."
            repeated_ref = f"توبه ۹:{fa_num(n)} و ۹:{fa_num(related_n)}"
        else:
            repeated_word, related_n = "", next_n
            repeated_relation = f"در این بررسی پیوندِ واژگانیِ تکرارشونده‌ای برای {verse_ref} انتخاب نشد؛ پیوندِ نزدیک فقط بازهٔ {window} است و از مجاورت به‌تنهایی معنا یا سببِ نزول نتیجه نمی‌شود."
            repeated_ref = window

        notes = [
            {"text": f"شاهدِ ترجمهٔ پایه برای {verse_ref}: {trans_quote} این نقل، برگردانِ فولادوند است و باید از متنِ عربی و شرحِ تفسیری جدا بماند.", "cite": tanzil_cite},
            {"text": f"در {verse_ref}، عبارتِ «{basis_clean}» را عیناً از ترجمه و گزارشِ مفسران جدا ثبت کن؛ نکتهٔ زبانی باید با صورتِ عربی و قرینهٔ نزدیک آزموده شود.", "cite": f"قرآن، توبه ۹:{fa_num(n)}؛ {tanzil_cite}؛ Izutsu, *God and Man in the Koran*, 1964"},
            {"text": f"در {verse_ref}، دامنهٔ قطعهٔ المیزان «{reference_range}» است؛ {'برشِ مستقیمِ بندِ شرح فقط به‌عنوانِ متنِ همان منبع ثبت شد' if mizan_result else 'برشِ مستقیمِ قابلِ انتساب بازیابی نشد'}؛ نبودِ برش را نبودِ تفسیر ندان.", "cite": mizan_cite, **({k: mizan_modern[k] for k in ("sourceId", "sourceRecordId", "referenceRange", "sourceExcerptTruncated") if k in mizan_modern})},
            {"text": f"برای خواندنِ {verse_ref}، آیاتِ مجاورِ {window} را کنارِ عبارتِ کانونی بگذار؛ هم‌جواری قرینهٔ متنی است، نه به‌تنهایی گزارشِ تاریخی یا سببِ نزول.", "cite": f"قرآن، {window}؛ ترجمهٔ پایهٔ فولادوند، شناسهٔ fa.fooladvand در Tanzil"},
            {"text": f"گزارش‌های طبری و قرطبی دربارهٔ {verse_ref} جداگانه مقابله شوند؛ همانندیِ دو برش را اجماع نخوان و تفاوتِ نقل، تفسیر و برداشتِ تحریری را روشن نگه دار.", "cite": f"{citation_tabari(n)}؛ {citation_qurtubi(n)}"},
        ]
        context = [
            {"text": f"پنجرهٔ پیشنهادی برای {verse_ref} بازهٔ {window} است؛ پیوندِ نحوی و واژگانیِ آیه با پیش و پس را ثبت کن، بی‌آنکه از ترتیبِ مصحف تاریخِ نزول بسازی.", "cite": f"قرآن، {window}؛ ترجمهٔ پایهٔ فولادوند، شناسهٔ fa.fooladvand در Tanzil"},
            {"text": f"در نمایهٔ قطعهٔ {mizan_record_id}، توبه ۹:{fa_num(n)} ذیلِ بازهٔ «{reference_range}» و عنوانِ «{section.get('title', 'بازهٔ ثبت‌شده در منبع')}» آمده است؛ این عنوان و دامنه از همان منبع است، نه داوریِ قطعیِ برنامه.", "cite": mizan_cite},
            {"text": f"برای زمینهٔ تفسیریِ {verse_ref}، متنِ طبری و قرطبی را در موضعِ همان آیه جدا بخوان؛ نقلِ تاریخیِ هر کدام باید با نامِ راوی و عبارتِ منبع سنجیده شود.", "cite": f"{citation_tabari(n)}؛ {citation_qurtubi(n)}"},
            {"text": f"التفسير الميسر برای {verse_ref} برشِ عربیِ نسخه‌دار دارد؛ آن را یک خوانشِ معاصرِ مشخص بدان و با ترجمهٔ پایه یا قولِ کهن یکی نکن.", "cite": citation_moyassar(n)},
            {"text": repeated_relation, "cite": f"قرآن، {repeated_ref}؛ متنِ عربیِ مصحفِ عثمانی در پیکرهٔ محلی"},
        ]
        critical = [
            {"text": f"خطرِ خوانشِ جداافتاده در {verse_ref}: «{basis_clean}» را در پنجرهٔ {window} بخوان؛ به‌ویژه دستور یا وصفِ همین سیاق را به همهٔ گروه‌ها و زمان‌ها تعمیم نده.", "cite": f"قرآن، {window}؛ ترجمهٔ پایهٔ فولادوند، شناسهٔ fa.fooladvand در Tanzil"},
            {"text": f"پرسشِ ترجمه در {verse_ref}: افزوده‌های داخلِ کروشه در فولادوند را از برابرنهادِ لفظی جدا کن؛ ترجمه شاهدِ برگردان است، نه نقلِ مستقیمِ هیچ تفسیر.", "cite": tanzil_cite},
            {"text": f"نقدِ منبع در {verse_ref}: طبری، قرطبی، المیسر و المیزان متن‌ها و روش‌های یکسان ندارند؛ نبودنِ برشِ مستقیم از یک قطعه را نبودِ تفسیر یا توافقِ منابع معرفی نکن.", "cite": f"{citation_tabari(n)}؛ {citation_qurtubi(n)}؛ {citation_moyassar(n)}؛ {mizan_cite}"},
            {"text": f"مرزِ گزارشِ تاریخی در {verse_ref}: هم‌جواریِ آیات، تیترِ یک قطعه یا شهرتِ یک روایت به‌تنهایی شأنِ نزول را ثابت نمی‌کند؛ هر ادعا را به گزارشِ مستقل و قابلِ بازیابی ببند.", "cite": f"قرآن، {window}؛ Sinai, *The Qur’an: A Historical-Critical Introduction*, 2017"},
            {"text": f"حدِّ قیاس در {verse_ref}: چارچوبِ زبانی فقط پرسش می‌سازد؛ اگر برای «{basis_clean}» منبعِ بیرونیِ مرتبط و شاهدِ مستقیم نیست، عدمِ انطباق را ثبت کن و ادعای علمی، حقوقی یا حکمِ امروز نساز.", "cite": "Fillmore, “Frame Semantics and the Nature of Language,” 1976, *Annals of the New York Academy of Sciences* 280, 20–32"},
        ]
        research = [
            {"text": f"پرسشِ واژگانی دربارهٔ {verse_ref}: ساخت و کارکردِ «{basis_clean}» در نحوِ آیه چیست و کدام بخش از پاسخ، دادهٔ صرفی است و کدام بخش گزارشِ مفسر؟", "cite": f"قرآن، توبه ۹:{fa_num(n)}؛ {citation_tabari(n)}؛ {citation_qurtubi(n)}"},
            {"text": f"در {verse_ref}، طبری و قرطبی کدام توضیح‌های جداگانه را برای عبارتِ «{basis_clean}» ثبت می‌کنند و اختلافِ آن‌ها چگونه باید از ترجمهٔ فولادوند تفکیک شود؟", "cite": f"{citation_tabari(n)}؛ {citation_qurtubi(n)}؛ {tanzil_cite}"},
            {"text": f"برگردانِ «{basis_clean}» در ترجمهٔ پایهٔ {verse_ref} چه انتخابی دارد؛ آیا التفسير الميسر همان واحدِ عربی را توضیح می‌دهد یا عبارتِ دیگری را برجسته می‌کند؟", "cite": f"{tanzil_cite}؛ {citation_moyassar(n)}"},
            {"text": f"قطعهٔ المیزان با نگاشتِ «{reference_range}» چه شاهدِ مستقیمی برای {verse_ref} دارد؛ اگر برشِ موضع‌دار بازیابی نشد، چه چیزی را نباید از عنوانِ کلِ قطعه نتیجه گرفت؟", "cite": mizan_cite},
            {"text": f"آیا برای {verse_ref} پیوندِ میان‌رشته‌ایِ مستقیم و منبع‌دار با موضوعِ «{basis_clean}» وجود دارد؛ چه شاهدی آن را از شباهتِ لفظی جدا می‌کند و در نبودِ شاهد، چرا ثبتِ عدمِ انطباق دقیق‌تر است؟", "cite": "قرآن، توبه ۹؛ Fillmore, “Frame Semantics and the Nature of Language,” 1976; Sinai, *The Qur’an: A Historical-Critical Introduction*, 2017"},
        ]
        new_dossiers[verse_id] = {
            "title": f"{verse_ref}؛ پروندهٔ منبع‌محور",
            "notes": notes,
            "context": context,
            "classical": classical,
            "modern": modern,
            "critical": critical,
            "research": research,
            "reviewStatus": "پیش‌نویس تحریری؛ نیازمند بازبینی تخصصی",
        }

        app_uses = [
            {
                "field": "واژه‌کاوی و ساخت",
                "text": f"در {verse_ref}، ساختِ عبارتِ «{basis_clean}» را از نظرِ صورت و پیوندِ اجزا بررسی کن؛ سپس گزارشِ طبری و قرطبی را کنارِ لفظ بگذار و دادهٔ دستوری را از قولِ مفسر جدا ثبت کن.",
                "basis": basis,
                "cite": f"{citation_tabari(n)}؛ {citation_qurtubi(n)}",
                "guard": "این تمرین تحلیلِ زبان است؛ نقلِ یک مفسر را اجماع یا معنای یگانه نخوان و از یک ساختِ دستوری حکمِ امروز استخراج نکن.",
            },
            {
                "field": "سیاق و پیوند قرآنی",
                "text": f"{verse_ref} را در پنجرهٔ {window} بخوان؛ برای هر پیوند، دو شاهدِ لفظی ثبت کن و هم‌جواری را به‌تنهایی سببِ نزول یا حکمِ اجرایی ندان.",
                "basis": basis,
                "cite": f"قرآن، {window}؛ ترجمهٔ پایهٔ فولادوند، شناسهٔ fa.fooladvand در Tanzil",
                "guard": "پنجرهٔ نزدیک فقط قرینهٔ متنی است؛ بدونِ گزارشِ مستقل از آن تاریخِ نزول، سببِ خاص یا تعمیم به اشخاصِ امروز نتیجه نگیر.",
            },
            {
                "field": "مقایسهٔ اقوال تفسیری",
                "text": f"در {verse_ref}، گزارشِ طبری و قرطبی را دربارهٔ «{basis_clean}» با التفسير الميسر و قطعهٔ نگاشت‌شدهٔ المیزان مقابله کن؛ هم‌پوشانی، اختلاف و نبودِ برشِ مستقیم را جدا ثبت کن.",
                "basis": basis,
                "cite": f"{citation_tabari(n)}؛ {citation_qurtubi(n)}؛ {citation_moyassar(n)}؛ {mizan_cite}",
                "guard": "تفاوتِ متنِ قرآن، ترجمه، گزارشِ مفسر و برداشتِ تحریری را صریح نگه دار؛ نبودِ گزیده را به معنای نبودِ تفسیر یا اجماعِ دیگر منابع ندان.",
            },
            {
                "field": "تمرین ترجمه و دلالت",
                "text": f"برای {verse_ref}، یک برگردانِ آزمایشی از «{basis_clean}» بنویس و آن را با ترجمهٔ پایهٔ فولادوند و شرحِ عربیِ التفسير الميسر مقابله کن؛ افزودهٔ توضیحی را از لفظ جدا نشان بده.",
                "basis": basis,
                "cite": f"{tanzil_cite}؛ {citation_moyassar(n)}",
                "guard": "این تمرین ترجمهٔ پایهٔ اپ را عوض نمی‌کند و برگردانِ آزمایشی را جایگزینِ متنِ قرآن یا تفسیرِ تخصصی نمی‌سازد.",
            },
            {
                "field": "آزمون میان‌رشته‌ای و مرزِ کاربرد",
                "text": f"در {verse_ref}، پیوندِ میان‌رشته‌ایِ «{basis_clean}» را فقط با منبعِ مرتبط و شاهدِ مستقیم بسنج؛ اگر آن پیوند پیدا نمی‌شود، عدمِ انطباق را ثبت کن و از قیاس یا ادعای علمی بپرهیز.",
                "basis": basis,
                "cite": "Fillmore, “Frame Semantics and the Nature of Language,” 1976, *Annals of the New York Academy of Sciences* 280, 20–32; Sinai, *The Qur’an: A Historical-Critical Introduction*, 2017",
                "guard": "روشِ زبانی دادهٔ تجربی یا قانونِ امروز نیست؛ بدونِ منبعِ بیرونیِ دقیق و تناسبِ مستقیم، آیه را به نظریه یا حکمِ امروزی هم‌ارز نکن.",
            },
        ]
        if n == 6:
            app_uses[4] = {
                "field": "آزمون میان‌رشته‌ای و مرزِ کاربرد",
                "text": f"در {verse_ref}، مضمونِ پناه‌دادن تا شنیدنِ پیام را فقط به‌عنوانِ پرسش با مادهٔ ۱۸ میثاقِ حقوقِ مدنی و سیاسی دربارهٔ آزادیِ دین و وجدان مقایسه کن؛ دو نظام را همسان ندان.",
                "basis": basis,
                "cite": "OHCHR, International Covenant on Civil and Political Rights, General Assembly resolution 2200A (XXI), 16 December 1966, art. 18; قرآن، توبه ۹:۶",
                "guard": "مادهٔ ۱۸ سندِ حقوقیِ معاصر است، نه تفسیرِ آیه؛ تفاوتِ زمان، مخاطب و صلاحیت را ثبت کن و از آن حکمِ فقهی یا تاریخِ نزول نتیجه نگیر.",
            }
        new_applications[verse_id] = {"uses": app_uses}

        evidence_text = f"قرآن، توبه ۹:{fa_num(n)}؛ متنِ عربی و ترجمهٔ پایهٔ فولادوند در Tanzil"
        mizan_evidence = f"{mizan_cite}؛ وضعیتِ این بررسی: {'برشِ مستقیمِ شرح بازیابی شد' if mizan_result else 'برشِ موضعی بازیابی نشد؛ نبودِ تفسیر ادعا نمی‌شود'}"
        framework = {
            "izutsu": {
                "input": f"واژه‌ها و پیوندهای صریحِ {verse_ref}: «{basis_clean}»",
                "operation": "هم‌نشینیِ صورتِ کانونی را در آیه و سیاقِ نزدیک ثبت کن و سپس آن را با شاهدِ تفسیری مقابله کن.",
                "meaning": "خروجی، نقشهٔ واژگانیِ همین موضع است؛ پیش از مقایسهٔ کاربردها معنای جامع یا ثابت اعلام نمی‌شود.",
                "limit": "تحلیل به صورتِ ثبت‌شده و سیاقِ نزدیک محدود است؛ حذفِ حرکات برای جست‌وجو، جایگزینِ قرائت و صرف نیست.",
                "cite": "Izutsu, *God and Man in the Koran*, 1964",
            },
            "fillmore": {
                "input": f"قابِ گفتار یا رویداد در {verse_ref}: «{basis_clean}»",
                "operation": "گوینده، کنش، مخاطب و پیامدِ صریح را جدا کن؛ هر نقشی که در لفظ نیست با برچسبِ نامعلوم نگه دار.",
                "meaning": "قابِ آموزشی پرسشی دربارهٔ ساختِ عبارت می‌سازد و به‌تنهایی تفسیر یا حکم تولید نمی‌کند.",
                "limit": "این چارچوب ابزارِ زبان‌شناختی است؛ نقشِ دستوری و کنشگرِ اجتماعی را بدونِ شاهد یکی نکن.",
                "cite": "Fillmore, “Frame Semantics and the Nature of Language,” *Annals of the New York Academy of Sciences* 280 (1976), 20–32",
            },
            "cognitive": {
                "input": f"تصویر، تقابل یا برجستگیِ صریح در {verse_ref}: «{basis_clean}»",
                "operation": "فقط تصویر یا تقابلِ موجود در لفظ را بیازما؛ اگر نشانهٔ روشن نیست، نبودِ شاهد را ثبت کن.",
                "meaning": "خوانشِ شناختی در اینجا فرضیه‌ای محلی است و از یک تصویر، ادعای روان‌شناختی یا تجربی ساخته نمی‌شود.",
                "limit": "روشِ شناختی جایِ دادهٔ تجربیِ مستقل را نمی‌گیرد و نباید به نیتِ اشخاصِ تاریخی تعمیم یابد.",
                "cite": "George Lakoff and Mark Johnson, *Metaphors We Live By*, 1980",
            },
            "historical": {
                "input": f"بافت و پیوندِ متن در {verse_ref}؛ بازهٔ منبع «{reference_range}»",
                "operation": "ترتیبِ مصحف، تیترِ قطعه و گزارشِ تاریخی را جدا بنویس؛ هر فرضیه را به خبرِ مشخص و چند منبعِ مستقل ببند.",
                "meaning": "این چارچوب پرسشِ تاریخی می‌سازد؛ از هم‌جواری یا عنوانِ قطعه تاریخِ قطعی و سببِ نزول به‌دست نمی‌آید.",
                "limit": "بدونِ شاهدِ مستقل، تاریخ‌گذاری و شأنِ نزول نامعلوم می‌ماند؛ روشِ تاریخی جایِ گزارشِ منبع‌دار نیست.",
                "cite": "Sinai, *The Qur’an: A Historical-Critical Introduction*, Edinburgh University Press, 2017",
            },
            "interdisciplinary": {
                "input": f"آیا برای {verse_ref} پیوندِ میان‌رشته‌ایِ مستقیم و منبع‌دار برای «{basis_clean}» وجود دارد؟",
                "operation": "نوعِ منبعِ بیرونی، نسبتِ دقیقِ آن با لفظ و حدِّ قیاس را پیشاپیش ثبت کن؛ در نبودِ شاهد، عدمِ انطباق بنویس.",
                "meaning": "پرهیز از قیاسِ بی‌شاهد بخشی از روش است؛ چارچوبِ زبان‌شناختی، دادهٔ تجربی یا حکمِ حقوقی ایجاد نمی‌کند.",
                "limit": "مقایسه فقط در حدِّ منبعِ مستقل و تناسبِ روشن معتبر است؛ همسانیِ تاریخی، حقوقی یا دینی مفروض نیست.",
                "cite": f"{evidence_text}; Fillmore, “Frame Semantics and the Nature of Language,” 1976",
            },
        }
        message_items = [
            {"text": f"پیشنهادِ من برای مطالعهٔ {verse_ref}: عبارتِ «{basis_clean}» را کنارِ ترجمهٔ فولادوند بخوان و دادهٔ لفظی را از تفسیر جدا ثبت کن؛ این پیشنهادِ تحریری فقط به همین شاهد محدود است.", "evidence": evidence_text},
            {"text": f"پیامِ محدودِ خوانشِ {verse_ref}: ابتدا همان عبارتِ «{basis_clean}» و پیوندش با آیاتِ مجاور را بررسی کن؛ از یک موضع، حکمِ همگانی یا قصدِ اشخاصِ امروز نتیجه نگیر.", "evidence": f"{evidence_text}؛ {window}"},
            {"text": f"پیشنهادِ مقایسه در {verse_ref}: هر قول را با نامِ مفسر نگه دار و تفاوتِ گزارشِ طبری و قرطبی را به ترجمه یا اجماع نسبت نده.", "evidence": f"{citation_tabari(n)}؛ {citation_qurtubi(n)}"},
            {"text": f"یادآوریِ منبعی برای {verse_ref}: قطعهٔ المیزان به بازهٔ «{reference_range}» نگاشت شده؛ نقلِ موضعی فقط در صورتِ بازیابیِ مستقیم پذیرفته می‌شود.", "evidence": mizan_evidence},
            {"text": f"پیشنهادِ پژوهشی دربارهٔ {verse_ref}: اگر پیوندِ بیرونیِ مستند برای «{basis_clean}» پیدا نشد، عدمِ انطباق را صریح بنویس؛ شباهتِ لفظی به‌تنهایی شاهد نیست.", "evidence": f"{evidence_text}؛ Fillmore, “Frame Semantics and the Nature of Language,” 1976"},
        ]
        principle_items = [
            {"text": f"اصلِ خوانشِ {verse_ref}: متنِ عربی، ترجمه و شرح سه لایه‌اند؛ در یادداشتِ پژوهشی، شاهدِ هر لایه را جدا بنویس.", "evidence": evidence_text},
            {"text": f"اصلِ انتساب در {verse_ref}: گزارشِ طبری و قرطبی فقط به خودِ همان مفسر نسبت داده شود، نه به همهٔ مسلمانان یا اجماع.", "evidence": f"{citation_tabari(n)}؛ {citation_qurtubi(n)}"},
            {"text": f"اصلِ سیاق برای {verse_ref}: آیه را در پنجرهٔ {window} بخوان؛ ترتیبِ متن به‌تنهایی دلیلِ علیت یا تاریخ نیست.", "evidence": f"قرآن، {window}؛ متنِ عربیِ مصحف"},
            {"text": f"اصلِ احتیاط در {verse_ref}: اگر برشِ مستقیمِ یک منبع موجود نیست، محدودیتِ بازیابی را ثبت کن و متنِ منبع را بازسازی نکن.", "evidence": mizan_evidence},
            {"text": f"اصلِ مرزبندی برای {verse_ref}: هیچ قیاسِ علمی، حقوقی یا اخلاقی را بدونِ منبعِ مستقل و تناسبِ روشن به آیه نسبت نده.", "evidence": f"{evidence_text}؛ Fillmore, “Frame Semantics and the Nature of Language,” 1976"},
        ]
        thematic_items = [
            {"reference": f"توبه ۹:{fa_num(n)}", "relation": f"لنگرِ لفظیِ این مطالعه عبارتِ «{basis_clean}» است؛ رابطهٔ موضوعی در این مدخل فقط تا حدِّ عبارت و سیاقِ همین آیه پیش می‌رود.", "evidence": evidence_text},
            {"reference": f"توبه ۹:{fa_num(previous_n)}–{fa_num(next_n)}", "relation": f"آیاتِ مجاورِ {verse_ref} برای آزمونِ پیوستگیِ لفظی خوانده می‌شوند؛ مجاورت، به‌تنهایی سببِ نزول یا رابطهٔ علّی نیست.", "evidence": f"قرآن، {window}؛ ترجمهٔ پایهٔ فولادوند، شناسهٔ fa.fooladvand در Tanzil"},
            {"reference": f"توبه ۹:{fa_num(n)}–{reference_range.split('–')[-1]}", "relation": f"قطعهٔ المیزان این آیه را در بازهٔ «{reference_range}» دسته‌بندی می‌کند؛ این برچسبْ دامنهٔ منبع است، نه طبقه‌بندیِ نهاییِ برنامه.", "evidence": mizan_cite},
            {"reference": repeated_ref, "relation": repeated_relation, "evidence": f"قرآن، {repeated_ref}؛ متنِ عربیِ مصحف"},
            {"reference": f"توبه ۹:{fa_num(n)}؛ التفسير الميسر، همان موضع", "relation": f"شرحِ معاصرِ المیسر برای {verse_ref} جدا از ترجمهٔ پایه ثبت می‌شود؛ هم‌موضوعیِ دو متن جایگزینِ مقایسهٔ عبارت‌ها نیست.", "evidence": f"{citation_moyassar(n)}؛ {tanzil_cite}"},
        ]
        context_items = [
            {"reference": f"توبه ۹:{fa_num(previous_n)}–{fa_num(next_n)}", "relation": f"قرینهٔ نزدیکِ {verse_ref} بازهٔ {window} است؛ پیوندِ آن باید با واژه و ساختِ حاضر در متن توضیح داده شود.", "evidence": f"قرآن، {window}؛ ترجمهٔ پایهٔ فولادوند، شناسهٔ fa.fooladvand در Tanzil"},
            {"reference": reference_range, "relation": f"عنوانِ منبع برای بازهٔ {reference_range}: «{section.get('title', 'بازهٔ ثبت‌شده در قطعه')}»؛ این عنوانِ المیزان است و نباید بی‌قید به تک‌آیه تعمیم یابد.", "evidence": mizan_cite},
            {"reference": f"توبه ۹:{fa_num(n)}", "relation": f"رکوردِ طبری در موضعِ {verse_ref} باید همراهِ عبارتِ کامل و نشانگرهای نقل خوانده شود؛ حذفِ سیاقِ روایت ممکن است نتیجه را عوض کند.", "evidence": citation_tabari(n)},
            {"reference": f"توبه ۹:{fa_num(n)}", "relation": f"رکوردِ قرطبی در موضعِ {verse_ref} خوانشی مستقل است؛ کوتاهی یا بلندیِ متنِ بازیابی‌شده را به‌عنوانِ ویژگیِ همان نسخه ثبت کن.", "evidence": citation_qurtubi(n)},
            {"reference": f"توبه ۹:{fa_num(n)}", "relation": f"التفسير الميسر برای این موضع یک شرحِ عربیِ نسخه‌دار دارد؛ آن را ترجمهٔ فارسی یا تفسیرِ همهٔ منابع معرفی نکن.", "evidence": citation_moyassar(n)},
        ]
        network_items = [
            {"reference": f"توبه ۹:{fa_num(n)} ↔ {fa_num(next_n)}", "relation": f"برای پیوندِ شبکه‌ای، صورتِ «{basis_clean}» را با آیهٔ مجاور بسنج؛ اگر صورت تکرار نمی‌شود، پیوند را صرفاً سیاقی و نه واژگانی برچسب بزن.", "evidence": f"قرآن، توبه ۹:{fa_num(n)}–{fa_num(next_n)}"},
            {"reference": repeated_ref, "relation": repeated_relation, "evidence": f"قرآن، {repeated_ref}؛ متنِ عربیِ مصحف"},
            {"reference": reference_range, "relation": f"شناسهٔ قطعهٔ {mizan_record_id} مسیرِ دسترسی به یک بخشِ تفسیریِ گسترده‌تر را نشان می‌دهد؛ هم‌نگاشتیِ بخش به‌تنهایی رابطهٔ معنایی اثبات نمی‌کند.", "evidence": mizan_cite},
            {"reference": f"توبه ۹:{fa_num(n)}؛ تفسیر طبری", "relation": f"در شبکهٔ منبع، نقلِ طبری به آیهٔ {verse_ref} متصل است؛ گزارشِ او را از شاهدِ قرآنی جدا نگه دار.", "evidence": citation_tabari(n)},
            {"reference": f"توبه ۹:{fa_num(n)}؛ تفسیر قرطبی", "relation": f"در شبکهٔ منبع، نقلِ قرطبی به همان موضع پیوند می‌خورد؛ هم‌ارجاعی با طبری توافقِ محتوایی را ثابت نمی‌کند.", "evidence": citation_qurtubi(n)},
        ]
        annotation_research = [
            {"title": f"ساختِ عبارت در {verse_ref}", "question": f"نقشِ واژه‌ها و پیوندهای دستوریِ «{basis_clean}» چیست و کدام بخش از پاسخ در گزارشِ طبری یا قرطبی می‌آید؟", "evidence": f"{evidence_text}؛ {citation_tabari(n)}؛ {citation_qurtubi(n)}"},
            {"title": f"ترجمه و دلالت در {verse_ref}", "question": f"فولادوند عبارتِ «{basis_clean}» را چگونه برمی‌گرداند و کدام جزء را التفسير الميسر در شرحِ عربی برجسته می‌کند؟", "evidence": f"{tanzil_cite}؛ {citation_moyassar(n)}"},
            {"title": f"دامنهٔ قطعهٔ المیزان برای {verse_ref}", "question": f"نگاشتِ «{reference_range}» چه شاهدی برای خواندنِ این آیه فراهم می‌کند و کدام بخش فقط به کلِّ بازه مربوط است؟", "evidence": mizan_evidence},
            {"title": f"پیوندِ واژگانی در {verse_ref}", "question": f"آیا صورتِ «{basis_clean}» در آیاتِ نزدیک تکرار می‌شود و چگونه می‌توان تکرارِ لفظ را از وحدتِ معنا جدا کرد؟", "evidence": f"قرآن، {window}؛ Izutsu, *God and Man in the Koran*, 1964"},
            {"title": f"آزمونِ پیوندِ میان‌رشته‌ای برای {verse_ref}", "question": f"چه منبعِ بیرونیِ مستقلی تناسبِ مستقیم با «{basis_clean}» دارد؛ اگر منبعِ معتبر نیافتیم، چرا ثبتِ عدمِ انطباق دقیق‌تر از قیاس است؟", "evidence": f"{evidence_text}؛ Fillmore, “Frame Semantics and the Nature of Language,” 1976"},
        ]
        if n == 6:
            annotation_research[4] = {
                "title": "مقایسهٔ محدودِ امان در توبه ۹:۶",
                "question": "چگونه می‌توان مضمونِ پناه‌دادن تا شنیدنِ پیام را فقط به‌عنوانِ پرسش با آزادیِ دین و وجدان در مادهٔ ۱۸ میثاقِ حقوقِ مدنی و سیاسی سنجید، بی‌آنکه دو نظام را یکی دانست؟",
                "evidence": "قرآن، توبه ۹:۶؛ OHCHR, International Covenant on Civil and Political Rights, General Assembly resolution 2200A (XXI), 16 December 1966, art. 18",
            }

        new_annotations[verse_id] = {
            "status": "پیش‌نویس تحریری؛ نیازمند بازبینی تخصصی",
            "notes": [
                {"text": f"شاهدِ ترجمهٔ {verse_ref}: {trans_quote} این نقل از ترجمهٔ پایه است، نه شرحِ تفسیری.", "evidence": tanzil_cite},
                {"text": f"یادداشتِ لفظیِ {verse_ref}: صورتِ «{basis_clean}» را با متنِ کامل و حرکاتِ مصحف مقابله کن؛ نرمال‌سازی فقط برای جست‌وجو است.", "evidence": evidence_text},
                {"text": f"یادداشتِ منبعیِ {verse_ref}: قطعهٔ المیزان با بازهٔ «{reference_range}» نگاشت شده؛ برشِ اختصاصی را فقط در صورتِ بازیابیِ مستقیم نقل کن.", "evidence": mizan_evidence},
                {"text": f"یادداشتِ سیاقیِ {verse_ref}: آیاتِ {window} پنجرهٔ نزدیک را می‌سازند؛ از هم‌جواری به‌تنهایی تاریخ یا علت نساز.", "evidence": f"قرآن، {window}؛ ترجمهٔ پایهٔ فولادوند، شناسهٔ fa.fooladvand در Tanzil"},
                {"text": f"یادداشتِ اختلافِ منبع در {verse_ref}: گزارشِ طبری و قرطبی باید جدا ثبت شود؛ نبودِ توافقِ صریح را با اجماع جایگزین نکن.", "evidence": f"{citation_tabari(n)}؛ {citation_qurtubi(n)}"},
            ],
            "messages": message_items,
            "principles": principle_items,
            "framework": framework,
            "thematic": thematic_items,
            "context": context_items,
            "network": network_items,
            "sources": ["ar_qe_arabic_moyassar", "ar_tabari_qurancom", "ar_qurtubi_qurancom", "fa_mizan_furqan"],
            "research": annotation_research,
        }

    # Validate anchors against the canonical Arabic text and ensure all values are source-backed.
    for verse_id, entry in new_dossiers.items():
        assert all(len(entry[field]) == 5 for field in ("notes", "context", "classical", "modern", "critical", "research")), verse_id
        assert len(entry["classical"]) == 5 and len(entry["modern"]) == 5
        assert [x.get("sourceId") for x in entry["classical"]].count("ar_tabari_qurancom") == 3
        assert [x.get("sourceId") for x in entry["classical"]].count("ar_qurtubi_qurancom") == 2
        for field in ("notes", "context", "classical", "modern", "critical", "research"):
            assert len({item["text"] for item in entry[field]}) == 5, (verse_id, field)
            assert all(len(item["text"].split()) >= 14 and item["cite"].strip() for item in entry[field]), (verse_id, field)
    for verse_id, entry in new_applications.items():
        assert len(entry["uses"]) == 5
        assert all(use["basis"] in corpus9[int(verse_id.split(":")[1])][2] for use in entry["uses"]), verse_id
    for verse_id, entry in new_annotations.items():
        for field in ("notes", "messages", "principles", "thematic", "context", "network", "research"):
            assert len(entry[field]) == 5, (verse_id, field)
        assert set(entry["framework"]) == {"izutsu", "fillmore", "cognitive", "historical", "interdisciplinary"}

    dossier = load_json(STATIC / "verse-dossiers.json")
    app = load_json(STATIC / "scholar-application.json")
    annotations = load_json(STATIC / "verse-study-annotations.json")
    assert not set(new_dossiers) & set(dossier["verses"])
    # Surah 9 was present only as an underfilled scaffold in the annotations layer.
    assert set(new_annotations) <= set(annotations["verses"])

    dossier["verses"].update(new_dossiers)
    dossier["batches"].append({
        "id": "dossier-34",
        "title": "بستهٔ سی‌وچهارم: توبه، پروندهٔ آیه‌به‌آیه",
        "range": "9:1–129",
        "count": 129,
        "status": f"پنج مورد در هر شش فیلد؛ ۱۲۹ برشِ مستقیمِ المیسر؛ {tabari_direct_count} نقلِ مستقیم و {tabari_gap_count} یادداشتِ محدودیتِ طبری؛ {qurtubi_direct_count} نقلِ مستقیم و {qurtubi_gap_count} یادداشتِ محدودیتِ قرطبی؛ {direct_mizan_count} برشِ مستقیمِ شرحِ المیزان و {len(mizan_missing)} موضعِ بدونِ برشِ مستقیم؛ پیش‌نویسِ نیازمندِ بازبینی",
    })
    previous_dossier_revision = dossier["revision"]
    dossier["revision"] = {
        "range": "9:1–9:129",
        "count": 129,
        "fields": ["notes", "context", "classical", "modern", "critical", "research"],
        "method": f"برای توبه ۹:۱–۱۲۹ در هر یک از شش فیلد پنج مدخل ثبت شد. رکوردهای طبری و قرطبی از نسخهٔ Quran.com API 1.1 و نقلِ المیسر از QuranEnc 1.0.0 است؛ برشِ مستقیمِ فارسیِ المیزان فقط در {direct_mizan_count} موضعی درج شد که عبارتِ پیوسته‌ای از آیه در بندِ شرحِ فارسیِ قطعهٔ نگاشت‌شده بازیابی شد؛ نقلِ صرفِ متنِ آیه یا تیتر به‌عنوانِ تفسیر شمرده نشد و در {len(mizan_missing)} موضع نقلِ مستقیم درج نشد. ارجاعِ قطعه‌ای، تفسیرِ همان منبع را گزارش می‌کند و خودْ اجماع یا تأییدِ تحریری نیست.",
        "caveat": "پنج‌گانه‌بودن و داشتنِ ارجاع، مقابلهٔ کاملِ همهٔ ادعاها یا تأییدِ تخصصی نیست. نقل‌های مستقیم برای راستی‌آزماییِ متن و نسخه عرضه شده‌اند؛ یادداشت‌ها، ملاحظاتِ انتقادی، تطبیق‌ها و پرسش‌ها پیش‌نویس‌اند و اختلافِ تفسیری را حل‌شده نمی‌نمایانند.",
        "previousRevision": previous_dossier_revision,
    }
    dossier["notice"] = f"پروندهٔ تفصیلیِ فاتحه، بقره، آل‌عمران، نساء، مائده، انعام، اعراف، انفال و اکنون توبه ثبت شده است؛ در نساء، مائده، انعام، اعراف، انفال و توبه ۸۷۱ آیه در مجموع پوششِ پنج‌گانه دارند. این ساختار به‌معنای بازبینیِ علمی یا تأییدِ نهایی نیست؛ نقلِ بی‌موضعِ مستقیم حذف می‌شود و یادداشت‌ها و پرسش‌ها پیش‌نویسِ نیازمندِ بازبینیِ متخصص‌اند."
    dossier["editorialMethod"] += f" در توبه ۹:۱–۱۲۹ نیز هر شش فیلد پنج مورد دارند؛ برشِ المیزان تنها در {direct_mizan_count} موضع پس از بازیابیِ یک عبارتِ پیوسته از آیه در بخشِ شرح درج شد و {len(mizan_missing)} موضع بدونِ نقلِ مستقیم ماند. گزیدهٔ نبودن، نبودِ تفسیر را اثبات نمی‌کند؛ قیاسِ میان‌رشته‌ای فقط پرسش است و بدونِ منبعِ مستقل و تناسبِ روشن نتیجه نمی‌سازد."
    save_json(STATIC / "verse-dossiers.json", dossier)

    app["batches"].append({
        "id": "batch-15",
        "title": "بستهٔ پانزدهم: توبه ۱–۱۲۹",
        "range": "۹:۱–۱۲۹",
        "segments": [["9:1", "9:129"]],
        "count": 129,
        "status": "پنج کاربستِ منبع‌محور برای هر آیه؛ شاهدِ لفظی، ارجاع و مرزِ سوءاستفاده؛ پیش‌نویسِ نیازمندِ بازبینی",
    })
    app["verses"].update(new_applications)
    previous_app_revision = app["revision"]
    previous_ranges = list(previous_app_revision["ranges"])
    previous_ranges.append("۹:۱–۱۲۹")
    app["revision"] = {
        "standard": "v3",
        "ranges": previous_ranges,
        "range": previous_app_revision["range"] + " و ۹:۱–۱۲۹",
        "count": previous_app_revision["count"] + 129,
        "rule": previous_app_revision["rule"],
        "note": "بسته‌های ۱ تا ۳: ۴۹۳ آیه و چهار کاربستِ تاریخی؛ از نساء تا توبه ۸۷۱ آیه با پنج کاربست برای هر آیه. شمارش و ساختار، تأییدِ تخصصیِ محتوا نیست.",
        "previousRevision": previous_app_revision,
    }
    app["notice"] = "در فاتحه ۱:۱–۷، بقره ۲:۱–۲۸۶ و آل‌عمران ۳:۱–۲۰۰، چهار کاربستِ تاریخی حفظ شده است؛ از نساء ۴:۱ تا توبه ۹:۱۲۹ پنج کاربست برای هر آیه ثبت شده است. هر کاربست شاهدِ لفظی، ارجاعِ منبع‌دار و مرزِ استنباط دارد؛ این تمرین فهمِ قرآن است، نه فتوا یا مجوزِ تعمیم."
    save_json(STATIC / "scholar-application.json", app)

    annotations["verses"].update(new_annotations)
    annotations["editorialMethod"] += " از توبه ۹:۱–۱۲۹ نیز هفت فیلدِ فهرستی پنج مدخل و چارچوب پنج‌مدلی دارد؛ نقلِ منابعِ کهن و معاصر از استنباطِ تحریری جداست، و نبودِ برشِ مستقیمِ المیزان به‌معنای نبودِ تفسیر نیست. پیشنهادِ تحریریِ هر مدخل به شاهدِ همان آیه محدود است؛ پیشنهادهای عمومی همچنان نیازمندِ شاهد، بررسی و تأییدند."
    save_json(STATIC / "verse-study-annotations.json", annotations)

    print(json.dumps({"dossier_count": len(new_dossiers), "application_count": len(new_applications), "annotation_count": len(new_annotations), "direct_mizan": direct_mizan_count, "mizan_missing": mizan_missing}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ساختِ پرونده‌های تحریریِ توبه از منابعِ محلیِ نسخه‌دار")
    parser.add_argument("--sources-dir", type=Path, default=SRC, help="پوشهٔ چهار snapshotِ تفسیری")
    main(parser.parse_args().sources_dir)
