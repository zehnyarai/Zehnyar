# -*- coding: utf-8 -*-
"""Precise design metadata for the ten per-verse extended fields.

Each field definition gains an explicit research question, an acceptance rule
(what makes an entry admissible), a rejection rule (what must not be stored),
the evidence keys every entry must carry, and the entry threshold for the
`core` and `full` tiers.  The app renders this design above each field so a
reader can see what the field claims to answer.
"""
from __future__ import annotations

import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "static" / "verse-dossier-extended-fields.json"
DATA = json.loads(PATH.read_text(encoding="utf-8"))

DESIGN = {
    "bibleComparison": {
        "question": "آیا در نسخهٔ مشخصی از کتاب مقدس، موضعی هم‌سو یا متقابل با مفادِ این آیه هست و شباهت و تفاوت کجاست؟",
        "acceptance": ("ارجاع به ترجمه و شمارهٔ باب و آیه، بیانِ شباهتِ ساختاری، تصریحِ تفاوتِ الهیاتی و اعلامِ "
                       "حدِ مقایسه (از جمله مقابله‌نشدن با متنِ اصلی یا نبودِ پژوهشِ تطبیقی)."),
        "rejection": "ادعای وام‌گیری یا وابستگیِ متنی بدون شاهدِ تاریخی، و مقایسهٔ کلیِ ادیان بدون ارجاعِ دقیق.",
    },
    "guidanceDiscourse": {
        "question": "این آیه چه کنشِ گفتاری و چه کارکردِ هدایتی در سیاقِ خود دارد و مخاطبش کیست؟",
        "acceptance": ("تعیینِ گوینده و مخاطب، نشانگرِ زبانیِ کنش (امر، نهی، خبر، شرط، استفهام) و پیوندِ آیه با "
                       "آیهٔ پیش و پس در همان واحدِ سیاق."),
        "rejection": "موعظهٔ عام، تعمیمِ اخلاقیِ بی‌شاهد و تکرارِ ترجمه در لباسِ تحلیل.",
    },
    "shubuhat": {
        "question": "کدام شبههٔ رایج یا خوانشِ رقیب بر این آیه وارد می‌شود و پاسخِ منبع‌دار چیست؟",
        "acceptance": ("صورت‌بندیِ دقیقِ شبهه، پاسخ بر پایهٔ متن یا منبعِ نام‌برده، و اعلامِ آنچه این پاسخ حل "
                       "نمی‌کند."),
        "rejection": "پاسخِ جدلیِ بدون ارجاع، نادیده‌گرفتنِ قرینه‌های درون‌متنی و ادعای حلِ کاملِ بحث.",
    },
    "modernSciences": {
        "question": "کدام یافتهٔ پژوهشیِ معاصر (روان‌شناسی، جامعه‌شناسی، اقتصاد، مطالعاتِ ناتوانی) با مفادِ آیه قابلِ سنجش است؟",
        "acceptance": ("ارجاعِ کتاب‌شناختیِ دقیق به اثرِ پژوهشی، بیانِ سازوکارِ قابلِ مقایسه با مفادِ آیه، و "
                       "تصریحِ اینکه آن پژوهش ارزش‌داوریِ دینی تولید نمی‌کند."),
        "rejection": "اعجازِ علمی، تطبیقِ نظریه‌های نو با متن بدون تفکیکِ توصیف از هنجار، و ارجاعِ کلی به «علم».",
    },
    "qiraat": {
        "question": "آیا در این آیه اختلافِ قرائت هست؛ کدام قاریان، با چه اثری بر معنا، و کدام ترجیح گزارش شده است؟",
        "acceptance": ("نامِ قاری یا راوی، وجه اعرابی یا صرفی، اثرِ معنایی، و در صورت وجود، شاهدِ شعری یا داوریِ "
                       "یک نحوی یا مفسر؛ اگر اختلافی یافت نشد، یادداشتِ کمبود ثبت شود و نه ادعای اجماع."),
        "rejection": "نسبت‌دادنِ قرائت به قاری بدون منبعِ قرائات، و نتیجه‌گیریِ معنایی از قرائتی که مقابله نشده است.",
    },
    "philosophicalFoundations": {
        "question": "آیه بر چه مفروضِ فلسفی در بابِ تکلیف، ارزش، عدالت یا فاعلیت استوار است؟",
        "acceptance": ("نام‌بردنِ چارچوبِ فلسفی، نشان‌دادنِ جایگاهِ آن در متن، و اعلامِ اینکه چارچوب حکمِ شرعی "
                       "تولید نمی‌کند."),
        "rejection": "تحمیلِ یک نظامِ فلسفیِ کامل بر آیه و خواندنِ اصطلاحاتِ مدرن به‌جای متن.",
    },
    "linguistics": {
        "question": "کدام نکتهٔ صرفی، نحوی یا معناشناختی با شاهدِ عربیِ درون‌متنی یا منبعِ لغوی روشن می‌شود؟",
        "acceptance": ("شاهدِ عربیِ دقیق (واژه، ساخت، اعراب)، ارجاعِ لغوی یا نحوی و بیانِ اثرِ آن بر فهمِ آیه."),
        "rejection": "تحلیلِ ذوقیِ بدون شاهد، و استنتاجِ حکمِ شرعی از یک نکتهٔ لغوی.",
    },
    "criticalDiscourseAnalysis": {
        "question": "آیه چه کنشگران، جایگاه‌ها و روابطِ قدرت را بازنمایی می‌کند و با چه روشِ تحلیلی؟",
        "acceptance": ("روشِ نام‌برده (برای نمونه فرکلاف یا گافمن)، شاهدِ متنی، و تفکیکِ توصیف از داوریِ ارزشی."),
        "rejection": "برچسبِ ایدئولوژیک بدون شاهد و اثباتِ انگیزهٔ تاریخیِ افراد از خودِ متن.",
    },
    "historicalContext": {
        "question": "کدام گزارشِ تاریخی یا سببِ نزول، با چه درجهٔ وثاقت، زمینهٔ فهمِ آیه را فراهم می‌کند؟",
        "acceptance": ("منبعِ کهنِ نام‌برده، سند یا ارجاعِ دقیق، و اعلامِ اختلافِ گزارش‌ها و مرزِ بازسازی."),
        "rejection": "بازسازیِ حدسی، تعمیمِ یک گزارش به حکمِ کلی، و تاریخ‌گذاریِ قاطع بدون سند.",
    },
    "balaghaNazm": {
        "question": "ساختِ بلاغی و نظمِ آیه (چیدمان، تقابل، حصر، ختام) چه اثری بر معنا دارد؟",
        "acceptance": ("نشان‌دادنِ سازهٔ مشخص در متن، بیانِ اثرِ آن بر معنا و مرزِ استنباط."),
        "rejection": "توصیفِ زیبایی‌شناختیِ بی‌شاهد و ادعای اعجاز بدونِ تحلیلِ سازه‌ها.",
    },
}

