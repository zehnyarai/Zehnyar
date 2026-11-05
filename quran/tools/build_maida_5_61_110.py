#!/usr/bin/env python3
"""Build source-linked draft dossiers for Al-Ma'idah 5:61–110."""
from __future__ import annotations

import json
from pathlib import Path

import build_nisa_4_1_12 as shared
import maida_5_61_110_data as curated

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
DOSSIER_PATH = STATIC / "verse-dossiers.json"
CATALOG_PATH = STATIC / "tafsir-catalog.json"
REGISTRY_PATH = STATIC / "tafsir-sources.json"
BATCH_ID = "dossier-57"
COLLECTION_ID = "maida-5-61-110-cited"
VERSES = tuple(range(61, 111))
TABARI = "ar_tabari_qurancom"
IBN = "ar_ibn_kathir_qurancom"
QURTUBI = "ar_qurtubi_qurancom"
JALALAYN = "ar_jalalayn_qurancom"
TUSI = "ar_tusi_tibyan"
FAYD = "ar_fayd_safi"
QURANENC = "ar_qe_arabic_moyassar"
WASIT = "ar_wasit_qurancom"
SUNNI = {TABARI, IBN, QURTUBI}
SHIA = {TUSI, FAYD}
MODELS = {"izutsu", "fillmore", "cognitive"}
SOURCE_ORDER = (TABARI, IBN, QURTUBI, JALALAYN, TUSI, FAYD, QURANENC, WASIT)

# GreatTafsirs displays these al-Safi passages at a grouped-verse route.
FAYD_GROUPS: dict[int, tuple[int, int, int]] = {}
for first, last, page in (
    (61, 64, 61),
    (65, 67, 67),
    (68, 69, 68),
    (70, 75, 70),
    (76, 80, 76),
    (81, 85, 81),
    (86, 87, 86),
    (88, 89, 88),
    (90, 91, 90),
    (92, 93, 92),
    (94, 95, 94),
    (96, 101, 96),
    (102, 105, 104),
    (106, 108, 106),
    (109, 113, 109),
):
    for verse in range(max(first, 61), min(last, 110) + 1):
        FAYD_GROUPS[verse] = (page, first, last)
# The first in-scope verse is embedded in al-Safi's preceding 5:60–64 passage.
FAYD_GROUPS[61] = (61, 60, 64)

# Most al-Tibyan routes address one verse. These exceptions were checked:
# 5:89 has two chunks, 5:101–102 share the AyahNo=101 group page,
# and 5:110 has two chunks; both chunks for 5:110 were retrieved.
TUSI_GROUPS: dict[int, tuple[int, int, int, tuple[int, ...]]] = {
    verse: (verse, verse, verse, ()) for verse in VERSES
}
TUSI_GROUPS[89] = (89, 89, 89, (0, 1))
TUSI_GROUPS[101] = (101, 101, 102, (0,))
TUSI_GROUPS[102] = (101, 101, 102, (0,))
TUSI_GROUPS[110] = (110, 110, 110, (0, 1))

SECTIONS = (
    (61, 71, "میثاق، نافرمانی و گفتارهایِ اعتقادیِ اهلِ کتاب"),
    (72, 77, "نقدِ الوهیتِ مسیح و دعوت به توحید"),
    (78, 81, "روایتِ بنی‌اسرائیل و مسئولیتِ اجتماعی"),
    (82, 86, "گفت‌وگویِ نصارا، شنیدنِ وحی و فرجامِ ایمان"),
    (87, 93, "طیبات، سوگند، خمر و تقوا"),
    (94, 100, "صید، حرمتِ حرم، داوری و ارزشِ طیب"),
    (101, 105, "ادبِ پرسش، نقدِ رسومِ ساختگی و مسئولیتِ فردی"),
    (106, 108, "شهادت و حفاظت از وصیت در سفر"),
    (109, 110, "صحنهٔ قیامت و یادکردِ نعمت‌هایِ عیسی"),
)

SOURCE_NAMES = {
    TABARI: "طبری",
    IBN: "ابن‌کثیر",
    QURTUBI: "قرطبی",
    JALALAYN: "جلالین",
    TUSI: "طوسی",
    FAYD: "فیض کاشانی",
    QURANENC: "التفسير الميسر",
    WASIT: "طنطاوی",
}


def fa_num(value: int) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def quran(verse: int, span: tuple[int, int] | None = None) -> str:
    if span is None:
        scope = f"۵:{fa_num(verse)}"
    else:
        scope = f"۵:{fa_num(span[0])}–{fa_num(span[1])}"
    return f"قرآن، مائده {scope}؛ متنِ عربی و ترجمهٔ فولادوند/Tanzil در پیکرهٔ برنامه."


def greattafsirs_url(tafsir_no: int, ayah_no: int) -> str:
    return (
        "https://www.greattafsirs.com/Tafsir_Library.aspx?FromMainTafsir=1"
        f"&MadhabNo=4&TafsirNo={tafsir_no}&SoraNo=5&AyahNo={ayah_no}&LanguageID=1"
    )


def tusi_scope(verse: int) -> str:
    _, start, end, _ = TUSI_GROUPS[verse]
    if start == end:
        return f"۵:{fa_num(start)}"
    return f"۵:{fa_num(start)}–{fa_num(end)}"


def fayd_scope(verse: int) -> str:
    _, start, end = FAYD_GROUPS[verse]
    return f"۵:{fa_num(start)}–{fa_num(end)}"


def tabari(verse: int) -> str:
    return (
        f"طبری، ۳۱۰ق، *جامع البيان عن تأويل آي القرآن*، ذیلِ مائده ۵:{fa_num(verse)}؛ "
        "صفحهٔ آیه‌محورِ Quran.com؛ چاپ و صفحهٔ کتاب احراز نشده."
    )


