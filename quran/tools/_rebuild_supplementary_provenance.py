#!/usr/bin/env python3
"""بازسازیِ فیلدهای تکمیلی فقط بر پایهٔ منابعِ ذیلِ همان آیه.

قاعدهٔ ماندنِ هر مدخل:
۱) ارجاعش صریحاً ذیلِ همان آیه باشد (پیوندِ منبع با شمارهٔ سوره/آیه، ارجاعِ
   فارسیِ همان آیه، یا برای مقایسهٔ عهدینی فایل/پیوندِ کتاب مقدس)، و
۲) متنش به متنِ عربی یا ترجمهٔ همان آیه لنگر داشته باشد، و
۳) برای مقایسه با کتاب مقدس، ساختارِ شباهت/تفاوت یا نامِ کتابِ عهدینی داشته باشد.
مدخل‌های با ارجاعِ صرفاً عام (کتابِ نظریِ بدون موضعِ آیه) حذف می‌شوند.
سپس هر فیلد از جمله‌های هم‌موضوعِ مدخل‌های پایهٔ همان آیه — که ارجاعِ ذیلِ همان
آیه دارند — تا سقف ۵ بند پر می‌شود؛ جملهٔ قالبیِ پرتکرار و بی‌لنگر راه ندارد.
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
    "qiraat": r"قرائت|قراءة|قرأ|قراء|قاریان|قاری|قارئ|اختلافِ قر|اختلف القر|خواندند|خوانده‌|روایتِ قرائت|بالخفض|بالرفع|بالنصب|بالجر|قرائات|قرئ|بی‌ألف|با تاء|با یاء",
    "linguistics": r"لغت|اشتقاق|واژه|کلمه|لفظ|ریشه|إعراب|نحو|صرف|معنای|مراد از|مقصود از",
    "balaghaNazm": r"بلاغ|نظمِ|فصاحت|ایجاز|اطناب|استعاره|کنایه|تشبیه|تقدیم|تأخیر|التفات|سجع|آهنگِ|ساختارِ آیه",
    "historicalContext": r"نزول|مکی|مدنی|سببِ|شأنِ|تاریخِ|واقعهٔ|حادثهٔ|دورهٔ|عصرِ|غزوه|حدیبیه|قبیله",
    "philosophicalFoundations": r"فلسف|اختیار|جبر|عدالت|غایت|حکمتِ الهی|ارادهٔ آزاد|حسن و قبح|مسئلهٔ شر|آزادی|ضرورت",
    "shubuhat": r"شبهه|اشکال|اعتراض|تناقض|ادعای|منکران|مخالفان",
    "guidanceDiscourse": r"هدایت|عبرت|الگو|تربیت|پیامِ آیه|درسِ|رهنمود",
    "criticalDiscourseAnalysis": r"گفتمان|قدرت|سلطه|بازنمایی|ایدئولوژ|خطاب|مخاطب",
    "modernSciences": r"روان‌شناس|جامعه‌شناس|تجربی|آزمایش|محیطِ زیست|پزشکی|نجوم|زیست‌شناس|علومِ",
}
GAP = re.compile(r"مدخل پوشش|پرونده مدخل|برنگشت|ثبت نشده است|یافت نشد|نیامده است|بررسی نشد|source-coverage")
SENT_SPLIT = re.compile(r"(?<=[.!؟])\s+")
DIAC = re.compile(r"[ً-ٰٟ]")
FA_STOP = set("است از به که در و با این آن را بر برای می شود شده اند ای هر چه یا نه نیز هم تا او ما شما آنان خود بود خواهد کرد کند".split())
PREFIXES = ("وال", "فال", "بال", "كال", "ال", "و", "ف", "ب", "ل")
MAX_SENTENCE_VERSES = 7
TARGET = 5


def norm(text: str) -> str:
    return re.sub(r"\s+", "", str(text or ""))


AR_STOP = {'في', 'إلى', 'على', 'من', 'ما', 'لا', 'إن', 'أن', 'هو', 'هي', 'لم', 'لن', 'قد', 'كان', 'ليس', 'بعد', 'قبل', 'عند', 'غير', 'كل', 'أي', 'ذو', 'ذات'}


def norm_ar(text: str) -> str:
    t = DIAC.sub("", str(text or "").replace("\u0670", "ا"))
    return t.replace("ی", "ي").replace("ک", "ك").replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")


def ar_tokens(text: str) -> set:
    toks = set()
    for w in re.findall(r"[ء-ي]{3,}", norm_ar(text)):
        if w in AR_STOP:
            continue
        toks.add(w)
        for pre in PREFIXES:
            if w.startswith(pre) and len(w) - len(pre) >= 3:
                toks.add(w[len(pre):])
    return toks


def fa_words(text: str) -> set:
    cleaned = DIAC.sub("", str(text or "")).replace("\u200c", "")
    return {w for w in re.findall(r"[آ-ی]{3,}", cleaned) if w not in FA_STOP}


def fa_num(n: int) -> str:
    return str(n).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def sentences(text: str):
    out = []
    for part in SENT_SPLIT.split(str(text or "")):
        part = part.strip()
        if not part:
            continue
        if len(part.split()) > 40 and "؛" in part:
            out.extend(p.strip() for p in part.split("؛") if p.strip())
        else:
            out.append(part)
    return out


DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def per_verse_cite(cite: str, vid: str, field: str = "") -> bool:
    c = str(cite or "").translate(DIGITS)
    surah, ayah = (int(x) for x in vid.split(":"))
    if re.search(rf"/{surah}/{ayah}(?!\d)", c):
        return True
    if f"{surah}:{ayah}" in c:
        return True
    if re.search(rf"\[?{surah}\.{ayah}\b", c):
        return True
    if re.search(rf"(?:Qur[\u02be'’]?an|Q)\.?\s*{surah}:{ayah}\b", c):
        return True
    if re.search(rf"\bAyat\s+{ayah}\b", c):
        return True
    for m in re.finditer(r"(?:آیات|ايات)\s*(\d+)[–—-]\s*(\d+)", c):
        if int(m.group(1)) <= ayah <= int(m.group(2)):
            return True
    if ("آیهٔ " + str(ayah)) in str(c):
        return True
    for m in re.finditer(rf"{surah}:(\d+)[–—-](\d+)", c):
        if int(m.group(1)) <= ayah <= int(m.group(2)):
            return True
    if field == "bibleComparison" and ("http" in c or ".json" in c or "Bible" in c):
        return True
    return False


def has_quote(text: str) -> bool:
    return bool(re.search(r"«[^»]{8,}»|﴿[^﴾]{4,}﴾", str(text or "")))


def main() -> int:
    corpus = json.loads((STATIC / "offline-corpus.json").read_text(encoding="utf-8"))
    arab = {f"{t[0]}:{t[1]}": t[2] for t in corpus["verses"]}
    pers = {f"{t[0]}:{t[1]}": t[3] for t in corpus["verses"]}
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

    payloads, verses = {}, {}
    for name in FILES:
        data = json.loads((STATIC / name).read_text(encoding="utf-8"))
        payloads[name] = data
        for vid, rec in (data.get("verses") or {}).items():
            verses[vid] = rec

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

    # رکوردهای دست‌نویسِ آغازین (انفال ۸:۵۱ تا هود ۱۱:۱۲۳) که با مقابلهٔ دستیِ
    # منابع ساخته شده‌اند از بازسازی کنار گذاشته می‌شوند؛ بازسازی برای بقیه است.
    def is_handwritten(vid: str) -> bool:
        surah, ayah = (int(x) for x in vid.split(":"))
        return (surah == 8 and ayah >= 51) or surah in (9, 10) or (surah == 11 and ayah <= 123)

    kept = dropped = mined_total = 0
    for vid, rec in verses.items():
        if is_handwritten(vid):
            continue
        at, pw = ar_tokens(arab.get(vid, "")), fa_words(pers.get(vid, ""))

        def anchored(text: str) -> bool:
            return bool(ar_tokens(text) & at) or bool(fa_words(text) & pw) or has_quote(text)

        extended = rec.get("extendedFields") or {}
        # فاز ۱: فقط مدخلِ دارای منشأِ ذیلِ همان آیه و لنگر به آیه می‌ماند
        for field in list(extended.keys()):
            fdata = extended[field] or {}
            entries = []
            for e in fdata.get("entries") or []:
                if e.get("kind") == "source-coverage-note" or GAP.search(str(e.get("text", ""))):
                    dropped += 1
                    continue
                ok = per_verse_cite(e.get("cite", ""), vid, field) and anchored(e.get("text", ""))
                if field == "bibleComparison":
                    t = str(e.get("text", ""))
                    ok = ok and ("شباهت" in t or "تفاوت" in t or "موازی" in t or "همانند" in t)
                if ok:
                    entries.append(e)
                    kept += 1
                else:
                    dropped += 1
            if entries:
                fdata["entries"] = entries
            else:
                del extended[field]
        # فاز ۲: پرکردن از مادهٔ مستندِ همان آیه
        existing_norms = set()
        for fd in extended.values():
            for e in fd.get("entries") or []:
                existing_norms.add(norm(e.get("text", "")))
        base_entries = []
        for bf in BASE_FIELDS:
            for item in rec.get(bf) or []:
                base_entries.append((bf, item))
        for field, pattern in TOPICS.items():
            rx = re.compile(pattern)
            fdata = extended.get(field)
            current = (fdata or {}).get("entries") or []
            if len(current) >= TARGET:
                continue
            mined = []
            used_cites = Counter()
            for bf, item in base_entries:
                if len(current) + len(mined) >= TARGET:
                    break
                cite = str(item.get("cite", "")).strip()
                if not cite or used_cites[cite] >= 2 or not per_verse_cite(cite, vid, field):
                    continue
                sents = sentences(item.get("text", ""))
                made = 0
                for i, sent in enumerate(sents):
                    if len(current) + len(mined) >= TARGET or made >= 2:
                        break
                    if skeleton(sent) in boilerplate or GAP.search(sent) or not rx.search(sent):
                        continue
                    chunk = sent
                    j = i + 1
                    while len(chunk.split()) < 14 and j < len(sents):
                        chunk = f"{chunk} {sents[j]}"
                        j += 1
                    if len(chunk.split()) < 14 or not anchored(chunk):
                        continue
                    if norm(chunk) in existing_norms or norm(chunk) == norm(item.get("text", "")):
                        continue
                    if len(norm(chunk)) > 0.8 * max(1, len(norm(item.get("text", "")))):
                        continue
                    existing_norms.add(norm(chunk))
                    used_cites[cite] += 1
                    made += 1
                    mined.append({
                        "kind": "source-attributed-summary",
                        "text": chunk,
                        "cite": cite,
                        "evidence": f"{vid}؛ برگرفته از فیلدِ «{BASE_LABELS[bf]}»ِ همین پرونده",
                        "limit": "این بند گزیده‌ای از مدخلِ پایهٔ همین آیه است و جای متنِ کاملِ منبعِ ارجاع‌شده را نمی‌گیرد؛ داوری نهایی با مقابلهٔ متنِ منبع است.",
                    })
            if mined:
                fdata = extended.setdefault(field, {
                    "status": "partial",
                    "coverage": {"completed": 0, "required": 5},
                    "sourceCoverageNote": "بندهای این فیلد از مدخل‌های مستندِ پایهٔ همین آیه و با همان ارجاع‌های ذیلِ همین آیه گرد آمده‌اند.",
                    "followUp": "برای تکمیلِ این فیلد، منابعِ تخصصیِ همین موضوع ذیلِ همین آیه مقابله و افزوده شود.",
                    "entries": [],
                })
                fdata["entries"] = (fdata.get("entries") or []) + mined
                mined_total += len(mined)
        # حذفِ تکرارِ میان‌فیلدی: متنِ برابر فقط در یک فیلد می‌ماند و اگر
        # نشانِ عهدینی دارد، فقط مقایسهٔ عهدینی آن را نگه می‌دارد
        seen_norms = {}
        for fid, fd in list(extended.items()):
            kept_here = []
            for e in fd.get("entries") or []:
                k = norm(e.get("text", ""))
                if k in seen_norms:
                    continue
                seen_norms[k] = fid
                kept_here.append(e)
            if kept_here:
                fd["entries"] = kept_here
            else:
                del extended[fid]
        # وضعیت و پوشش
        for fdata in extended.values():
            entries = fdata.get("entries") or []
            fdata["status"] = "complete" if len(entries) >= 5 else "partial"
            if isinstance(fdata.get("coverage"), dict):
                fdata["coverage"]["completed"] = len(entries)
        if extended:
            rec["extendedFields"] = extended
        else:
            rec.pop("extendedFields", None)

    for name in FILES:
        path = STATIC / name
        path.write_text(json.dumps(payloads[name], ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(name, "MB:", round(path.stat().st_size / 1e6, 2))
    print(f"kept={kept} dropped={dropped} mined={mined_total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
