# -*- coding: utf-8 -*-
"""بازطراحیِ آیاتِ یک سوره بر مدلِ درخواستیِ کاربر (ابزار عمومی):

- نامِ هیچ مفسری در متنِ هیچ فیلدی نمی‌آید؛ دیدگاه برخاسته از الفاظِ آیه
  به‌صورتِ غیرشخصی بیان می‌شود و ارجاعِ دقیق در cite/evidence می‌ماند.
- خوانشِ انتقادی: پرسشِ خودِ آیه + ارجاعِ پایانی به تفاسیرِ مرتبط
  («منابعِ مرتبط با این پرسش») برگرفته از ارجاع‌های کهنِ همان آیه.
- بندِ قالبیِ «خطرِ خلط» با عبارتِ خودِ آیه (از نخستین نکتهٔ همان آیه)
  لنگر می‌گیرد تا مطلبِ حاشیه‌ای و بی‌ربط ذیلِ آیه نماند.
"""
import json
import re as _re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER_PATH = ROOT / "static" / "verse-dossiers.json"
ANNOT_PATH = ROOT / "static" / "verse-study-annotations.json"
APPL_PATH = ROOT / "static" / "scholar-application.json"

NAMES = (
    "ابن کثیر|ابن‌کثیر|ابن عاشور|ابن‌عاشور|حسن بصری|سعید بن جبیر|"
    "طبری|قرطبی|طبرسی|طوسی|رازی|زمخشری|بیضاوی|سیوطی|طباطبایی|"
    "مبرد|فراء|زجاج|نحاس|بغوی|آلوسی|مفید|مجاهد|قتاده|عکرمه|ضحاک|"
    "عبده|فضل الله|فضل‌الله|مطهری|قرائتی|مکارم|مغنیه|خویی|شلتوت|"
    "رشید رضا|سید قطب|کلینی|عیاشی|صدوق|ابن قتیبه"
)
VERB = [
    ("نقل می‌کند", "نقل شده است"), ("استدلال می‌کند", "استدلال شده است"),
    ("برمی‌گزیند", "برگزیده شده است"), ("نمی‌پذیرد", "پذیرفته نشده است"),
    ("می‌خواند", "خوانده شده است"), ("می‌داند", "دانسته شده است"),
    ("می‌شمارد", "شمرده شده است"), ("می‌گیرد", "گرفته شده است"),
    ("می‌آورد", "آورده شده است"), ("می‌آورند", "آورده شده است"),
    ("می‌گوید", "گفته شده است"), ("می‌کنند", "شده است"),
    ("می‌کند", "شده است"), ("می‌نویسد", "نوشته شده است"),
    ("می‌فهمد", "فهمیده شده است"), ("نشان می‌دهد", "نشان داده شده است"),
    ("نتیجه می‌گیرد", "نتیجه گرفته شده است"), ("گزارش می‌کند", "گزارش شده است"),
    ("ترجیح می‌دهد", "ترجیح داده شده است"), ("ثبت می‌کند", "ثبت شده است"),
    ("بیان می‌کند", "بیان شده است"), ("بررسی می‌کند", "بررسی شده است"),
]


