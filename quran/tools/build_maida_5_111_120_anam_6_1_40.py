#!/usr/bin/env python3
"""Build source-linked draft dossiers for Ma'idah 5:111–120 and al-An'am 6:1–40."""
from __future__ import annotations

import json
import re
from pathlib import Path

import build_nisa_4_1_12 as shared
import maida_5_111_120_anam_6_1_40_data as curated

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
DOSSIER_PATH = STATIC / "verse-dossiers.json"
CATALOG_PATH = STATIC / "tafsir-catalog.json"
REGISTRY_PATH = STATIC / "tafsir-sources.json"
ATTRIBUTION_PATH = ROOT / "data" / "TAFSIR_ATTRIBUTION.md"
BATCH_ID = "dossier-58"
COLLECTION_ID = "maida-5-111-120-anam-6-1-40-cited"

TABARI = curated.TABARI
IBN = curated.IBN
QURTUBI = curated.QURTUBI
TUSI = curated.TUSI
FAYD = curated.FAYD
QURANENC = curated.QURANENC
WASIT = curated.WASIT
SUNNI = {TABARI, IBN, QURTUBI}
SHIA = {TUSI, FAYD}
CLASSICAL_ORDER = (TABARI, IBN, QURTUBI, TUSI, FAYD)
SOURCE_ORDER = (*CLASSICAL_ORDER, QURANENC, WASIT)
MODELS = ("izutsu", "fillmore", "cognitive")
VERSES = tuple(curated.DATA)

SURAH_NAMES = {5: "مائده", 6: "انعام"}
FA_SURAHS = {5: "۵", 6: "۶"}
SOURCE_NAMES = {
    TABARI: "طبری",
    IBN: "ابن‌کثیر",
    QURTUBI: "قرطبی",
    TUSI: "طوسی",
    FAYD: "فیض کاشانی",
    QURANENC: "التفسير الميسر",
    WASIT: "طنطاوی",
}
QURANCOM_SLUGS = {
    TABARI: "ar-tafsir-al-tabari",
    IBN: "ar-tafsir-ibn-kathir",
    QURTUBI: "ar-tafsir-al-qurtubi",
    WASIT: "ar-tafsir-al-wasit",
}

QURAN_EBOOK_COMMIT = "c9550fdd58b0feec36300dcc42cbb3d5a4ccafc5"
OPENITI_TUSI_COMMIT = "cc9beb0d9645e8cdce892556423b9926a127054f"
OPENITI_FAYD_COMMIT = "aef851961abf65f7cc4986a0fb420179d60f81c4"
TUSI_PATH = (
    "data/0460ShaykhTusi/0460ShaykhTusi.Tibyan/"
    "0460ShaykhTusi.Tibyan.Tafsir04039-ara1"
)
FAYD_PATH = (
    "data/1091MuhammadMuhsinFaydKashani/1091MuhammadMuhsinFaydKashani.TafsirSafi/"
    "1091MuhammadMuhsinFaydKashani.TafsirSafi.Tafsir04041-ara1"
)
TUSI_URL = f"https://github.com/OpenITI/0475AH/blob/{OPENITI_TUSI_COMMIT}/{TUSI_PATH}"
FAYD_URL = f"https://github.com/OpenITI/1100AH/blob/{OPENITI_FAYD_COMMIT}/{FAYD_PATH}"

QURAN_EBOOK_ARCHIVES = {
    TABARI: {
        "path": "release/quran_tafsir_tabari_v1.1.zip",
        "gitBlobSha": "e615322cbd85a576ac501a7dc347e79cc95a83c1",
        "sha256": "17f07782a9a3c64a7c6d9af98125d87d4148f6f9f7dbd7c1e792d8e5b34f1dbb",
    },
    IBN: {
        "path": "release/quran_tafsir_ibn_kathir_ar_v1.1.zip",
        "gitBlobSha": "b15a25f10e4ea00ef43d36d96f7370cb447f4982",
        "sha256": "d3c5f65dfeec7b8515bdaf8336d1870bbc1ec078d0442e92dad365f5ea8b8d53",
    },
    QURTUBI: {
        "path": "release/quran_tafsir_qurtubi_v1.1.zip",
        "gitBlobSha": "ebc9b23a5a4b781515cec868dff01d70b2fe979b",
        "sha256": "13cffe800233fc50a0874ba1a03966aa7816ccbf0cfe67067f43b1ffa049a8e7",
    },
    WASIT: {
        "path": "release/quran_tafsir_wasit_v1.1.zip",
        "gitBlobSha": "5794f5c9c26a8aef243506f64ee249b7feade31a",
        "sha256": "05155daff7bc7d1297d5acd69db1e5cc96034b41b27d1ccd4b1416ba69ef3f1e",
    },
}

OPENITI_SNAPSHOTS = {
    TUSI: {
        "repository": "OpenITI/0475AH",
        "commit": OPENITI_TUSI_COMMIT,
        "path": TUSI_PATH,
        "gitBlobSha": "eff436d198caca98a3c352533ce5da2dd06be463",
        "fileSha256": "2d2f7d2580943709fdac7f59924a1b8ba9996c10529cc07483e3b628f2d59384",
        "metadataPath": (
            "data/0460ShaykhTusi/0460ShaykhTusi.Tibyan/"
            "0460ShaykhTusi.Tibyan.Tafsir04039-ara1.yml"
        ),
        "metadataGitBlobSha": "5198ad76db15585eed0cbf9b516e9e1b102b2572",
        "url": TUSI_URL,
        "origin": "متنِ ناقصِ شرح؛ طبقِ metadata از altafsir.com به‌دست آمده و در ۲۰۲۳ پاک‌سازی شده است.",
    },
    FAYD: {
        "repository": "OpenITI/1100AH",
        "commit": OPENITI_FAYD_COMMIT,
        "path": FAYD_PATH,
        "gitBlobSha": "31229da4df1b5e28e1dc01fc5786fe88f4574115",
        "fileSha256": "4811245d561da022eebb546f3dd715d39e26e39f2c0f171abd47c85369662f6d",
        "metadataPath": (
            "data/1091MuhammadMuhsinFaydKashani/1091MuhammadMuhsinFaydKashani.TafsirSafi/"
            "1091MuhammadMuhsinFaydKashani.TafsirSafi.Tafsir04041-ara1.yml"
        ),
        "metadataGitBlobSha": "a792babb30635c941a7864463428356ecb45481e",
        "url": FAYD_URL,
        "origin": "متنِ ناقصِ شرح؛ طبقِ metadata از altafsir.com گردآوری شده است.",
    },
}

# OpenITI section markers, not printed-page numbers. A grouped source remains grouped
# in every dossier; the text is not made artificially verse-specific.
TUSI_GROUPS: dict[str, tuple[int, int]] = {key: (int(key.split(":")[1]), int(key.split(":")[1])) for key in VERSES}
for group in (
    (5, 119, 120),
    (6, 8, 9),
    (6, 12, 13),
    (6, 17, 18),
    (6, 23, 24),
    (6, 29, 30),
    (6, 40, 41),
):
    surah, start, end = group
    for ayah in range(start, min(end, 40 if surah == 6 else 120) + 1):
        key = f"{surah}:{ayah}"
        if key in TUSI_GROUPS:
            TUSI_GROUPS[key] = (start, end)

FAYD_GROUPS: dict[str, tuple[int, int]] = {}
for surah, ranges in (
    (5, ((109, 113), (114, 115), (116, 117), (118, 120))),
    (6, ((1, 4), (5, 9), (10, 19), (20, 24), (25, 31), (32, 35), (36, 41))),
):
    for start, end in ranges:
        for ayah in range(max(start, 111 if surah == 5 else 1), min(end, 120 if surah == 5 else 40) + 1):
            FAYD_GROUPS[f"{surah}:{ayah}"] = (start, end)

# The Wasit archive heading for 6:4 is explicitly “Al-An'am 4–5”.
WASIT_GROUPS = {"6:4": (4, 5), "6:5": (4, 5)}

SECTIONS = (
    (5, 111, 115, "حواریون، مائده و مسئولیتِ پس از دریافتِ آیت"),
    (5, 116, 120, "گواهیِ عیسی، داوری و مالکیتِ خداوند"),
    (6, 1, 4, "حمد، آفرینش و نشانه‌هایِ توحید"),
    (6, 5, 10, "تکذیب، نشانه‌هایِ پیشنهادی و عبرت از گذشتگان"),
    (6, 11, 20, "سیر، مالکیت، رحمت و گواهی بر رسالت"),
    (6, 21, 31, "افترا، شریکان و صحنه‌هایِ بازخواست"),
    (6, 32, 40, "حیاتِ دنیا، رسالت، نشانه‌ها و پناه‌جویی"),
)


