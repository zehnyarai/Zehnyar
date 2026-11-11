"""ساخت `data/booklets_1405.json` از متن دفترچه‌های انتخاب رشته‌ی ۱۴۰۵.

ورودی: پوشه‌ای که در آن فایل‌های متنی استخراج‌شده هستند:
  ensani.txt, riazi.txt, tajrobi.txt, honar.txt, zaban.txt
  (هر فایل با خط‌های «=====PAGE n=====» صفحه‌بندی شده است)

استخراج متن از PDF (با pypdf):
  python3 -m venv venv && ./venv/bin/pip install pypdf
  ./venv/bin/python -c "import sys,unicodedata;from pypdf import PdfReader as R; ..."
  (هر صفحه: extract_text() با NFKC نرمال‌سازی و خط جداکننده‌ی «=====PAGE n=====»)

اجرا: python3 reshteyar/scripts/build_booklets_1405.py <txt_dir> reshteyar/data/booklets_1405.json

روش:
- هر ردیف کدرشته‌محل با «ظرفیت + نام رشته + کد پنج‌رقمی» شناخته می‌شود.
- نام دانشگاه/پردیس از متن قبل از ردیف برداشته می‌شود. اگر خالی باشد، از ردیف قبلی گرفته می‌شود
  (در جدول‌ها نام دانشگاه برای ردیف‌های پشت‌سرهم فقط یک بار نوشته شده است).
- نام‌هایی که فقط با پسوند «- شهر» فرق دارند زیر نام اصلی ادغام می‌شوند.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

GROUPS = {"riazi": "ریاضی و فنی", "tajrobi": "علوم تجربی", "ensani": "علوم انسانی",
          "honar": "هنر", "zaban": "زبان‌های خارجی"}
DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
HEADER_LINE = re.compile(r"دفترچه راهنما|محل خدمت|رشتههای تحصیلی|رشته‌های تحصیلی|^\s*\d{1,3}\s*$|^\s*ادامه|کدرشته")
HEADER_WORDS = re.compile(r"توضیحات جنس پذیرش ظرفیت پذیرش نیمسال عنوان رشته کد رشته محل دوره تحصیلی نحوه پذیرش(?: مرد زن دوم اول)?")
ROW = re.compile(r"((?:(?:مرد|زن|-)\s*)+)\s(\d{1,3})\s+([^\d\-]{2,}?)\s+(\d{4,6})(?=\s|$)")
CUT_WORDS = ["روزانه", "نوبت دوم", "شهریه پرداز", "شهریهپرداز", "پیامنور", "صرفا", "صرفاً", "با آزمون",
             "فاقد خوابگاه", "دارای خوابگاه", "ممنوعیت", "عدم تعهد", "محدودیت", "شرایط در", "توضیحات", "امکان ",
             "مرد ", "زن ", "استان ", "ناحیه", "منطقه", "کارآموزی", "انجام کلیه", "دارای مصاحبه", "دارایخوابگاه",
             "بورس", "آزاد تمام وقت"]
CUT_RE = re.compile("|".join(re.escape(w) for w in CUT_WORDS))
INST = re.compile(r"(?:^|\s)(دانشگاه|پردیس|مؤسسه|موسسه|دانشکده|پژوهشگاه|آموزشکده|پژوهشکده|مجتمع|مرکز آموزش عالی|مرکز|واحد)(?=\s)")
SUFFIX = re.compile(r"^(.*?)\s+-\s+([^-]{2,20})$")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).translate(DIGITS)
    s = s.replace("ي", "ی").replace("ك", "ک").replace("\u200c", " ").replace("\u200f", "").replace("\u200e", "")
    return re.sub(r"[ \t]+", " ", s)


def place_inst(seg: str) -> tuple[str, str]:
    ms = list(INST.finditer(seg))
    if not ms:
        return "", ""
    m = ms[-1]
    before, inst = seg[:m.start()], seg[m.start():]
    c = CUT_RE.search(inst)
    if c and c.start() > 3:
        inst = inst[:c.start()]
    inst = inst.split("/")[0]
    inst = re.split(r"\s+-\s+|\s*\(\s*محل|\s*اولویت|\s*مخصوص", inst)[0]
    inst = re.split(r"\.\s|\.$", inst)[0].strip(" -،,()")
    cb = list(CUT_RE.finditer(before))
    place = before[cb[-1].end():] if cb else before
    return place.strip(" -،,()"), inst


def clean_name(s: str) -> str:
    s = re.sub(r"\(\s*(?:این|اینرشته|این رشته)[^)]*\)", "", s)
    s = re.sub(r"\(\s*[^)]*متعلق[^)]*\)", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s.count("(") > s.count(")"):
        s = s[: s.rfind("(")].strip()
    s = re.sub(r"\s*-\s*", " - ", s)
    return s.strip(" -،,")


def clean_uni(s: str) -> str:
    s = s.replace("–", "-")
    s = re.split(r"\s+اسامی\s|\s+در استان|\s+نداشتن|\s+سال اول|\s+باتوجه|\s+شرایط|\s+ممنوعیت", s)[0]
    s = clean_name(s)
    if len(s) < 6 or s in ("دانشگاه در", "دانشگاه", "پردیس", "مرکز", "موسسه", "دانشکده"):
        return ""
    return s


def key(s: str) -> str:
    return re.sub(r"[\s\-()،,‌.]", "", s)


def parse_group(txt: str, grp: str) -> list[dict]:
    parts = []
    for line in norm(txt).split("\n"):
        mp = re.match(r"=====PAGE (\d+)=====", line)
        if mp:
            parts.append(f" \x00{mp.group(1)}\x00 ")
            continue
        if HEADER_LINE.search(line):
            continue
        parts.append(line.strip() + " ")
    text = HEADER_WORDS.sub(" ", re.sub(r"\s+", " ", "".join(parts)))
    rows, last, page = [], 0, None
    last_inst = ""
    for m in ROW.finditer(text):
        seg_raw = text[last:m.start()]
        pages = re.findall(r"\x00(\d+)\x00", seg_raw)
        if pages:
            page = int(pages[-1])
        seg = re.sub(r"\x00\d+\x00", " ", seg_raw).strip()
        seg = re.sub(r"(?:\s*-)+\s*$", "", seg).strip()
        place, inst = place_inst(seg)
        uni = clean_uni(inst)
        if uni:
            last_inst = uni
        else:
            uni = last_inst
        field = clean_name(m.group(3).strip(" -،,"))
        if field:
            rows.append({"group": grp, "code": m.group(4), "field": field, "university": uni,
                         "location": place, "capacity": int(m.group(2)), "page": page})
        last = m.end()
    return rows


CATALOGUE = re.compile(r"(?:کارشناسی|کاردانی|دکتری)(?: ناپیوسته| پیوسته| ارشد| عمومی| حرفه ای)*\s+([^\d]{3,70}?)\s+(?:کشوری|قطبی|ایناحیه|ناحیه ای|ناحیهای|استانی)")


def catalogue_names(txt: str) -> list[str]:
    """نام رشته‌ها از جدول «رشته‌های تحصیلی» (برای رشته‌هایی که در جدول کدرشته‌محل نیستند)."""
    return [clean_name(m.group(1).strip()) for m in CATALOGUE.finditer(norm(txt))]


def build(txt_dir: Path) -> dict:
    out = {"year": 1405, "groups": {}}
    for slug, grp in GROUPS.items():
        rows = parse_group((txt_dir / f"{slug}.txt").read_text(encoding="utf-8"), grp)
        ucount, fcount = defaultdict(Counter), defaultdict(Counter)
        for r in rows:
            u = r["university"] or "(نامشخص)"
            ucount[key(u)][u] += 1
            fcount[key(r["field"])][r["field"]] += 1
        names = {c.most_common(1)[0][0]: sum(c.values()) for c in ucount.values()}
        merged: Counter = Counter()
        for name, n in names.items():
            m = SUFFIX.match(name)
            base = m.group(1).strip() if m else None
            merged[base if base and base in names and name != "(نامشخص)" else name] += n
        unis = sorted(({"name": n, "rows": c} for n, c in merged.items()), key=lambda x: (-x["rows"], x["name"]))
        flds = sorted(({"name": c.most_common(1)[0][0], "rows": sum(c.values())} for c in fcount.values()),
                      key=lambda x: (-x["rows"], x["name"]))
        have = {key(f["name"]) for f in flds}
        extra = []
        for name in catalogue_names((txt_dir / f"{slug}.txt").read_text(encoding="utf-8")):
            k = key(name)
            if len(k) > 4 and k not in have:
                have.add(k)
                extra.append({"name": name, "rows": 0, "catalogue_only": True})
        out["groups"][slug] = {"title": grp, "rows": len(rows), "universities": unis,
                               "fields": flds + sorted(extra, key=lambda x: x["name"])}
        print(slug, "rows", len(rows), "universities", len(unis), "fields", len(flds),
              "unnamed", names.get("(نامشخص)", 0), file=sys.stderr)
    out["note"] = ("فهرست از متن دفترچه‌های PDF استخراج شده و بازبینی دستی نشده است. "
                   "اصلاحیه‌های ۱۶، ۱۸ و ۱۹ مهر ۱۴۰۵ اعمال نشده‌اند. "
                   "فهرست رشته‌ها فقط از ردیف‌های کدرشته‌محل استخراج شده است.")
    return out


if __name__ == "__main__":
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    dst.write_text(json.dumps(build(src), ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", dst, file=sys.stderr)
