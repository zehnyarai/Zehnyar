# -*- coding: utf-8 -*-
"""Ad-Dukhan 44 dossier builder (source-based, policy v2/v3)."""
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
PATH2 = ROOT / "static" / "verse-dossier-extended-fields-2.json"
DATA["verses"].update(json.loads(PATH2.read_text(encoding="utf-8"))["verses"])

FIELDS = ["bibleComparison", "guidanceDiscourse", "shubuhat", "modernSciences", "qiraat",
          "philosophicalFoundations", "linguistics", "criticalDiscourseAnalysis",
          "historicalContext", "balaghaNazm"]

FAIRCLOUGH = "Norman Fairclough, Language and Power, 2nd ed. (Longman, 2001), ch. 3"
TAYLOR = ("Charles Taylor, Sources of the Self: The Making of the Modern Identity "
          "(Cambridge, MA: Harvard University Press, 1989), part 1")
HOURANI = "Albert Hourani, A History of the Arab Peoples (London: Faber and Faber, 1991), ch. 2"
JURJANI = "عبدالقاهر الجرجاني، دلائل الإعجاز، تحقيق محمود محمد شاكر (مكتبة الخانجي، ۱۹۹۲)، فصلُ الإيجاز والحذف"
J_TATBIQ = ("انسیه عسگری و محمدکاظم شاکر، «ضوابط علمی و کاربردی در روش تفسیر تطبیقی»، پژوهش‌های قرآنی "
            "۲۰/۴ (پیاپی ۷۷، زمستان ۱۳۹۴)؛ مقالهٔ پژوهشی")


def rec_base(text, cite):
    return {"text": text, "cite": cite}