def fa_num(value: int) -> str:
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def parse_key(key: str) -> tuple[int, int]:
    surah, ayah = key.split(":", 1)
    return int(surah), int(ayah)


def verse_ref(key: str) -> str:
    surah, ayah = parse_key(key)
    return f"{SURAH_NAMES[surah]} {FA_SURAHS[surah]}:{fa_num(ayah)}"


def quran(key: str, end_key: str | None = None) -> str:
    if end_key is None or end_key == key:
        scope = verse_ref(key)
    else:
        start_surah, start_ayah = parse_key(key)
        end_surah, end_ayah = parse_key(end_key)
        if start_surah == end_surah:
            scope = (
                f"{SURAH_NAMES[start_surah]} {FA_SURAHS[start_surah]}:"
                f"{fa_num(start_ayah)}–{fa_num(end_ayah)}"
            )
        else:
            scope = f"{verse_ref(key)} و {verse_ref(end_key)}"
    return f"قرآن، {scope}؛ متنِ عربی و ترجمهٔ فولادوند/Tanzil در پیکرهٔ برنامه."


def source_scope(source_id: str, key: str) -> tuple[int, int]:
    return (TUSI_GROUPS if source_id == TUSI else FAYD_GROUPS)[key]


def tafsir_scope(source_id: str, key: str) -> str:
    surah, _ = parse_key(key)
    start, end = source_scope(source_id, key)
    if start == end:
        return verse_ref(f"{surah}:{start}")
    return (
        f"{SURAH_NAMES[surah]} {FA_SURAHS[surah]}:"
        f"{fa_num(start)}–{fa_num(end)}"
    )


def tusi_scope(key: str) -> str:
    return tafsir_scope(TUSI, key)


def fayd_scope(key: str) -> str:
    return tafsir_scope(FAYD, key)


def qurancom_url(source_id: str, key: str, route_ayah: int | None = None) -> str:
    surah, ayah = parse_key(key)
    slug = QURANCOM_SLUGS[source_id]
    verse_no = route_ayah if route_ayah is not None else ayah
    return f"https://quran.com/{surah}/{verse_no}/tafsirs/{slug}"


def source_url(source_id: str, key: str) -> str:
    if source_id in {TABARI, IBN, QURTUBI}:
        return qurancom_url(source_id, key)
    if source_id == WASIT:
        if key in WASIT_GROUPS:
            return qurancom_url(source_id, key, WASIT_GROUPS[key][0])
        return qurancom_url(source_id, key)
    if source_id == TUSI:
        return TUSI_URL
    if source_id == FAYD:
        return FAYD_URL
    if source_id == QURANENC:
        return "https://quranenc.com/en/browse/arabic_moyassar"
    raise KeyError(source_id)


def archive_cite(source_id: str, key: str) -> str:
    surah, ayah = parse_key(key)
    name_title = {
        TABARI: "جامع البيان عن تأويل آي القرآن",
        IBN: "تفسير القرآن العظيم",
        QURTUBI: "الجامع لأحكام القرآن",
        WASIT: "التفسير الوسيط للقرآن الكريم",
    }[source_id]
    author = {
        TABARI: "طبری، ۳۱۰ق",
        IBN: "ابن‌کثیر، ۷۷۴ق",
        QURTUBI: "قرطبی، ۶۷۱ق",
        WASIT: "محمد سید طنطاوی",
    }[source_id]
    target_scope = verse_ref(key)
    if source_id == WASIT and key in WASIT_GROUPS:
        start, end = WASIT_GROUPS[key]
        target_scope = f"انعام ۶:{fa_num(start)}–{fa_num(end)}"
        exact_note = "؛ متنِ آرشیوشده با عنوانِ گروهیِ ۶:۴–۵ مقابله شد"
    else:
        exact_note = ""
    return (
        f"{author}، *{name_title}*، ذیلِ {target_scope}؛ "
        "Quran.com API v4، دادهٔ آرشیویِ نسخهٔ 1.1 از zeeyado/quran-ebook، "
        f"commit {QURAN_EBOOK_COMMIT}؛ چاپ و صفحهٔ نسخهٔ تفسیری احراز نشده{exact_note}."
    )


def source_cite(source_id: str, key: str) -> str:
    if source_id in QURANCOM_SLUGS:
        return archive_cite(source_id, key)
    if source_id == TUSI:
        scope = tusi_scope(key)
        return (
            f"طوسی، ۴۶۰ق، *التبيان الجامع لعلوم القرآن*، شرحِ "
            f"{'مستقیمِ' if source_scope(TUSI, key)[0] == source_scope(TUSI, key)[1] else 'گروهیِ'} {scope}؛ "
            f"متنِ OpenITI، مخزنِ OpenITI/0475AH، commit {OPENITI_TUSI_COMMIT}، "
            f"پروندهٔ `{TUSI_PATH}`؛ نسخهٔ ناقصِ برگرفته از altafsir.com؛ چاپ و صفحه احراز نشده."
        )
    if source_id == FAYD:
        if key == "6:26":
            return (
                f"فیض کاشانی، *الصافي في تفسير كلام الله الوافي*، متنِ ناقصِ OpenITI، "
                f"مخزنِ OpenITI/1100AH، commit {OPENITI_FAYD_COMMIT}، پروندهٔ `{FAYD_PATH}`؛ "
                "در گروهِ ۶:۲۵–۳۱ نشانِ (۲۵) به (۲۷) می‌رسد و موضعِ ۶:۲۶ دیده نشد؛ "
                "این ارجاع یادداشتِ پوشش است، نه شرحِ آیه؛ چاپ و صفحه احراز نشده."
            )
        scope = fayd_scope(key)
        marker_note = (
            "؛ گروهِ ۶:۱–۴ متنِ صریحِ آفرینش از گل و اجل‌ها دارد اما نشانِ مستقلِ (۲) ندارد"
            if key == "6:2"
            else ""
        )
        return (
            f"فیض کاشانی، *الصافي في تفسير كلام الله الوافي*، شرحِ گروهیِ {scope}؛ "
            f"متنِ OpenITI، مخزنِ OpenITI/1100AH، commit {OPENITI_FAYD_COMMIT}، "
            f"پروندهٔ `{FAYD_PATH}`؛ نسخهٔ ناقصِ برگرفته از altafsir.com{marker_note}؛ "
            "چاپ و صفحه احراز نشده."
        )
    if source_id == QURANENC:
        return (
            f"التفسير الميسر، قرآن‌انک، نسخهٔ 1.0.0، ذیلِ {verse_ref(key)}؛ "
            "متنِ محلیِ آیه‌به‌آیه."
        )
    raise KeyError(source_id)


def source_evidence(source_id: str, key: str) -> str:
    if source_id in {TABARI, IBN, QURTUBI}:
        return (
            f"شاهدِ منبع: مدخلِ عربیِ آیه‌محورِ {verse_ref(key)} در آرشیوِ نسخهٔ 1.1 بررسی شد؛ "
            "خلاصه فقط به همان مدخل محدود است و چاپ/صفحهٔ متنِ تفسیری از آرشیو احراز نشده."
        )
    if source_id == WASIT:
        if key in WASIT_GROUPS:
            return (
                "شاهدِ منبع: عنوانِ مدخلِ طنطاوی «Al-An'am 4–5» است و متنِ آن هر دو آیه را شرح می‌دهد؛ "
                f"برایِ پروندهٔ {verse_ref(key)} فقط موضعِ همان آیه خلاصه شد."
            )
        return (
            f"شاهدِ منبع: مدخلِ عربیِ طنطاوی برایِ {verse_ref(key)} در آرشیوِ نسخهٔ 1.1 بررسی شد؛ "
            "ارجاعِ آیه‌محور ثبت شده و چاپ/صفحهٔ متن احراز نشده است."
        )
    if source_id == TUSI:
        start, end = source_scope(TUSI, key)
        group = tusi_scope(key)
        return (
            f"شاهدِ OpenITI: متن در دامنهٔ {group} است؛ "
            + ("فقط عبارتِ آیهٔ هدف از شرحِ گروهی خلاصه شد." if start != end else "موضعِ آیه در متنِ ناقص بررسی شد.")
            + " شمارهٔ صفحه و چاپ از metadata احراز نشده است."
        )
    if source_id == FAYD:
        if key == "6:26":
            return (
                "شاهدِ پوشش: در بخشِ گروهیِ ۶:۲۵–۳۱، نشانِ (۲۵) با نشانِ (۲۷) دنبال می‌شود؛ "
                "برایِ ۶:۲۶ در این متنِ ناقص نشان یا شرحِ مستقل دیده نشد."
            )
        if key == "6:2":
            return (
                "شاهدِ OpenITI: متنِ گروهیِ ۶:۱–۴ پس از شرحِ نشانِ (۱)، عبارتِ صریحِ «هو الذي خلقكم من طين» "
                "و شرحِ اجل‌ها را دارد، اما نشانِ مستقلِ (۲) ندارد؛ خلاصه به همان عبارت محدود است."
            )
        start, end = source_scope(FAYD, key)
        return (
            f"شاهدِ OpenITI: دامنهٔ نشان‌گذاری‌شدهٔ فیض {fayd_scope(key)} است؛ "
            f"فقط موضعِ {verse_ref(key)} از شرحِ گروهی خلاصه شد."
        )
    if source_id == QURANENC:
        return (
            f"شاهدِ محلی: متنِ نسخهٔ 1.0.0 قرآن‌انک برایِ {verse_ref(key)} بررسی شد؛ "
            "خلاصه نقلِ لفظی نیست."
        )
    raise KeyError(source_id)


