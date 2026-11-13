#!/usr/bin/env python3
"""بازنویسیِ فیلدهای تکمیلیِ کم‌محتوا از مطالبِ مستندِ خودِ همان آیه.

برای هر آیه، جمله‌های مدخل‌های پایه (نکات، سیاق، کهن، معاصر، انتقادی، پژوهش) که
دقیقاً دربارهٔ موضوعِ یک فیلد تکمیلی‌اند، با همان ارجاعِ اصلی به آن فیلد منتقل
می‌شوند؛ به شرط آنکه جمله در سراسر پیکره پرتکرار نباشد و به متن/ترجمهٔ همان آیه
لنگر داشته باشد یا ارجاعش ذیلِ همان آیه باشد. فیلدی که مادهٔ هم‌موضوع ندارد خالی
می‌ماند و در رابط «نیازمند پژوهش» دیده می‌شود. فقط فیلدهای زیر ۳ مدخل، تا سقف ۳،
تکمیل می‌شوند.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "static"
FILES = ["verse-dossier-extended-fields.json", "verse-dossier-extended-fields-2.json"]
BASE_FIELDS = ("notes", "context", "classical", "modern", "critical", "research")
BASE_LABELS = {
    "notes": "نکات مهم آیه", "context": "سیاق و جایگاه", "classical": "تفسیر کهن",
    "modern": "تفسیر معاصر", "critical": "خوانش انتقادی", "research": "پژوهش در آیه",
}
TOPICS = {
    "qiraat": r"قرائت|قراءة|قرأ |یقرأ|تقرأ|قراء|اختلافِ قراء|قرأه|قرأها|بالخفض|بالرفع|بالنصب|قرائات",
    "linguistics": r"لغت|اشتقاق|واژه|کلمه|لفظ|ریشهٔ|إعراب|در لغت|معنایِ واژه|معنایِ کلمه|صرفِ|نحوِ",
    "balaghaNazm": r"بلاغ|نظمِ|فصاحت|ایجاز|اطناب|استعاره|کنایه|تشبیه|تقدیم|تأخیر|التفات|سجع|فاصلهٔ آیات",
    "historicalContext": r"سببِ نزول|شأنِ نزول|مکیّه|مدنیّه|مکی است|مدنی است|نازل شد|زمینهٔ تاریخی|غزوه|حدیبیه|قبیلهٔ",
    "philosophicalFoundations": r"فلسف|اختیار|جبر|عدالت|غایت|حکمتِ الهی|ارادهٔ آزاد|مسئلهٔ شر|حسن و قبح",
    "shubuhat": r"شبهه|اشکال|اعتراض|تناقض|ادعایِ مخالفان|منکران|پاسخ به شبهه|اشکالِ",
    "guidanceDiscourse": r"هدایت|عبرت|الگو|تربیت|پیامِ آیه|درسِ",
    "criticalDiscourseAnalysis": r"گفتمان|قدرت|سلطه|بازنمایی|ایدئولوژ|خطاب به",
    "modernSciences": r"روان‌شناس|جامعه‌شناس|پژوهشِ تجربی|آزمایش|محیطِ زیست|پزشکی|نجوم|علمِ",
}
GAP = re.compile(r"مدخل پوشش|پرونده مدخل|برنگشت|ثبت نشده است|یافت نشد|نیامده است|بررسی نشد|source-coverage")
SENT_SPLIT = re.compile(r"(?<=[.!؟])\s+")
DIAC = re.compile(r"[ً-ٰٟ]")
FA_STOP = set("است از به که در و با این آن را بر برای می شود شده اند ای هر چه یا نه نیز هم تا او ما شما آنان خود بود خواهد کرد کند".split())
PREFIXES = ("وال", "فال", "بال", "كال", "ال", "و", "ف", "ب", "ل")
MAX_SENTENCE_VERSES = 7


def norm(text: str) -> str:
    return re.sub(r"\s+", "", str(text or ""))


def norm_ar(text: str) -> str:
    t = DIAC.sub("", str(text or ""))
    return t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")


def ar_tokens(text: str) -> set:
    toks = set()
    for w in re.findall(r"[ء-ي]{4,}", norm_ar(text)):
        toks.add(w)
        for pre in PREFIXES:
            if w.startswith(pre) and len(w) - len(pre) >= 4:
                toks.add(w[len(pre):])
    return toks


def fa_words(text: str) -> set:
    return {w for w in re.findall(r"[آ-ی]{3,}", str(text or "")) if w not in FA_STOP}


def fa_num(n: int) -> str:
    return str(n).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def sentences(text: str):
    return [p.strip() for p in SENT_SPLIT.split(str(text or "")) if p.strip()]


def main() -> int:
    corpus = json.loads((STATIC / "offline-corpus.json").read_text(encoding="utf-8"))
    arab = {f"{t[0]}:{t[1]}": t[2] for t in corpus["verses"]}
    pers = {f"{t[0]}:{t[1]}": t[3] for t in corpus["verses"]}

    payloads = {}
    verses = {}
    for name in FILES:
        data = json.loads((STATIC / name).read_text(encoding="utf-8"))
        payloads[name] = data
        for vid, rec in (data.get("verses") or {}).items():
            verses[vid] = rec

    # جمله‌هایی که در پروندهٔ آیه‌های بسیار تکرار شده‌اند قالبی‌اند و استخراج نمی‌شوند؛
    # شمارش با اسکلتِ نرمال‌شده (عدد/نقل/نام سوره حذف‌شده) انجام می‌شود.
    chapters = json.loads((STATIC.parent / "data" / "chapters.json").read_text(encoding="utf-8"))
    surah_names = set()
    for row in (chapters if isinstance(chapters, list) else chapters.get("chapters", [])):
        for key in ("name_arabic", "name", "arabic_name", "title"):
            if row.get(key):
                surah_names.add(str(row[key]))

    def skeleton(text: str) -> str:
        t = re.sub(r"[0-9۰-۹]+", "N", str(text or ""))
        t = re.sub(r"«[^»]{0,80}»", "«X»", t)
        for nm in surah_names:
            t = t.replace(nm, "S")
        return re.sub(r"\s+", "", t)

    sentence_verses = Counter()
    for rec in verses.values():
        seen_here = set()
        for bf in BASE_FIELDS:
            for item in rec.get(bf) or []:
                for sent in sentences(item.get("text", "")):
                    seen_here.add(skeleton(sent))
        for key in seen_here:
            sentence_verses[key] += 1
    boilerplate = {k for k, c in sentence_verses.items() if c > MAX_SENTENCE_VERSES}

    added_total = 0
    touched = 0
    for vid, rec in verses.items():
        base_entries = []
        for bf in BASE_FIELDS:
            for item in rec.get(bf) or []:
                base_entries.append((bf, item))
        if not base_entries:
            continue
        at, pw = ar_tokens(arab.get(vid, "")), fa_words(pers.get(vid, ""))
        surah, ayah = (int(x) for x in vid.split(":"))

        def anchored(chunk: str, cite: str) -> bool:
            if (ar_tokens(chunk) & at) or (fa_words(chunk) & pw):
                return True
            c = str(cite or "")
            return "http" in c or ".json" in c or f"{fa_num(surah)}:{fa_num(ayah)}" in c or f"{surah}:{ayah}" in c

        extended = rec.setdefault("extendedFields", {})
        existing_norms = set()
        for fd in extended.values():
            for e in fd.get("entries") or []:
                existing_norms.add(norm(e.get("text", "")))
        verse_added = 0
        for field, pattern in TOPICS.items():
            rx = re.compile(pattern)
            current = (extended.get(field) or {}).get("entries") or []
            if len(current) >= 3:
                continue
            mined = []
            used_cites = set()
            for bf, item in base_entries:
                if len(current) + len(mined) >= 3:
                    break
                cite = str(item.get("cite", "")).strip()
                if not cite or cite in used_cites:
                    continue
                sents = sentences(item.get("text", ""))
                for i, sent in enumerate(sents):
                    if skeleton(sent) in boilerplate or GAP.search(sent) or not rx.search(sent):
                        continue
                    chunk = sent
                    j = i + 1
                    while len(chunk.split()) < 14 and j < len(sents):
                        chunk = f"{chunk} {sents[j]}"
                        j += 1
                    if len(chunk.split()) < 14 or not anchored(chunk, cite):
                        continue
                    if norm(chunk) in existing_norms or norm(chunk) == norm(item.get("text", "")):
                        continue
                    existing_norms.add(norm(chunk))
                    used_cites.add(cite)
                    mined.append({
                        "kind": "source-attributed-summary",
                        "text": chunk,
                        "cite": cite,
                        "evidence": f"{vid}؛ برگرفته از فیلدِ «{BASE_LABELS[bf]}»ِ همین پرونده",
                        "limit": "این بند گزیده‌ای از مدخلِ پایهٔ همین آیه است و جای متنِ کاملِ منبعِ ارجاع‌شده را نمی‌گیرد؛ داوری نهایی با مقابلهٔ متنِ منبع است.",
                    })
                    break
            if mined:
                fdata = extended.setdefault(field, {
                    "status": "partial",
                    "coverage": {"completed": 0, "required": 5},
                    "sourceCoverageNote": "بندهای این فیلد از مدخل‌های مستندِ پایهٔ همین آیه و با همان ارجاع‌ها گرد آمده‌اند.",
                    "followUp": "برای تکمیلِ این فیلد، منابعِ تخصصیِ همین موضوع ذیلِ همین آیه مقابله و افزوده شود.",
                    "entries": [],
                })
                fdata["entries"] = (fdata.get("entries") or []) + mined
                fdata["status"] = "complete" if len(fdata["entries"]) >= 5 else "partial"
                if isinstance(fdata.get("coverage"), dict):
                    fdata["coverage"]["completed"] = len(fdata["entries"])
                added_total += len(mined)
                verse_added += len(mined)
        if verse_added:
            touched += 1
        if not extended:
            rec.pop("extendedFields", None)

    for name in FILES:
        path = STATIC / name
        path.write_text(json.dumps(payloads[name], ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(name, "MB:", round(path.stat().st_size / 1e6, 2))
    print(f"mined entries added={added_total} verses touched={touched} boilerplate sentences={len(boilerplate)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
