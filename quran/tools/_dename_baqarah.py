# -*- coding: utf-8 -*-
"""بازطراحیِ آیاتِ بقره (۲:۱–۲۸۶) بر مدلِ درخواستیِ کاربر:

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
    t = t.replace("مجمع البیان", "تفسیرِ کهنِ شیعی").replace("مفاتیح الغیب", "تفسیرِ کهن")
    t = t.replace("تفسیرِ نور", "تفسیرِ معاصرِ فارسی").replace("تفسیرِ نمونه", "تفسیرِ معاصرِ شیعی")
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
    dossier = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))
    verses = dossier["verses"]
    changed = 0
    for i in range(1, 287):
        rec = verses[f"2:{i}"]
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
        for field in ("notes", "context", "classical", "modern", "critical", "research"):
            for e in rec[field]:
                old = e["text"]
                if field == "critical" and old.startswith("خطرِ خلط در بقره") and phrase:
                    e["text"] = (
                        f"خطرِ خلط در بقره ۲:{i}: عبارتِ «{phrase}» را نخست از خودِ آیه بخوان "
                        "و توضیحِ تفاسیر را با معنایِ لفظ یکی مگیر؛ هر برداشت را به منبعِ خودش "
                        "نسبت بده و ترجمه را عینِ تفسیر نخوان."
                    )
                else:
                    e["text"] = de_name(old)
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
    for i in range(1, 287):
        rec = averses[f"2:{i}"]
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
    for i in range(1, 287):
        rec = sverses.get(f"2:{i}")
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