def source_limit(source_id: str) -> str:
    if source_id in {TABARI, IBN, QURTUBI, WASIT}:
        return (
            "این بند خلاصهٔ منسوب است، نه نقلِ لفظی؛ نسخه و صفحهٔ اثر احراز نشده‌اند. "
            "مخزنِ quran-ebook پروانهٔ GPL-3.0 دارد، اما دامنهٔ آن نسبت به متنِ تفسیریِ برگرفته از Quran.com "
            "و شرایطِ منبعِ اصلی نیازمندِ بررسی است؛ حقوقِ اقتباس/بازنشرِ متن هنوز نهایی نشده است."
        )
    if source_id in {TUSI, FAYD}:
        return (
            "این بند خلاصهٔ تحریری از نسخه‌ای ناقص است، نه نقلِ لفظی؛ چاپ و صفحه شناسایی نشده و "
            "مجوزِ OpenITI/Altafsir برایِ اقتباس یا بازنشر در این بررسی احراز نشده است."
        )
    if source_id == QURANENC:
        return shared.SOURCE_LIMIT
    raise KeyError(source_id)


def source_item(source_id: str, key: str, text: str) -> dict:
    record = {
        "text": text,
        "cite": source_cite(source_id, key),
        "kind": "source-summary",
        "language": "fa",
        "sourceId": source_id,
        "sourceUrl": source_url(source_id, key),
        "evidence": source_evidence(source_id, key),
        "limit": source_limit(source_id),
        "tradition": shared.SOURCE_TRADITIONS.get(source_id, "اهل‌سنت"),
    }
    if source_id == FAYD and key == "6:26":
        record.update({
            "kind": "source-coverage-note",
            "text": text,
            "limit": (
                "این یادداشت فقط خلأِ فایلِ ناقصِ پین‌شده را ثبت می‌کند؛ نبودِ موضع در این نسخه "
                "دلیلِ نبودِ شرح در کلِ اثر نیست و به‌عنوانِ خوانش یا پنجمین تفسیر شمرده نمی‌شود."
            ),
        })
    return record


def unpack_note(note: tuple) -> tuple[str, str, str, bool]:
    focus, text, source_id = note[:3]
    is_gap = len(note) == 4 and note[3] == "gap"
    return focus, text, source_id, is_gap


def source_note_item(key: str, note: tuple) -> dict:
    focus, text, source_id, is_gap = unpack_note(note)
    if is_gap:
        return {
            "text": f"{focus}: {text}",
            "cite": source_cite(source_id, key),
            "kind": "source-coverage-note",
            "language": "fa",
            "sourceId": source_id,
            "sourceUrl": source_url(source_id, key),
            "evidence": source_evidence(source_id, key),
            "limit": (
                "این کارت خلأِ همین فایل را ثبت می‌کند؛ شاهدِ تفسیری نیست و نباید در شمارِ "
                "خلاصه‌هایِ تفسیریِ مستقل وارد شود."
            ),
            "tradition": shared.SOURCE_TRADITIONS[source_id],
        }
    return {
        "text": (
            f"{focus}: {text} این نکته به همان مفسر و دامنهٔ ثبت‌شده منسوب است؛ "
            "به‌تنهایی اجماعِ تفسیری یا واقعیتِ مستقل را اثبات نمی‌کند."
        ),
        "cite": source_cite(source_id, key),
        "kind": "editorial-inference",
        "language": "fa",
        "sourceId": source_id,
        "sourceUrl": source_url(source_id, key),
        "evidence": source_evidence(source_id, key),
        "limit": "این یادداشت بازگوییِ منسوب است، نه نقلِ لفظی یا جمع‌بندیِ اجماعی.",
        "tradition": shared.SOURCE_TRADITIONS.get(source_id, "اهل‌سنت"),
    }


def editorial_item(text: str, cite: str, key: str, field: str, evidence: str | None = None) -> dict:
    return {
        "text": text,
        "cite": cite,
        "kind": shared.FIELD_KIND[field],
        "language": "fa",
        "evidence": evidence or f"شاهدِ متنی: {quran(key)}؛ این بند تحلیلِ تحریری است.",
        "limit": shared.EDITORIAL_LIMIT,
    }


def model_item(model: str, text: str, key: str) -> dict:
    surah, ayah = parse_key(key)
    if model == "izutsu":
        cite = (
            "توشیهیکو ایزوتسو، *God and Man in the Koran: Semantics of the Koranic Weltanschauung*, 1964؛ "
            f"کاربستِ محدود بر {verse_ref(key)}."
        )
    elif model == "fillmore":
        cite = (
            "Charles J. Fillmore, “Frame Semantics,” in *Linguistics in the Morning Calm*, 1982; "
            f"limited application to Qur'an {surah}:{ayah}."
        )
    elif model == "cognitive":
        cite = (
            "جورج لیکاف و مارک جانسون، *Metaphors We Live By*, 1980؛ "
            f"کاربستِ محدودِ معناشناسیِ شناختی بر {verse_ref(key)}."
        )
    else:
        raise KeyError(model)
    return {
        "text": text,
        "cite": cite,
        "kind": "editorial-method-application",
        "language": "fa",
        "model": model,
        "evidence": f"شاهدِ متنی: {quran(key)}؛ کاربردِ محدودِ چارچوب در سطحِ واژگان و ساختارِ همین آیه.",
        "limit": "این کاربردِ تحریریِ چارچوب است، نه ادعای آنکه نظریه‌پرداز آیه را مستقلاً تفسیر کرده باشد.",
    }


def models_for(key: str, record: dict) -> dict[str, str]:
    semantic, frame, image = record["model_terms"]
    return {
        "izutsu": (
            f"در کاربستِ محدودِ ایزوتسو، «{semantic}» شبکه‌ای از نسبت‌هایِ معنایی می‌سازد؛ "
            f"این واژگان باید در سیاقِ {verse_ref(key)} سنجیده شوند، نه به‌صورتِ معادل‌هایِ جداافتاده."
        ),
        "fillmore": (
            f"در قابِ فیلمور، «{frame}» نقش‌هایِ کنشگر، مخاطب، کنش و پیامد را مرتب می‌کند؛ "
            "این صورت‌بندی ابزارِ تحلیل است، نه جایگزینِ نحو یا گزارشِ تاریخیِ مفسران."
        ),
        "cognitive": (
            f"در کاربستِ معناشناسیِ شناختی، «{image}» تصویری برایِ سازمان‌دهیِ فهمِ عبارت فراهم می‌کند؛ "
            "این تحلیلِ محدود به‌تنهایی ادعایِ تاریخی، کلامی یا فقهیِ آیه را اثبات نمی‌کند."
        ),
    }


def section_for(key: str) -> tuple[int, int, int, str]:
    surah, ayah = parse_key(key)
    for section_surah, start, end, title in SECTIONS:
        if (section_surah, start) <= (surah, ayah) <= (section_surah, end):
            return section_surah, start, end, title
    raise KeyError(key)


def tusi_scope_note(key: str) -> str:
    start, end = TUSI_GROUPS[key]
    label = "شرحِ مستقیمِ" if start == end else "شرحِ گروهیِ"
    return f"طوسی {label} {tusi_scope(key)} را دارد"


def fayd_scope_note(key: str) -> str:
    return f"فیض دامنهٔ نشان‌گذاری‌شدهٔ {fayd_scope(key)} را دارد"


