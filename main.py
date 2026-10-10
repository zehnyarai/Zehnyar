"""Zehnyar — transparent, evidence-first thematic exploration of the Qur'an.

The application deliberately separates lexical retrieval from heuristic thematic links.
It does not generate fatwas or present an automated summary as a substitute for tafsir.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

ARABIC_MARKS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u08d4-\u08ff]")
PUNCTUATION = re.compile(r"[^\w\s\u0600-\u06ff]")
WHITESPACE = re.compile(r"\s+")


def normalize(value: str) -> str:
    """Normalize Arabic/Persian text for retrieval while retaining display text unchanged."""
    value = ARABIC_MARKS.sub("", value or "")
    value = value.translate(
        str.maketrans(
            {
                "ٱ": "ا",
                "أ": "ا",
                "إ": "ا",
                "آ": "ا",
                "ى": "ی",
                "ي": "ی",
                "ئ": "ی",
                "ؤ": "و",
                "ك": "ک",
                "ة": "ه",
                "ـ": "",
                "‌": " ",
            }
        )
    )
    value = PUNCTUATION.sub(" ", value.lower())
    return WHITESPACE.sub(" ", value).strip()


# The vocabulary is intentionally small, reviewable, and shown to the user in the UI.
# It makes semantic expansion auditable rather than hiding an opaque embedding model.
TOPICS: dict[str, dict[str, Any]] = {
    "عدالت": {
        "aliases": ["عدالت", "عدل", "قسط", "انصاف", "میزان", "دادگری"],
        "terms": [
            ("عدل", "عدالت / توازن"),
            ("قسط", "دادگری"),
            ("میزان", "سنجش و تراز"),
            ("بالقسط", "به دادگری"),
            ("شهداء بالقسط", "گواهان به قسط"),
            ("عدالت", "ترجمهٔ عدالت"),
            ("انصاف", "ترجمهٔ انصاف"),
            ("دادگری", "ترجمهٔ دادگری"),
        ],
        "description": "عدالت در این نقشه با واژگان قسط، عدل و میزان دنبال می‌شود؛ دامنهٔ آن در هر آیه باید با سیاق همان آیه خوانده شود.",
        "questions": ["مخاطبِ فرمان به قسط در این آیه کیست؟", "آیا آیه ناظر به داوری، شهادت، اقتصاد یا رفتار فردی است؟"],
    },
    "رحمت": {
        "aliases": ["رحمت", "مهربانی", "بخشش", "آمرزش", "رأفت", "مغفرت"],
        "terms": [
            ("رحم", "رحمت"),
            ("رحمن", "بخشندگی فراگیر"),
            ("رحیم", "مهربانی"),
            ("رأف", "رأفت"),
            ("غفر", "آمرزش"),
            ("رحمت", "ترجمهٔ رحمت"),
            ("آمرزش", "ترجمهٔ آمرزش"),
            ("مهربان", "ترجمهٔ مهربانی"),
        ],
        "description": "این خوشه میان رحمت، رأفت و مغفرت تفاوت می‌گذارد و آن‌ها را به‌عنوان هم‌معناهای مطلق تلقی نمی‌کند.",
        "questions": ["رحمت در این آیه صفت الهی است یا دستور اخلاقی؟", "رابطهٔ رحمت با توبه، عمل یا هدایت در سیاق چیست؟"],
    },
    "علم": {
        "aliases": ["علم", "دانش", "آگاهی", "تعلیم", "تفکر", "اندیشه", "عقل", "یادگیری"],
        "terms": [
            ("علم", "دانش"),
            ("یعلم", "دانستن"),
            ("تعلم", "آموختن"),
            ("عقل", "خردورزی"),
            ("یتفکر", "اندیشیدن"),
            ("تدبر", "تدبر"),
            ("دانش", "ترجمهٔ دانش"),
            ("آگاه", "ترجمهٔ آگاهی"),
            ("بیندیش", "ترجمهٔ اندیشیدن"),
        ],
        "description": "در این مسیر، علم، تعقل و تفکر با برچسب‌های جدا بازیابی می‌شوند تا تفاوت نقش معرفتی آن‌ها پنهان نشود.",
        "questions": ["فاعلِ دانستن یا اندیشیدن در آیه کیست؟", "آیا سخن از دانایی الهی، تجربه، نشانه‌ها یا مسئولیت معرفتی است؟"],
    },
    "خانواده": {
        "aliases": ["خانواده", "ازدواج", "همسر", "والدین", "پدر", "مادر", "فرزند", "طلاق"],
        "terms": [
            ("زوج", "همسران"),
            ("نساء", "زنان"),
            ("والد", "والدین"),
            ("امهات", "مادران"),
            ("اباء", "پدران"),
            ("ابن", "فرزندان"),
            ("ذری", "ذریه"),
            ("نکاح", "ازدواج"),
            ("طلاق", "طلاق"),
            ("خانواده", "ترجمهٔ خانواده"),
            ("همسر", "ترجمهٔ همسر"),
            ("والدین", "ترجمهٔ والدین"),
            ("مادر", "ترجمهٔ مادر"),
            ("فرزند", "ترجمهٔ فرزند"),
        ],
        "description": "«خانواده» واژه‌ای پوششی است؛ نتایج بر پایهٔ نقش‌های خویشاوندی و احکام مربوط بازیابی و از هم تفکیک می‌شوند.",
        "questions": ["آیه دربارهٔ حق، مسئولیت یا توصیف یک رابطه سخن می‌گوید؟", "آیا قیدها و استثناهای آیه در نتیجه لحاظ شده‌اند؟"],
    },
    "صبر": {
        "aliases": ["صبر", "پایداری", "استقامت", "شکیبایی", "بردباری"],
        "terms": [
            ("صبر", "شکیبایی"),
            ("صابر", "صبرکنندگان"),
            ("اصبر", "فرمان به صبر"),
            ("استعینوا بالصبر", "یاری‌جستن از صبر"),
            ("صبر", "ترجمهٔ صبر"),
            ("شکیبا", "ترجمهٔ شکیبایی"),
            ("پایداری", "ترجمهٔ پایداری"),
        ],
        "description": "صبر با موقعیت‌های آزمون، عبادت و پایداری بررسی می‌شود؛ صرفِ هم‌جواری، هم‌معنایی قطعی نیست.",
        "questions": ["صبر در این آیه در برابر چه وضعیتی آمده است؟", "آیا آیه وعده، فرمان یا توصیف یک گروه را بیان می‌کند؟"],
    },
    "توبه": {
        "aliases": ["توبه", "بازگشت", "پشیمانی", "بخشش گناه", "استغفار"],
        "terms": [
            ("توب", "توبه"),
            ("استغفر", "آمرزش‌خواهی"),
            ("غفور", "بسیار آمرزنده"),
            ("غفار", "آمرزنده"),
            ("تابوا", "بازگشتند"),
            ("توبه", "ترجمهٔ توبه"),
            ("آمرزش", "ترجمهٔ آمرزش"),
            ("استغفار", "ترجمهٔ استغفار"),
        ],
        "description": "توبه، استغفار و مغفرت در نتایج با نسبت‌شان به متن نشان داده می‌شوند، نه به‌عنوان مراحل قطعی یک الگو.",
        "questions": ["آیا آیه شرط یا نشانه‌ای برای توبه مطرح می‌کند؟", "مخاطب و زمانِ بازگشت در سیاق آیه چیست؟"],
    },
    "انفاق": {
        "aliases": ["انفاق", "صدقه", "بخشش مالی", "زکات", "کمک", "بخشندگی"],
        "terms": [
            ("انفق", "انفاق"),
            ("زک", "زکات / پاکی"),
            ("صدقات", "صدقه"),
            ("اطعم", "خوراک‌دادن"),
            ("مال", "مال"),
            ("انفاق", "ترجمهٔ انفاق"),
            ("زکات", "ترجمهٔ زکات"),
            ("صدقه", "ترجمهٔ صدقه"),
        ],
        "description": "این خوشه میان انفاق، زکات، صدقه و اطعام تمایز می‌گذارد و نتایج را با واژهٔ شاهد نمایش می‌دهد.",
        "questions": ["موضوعِ بخشش در آیه چیست و مخاطب آن کیست؟", "آیا آیه قید نیت، زمان یا شیوهٔ پرداخت دارد؟"],
    },
    "آزادی و اختیار": {
        "aliases": ["آزادی", "اختیار", "اجبار", "انتخاب", "اراده", "مسئولیت"],
        "terms": [
            ("اکراه", "اجبار"),
            ("شاء", "خواستن"),
            ("اختار", "برگزیدن"),
            ("کسب", "کسب و مسئولیت"),
            ("اراده", "ترجمهٔ اراده"),
            ("اجبار", "ترجمهٔ اجبار"),
            ("اختیار", "ترجمهٔ اختیار"),
            ("انتخاب", "ترجمهٔ انتخاب"),
        ],
        "description": "این موضوعِ پیچیده با واژه‌های نزدیک بازیابی می‌شود؛ نسبت ارادهٔ الهی و کنش انسانی نیازمند مطالعهٔ تفسیری جداگانه است.",
        "questions": ["فاعلِ خواستن یا انتخاب در آیه کیست؟", "آیا آیه در مقام گزارش، دعوت یا داوری اخلاقی است؟"],
    },
}
# These categories are a navigation aid, not a taxonomy imposed on the Qur'an.
# Each suggested topic remains a transparent lexical query that users can inspect.
TOPICS.update(
    {
        "توحید": {
            "aliases": ["توحید", "یکتاپرستی", "خداپرستی", "شرک", "یکتایی"],
            "terms": [("لا اله", "نفیِ معبودِ دیگر"), ("اله واحد", "معبودِ یگانه"), ("شریک", "شریک‌گرفتن"), ("یکتا", "ترجمهٔ یکتایی"), ("یگانه", "ترجمهٔ یگانگی")],
            "description": "این خوشه با عبارت‌ها و واژه‌های شاهدِ محدود به یکتایی و شریک‌گرفتن وارد متن می‌شود؛ برای پرهیز از فراگیریِ بی‌دلیل، واژهٔ «الله» به‌تنهایی در آن نیست.",
            "questions": ["آیه در مقام نفی، اثبات، استدلال یا دعوت است؟", "مرزِ مفهومیِ واژهٔ شاهد با سیاقِ آیه چیست؟"],
        },
        "وحی و رسالت": {
            "aliases": ["وحی", "رسالت", "پیامبر", "رسول", "نبوت", "نبی"],
            "terms": [("وحی", "وحی"), ("رسول", "فرستاده"), ("نبی", "پیامبر"), ("کتاب", "کتاب"), ("پیامبر", "ترجمهٔ پیامبر"), ("رسالت", "ترجمهٔ رسالت")],
            "description": "وحی، رسالت، نبوت و کتاب در آیات یک نقش یگانه ندارند؛ این جست‌وجو باید با تعیین گوینده، مخاطب و موضوع دنبال شود.",
            "questions": ["در آیه چه کسی مخاطب یا حامل پیام است؟", "آیا آیه دربارهٔ دریافت، ابلاغ، واکنش یا مسئولیت پیام سخن می‌گوید؟"],
        },
        "هدایت": {
            "aliases": ["هدایت", "راهنمایی", "گمراهی", "راه راست", "رشد"],
            "terms": [("هدی", "هدایت"), ("اهدنا", "درخواست هدایت"), ("ضلال", "گمراهی"), ("رشد", "رشد"), ("هدایت", "ترجمهٔ هدایت"), ("گمراه", "ترجمهٔ گمراهی")],
            "description": "هدایت و گمراهی با واژه‌های شاهد جداگانه بازیابی می‌شوند؛ نسبت آن‌ها با اختیار و عمل باید در سیاق خوانده شود.",
            "questions": ["هدایت در این آیه وصف، درخواست یا فرمان است؟", "مخاطب و نشانهٔ راه‌یافتگی در بافت چیست؟"],
        },
        "تقوا": {
            "aliases": ["تقوا", "پرهیزگاری", "پرهیز", "خویشتن‌داری", "متقین"],
            "terms": [("تقوی", "تقوا"), ("اتق", "فرمان به تقوا"), ("متق", "پرهیزگاران"), ("تقوا", "ترجمهٔ تقوا"), ("پرهیزگار", "ترجمهٔ پرهیزگاری")],
            "description": "تقوا در این جست‌وجو یک برچسب اخلاقیِ کلی تلقی نمی‌شود؛ واژهٔ شاهد و کارکرد آن در آیه باید جدا بررسی شود.",
            "questions": ["تقوا در این آیه با چه کنش یا پیامدی همراه است؟", "آیا آیه تعریف، فرمان یا توصیفِ گروهی را بیان می‌کند؟"],
        },
        "ایمان": {
            "aliases": ["ایمان", "باور", "مؤمن", "کفر", "نفاق"],
            "terms": [("ایمان", "ایمان"), ("مومن", "مؤمنان"), ("کفر", "کفر"), ("نفاق", "نفاق"), ("باور", "ترجمهٔ باور")],
            "description": "ایمان، کفر و نفاق هم‌معنا نیستند؛ این خوشه فقط مسیر ورود به آیات را فراهم می‌کند، نه تعریف نهایی مفاهیم.",
            "questions": ["ایمان در آیه با کدام قول، عمل یا گروه پیوند دارد؟", "آیا آیه توصیف، دعوت یا هشدار است؟"],
        },
        "آخرت": {
            "aliases": ["آخرت", "قیامت", "رستاخیز", "حساب", "معاد", "روز جزا"],
            "terms": [("الاخره", "آخرت"), ("یوم الدین", "روز جزا"), ("بعث", "برانگیخته‌شدن"), ("حساب", "حساب"), ("قیامت", "ترجمهٔ قیامت"), ("رستاخیز", "ترجمهٔ رستاخیز")],
            "description": "این خوشه میان آخرت، حساب و برانگیخته‌شدن تمایز می‌گذارد و نیازمند مطالعهٔ تصویر آیه و سیاق سوره است.",
            "questions": ["آیه کدام بُعد از آخرت را طرح می‌کند؟", "رابطهٔ این تصویر با مسئولیت و عمل در آیه چیست؟"],
        },
        "شکر": {
            "aliases": ["شکر", "سپاس", "سپاسگزاری", "نعمت"],
            "terms": [("شکر", "شکر"), ("شاکر", "سپاسگزاران"), ("شکور", "بسیار سپاسگزار"), ("سپاس", "ترجمهٔ سپاس"), ("نعمت", "ترجمهٔ نعمت")],
            "description": "شکر و نعمت با واژه‌های جدا بازمی‌گردند تا نسبت آن‌ها از دلِ آیه بررسی شود.",
            "questions": ["موضوعِ سپاس یا نعمت در آیه چیست؟", "آیا آیه از پاسخ انسانی، صفت الهی یا پیامد عمل می‌گوید؟"],
        },
        "امانت و عهد": {
            "aliases": ["امانت", "عهد", "پیمان", "وفا", "تعهد"],
            "terms": [("امانات", "امانت‌ها"), ("امانه", "امانت"), ("عهد", "عهد"), ("وفا", "وفاداری"), ("پیمان", "ترجمهٔ پیمان"), ("امانت", "ترجمهٔ امانت")],
            "description": "امانت، عهد و وفا در این خروجی از هم جدا برچسب می‌خورند؛ تعیین قلمرو حقوقی آن‌ها به مطالعهٔ تخصصی نیاز دارد.",
            "questions": ["مخاطبِ عهد یا امانت در آیه کیست؟", "آیا آیه قید، استثنا یا پیامدی را بیان می‌کند؟"],
        },
        "دعاء و عبادت": {
            "aliases": ["دعا", "دعاء", "عبادت", "نماز", "ذکر", "نیایش"],
            "terms": [("دعاء", "دعا"), ("ادع", "فراخواندن / دعا"), ("صلوة", "نماز"), ("ذکر", "یادکرد"), ("عبادت", "ترجمهٔ عبادت"), ("نماز", "ترجمهٔ نماز")],
            "description": "دعا، نماز و ذکر در این خوشه یکسان گرفته نمی‌شوند و هر کدام با واژهٔ شاهد خود نشان داده می‌شوند.",
            "questions": ["سخن از خطاب به خدا، ذکر، یا عمل عبادی است؟", "زمان، مخاطب و قیدِ این عمل در سیاق چیست؟"],
        },
        "اصلاح و صلح": {
            "aliases": ["اصلاح", "صلح", "آشتی", "فساد", "سازش"],
            "terms": [("اصلح", "اصلاح"), ("اصلاح", "اصلاح"), ("صلح", "صلح"), ("فساد", "فساد"), ("آشتی", "ترجمهٔ آشتی")],
            "description": "اصلاح و صلح با فساد در یک خوشهٔ مقایسه‌ای بازیابی می‌شوند، اما دایرهٔ اجتماعی یا فردی هر مورد از متن تعیین می‌شود.",
            "questions": ["اصلاح در آیه ناظر به چه رابطه یا وضعیتی است؟", "آیا آیه راهِ حل، هشدار یا توصیفِ پیامد را بیان می‌کند؟"],
        },
        "نشانه‌ها و آفرینش": {
            "aliases": ["نشانه", "آفرینش", "خلقت", "آسمان", "زمین", "طبیعت"],
            "terms": [("ایات", "نشانه‌ها"), ("خلق", "آفرینش"), ("سماوات", "آسمان‌ها"), ("ارض", "زمین"), ("نشانه", "ترجمهٔ نشانه"), ("آفرینش", "ترجمهٔ آفرینش")],
            "description": "این موضوع گسترده است؛ آسمان، زمین و آفرینش لزوماً یک استدلال واحد را نشان نمی‌دهند و باید در سیاق آیه خوانده شوند.",
            "questions": ["نشانه در آیه به مشاهده، استدلال یا یادآوری چه چیزی دعوت می‌کند؟", "مخاطب و نوع خطاب در این بخش چیست؟"],
        },
        "داستان و عبرت": {
            "aliases": ["داستان", "قصه", "عبرت", "مثل", "سرگذشت"],
            "terms": [("قصص", "داستان‌ها"), ("عبره", "عبرت"), ("مثل", "مَثَل"), ("نبا", "خبر / روایت"), ("داستان", "ترجمهٔ داستان")],
            "description": "داستان، مَثَل و عبرت شیوه‌های بیانی متفاوت‌اند؛ این خوشه فقط آیات ورودی را بازمی‌یابد.",
            "questions": ["این بخش روایت، مَثَل یا نتیجه‌گیری از یک روایت است؟", "پیوند بخش با آیات پیش و پس از خود چیست؟"],
        },
    }
)

TOPIC_CATEGORIES = [
    {"id": "worldview", "title": "جهان‌بینی و جهت‌گیری", "description": "مفاهیم بنیادین دربارهٔ توحید، وحی، هدایت، باور، مسئولیت و فرجام.", "topics": ["توحید", "وحی و رسالت", "هدایت", "ایمان", "تقوا", "آخرت", "آزادی و اختیار"]},
    {"id": "ethics", "title": "اخلاق و خودسازی", "description": "مسیرهای واژگانیِ صبر، توبه، شکر، رحمت و امانت.", "topics": ["رحمت", "صبر", "توبه", "شکر", "امانت و عهد"]},
    {"id": "society", "title": "زندگی اجتماعی و مسئولیت", "description": "ورودی‌های پژوهش دربارهٔ عدالت، خانواده، بخشش و اصلاح.", "topics": ["عدالت", "خانواده", "انفاق", "اصلاح و صلح"]},
    {"id": "knowledge", "title": "معرفت، نشانه و روایت", "description": "برای پیگیری علم، آفرینش، استدلال و شیوه‌های بیانی قرآن.", "topics": ["علم", "نشانه‌ها و آفرینش", "داستان و عبرت", "دعاء و عبادت"]},
]

READING_PROTOCOL = [
    {"id": "text", "title": "متن، ترجمه و واژهٔ شاهد", "description": "پیش از برداشت، ببینید تطابق در عربی است یا ترجمه و کدام واژه آیه را وارد نتیجه کرده است.", "availability": "فعال در ذهن‌یار"},
    {"id": "context", "title": "سیاق نزدیک و پیوستگی سوره", "description": "آیه‌های پیش و پس را بخوانید و نتیجه را از موضوع و حرکتِ سوره جدا نکنید.", "availability": "سیاق نزدیک فعال؛ مطالعهٔ سوره با کاربر"},
    {"id": "linguistics", "title": "صرف، نحو و چندمعنایی", "description": "ریشه، نقش دستوری و اشتراک لفظی باید با منبع زبان‌شناختی معتبر بررسی شود.", "availability": "نیازمند منبع تخصصیِ افزوده‌شونده"},
    {"id": "history", "title": "مخاطب، مکی/مدنی و تاریخ", "description": "طبقه‌بندی مکی/مدنی یک قرینه است؛ شأن نزول و تاریخ باید با منبع دقیق و قابل ارجاع سنجیده شود.", "availability": "مکی/مدنی فعال؛ شأن نزول خارج از پیکرهٔ فعلی"},
    {"id": "tafsir", "title": "تفسیر، اختلاف دیدگاه و احتیاط", "description": "هر تفسیر باید با نام اثر، مؤلف، جلد و صفحه ثبت شود و اختلاف نظرها حذف نشوند.", "availability": "دفتر شواهدِ محلی برای آیه و یادداشت منبع آماده است؛ متن تفسیر افزوده نشده است"},
]



def load_corpus() -> tuple[list[dict[str, Any]], dict[tuple[int, int], dict[str, Any]], dict[int, dict[str, Any]]]:
    with (DATA_DIR / "quran-uthmani.json").open(encoding="utf-8") as file:
        arabic = json.load(file)
    with (DATA_DIR / "quran-fa-ih.json").open(encoding="utf-8") as file:
        persian = json.load(file)
    with (DATA_DIR / "chapters.json").open(encoding="utf-8") as file:
        chapters_data = json.load(file)["chapters"]

    chapters = {item["id"]: item for item in chapters_data}
    corpus: list[dict[str, Any]] = []
    verse_map: dict[tuple[int, int], dict[str, Any]] = {}

    for chapter_key, ayat in arabic.items():
        for arabic_ayah, persian_ayah in zip(ayat, persian[chapter_key]):
            chapter = int(arabic_ayah["chapter"])
            verse = int(arabic_ayah["verse"])
            record = {
                "surah": chapter,
                "ayah": verse,
                "arabic": arabic_ayah["text"],
                "persian": persian_ayah["text"],
                "arabic_normalized": normalize(arabic_ayah["text"]),
                "persian_normalized": normalize(persian_ayah["text"]),
                "surah_name": chapters[chapter]["name"],
                "surah_type": "مدنی" if chapters[chapter]["type"] == "medinan" else "مکی",
            }
            corpus.append(record)
            verse_map[(chapter, verse)] = record
    return corpus, verse_map, chapters


CORPUS, VERSE_MAP, CHAPTERS = load_corpus()


class AnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=120)
    limit: int = Field(default=12, ge=6, le=24)
    include_context: bool = True
    mode: Literal["topic", "literal"] = "topic"


def find_topic(query: str) -> tuple[str | None, dict[str, Any] | None]:
    query_normalized = normalize(query)
    matches: list[tuple[int, str, dict[str, Any]]] = []
    for title, topic in TOPICS.items():
        for alias in topic["aliases"]:
            alias_normalized = normalize(alias)
            if alias_normalized and alias_normalized in query_normalized:
                matches.append((len(alias_normalized), title, topic))
    if not matches:
        return None, None
    _, title, topic = max(matches, key=lambda item: item[0])
    return title, topic


def contains_term(record: dict[str, Any], normalized_term: str) -> bool:
    return normalized_term in record["arabic_normalized"] or normalized_term in record["persian_normalized"]


def make_terms(
    query: str, topic: dict[str, Any] | None, mode: Literal["topic", "literal"]
) -> list[tuple[str, str, bool, str]]:
    """Return term, readable label, directness, and provenance for retrieval.

    Literal mode protects the user's expression from implicit expansion. Topic mode
    adds only the compact, visible vocabulary declared in TOPICS.
    """
    output: list[tuple[str, str, bool, str]] = []
    query_normalized = normalize(query)
    if query_normalized:
        output.append((query_normalized, "عبارتِ جست‌وجوشده", True, "literal"))

    if mode == "topic":
        # Components of a multiword question are discovery aids, not direct matches
        # for the complete phrase.
        for token in query_normalized.split():
            if len(token) >= 3 and token != query_normalized:
                output.append((token, f"واژهٔ «{token}»", False, "query_component"))
        if topic:
            for term, label in topic["terms"]:
                normalized_term = normalize(term)
                if normalized_term:
                    output.append(
                        (
                            normalized_term,
                            label,
                            normalized_term == query_normalized,
                            "topic_lexicon",
                        )
                    )

    seen: set[str] = set()
    unique: list[tuple[str, str, bool, str]] = []
    for item in output:
        if item[0] not in seen:
            unique.append(item)
            seen.add(item[0])
    return unique


def evidence_for(
    record: dict[str, Any], terms: list[tuple[str, str, bool, str]]
) -> tuple[int, list[str], bool, list[dict[str, str]]]:
    """Score a verse and preserve the exact field and vocabulary that retrieved it."""
    score = 0
    labels: list[str] = []
    trace: list[dict[str, str]] = []
    direct = False

    for term, label, is_query_term, origin in terms:
        in_arabic = term in record["arabic_normalized"]
        in_persian = term in record["persian_normalized"]
        if not (in_arabic or in_persian):
            continue
        source = "هر دو متن" if in_arabic and in_persian else "متن عربی" if in_arabic else "ترجمهٔ فارسی"
        labels.append(label)
        trace.append(
            {
                "label": label,
                "term": term,
                "source": source,
                "origin": "عبارتِ کاربر" if is_query_term else "واژه‌نامهٔ موضوعی" if origin == "topic_lexicon" else "جزءِ پرسش",
            }
        )
        score += 8 if is_query_term else 4
        direct = direct or is_query_term

    # A small, explicit preference for results with an Arabic witness; it does not
    # change their relation type or assert any semantic priority.
    if trace and any(item["source"] in {"متن عربی", "هر دو متن"} for item in trace):
        score += 1

    unique_trace: list[dict[str, str]] = []
    seen_trace: set[tuple[str, str]] = set()
    for item in trace:
        key = (item["label"], item["source"])
        if key not in seen_trace:
            unique_trace.append(item)
            seen_trace.add(key)
    return score, list(dict.fromkeys(labels))[:4], direct, unique_trace[:5]


def serialize_verse(
    record: dict[str, Any],
    score: int,
    matches: list[str],
    relation: str,
    evidence: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "id": f"{record['surah']}:{record['ayah']}",
        "surah": record["surah"],
        "ayah": record["ayah"],
        "reference": f"{record['surah_name']} {record['surah']}:{record['ayah']}",
        "revelation": record["surah_type"],
        "arabic": record["arabic"],
        "persian": record["persian"],
        "score": score,
        "matches": matches,
        "evidence": evidence or [],
        "relation": relation,
    }


def surrounding_context(record: dict[str, Any]) -> list[dict[str, Any]]:
    context: list[dict[str, Any]] = []
    for delta in (-1, 1):
        neighbor = VERSE_MAP.get((record["surah"], record["ayah"] + delta))
        if neighbor:
            context.append(
                serialize_verse(
                    neighbor,
                    0,
                    ["همسایگی خطی با آیهٔ بازیابی‌شده"],
                    "سیاق خطی",
                )
            )
    return context


def structural_payload(
    candidates: list[tuple[dict[str, Any], int, list[str], bool, list[dict[str, str]]]]
) -> dict[str, Any]:
    """Describe result distribution without converting a pattern into interpretation."""
    buckets: dict[int, dict[str, Any]] = {}
    revelation = {
        "مکی": {"total": 0, "direct": 0},
        "مدنی": {"total": 0, "direct": 0},
    }
    ordered = sorted(candidates, key=lambda item: (item[0]["surah"], item[0]["ayah"]))

    for record, _, _, direct, _ in ordered:
        surah = record["surah"]
        bucket = buckets.setdefault(
            surah,
            {
                "surah": surah,
                "name": record["surah_name"],
                "type": record["surah_type"],
                "total": 0,
                "direct": 0,
            },
        )
        bucket["total"] += 1
        bucket["direct"] += int(direct)
        revelation[record["surah_type"]]["total"] += 1
        revelation[record["surah_type"]]["direct"] += int(direct)

    clusters: list[dict[str, Any]] = []
    run: list[tuple[dict[str, Any], int, list[str], bool, list[dict[str, str]]]] = []
    for item in ordered:
        record = item[0]
        if not run or (record["surah"] == run[-1][0]["surah"] and record["ayah"] <= run[-1][0]["ayah"] + 3):
            run.append(item)
            continue
        if len(run) >= 2:
            clusters.append(
                {
                    "reference": f"{run[0][0]['surah_name']} {run[0][0]['surah']}:{run[0][0]['ayah']}–{run[-1][0]['ayah']}",
                    "count": len(run),
                    "span": run[-1][0]["ayah"] - run[0][0]["ayah"] + 1,
                }
            )
        run = [item]
    if len(run) >= 2:
        clusters.append(
            {
                "reference": f"{run[0][0]['surah_name']} {run[0][0]['surah']}:{run[0][0]['ayah']}–{run[-1][0]['ayah']}",
                "count": len(run),
                "span": run[-1][0]["ayah"] - run[0][0]["ayah"] + 1,
            }
        )

    distribution = sorted(buckets.values(), key=lambda item: (-item["total"], item["surah"]))[:7]
    clusters.sort(key=lambda item: (-item["count"], item["span"], item["reference"]))
    return {
        "revelation": revelation,
        "distribution": distribution,
        "clusters": clusters[:4],
        "note": "این نمودار فقط پراکندگیِ بازیابی را توصیف می‌کند و نشان‌دهندهٔ اهمیت تفسیری یا رتبه‌بندی سوره‌ها نیست.",
    }


def graph_payload(canonical: str, terms: list[tuple[str, str, bool, str]], verses: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = [
        {
            "id": "topic",
            "label": canonical,
            "meta": "پرسشِ کاربر",
            "kind": "topic",
            "weight": 1,
        }
    ]
    edges: list[dict[str, str]] = []
    term_nodes = []
    for index, (term, label, direct, _) in enumerate(terms[:4]):
        identifier = f"term-{index}"
        term_nodes.append((identifier, term, label))
        nodes.append(
            {
                "id": identifier,
                "label": label.replace("ترجمهٔ ", ""),
                "meta": "واژهٔ جست‌وجو" if direct else "واژهٔ هم‌خانواده",
                "kind": "term",
                "weight": 0.75,
            }
        )
        edges.append({"source": "topic", "target": identifier, "label": "مسیر بازیابی"})

    for index, verse in enumerate(verses[:6]):
        identifier = f"verse-{index}"
        nodes.append(
            {
                "id": identifier,
                "label": verse["reference"],
                "meta": verse["relation"],
                "kind": "verse",
                "weight": 0.5,
            }
        )
        match_index = index % max(len(term_nodes), 1)
        source = term_nodes[match_index][0] if term_nodes else "topic"
        edges.append({"source": source, "target": identifier, "label": verse["relation"]})
    return {"nodes": nodes, "edges": edges}


def analyze(
    query: str,
    limit: int,
    include_context: bool,
    mode: Literal["topic", "literal"] = "topic",
) -> dict[str, Any]:
    cleaned_query = WHITESPACE.sub(" ", query).strip()
    if not cleaned_query:
        raise HTTPException(status_code=422, detail="عبارت جست‌وجو نمی‌تواند خالی باشد.")

    canonical, topic = find_topic(cleaned_query)
    active_topic = topic if mode == "topic" else None
    terms = make_terms(cleaned_query, active_topic, mode)
    candidates: list[tuple[dict[str, Any], int, list[str], bool, list[dict[str, str]]]] = []
    for record in CORPUS:
        score, labels, direct, trace = evidence_for(record, terms)
        if score:
            candidates.append((record, score, labels, direct, trace))

    candidates.sort(key=lambda item: (-item[1], item[0]["surah"], item[0]["ayah"]))
    direct_candidates = [item for item in candidates if item[3]]
    thematic_candidates = [item for item in candidates if not item[3]]

    # Keep literal evidence first, then add transparent, tagged topical evidence.
    selected = (direct_candidates + thematic_candidates)[:limit]
    verses = [
        serialize_verse(
            record,
            score,
            labels,
            "ذکر / ترجمهٔ مستقیم" if direct else "پیوند واژگانیِ موضوعی",
            trace,
        )
        for record, score, labels, direct, trace in selected
    ]

    contexts: list[dict[str, Any]] = []
    if include_context and selected:
        seen = {item["id"] for item in verses}
        for record, _, _, _, _ in selected[:3]:
            for neighbor in surrounding_context(record):
                if neighbor["id"] not in seen:
                    contexts.append(neighbor)
                    seen.add(neighbor["id"])
                if len(contexts) >= 4:
                    break
            if len(contexts) >= 4:
                break

    surah_counts = Counter(record["surah"] for record, _, _, _, _ in candidates)
    canonical_label = canonical if mode == "topic" and canonical else cleaned_query
    expansion_labels = [label for _, label, is_query, _ in terms if not is_query][:6]
    if mode == "literal":
        summary = (
            f"در حالتِ عبارت‌محور، {len(direct_candidates)} شاهد برای «{cleaned_query}» بازیابی شد. "
            "هیچ واژهٔ هم‌خانواده یا توسعهٔ موضوعی به این جست‌وجو افزوده نشده است."
        )
    else:
        summary = (
            f"برای «{canonical_label}»، {len(direct_candidates)} شاهدِ دارای عبارتِ جست‌وجوشده و "
            f"{len(thematic_candidates)} شاهدِ دارای واژه‌های هم‌خانواده بازیابی شد. "
            "نتایجِ موضوعی با برچسب واژهٔ شاهد نمایش داده شده‌اند تا مسیر استدلال قابل بازبینی بماند."
        )
    if not candidates:
        summary = (
            f"برای «{cleaned_query}» در بازیابی واژگانیِ فعلی شاهدی پیدا نشد. "
            "صورت عربیِ واژه، ریشهٔ کوتاه‌تر یا حالت موضوعی را امتحان کنید."
        )

    mode_info = {
        "id": mode,
        "label": "موضوعیِ شفاف" if mode == "topic" else "فقط عبارت",
        "description": (
            "عبارتِ کاربر با واژه‌نامهٔ کوچک و قابل مشاهدهٔ موضوع گسترش می‌یابد."
            if mode == "topic"
            else "فقط عبارتِ واردشده در متن عربی و ترجمهٔ فارسی جست‌وجو می‌شود."
        ),
    }
    method = {
        "title": "روشِ بازیابیِ قابل‌ممیزی",
        "steps": [
            "متن عربی و ترجمهٔ فارسی به‌صورت جداگانه نرمال‌سازی و جست‌وجو می‌شوند.",
            mode_info["description"],
            "روی هر آیه، منبع شاهد (متن عربی یا ترجمهٔ فارسی) و مسیر واژه‌ای نمایش داده می‌شود.",
            "برای جلوگیری از بریده‌خوانی، همسایه‌های خطیِ چند آیهٔ اول نیز نشان داده می‌شوند.",
            "گراف و نمودار ساختاری فقط دادهٔ بازیابی را نشان می‌دهند؛ نتیجهٔ تفسیریِ قطعی نیستند.",
        ],
    }
    graph_terms = terms if terms else [(normalize(cleaned_query), "عبارتِ جست‌وجوشده", True, "literal")]
    return {
        "query": cleaned_query,
        "canonical_topic": canonical if mode == "topic" else None,
        "mode": mode_info,
        "summary": summary,
        "topic_description": active_topic["description"] if active_topic else "جست‌وجوی عبارت‌محور، بدون توسعهٔ موضوعیِ ازپیش‌تعریف‌شده.",
        "questions": active_topic["questions"] if active_topic else [
            "این واژه در کدام نقش دستوری و سیاق به کار رفته است؟",
            "آیا صورت عربی یا واژهٔ هم‌ریشه‌ای برای جست‌وجوی دقیق‌تر وجود دارد؟",
        ],
        "stats": {
            "direct": len(direct_candidates),
            "thematic": len(thematic_candidates),
            "surahs": len(surah_counts),
            "shown": len(verses),
        },
        "expansion": expansion_labels,
        "verses": verses,
        "context": contexts,
        "structure": structural_payload(candidates),
        "graph": graph_payload(canonical_label, graph_terms, verses),
        "method": method,
        "corpus": {
            "arabic": "Tanzil Uthmani (verbatim)",
            "persian": "QuranEnc — Persian, Ihsan Elahi Zaheer",
            "total_verses": len(CORPUS),
        },
    }


app = FastAPI(
    title="ذهن‌یار | پژوهش موضوعی قرآن",
    version="1.1.0",
    description="بازیابی شفاف واژگانی و پیوندهای موضوعی در متن قرآن، با نمایش شواهد، سیاق و مسیر بازیابی.",
)
app.add_middleware(GZipMiddleware, minimum_size=600)


@app.middleware("http")
async def standards_headers(request, call_next):
    """Keep the single-page research workspace private and self-contained by default."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; font-src 'self' data:; connect-src 'self'; "
        "object-src 'none'; base-uri 'self'; form-action 'self'"
    )
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/health", tags=["system"])
def health() -> dict[str, Any]:
    return {"status": "ok", "verses": len(CORPUS), "topics": len(TOPICS)}