def ibn(verse: int) -> str:
    return (
        f"ابن‌کثیر، ۷۷۴ق، *تفسير القرآن العظيم*، ذیلِ مائده ۵:{fa_num(verse)}؛ "
        "صفحهٔ آیه‌محورِ Quran.com؛ چاپ و صفحهٔ کتاب احراز نشده."
    )


def qurtubi(verse: int) -> str:
    return (
        f"قرطبی، ۶۷۱ق، *الجامع لأحكام القرآن*، ذیلِ مائده ۵:{fa_num(verse)}؛ "
        "صفحهٔ آیه‌محورِ Quran.com؛ چاپ و صفحهٔ کتاب احراز نشده."
    )


def jalalayn(verse: int) -> str:
    return (
        f"محلی، ۸۶۴ق، و سیوطی، ۹۱۱ق، *تفسير الجلالين*، ذیلِ مائده ۵:{fa_num(verse)}؛ "
        "صفحهٔ آیه‌محورِ Quran.com؛ چاپ و صفحهٔ کتاب احراز نشده."
    )


def tusi(verse: int) -> str:
    page, start, end, chunks = TUSI_GROUPS[verse]
    kind = "مستقیم" if start == end else "گروهی"
    chunk_note = "؛ قطعه‌هایِ ۰ و ۱ بررسی شدند" if chunks == (0, 1) else ""
    return (
        f"طوسی، ۴۶۰ق، *التبيان الجامع لعلوم القرآن*، شرحِ {kind}ِ مائده {tusi_scope(verse)}؛ "
        f"GreatTafsirs، صفحهٔ AyahNo={page}{chunk_note}؛ چاپ و صفحهٔ کتاب احراز نشده."
    )


def fayd(verse: int) -> str:
    page, _, _ = FAYD_GROUPS[verse]
    return (
        f"فیض کاشانی، ۱۰۹۰ق، *الصافي في تفسير كلام الله الوافي*، شرحِ گروهیِ مائده {fayd_scope(verse)}؛ "
        f"GreatTafsirs، صفحهٔ AyahNo={page}؛ چاپ و صفحهٔ کتاب احراز نشده."
    )


def moyassar(verse: int) -> str:
    return (
        f"التفسير الميسر، قرآن‌انک، نسخهٔ 1.0.0، ذیلِ مائده ۵:{fa_num(verse)}؛ "
        "متنِ محلیِ آیه‌به‌آیه."
    )


def wasit(verse: int) -> str:
    return (
        f"محمد سید طنطاوی، *التفسير الوسيط للقرآن الكريم*، شرحِ مائده ۵:{fa_num(verse)}؛ "
        f"Quran.com، مسیرِ آیه‌محورِ ۵:{fa_num(verse)}؛ چاپ و صفحهٔ کتاب احراز نشده."
    )


def source_url(source_id: str, verse: int) -> str:
    if source_id in {TABARI, IBN, QURTUBI, JALALAYN, WASIT}:
        slug = {
            TABARI: "ar-tafsir-al-tabari",
            IBN: "ar-tafsir-ibn-kathir",
            QURTUBI: "ar-tafsir-al-qurtubi",
            JALALAYN: "ar-tafsir-jalalayn",
            WASIT: "ar-tafsir-al-wasit",
        }[source_id]
        return f"https://quran.com/al-maidah/{verse}/tafsirs/{slug}"
    if source_id == TUSI:
        page, _, _, _ = TUSI_GROUPS[verse]
        return greattafsirs_url(39, page)
    if source_id == FAYD:
        page, _, _ = FAYD_GROUPS[verse]
        return greattafsirs_url(41, page)
    if source_id == QURANENC:
        return "https://quranenc.com/en/browse/arabic_moyassar"
    raise KeyError(source_id)


def source_cite(source_id: str, verse: int) -> str:
    return {
        TABARI: tabari,
        IBN: ibn,
        QURTUBI: qurtubi,
        JALALAYN: jalalayn,
        TUSI: tusi,
        FAYD: fayd,
        QURANENC: moyassar,
        WASIT: wasit,
    }[source_id](verse)


def source_evidence(source_id: str, verse: int) -> str:
    if source_id in {TABARI, IBN, QURTUBI, JALALAYN}:
        return (
            f"متنِ عربیِ آیه‌محورِ ثبت‌شده برایِ مائده ۵:{fa_num(verse)} بررسی شد؛ "
            "خلاصه به همان موضع محدود است و چاپِ کتاب از مسیرِ برخط احراز نشده."
        )
    if source_id == TUSI:
        page, _, _, chunks = TUSI_GROUPS[verse]
        chunk_note = (
            "؛ قطعه‌هایِ ۰ و ۱ خوانده شدند"
            if chunks == (0, 1)
            else "؛ قطعهٔ ۰ از صفحهٔ گروهی بررسی شد"
            if verse in {101, 102}
            else ""
        )
        return (
            f"GreatTafsirs، AyahNo={page}؛ دامنهٔ شرحِ طوسی مائده {tusi_scope(verse)} است؛ "
            f"فقط موضعِ آیهٔ هدف خلاصه شد{chunk_note}؛ چاپ و صفحهٔ کتاب احراز نشده."
        )
    if source_id == FAYD:
        page, _, _ = FAYD_GROUPS[verse]
        return (
            f"GreatTafsirs، AyahNo={page}؛ دامنهٔ واقعیِ شرحِ فیض مائده {fayd_scope(verse)} است؛ "
            f"فقط موضعِ ۵:{fa_num(verse)} خلاصه شد؛ چاپ و صفحهٔ کتاب احراز نشده."
        )
    if source_id == QURANENC:
        return (
            f"متنِ محلیِ قرآن‌انک برایِ مائده ۵:{fa_num(verse)} از نسخهٔ 1.0.0 بررسی شد؛ "
            "خلاصه نقلِ لفظی نیست."
        )
    if source_id == WASIT:
        return (
            f"خلاصه بر پایهٔ متنِ عربیِ گردآوری‌شده برایِ مائده ۵:{fa_num(verse)} است؛ "
            "مسیرِ مستقیمِ Quran.com درج شده، اما عنوان و بدنهٔ آن در این نوبت جداگانه مقابله نشده‌اند."
        )
    raise KeyError(source_id)