def context_items(key: str, record: dict, previous_key: str, next_key: str | None) -> list[dict]:
    surah, ayah = parse_key(key)
    section_surah, start, end, title = section_for(key)
    prev_title = (
        curated.DATA[previous_key]["title"]
        if previous_key in curated.DATA
        else "عنوانِ پروندهٔ پیشین"
    )
    if previous_key not in curated.DATA:
        # The sole preceding key is 5:110, already in the dossier.
        prev_title = PREVIOUS_TITLES.get(previous_key, prev_title)
    if next_key in curated.DATA:
        next_title = curated.DATA[next_key]["title"]
    elif next_key is not None:
        next_title = "ادامهٔ سوره در آیهٔ پس از این بسته"
    else:
        next_title = "پایانِ محدودهٔ این بسته"
    first_focus, first_summary, first_source, _ = unpack_note(record["notes"][0])
    last_focus, last_summary, last_source, last_gap = unpack_note(record["notes"][-1])
    if key == "6:26":
        group_note = (
            f"{tusi_scope_note(key)}؛ {fayd_scope_note(key)}، اما در فایلِ ناقصِ فیض نشانِ (۲۵) به (۲۷) می‌رسد و موضعِ ۶:۲۶ غایب است."
        )
    elif key == "6:2":
        group_note = (
            f"{tusi_scope_note(key)}؛ {fayd_scope_note(key)}، بی‌آنکه برایِ ۶:۲ نشانِ مستقل در فایلِ فیض باشد؛ فقط عبارتِ روشنِ خلق از گل به کار رفته است."
        )
    else:
        group_note = f"{tusi_scope_note(key)}؛ {fayd_scope_note(key)}؛ دامنهٔ گروهی با شرحِ مستقلِ همان آیه یکی نیست."
    prev_cite = quran_pair(previous_key, key)
    next_cite = quran_pair(key, next_key) if next_key else quran(key)
    section_cite = quran(f"{section_surah}:{start}", f"{section_surah}:{end}")
    texts = [
        (
            f"در ترتیبِ مصحف، {verse_ref(previous_key)} با محورِ «{prev_title}» پیش ازِ {verse_ref(key)} می‌آید؛ "
            f"آیهٔ حاضر با «{record['title']}» ادامه می‌یابد و این پیوندِ ساختاری است، نه سببِ نزول."
        ),
        (
            f"لنگرِ سیاقیِ {verse_ref(key)} در این پرونده «{record['title']}» است؛ "
            f"«{first_focus}» را در کنارِ عبارتِ قرآنی و نه به‌جایِ آن بخوانید."
        ),
        (
            f"در ادامهٔ نزدیک، {verse_ref(key)} به «{next_title}» می‌رسد؛ "
            "این مقایسه گذارِ موضوعی را نشان می‌دهد و به‌تنهایی وحدتِ سببِ نزول را اثبات نمی‌کند."
        ),
        (
            f"{verse_ref(key)} در محدودهٔ مطالعهٔ «{title}»، یعنی {SURAH_NAMES[section_surah]} "
            f"{FA_SURAHS[section_surah]}:{fa_num(start)}–{fa_num(end)} قرار دارد؛ این بخش‌بندی تحریری و سازمان‌دهنده است."
        ),
        (
            f"برایِ پیوندِ شرح در پروندهٔ {verse_ref(key)} با دامنهٔ واقعیِ منبع، «{last_focus}» را در حدِ شاهدِ ثبت‌شده نگه دارید: "
            f"{group_note}"
        ),
    ]
    cites = [
        prev_cite,
        quran(key) + "؛ مقابله با " + source_cite(first_source, key),
        next_cite,
        section_cite,
        source_cite(TUSI, key) + "؛ مقابله با " + source_cite(FAYD, key),
    ]
    return [
        editorial_item(
            text,
            cite,
            key,
            "context",
            evidence=f"شاهدِ متنی: {quran(key)}؛ این پیوندْ تحلیلِ سیاقیِ تحریری است و دامنهٔ منبع در ارجاع آمده است.",
        )
        for text, cite in zip(texts, cites)
    ]


def quran_pair(first: str, second: str | None) -> str:
    if second is None:
        return quran(first)
    first_surah, first_ayah = parse_key(first)
    second_surah, second_ayah = parse_key(second)
    if first_surah == second_surah and second_ayah == first_ayah + 1:
        return quran(first, second)
    return quran(first) + "؛ " + quran(second)


def note_body(note: tuple) -> str:
    _focus, text, source_id, is_gap = unpack_note(note)
    if is_gap:
        return text
    author = SOURCE_NAMES[source_id]
    body = text[len(author):].lstrip() if text.startswith(author) else text
    for prefix in ("می‌گوید ", "می‌داند ", "می‌خواند ", "توضیح می‌دهد "):
        if body.startswith(prefix):
            body = body[len(prefix):]
            break
    return body.rstrip().rstrip(".؛،").rstrip()


def critical_items(key: str, record: dict) -> list[dict]:
    n0, n1, n2, n3, n4 = record["notes"]
    m0 = record["modern_sources"][QURANENC]
    m1 = record["modern_sources"][WASIT]
    if key == "6:26":
        group_critical = (
            "برایِ فیض، این موضع در متنِ ناقص دیده نشد؛ یادداشتِ پوشش را با خوانشِ طوسی یا گزارشِ دیگران جایگزین نکنید. "
            "چهار خلاصهٔ تفسیریِ موجود، چهار شاهدند و کارتِ پنجم فقط خلأ را ثبت می‌کند."
        )
        group_cite = source_cite(TUSI, key) + "؛ " + source_cite(FAYD, key)
        final = record["critical_focus"] + " این نتیجه مرزِ همان نسخهٔ ناقص را نشان می‌دهد، نه کلِ اثر را."
        final_cite = source_cite(FAYD, key) + "؛ مقابله با " + source_cite(TUSI, key)
    elif key == "6:2":
        group_critical = (
            "شرحِ فیض برایِ ۶:۲ در گروهِ ۶:۱–۴ بی‌نشانِ مستقل است؛ عبارتِ خلق از گل روشن است، اما دامنهٔ همان متنِ گروهی باید ثبت بماند. "
            "طوسی نیز برایِ دو اجل احتمال‌هایِ تفسیری می‌آورد."
        )
        group_cite = source_cite(TUSI, key) + "؛ " + source_cite(FAYD, key)
        final = record["critical_focus"] + " تمایزِ این تقریر با ترجمهٔ آیه حفظ شود."
        final_cite = source_cite(FAYD, key) + "؛ مقابله با " + source_cite(IBN, key)
    else:
        group_critical = (
            f"در {verse_ref(key)}، استفاده از دو متنِ گروهی چنین است: {tusi_scope_note(key)}؛ {fayd_scope_note(key)}. "
            "ارجاعِ گروهی را با شرحِ مستقلِ یک آیه اشتباه نگیرید و فقط موضعِ هدف را خلاصه کنید."
        )
        group_cite = source_cite(TUSI, key) + "؛ مقابله با " + source_cite(FAYD, key)
        if record.get("critical_focus"):
            final = record["critical_focus"] + " مرزِ گزارشِ مفسر و ارزیابیِ تحریری را جدا نگه دارید."
            final_cite = source_cite(n4[2], key) + "؛ مقابله با " + quran(key)
        else:
            focus = unpack_note(n4)[0]
            final = (
                f"در «{record['title']}»، «{focus}» فقط به {SOURCE_NAMES[n4[2]]} و دامنهٔ بررسی‌شده محدود است؛ "
                "مرزِ آن با اجماع و واقعیتِ تاریخیِ مستقل را روشن نگه دارید."
            )
            final_cite = source_cite(n4[2], key)

    texts = [
        (
            f"{SOURCE_NAMES[n0[2]]} در «{unpack_note(n0)[0]}» {note_body(n0)}؛ "
            f"{SOURCE_NAMES[n3[2]]} در «{unpack_note(n3)[0]}» {note_body(n3)}. "
            "این دو تقریر را به صاحبانشان نسبت دهید و تفاوتِ سطحِ بحث را بی‌دلیل تناقضِ قطعی نخوانید."
        ),
        (
            f"{SOURCE_NAMES[n1[2]]} در «{unpack_note(n1)[0]}» {note_body(n1)}؛ "
            f"{SOURCE_NAMES[n2[2]]} در «{unpack_note(n2)[0]}» {note_body(n2)}. "
            "این دو را به‌جایِ یک قولِ بی‌اختلاف ننشانید."
        ),
        group_critical,
        (
            f"دو شرحِ معاصر چنین می‌گویند: قرآن‌انک، «{m0}»؛ و طنطاوی، «{m1}». "
            "اینها بازگویی‌هایِ تفسیری‌اند، نه شاهدِ مستقلِ تاریخی یا داوریِ تخصصیِ پرونده."
        ),
        final,
    ]
    cites = [
        source_cite(n0[2], key) + "؛ مقابله با " + source_cite(n3[2], key),
        source_cite(n1[2], key) + "؛ مقابله با " + source_cite(n2[2], key),
        group_cite,
        source_cite(QURANENC, key) + "؛ مقابله با " + source_cite(WASIT, key),
        final_cite,
    ]
    return [
        editorial_item(
            text,
            cite,
            key,
            "critical",
            evidence=f"شاهدِ نقد: {quran(key)}؛ انتساب و دامنهٔ هر شاهد در ارجاع و فهرستِ نسخه‌ها ثبت شده است.",
        )
        for text, cite in zip(texts, cites)
    ]


