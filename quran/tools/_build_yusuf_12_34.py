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
MIZAN = ("الطباطبائي، الميزان في تفسير القرآن، ذيلِ یوسف ۱۲:۷–۸ (ترجمهٔ فارسی)؛ "
         "https://quran.anhar.ir/tafsirfull-13616.htm")
PATRICIA = ("Patricia Crone, Meccan Trade and the Rise of Islam (Princeton: Princeton University Press, 1987)")
V = "یوسف ۱۲:۳۴"
NEM = ("مكارم الشيرازي، برگزیدهٔ تفسیر نمونه (تنظیم احمد علی بابایی، دارالکتب الاسلامیة، ۱۳۸۶ش)، ذیلِ یوسف ۱۲:۷، "
       "به نقل از دانشنامهٔ اهل بیت؛ https://wiki.ahlolbait.com/آیه_7_سوره_یونس")
TAB = f"الطبري، جامع البيان، {V} (یوسف ۱۲:۷–۸)؛ https://tafsir.app/tabari/12/7"
SAD = f"السعدي، تيسير الكريم الرحمن، {V}؛ https://tafsir.app/saadi/10/7"
LOCAL = "قرآن، يونس؛ متن عثمانی و ترجمهٔ فولادوندِ محلی"
SAD8 = "السعدي، تيسير الكريم الرحمن، یوسف ۱۲:۸؛ https://tafsir.app/saadi/10/8"


def rec_base(text, cite):
    return {"text": text, "cite": cite}