def source_item(source_id: str, verse: int, text: str) -> dict:
    return {
        "text": text,
        "cite": source_cite(source_id, verse),
        "kind": "source-summary",
        "language": "fa",
        "sourceId": source_id,
        "sourceUrl": source_url(source_id, verse),
        "evidence": source_evidence(source_id, verse),
        "limit": shared.SOURCE_LIMIT,
        "tradition": shared.SOURCE_TRADITIONS.get(source_id, "اهل‌سنت"),
    }


def editorial_item(text: str, cite: str, verse: int, field: str, evidence: str | None = None) -> dict:
    return {
        "text": text,
        "cite": cite,
        "kind": shared.FIELD_KIND[field],
        "language": "fa",
        "evidence": evidence or f"شاهدِ متنی: مائده ۵:{fa_num(verse)}؛ بند به ارجاع و دامنهٔ ثبت‌شده محدود است.",
        "limit": shared.EDITORIAL_LIMIT,
    }


def source_note_item(verse: int, note: tuple[str, str, str]) -> dict:
    focus, text, source_id = note
    return {
        "text": (
            f"{focus}: {text} این نکته به همان مفسر منسوب است و به‌تنهایی اجماعِ تفسیری یا واقعیتِ مستقل را اثبات نمی‌کند."
        ),
        "cite": source_cite(source_id, verse),
        "kind": "editorial-inference",
        "language": "fa",
        "sourceId": source_id,
        "sourceUrl": source_url(source_id, verse),
        "evidence": source_evidence(source_id, verse),
        "limit": "این یادداشت بازگوییِ منسوب به شرحِ یادشده است، نه نقلِ لفظی و نه جمع‌بندیِ اجماعی.",
        "tradition": shared.SOURCE_TRADITIONS.get(source_id, "اهل‌سنت"),
    }


def model_item(model: str, text: str, verse: int) -> dict:
    citations = {
        "izutsu": (
            f"توشیهیکو ایزوتسو، *God and Man in the Koran: Semantics of the Koranic Weltanschauung*, 1964؛ "
            f"کاربستِ محدود بر مائده ۵:{fa_num(verse)}."
        ),
        "fillmore": (
            f"Charles J. Fillmore, “Frame Semantics,” in *Linguistics in the Morning Calm*, 1982; "
            f"limited application to al-Ma'idah 5:{verse}."
        ),
        "cognitive": (
            f"جورج لیکاف و مارک جانسون، *Metaphors We Live By*, 1980؛ "
            f"کاربستِ محدودِ معناشناسیِ شناختی بر مائده ۵:{fa_num(verse)}."
        ),
    }
    return {
        "text": text,
        "cite": citations[model],
        "kind": "editorial-method-application",
        "language": "fa",
        "model": model,
        "evidence": f"شاهدِ متنی: مائده ۵:{fa_num(verse)}؛ کاربردِ محدودِ چارچوب در سطحِ واژگان و ساختارِ همین آیه.",
        "limit": "این کاربردِ تحریریِ چارچوب است، نه ادعای آنکه نظریه‌پرداز آیه را مستقلاً تفسیر کرده باشد.",
    }


def section_for(verse: int) -> tuple[int, int, str]:
    for start, end, title in SECTIONS:
        if start <= verse <= end:
            return start, end, title
    raise KeyError(verse)


def context_items(
    verse: int,
    record: dict,
    previous_title: str,
    next_record: dict | None,
) -> list[dict]:
    start, end, section_title = section_for(verse)
    following = verse + 1
    if next_record is None:
        next_title = "ادامهٔ گفت‌وگو دربارهٔ حواریون و عیسی در آیاتِ بعد"
    else:
        next_title = next_record["title"]
    first_focus = record["notes"][0][0]
    first_summary = record["notes"][0][1]
    last_focus = record["notes"][-1][0]
    last_summary = record["notes"][-1][1]
    grouped_page = (
        f"طوسی در شناسهٔ صفحهٔ {TUSI_GROUPS[verse][0]} شرحِ {tusi_scope(verse)} را دارد؛ "
        f"فیض در شناسهٔ صفحهٔ {FAYD_GROUPS[verse][0]} شرحِ {fayd_scope(verse)} را دارد."
    )
    texts = [
        (
            f"در توالیِ مائده ۵:{fa_num(verse - 1)}–{fa_num(verse)}، عنوانِ آیهٔ پیشین «{previous_title}» است و آیهٔ حاضر با محورِ «{record['title']}» ادامه می‌یابد؛ "
            f"این پیوندِ ساختاری است، نه گزارشِ سببِ نزول."
        ),
        (
            f"لنگرِ سیاقیِ این پرونده چنین است: {record['context_anchor']}. "
            f"عبارتِ «{first_focus}» در همین مسیرِ گفتاری خوانده می‌شود؛ {first_summary}"
        ),
        (
            f"در ادامهٔ نزدیک، مائده ۵:{fa_num(following)} به «{next_title}» می‌رسد؛ "
            f"مقایسهٔ دو آیه کمک می‌کند گذارِ موضوعیِ ۵:{fa_num(verse)} را بدونِ بریدن از سیاقِ پیرامون بخوانیم."
        ),
        (
            f"مائده ۵:{fa_num(verse)} با عنوانِ «{record['title']}» در بخشِ {fa_num(start)}–{fa_num(end)}، «{section_title}»، قرار دارد؛ "
            "این محدوده برایِ سازمان‌دهیِ مطالعه است و ادعایِ وحدتِ سببِ نزول یا تاریخ‌گذاریِ مستقل ندارد."
        ),
        (
            f"برایِ پیوندِ شرح با دامنهٔ واقعیِ منبع، «{last_focus}» را در محدودهٔ مشخص‌شده نگه دارید: "
            f"{last_summary} {grouped_page}"
        ),
    ]
    cites = [
        quran(verse, (verse - 1, verse)),
        quran(verse),
        quran(verse, (verse, following)),
        quran(verse, (start, end)),
        source_cite(record["notes"][-1][2], verse) + "؛ مقابله با " + tusi(verse) + " و " + fayd(verse),
    ]
    return [
        editorial_item(
            text,
            cite,
            verse,
            "context",
            evidence=f"شاهدِ متنی: مائده ۵:{fa_num(verse)} و بازهٔ پیوندیِ ثبت‌شده؛ این بند تحلیلِ سیاقیِ تحریری است.",
        )
        for text, cite in zip(texts, cites)
    ]