def research_items(key: str, record: dict) -> list[dict]:
    n0, n1, n2, n3, n4 = record["notes"]
    first_focus = unpack_note(n0)[0]
    second_focus = unpack_note(n1)[0]
    third_focus = unpack_note(n2)[0]
    fourth_focus = unpack_note(n3)[0]
    fifth_focus = unpack_note(n4)[0]
    if key == "6:26":
        group_question = (
            "برایِ ۶:۲۶، چه نسخهٔ کامل و قابلِ استنادی می‌تواند خلأِ فیض را پر کند؛ "
            "چگونه می‌توان مطمئن شد که شرحِ تازه واقعاً همین آیه را پوشش می‌دهد؟",
            source_cite(FAYD, key) + "؛ مقابله با " + source_cite(TUSI, key),
        )
    else:
        group_question = (
            f"شرحِ گروهیِ طوسی ذیلِ {tusi_scope(key)} و فیض ذیلِ {fayd_scope(key)} چه شاهدهایی برایِ «{fourth_focus}» و «{fifth_focus}» می‌آورند؛ "
            "کدام گزاره واقعاً به آیهٔ هدف مربوط است؟",
            source_cite(TUSI, key) + "؛ مقابله با " + source_cite(FAYD, key),
        )
    questions = [
        (
            f"کاربردِ «{first_focus}» در {verse_ref(key)} از نظرِ لغت، نحو و سیاق چه دامنه‌ای دارد و طبری کدام قرینه را برجسته می‌کند؟",
            source_cite(n0[2], key) + "؛ مقابله با " + quran(key),
        ),
        (
            f"شرحِ {SOURCE_NAMES[n1[2]]} دربارهٔ «{second_focus}» بر کدام نقل، قرائت یا استدلال تکیه دارد و متنِ آیه چه حدی برایِ آن می‌گذارد؟",
            source_cite(n1[2], key),
        ),
        (
            f"تقریرِ {SOURCE_NAMES[n2[2]]} دربارهٔ «{third_focus}» را با طبری و بافتِ جمله مقایسه کنید؛ کدام بخش اختلافِ واقعی و کدام تفاوتِ تأکید است؟",
            source_cite(n2[2], key) + "؛ مقابله با " + source_cite(TABARI, key),
        ),
        group_question,
        (
            f"دو شرحِ معاصر چگونه «{curated.DATA[key]['title']}» را توضیح می‌دهند و کدام تفاوت‌ها نیازمندِ مقابله با متنِ عربی یا گزارش‌هایِ دیگر است؟",
            source_cite(QURANENC, key) + "؛ مقابله با " + source_cite(WASIT, key),
        ),
    ]
    return [
        editorial_item(
            text,
            cite,
            key,
            "research",
            evidence=f"پرسشِ پژوهشیِ ناظر به {quran(key)}؛ پاسخ به مقابلهٔ متن و منابعِ ارجاع‌شده نیاز دارد.",
        )
        for text, cite in questions
    ]


def build_entry(key: str, record: dict, previous_key: str, next_key: str | None) -> dict:
    entry = {"title": record["title"]}
    entry["notes"] = [source_note_item(key, note) for note in record["notes"]]
    entry["context"] = context_items(key, record, previous_key, next_key)
    by_source = {unpack_note(note)[2]: note for note in record["notes"]}
    entry["classical"] = [
        source_item(source_id, key, unpack_note(by_source[source_id])[1])
        for source_id in CLASSICAL_ORDER
    ]
    entry["modern"] = [
        source_item(source_id, key, record["modern_sources"][source_id])
        for source_id in (QURANENC, WASIT)
    ]
    entry["modern"].extend(
        model_item(model, text, key) for model, text in models_for(key, record).items()
    )
    entry["critical"] = critical_items(key, record)
    entry["research"] = research_items(key, record)
    entry["status"] = shared.STATUS
    entry["standard"] = 2
    return entry


def source_ids() -> tuple[str, ...]:
    return SOURCE_ORDER


def build_catalog(registry: dict) -> dict:
    by_id = {source["id"]: source for source in registry["sources"]}
    urls_by_source: dict[str, list[str]] = {source_id: [] for source_id in source_ids()}
    for key in VERSES:
        for source_id in CLASSICAL_ORDER:
            urls_by_source[source_id].append(source_url(source_id, key))
        for source_id in (QURANENC, WASIT):
            urls_by_source[source_id].append(source_url(source_id, key))

    bases = {
        TABARI: "برایِ مائده ۵:۱۱۱–۱۲۰ و انعام ۶:۱–۴۰، مدخل‌هایِ عربیِ آرشیوِ Quran.com API v4 نسخهٔ 1.1 با عنوانِ آیه‌محور استخراج و خلاصه شدند؛ اختلافِ روایت و قرائت به طبری منسوب است.",
        IBN: "مدخل‌هایِ عربیِ ابن‌کثیر از آرشیوِ نسخهٔ 1.1 برایِ هر ۵۰ آیه بررسی شدند؛ روایت‌هایِ تاریخی و ترجیح‌هایِ مفسر به خودِ او نسبت داده شده‌اند.",
        QURTUBI: "مدخل‌هایِ آیه‌محورِ قرطبی در آرشیوِ نسخهٔ 1.1 برایِ هر ۵۰ آیه بررسی شدند؛ اقوالِ متعارضِ نقل‌شده یکی نشده‌اند.",
        TUSI: "متنِ ناقصِ التبيان از OpenITI، commit پین‌شده، بررسی شد؛ گروه‌هایِ ۵:۱۱۹–۱۲۰، ۶:۸–۹، ۶:۱۲–۱۳، ۶:۱۷–۱۸، ۶:۲۳–۲۴، ۶:۲۹–۳۰ و ۶:۴۰–۴۱ به همان دامنهٔ واقعی ثبت شده‌اند؛ چاپ و صفحه احراز نشده.",
        FAYD: "متنِ ناقصِ الصافي در OpenITI، commit پین‌شده، بررسی شد؛ دامنه‌هایِ ۵:۱۰۹–۱۱۳، ۵:۱۱۴–۱۱۵، ۵:۱۱۶–۱۱۷، ۵:۱۱۸–۱۲۰، ۶:۱–۴، ۶:۵–۹، ۶:۱۰–۱۹، ۶:۲۰–۲۴، ۶:۲۵–۳۱، ۶:۳۲–۳۵ و ۶:۳۶–۴۱ ثبت شدند. در ۶:۲ نشانِ مستقل نیست و در ۶:۲۶ موضع غایب است.",
        QURANENC: "متنِ محلیِ آیه‌به‌آیهٔ قرآن‌انک، نسخهٔ 1.0.0، برایِ هر ۵۰ آیه بررسی شد؛ خلاصه‌ها نقلِ لفظی نیستند.",
        WASIT: "متن‌هایِ عربیِ طنطاوی از آرشیوِ Quran.com API v4 نسخهٔ 1.1 بررسی شدند؛ عنوانِ ۶:۴–۵ یک گروه را نشان می‌دهد و هر دو پرونده همان دامنه را آشکار می‌کنند.",
    }
    scopes = {
        TABARI: "مائده ۵:۱۱۱–۱۲۰ و انعام ۶:۱–۴۰؛ مدخل‌هایِ آیه‌محورِ آرشیوِ نسخهٔ 1.1",
        IBN: "مائده ۵:۱۱۱–۱۲۰ و انعام ۶:۱–۴۰؛ مدخل‌هایِ آیه‌محورِ آرشیوِ نسخهٔ 1.1",
        QURTUBI: "مائده ۵:۱۱۱–۱۲۰ و انعام ۶:۱–۴۰؛ مدخل‌هایِ آیه‌محورِ آرشیوِ نسخهٔ 1.1",
        TUSI: "مستقیم جز ۵:۱۱۹–۱۲۰، ۶:۸–۹، ۶:۱۲–۱۳، ۶:۱۷–۱۸، ۶:۲۳–۲۴، ۶:۲۹–۳۰ و ۶:۴۰–۴۱؛ متنِ ناقصِ OpenITI",
        FAYD: "گروه‌هایِ ۵:۱۰۹–۱۱۳، ۱۱۴–۱۱۵، ۱۱۶–۱۱۷، ۱۱۸–۱۲۰؛ ۶:۱–۴، ۵–۹، ۱۰–۱۹، ۲۰–۲۴، ۲۵–۳۱، ۳۲–۳۵ و ۳۶–۴۱؛ خلأِ ۶:۲۶ و نشانِ غایبِ ۶:۲ ثبت شد",
        QURANENC: "مائده ۵:۱۱۱–۱۲۰ و انعام ۶:۱–۴۰؛ متنِ محلیِ آیه‌به‌آیه، نسخهٔ 1.0.0",
        WASIT: "مائده ۵:۱۱۱–۱۲۰ و انعام ۶:۱–۴۰؛ گروهِ واقعیِ ۶:۴–۵ در مسیرِ طنطاوی حفظ شد",
    }
    items = []
    for source_id in source_ids():
        source = by_id[source_id]
        urls = list(dict.fromkeys(urls_by_source[source_id]))
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
            "licenseStatus": source.get("licenseStatus", "review-needed"),
        })
    return {
        "id": COLLECTION_ID,
        "title": "منابعِ تفسیریِ مورد استناد در بستهٔ مائده ۵:۱۱۱–۱۲۰ و انعام ۶:۱–۴۰",
        "status": "mixed-linked-and-summary-only",
        "items": items,
        "comparativeCore": {
            "scope": "مائده ۵:۱۱۱–۱۲۰ و انعام ۶:۱–۴۰؛ در ۶:۲۶ متنِ فیض در نسخهٔ ناقصِ بررسی‌شده موضع ندارد",
            "sunniSourceIds": sorted(SUNNI),
            "shiaSourceIds": sorted(SHIA),
            "modernSourceIds": [QURANENC, WASIT],
            "note": (
                "در هر یک از ۵۰ پرونده شش فیلدِ مستقلِ notes/context/classical/modern/critical/research پنج‌بندی‌اند؛ "
                "در ۴۹ آیه پنج خلاصهٔ کهن، و در ۶:۲۶ چهار خلاصهٔ کهن به‌علاوهٔ کارتِ صریحِ خلأِ فیض آمده است؛ "
                "کارتِ خلأ تفسیر شمرده نمی‌شود. دو شرحِ معاصر و سه کاربستِ محدودِ ایزوتسو، فیلمور و معناشناسیِ شناختی جدا هستند. "
                "طوسی ۵:۱۱۹–۱۲۰ و گروه‌هایِ ۶:۸–۹، ۶:۱۲–۱۳، ۶:۱۷–۱۸، ۶:۲۳–۲۴، ۶:۲۹–۳۰ و ۶:۴۰–۴۱ را گروهی شرح می‌دهد؛ "
                "طنطاوی ۶:۴–۵ را در یک مدخلِ گروهی دارد. متنِ فیض در ۶:۲ نشانِ مستقل ندارد اما عبارتِ صریحِ آیه را در گروهِ ۶:۱–۴ شرح می‌کند؛ "
                "در گروهِ ۶:۲۵–۳۱، نشانِ ۲۵ به ۲۷ می‌رسد و شرحِ ۶:۲۶ در فایل دیده نشد. "
                "مخزنِ quran-ebook دارایِ LICENSE با GPL-3.0 است، اما دامنهٔ آن برایِ متنِ تفسیریِ برگرفته از Quran.com و شرایطِ منبعِ اصلی بررسیِ جداگانه می‌خواهد؛ "
                "برایِ متن‌هایِ OpenITI مجوزِ اقتباس یا بازنشر در این کار احراز نشده است. چاپ و صفحهٔ احرازنشده ساخته نشده و همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند."
            ),
        },
        "notice": (
            "ارجاع‌ها به نسخه‌هایِ پین‌شده و دامنهٔ واقعیِ شرح‌هایِ گروهی متصل‌اند؛ خلاصه‌ها نقلِ لفظی نیستند. "
            "نسخه‌هایِ متنِ تفسیر برایِ طوسی و فیض ناقص‌اند و شرایطِ اقتباس/بازنشرِ متنِ Quran.com و OpenITI/Altafsir هنوز احراز نشده است. "
            "خلأِ فیض در ۶:۲۶ و نشانِ مستقلِ ۶:۲ آشکار ثبت شده‌اند؛ همهٔ پرونده‌ها پیش‌نویس و نیازمندِ داوریِ تخصصی‌اند."
        ),
    }


