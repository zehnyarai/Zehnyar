# -*- coding: utf-8 -*-
"""Yunus 10:9-11 dossier — those who do not hope for the meeting, and their refuge.

Tabari reads «ضياء» and «نور» as day and night lights, explains the singular
pronoun in «وقدّره» with two options, and ties the mansions to the calendar;
Saadi builds an argument from design; Nemuneh lists three views on the
difference between «ضياء» and «نور».
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from source_policy import POLICY, collect  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "static" / "verse-dossier-extended-fields.json"
TR = json.loads((ROOT / "data" / "quran-fa-fooladvand.json").read_text(encoding="utf-8"))
DATA = json.loads(PATH.read_text(encoding="utf-8"))

FIELDS = ["bibleComparison", "guidanceDiscourse", "shubuhat", "modernSciences", "qiraat",
          "philosophicalFoundations", "linguistics", "criticalDiscourseAnalysis",
          "historicalContext", "balaghaNazm"]

FAIRCLOUGH = "Norman Fairclough, Language and Power, 2nd ed. (Longman, 2001), ch. 3"
WATT = "W. Montgomery Watt, Muhammad at Mecca (Clarendon Press, 1953), ch. 3"
WRIGHT = "W. Wright, A Grammar of the Arabic Language, 3rd ed. (Cambridge University Press, 1896), vol. 2, § 36–41"
JURJANI = "عبدالقاهر الجرجاني، دلائل الإعجاز، تحقيق محمود محمد شاكر (مكتبة الخانجي، ۱۹۹۲)، فصلُ الإيجاز والحذف"
GENESIS = ("Matthew 6:19–21 (King James Version)؛ "
           "https://www.biblegateway.com/passage/?search=Matthew%206%3A19-21")
MATT16 = ("Matthew 16:27 (King James Version)؛ "
          "https://www.biblegateway.com/passage/?search=Matthew%2016%3A27")
FRANKFURT = ("Harry G. Frankfurt, The Importance of What We Care About: Philosophical Essays "
             "(Cambridge: Cambridge University Press, 1988), ch. 6")
GHAZALI3 = ("Abū Ḥāmid al-Ghazālī, Iḥyāʾ ʿulūm al-dīn, kitāb al-khawf wa-l-rajāʾ (Beirut: Dār al-Maʿrifa)")
WATT2 = ("W. Montgomery Watt, Muhammad at Mecca (Oxford: Clarendon Press, 1953), ch. 4")
KIAI2 = ("سیده فاطمه کیایی و سید قاسم کیایی، «تبیینی غیر امیدبخش از معاد مبتنی بر معادل‌انگاری رجاء با تصدیق "
         "در آیۀ ۷ سورۀ یونس»، نشریهٔ علوم و معارف قرآن؛ https://qd.razavi.ac.ir/article_1282.html")
RAJA = ("فاطمه رهبری و مرضیه رستمیان، «معناشناسی واژهٔ رجاء در قرآن با تکیه بر روابط همنشینی و جانشینی»، "
        "پژوهش‌های معناشناختی متون ادبی ۱۰ (تابستان ۱۴۰۴): ۳۴–۵۰؛ مقالهٔ پژوهشی")
MIZAN = ("الطباطبائي، الميزان في تفسير القرآن، ذيلِ يونس ۱۰:۷–۸ (ترجمهٔ فارسی)؛ "
         "https://quran.anhar.ir/tafsirfull-13616.htm")
PATRICIA = ("Patricia Crone, Meccan Trade and the Rise of Islam (Princeton: Princeton University Press, 1987)")
V = "يونس ۱۰:۷–۸"
NEM = ("مكارم الشيرازي، برگزیدهٔ تفسیر نمونه (تنظیم احمد علی بابایی، دارالکتب الاسلامیة، ۱۳۸۶ش)، ذیلِ يونس ۱۰:۷، "
       "به نقل از دانشنامهٔ اهل بیت؛ https://wiki.ahlolbait.com/آیه_7_سوره_یونس")
TAB = f"الطبري، جامع البيان، {V} (يونس ۱۰:۷–۸)؛ https://tafsir.app/tabari/10/7"
SAD = f"السعدي، تيسير الكريم الرحمن، {V}؛ https://tafsir.app/saadi/10/7"
LOCAL = "قرآن، يونس؛ متن عثمانی و ترجمهٔ فولادوندِ محلی"
SAD8 = "السعدي، تيسير الكريم الرحمن، يونس ۱۰:۸؛ https://tafsir.app/saadi/10/8"


def rec_base(text, cite):
    return {"text": text, "cite": cite}


def build(*, title: str, review: str, notes: list, context: list, classical: list,
          modern: list, critical: list, research: list, ext: dict) -> dict:
    record = {
        "tier": "core",
        "sourcePolicyVersion": 2,
        "title": title,
        "reviewStatus": review,
        "coverageNote": ("این رکورد در سطحِ core است: شش فیلدِ پایه هر یک سه مدخل و ده فیلدِ افزوده یک یا دو "
                         "مدخل دارند؛ سطحِ full به پنج مدخلِ مقابله‌شده در هر فیلد نیاز دارد."),
        "fieldCoverageStatus": ("شش فیلدِ پایه سه‌مدخلی‌اند و فیلدهایِ افزوده یک یا دو مدخلی؛ هر جا منبعِ "
                                "مقابله‌شده داده‌ای نداشته، همان کمبود با status و یادداشت ثبت شده است."),
        "notes": notes,
        "context": context,
        "classical": classical,
        "modern": modern,
        "critical": critical,
        "research": research,
        "extendedFields": {},
    }
    for fid in FIELDS:
        value = ext[fid]
        items = value if isinstance(value, list) else [value]
        entries = [{"kind": kind, "text": text, "cite": cite, "evidence": evidence, "limit": limit}
                   for text, evidence, limit, cite, kind in items]
        record["extendedFields"][fid] = {
            "status": "partial",
            "coverage": {"completed": len(entries), "required": 5},
            "sourceCoverageNote": (f"برای {V} در فیلدِ {fid} {len(entries)} مدخل ثبت شده است؛ رسیدن به "
                                   "پوششِ پنج‌مدخلی به مقابلهٔ منابعِ تخصصیِ همین فیلد نیاز دارد."),
            "followUp": "منابعِ تخصصیِ این فیلد مقابله شوند و مدخل‌ها به پنج برسد؛ در نبودِ شاهد، ادعا ساخته نشود.",
            "entries": entries,
        }
    record["sourceMix"] = collect(record)
    return record


records = {}

T36 = "الطبري، جامع البيان، يونس ۱۰:۳۶؛ https://tafsir.app/tabari/10/36"
S36 = "السعدي، تيسير الكريم الرحمن، يونس ۱۰:۳۶؛ https://tafsir.app/saadi/10/36"
MIZ = ("الطباطبائي، الميزان في تفسير القرآن، ذيلِ يونس ۱۰:۲۶–۳۶ (ترجمهٔ فارسی)؛ "
       "https://quran.anhar.ir/tafsirfull-13618.htm")
LOCALY = "قرآن، يونس؛ متن عثمانی و ترجمهٔ فولادوندِ محلی"
TAYLOR = ("Charles Taylor, Sources of the Self: The Making of the Modern Identity "
          "(Cambridge, MA: Harvard University Press, 1989), part 1")
HOURANI = "Albert Hourani, A History of the Arab Peoples (London: Faber and Faber, 1991), ch. 2"
WRIGHTJ = "W. Wright, A Grammar of the Arabic Language, 3rd ed. (Cambridge University Press, 1896), vol. 2, § 36–41"
JURJANI = "عبدالقاهر الجرجاني، دلائل الإعجاز، تحقيق محمود محمد شاكر (مكتبة الخانجي، ۱۹۹۲)، فصلُ الحصر والقصر"
FAIRCLOUGH = "Norman Fairclough, Language and Power, 2nd ed. (Longman, 2001), ch. 3"
J_TATBIQ = ("انسیه عسگری و محمدکاظم شاکر، «ضوابط علمی و کاربردی در روش تفسیر تطبیقی»، پژوهش‌های قرآنی "
            "۲۰/۴ (پیاپی ۷۷، زمستان ۱۳۹۴)؛ مقالهٔ پژوهشی")
J_IBTILA = ("مقالهٔ پژوهشی «ابتلا و آزمایش در قرآن»، عبدالعلی پاکزاد، پژوهش‌های قرآنی (۱۳۸۸)؛ "
            "https://quran.isca.ac.ir/fa/Article/Detail/3456")
PROV14 = ("Proverbs 14:12 (King James Version)؛ "
          "https://www.biblegateway.com/passage/?search=Proverbs%2014%3A12")
JOHN8 = ("John 8:32 (King James Version)؛ "
         "https://www.biblegateway.com/passage/?search=John%208%3A32")
ISAIAH55 = ("Isaiah 55:8–9 (King James Version)؛ "
            "https://www.biblegateway.com/passage/?search=Isaiah%2055%3A8-9")

records["10:36"] = build(
    title="يونس ۱۰:۳۶ | «إن الظن لا يغني من الحق شيئًا»",
    review=("پیش‌نویسِ منبع‌محور در سطحِ core برای يونس ۱۰:۳۶: طبری ظن را شك و ریبه می‌داند که جای یقین را "
            "نمی‌گیرد؛ سعدی ریشهٔ شرک را «تزیینِ شیطان» می‌شمارد؛ المیزان توضیح می‌دهد چرا ظن به «أکثر» نسبت "
            "یافته و رهبران کفر از آن بیرون‌اند."),
    notes=[
        rec_base(f"فولادوند يونس ۱۰:۳۶ را چنین برگردانده است: «{TR['10'][35]['text']}»؛ نقلِ ترجمه شاهدِ برگردان "
                 "است و از گزارشِ تفسیری جدا می‌ماند.", LOCALY),
        rec_base("طبری «إلا ظنًّا» را «إلا ما لا علم لهم بحقيقته وصحته، بل هم منه في شكٍّ وريبة» معنا می‌کند؛ پس "
                 "ظن را بی‌علمی می‌شمارد.", T36),
        rec_base("طبری «إن الظن لا يغني من الحق شيئًا» را «إن الشك لا يغني من اليقين شيئًا» می‌خواند؛ پس ظن را با "
                 "شک برابر می‌گیرد.", T36),
    ],
    context=[
        rec_base("طبری «ولا يقوم في شيء مقامه، ولا ينتفع به حيث يُحتاج إلى اليقين» می‌افزاید؛ پس سودِ ظن را به "
                 "موضعِ نیازِ یقینی محدود می‌کند.", T36),
        rec_base("طبری «إن الله عليم بما يفعلون» را چنین می‌گشاید: خدا می‌داند آنان «من اتباعهم الظن، وتكذيبهم "
                 "الحق اليقين»، و «هو لهم بالمرصاد».", T36),
        rec_base("المیزان می‌گوید نسبتِ ظن به «أکثر» از آن روست که رهبرانِ کفر «به نادرستى آن و به حقانيت دين "
                 "حق يقين دارند».", MIZ),
    ],
    classical=[
        rec_base("طبری «ظن» را در این آیه بر «شک و ریبه» حمل می‌کند و آن را در برابرِ «علم» و «یقین» می‌نشاند؛ "
                 "پس تقابلِ آیه را معرفتی می‌داند.", T36),
        rec_base("طبری «عليم» را در آیه بر آگاهیِ خدا به فعلِ مخاطبان حمل می‌کند، نه بر آگاهیِ آنان؛ پس فاعلِ "
                 "علم را خدا می‌شمارد.", T36),
        rec_base("طبری در تفسیرِ «أغنی» خواننده را به مواضعِ پیشینِ همین ماده ارجاع می‌دهد و بحثِ لغوی را در "
                 "همان‌جا مفصل می‌داند.", T36),
    ],
    modern=[
        rec_base("سعدی ریشهٔ شرک را «تزيين الشيطان للإنسان أقبح البهتان وأضل الضلال» می‌شمارد؛ پس منشأ را "
                 "فریبِ بیرونی می‌داند.", S36),
        rec_base("سعدی تصریح می‌کند: «فإنه ليس لله شريك أصلًا عقلًا ولا نقلًا»؛ پس شرک را هم عقلاً و هم نقلاً "
                 "باطل می‌خواند.", S36),
        rec_base("سعدی برای تأیید، نجم ۲۳ را می‌آورد: «إن هي إلا أسماء سميتموها أنتم وآباؤكم ما أنزل الله بها "
                 "من سلطان».", S36),
    ],
    critical=[
        rec_base("المیزان رهبرانِ کفر را از دایرهٔ ظن بیرون می‌برد، زیرا آنان «به حقانيت دين حق يقين دارند» و "
                 "بازداشتنشان از حق به‌سببِ «بغى و دشمنی» است.", MIZ),
        rec_base("المیزان «اکثریت» را پیروِ «تقلید كوركورانه از پدران» می‌داند؛ پس ظن را نتیجهٔ تقلید می‌شمارد، "
                 "نه استدلالِ ناقص.", MIZ),
        rec_base("المیزان یادآور می‌شود که «أغنی» هم با «من» و هم با «عن» متعدی می‌شود و قرآن هر دو را به کار "
                 "برده است؛ شاهدِ دوم: «ما أغنى عني ماليه».", MIZ),
    ],
    research=[
        rec_base("المیزان جملهٔ «إن الله عليم بما يفعلون» را «تعليل» جملهٔ پیشین می‌داند: خدا می‌داند که کافران "
                 "جز پیرویِ ظن دلیلی ندارند.", MIZ),
        rec_base("عسگری و شاکر بر لزومِ تفکیکِ سطحِ استدلالِ متن از سطحِ گزارشِ مفسر تأکید می‌کنند؛ همین تفکیک "
                 "در تقابلِ «ظن/یقین» این آیه کارساز است.", J_TATBIQ),
        rec_base("گامِ بعدی، مقابلهٔ «إن الظن لا يغني من الحق» با ۵۳:۲۸ و ۴:۱۵۷ است تا روشن شود در هر سیاق ظن "
                 "به چه چیزی نسبت داده شده است.", f"{T36}؛ {MIZ}"),
    ],
    ext={
        "bibleComparison": [
            ("Proverbs 14:12 می‌گوید «There is a way which seemeth right unto a man, but the end thereof are "
             "the ways of death»؛ همان نقدِ راهی که بر ظن استوار است.",
             "تعبیرِ «seemeth right» با «ما يتبع أكثرهم إلا ظنًّا» هم‌سو است.",
             "این مقایسه مضمونی است و در منابعِ مقابله‌شده سندی بر پیوندِ دو متن نیست.",
             PROV14, "analysis"),
        ],
        "guidanceDiscourse": [
            ("آیه سه جملهٔ اسمیهٔ پیوسته می‌آورد و با «إنّ» سه بار تأکید می‌کند؛ همین تکرار، داوری را از گزارش "
             "به حکم می‌برد.",
             "تکرارِ «إنّ» در «إن الظن… إن الله» شاهدِ این ساخت است.",
             "این خوانش ساختارِ متن را روشن می‌کند و دربارهٔ مخاطبان ادعایی ندارد.",
             f"{T36}؛ {MIZ}", "analysis"),
        ],
        "shubuhat": [
            ("شبهه این است که اگر پیرویِ ظن باطل است، چگونه تقلیدِ عامیانه مجاز شمرده می‌شود؛ پاسخِ منابعِ "
             "مقابله‌شده تفکیکِ ظنِ بی‌دلیل از پیرویِ مستند است.",
             "تعبیرِ «لا ينتفع به حيث يُحتاج إلى اليقين» در طبری شاهدِ این تفکیک است.",
             "این پاسخ تفسیری است و بحثِ کلامیِ حجیتِ ظن در این فیلد مقابله نشده است.",
             f"{T36}؛ {S36}", "analysis"),
        ],
        "modernSciences": [
            ("در منابعِ مقابله‌شده برای ۱۰:۳۶ ادعای علمیِ تجربی نیامده است؛ سخن از ارزشِ معرفتیِ ظن است و "
             "خوانشِ شناختیِ آن نیازمندِ پژوهشِ مستقل است.",
             "مدخل‌های طبری و سعدی و المیزان در این آیه لغوی و معرفتی‌اند.",
             "این خلأ نبودِ پژوهشِ میان‌رشته‌ای را اثبات نمی‌کند؛ منابعِ تخصصی مقابله نشده‌اند.",
             f"{T36}؛ {MIZ}", "source-coverage-note"),
        ],
        "qiraat": [
            ("در این آیه اختلافِ قرائتیِ ثبت‌شده‌ای در طبری نیامده است و «أكثرهم» و «يغنِ» در قرائتِ رایج بدونِ "
             "اختلاف خوانده می‌شوند.",
             "طبری در این آیه فقط معنا و لغت را می‌آورد و بابی برای قرائت نمی‌گشاید.",
             "نبودِ گزارش در یک منبع اثباتِ نبودِ اختلاف نیست؛ کتبِ قرائات مقابله نشده‌اند.",
             T36, "source-coverage-note"),
        ],
        "philosophicalFoundations": [
            ("تیلور نشان می‌دهد آدمی باورهای خود را در چارچوبِ پیش‌فرض‌هایی می‌سازد که کمتر می‌آزماید؛ آیه همان "
             "پیش‌فرضِ ناآزموده را «ظن» می‌نامد.",
             "بحثِ «background assumptions» شاهدِ این چارچوب است.",
             "این تحلیل فلسفی است و دربارهٔ ارزشِ معرفتیِ باور داوری نمی‌کند.",
             TAYLOR, "analysis"),
        ],
        "linguistics": [
            ("«ظن» در عربی میان شک و گمانِ راجح نوسان دارد و آیه آن را در برابرِ «حق» می‌نشاند؛ همین تقابل، "
             "معنای منفی را تثبیت می‌کند.",
             "معادل‌گذاریِ طبری («في شكٍّ وريبة») شاهدِ این تحلیل است.",
             "این تحلیل لغوی است و دربارهٔ مصداقِ ظن داوری نمی‌کند.",
             f"{T36}؛ {WRIGHTJ}", "analysis"),
        ],
        "criticalDiscourseAnalysis": [
            ("آیه با «أكثرهم» دامنهٔ داوری را محدود می‌کند و با «عليم بما يفعلون» آن را به آگاهیِ خدا می‌بندد؛ "
             "همین دو حرکت، حکم را از تعمیم به تهدید می‌برد.",
             "تقابلِ «أكثرهم» و «عليم» شاهدِ این دو حرکت است.",
             "تحلیلِ گفتمانی خوانشی از دامنهٔ خطاب است و دربارهٔ مخاطبان داوری نمی‌کند.",
             FAIRCLOUGH, "analysis"),
        ],
        "historicalContext": [
            ("هوارانی نشان می‌دهد دینِ عربِ پیش از اسلام بر میراثِ پدران و آیینِ حرم استوار بود؛ آیه همین "
             "اتکای به میراث را هدف می‌گیرد.",
             "بحثِ هوارانی دربارهٔ آیینِ حرم و سنتِ پدران شاهدِ این زمینه است.",
             "هوارانی تاریخِ عمومی است و مصداقِ خاصِ آیه را تعیین نمی‌کند.",
             HOURANI, "analysis"),
        ],
        "balaghaNazm": [
            ("آیه «الظن» را با الف و لامِ جنس می‌آورد و «الحق» را نیز چنین؛ پس دو مفهوم را در سطحِ کلی "
             "می‌سنجد، نه در مصداقِ جزئی.",
             "تعریفِ هر دو طرف در «إن الظن لا يغني من الحق» شاهدِ این ساخت است.",
             "داوریِ بلاغی تحلیلی است و معیارِ کمّیِ مستقل ندارد.",
             f"{JURJANI}؛ {MIZ}", "analysis"),
        ],
    },
)

DATA["criteria"].update(POLICY)
for verse_id, record in records.items():
    record["requiresDiverseSources"] = True
    record["sourceMix"] = collect(record)

fa = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
total = len({**DATA["verses"], **records})
for item in DATA["scope"]:
    if item["range"] == "9:1–129":
        item["status"] = (
            "هدفِ فعال تکمیلِ سوره‌های توبه، يونس و هود است؛ overlay اکنون تا ۹:۱۰۸ و آیاتِ آغازینِ يونس "
            f"(۱۰:۱–۳۶) و هود (۱۱:۱) می‌رسد ({str(total).translate(fa)} رکورد با احتسابِ ۸:۵۱–۷۵). از ۱۰:۱ سیاستِ v3 "
            "(تفسیرِ سنّی + شیعی + مقالهٔ داوری‌شده) اجرا می‌شود. ۹:۱۰۹–۱۲۹ و ادامهٔ ۱۰ و ۱۱ هنوز وارد نشده و "
            "سوره‌ها کامل نیستند.")
    if item["range"] == "۱۰:۱–۳۵ · تنوعِ منابع v3":
        item["range"] = "۱۰:۱–۳۶ · تنوعِ منابع v3"
        item["status"] = (
            "سیاستِ تنوعِ v3 از ۱۰:۱ اجرا می‌شود و ۱۰:۱ تا ۱۰:۳۶ و ۱۱:۱ آن را برآورده‌اند: هر رکورد دست‌کم یک "
            "تفسیرِ کهنِ سنّی، یک منبعِ معاصر، یک منبعِ شیعی و یک مقالهٔ پژوهشیِ داوری‌شده دارد. همین قاعده تا "
            "پایانِ قرآن ادامه می‌یابد و رکوردهایِ پیشینِ توبه به‌تدریج پر می‌شوند.")
DATA["scope"].append({
    "range": "10:36",
    "status": (
        "۱۰:۳۶ در سطحِ core ثبت شد: تقابلِ معرفتیِ «ظن/یقین»، تهدیدِ «عليم بما يفعلون»، تزیینِ شیطان در سعدی، و "
        "تفکیکِ اکثریتِ مقلّد از رهبرانِ کفر در المیزان با بحثِ تعدیهٔ «أغنی».")})

for verse_id, record in records.items():
    DATA["verses"][verse_id] = record

DATA["verses"] = dict(sorted(DATA["verses"].items(),
                             key=lambda kv: (int(kv[0].split(":")[0]), int(kv[0].split(":")[1]))))
PATH.write_text(json.dumps(DATA, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

print(f"records: {len(DATA['verses'])}")
for verse_id, record in records.items():
    print(verse_id, "mix:", [(m["work"][:26], m["role"], m["entries"]) for m in record["sourceMix"]])