@app.get("/api/framework", tags=["research"])
def framework() -> dict[str, Any]:
    return {
        "categories": TOPIC_CATEGORIES,
        "protocol": READING_PROTOCOL,
        "notice": "این نقشه، چارچوب پژوهش و مسیر ورود به متن است؛ جایگزین تفسیر معتبر یا داوری تخصصی نیست.",
    }


@app.get("/api/meta", tags=["research"])
def meta() -> dict[str, Any]:
    category_by_topic = {
        topic: category["id"]
        for category in TOPIC_CATEGORIES
        for topic in category["topics"]
    }
    return {
        "topics": [
            {
                "title": title,
                "aliases": topic["aliases"],
                "description": topic["description"],
                "category": category_by_topic.get(title, "other"),
            }
            for title, topic in TOPICS.items()
        ],
        "modes": [
            {"id": "literal", "label": "فقط عبارت", "description": "بدون توسعهٔ واژگانی"},
            {"id": "topic", "label": "موضوعیِ شفاف", "description": "با واژه‌نامهٔ قابل مشاهدهٔ موضوع"},
        ],
        "corpus": {"verses": len(CORPUS), "arabic": "Tanzil Uthmani", "persian": "QuranEnc Persian (Ihsan Elahi Zaheer)"},
    }


@app.post("/api/analyze", tags=["research"])
def analyze_topic(request: AnalyzeRequest) -> dict[str, Any]:
    return analyze(request.query, request.limit, request.include_context, request.mode)


@app.get("/api/analyze", tags=["research"])
def analyze_topic_get(
    q: str = Query(..., min_length=1, max_length=120),
    limit: int = Query(default=12, ge=6, le=24),
    mode: Literal["topic", "literal"] = Query(default="topic"),
) -> dict[str, Any]:
    return analyze(q, limit, True, mode)


@app.get("/api/verse/{surah}/{ayah}", tags=["research"])
def get_verse(surah: int, ayah: int) -> dict[str, Any]:
    record = VERSE_MAP.get((surah, ayah))
    if not record:
        raise HTTPException(status_code=404, detail="آیه پیدا نشد.")
    return serialize_verse(record, 0, [], "متنِ پایه")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
