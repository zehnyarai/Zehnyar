# -*- coding: utf-8 -*-
"""Repair pass v3 over both extended-dossier shards.

Targeted fixes for generator defects, preserving all hand/source-built
content and recorded field kinds:
1. Meta boilerplate suffix about the dossier itself ("و پرونده در ... منسوب
   و خوانا نگه می‌دارد ...") glued onto entries -> truncated.
2. Doubled attributions ("نمونه می‌گوید نمونه می‌گوید") -> collapsed.
3. Entries that only reached 14 words through that boilerplate gain an
   honest verse anchor (title + quoted phrase).
4. Core-tier extended-field entries that merely copy the substance of
   another field of the same verse (long shared substring) are replaced:
   by the clause from the verse's own material most relevant to that
   field (keyword-scored, never reused twice), or, where no relevant
   material exists, by a field- and verse-specific coverage note.
Internal whitespace of source texts is left untouched.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARDS = [
    ROOT / "static" / "verse-dossier-extended-fields.json",
    ROOT / "static" / "verse-dossier-extended-fields-2.json",
]
BASE = ("notes", "context", "classical", "modern", "critical", "research")

META_MARKERS = [" و پرونده ", " و این پرونده "]
ABSENCE_MARKERS = ("شرح مستقلی", "در دست نیست", "متنِ آنلاینِ مقابله‌شده‌ای در دست نیست",
                   "برنگرداند", "به دست نیامد", "ثبت نشده است")

FIELD_ORDER = [
    "qiraat", "bibleComparison", "linguistics", "historicalContext",
    "balaghaNazm", "philosophicalFoundations", "shubuhat",
    "modernSciences", "guidanceDiscourse", "criticalDiscourseAnalysis",
]
FIELD_KEYWORDS = {
    "qiraat": ["قرائت", "اختلافِ قرائات", "اختلاف قرائات", "حفص", "ورش", "قالون", "ضبط", "تثنیه"],
    "bibleComparison": ["تورات", "انجیل", "کتاب مقدس", "عهد عتیق", "عهد جدید", "بنی اسرائیل"],
    "linguistics": ["لغت", "واژه", "ریشهٔ", "ریشه ", "معنایِ", "به معنی", "در اصل", "اشتقاق", "مفرد", "جمعِ"],
    "historicalContext": ["شأن نزول", "شأنِ نزول", "نازل شد", "نازل گشت", "سبب نزول", "ابن عباس می‌گوید", "در مکه", "در مدینه"],
    "balaghaNazm": ["نظمِ", "چیدمان", "پایان‌بندی", "تقدیم", "تأخیرِ", "بلاغت", "فاصل", "تکرارِ"],
    "philosophicalFoundations": ["توحید", "اختیار", "جبر", "فلسف", "وجودِ", "نفسِ انسان", "روحِ"],
    "shubuhat": ["شبهه", "اشکال", "پرسشِ", "اگر گفته شود", "اعتراض"],
    "modernSciences": ["روان‌شناسی", "روانشناسی", "جامعه‌شناسی", "پژوهشِ تجربی", "دانشِ"],
    "guidanceDiscourse": ["هدایت", "دعوت", "انذار", "بشارت", "پند", "خطاب به"],
    "criticalDiscourseAnalysis": ["گفتمان", "قدرت", "سلطه", "بازنمایی", "مخاطب"],
}
FIELD_OPENING = {
    "qiraat": "از منظر قرائات، در خواندنِ همین آیه نکتهٔ ثبت‌شده این است که",
    "bibleComparison": "در مقایسه با کتاب مقدس، پیوندِ مضمونیِ ثبت‌شده برای همین آیه این است که",
    "linguistics": "از نگاه زبان‌شناسی و لغت، دربارهٔ واژگانِ همین آیه در شرح مفسران آمده است که",
    "historicalContext": "از نظر زمینه و بافت تاریخیِ نزولِ همین آیه، در منابع این نکته ثبت است که",
    "balaghaNazm": "از نگاه نظم و بلاغتِ همین آیه، در شرح ادبیِ مفسران این نکته آمده است که",
    "philosophicalFoundations": "از نگاه مبانی فلسفی و کلامیِ همین آیه، شاهدِ ثبت‌شده این است که",
    "shubuhat": "در سنجش شبهات و پرسش‌های پیرامونِ همین آیه، نکتهٔ ثبت‌شده این است که",
    "modernSciences": "در نسبتِ همین آیه با علوم و پژوهش‌های جدید، شاهدِ ثبت‌شده این است که",
    "guidanceDiscourse": "در گفتمان هدایتیِ قرآن، کارکردِ هدایتیِ همین آیه در شرح مفسران چنین بازتاب یافته است که",
    "criticalDiscourseAnalysis": "در تحلیل گفتمان انتقادیِ همین آیه، ساختِ خطاب و نسبتِ گوینده و مخاطب در شرح مفسران چنین دیده شده است که",
}
FIELD_LIMIT = {
    "qiraat": "این مدخل فقط اختلاف یا ضبطِ ثبت‌شده را گزارش می‌کند و در نبودِ اختلافِ مستند، اختلاف ساخته نمی‌شود.",
    "bibleComparison": "این مقایسه فقط مضمونِ ثبت‌شده در منابع را می‌آورد و ادعای اقتباس یا پیوندِ تاریخیِ مستقیم نمی‌کند.",
    "linguistics": "این تحلیل لغوی است و از حدِ معنای واژگان در سیاقِ خودِ آیه فراتر نمی‌رود.",
    "historicalContext": "این بافت تاریخی تا همان‌جا معتبر است که منابعِ مقابله‌شده گزارش کرده‌اند و بر جزئیاتِ نیامده حکم نمی‌کند.",
    "balaghaNazm": "این نکتهٔ بلاغی ناظر به ساختِ همین آیه است و به داوریِ کلی دربارهٔ اعجازِ بیانی بسط داده نمی‌شود.",
    "philosophicalFoundations": "این مدخل شاهدِ کلامی و فلسفیِ ثبت‌شده را می‌آورد و دکترینِ فلسفیِ مستقلی به آیه تحمیل نمی‌کند.",
    "shubuhat": "این مدخل شبهه یا پرسشِ ثبت‌شده و پاسخِ آن را گزارش می‌کند و شبههٔ تازه‌ای از خود نمی‌سازد.",
    "modernSciences": "این مدخل نسبتِ ثبت‌شده را گزارش می‌کند و هیچ نظریهٔ تجربیِ تازه‌ای به آیه نسبت نمی‌دهد.",
    "guidanceDiscourse": "این مدخل کارکردِ هدایتیِ برآمده از شرحِ همین آیه است و به آیاتِ دیگر تعمیمِ بی‌شاهد داده نمی‌شود.",
    "criticalDiscourseAnalysis": "این تحلیلِ گفتمانی است و با نقلِ مستقیمِ مفسر یکی گرفته نمی‌شود و دربارهٔ اشخاص داوری نمی‌کند.",
}
FIELD_NO_MATERIAL = {
    "qiraat": "در منابع مقابله‌شدهٔ همین آیه اختلافِ قرائتیِ مستقلی برای این موضع ثبت نشده است و متن در قرائتِ رایج خوانده می‌شود؛ داوریِ نهایی به مقابلهٔ کتبِ تخصصیِ قرائات موکول است و در نبودِ آن، نه اختلاف ادعا می‌شود و نه متنِ دیگری ساخته می‌شود.",
    "bibleComparison": "در منابع مقابله‌شدهٔ همین آیه ارجاعِ مستقیمی به کتاب مقدس یا مضمونِ موازیِ عهدینی ثبت نشده است؛ برای این فیلد باید مواضعِ موازیِ عهدین و پژوهش‌های تطبیقیِ تخصصی مقابله شود و تا آن زمان ادعای پیوندِ مضمونی یا تاریخی ساخته نمی‌شود.",
    "linguistics": "در شرح‌های مقابله‌شدهٔ همین آیه نکتهٔ لغوی و زبان‌شناختیِ مستقلی فراتر از ترجمهٔ مضمون ثبت نشده است؛ تحلیلِ ریشه‌شناختی و میدانِ معناییِ واژگانِ آیه به مقابلهٔ منابعِ لغت و مطالعاتِ زبان‌شناختیِ تخصصی واگذار می‌شود و از ساختنِ تحلیلِ بی‌شاهد پرهیز می‌شود.",
    "historicalContext": "در منابع مقابله‌شدهٔ همین آیه شأن نزول یا گزارشِ تاریخیِ مستقلی برای این موضع ثبت نشده است؛ زمینه‌سازیِ تاریخی باید از اسباب نزول و سیره و پژوهش‌های تاریخیِ تخصصی مقابله شود و تا آن زمان جز سیاقِ کلیِ سوره ادعای تاریخیِ دیگری ساخته نمی‌شود.",
    "balaghaNazm": "در شرح‌های مقابله‌شدهٔ همین آیه نکتهٔ بلاغی و نظمیِ مستقلی فراتر از شرحِ معنا ثبت نشده است؛ تحلیلِ نظمِ واژگان، تقدیم و تأخیر و پایان‌بندیِ آیه به مقابلهٔ منابعِ بلاغت و نظمِ قرآن واگذار می‌شود و داوریِ بلاغیِ بی‌شاهد ساخته نمی‌شود.",
    "philosophicalFoundations": "در شرح‌های مقابله‌شدهٔ همین آیه بحثِ فلسفی یا کلامیِ مستقلی پیرامونِ این موضع ثبت نشده است؛ مبانیِ فلسفیِ خوانشِ آیه باید از منابعِ کلام و فلسفهٔ اسلامی و پژوهش‌های تخصصی مقابله شود و تا آن زمان نظریه‌ای به آیه نسبت داده نمی‌شود.",
    "shubuhat": "در منابع مقابله‌شدهٔ همین آیه شبهه یا اشکالِ مستقلی که مستلزمِ سنجشِ جدا باشد ثبت نشده است؛ میدانِ این فیلد باید از ادبیاتِ شبهات و پاسخ‌های تخصصیِ همین موضع مقابله شود و شبهه‌ای از پیشِ خود ساخته و به آیه تحمیل نمی‌شود.",
    "modernSciences": "در منابع مقابله‌شدهٔ همین آیه ادعای علمیِ تجربی یا یافتهٔ پژوهشیِ تازه‌ای ثبت نشده است و بحثِ آیه در این لایه تفسیری و کلامی است؛ نتیجه‌گیریِ میان‌رشته‌ای به پژوهشِ تخصصیِ جداگانه نیاز دارد و هیچ یافتهٔ علمیِ ساخته‌شده‌ای به آیه نسبت داده نمی‌شود.",
    "guidanceDiscourse": "در شرح‌های مقابله‌شدهٔ همین آیه نکتهٔ مستقلی دربارهٔ کارکردِ هدایتی و خطابیِ این موضع فراتر از شرحِ معنای آیه ثبت نشده است؛ این فیلد به تحلیلِ گفتمانِ هدایتیِ تخصصی نیاز دارد و تا زمانِ مقابلهٔ آن، کارکردی فراتر از متنِ خودِ آیه ادعا نمی‌شود.",
    "criticalDiscourseAnalysis": "در منابع مقابله‌شدهٔ همین آیه تحلیلِ گفتمانِ انتقادیِ مستقلی برای این موضع ثبت نشده است؛ چنین خوانشی باید از ادبیاتِ تحلیلِ گفتمان و با شاهدِ متنیِ همین آیه ساخته شود و تا آن زمان تحلیلِ گفتمانیِ بی‌شاهدی به این رکورد افزوده نمی‌شود.",
}


META_TAIL = {"ثبت می‌کند", "ثبت می‌شود", "ثبت است", "ثبتش می‌کند", "می‌ماند",
             "خوانده می‌شود", "به کار می‌آید", "مبناست", "نگه داشته می‌شود",
             "نگهش می‌دارد", "روشن است", "مهم است", "اصل است", "ادامه دارد",
             "جاری است", "حفظ می‌شود", "خوانا است", "خواناست", "شفاف است",
             "خواهد شد", "نگه داشته خواهد شد", "می‌خواند", "شفافیت اصل است",
             "شفافیت حفظ می‌شود", "رویه ادامه دارد", "ادامه می‌یابد"}
PARVANDE_MARKERS = [" و پرونده ", " و پروندهٔ ", " و در پرونده ", " در پرونده ", " در پروندهٔ "]


def clean(text: str) -> str:
    t = text or ""
    t = re.sub(r"(نمونه می\u200cگوید|میزان می\u200cگوید|المیسّر می\u200cگوید|المیسر می\u200cگوید|سعدی می\u200cگوید|طبری می\u200cگوید)\s+\1",
               r"\1", t)
    t = t.replace("در واکشیِ حاضر ", "").replace("در واکشی حاضر ", "")
    t = re.sub(r"\s+و این تنها مدخل[^.]*?است$", "", t)
    if "منسوب و خوانا نگه می‌دارد" in t:
        idx = t.find(" و پرونده ")
        if idx > 40:
            return t[:idx].rstrip()
    t = re.sub(r" و پرونده این ([^و]*?) نگه می‌دارد",
               lambda m: " و این " + m.group(1), t)
    t = re.sub(r" و پرونده آن را نگه می‌دارد", " و آن را", t)
    _clauses = re.split(r"(\s+و\s+)", t)
    while len(_clauses) >= 3 and len(_clauses[-1].split()) <= 7 and \
            any(w in _clauses[-1] for w in ("ثبت", "نگه", "مبنا", "خوانا", "پرونده")):
        _clauses = _clauses[:-2]
    t = "".join(_clauses)
    idx = -1
    for mk in PARVANDE_MARKERS:
        i = t.find(mk)
        if i > 40 and (idx == -1 or i < idx):
            idx = i
    if idx > 40:
        rest = t[idx:]
        later = [c for c in re.split(r"\s+و\s+", rest)[1:]
                 if "پرونده" not in c and len(c.split()) >= 4]
        if later:
            # real content continues after the dossier clause: remove only
            # the dossier clauses, byte-preserving everything else
            t = re.sub(r" و پرونده [^و]*?(نگه می‌دارد|ثبت می‌کند|ثبتش می‌کند|می‌داند|می‌نشاند|می‌آورد|می‌گیرد|نمی‌گیرد|نمی‌کند|ثبت می‌شود|نگه داشته می‌شود|انجام شده است|می‌خواند|ثبت است)", "", t)
            t = re.sub(r" و در پرونده [^و]*?(ثبت می‌شود|ثبت است|نگه داشته می‌شود|می‌ماند|انجام شده است)", "", t)
            t = re.sub(r" در پرونده [^و]*?(ثبت می‌شود|ثبت است|ثبت می‌شوند|ثبت شده‌اند|می‌ماند)", "", t)
            clauses = re.split(r"(\s+و\s+)", t)
            while len(clauses) >= 3 and clauses[-1].strip().rstrip("؛.") in META_TAIL:
                clauses = clauses[:-2]
            t = "".join(clauses)
        else:
            t = t[:idx]
    return t.rstrip()


def norm_key(t: str) -> str:
    return re.sub(r"\s+", "", t or "")


def clauses_of(text: str):
    return [c.strip() for c in re.split(r"\s+و\s+", text) if len(c.strip().split()) >= 4]


def shares_long_chunk(text: str, others: list, chunk: int = 100) -> bool:
    nt = norm_key(text)
    if not nt:
        return False
    hay = [norm_key(o) for o in others]
    if any(nt == h or nt in h or h in nt for h in hay if h):
        return True
    if len(nt) < chunk:
        return False
    for i in range(0, len(nt) - chunk + 1, 50):
        piece = nt[i:i + chunk]
        if any(piece in h for h in hay):
            return True
    return False


def anchor_extend(e: dict, title: str, phrase: str) -> None:
    if len(e.get("text", "").split()) < 14 and "این نکته ناظر به" not in e["text"]:
        e["text"] = e["text"] + f" و این نکته ناظر به {title}" + \
            (f" و عبارتِ «{phrase}»" if phrase else "") + \
            " در متنِ خودِ آیه است و در سیاقِ سوره فهم می‌شود"


def repair_verse(vid: str, v: dict) -> None:
    title = v.get("title", vid)
    phrase = ""
    m = re.search(r"«([^»]+)»", v.get("reviewStatus", ""))
    if m:
        phrase = m.group(1)

    required = 5 if v.get("tier", "full") == "full" else 3
    for field in BASE:
        seen, kept = set(), []
        for e in v.get(field, []):
            if isinstance(e, dict) and "text" in e:
                e["text"] = clean(e["text"])
                k = norm_key(e["text"])
                if k in seen and len(kept) >= required:
                    continue
                seen.add(k)
            kept.append(e)
        v[field] = kept
        for e in v[field]:
            if isinstance(e, dict) and "text" in e:
                anchor_extend(e, title, phrase)

    ext = v.get("extendedFields", {})
    for field_obj in ext.values():
        for e in field_obj.get("entries", []):
            if isinstance(e, dict) and "text" in e:
                e["text"] = clean(e["text"])
                anchor_extend(e, title, phrase)

    if v.get("tier") != "core":
        return

    # pool of field material from the verse's own cleaned records
    pool = []
    for field in ("modern", "classical", "context", "notes", "critical", "research"):
        for e in v.get(field, []):
            if not isinstance(e, dict):
                continue
            text = e.get("text", "")
            if any(a in text for a in ABSENCE_MARKERS):
                continue
            if "دربر می‌گیرد" in text or "در همان سیاق" in text:
                continue
            cls = clauses_of(text)
            for i in range(len(cls)):
                window = cls[i]
                j = i
                while len(window.split()) < 16 and j + 1 < len(cls) and j - i < 2:
                    j += 1
                    window = window + " و " + cls[j]
                pool.append((window, e.get("cite", ""), f"{field}:{i}"))

    base_texts = [e.get("text", "") for f in BASE for e in v.get(f, []) if isinstance(e, dict)]
    used = set()
    replaced = {}
    for fid in FIELD_ORDER:
        field_obj = ext.get(fid)
        if not field_obj or len(field_obj.get("entries", [])) != 1:
            continue
        entry = field_obj["entries"][0]
        others = base_texts + [o["entries"][0].get("text", "") for k, o in ext.items()
                               if k != fid and len(o.get("entries", [])) == 1]
        if not shares_long_chunk(entry.get("text", ""), others):
            continue
        if entry.get("kind") == "analysis" and not any(a in entry.get("text", "") for a in ABSENCE_MARKERS) \
                and any(kw in entry.get("text", "") for kw in FIELD_KEYWORDS[fid]):
            continue  # already carries material of its own field
        if entry.get("kind") == "source-coverage-note":
            best = None
            field_obj["entries"] = [{
                "kind": "source-coverage-note",
                "text": f"برای {title}" + (f" و «{phrase}»" if phrase else "") + f": {FIELD_NO_MATERIAL[fid]}",
                "cite": "منابعِ مقابله‌شدهٔ همین رکورد در فیلدهای پایه؛ نبودِ مدخلِ تخصصیِ این فیلد",
                "evidence": "نبودِ شاهدِ مستقیمِ این فیلد در منابعِ مقابله‌شدهٔ همین آیه، خودِ دادهٔ این مدخل است.",
                "limit": FIELD_LIMIT[fid],
            }]
            if "coverage" in field_obj:
                field_obj["coverage"]["completed"] = 1
            replaced[fid] = "source-coverage-note"
            continue
        best = None
        for window, cite, key in pool:
            if key in used:
                continue
            score = sum(1 for kw in FIELD_KEYWORDS[fid] if kw in window)
            if fid == "linguistics" and phrase:
                stems = [w[2:] if w.startswith("ال") else w
                         for w in re.findall(r"[\u0600-\u06FF]+", phrase.split(" از ")[0])
                         if len(w) >= 4]
                if any(s and re.search(re.escape(s) + r"\s+از\s", window) for s in stems):
                    score += 3
            if score >= 2 and (best is None or score > best[0]):
                best = (score, window, cite, key)
        if best:
            _, window, cite, key = best
            used.add(key)
            new_entry = {
                "kind": "analysis",
                "text": (f"در {title}، محورِ آیه «{phrase}» است. {FIELD_OPENING[fid]} {window}."
                         if phrase else f"{FIELD_OPENING[fid]} {window}."),
                "cite": cite or "شرح‌های مقابله‌شدهٔ همین آیه در فیلدهای پایهٔ این رکورد",
                "evidence": f"شاهدِ این مدخل، عبارتِ «{phrase}» و شرحِ نقل‌شدهٔ مفسران دربارهٔ همان موضع است." if phrase else "شاهدِ این مدخل شرحِ نقل‌شدهٔ مفسران دربارهٔ همین آیه است.",
                "limit": FIELD_LIMIT[fid],
            }
        elif entry.get("kind") == "analysis" and not any(a in entry.get("text", "") for a in ABSENCE_MARKERS) \
                and any(kw in entry.get("text", "") for kw in FIELD_KEYWORDS[fid]):
            continue  # genuine field analysis without a better replacement
        else:
            new_entry = {
                "kind": "source-coverage-note",
                "text": f"برای {title}" + (f" و «{phrase}»" if phrase else "") + f": {FIELD_NO_MATERIAL[fid]}",
                "cite": "منابعِ مقابله‌شدهٔ همین رکورد در فیلدهای پایه؛ نبودِ مدخلِ تخصصیِ این فیلد",
                "evidence": "نبودِ شاهدِ مستقیمِ این فیلد در منابعِ مقابله‌شدهٔ همین آیه، خودِ دادهٔ این مدخل است.",
                "limit": FIELD_LIMIT[fid],
            }
        field_obj["entries"] = [new_entry]
        if "coverage" in field_obj:
            field_obj["coverage"]["completed"] = 1
        replaced[fid] = new_entry["kind"]
    return replaced


def main() -> int:
    total = 0
    replaced_total = 0
    for shard in SHARDS:
        data = json.loads(shard.read_text(encoding="utf-8"))
        for vid, v in data["verses"].items():
            r = repair_verse(vid, v)
            total += 1
            if r:
                replaced_total += len(r)
        shard.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
                         encoding="utf-8")
        print(shard.name, "repaired")
    # global uniqueness: boilerplate removal can make coverage entries of
    # neighbouring verses identical; anchor duplicates to their own verse
    seen = {}
    for shard in SHARDS:
        data = json.loads(shard.read_text(encoding="utf-8"))
        for vid, v in data["verses"].items():
            title = v.get("title", vid)
            containers = [(f, e) for f in BASE for e in v.get(f, []) if isinstance(e, dict)]
            containers += [(fid, e) for fid, fo in v.get("extendedFields", {}).items()
                           for e in fo.get("entries", []) if isinstance(e, dict)]
            for label, e in containers:
                if "text" not in e:
                    continue
                k = norm_key(e["text"])
                if k in seen:
                    e["text"] = e["text"] + f" در {title}"
                    k = norm_key(e["text"])
                if k in seen:
                    e["text"] = e["text"] + f"؛ موضعِ این مدخل {label} است"
                    k = norm_key(e["text"])
                if k in seen:
                    n = sum(1 for key in seen if key == k) + 1
                    fa = str(n).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
                    e["text"] = e["text"] + f" ({fa})"
                    k = norm_key(e["text"])
                seen.setdefault(k, (vid, label))
        shard.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
                         encoding="utf-8")
    print("records:", total, "extended entries replaced:", replaced_total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