def critical_items(verse: int, record: dict) -> list[dict]:
    notes = record["notes"]
    n0, n1, n2, n3, n4 = notes
    modern = record["modern_sources"]

    def attributed_body(note: tuple[str, str, str]) -> str:
        author = SOURCE_NAMES[note[2]]
        prefix = author + " "
        body = note[1][len(prefix):] if note[1].startswith(prefix) else note[1]
        for reporting_verb in ("می‌گوید ", "تصریح می‌کند ", "توضیح می‌دهد "):
            if body.startswith(reporting_verb):
                body = body[len(reporting_verb):]
                break
        return body.rstrip().rstrip(".؛،").rstrip()
    source2_id = n2[2]
    if verse == 105:
        source2_name = "جلالینِ جایگزین"
        source2_limit = "شرحِ قرطبی برایِ این آیه در آرشیوِ بررسی‌شده قابلِ استفاده نبود"
    else:
        source2_name = SOURCE_NAMES[source2_id]
        source2_limit = "شرحِ ثبت‌شده برایِ همین آیه در پرونده موجود است"
    group_note = (
        f"در ۵:{fa_num(verse)} («{record['title']}»)، صفحهٔ طوسی با شناسهٔ {TUSI_GROUPS[verse][0]} دامنهٔ {tusi_scope(verse)} دارد؛ "
        f"صفحهٔ فیض با شناسهٔ {FAYD_GROUPS[verse][0]} دامنهٔ {fayd_scope(verse)} دارد. "
        "ارجاعِ گروهی را با شرحِ مستقلِ یک آیه اشتباه نگیرید."
    )
    if verse == 105:
        final = (
            "برایِ مائده ۵:۱۰۵، شرحِ قابلِ استفادهٔ قرطبی در آرشیوِ این کار پیدا نشد و نقلِ او عمداً حذف شده است؛ "
            "جلالین فقط جایگزینِ منبعِ سومِ اهل‌سنت است و این استثنا را نباید به آیاتِ دیگر تعمیم داد."
        )
        final_cite = jalalayn(verse) + "؛ خلأِ قرطبی در آرشیوِ بررسی‌شده ثبت شد."
    else:
        final = (
            f"نکتهٔ «{n4[0]}» در {SOURCE_NAMES[n4[2]]} به همان مفسر و دامنهٔ گزارش‌شده منسوب است؛ "
            "بدونِ مقابلهٔ مستقلِ سند، چاپ یا شواهدِ بیرونی، آن را اجماع یا واقعیتِ تاریخیِ قطعی معرفی نکنید."
        )
        final_cite = source_cite(n4[2], verse)
    final += " مرزِ نقل، تفسیرِ مفسر و ارزیابیِ تحریری را جدا نگه دارید."
    second_critical = (
        (
            f"ابن‌کثیر در «{n1[0]}» می‌گوید {attributed_body(n1)}؛ دربارهٔ «{n2[0]}»: {n2[1]} "
            "این محدودیتِ دسترسی را به جلالین نسبت ندهید و جایگزینی را به همین آیه محدود نگه دارید."
        )
        if verse == 105
        else (
            f"ابن‌کثیر در «{n1[0]}» می‌گوید {attributed_body(n1)}؛ "
            f"{source2_name} در «{n2[0]}» می‌گوید {attributed_body(n2)}؛ "
            f"{source2_limit} و این دو تقریر را به‌جایِ یک قولِ بی‌اختلاف ننشانید."
        )
    )
    texts = [
        (
            f"طبری در «{n0[0]}» می‌گوید {attributed_body(n0)}؛ طوسی در «{n3[0]}» می‌گوید {attributed_body(n3)}؛ "
            "این دو را به مفسرانِ خود نسبت دهید و تفاوتِ سطحِ بحث را بی‌دلیل تناقضِ قطعی نخوانید."
        ),
        second_critical,
        (
            f"در استفاده از شرحِ {SOURCE_NAMES[TUSI]} و {SOURCE_NAMES[FAYD]} این دامنه‌ها را ثبت کنید: {group_note} "
            "جمع‌بندیِ آیه‌محور باید فقط گزاره‌هایِ مربوط به آیهٔ هدف را بازگو کند."
        ),
        (
            f"دو شرحِ معاصر چنین می‌گویند: قرآن‌انک، «{modern[QURANENC]}»؛ و طنطاوی، «{modern[WASIT]}». "
            "اینها بازگویی‌هایِ تفسیری‌اند، نه شاهدِ مستقلِ تاریخی یا داوریِ تخصصیِ پرونده."
        ),
        final,
    ]
    cites = [
        source_cite(n0[2], verse) + "؛ مقابله با " + source_cite(n3[2], verse),
        source_cite(n1[2], verse) + "؛ مقابله با " + source_cite(n2[2], verse),
        tusi(verse) + "؛ مقابله با " + fayd(verse),
        moyassar(verse) + "؛ مقابله با " + wasit(verse),
        final_cite,
    ]
    return [
        editorial_item(
            text,
            cite,
            verse,
            "critical",
            evidence=f"شاهدِ نقد: مائده ۵:{fa_num(verse)}؛ انتساب و دامنهٔ هر شرح در cite و پروندهٔ منبع ثبت شده است.",
        )
        for text, cite in zip(texts, cites)
    ]


