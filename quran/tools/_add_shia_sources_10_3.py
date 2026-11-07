# -*- coding: utf-8 -*-
"""Complete the diversity policy for Yunus 10:3.

Adds Tafsir Nemuneh's reading (yawm = period, 'arsh = power, tadbir from dubur)
and a peer-reviewed comparative article on 'arsh/istiwa' across the madhhabs,
then flags the record so the v3 rule (Sunni + Shia + journal) is enforced.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from source_policy import POLICY, collect  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "static" / "verse-dossier-extended-fields.json"
DATA = json.loads(PATH.read_text(encoding="utf-8"))
VERSE = DATA["verses"]["10:3"]

NEM10 = ("مكارم الشيرازي، تفسير نمونه (Tafsir e Namoona، برگردانِ انگلیسی)، ذیلِ يونس ۱۰:۳–۴؛ "
         "https://www.tafseerenamoona.net/surahs/10")
KHOSHFAR = ("محسن خوش‌فر و مینا ابراهیم، «گفتمان تفاسیر مذاهب اسلامی در تحلیل عرش و استواء بر آن»، مطالعات "
            "تقریبی مذاهب اسلامی (فروغ وحدت) ۲۰/۶۳ (۱۴۰۴)، شمارهٔ مقاله e204097؛ "
            "https://foroughevahdat.mazaheb.ac.ir/article_204097.html")


def add(field: str, items: list[tuple[str, str]]) -> None:
    for text, cite in items:
        assert all(existing["text"] != text for existing in VERSE[field]), field
        VERSE[field].append({"text": text, "cite": cite})


add("modern", [
    ("«تفسیر نمونه» «یوم» را در «ستة أيام» به معنای دوره و عصر می‌گیرد، نه لزوماً شبانه‌روزِ بیست‌وچهارساعتی، "
     "و به کاربردِ عرفیِ «روزگار» در فارسی و عربی استناد می‌کند؛ بنابراین شش روز را شش دورهٔ آفرینش "
     "می‌شمارد.", NEM10),
    ("«تفسیر نمونه» معنای اصلیِ «عرش» را «قدرت» می‌داند و «استوى على العرش» را «به دست گرفتنِ تدبیرِ امورِ "
     "جهان» تفسیر می‌کند، نه نشستن بر تخت؛ این خوانش در کنارِ «استواء يليق بعظمته» در سعدی و سکوتِ طبری سه "
     "موضعِ متفاوت می‌سازد.", NEM10),
    ("«تفسیر نمونه» «تدبیر» را از ریشهٔ «دُبُر» به معنای پشت و پایانِ کار می‌داند: نگریستن در فرجامِ امور و "
     "سامان‌دادن به آن‌ها بر پایهٔ سود؛ و بر همین پایه نتیجه می‌گیرد که بتانِ بی‌جان هیچ سهمی در سرنوشتِ "
     "انسان ندارند.", NEM10),
])
add("critical", [
    ("سه موضعِ مقابله‌شده را نباید در هم آمیخت: طبری توضیحِ «استوى» را به مواضعِ پیشین حواله می‌دهد، سعدی "
     "آن را «استواء يليق بعظمته» می‌خواند و نمونه آن را به «قدرت» و تدبیر برمی‌گرداند؛ هر سه ثبت می‌شوند و "
     "داوریِ نهایی به پژوهشِ کلامیِ مستقل واگذار می‌شود.", f"{NEM10}؛ {KHOSHFAR}"),
])
add("research", [
    ("خوش‌فر و ابراهیم در «گفتمان تفاسیر مذاهب اسلامی در تحلیل عرش و استواء بر آن» مواضعِ مذاهب را کنارِ هم "
     "می‌نشانند و نشان می‌دهند اختلاف بر سرِ «استواء» بیشتر اختلافِ چارچوبِ کلامی است تا اختلافِ نقل؛ همین "
     "مقاله می‌تواند سه‌گانهٔ طبری، سعدی و نمونه را در یک جدولِ گفتمانی بنشاند.", KHOSHFAR),
])

VERSE["requiresDiverseSources"] = True
VERSE["sourceMix"] = collect(VERSE)

DATA["criteria"].update(POLICY)
scope = {item["range"]: item for item in DATA["scope"]}
scope["10:3"]["status"] = (
    "۱۰:۳ در سطحِ core ثبت شد: استدلالِ طبری از آفرینش به توحیدِ عبادی، خبرِ مجاهد «يقضيه وحده»، شرحِ سعدی "
    "بر «تدبير الأمر» و قیدِ «اذن»، خوانشِ تفسیر نمونه (یوم = دوره، عرش = قدرت، تدبیر از «دُبُر») و مقالهٔ "
    "داوری‌شدهٔ خوش‌فر و ابراهیم دربارهٔ گفتمانِ مذاهب در «عرش و استواء». سیاستِ v3 برای این آیه کامل شد.")
scope["10:1–2 · منابعِ شیعی و مقالات"]["range"] = "۱۰:۱–۳ · تنوعِ منابع v3"
scope["10:1–2 · منابعِ شیعی و مقالات"]["status"] = (
    "سیاستِ تنوعِ v3 از ۱۰:۱ اجرا می‌شود و ۱۰:۱، ۱۰:۲، ۱۰:۳ و ۱۱:۱ آن را برآورده‌اند: هر رکورد دست‌کم یک "
    "تفسیرِ کهن، یک منبعِ معاصر، یک منبعِ شیعی، یک منبعِ سنّی و یک مقالهٔ پژوهشیِ داوری‌شده دارد. همین قاعده "
    "برای همهٔ آیات تا پایانِ قرآن ادامه می‌یابد و رکوردهایِ پیشینِ توبه به‌تدریج پر می‌شوند؛ ادعای "
    "کامل‌بودن نمی‌شود.")

PATH.write_text(json.dumps(DATA, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("10:3 mix:", sorted({(m["work"], m["role"]) for m in VERSE["sourceMix"]}))