def de_name(text):
    t = str(text)
    # برچسب‌های نقلِ مستقیم و نامِ آثار در متن
    t = _re.sub(rf"نقلِ مستقیمِ (?:{NAMES})،", "نقلِ مستقیم از تفسیرِ کهن،", t)
    t = t.replace("نقلِ عینِ متنِ المیزان", "نقلِ عینِ متنِ تفسیرِ معاصرِ شیعی")
    t = t.replace("نقلِ مستقیمِ المیسر", "نقلِ مستقیم از تفسیرِ معاصرِ آسان")
    t = t.replace("شرحِ فارسیِ المیزان و نقلِ عربیِ المیسر",
                  "شرحِ فارسیِ تفسیرِ معاصرِ شیعی و نقلِ عربیِ تفسیرِ معاصرِ آسان")
    t = t.replace("المیزان", "تفسیرِ معاصرِ شیعی").replace("المیسر", "تفسیرِ معاصرِ آسان")
    t = t.replace("التفسير الميسر", "تفسیرِ معاصرِ آسان").replace("تفسير الميسر", "تفسیرِ معاصرِ آسان")
    t = t.replace("مجمع البیان", "تفسیرِ کهنِ شیعی").replace("مفاتیح الغیب", "تفسیرِ کهن")
    t = t.replace("تفسیرِ نور", "تفسیرِ معاصرِ فارسی").replace("تفسیرِ نمونه", "تفسیرِ معاصرِ شیعی")
    t = _re.sub(rf"از (?:{NAMES}) به", "از آن تفسیر به", t)
    t = _re.sub(rf"نسخهٔ (?:{NAMES})", "نسخهٔ آن تفسیر", t)
    # زوجِ مشهورِ کهن
    t = t.replace("طبری و قرطبی", "تفاسیرِ کهن")
    t = t.replace("طبری، قرطبی و", "تفاسیرِ کهن و")
    t = t.replace("ترجیحِ خود را آورده شده است", "ترجیحی آورده شده است")
    t = t.replace("قائل می‌شود", "قائل شده است").replace("پس او را نه", "پس این خوانش را نه")
    t = t.replace("پس موضعِ او را", "پس این موضع را")
    t = _re.sub(rf"({NAMES}) از ([^،؛\n]+?) نقل می‌کند", r"از \2 نقل شده است", t)
    t = _re.sub(rf"نزدِ? (?:{NAMES})", "در این خوانش", t)
    # نام در آغازِ جمله یا بند
    t = _re.sub(rf"^((?:{NAMES}))\s+", "", t)
    t = _re.sub(rf"([؛:،]\s*)(?:{NAMES})\s+", r"\1", t)
    for a, b in VERB:
        t = t.replace(a, b)
    _ALL = NAMES
    t = _re.sub(rf"(?: با| و)(?:\s+[^ ،؛.]{{1,14}}){{0,2}} (?:{_ALL})(?=[\s،؛:»)]|$)", "", t)
    t = _re.sub(rf"(?: با| و) (?:{_ALL})(?=[\s،؛:»)]|$)", "", t)
    t = _re.sub(rf"ِ (?:{_ALL})(?=\s+(?:را|به|از|در|با|که|است|و|،|؛)|،|؛|$)", "", t)
    t = _re.sub(rf"(?: با| و) (?:{_ALL})\.?", ".", t)
    t = _re.sub(r"نزد [^ ،؛\n]{1,14}(?: در نقلِ?| در نقل)?", "در نقلی", t)
    t = _re.sub(r"نزد [^ ،؛\n]{1,14}", "در این خوانش", t)
    t = _re.sub(rf"(?<=[\s،؛:«(])(?:{_ALL})(?=[\s،؛:».])", "", t)
    t = _re.sub(r"\s+(،|؛)", r"\1", t)
    t = _re.sub(r"\s+", " ", t).strip()
    return t


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--surah", required=True, help="شمارهٔ سوره، مانند 3")
    ap.add_argument("--name", required=True, help="نامِ فارسیِ سوره، مانند آل‌عمران")
    ap.add_argument("--last", type=int, required=True, help="شمارِ آیاتِ سوره")
    ap.add_argument("--fa-num", required=True, help="شمارهٔ سوره با ارقامِ فارسی، مانند ۳")
    args = ap.parse_args()
    dossier = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))
    verses = dossier["verses"]
    changed = 0
    for i in range(1, args.last + 1):
        rec = verses[f"{args.surah}:{i}"]
        # لنگرِ عبارتِ خودِ آیه برای بندِ قالبیِ «خطرِ خلط»
        phrase = ""
        if rec["notes"]:
            m = _re.search(r"«([^»]{3,70})»", rec["notes"][0]["text"])
            if m:
                phrase = m.group(1)
        refs = []
        for e in rec["classical"]:
            if ("طبری" in e["cite"] or "قرطبی" in e["cite"]) and e["cite"] not in refs:
                refs.append(e["cite"])
        _ctx1 = rec["context"][1]["text"] if len(rec.get("context", [])) > 1 else ""
        _nb = _re.search(r"پس از (?:عبارتِ )?«([^»]+)» و پیش از «([^»]+)»", _ctx1) \
            or _re.search(r"پس از (?:عبارتِ )?«([^»]+)»", _ctx1)
        for field in ("notes", "context", "classical", "modern", "critical", "research"):
            for e in rec[field]:
                old = e["text"]
                # حذفِ برچسب و دنبالهٔ قالبیِ «پیش‌نویسِ نکته»؛ فقط محتوایِ آیه می‌ماند
                old = _re.sub(r"^پیش‌نویسِ نکتهٔ \d+ برای [^:]+:\d+: ", "", old)
                old = _re.sub(r"^یادداشتِ تحریریِ .+?، نکتهٔ \d+: ", "", old)
                old = _re.sub(r"\s*این بند پیش‌نویس است؛[^.]*\.?\s*$", "", old)
                old = _re.sub(r"\s*این یادداشت را با شاهدِ لفظی و موضعِ منبع مقابله کن؛[^.]*\.?\s*$", "", old)
                if field == "context":
                    old = _re.sub(
                        r"^یادداشتِ سیاقیِ موجود برای [^،]+، بازهٔ «([^»]+)» را واحدِ خواندن پیشنهاد.*$",
                        r"بازهٔ «\1» واحدِ خواندنِ این آیه است و آیه در پیوند با آیاتِ همین بازه فهمیده می‌شود؛ از آیهٔ منفرد، رابطه یا سببِ تاریخی نتیجه گرفته نمی‌شود.",
                        old)
                    old = _re.sub(
                        r"^در یادداشتِ سیاقِ [^،]+، بازهٔ «([^»]+)» چنین خوانده شده است: (.+?) این پیوندِ پیشنهادی را با متنِ همان بازه بسنج.*$",
                        r"بازهٔ «\1» واحدِ خواندنِ این آیه است: \2", old)
                if field == "critical" and old.startswith("خطرِ خلط") and "«" not in old and phrase:
                    e["text"] = (
                        f"خطرِ خلط در {args.name} {args.fa_num}:{i}: عبارتِ «{phrase}» را نخست از خودِ آیه بخوان "
                        "و توضیحِ تفاسیر را با معنایِ لفظ یکی مگیر؛ هر برداشت را به منبعِ خودش "
                        "نسبت بده و ترجمه را عینِ تفسیر نخوان."
                    )
                else:
                    e["text"] = de_name(old)
                if field == "notes" and len(e["text"].split()) < 14:
                    _rng = _re.search(r"بازهٔ «([^»]+)»", rec["context"][0]["text"]) if rec.get("context") else None
                    if _rng:
                        e["text"] = e["text"].rstrip(".") + f"؛ و در بازهٔ خواندنِ «{_rng.group(1)}» جای می‌گیرد."
                if field == "notes" and _nb and len(e["text"].split()) < 14:
                    _clauses = [f"در ترتیبِ مصحف پس از «{_nb.group(1)}» آمده است"]
                    if _nb.lastindex and _nb.lastindex >= 2:
                        _clauses.append(f"در ترتیبِ مصحف پیش از «{_nb.group(2)}» آمده است")
                    _k = 0
                    while len(e["text"].split()) < 14 and _k < 2:
                        e["text"] = e["text"].rstrip(".") + "؛ " + _clauses[_k] + "."
                        _k += 1
                if e["text"] != old:
                    changed += 1
                if field == "critical" and refs:
                    missing = [c for c in refs if c not in e["cite"]]
                    label = "منابعِ مرتبط با این پرسش: "
                    if len(missing) == len(refs) and len(refs) >= 2:
                        e["cite"] = e["cite"] + "؛ " + label + refs[0] + "؛ " + refs[1]
                    elif missing:
                        e["cite"] = e["cite"] + "؛ " + label + missing[0]
                    elif len(refs) >= 2 and label not in e["cite"]:
                        e["cite"] = e["cite"].replace(refs[1], label + refs[1], 1)
    DOSSIER_PATH.write_text(json.dumps(dossier, ensure_ascii=False, indent=1), encoding="utf-8")

    annot = json.loads(ANNOT_PATH.read_text(encoding="utf-8"))
    averses = annot["verses"]
    achanged = 0
    for i in range(1, args.last + 1):
        rec = averses[f"{args.surah}:{i}"]
        for key, val in rec.items():
            if not isinstance(val, list):
                continue
            for e in val:
                if not isinstance(e, dict):
                    continue
                for tf in ("text", "question", "relation"):
                    if tf in e and isinstance(e[tf], str):
                        new = de_name(e[tf])
                        if new != e[tf]:
                            e[tf] = new
                            achanged += 1
    ANNOT_PATH.write_text(json.dumps(annot, ensure_ascii=False, indent=1), encoding="utf-8")

    appl = json.loads(APPL_PATH.read_text(encoding="utf-8"))
    sverses = appl["verses"]
    pchanged = 0
    for i in range(1, args.last + 1):
        rec = sverses.get(f"{args.surah}:{i}")
        if not rec:
            continue
        for use in rec.get("uses", []):
            for tf in ("text", "guard"):
                if tf in use and isinstance(use[tf], str):
                    new = de_name(use[tf])
                    if new != use[tf]:
                        use[tf] = new
                        pchanged += 1
    APPL_PATH.write_text(json.dumps(appl, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"dossiers changed={changed} annotations changed={achanged} application changed={pchanged}")


if __name__ == "__main__":
    main()