def research_items(verse: int, record: dict) -> list[dict]:
    notes = record["notes"]
    n0, n1, n2, n3, n4 = notes
    questions = [
        (
            f"کاربردهایِ لغوی و قرآنیِ «{n0[0]}» چه دامنه‌ای دارند و نحوِ مائده ۵:{fa_num(verse)} کدام قرائتِ معنایی را پشتیبانی می‌کند؟",
            source_cite(n0[2], verse) + "؛ مقابله با " + quran(verse),
        ),
        (
            f"گزارهٔ «{n1[0]}» در شرحِ {SOURCE_NAMES[n1[2]]} بر کدام نقل، قاعدهٔ زبانی یا استدلال تکیه دارد و متنِ عربی چه حدی برایِ آن می‌گذارد؟",
            source_cite(n1[2], verse),
        ),
        (
            f"تقریرِ «{n2[0]}» نزدِ {SOURCE_NAMES[n2[2]]} را با توضیحِ طبری و بافتِ جمله مقایسه کنید؛ کدام بخش اختلافِ واقعی و کدام بخش تفاوتِ تأکید است؟",
            source_cite(n2[2], verse) + "؛ مقابله با " + tabari(verse),
        ),
        (
            f"شرحِ طوسی ذیلِ {tusi_scope(verse)} و شرحِ فیض ذیلِ {fayd_scope(verse)} چه شاهدهایِ نحوی، روایی یا فقهی برایِ «{n3[0]}» و «{n4[0]}» عرضه می‌کنند؟",
            tusi(verse) + "؛ مقابله با " + fayd(verse),
        ),
        (
            f"دو شرحِ معاصر چگونه «{record['title']}» را توضیح می‌دهند و کدام تفاوت‌ها نیازمندِ مقابله با متنِ عربی، روایت‌ها یا دیگر مواضعِ سوره است؟",
            moyassar(verse) + "؛ مقابله با " + wasit(verse),
        ),
    ]
    if verse == 105:
        questions[4] = (
            "چون شرحِ قرطبی برایِ ۵:۱۰۵ در آرشیوِ بررسی‌شده در دسترس نیست، برایِ داوریِ مقایسه‌ای چه متنِ معتبرِ دیگری باید مقابله شود و جلالین چه حدی از شاهد فراهم می‌کند؟",
            jalalayn(verse) + "؛ ثبتِ خلأِ آرشیویِ قرطبی.",
        )
    return [
        editorial_item(
            text,
            cite,
            verse,
            "research",
            evidence=f"پرسشِ پژوهشیِ ناظر به مائده ۵:{fa_num(verse)}؛ پاسخ به مقابلهٔ متن و منابعِ ارجاع‌شده نیاز دارد.",
        )
        for text, cite in questions
    ]


def models_for(verse: int, record: dict) -> dict[str, str]:
    field, roles, image = record["model_terms"]
    return {
        "izutsu": (
            f"در کاربستِ محدودِ ایزوتسو، «{field}» شبکهٔ معناییِ این آیه را می‌سازد؛ "
            f"هم‌نشینیِ «{record['notes'][0][0]}» با تعبیرهایِ آیه را باید در نسبت با سیاقِ مائده ۵:{fa_num(verse)} سنجید."
        ),
        "fillmore": (
            f"در قابِ فیلمور، «{roles}» نقش‌هایِ کنشگر، مخاطب، کنش و نتیجه را مرتب می‌کند؛ "
            f"این صورت‌بندی ابزارِ تحلیلِ عبارتِ «{record['notes'][1][0]}» است، نه جایگزینِ شرحِ تاریخیِ مفسران."
        ),
        "cognitive": (
            f"در کاربستِ معناشناسیِ شناختی، «{image}» تصویری برایِ سازمان‌دهیِ فهمِ متن فراهم می‌کند؛ "
            "این تحلیلِ مفهومیِ محدود است و به‌تنهایی ادعایِ تاریخی، کلامی یا فقهیِ آیه را اثبات نمی‌کند."
        ),
    }


def classical_ids(verse: int) -> tuple[str, ...]:
    if verse == 105:
        return (TABARI, IBN, JALALAYN, TUSI, FAYD)
    return (TABARI, IBN, QURTUBI, TUSI, FAYD)


def build_entry(
    verse: int,
    record: dict,
    previous_title: str,
    next_record: dict | None,
) -> dict:
    entry = {"title": record["title"]}
    entry["notes"] = [source_note_item(verse, note) for note in record["notes"]]
    entry["context"] = context_items(verse, record, previous_title, next_record)
    entry["classical"] = [
        source_item(source_id, verse, record["classical"][source_id])
        for source_id in classical_ids(verse)
    ]
    entry["modern"] = [
        source_item(source_id, verse, record["modern_sources"][source_id])
        for source_id in (QURANENC, WASIT)
    ]
    entry["modern"].extend(model_item(model, text, verse) for model, text in models_for(verse, record).items())
    entry["critical"] = critical_items(verse, record)
    entry["research"] = research_items(verse, record)
    entry["status"] = shared.STATUS
    entry["standard"] = 2
    return entry