def update_registry(registry: dict) -> dict:
    by_id = {source["id"]: source for source in registry["sources"]}
    quran_license = (
        "مخزن/بستهٔ zeeyado/quran-ebook دارایِ LICENSE با GPL-3.0 است؛ "
        "دامنهٔ آن نسبت به متنِ تفسیریِ برگرفته از Quran.com و شرایطِ منبعِ اصلی جداگانه نیازمندِ بررسی است."
    )
    for source_id in (TABARI, IBN, QURTUBI, WASIT):
        source = by_id[source_id]
        source["license"] = quran_license
        source["licenseStatus"] = "review-needed"
        source["attributionReview"] = (
            f"آرشیوِ Quran.com API v4 از zeeyado/quran-ebook، commit {QURAN_EBOOK_COMMIT}؛ "
            "ارجاع به نسخهٔ آرشیوی به‌تنهایی حقوقِ متنِ اصلی را احراز نمی‌کند."
        )
        source["archiveSnapshot"] = QURAN_EBOOK_ARCHIVES[source_id]
    for source_id, snapshot in OPENITI_SNAPSHOTS.items():
        source = by_id[source_id]
        source["source"] = "OpenITI text snapshot / GreatTafsirs study route"
        source["license"] = (
            "مجوزی برایِ متنِ ناقصِ OpenITI یا نسخهٔ اخذشده از Altafsir در این بررسی احراز نشده؛ "
            "شرایطِ میزبانِ GreatTafsirs و حقوقِ اقتباس/بازنشر نیازمندِ بررسی است."
        )
        source["licenseStatus"] = "unresolved"
        source["researchSnapshot"] = {
            "repository": snapshot["repository"],
            "commit": snapshot["commit"],
            "path": snapshot["path"],
            "gitBlobSha": snapshot["gitBlobSha"],
            "metadataPath": snapshot["metadataPath"],
            "metadataGitBlobSha": snapshot["metadataGitBlobSha"],
            "url": snapshot["url"],
            "origin": snapshot["origin"],
            "edition": "not identified",
            "pagination": "not specified",
            "licenseStatus": "unresolved",
        }
        source["availabilityNote"] = (
            "متنِ OpenITI برایِ این بسته به‌طورِ موقت و در دامنهٔ آیاتِ هدف بررسی شد؛ "
            "نسخه ناقص است، متنِ کامل در برنامه بازنشر نشده و مجوزِ اقتباس/بازنشر احراز نشده است."
        )
    registry["version"] = max(int(registry.get("version", 0)), 8)
    return registry


def source_snapshot_metadata() -> dict:
    archives = {
        source_id: {
            "sourceId": source_id,
            "repository": "zeeyado/quran-ebook",
            "commit": QURAN_EBOOK_COMMIT,
            **archive,
            "licenseStatus": "repository GPL-3.0 declared; scope for upstream tafsir text requires separate review",
        }
        for source_id, archive in QURAN_EBOOK_ARCHIVES.items()
    }
    openiti = {
        source_id: {
            "sourceId": source_id,
            **snapshot,
            "edition": "not identified",
            "pagination": "not specified",
            "textStatus": "incomplete; scraped from altafsir.com per OpenITI metadata",
            "licenseStatus": "unresolved; no permission for adaptation/redistribution established",
        }
        for source_id, snapshot in OPENITI_SNAPSHOTS.items()
    }
    return {
        "batchId": BATCH_ID,
        "range": "5:111–120; 6:1–40",
        "quranEbook": {
            "repository": "zeeyado/quran-ebook",
            "commit": QURAN_EBOOK_COMMIT,
            "repositoryLicense": "GPL-3.0 LICENSE file exists at the pinned repository snapshot",
            "textRightsStatus": "unresolved; repository license scope over Quran.com-derived tafsir text is not assumed",
            "archives": archives,
        },
        "openIti": openiti,
        "scopeNotes": {
            "tusi": "Grouped passages are recorded as 5:119–120; 6:8–9; 6:12–13; 6:17–18; 6:23–24; 6:29–30; 6:40–41.",
            "fayd": "Groups are 5:109–113; 114–115; 116–117; 118–120; 6:1–4; 5–9; 10–19; 20–24; 25–31; 32–35; 36–41. 6:2 has explicit commentary without its own marker; 6:26 is absent between markers 25 and 27.",
            "wasit": "The archive heading for 6:4–5 is one grouped entry; both dossiers cite that scope.",
        },
        "rawWorkBench": {
            "path": "/tmp/next50-sources.json",
            "sha256": "4ccb0d467cf4aabdcdac52974465cc54e231618e39b153368570340e0376f3d2",
            "status": "temporary extraction, not included in the application; curated paraphrases and source metadata are stored in the builder and data module",
        },
    }


