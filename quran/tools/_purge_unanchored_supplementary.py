#!/usr/bin/env python3
"""پاکسازیِ محتوای فیلدهای تکمیلی (standard3) در هر دو شارد:

۱) یادداشت‌های «پوشش منبع» حذف می‌شوند؛ نبودِ فیلد در رابط صادقانه نشان داده می‌شود.
۲) مقدمه‌های قالبیِ تکرارشونده (مانند «ساختِ خطاب و جای گوینده و مخاطب...» و
   «نظمِ ... در چیدمانِ واژگان...») از آغازِ بندها برداشته می‌شوند تا هر بند با
   محتوای مخصوصِ همان آیه آغاز شود؛ بندی که پس از حذفِ مقدمه کوتاه شود حذف می‌شود.
۳) مدخل فقط می‌ماند اگر به همان آیه لنگر داشته باشد (واژهٔ عربیِ آیه یا واژهٔ
   محتواییِ ترجمه‌اش)، یا ارجاعِ بیرونیِ واقعی/ذیلِ همان آیه داشته باشد، یا
   اسکلتِ متنش یکتا و ارجاعش نامِ اثرِ علمیِ مشخص باشد.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

STATIC = Path(__file__).resolve().parent.parent / "static"
ROOT = STATIC.parent
FILES = ["verse-dossier-extended-fields.json", "verse-dossier-extended-fields-2.json"]
DIAC = re.compile(r"[ً-ٰٟ]")
FA_STOP = set("است از به که در و با این آن را بر برای می شود شده اند ای هر چه یا نه نیز هم تا او ما شما آنان خود بود خواهد کرد کند".split())
PREFIXES = ("وال", "فال", "بال", "كال", "ال", "و", "ف", "ب", "ل")
GAP_PHRASE = re.compile(r"مدخل پوشش|پرونده مدخل|برنگشت|ثبت نشده است|یافت نشد|نیامده است|بررسی نشد")
PREAMBLES = [
    re.compile(r"^در .{0,50}? ساختِ خطاب و جای گوینده و مخاطب، بارِ اصلیِ معنا را می‌کشد:\s*"),
    re.compile(r"^نظمِ .{0,50}? در چیدمانِ واژگان و پایان‌بندیِ آیه معنا را می‌سازد:\s*"),
]


def norm_ar(text: str) -> str:
    t = DIAC.sub("", str(text or ""))
    return (
        t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
        .replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    )


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


def _fa(number: int) -> str:
    return str(number).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def external_cite(cite: str, vid: str = "") -> bool:
    c = str(cite or "")
    if "http" in c or ".json" in c or "doi" in c.lower():
        return True
    if vid:
        surah, ayah = (int(x) for x in vid.split(":"))
        return f"{_fa(surah)}:{_fa(ayah)}" in c or f"{surah}:{ayah}" in c
    return False


def publication_cite(cite: str) -> bool:
    return bool(re.search(r"[A-Za-z]{3,}(?:\s+[A-Za-z]{3,})+", str(cite or "")))


def main() -> int:
    corpus = json.loads((STATIC / "offline-corpus.json").read_text(encoding="utf-8"))
    arab = {f"{t[0]}:{t[1]}": t[2] for t in corpus["verses"]}
    pers = {f"{t[0]}:{t[1]}": t[3] for t in corpus["verses"]}
    chapters = json.loads((ROOT / "data" / "chapters.json").read_text(encoding="utf-8"))
    surah_names = set()
    rows = chapters if isinstance(chapters, list) else chapters.get("chapters", [])
    for row in rows:
        for key in ("name_arabic", "name", "arabic_name", "title"):
            if row.get(key):
                surah_names.add(str(row[key]))

    def skeleton(text: str) -> str:
        t = re.sub(r"[0-9۰-۹]+", "N", str(text or ""))
        t = re.sub(r"«[^»]{0,80}»", "«X»", t)
        for name in surah_names:
            t = t.replace(name, "S")
        return t

    payloads = {}
    verses = {}
    for name in FILES:
        data = json.loads((STATIC / name).read_text(encoding="utf-8"))
        payloads[name] = data
        for vid, rec in (data.get("verses") or {}).items():
            verses[vid] = rec

    # گام ۱ و ۲: حذف یادداشت‌های پوشش و مقدمه‌های قالبی
    stripped = dropped_short = 0
    for rec in verses.values():
        for fdata in (rec.get("extendedFields") or {}).values():
            kept = []
            for e in fdata.get("entries") or []:
                text = str(e.get("text", ""))
                if e.get("kind") == "source-coverage-note" or text.startswith("[source-coverage-note]") or GAP_PHRASE.search(text):
                    continue
                for pat in PREAMBLES:
                    new_text = pat.sub("", text, count=1)
                    if new_text != text:
                        text = new_text
                        stripped += 1
                    break
                if len(text.split()) < 14:
                    dropped_short += 1
                    continue
                e["text"] = text
                kept.append(e)
            fdata["entries"] = kept

    # اسکلت‌های پس از پاکسازی برای سنجش یکتایی
    counts = {}
    for rec in verses.values():
        for field, fdata in (rec.get("extendedFields") or {}).items():
            counter = counts.setdefault(field, Counter())
            for e in fdata.get("entries") or []:
                counter[skeleton(e.get("text", ""))] += 1

    # گام ۳: نگه‌داشتن فقط مدخلِ لنگردار/مستند/یکتا
    removed = kept_total = 0
    for vid, rec in verses.items():
        at, pw = ar_tokens(arab.get(vid, "")), fa_words(pers.get(vid, ""))
        extended = rec.get("extendedFields") or {}
        for field in list(extended.keys()):
            fdata = extended[field] or {}
            entries = []
            for e in fdata.get("entries") or []:
                txt = e.get("text", "")
                anchored = bool(ar_tokens(txt) & at) or bool(fa_words(txt) & pw)
                unique_scholarly = counts[field][skeleton(txt)] < 8 and publication_cite(e.get("cite", ""))
                if anchored or external_cite(e.get("cite", ""), vid) or unique_scholarly:
                    entries.append(e)
                    kept_total += 1
                else:
                    removed += 1
            if entries:
                fdata["entries"] = entries
                fdata["status"] = "complete" if len(entries) >= 5 else "partial"
                if isinstance(fdata.get("coverage"), dict):
                    fdata["coverage"]["completed"] = len(entries)
            else:
                del extended[field]
        if extended:
            rec["extendedFields"] = extended
        else:
            rec.pop("extendedFields", None)

    # گام ۴: حذفِ متنِ تکراریِ میانِ فیلدهای همان آیه و فیلدهای خالی‌شده
    base_fields = ("notes", "context", "classical", "modern", "critical", "research")
    for rec in verses.values():
        seen = {}
        for f in base_fields:
            for item in rec.get(f) or []:
                seen.setdefault(re.sub(r"\s+", "", str(item.get("text", ""))), f)
        extended = rec.get("extendedFields") or {}
        for field in list(extended.keys()):
            fdata = extended[field]
            kept = []
            for e in fdata.get("entries") or []:
                key = re.sub(r"\s+", "", str(e.get("text", "")))
                if key in seen:
                    removed += 1
                    continue
                seen[key] = field
                kept.append(e)
            if kept:
                fdata["entries"] = kept
                fdata["status"] = "complete" if len(kept) >= 5 else "partial"
                if isinstance(fdata.get("coverage"), dict):
                    fdata["coverage"]["completed"] = len(kept)
            else:
                del extended[field]
        if extended:
            rec["extendedFields"] = extended
        else:
            rec.pop("extendedFields", None)

    for name in FILES:
        path = STATIC / name
        path.write_text(json.dumps(payloads[name], ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(name, "MB:", round(path.stat().st_size / 1e6, 2))
    print(f"stripped={stripped} dropped_short={dropped_short} kept={kept_total} removed={removed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