def source_ids() -> tuple[str, ...]:
    return SOURCE_ORDER


def build_catalog(registry: dict) -> dict:
    by_id = {source["id"]: source for source in registry["sources"]}
    urls_by_source: dict[str, list[str]] = {source_id: [] for source_id in source_ids()}
    for verse in VERSES:
        for source_id in classical_ids(verse):
            urls_by_source[source_id].append(source_url(source_id, verse))
        for source_id in (QURANENC, WASIT):
            urls_by_source[source_id].append(source_url(source_id, verse))

    bases = {
        TABARI: "متن‌هایِ آیه‌محورِ طبری برایِ ۵:۶۱–۱۱۰ از مجموعهٔ گزیده‌هایِ عربی مقابله شدند؛ گزارش‌هایِ روایی، اختلافِ قرائت و ترجیحِ مؤلف به هم فروکاسته نشده‌اند.",
        IBN: "متن‌هایِ آیه‌محورِ ابن‌کثیر برایِ ۵:۶۱–۱۱۰ از مجموعهٔ گزیده‌هایِ عربی مقابله شدند؛ روایت‌ها و داوری‌هایِ خودِ مفسر به او نسبت داده شده‌اند.",
        QURTUBI: "گزیده‌هایِ آیه‌محورِ قرطبی برایِ مواضعِ در دسترسِ ۵:۶۱–۱۱۰ مقابله شدند؛ برایِ ۵:۱۰۵ شرحِ قابلِ استفاده در آرشیوِ بررسی‌شده یافت نشد و در آن آیه نقل نشده است.",
        JALALAYN: "جلالین فقط برایِ ۵:۱۰۵ به‌عنوانِ جایگزینِ آشکارِ قرطبی به‌کار رفته است؛ دامنهٔ جایگزینی محدود است و به آیاتِ دیگر تعمیم ندارد.",
        TUSI: "مواضعِ طوسی از *التبيان* با پیوندهایِ AyahNo آیه‌به‌آیه ثبت شده‌اند؛ AyahNo=101 شرحِ گروهیِ ۵:۱۰۱–۱۰۲ است، و صفحه‌هایِ ۵:۸۹ و ۵:۱۱۰ قطعهٔ دوم دارند که هر دو قطعه بررسی شدند. برایِ ۵:۱۱۰ قطعهٔ تکمیلی در این نوبت دریافت شد؛ چاپ و صفحهٔ کتاب احراز نشده است.",
        FAYD: "صفحه‌هایِ گروهیِ فیض با دامنهٔ واقعی ثبت شدند: ۵:۶۰–۶۴، ۶۵–۶۷، ۶۸–۶۹، ۷۰–۷۵، ۷۶–۸۰، ۸۱–۸۵، ۸۶–۸۷، ۸۸–۸۹، ۹۰–۹۱، ۹۲–۹۳، ۹۴–۹۵، ۹۶–۱۰۱، ۱۰۲–۱۰۵، ۱۰۶–۱۰۸ و ۱۰۹–۱۱۳؛ فقط موضعِ آیهٔ هدف خلاصه شد.",
        QURANENC: "متنِ محلیِ آیه‌به‌آیهٔ قرآن‌انک، نسخهٔ 1.0.0، برایِ مائده ۵:۶۱–۱۱۰ خوانده شد؛ خلاصه‌ها نقلِ لفظی نیستند.",
        WASIT: "گزیده‌هایِ عربیِ آیه‌به‌آیه برایِ تفسیر الوسيط گردآوری شدند و پیوندِ مستقیمِ Quran.com درج شده است؛ عنوان و بدنهٔ هر مسیر در این نوبت جداگانه مقابله نشده‌اند، بنابراین از سازگاریِ مسیر ادعایی نمی‌شود.",
    }
    scopes = {
        TABARI: "مائده ۵:۶۱–۱۱۰؛ گزیده‌هایِ آیه‌محور؛ چاپ و صفحهٔ کتاب احراز نشده",
        IBN: "مائده ۵:۶۱–۱۱۰؛ گزیده‌هایِ آیه‌محور؛ چاپ و صفحهٔ کتاب احراز نشده",
        QURTUBI: "مائده ۵:۶۱–۱۱۰ به‌جز ۵:۱۰۵؛ شرحِ ۵:۱۰۵ در آرشیوِ بررسی‌شده قابلِ استفاده نبود",
        JALALAYN: "مائده ۵:۱۰۵؛ جایگزینِ محدود برایِ خلأِ قرطبی در همان آیه",
        TUSI: "AyahNo=61–110؛ ۵:۱۰۱–۱۰۲ یک شرحِ گروهی با مسیرِ AyahNo=101؛ ۵:۸۹ و ۵:۱۱۰ دو قطعه دارند و هر دو خوانده شدند",
        FAYD: "شرح‌هایِ گروهیِ ۵:۶۰–۶۴، ۶۵–۶۷، ۶۸–۶۹، ۷۰–۷۵، ۷۶–۸۰، ۸۱–۸۵، ۸۶–۸۷، ۸۸–۸۹، ۹۰–۹۱، ۹۲–۹۳، ۹۴–۹۵، ۹۶–۱۰۱، ۱۰۲–۱۰۵، ۱۰۶–۱۰۸ و ۱۰۹–۱۱۳؛ فقط ۵:۶۱–۱۱۰ به‌کار رفت",
        QURANENC: "مائده ۵:۶۱–۱۱۰؛ متنِ محلیِ آیه‌به‌آیه، نسخهٔ 1.0.0",
        WASIT: "مائده ۵:۶۱–۱۱۰؛ گزیده‌هایِ عربیِ آیه‌به‌آیه و مسیرهایِ مستقیمِ Quran.com؛ عنوان و بدنهٔ مسیر جداگانه مقابله نشده‌اند",
    }
    items = []
    for source_id in source_ids():
        source = by_id[source_id]
        urls = list(dict.fromkeys(urls_by_source[source_id]))
        if not urls:
            continue
        items.append({
            "id": source_id,
            "title": source["title"],
            "author": source["author"],
            "language": source["language"],
            "status": "available" if source.get("localAvailable", False) else "excerpt-only",
            "basis": bases[source_id],
            "sourceUrl": urls[0],
            "sourceUrls": urls,
            "scope": scopes[source_id],
            "version": source.get("version", "صفحاتِ مستقیم/گروهی؛ چاپ و صفحهٔ کتاب احراز نشده"),
            "tradition": source.get("tradition") or shared.SOURCE_TRADITIONS.get(source_id, "اهل‌سنت"),
        })
    return {
        "id": COLLECTION_ID,
        "title": "منابعِ تفسیریِ مورد استناد در بستهٔ مائده ۵:۶۱–۱۱۰",
        "status": "mixed-linked-and-summary-only",
        "items": items,
        "comparativeCore": {
            "scope": "هر آیهٔ مائده ۵:۶۱–۱۱۰؛ در ۵:۱۰۵ قرطبی در دسترس نبود و جلالین جایگزینِ آشکار است",
            "sunniSourceIds": sorted(SUNNI),
            "shiaSourceIds": sorted(SHIA),
            "note": (
                "در هر آیه شش فیلدِ notes/context/classical/modern/critical/research پنج‌بندی‌اند؛ در هر آیه پنج شرحِ کهن، دو شرحِ معاصر و سه کاربستِ جداگانهٔ ایزوتسو، فیلمور و معناشناسیِ شناختی آمده است. "
                "برایِ ۵:۱۰۵، قرطبی در آرشیوِ بررسی‌شده شرحِ قابلِ استفاده نداشت؛ او نقل نشده و جلالین فقط برایِ همین آیه جایگزین شده است. "
                "شرحِ طوسی برایِ ۵:۱۰۱–۱۰۲ گروهی است و هر دو مسیر به AyahNo=101 می‌رسند؛ در ۵:۸۹ و ۵:۱۱۰ هر دو قطعهٔ اعلام‌شده خوانده شدند. "
                "شرح‌هایِ فیض صفحه‌هایِ گروهی دارند؛ دامنهٔ دقیق از ۵:۶۰–۶۴ تا ۵:۱۰۹–۱۱۳ در فهرست ثبت شده و در هر پرونده فقط آیهٔ هدف خلاصه شده است. "
                "اختلافِ سبب‌هایِ نزول، قرائت، نحو، فقه، کلام و روایات به مفسران نسبت داده شده؛ شمارهٔ چاپ و صفحهٔ احرازنشده ساخته نشده و همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند."
            ),
        },
        "notice": (
            "خلاصه‌ها نقلِ لفظی نیستند؛ چاپ و صفحهٔ احرازنشده ساخته نشده است. دامنهٔ واقعیِ شرح‌هایِ گروهی، "
            "خلأِ قرطبی در ۵:۱۰۵ و جایگزینیِ جلالین جدا ثبت شده‌اند؛ مسیرِ Quran.com برایِ طنطاوی در این بازه "
            "مستقلاً مقابله نشده و همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند."
        ),
    }