fields = DATA["fields"]
assert len(fields) == 10 and {f["id"] for f in fields} == set(DESIGN), "field ids drifted"
for field in fields:
    design = DESIGN[field["id"]]
    field["question"] = design["question"]
    field["acceptance"] = design["acceptance"]
    field["rejection"] = design["rejection"]
    field["evidenceKeys"] = ["text", "cite", "evidence", "limit"]
    field["allowedKinds"] = ["analysis", "source-coverage-note"]
    field["minEntries"] = {"core": 1, "full": 5}

DATA["criteria"]["extendedFieldStandard"] = {
    "designVersion": 2,
    "note": (
        "هر یک از ده فیلدِ ذیلِ آیه یک پرسشِ پژوهشیِ صریح، قاعدهٔ پذیرشِ مدخل و قاعدهٔ رد دارد. مدخلِ پذیرفته "
        "باید متن، ارجاع، شاهد و حدِ استنباط را با هم داشته باشد؛ یادداشتِ کمبود جای مدخلِ پژوهشی را نمی‌گیرد و "
        "ادعای پوششِ کامل تنها با رسیدن به آستانهٔ هر سطح سنجیده می‌شود."),
    "requiredEntryKeys": ["text", "cite", "evidence", "limit"],
    "kindDefinitions": {
        "analysis": "مدخلِ پژوهشیِ دارای متن، ارجاع، شاهد و حدِ استنباط.",
        "source-coverage-note": "یادداشتِ صریحِ کمبودِ پوشش؛ تنها وقتی ثبت می‌شود که مقابله انجام شده و داده‌ای نیامده است.",
    },
    "tierThresholds": {"core": 1, "full": 5},
}

PATH.write_text(json.dumps(DATA, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("fields designed:", len(fields))
for field in fields:
    print(field["id"], "|", field["question"][:60])