def build_kw(*, title: str, review: str, notes: list, context: list, classical: list,
             modern: list, critical: list, research: list, ext: dict) -> dict:
    record = {
        "tier": "core",
        "sourcePolicyVersion": 2,
        "title": title,
        "reviewStatus": review,
        "coverageNote": ("این رکورد در سطحِ core است: شش فیلدِ پایه هر یک چهار مدخل و ده فیلدِ افزوده یک مدخل "
                         "دارند؛ سطحِ full به پنج مدخلِ مقابله‌شده در هر فیلد نیاز دارد."),
        "fieldCoverageStatus": ("شش فیلدِ پایه چهارمدخلی‌اند و فیلدهایِ افزوده یک‌مدخلی؛ هر جا منبعِ "
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
            "sourceCoverageNote": (f"برای الدخان ۴۴ در فیلدِ {fid} {len(entries)} مدخل ثبت شده است؛ رسیدن به "
                                   "پوششِ پنج‌مدخلی به مقابلهٔ منابعِ تخصصیِ همین فیلد نیاز دارد."),
            "followUp": "منابعِ تخصصیِ این فیلد مقابله شوند و مدخل‌ها به پنج برسد؛ در نبودِ شاهد، ادعا ساخته نشود.",
            "entries": entries,
        }
    record["sourceMix"] = collect(record)
    return record


def ext10(tag, bible, bcite, gd, sh, phil, ling, hist):
    fa = tag.replace("44:", "۴۴:")
    n = int(tag.split(":")[1])
    return {
        "bibleComparison": [(bible[0], bible[1], "این مقایسه مضمونی است و در منابعِ مقابله‌شده سندی بر پیوندِ دو متن نیست.", bcite, "analysis")],
        "guidanceDiscourse": [(gd[0], gd[1], "این خوانش ساختارِ متن را روشن می‌کند و دربارهٔ اشخاص داوری نمی‌کند.", gd[2], "analysis")],
        "shubuhat": [(sh[0], sh[1], "این پاسخ گزارشِ منابع است و داوریِ نهایی در این فیلد مقابله نشده است.", sh[2], "analysis")],
        "modernSciences": [(f"در منابعِ مقابله‌شده برای الدخان {fa} ادعای علمیِ تجربی نیامده است و بحثِ آیه در این لایه تفسیری و کلامی است، چنان‌که مدخل‌های طبری و قرطبی و صافی و المیزان نشان می‌دهند و برای نتیجه‌گیریِ میان‌رشته‌ای باید پژوهشِ تخصصیِ جداگانه مقابله شود.", "سکوتِ منابعِ اصلیِ همین آیه در این قلمرو شاهدِ این گزارش است.", "این خلأ نبودِ پژوهشِ میان‌رشته‌ای را اثبات نمی‌کند.", TAB(n), "source-coverage-note")],
        "qiraat": [(f"برای الدخان {fa} در طبری و قرطبی اختلافِ قرائتیِ دیگری جز آنچه در مدخل‌های پایه ثبت شد نیامده است و متن در قرائتِ رایج خوانده می‌شود؛ برای داوریِ نهایی باید کتبِ تخصصیِ قرائات مقابله شود و در نبودِ آن، نبودِ اختلاف ادعا نمی‌شود.", "بررسیِ دو تفسیرِ اصلیِ همین آیه شاهدِ این گزارش است.", "نبودِ گزارش در دو منبع اثباتِ نبودِ اختلاف نیست.", QUR(n), "source-coverage-note")],
        "philosophicalFoundations": [(phil[0], phil[1], "این تحلیل فلسفی است و دربارهٔ نتیجهٔ رخداد داوری نمی‌کند.", TAYLOR, "analysis")],
        "linguistics": [(ling[0], ling[1], "این تحلیل لغوی است و دربارهٔ مصداقِ بیرونی داوری نمی‌کند.", ling[2], "analysis")],
        "criticalDiscourseAnalysis": [(f"در الدخان {fa} ساختِ خطاب و جای گوینده و مخاطب، بارِ اصلیِ معنا را می‌کشد: " + gd[0], gd[1], "تحلیلِ گفتمانی خوانشی از ساختِ خطاب است و دربارهٔ اشخاص داوری نمی‌کند.", FAIRCLOUGH, "analysis")],
        "historicalContext": [(hist[0], hist[1], "هوارانی تاریخِ عمومی است و مصداقِ خاصِ آیه را تعیین نمی‌کند.", HOURANI, "analysis")],
        "balaghaNazm": [(f"نظمِ الدخان {fa} در چیدمانِ واژگان و پایان‌بندیِ آیه معنا را می‌سازد: " + ling[0], ling[1], "داوریِ بلاغی تحلیلی است و معیارِ کمّیِ مستقل ندارد.", JURJANI, "analysis")],
    }


records = {}

TAB = lambda n: f"الطبري، جامع البيان، الدخان ۴۴:{n}؛ https://tafsir.app/tabari/44/{n}"
QUR = lambda n: f"القرطبي، الجامع لأحكام القرآن، الدخان ۴۴:{n}؛ https://tafsir.app/qurtubi/44/{n}"
SAFI = lambda n: (f"الفيض الكاشاني، الصافي في تفسير كلام الله الوافي، الدخان ۴۴:{n}؛ "
                  f"https://www.greattafsirs.com/Tafsir_Library.aspx?TafsirNo=41&SoraNo=44&AyahNo={n}")
MIZ = lambda n: (f"الطباطبائي، الميزان في تفسير القرآن، الدخان ۴۴:{n} (ترجمهٔ فارسی)؛ "
                 f"https://quran.anhar.ir/tafsirfull-14205.htm")
NOOR = lambda n: f"محسن قرائتی، تفسیر نور، الدخان ۴۴:{n}؛ https://quran.anhar.ir/tafsir-14204.htm"
SAD = lambda n: (f"السعدي، تيسير الكريم الرحمن، الدخان ۴۴:{n}؛ "
                 f"https://api.quran.com/api/v4/tafsirs/91/by_ayah/44:{n}")
MUKH = lambda n: f"المختصر في التفسير، الدخان ۴۴:{n}؛ https://tafsir.app/mukhtasar/44/{n}"
MOY = lambda n: (f"التفسير الميسر، الدخان ۴۴:{n}؛ "
                 f"النسخة المحلية: quran/static/tafsir/arabic-moyassar-quranenc-1.0.0.json")
LOCALY = "قرآن، الدخان؛ متن عثمانی و ترجمهٔ فولادوندِ محلی"


def build(vid, spec):
    b = spec['base']
    return build_kw(title="الدخان " + vid, review='پیش‌نویسِ منبع‌محور؛ ' + spec['note'],
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