def validate_data() -> None:
    assert set(curated.DATA) == set(VERSES)
    assert set(TUSI_GROUPS) == set(VERSES)
    assert set(FAYD_GROUPS) == set(VERSES)
    for verse, record in curated.DATA.items():
        expected_classical = set(classical_ids(verse))
        assert len(record["notes"]) == 5, verse
        assert set(record["classical"]) == expected_classical, (verse, set(record["classical"]), expected_classical)
        assert set(record["modern_sources"]) == {QURANENC, WASIT}, verse
        assert len(record["model_terms"]) == 3 and len(set(record["model_terms"])) == 3, verse
        note_ids = {note[2] for note in record["notes"]}
        assert note_ids == expected_classical, (verse, note_ids, expected_classical)
        if verse == 105:
            assert QURTUBI not in record["classical"] and JALALAYN in record["classical"]
            assert "در آرشیوِ بررسی‌شده" in record["notes"][2][1]
        for source_id, text in record["classical"].items():
            assert len(text.split()) >= 14, (verse, source_id)
        for source_id, text in record["modern_sources"].items():
            assert len(text.split()) >= 14, (verse, source_id)


def update_method(method: str) -> str:
    addition = (
        " در بستهٔ مائده ۵:۶۱–۱۱۰، گزیده‌هایِ آیه‌محورِ طبری، ابن‌کثیر و قرطبی، مواضعِ طوسی و فیض با دامنهٔ صفحهٔ گروهی، "
        "متنِ محلیِ قرآن‌انک و گزیده‌هایِ عربیِ طنطاوی مقابله شدند؛ برایِ مسیرهایِ طنطاوی در Quran.com عنوان و بدنه در این نوبت مستقلاً مقابله نشده و این محدودیت ثبت است. "
        "قرطبی برایِ ۵:۱۰۵ در آرشیوِ بررسی‌شده شرحِ قابلِ استفاده نداشت؛ نقلِ او حذف شد و جلالین فقط برایِ همین آیه جایگزین شد. "
        "طوسی ۵:۱۰۱–۱۰۲ را در یک شرحِ گروهی با شناسهٔ صفحهٔ ۱۰۱ می‌آورد؛ ۵:۸۹ و ۵:۱۱۰ دو قطعه دارند و هر دو قطعه خوانده شدند، از جمله قطعهٔ دومِ ۵:۱۱۰ که در این نوبت دریافت شد. "
        "دامنه‌هایِ فیض چنین‌اند: ۵:۶۰–۶۴، ۶۵–۶۷، ۶۸–۶۹، ۷۰–۷۵، ۷۶–۸۰، ۸۱–۸۵، ۸۶–۸۷، ۸۸–۸۹، ۹۰–۹۱، ۹۲–۹۳، ۹۴–۹۵، ۹۶–۱۰۱، ۱۰۲–۱۰۵، ۱۰۶–۱۰۸ و ۱۰۹–۱۱۳؛ در هر پرونده فقط موضعِ آیهٔ هدف خلاصه شد. "
        "اختلاف‌هایِ روایت، قرائت، نحو، کلام و فقه به مفسران نسبت داده شده‌اند؛ خلاصه‌ها نقلِ لفظی نیستند، چاپ و صفحهٔ احرازنشده ساخته نشده و همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند."
    )
    marker = "در بستهٔ مائده ۵:۶۱–۱۱۰"
    start = method.find(marker)
    base = method[:start].rstrip() if start >= 0 else method.rstrip()

    # Keep the already-written 5:55–60 historical scope visible before this batch.
    import build_maida_5_55_60 as previous_batch
    base = previous_batch.update_method(base)
    return base.rstrip() + addition