def quran_pair(first: str, second: str | None) -> str:
    if second is None:
        return quran(first)
    first_surah, first_ayah = parse_key(first)
    second_surah, second_ayah = parse_key(second)
    if first_surah == second_surah and second_ayah == first_ayah + 1:
        return quran(first, second)
    return quran(first) + "؛ " + quran(second)


def validate_data(registry: dict | None = None) -> None:
    assert len(VERSES) == 50
    assert set(VERSES) == set(curated.DATA)
    assert set(TUSI_GROUPS) == set(VERSES)
    assert set(FAYD_GROUPS) == set(VERSES)
    for key, record in curated.DATA.items():
        assert len(record["notes"]) == 5, key
        note_ids = [unpack_note(note)[2] for note in record["notes"]]
        assert len(note_ids) == 5 and set(note_ids) == set(CLASSICAL_ORDER), (key, note_ids)
        assert set(record["modern_sources"]) == {QURANENC, WASIT}, key
        assert len(record["model_terms"]) == 3 and all(record["model_terms"]), key
        for note in record["notes"]:
            focus, text, source_id, is_gap = unpack_note(note)
            assert focus and text and source_id in CLASSICAL_ORDER, (key, note)
            if is_gap:
                assert key == "6:26" and source_id == FAYD
            else:
                assert len(text.split()) >= 12, (key, source_id, text)
        for source_id, text in record["modern_sources"].items():
            assert len(text.split()) >= 14, (key, source_id, text)
    assert TUSI_GROUPS["5:119"] == TUSI_GROUPS["5:120"] == (119, 120)
    assert TUSI_GROUPS["6:40"] == (40, 41)
    assert FAYD_GROUPS["6:2"] == (1, 4) and FAYD_GROUPS["6:26"] == (25, 31)
    if registry:
        assert {source["id"] for source in registry["sources"]} >= set(SOURCE_ORDER)


def update_method(method: str) -> str:
    marker = "در بستهٔ مائده ۵:۱۱۱–۱۲۰ و انعام ۶:۱–۴۰"
    start = method.find(marker)
    base = method[:start].rstrip() if start >= 0 else method.rstrip()
    addition = (
        " در بستهٔ مائده ۵:۱۱۱–۱۲۰ و انعام ۶:۱–۴۰، مدخل‌هایِ آیه‌محورِ طبری، ابن‌کثیر و قرطبی از آرشیوِ نسخهٔ 1.1، "
        "متنِ محلیِ قرآن‌انک، مدخل‌هایِ طنطاوی و مواضعِ طوسی و فیض در متن‌هایِ ناقصِ OpenITI مقابله شدند. "
        "طوسی ۵:۱۱۹–۱۲۰ و گروه‌هایِ ۶:۸–۹، ۶:۱۲–۱۳، ۶:۱۷–۱۸، ۶:۲۳–۲۴، ۶:۲۹–۳۰ و ۶:۴۰–۴۱ را یکجا شرح می‌دهد؛ "
        "طنطاوی در ۶:۴–۵ مدخلِ گروهی دارد. دامنه‌هایِ فیض چنین‌اند: ۵:۱۰۹–۱۱۳، ۱۱۴–۱۱۵، ۱۱۶–۱۱۷، ۱۱۸–۱۲۰؛ "
        "۶:۱–۴، ۵–۹، ۱۰–۱۹، ۲۰–۲۴، ۲۵–۳۱، ۳۲–۳۵ و ۳۶–۴۱؛ در هر پرونده فقط موضعِ آیهٔ هدف خلاصه شده است. "
        "برایِ ۶:۲ نشانِ مستقلِ فیض نیست، اما گروهِ ۶:۱–۴ عبارتِ روشنِ آیه و شرحِ اجل‌ها را دارد؛ "
        "برایِ ۶:۲۶ نشانِ ۲۵ به ۲۷ می‌رسد و خلأِ نسخه ثبت شده، نه آنکه به‌عنوانِ دیدگاهِ مفسر شمرده شود. "
        "قرائت، نحو، روایت، کلام و سببِ نزول به مفسران نسبت داده شده‌اند؛ در ۵:۱۱۲ قرائت و معنایِ استطاعت، در ۵:۱۱۵ نزول یا عدمِ نزول، "
        "در ۵:۱۱۶ زمانِ خطاب، در ۶:۲ اجل‌ها، در ۶:۳ تأویلِ حضور، در ۶:۲۳ معنایِ فتنه، در ۶:۳۱ مرجعِ ضمیر و در ۶:۳۳ قرائت‌ها جدا نگه داشته شده‌اند. "
        "خلاصه‌ها نقلِ لفظی نیستند، چاپ و صفحهٔ احرازنشده ساخته نشده و همهٔ پرونده‌ها پیش‌نویسِ نیازمندِ داوریِ تخصصی‌اند. "
        "مخزنِ quran-ebook دارایِ LICENSE با GPL-3.0 است، اما دامنهٔ آن نسبت به متنِ تفسیریِ برگرفته از Quran.com و شرایطِ منبعِ اصلی جداگانه باید بررسی شود؛ "
        "OpenITI نسخه‌ها را ناقص و برگرفته از altafsir.com توصیف می‌کند و مجوزِ اقتباس/بازنشر در این کار احراز نشده است."
    )
    return base.rstrip() + addition


def update_notice(notice: str) -> str:
    new_coverage = (
        "بسته‌های مائده ۵:۱–۶، ۵:۷–۱۲، ۵:۱۳–۱۸، ۵:۱۹–۲۴، ۵:۲۵–۳۰، ۵:۳۱–۳۶، ۵:۳۷–۴۲، ۵:۴۳–۴۸، "
        "۵:۴۹–۵۴، ۵:۵۵–۶۰، ۵:۶۱–۱۱۰ و ۵:۱۱۱–۱۲۰ افزوده شده‌اند؛ مائده در این checkout بازهٔ ۵:۱–۱۲۰ و انعام بازهٔ ۶:۱–۴۰ را پوشش می‌دهند؛ ادامهٔ هر دو سوره هنوز پوشش ندارد."
    )
    pattern = r"بسته‌های مائده .*?مائده در این checkout بازهٔ ۵:۱–۱۱۰ را پوشش می‌دهد و ادامهٔ سوره هنوز پوشش ندارد\."
    if re.search(pattern, notice):
        notice = re.sub(pattern, new_coverage, notice, count=1)
    elif "مائده در این checkout بازهٔ ۵:۱–" in notice:
        notice = re.sub(
            r"بسته‌های مائده .*?مائده در این checkout بازهٔ ۵:۱–[^؛.]* و ادامهٔ سوره هنوز پوشش ندارد\.",
            new_coverage,
            notice,
            count=1,
        )
    else:
        notice = notice.rstrip() + " " + new_coverage
    detail_marker = "خلأِ فیض در انعام ۶:۲۶"
    notice = notice.split(detail_marker, 1)[0].rstrip()
    addition = (
        " خلأِ نسخهٔ ناقصِ فیض در انعام ۶:۲۶، نشانِ مستقلِ ۶:۲ و گروهِ طنطاوی برایِ ۶:۴–۵ جدا ثبت شده‌اند؛ "
        "خلاصه‌ها نقلِ لفظی نیستند، صفحه یا اطلاعاتِ نشرِ احرازنشده ساخته نشده و هیچ بندی بازبینیِ تخصصی‌شده معرفی نمی‌شود. "
        "مجوزِ متنِ تفسیریِ آرشیوهایِ Quran.com و OpenITI/Altafsir برایِ اقتباس یا بازنشر در این کار احراز نشده است."
    )
    return notice.rstrip() + addition


def update_source_snapshots(dossier: dict) -> None:
    snapshots = dossier.setdefault("sourceSnapshots", {})
    snapshots["maida_111_120_anam_6_1_40"] = source_snapshot_metadata()
    # Preserve prior source records but avoid implying that the archive's GPL applies
    # automatically to the original tafsir texts.
    for key in ("tabari", "qurtubi"):
        if key in snapshots:
            snapshots[key]["textRightsStatus"] = (
                "The quran-ebook repository has a GPL-3.0 LICENSE; its scope over the Quran.com-derived tafsir text and original-source terms still requires review."
            )