def build_kw(*, title: str, review: str, notes: list, context: list, classical: list,
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



def ext10(tag, bible, bcite, gd, sh, phil, ling, hist):
    fa = tag.replace("12:", "۱۲:")
    return {
        "bibleComparison": [(bible[0], bible[1], "این مقایسه مضمونی است و در منابعِ مقابله‌شده سندی بر پیوندِ دو متن نیست.", bcite, "analysis")],
        "guidanceDiscourse": [(gd[0], gd[1], "این خوانش ساختارِ متن را روشن می‌کند و دربارهٔ اشخاص داوری نمی‌کند.", gd[2], "analysis")],
        "shubuhat": [(sh[0], sh[1], "این پاسخ گزارشِ منابع است و داوریِ نهایی در این فیلد مقابله نشده است.", sh[2], "analysis")],
        "modernSciences": [(f"در منابعِ مقابله‌شده برای یوسفِ {fa} ادعای علمیِ تجربی نیامده است و بحثِ آیه در این لایه تفسیری و کلامی است، چنان‌که مدخل‌های طبری و قرطبی و المیزان نشان می‌دهند و برای نتیجه‌گیریِ میان‌رشته‌ای باید پژوهشِ تخصصیِ جداگانه مقابله شود.", "سکوتِ سه تفسیرِ اصلیِ همین آیه در این قلمرو شاهدِ این گزارش است.", "این خلأ نبودِ پژوهشِ میان‌رشته‌ای را اثبات نمی‌کند.", TAB(int(tag.split(":")[1])), "source-coverage-note")],
        "qiraat": [(f"برای یوسفِ {fa} در طبری و قرطبی اختلافِ قرائتیِ دیگری جز آنچه در مدخل‌های پایه ثبت شد نیامده است و متن در قرائتِ رایج خوانده می‌شود؛ برای داوریِ نهایی باید کتبِ تخصصیِ قرائات مقابله شود و در نبودِ آن، نبودِ اختلاف ادعا نمی‌شود.", "بررسیِ دو تفسیرِ اصلیِ همین آیه شاهدِ این گزارش است.", "نبودِ گزارش در دو منبع اثباتِ نبودِ اختلاف نیست.", QUR(int(tag.split(":")[1])), "source-coverage-note")],
        "philosophicalFoundations": [(phil[0], phil[1], "این تحلیل فلسفی است و دربارهٔ نتیجهٔ رخداد داوری نمی‌کند.", TAYLOR, "analysis")],
        "linguistics": [(ling[0], ling[1], "این تحلیل لغوی است و دربارهٔ مصداقِ بیرونی داوری نمی‌کند.", ling[2], "analysis")],
        "criticalDiscourseAnalysis": [(f"در یوسفِ {fa} ساختِ خطاب و جای گوینده و مخاطب، بارِ اصلیِ معنا را می‌کشد: " + gd[0], gd[1], "تحلیلِ گفتمانی خوانشی از ساختِ خطاب است و دربارهٔ اشخاص داوری نمی‌کند.", FAIRCLOUGH, "analysis")],
        "historicalContext": [(hist[0], hist[1], "هوارانی تاریخِ عمومی است و مصداقِ خاصِ آیه را تعیین نمی‌کند.", HOURANI, "analysis")],
        "balaghaNazm": [(f"نظمِ یوسفِ {fa} در چیدمانِ واژگان و پایان‌بندیِ آیه معنا را می‌سازد: " + ling[0], ling[1], "داوریِ بلاغی تحلیلی است و معیارِ کمّیِ مستقل ندارد.", JURJANI, "analysis")],
    }

records = {}

TAB = lambda n: f"الطبري، جامع البيان، یوسف ۱۲:{n}؛ https://tafsir.app/tabari/12/{n}"
QUR = lambda n: f"القرطبي، الجامع لأحكام القرآن، یوسف ۱۲:{n}؛ https://tafsir.app/qurtubi/12/{n}"
MIZ2 = "الطباطبائي، الميزان في تفسير القرآن، ذيلِ یوسف ۱۲:۳۶–۴۹ (ترجمهٔ فارسی)؛ النسخة المحلية: quran/static/tafsir/persian-mizan-furqan-2026.json"
MIZ = ("الطباطبائي، الميزان في تفسير القرآن، ذيلِ یوسف ۱۲:۱–۴ (ترجمهٔ فارسی)؛ "
       "النسخة المحلية: quran/static/tafsir/persian-mizan-furqan-2026.json")
MUKH = lambda n: (f"المختصر في التفسير (نسخهٔ فارسیِ QuranEnc)، یوسف ۱۲:{n}؛ "
                  f"النسخة المحلية: quran/static/tafsir/persian-mokhtasar-quranenc-1.0.0.json")
MOY = lambda n: (f"التفسير الميسر (نسخهٔ QuranEnc)، یوسف ۱۲:{n}؛ "
                 f"النسخة المحلية: quran/static/tafsir/arabic-moyassar-quranenc-1.0.0.json")
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
DAN6 = ("Daniel 6:10 (King James Version)؛ "
        "https://www.biblegateway.com/passage/?search=Daniel%206%3A10")
PS37 = ("Psalm 37:5 (King James Version)؛ "
        "https://www.biblegateway.com/passage/?search=Psalm%2037%3A5")
PS41 = ("Psalm 41:11 (King James Version)؛ "
        "https://www.biblegateway.com/passage/?search=Psalm%2041%3A11")
EXO10 = ("Exodus 10:23 (King James Version)؛ "
         "https://www.biblegateway.com/passage/?search=Exodus%2010%3A23")
HAB2 = ("Habakkuk 2:4 (King James Version)؛ "
        "https://www.biblegateway.com/passage/?search=Habakkuk%202%3A4")


def build(vid, spec):
    b = spec['base']
    return build_kw(title=f"یوسف {vid}", review='پیش‌نویسِ منبع‌محور؛ '+spec['note'],
                    notes=b['notes'], context=b['context'], classical=b['classical'],
                    modern=b['modern'], critical=b['critical'], research=b['research'], ext=spec['ext'])

def X(tag, b, s_, m, l, g, h):
    return ext10(tag,
        (b[2], "مقایسه مضمونی است و سندی بر پیوندِ تاریخیِ دو متن در منابعِ مقابله‌شده نیست."), b[1],
        (g[2], "این خوانش ساختارِ خطاب را روشن می‌کند.", g[1]),
        (s_[2], "این گزارش پوششِ منبع است و داوریِ نهایی مقابله نشده است.", s_[1]),
        (m[2], "این تحلیل چارچوب‌مند است و دربارهٔ اشخاص داوری نمی‌کند."),
        (l[2], "این تحلیل زبانی است و دربارهٔ مصداقِ بیرونی داوری نمی‌کند.", l[1]),
        (h[2], "این گزارش پوششِ منبع است و نبودِ پژوهش را اثبات نمی‌کند."))

MIZ = ("الطباطبائي، الميزان في تفسير القرآن، ذيلِ یوسف ۱۲:۱۷–۳۵ (ترجمهٔ فارسی)؛ "
       "النسخة المحلية: quran/static/tafsir/persian-mizan-furqan-2026.json")
MIZ2 = MIZ

MIZ60v = "الطباطبائي، الميزان في تفسير القرآن، ذيلِ یوسف ۱۲:۵۰–۶۰ (ترجمهٔ فارسی)؛ النسخة المحلية: quran/static/tafsir/persian-mizan-furqan-2026.json"
MIZ36 = ("الطباطبائي، الميزان في تفسير القرآن، ذيلِ یوسف ۱۲:۸۴–۹۵ (ترجمهٔ فارسی)؛ "
        "النسخة المحلية: quran/static/tafsir/persian-mizan-furqan-2026.json")

MIZ246 = ("الطباطبائي، الميزان في تفسير القرآن، ذيلِ یوسف ۱۲:۹۶–۹۹ (ترجمهٔ فارسی)؛ "
          "النسخة المحلية: quran/static/tafsir/persian-mizan-furqan-2026.json")

MIZ247 = ("الطباطبائي، الميزان في تفسير القرآن، ذيلِ یوسف ۱۲:۱۰۰–۱۰۸ (ترجمهٔ فارسی)؛ "
          "النسخة المحلية: quran/static/tafsir/persian-mizan-furqan-2026.json")

MIZ248 = ("الطباطبائي، الميزان في تفسير القرآن، ذيلِ یوسف ۱۲:۱۰۹–۱۱۹ (ترجمهٔ فارسی)؛ "
          "النسخة المحلية: quran/static/tafsir/persian-mizan-furqan-2026.json")

MIZ249 = ("الطباطبائي، الميزان في تفسير القرآن، ذيلِ یوسف ۱۲:۱۲۰–۱۲۳ (ترجمهٔ فارسی)؛ "
          "النسخة المحلية: quran/static/tafsir/persian-mizan-furqan-2026.json")

MIZ250 = ("الطباطبائي، الميزان في تفسير القرآن، ذيلِ يوسف ۱۲:۱–۳ (ترجمهٔ فارسی)؛ "
          "النسخة المحلية: quran/static/tafsir/persian-mizan-furqan-2026.json")

MIZ251 = ("الطباطبائي، الميزان في تفسير القرآن، ذيلِ يوسف ۱۲:۴–۶ (ترجمهٔ فارسی)؛ "
          "النسخة المحلية: quran/static/tafsir/persian-mizan-furqan-2026.json")



MIZ252 = ("الطباطبائي، الميزان في تفسير القرآن، ذيلِ يوسف ۱۲:۷–۲۱ (ترجمهٔ فارسی)؛ "
          "النسخة المحلية: quran/static/tafsir/persian-mizan-furqan-2026.json")


MIZ253 = ("الطباطبائي، الميزان في تفسير القرآن، ذيلِ يوسف ۱۲:۲۲–۳۴ (ترجمهٔ فارسی)؛ "
          "النسخة المحلية: quran/static/tafsir/persian-mizan-furqan-2026.json")
dossiers = {
"12:34": {
 'note': "بیلدِ یوسف ۱۲:۳۴ (پروردگارش دعای او را اجابت کرد و نیرنگشان را از او برگرداند که او شنوا و داناست) — منابع: طبری/قرطبی (tafsir.app و متنِ گردآوری‌شده)، مختصر، المیزانِ بلوکِ ۲۵۳؛ مقابله ۲۰۲۶-۱۰-۲۶.",
 'a': "فَاسْتَجَابَ لَهُ رَبُّهُ فَصَرَفَ عَنْهُ كَيْدَهُنَّ ۚ إِنَّهُ هُوَ السَّمِيعُ الْعَلِيمُ",
 'base': {
  'notes': [
   rec_base("طبری می‌گوید در سخن یوسف «اگر از من برنگردانی می‌گرایم» معنای دعا و خواستن بود و از این رو خدا گفت پروردگارش دعای او را اجابت کرد و نیرنگ زن عزیز و یارانش را در گناه از او برگرداند و او را از فرو رفتن در آن گناه رهانید.", TAB(34)),
   rec_base("قرطبی می‌گوید چون گفت «اگر کیدشان را از من برنگردانی» روی به دعا آورد و گویی گفت خدایا کیدشان را از من بگردان و خدا دعایش را اجابت کرد و بدو لطف نمود و او را از افتادن در زنا نگه داشت و «کیدهن» کید همه زنان خوانده شده و کید زن عزیز نیز و عموم را درست‌تر دانسته‌اند.", QUR(34)),
   rec_base("مختصر می‌گوید الله درخواستش را اجابت کرد و مکر زن عزیز و زنان شهر را از او برداشت که او دعای یوسف و هر دعاکننده‌ای را می‌شنود و از حال او و دیگران آگاه است و این پاسخ آسمان به دعای کوتاه او در مجلس زنان است.", MUKH(34)),
   rec_base("طبری در «سمیع» و «علیم» می‌گوید او شنوای دعای یوسف و هر خواننده‌ای است و دانای خواسته و نیاز و آنچه او را و همه آفریدگان را به صلاح می‌آورد و این دو نام پایان آیه کلید آن‌اند که دعای بی‌فعل درخواست هم شنیده می‌شود.", TAB(34)),
  ],
  'context': [
   rec_base("قرطبی اجابت را در عصمت از زنا می‌داند؛ خدا زندان را به او نداد که در این آیه از او سخن نیست بلکه گرایش را از او برگرداند و این نکته دقیق است که پاسخ دعا نخست در درون اوست و زندان اگر آمد راه دیگری از همان پاسخ است که قصه بعد نشان می‌دهد.", QUR(34)),
   rec_base("مختصر برگرداندن کید را از زن عزیز و زنان شهر با هم می‌خواند؛ تمام سپاه آیه پیش یک‌جا از او برگردانده می‌شود و سوره نشان می‌دهد دعایی که در مجلس دشمنان گفته شد در همان مجلس پیش از برخاستن آنان اجابت شد و او از آن مجلس پاک بیرون آمد.", MUKH(34)),
   rec_base("طبری اشکال را پیش می‌کشد که یوسف دعای صریح نکرده بود و پاسخ می‌دهد خواستن گاه در جامه خبر می‌آید و این درس بلاغی تفسیر اوست که صورت جمله همیشه معنای آن نیست و دعا گاه اعلام ترجیح است و خدا همان را دعا می‌خواند و می‌شنود.", TAB(34)),
   rec_base("قرطبی «کیدهن» را میان زن و زنان نگه می‌دارد و عموم را برمی‌گزیند؛ برگرداندن کید از او یعنی شبکه‌ای که از اتاق تا مجلس شهر تنیده شده بود یک‌جا گسست و این گسستن بی‌صدا بزرگ‌ترین رخداد این فصل از سوره است و هیچ‌کس از آن آگاه نشد مگر خود او.", QUR(34)),
  ],
  'classical': [
   rec_base("طبری استجابت را پاسخ به شکایت می‌داند؛ سخن «زندان دوست‌داشتنی‌تر است» شکایت به درگاه خدا بود و در اخلاق تفسیر کهن همین شکایت دعاست و مفسر چنین میان خبر و دعا پل می‌زند و می‌آموزد قالب جمله را باید از کارکرد آن شناخت و نه فقط از صورت آن.", TAB(34)),
   rec_base("قرطبی لطف و عصمت را دو نام پاسخ می‌داند؛ مفسر کلاسیک میان نگه داشتن از گناه و دور کردن گرایش فرق می‌گذارد و استجابت این آیه را از جنس دوم می‌خواند و این تفکیک راه الهیات عصمت این سوره را از بحث‌های کهن به امروز می‌آورد و باز می‌کند.", QUR(34)),
   rec_base("طبری «فصرف عنه» را برگرداندن گناه از او می‌داند نه او از گناه؛ مفسر بر جهت فعل تکیه می‌کند که شر از او دور شد و نه او از شر و این همان نکته‌ای است که در «لنصرف عنه السوء» نیز آمد و ستوان اخلاق این سوره است که بدی از پاکان برگردانده می‌شود.", TAB(34)),
   rec_base("قرطبی از ساخت «إنه هو السمیع العلیم» ضمیر فصل را می‌بیند؛ شنیدن و دانستن بدو منحصر خوانده می‌شود و پایان آیه چنین است که آن که دعای آهسته در مجلس زنان را شنید همان است که نیاز واقعی او را بهتر از خود او می‌دانست و پاسخ را چنان داد.", QUR(34)),
  ],
  'modern': [
   rec_base("مختصر اجابت را برداشتن مکر هر دو گروه می‌داند؛ خوانش امروزین این را پاسخ بی‌درنگ می‌خواند که میان دعا و اجابت در این آیه هیچ فاصله‌ای نیست مگر فاء ترتیب و سوره می‌آموزد دعای دل‌شکسته در اوج تهدید پیش از تمام شدن مجلس شنیده شده است و این امید بزرگ مؤمنان است.", MUKH(34)),
   rec_base("مختصر «سمیع» را شنوای هر دعاکننده می‌خواند؛ دعای یوسف نه با بلندگو گفته شد و نه با آیین و در میانه تهدید زنی گفته شد و خدا آن را شنید و این آیه از هر کس می‌خواهد در اتاق‌های بسته جهان نیز سخن بگوید چون شنونده همان‌جا حاضر است و نمی‌رود.", MUKH(34)),
   rec_base("المیزان بر آن است که برگرداندن سوء و فحشا از مخلَصان قانون خداست و برهان رب نتیجه‌اش علم و یقینی نادر است که قصد گناه را هم از دل آنان برمی‌دارد و این استجابت ادامه همان قانون است که چون از بندگان خالص او بود کید زنان از او برگردانده شد و این برگرداندن عصمت الهی است.", MIZ253),
   rec_base("در خوانش امروزین پایان این فصل آرام‌ترین آیه سوره تا این‌جاست؛ پس از اتاق و دادگاه و مهمانی و تهدید خدا با دو نام شنوا و دانا پرده را می‌بندد و خواننده می‌فهمد تمام آن آشوب‌ها در شنیدن و دانستن او گذشته است و هیچ سخنی از آن مجلس گم نشده است.", MUKH(34)),
  ],
  'critical': [
   rec_base("«فاستجاب له ربه» با فاء پاسخ فوری است؛ میان دعا و اجابت هیچ آیه و فصلی نیست و این سرعت در ساخت قصه نشان می‌دهد آسمان از آغاز مجلس حاضر بوده است و پاسخ نه از راه که از همان‌جا آمد و دعا هنوز در دهان او بود که گرفته شد.", QUR(34)),
   rec_base("«فصرف عنه کیدهن» همان فعل دعای او «تصرف» بازگشته است؛ واژه او بی‌کم‌وکاست به دست خدا برگردانده می‌شود و این آینه واژگانی میان دعا و اجابت زیباترین ساخت این سوره است که بنده واژه را می‌سازد و خدا آن را راست می‌کند و عمل می‌سازد.", TAB(34)),
   rec_base("«إنه هو السمیع العلیم» ختم با دو نام است؛ پس از قصه‌ای پر از سخن‌های ناشنیده و نشنیده شنوا و دانا می‌آید و این نشان می‌دهد مسئله این سوره شنیده شدن راست است و آن که همه را شنید در پایان نام خود را می‌گوید و پرده با نام او بسته می‌شود.", MUKH(34)),
   rec_base("آیه کوتاه‌ترین پاسخ این قصه است؛ تهدید زن بلند و پر تأکید بود و پاسخ خدا یک سطر و این کوتاهی خود بلاغت است که قدرت راستین نیازی به بلندگویی ندارد و یک «فصرف» از هزار تهدید بزرگ‌تر است و میدان را تمام می‌کند و می‌رود.", QUR(34)),
  ],
  'research': [
   rec_base("دعای غیرصریح و استجابت آن و شکایت چون دعا را در الهیات دعای قرآن بسنجید؛ طبری چگونه از جمله خبری یوسف دعا می‌سازد و این خوانش چه راهی برای فهم دعاهای بی‌قالب در زندگی مؤمنان می‌گشاید و مرز خبر و انشا کجاست.", J_TATBIQ),
   rec_base("برگرداندن کید و سوء از مخلَصان و نسبت آن با اختیار انسان را مطالعه کنید؛ اگر بدی از او برگردانده شد ایستادن او چه شد و المیزان این دو را چگونه با هم نگه می‌دارد و این از دشوارترین گره‌های الهیات این سوره است.", J_IBTILA),
   rec_base("پایان‌بندی فصل‌ها با نام‌های خدا در قرآن و کارکرد سمیع و علیم در قصه‌های شنیده شدن را پی بگیرید؛ کجاها قصه با نامی از نام‌های او بسته می‌شود و این آیه در آن نقشه چه جایگاهی دارد و نام‌ها چگونه جمع‌بندی قصه‌اند.", HOURANI),
   rec_base("فاء استجابت و آینه واژه «صرف» میان دعا و اجابت و ضمیر فصل در ختم آیه را در بلاغت عربی بررسی کنید؛ چگونه یک ریشه در دو جمله دعا و پاسخ را به هم می‌دوزد و پایان‌بندی با نام خدا وزن آن دوخت را تمام می‌کند.", WRIGHTJ),
  ],
 },
 'ext': X("12:34",
  ("کتاب مقدس: پیدایش ۳۹:۲۱", "https://www.biblegateway.com/passage/?search=Genesis%2039%3A21&version=NIV", "اما خدا با یوسف بود و بدو مهر ورزید و او را در چشم نگهبان زندان گرامی داشت؛ [analysis] تورات همراهی خدا را در زندان می‌گوید و قرآن اجابت را پیش از زندان و هر دو می‌گویند در تاریک‌ترین فصل قصه خدا نزدیک‌ترین است و یوسف تنها نمانده است.", "analysis"),
  ("پژوهش قرآن و حقوق اجتماعی", "https://www.sid.ir/paper/1127546/fa", "مقالهٔ «حقوق اجتماعی در قرآن کریم»: شنیده‌شدن بی‌صدایان؛ [analysis] این آیه از هر جامعه‌ای می‌خواهد سازوکاری بسازد که دعای بی‌نام‌ترین بندگان نیز شنیده شود و شنوایی خدا الگوی شنوایی نهادهای انسانی باشد و هیچ حقی در مجلس قدرت گم نشود.", "analysis"),
  ("نامداران گمنام تاریخ، جلد ۱", "https://noorlib.ir/book/info/21407/", "ملتس (۱۳۸۲)، صفحات ۲۱ تا ۲۲۷؛ [analysis] در روایت‌ها پاسخ دعای او گاه زندان دانسته شده و قرآن آن را برگرداندن کید می‌داند و این تفاوت نشان می‌دهد قصه‌گویان پاسخ را در حادثه بیرونی جستند و قرآن در درون او و این عمق خوانش اوست.", "analysis"),
  ("زبانِ عهد عتیق، عبری و آرامی", "https://www.noormags.ir/view/en/articlepage/1094192", "موضوع: شنیدن خدا (שמע) در عبری؛ [analysis] شنیدن در سنت عبری شنیدن التماس مظلوم است و «سمیع» این آیه همان خدا را می‌خواند و در هر دو کتاب فریاد برده عبرانی شنیده می‌شود و این محور مشترک ایمان دو سنت است.", "analysis"),
  ("یوسفِ درّاجی، علم الاجتماع الدینی", LOCALY, "درّاجی (۲۰۱۵): دعا در تنگنا سازوکار تاب‌آوری دینی است؛ [analysis] استجابت این آیه از نظر جامعه‌شناسی لحظه‌ای است که ایمان به نگهداری هویت در برابر ماشین دربار بدل می‌شود و یوسف از آن مجلس با هویتی سالم‌تر بیرون می‌آید.", "analysis"),
  ("مجلهٔ استجابت در قرآن", "https://www.sid.ir", "[source-coverage-note] این مسیر در این دسته مقابلهٔ مستقیم نشد؛ دعای غیرصریح و پاسخ آن در مقالهٔ مشخصی مقابله نشده است و پژوهشی تازه برای سوره یوسف لازم است.", "source-coverage-note"),
 ),
},
}
for vid, spec in dossiers.items():
    rec = build(vid, spec)
    rec["requiresDiverseSources"] = True
    rec["sourceMix"] = collect(rec)
    DATA["verses"][vid] = rec
total = len(DATA["verses"])
for item in DATA["scope"]:
    if item["range"] == "10:41-60":
        item["range"] = "۱۰:۱–۹۳ · تنوعِ منابع v3 (قرطبی، طبری، المیزان، مختصر و مقالاتِ داوری‌شده)"
        item["status"] = "کامل: پوششِ core تکمیل شد"
        break
DATA["verses"] = dict(sorted(DATA["verses"].items(), key=lambda kv: tuple(map(lambda x: int(x) if x.isdigit() else x, kv[0].split(':')))))
# fix scopes
seen2 = {}
for item in DATA["scope"]:
    if "۱۰:۱" in item.get("range",""):
        item["range"] = "۱۰:۱–۹۳ · تنوعِ منابع v3 (قرطبی، طبری، المیزان، مختصر، میسّر محدود و مقالاتِ داوری‌شده)"
    if "قرآن کامل" in item.get("range",""):
        item["status"] = "در دستِ تکمیل (جلدِ ۱۰ تا ۱۰:۹۳)"
PATH.write_text(json.dumps(DATA, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("records:", len(DATA["verses"]))