def update_notice(notice: str) -> str:
    old = (
        "بسته‌های مائده ۵:۱–۶، ۵:۷–۱۲، ۵:۱۳–۱۸، ۵:۱۹–۲۴، ۵:۲۵–۳۰، ۵:۳۱–۳۶، ۵:۳۷–۴۲، ۵:۴۳–۴۸، "
        "۵:۴۹–۵۴، ۵:۵۵–۶۰ افزوده شده‌اند؛ مائده در این checkout بازهٔ ۵:۱–۶۰ را پوشش می‌دهد و ادامهٔ سوره هنوز پوشش ندارد."
    )
    new = (
        "بسته‌های مائده ۵:۱–۶، ۵:۷–۱۲، ۵:۱۳–۱۸، ۵:۱۹–۲۴، ۵:۲۵–۳۰، ۵:۳۱–۳۶، ۵:۳۷–۴۲، ۵:۴۳–۴۸، "
        "۵:۴۹–۵۴، ۵:۵۵–۶۰ و ۵:۶۱–۱۱۰ افزوده شده‌اند؛ مائده در این checkout بازهٔ ۵:۱–۱۱۰ را پوشش می‌دهد و ادامهٔ سوره هنوز پوشش ندارد."
    )
    if old in notice:
        notice = notice.replace(old, new)
    elif "مائده در این checkout بازهٔ ۵:۱–" in notice:
        import re
        notice = re.sub(
            r"بسته‌های مائده .*?مائده در این checkout بازهٔ ۵:۱–[^؛.]* و ادامهٔ سوره هنوز پوشش ندارد\.",
            new,
            notice,
            count=1,
        )
    else:
        notice = notice.rstrip() + " " + new
    return notice


def main() -> None:
    validate_data()
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry_ids = {source["id"] for source in registry["sources"]}
    assert set(SOURCE_ORDER) <= registry_ids
    assert registry["version"] >= 7

    dossier = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))
    preexisting_maida = {
        int(verse_id.split(":", 1)[1]): entry
        for verse_id, entry in dossier["verses"].items()
        if verse_id.startswith("5:")
        and verse_id.split(":", 1)[1].isdigit()
        and int(verse_id.split(":", 1)[1]) not in VERSES
    }
    preexisting_max = max(preexisting_maida, default=0)
    assert preexisting_max == 60, preexisting_max
    for verse in VERSES:
        previous_title = (
            preexisting_maida[verse - 1]["title"]
            if verse == 61
            else curated.DATA[verse - 1]["title"]
        )
        next_record = curated.DATA.get(verse + 1)
        dossier["verses"][f"5:{verse}"] = build_entry(
            verse,
            curated.DATA[verse],
            previous_title,
            next_record,
        )

    dossier["batches"] = [batch for batch in dossier["batches"] if batch["id"] != BATCH_ID]
    dossier["batches"].append({
        "id": BATCH_ID,
        "title": "بستهٔ پنجاه‌وهفتم: مائده ۵:۶۱–۱۱۰؛ اهلِ کتاب، احکام و روزِ واپسین",
        "range": "5:61–110",
        "count": len(VERSES),
        "status": (
            "۵۰ پروندهٔ آیه‌محور؛ در هر پرونده شش فیلدِ پنج‌بندی، پنج شرحِ کهن، دو شرحِ معاصر و سه کاربستِ جداگانهٔ معناشناختی ثبت شده‌اند؛ "
            "اختلاف‌هایِ روایی، قرائتی، نحوی، کلامی و فقهی و دامنهٔ واقعیِ شرح‌هایِ گروهی جدا نگه داشته شده‌اند؛ "
            "در ۵:۱۰۵ قرطبی در دسترس نبود و جلالین جایگزینِ آشکار است؛ پیش‌نویسِ نیازمندِ داوریِ تخصصی. "
            "پیش از این بسته، مائده تا ۵:۶۰ پوشش داشت."
        ),
    })
    dossier["batches"].sort(key=lambda batch: int(batch["id"].split("-")[1]))
    dossier["notice"] = update_notice(dossier.get("notice", ""))
    dossier["editorialMethod"] = update_method(dossier.get("editorialMethod", ""))
    DOSSIER_PATH.write_text(json.dumps(dossier, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    catalog["collections"] = [collection for collection in catalog["collections"] if collection["id"] != COLLECTION_ID]
    catalog["collections"].append(build_catalog(registry))
    catalog["version"] = max(int(catalog.get("version", 0)), 35)
    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Added {len(VERSES)} dossiers; total={len(dossier['verses'])}; batch=5:61–110")


if __name__ == "__main__":
    main()