def main() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry = update_registry(registry)
    validate_data(registry)

    dossier = json.loads(DOSSIER_PATH.read_text(encoding="utf-8"))
    target_keys = set(VERSES)
    existing_maida = {
        key for key in dossier["verses"]
        if key.startswith("5:") and key not in target_keys
    }
    existing_max = max((int(key.split(":")[1]) for key in existing_maida), default=0)
    assert existing_max == 110, existing_max
    existing_anam = {
        key for key in dossier["verses"]
        if key.startswith("6:") and key not in target_keys
    }
    assert not existing_anam, existing_anam

    ordered = list(VERSES)
    for index, key in enumerate(ordered):
        previous_key = ordered[index - 1] if index else "5:110"
        next_key = ordered[index + 1] if index + 1 < len(ordered) else "6:41"
        record = curated.DATA[key]
        if key == "5:111":
            previous_title = dossier["verses"][previous_key]["title"]
            PREVIOUS_TITLES[previous_key] = previous_title
        dossier["verses"][key] = build_entry(key, record, previous_key, next_key)

    dossier["batches"] = [batch for batch in dossier["batches"] if batch["id"] != BATCH_ID]
    dossier["batches"].append({
        "id": BATCH_ID,
        "title": "بستهٔ پنجاه‌وهشتم: مائده ۵:۱۱۱–۱۲۰ و انعام ۶:۱–۴۰؛ حواریون، قیامت و نشانه‌هایِ آفرینش",
        "range": "5:111–120; 6:1–40",
        "count": len(VERSES),
        "status": (
            "۵۰ پروندهٔ آیه‌محور در ترتیبِ مصحف؛ شش فیلدِ پنج‌بندی، پنج شرحِ کهن در هر آیه به‌جز ۶:۲۶ که چهار خلاصه و یک یادداشتِ خلأ دارد، "
            "دو شرحِ معاصر و سه کاربردِ جداگانهٔ معناشناختی؛ اختلافِ قرائت، روایت و دامنهٔ گروهی آشکار است؛ "
            "خلأِ موضعِ فیض در ۶:۲۶ و نشانِ مستقلِ ۶:۲ ثبت شده؛ مجوزِ اقتباس/بازنشرِ متن‌هایِ آرشیوی هنوز احراز نشده؛ "
            "پیش‌نویسِ نیازمندِ داوریِ تخصصی. پیش از این بسته، مائده تا ۵:۱۱۰ پوشش داشت و برایِ انعام در این پیکره پرونده‌ای نبود."
        ),
    })
    dossier["batches"].sort(key=lambda item: int(item["id"].split("-")[1]))
    dossier["notice"] = update_notice(dossier.get("notice", ""))
    dossier["editorialMethod"] = update_method(dossier.get("editorialMethod", ""))
    update_source_snapshots(dossier)
    DOSSIER_PATH.write_text(json.dumps(dossier, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    catalog["collections"] = [collection for collection in catalog["collections"] if collection["id"] != COLLECTION_ID]
    catalog["collections"].append(build_catalog(registry))
    catalog["version"] = max(int(catalog.get("version", 0)), 36)
    CATALOG_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_attribution_doc()
    print(f"Added {len(VERSES)} dossiers; total={len(dossier['verses'])}; batch=5:111–120 + 6:1–40")


# Previous boundary title is loaded immediately before building 5:111.
PREVIOUS_TITLES: dict[str, str] = {}


def update_attribution_doc() -> None:
    if not ATTRIBUTION_PATH.exists():
        return
    text = ATTRIBUTION_PATH.read_text(encoding="utf-8")
    marker = "## ۵. منابعِ بررسی‌شده برایِ بستهٔ مائده و انعام"
    if marker in text:
        text = text.split(marker, 1)[0].rstrip()
    addition = f"""

{marker}

برایِ بستهٔ ۵:۱۱۱–۱۲۰ و ۶:۱–۴۰، متنِ خامِ تفسیری در فایل‌هایِ برنامه بازنشر نشده است؛ پرونده‌ها خلاصه‌هایِ تحریریِ منتسب و ارجاع‌هایِ دامنه‌مند دارند. پین‌کردنِ نسخه برایِ بازبینیِ متن است و به‌تنهایی تأییدِ حقِ اقتباس یا بازنشر نیست.

### آرشیوهایِ Quran.com API v4 در `zeeyado/quran-ebook`

- مخزنِ بررسی‌شده: commit `{QURAN_EBOOK_COMMIT}`؛ مخزن فایلِ `LICENSE` با متنِ GPL-3.0 دارد. دامنهٔ حقوقیِ آن نسبت به متن‌هایِ تفسیریِ برگرفته از Quran.com و شرایطِ منبعِ اصلی در این کار احراز نشده است؛ وضعیتِ اقتباس/بازنشر را «نیازمندِ بررسی» بدانید.
- طبری: `release/quran_tafsir_tabari_v1.1.zip`، blob `{QURAN_EBOOK_ARCHIVES[TABARI]['gitBlobSha']}`، SHA-256 `{QURAN_EBOOK_ARCHIVES[TABARI]['sha256']}`.
- ابن‌کثیر: `release/quran_tafsir_ibn_kathir_ar_v1.1.zip`، blob `{QURAN_EBOOK_ARCHIVES[IBN]['gitBlobSha']}`، SHA-256 `{QURAN_EBOOK_ARCHIVES[IBN]['sha256']}`.
- قرطبی: `release/quran_tafsir_qurtubi_v1.1.zip`، blob `{QURAN_EBOOK_ARCHIVES[QURTUBI]['gitBlobSha']}`، SHA-256 `{QURAN_EBOOK_ARCHIVES[QURTUBI]['sha256']}`.
- وسيطِ طنطاوی: `release/quran_tafsir_wasit_v1.1.zip`، blob `{QURAN_EBOOK_ARCHIVES[WASIT]['gitBlobSha']}`، SHA-256 `{QURAN_EBOOK_ARCHIVES[WASIT]['sha256']}`. عنوانِ آرشیوشدهٔ انعام ۶:۴–۵ گروهی است؛ در هر دو پرونده همان دامنه ذکر شده است.

### متن‌هایِ OpenITI برایِ طوسی و فیض

- طوسی، *التبيان الجامع لعلوم القرآن*: مخزن `OpenITI/0475AH`، commit `{OPENITI_TUSI_COMMIT}`؛ پروندهٔ `{TUSI_PATH}`، Git blob `{OPENITI_SNAPSHOTS[TUSI]['gitBlobSha']}`، SHA-256ِ فایلِ دریافت‌شده `{OPENITI_SNAPSHOTS[TUSI]['fileSha256']}`؛ metadata volume file `{OPENITI_SNAPSHOTS[TUSI]['metadataPath']}`، blob `{OPENITI_SNAPSHOTS[TUSI]['metadataGitBlobSha']}`.
- فیض کاشانی، *الصافي في تفسير كلام الله الوافي*: مخزن `OpenITI/1100AH`، commit `{OPENITI_FAYD_COMMIT}`؛ پروندهٔ `{FAYD_PATH}`، Git blob `{OPENITI_SNAPSHOTS[FAYD]['gitBlobSha']}`، SHA-256ِ فایلِ دریافت‌شده `{OPENITI_SNAPSHOTS[FAYD]['fileSha256']}`؛ metadata volume file `{OPENITI_SNAPSHOTS[FAYD]['metadataPath']}`، blob `{OPENITI_SNAPSHOTS[FAYD]['metadataGitBlobSha']}`.
- metadataهایِ این دو متن آنها را نسخه‌هایی ناقص و اخذشده از altafsir.com معرفی می‌کنند؛ مقدمهٔ اثر، چاپِ مشخص و صفحهٔ چاپی تعیین نشده است. برایِ متن/میزبان مجوزی در این بررسی احراز نشد؛ وضعیتِ اقتباس و بازنشر نامشخص است.
- دامنه‌هایِ گروهی در dossier و کاتالوگ ثبت شده‌اند؛ طوسی در ۵:۱۱۹–۱۲۰ و گروه‌هایِ ۶:۸–۹، ۶:۱۲–۱۳، ۶:۱۷–۱۸، ۶:۲۳–۲۴، ۶:۲۹–۳۰ و ۶:۴۰–۴۱ شرحِ پیوسته دارد. فیض در ۶:۲ نشانِ مستقل ندارد اما در گروهِ ۶:۱–۴ عبارتِ صریحِ آیه و شرحِ اجل‌ها حاضر است؛ در گروهِ ۶:۲۵–۳۱ متن از نشانِ (۲۵) به (۲۷) می‌رسد و موضعِ ۶:۲۶ غایب است. این خلأ تنها به فایلِ بررسی‌شده مربوط است، نه به کلِ اثر.

در فایلِ دادهٔ پژوهشی فقط خلاصه‌هایِ بازنویسی‌شده و نامِ منبع ثبت شده‌اند؛ نسخهٔ خامِ استخراج‌شده در `/tmp/next50-sources.json` موقت بود و در برنامه/مخزن گنجانده نشده است. همهٔ بندها پیش‌نویس‌اند و به داوریِ تخصصی نیاز دارند.
"""
    ATTRIBUTION_PATH.write_text(text.rstrip() + addition, encoding="utf-8")


if __name__ == "__main__":
    main()
