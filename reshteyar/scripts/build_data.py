"""
ساخت فایل‌های داده‌ی رشته‌یار از منابع باز.

منابع (هر دو مخزن در GitHub منتشر شده‌اند؛ مجوز صریح ندارند؛ ببینید data/SOURCES.md):
  * farhadmpr/List-of-universities      -> university.csv (داده‌ی فهرست موسسات وزارت علوم، msrt.ir)
  * mdabagh/List-of-universities-and-academic-fields-in-Iran -> university.json و academic_discipline.json

اجرا:
  python scripts/build_data.py            # دانلود از codeload.github.com و ساخت data/*.json
  python scripts/build_data.py --offline  # فقط از scripts/.cache استفاده می‌کند

خروجی: data/universities.json, data/fields.json, data/meta.json
نگاشت «رشته -> گروه آزمایشی» و «دانشگاه -> گروه مرتبط» تقریبی و قاعده‌محور است؛
برای دقت بالا باید با دفترچه‌ی انتخاب رشته‌ی همان سال تطبیق داده شود.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import tarfile
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path(__file__).resolve().parent / ".cache"
DATA = ROOT / "data"

ARCHIVES = {
    "msrt": (
        "https://codeload.github.com/farhadmpr/List-of-universities/tar.gz/refs/heads/master",
        "List-of-universities-master/university.csv",
    ),
    "mdabagh_univ": (
        "https://codeload.github.com/mdabagh/List-of-universities-and-academic-fields-in-Iran/tar.gz/refs/heads/main",
        "List-of-universities-and-academic-fields-in-Iran-main/university.json",
    ),
    "mdabagh_fields": (
        "https://codeload.github.com/mdabagh/List-of-universities-and-academic-fields-in-Iran/tar.gz/refs/heads/main",
        "List-of-universities-and-academic-fields-in-Iran-main/academic_discipline.json",
    ),
}

PROVINCES = {
    "آذربایجان شرقی", "آذربایجان غربی", "اردبیل", "اصفهان", "البرز", "ایلام", "بوشهر", "تهران",
    "خراسان جنوبی", "خراسان رضوی", "خراسان شمالی", "خوزستان", "زنجان", "سمنان", "سیستان و بلوچستان",
    "فارس", "قزوین", "قم", "لرستان", "مازندران", "مرکزی", "هرمزگان", "همدان", "چهارمحال و بختیاری",
    "کردستان", "کرمان", "کرمانشاه", "کهگیلویه و بویراحمد", "گلستان", "گیلان", "یزد",
}


# ---------------------------------------------------------------- helpers
def fa(s) -> str:
    """یکدست‌سازی متن فارسی: حروف عربی، نیم‌فاصله‌ها و فاصله‌های اضافه."""
    if s is None:
        return ""
    s = str(s).strip().strip("'").strip()
    s = s.replace("\u064a", "ی").replace("\u0643", "ک").replace("\xad", "")
    s = s.replace("\u200f", "").replace("\u200e", "").replace("\u200c", " ")
    s = re.sub(r"\s*[-–—]\s*", " - ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip(" -،,")


def fetch_archive(url: str, offline: bool) -> bytes:
    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / (re.sub(r"[^A-Za-z0-9]+", "_", url)[-80:] + ".tgz")
    if cached.exists():
        return cached.read_bytes()
    if offline:
        raise SystemExit(f"نسخه‌ی محلی وجود ندارد: {cached}")
    with urllib.request.urlopen(url, timeout=120) as r:
        blob = r.read()
    cached.write_bytes(blob)
    return blob


def read_member(key: str, offline: bool) -> bytes:
    url, member = ARCHIVES[key]
    blob = fetch_archive(url, offline)
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tf:
        f = tf.extractfile(member)
        if f is None:
            raise SystemExit(f"فایل {member} در آرشیو نیست")
        return f.read()


# ---------------------------------------------------------------- universities
# فقط موسسات آموزش عالی دارای مدرک (مراکز رشد، واحدهای پژوهشی و مراکز علم و فناوری حذف می‌شوند)
MSRT_TYPE_MAP = {
    "دانشگاه - دولتی": "دولتی",
    "دانشگاه - وابسته": "وابسته",
    "دانشگاه آزاد اسلامی": "آزاد اسلامی",
    "دانشگاه پیام نور": "پیام نور",
    "دانشگاه فرهنگیان": "فرهنگیان",
    "دانشگاه فنی و حرفه ای": "فنی و حرفه‌ای",
    "دانشگاه جامع علمی کاربردی - دولتی": "جامع علمی‌کاربردی",
    "دانشگاه جامع علمی کاربردی - غیردولتی": "جامع علمی‌کاربردی",
    "دانشگاه جامع علمی کاربردی - وابسته": "جامع علمی‌کاربردی",
    "موسسات آموزش عالی غیر دولتی - غیر انتفاعی": "غیرانتفاعی",
    "دانشگاههای و موسسات آموزش عالی غیر دولتی-غیر انتفاعی مجازی": "مجازی",
}

MDABAGH_TYPE_MAP = [
    ("علمی-کاربردی", "جامع علمی‌کاربردی"),
    ("فنی و حرفه ای", "فنی و حرفه‌ای"),
    ("آزاد اسلامی", "آزاد اسلامی"),
    ("سما", "آزاد اسلامی"),
    ("پیام نور", "پیام نور"),
    ("غیرانتفاعی", "غیرانتفاعی"),
    ("وزارت بهداشت", "دولتی"),
    ("وزارت علوم", "دولتی"),
    ("دیگردولتی", "وابسته"),
    ("وزارت آموزش و پرورش", "وابسته"),
]

# گروه‌های مرتبط بر اساس نام دانشگاه (برای نمایش «دانشگاه‌های تخصصی هر گروه»)
UNI_FOCUS_RULES = [
    (("علوم پزشکی", "پزشکی", "دندانپزشکی", "داروسازی", "علوم دارویی", "توانبخشی"), ["تجربی"]),
    (("کشاورزی", "منابع طبیعی", "دامپزشکی", "شیلات"), ["تجربی"]),
    (("صنعتی", "فنی و مهندسی", "علم و صنعت", "خواجه نصیرالدین", "سهند"), ["ریاضی"]),
    (("هنر", "هنرهای زیبا", "هنرهای نمایشی", "هنرهای تجسمی"), ["هنر"]),
    (("زبان‌های خارجه", "زبانهای خارجه", "زبان های خارجه"), ["زبان"]),
    (("قرآن", "معارف", "امام صادق", "علوم اسلامی", "ادیان", "المصطفی", "حدیث"), ["معارف"]),
    (("علوم انتظامی", "امنیت"), ["انسانی"]),
]

KEY_STOPWORDS = {
    "دانشگاه", "موسسه", "آموزش", "عالی", "واحد", "پردیس", "دانشکده", "آموزشکده", "مرکز", "آزاد", "اسلامی",
    "پیام", "نور", "غیرانتفاعی", "غیردولتی", "غیر", "انتفاعی", "دولتی", "علمی", "کاربردی", "جامع", "آیت",
    "الله", "العظمی", "ا...", "ا", "و", "-", "مؤسسه",
}


def _has_phrase(name: str, phrase: str) -> bool:
    """تطبیق کامل واژه (نه زیررشته): «هنر» داخل «باهنر» نباشد."""
    return f" {phrase} " in f" {name} "


def uni_focus(name: str) -> list[str]:
    for keywords, groups in UNI_FOCUS_RULES:
        if any(_has_phrase(name, k) for k in keywords):
            return groups
    return []


def uni_key(name: str) -> str:
    """کلید یکتا برای حذف تکرارهای بین دو منبع (نام‌هایی که فقط در واژه‌های عمومی فرق دارند)."""
    s = fa(name).replace("ا...", " ").replace("مؤسسه", "موسسه")
    s = re.sub(r"[^\w\u0600-\u06FF]+", " ", s)
    tokens = [t for t in s.split() if t not in KEY_STOPWORDS]
    return "".join(tokens)  # بدون فاصله: «امیر کبیر» و «امیرکبیر» یکی‌اند


def build_universities(offline: bool) -> list[dict]:
    msrt_rows = list(csv.reader(io.StringIO(read_member("msrt", offline).decode("utf-8"))))[1:]
    city_province: Counter = Counter()
    records: dict[str, dict] = {}

    def add(name, utype, province, city, source):
        key = uni_key(name)
        if not key or key in records:
            return
        records[key] = {
            "name": name, "type": utype, "province": province, "city": city,
            "focus": uni_focus(name), "source": source,
        }

    for row in msrt_rows:
        if len(row) < 4:
            continue
        raw_type = fa(row[1])
        if raw_type not in MSRT_TYPE_MAP:
            continue
        name, province, city = fa(row[0]), fa(row[2]), fa(row[3])
        if province in PROVINCES:
            city_province[(city, province)] += 1
        add(name, MSRT_TYPE_MAP[raw_type], province if province in PROVINCES else "نامشخص", city, "msrt")

    city_to_prov: dict[str, str] = {}
    for (city, prov), _ in city_province.most_common():
        city_to_prov.setdefault(city, prov)

    for item in json.loads(read_member("mdabagh_univ", offline).decode("utf-8")):
        name = fa(item.get("University_name"))
        if uni_key(name) in records:
            continue
        mtype_raw = fa(item.get("University_type"))
        utype = next((v for k, v in MDABAGH_TYPE_MAP if k in mtype_raw), "سایر")
        city = fa(item.get("University_city"))
        state = fa(item.get("University_State"))
        province = state if state in PROVINCES else city_to_prov.get(city, "نامشخص")
        add(name, utype, province, city, "mdabagh")

    unis = sorted(records.values(), key=lambda u: (u["type"], u["province"], u["name"]))
    for i, u in enumerate(unis, 1):
        u["id"] = f"u{i:04d}"
    return unis


# ---------------------------------------------------------------- fields (رشته‌ها)
KEEP_DEGREES = {
    "کاردانی ناپیوسته": "کاردانی ناپیوسته",
    "کاردانی پیوسته": "کاردانی پیوسته",
    "کارشناسی ناپیوسته": "کارشناسی ناپیوسته",
    "کارشناسی پیوسته": "کارشناسی پیوسته",
    "دکتری عمومی": "دکتری عمومی (حرفه‌ای)",
}

ENG_KW = ["مهندسی", "مکانیک", "برق", "عمران", "کامپیوتر", "نرم افزار", "سخت افزار", "شبکه", "فناوری اطلاعات",
          "هوش مصنوعی", "الکترونیک", "مخابرات", "نقشه برداری", "معدن", "متالورژی", "مهندسی مواد", "پلیمر",
          "نفت", "گاز", "پتروشیمی", "هوافضا", "هوایی", "نساجی", "ساختمان", "راهسازی", "راه آهن", "سازه",
          "آبیاری", "مهندسی آب", "منابع آب", "انرژی", "ترافیک", "حمل و نقل", "تاسیسات", "تأسیسات", "جوشکاری",
          "تعمیر و نگهداری", "خودرو", "ماشین", "ریاضی", "فیزیک", "آمار", "کاردانی فنی", "اندازه شناسی", "رباتیک",
          "مهندس", "ابزار دقیق", "کشتی", "دریایی", "هوانوردی", "فناوری", "نانو", "مکانیزاسیون", "نقشه", "پدافند",
          "صنایع شیمیایی", "مهندسی صنایع", "صنایع چوب", "صنایع نفت", "صنایع الکترونیک", "صنایع فلزی",
          "صنایع کاغذ", "صنایع نساجی", "صنایع فرآورده", "صنایع اوراق", "ژئو", "ایمنی پرواز"]
BIO_KW = ["پزشک", "دندان", "داروساز", "دارو", "پرستار", "مامای", "بهداشت", "تغذیه", "آزمایشگاه", "فیزیوتراپی",
          "رادیولوژی", "اتاق عمل", "هوشبری", "سلامت", "ژنتیک", "زیست", "میکروب", "دامپزشک", "دامی", "دامپروری",
          "کشاورز", "گیاه", "باغبانی", "جنگلداری", "منابع طبیعی", "محیط زیست", "شیلات", "بیوشیمی", "بیولوژی",
          "پیراپزشک", "بینایی", "شنوایی", "زمین شناسی", "اکولوژی", "آبزی", "پرورش ماهی", "توانبخشی", "زراعی", "باغی", "تولیدات گیاهی", "جانوری", "بیوتکنولوژی", "بیوانفورماتیک",
          "تشریح", "علوم اعصاب", "طب ", "علوم تجربی"]
ART_KW = ["هنر", "نقاشی", "گرافیک", "موسیقی", "سینما", "عکاسی", "فیلم", "تئاتر", "بازیگری", "هنرهای نمایشی", "انیمیشن",
          "طراحی", "صنایع دستی", "مجسمه", "سفال", "فرش", "خوشنویسی", "تصویرسازی", "تلویزیون", "سرامیک",
          "معماری", "شهرسازی", "عکس", "فتوگرافیک", "ترسیم", "کاشی", "مینیاتور", "تذهیب", "آهنگسازی",
          "نوازندگی", "خوانندگی"]
LANG_KW = ["زبان انگلیسی", "زبان های خارجی", "زبان‌های خارجی", "زبان های خارجه", "مترجمی", "ترجمه", "زبان فرانسه",
           "زبان آلمانی", "زبان روسی", "زبان اسپانیایی", "زبان ترکی", "زبان ژاپنی", "زبان عربی", "زبان اشاره",
           "زبان و ادبیات انگلیسی", "زبان و ادبیات عربی", "زبان و ادبیات فرانسه", "زبان و ادبیات آلمانی",
           "زبان و ادبیات روسی", "آموزش زبان", "زبان شناسی", "زبان‌شناسی", "انگلیسی", "فرانسه", "آلمانی", "روسی",
           "اسپانیایی", "ترکی", "ژاپنی", "چینی", "ایتالیایی"]
MAARF_KW = ["معارف", "الهیات", "فقه", "قرآن", "حدیث", "تفسیر", "کلام", "ادیان", "علوم اسلامی", "مطالعات اسلامی",
            "احکام", "تاریخ اسلام", "مذاهب", "تشیع"]
HUM_KW = ["حقوق", "مدیریت", "حسابداری", "حسابرسی", "اقتصاد", "بازرگانی", "بیمه", "بانک", "مالی", "گردشگری",
          "جامعه شناسی", "جامعه‌شناسی", "علوم اجتماعی", "روانشناسی", "روان شناسی", "روان‌شناسی", "علوم سیاسی",
          "مشاوره", "تاریخ", "جغرافیا", "فلسفه", "منطق", "ادبیات", "علوم تربیتی", "ارتباطات", "روزنامه",
          "رسانه", "کتابداری", "اطلاع رسانی", "بازاریابی", "تعاون", "تجارت", "قضایی", "امنیت", "انتظامی",
          "ثبت", "کارگزاری", "گمرک", "علوم اداری", "کسب و کار", "مددکاری", "ورزش", "تربیت بدنی"]

MEDICAL_FIELDS = [
    ("پزشکی", "دکتری عمومی (حرفه‌ای)"),
    ("دندانپزشکی", "دکتری عمومی (حرفه‌ای)"),
    ("داروسازی", "دکتری عمومی (حرفه‌ای)"),
    ("پرستاری", "کارشناسی پیوسته"),
    ("مامایی", "کارشناسی پیوسته"),
    ("علوم آزمایشگاهی", "کارشناسی پیوسته"),
    ("علوم تغذیه", "کارشناسی پیوسته"),
    ("بهداشت عمومی", "کارشناسی پیوسته"),
    ("فیزیوتراپی", "کارشناسی پیوسته"),
    ("رادیولوژی", "کارشناسی پیوسته"),
    ("هوشبری", "کارشناسی پیوسته"),
    ("بینایی‌سنجی", "کارشناسی پیوسته"),
    ("شنوایی‌سنجی", "کارشناسی ناپیوسته"),
    ("فناوری اتاق عمل", "کارشناسی ناپیوسته"),
    ("فوریت‌های پزشکی", "کارشناسی ناپیوسته"),
    ("مدیریت خدمات بهداشتی و درمانی", "کارشناسی ناپیوسته"),
]

FALLBACK_BY_CATEGORY = {
    "علوم انسانی": ["انسانی"], "علوم اجتماعی": ["انسانی"], "فنی و مهندسی": ["ریاضی"],
    "علوم پایه": ["ریاضی"], "کشاورزی": ["تجربی"], "دامپزشکی": ["تجربی"], "هنر و معماری": ["هنر"],
    "فنی و حرفه ای": ["ریاضی"], "علمی و کاربردی": ["انسانی"], "علوم پزشکی": ["تجربی"],
}


def map_groups(name: str, category: str) -> list[str]:
    """نگاشت تقریبی هر رشته به یک یا چند گروه آزمایشی (قاعده‌محور)."""
    groups: list[str] = []

    def add(g: str) -> None:
        if g not in groups:
            groups.append(g)

    is_art = any(k in name for k in ART_KW)
    is_maarf = any(k in name for k in MAARF_KW)
    is_lang = any(k in name for k in LANG_KW)
    is_bio = any(k in name for k in BIO_KW)
    is_eng = any(k in name for k in ENG_KW)
    is_hum = any(k in name for k in HUM_KW)

    if "صنایع دستی" in name:
        is_eng = False
    if "حقوق اسلامی" in name or "فقه و حقوق" in name:
        add("معارف")
        is_hum = True
    if is_art:
        add("هنر")
    if ("معماری" in name or "شهرسازی" in name or "طراحی صنعتی" in name) and "هنر" not in name:
        add("ریاضی")
    if is_maarf:
        add("معارف")
    if is_lang and not name.startswith("زبان و ادبیات فارسی"):
        add("زبان")
    if is_bio:
        add("تجربی")
    if "شیمی" in name and "صنعتی" not in name:
        add("تجربی")
    if (is_eng or "شیمی" in name or "فیزیک" in name or "ریاضی" in name or "آمار" in name) and not (is_art and not is_eng):
        add("ریاضی")
    if is_hum:
        add("انسانی")
    if "مدیریت" in name and "سلامت" in name:
        add("تجربی")
    if groups:
        return groups
    return list(FALLBACK_BY_CATEGORY.get(category, ["انسانی"]))


def strip_group_suffix(name: str) -> str:
    base = re.split(r"\s+(?:گرایش|با گرایش)\s*[:：]?\s*", name)[0]
    return base.strip(" -،,:")


def build_fields(offline: bool) -> list[dict]:
    raw = json.loads(read_member("mdabagh_fields", offline).decode("utf-8"))
    merged: dict[str, dict] = {}
    for item in raw:
        deg = KEEP_DEGREES.get(fa(item.get("degree")))
        if not deg:
            continue
        name = strip_group_suffix(fa(item.get("academic_discipline_name")))
        if len(name) < 2:
            continue
        rec = merged.setdefault(name, {"category": fa(item.get("academic_discipline_type")), "degrees": set(),
                                       "source": "mdabagh"})
        rec["degrees"].add(deg)

    for name, label in MEDICAL_FIELDS:
        rec = merged.setdefault(name, {"category": "علوم پزشکی", "degrees": set(), "source": "manual"})
        rec["degrees"].add(label)
        rec["category"] = "علوم پزشکی"
        rec["source"] = "manual"

    out = []
    for name, rec in merged.items():
        out.append({
            "name": name,
            "category": rec["category"],
            "degrees": sorted(rec["degrees"], key=lambda d: ("کاردانی" not in d, d)),
            "groups": map_groups(name, rec["category"]),
            "source": rec["source"],
        })
    out.sort(key=lambda f: (f["groups"][0], f["name"]))
    for i, f in enumerate(out, 1):
        f["id"] = f"f{i:04d}"
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="فقط از کش scripts/.cache استفاده کن")
    args = ap.parse_args()

    unis = build_universities(args.offline)
    fields = build_fields(args.offline)
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "universities.json").write_text(json.dumps(unis, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA / "fields.json").write_text(json.dumps(fields, ensure_ascii=False, indent=1), encoding="utf-8")

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "universities_total": len(unis),
        "universities_by_type": dict(Counter(u["type"] for u in unis).most_common()),
        "fields_total": len(fields),
        "fields_by_group": dict(Counter(g for f in fields for g in f["groups"]).most_common()),
        "fields_by_source": dict(Counter(f["source"] for f in fields)),
        "sources": [
            "https://github.com/farhadmpr/List-of-universities (داده‌ی فهرست موسسات وزارت علوم، msrt.ir)",
            "https://github.com/mdabagh/List-of-universities-and-academic-fields-in-Iran",
        ],
    }
    (DATA / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
