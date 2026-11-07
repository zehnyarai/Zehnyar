# -*- coding: utf-8 -*-
"""Shared source-diversity policy helpers (policy v2).

Every dossier record must be backed by at least three distinct works, at least
one classical tafsir and at least one contemporary source, with no single
contemporary work supplying more than 60% of the contemporary entries and no
more than one entry from *al-Tafsir al-Muyassar*.  `collect()` derives the
per-verse `sourceMix` that is stored in the JSON data and rendered in the app.
"""
from __future__ import annotations

import re
from collections import Counter

CLASSICAL = {
    "الطبري": ("جامع البيان", "classical"),
    "البغوي": ("معالم التنزيل", "classical"),
    "القرطبي": ("الجامع لأحكام القرآن", "classical"),
    "ابن كثير": ("تفسير القرآن العظيم", "classical"),
    "الواحدي": ("أسباب النزول", "classical"),
    "ابن عاشور": ("التحرير والتنوير", "classical"),
}
MODERN = {
    "التفسير الميسر": ("التفسير الميسر", "modern"),
    "المختصر": ("المختصر في التفسير", "modern"),
    "السعدي": ("تيسير الكريم الرحمن", "modern"),
    "أيسر التفاسير": ("أيسر التفاسير", "modern"),
}
SHIA = {
    "الطبرسي": ("مجمع البيان", "shia-classical"),
    "الطوسي": ("التبيان", "shia-classical"),
    "الفيض الكاشاني": ("الصافي", "shia-classical"),
    "الحويزي": ("نور الثقلين", "shia-classical"),
    "البحراني": ("البرهان", "shia-classical"),
    "القمي": ("تفسير القمي", "shia-classical"),
    "الميزان": ("الميزان", "shia-modern"),
    "الطباطبائي": ("الميزان", "shia-modern"),
    "الطباطبائی": ("الميزان", "shia-modern"),
    "مكارم الشيرازي": ("تفسير نمونه", "shia-modern"),
    "مکارم شیرازی": ("تفسیر نمونه", "shia-modern"),
    "الأمثل": ("الأمثل", "shia-modern"),
    "من وحي القرآن": ("من وحي القرآن", "shia-modern"),
}
JOURNAL_HINTS = (
    "Journal of Qur'anic Studies",
    "Journal of the International Qur",
    "Bulletin of the School of Oriental",
    "Arabica",
    "Der Islam",
    "پژوهشهای",
    "پژوهش‌های",
    "مطالعات قرآن",
    "مطالعات تقریبی",
    "پژوهش",
    "دوفصلنامه",
    "فصلنامه",
    "نشریه",
    "مقالهٔ پژوهشی",
    "پژوهشنامه",
    "تحقیقات علوم قرآن",
    "قرآن‌شناخت",
    "doi.org/10.",
)
LATIN_RE = re.compile(r"[A-Za-z]{3}")

POLICY = {
    "sourcePolicyVersion": 2,
    "minimumDistinctWorksPerRecord": 3,
    "requiredSourceRoles": ["classical", "modern"],
    "maxShareOfContemporaryEntriesFromSingleWork": 0.6,
    "maxMuyassarEntriesPerRecord": 1,
    "diversityPolicyVersion": 3,
    "minShiaWorksPerRecord": 1,
    "minSunniWorksPerRecord": 1,
    "requiresBothTraditions": True,
    "minPeerReviewedArticlesPerRecord": 1,
    "diversityScope": "همهٔ آیاتِ قرآن از ۱۰:۱ تا پایانِ مصحف",
    "diversityPolicyNote": (
        "از يونس ۱۰:۱ تا پایانِ قرآن هر رکورد باید هم‌زمان چهار چیز داشته باشد: دست‌کم یک تفسیرِ کهن، دست‌کم یک "
        "منبعِ معاصر، دست‌کم یک منبعِ شیعی (مجمع البيان/التبيان/الميزان/نمونه) و دست‌کم یک منبعِ سنّی "
        "(جامع البيان/تيسير الكريم الرحمن و مانندِ آن)، و نیز دست‌کم یک مقالهٔ پژوهشیِ داوری‌شده از مجله‌های "
        "معتبرِ داخلی یا خارجی. هیچ سنتی کنار گذاشته نمی‌شود و هیچ ادعای کامل‌بودنی ساخته نمی‌شود."
    ),
    "contemporaryRoles": ["modern", "academic"],
    "sourceMixRequired": True,
    "policyNote": (
        "از توبه ۹:۹۰ به بعد هر پرونده باید دست‌کم سه اثرِ متمایز، یک تفسیرِ کهن و یک منبعِ معاصر داشته باشد. "
        "هیچ اثرِ معاصری (تفسیری یا پژوهشی) نباید بیش از شصت درصدِ مدخل‌های معاصر را بگیرد و التفسیر المیسّر در هر آیه "
        "حداکثر یک مدخل دارد؛ تنوعِ منابع در فیلدِ sourceMix هر آیه ثبت و در اپ نمایش داده می‌شود."
    ),
}


def work_of(cite: str) -> tuple[str, str]:
    cite = cite.strip()
    for token, (name, role) in {**CLASSICAL, **MODERN}.items():
        if cite.startswith(token) or token in cite.split("؛")[0]:
            return name, role
    if cite.startswith("قرآن") or "ترجمهٔ فولادوند" in cite:
        return "متن و ترجمهٔ قرآن", "primary"
    for token, (name, role) in SHIA.items():
        if cite.startswith(token) or token in cite.split("؛")[0]:
            return name, role
    if any(hint in cite for hint in JOURNAL_HINTS):
        title = cite.split("«")[1].split("»")[0].strip() if "«" in cite and "»" in cite else cite.split("؛")[0]
        return title[:60], "journal"
    if LATIN_RE.search(cite):
        head = cite.split(",")[0].strip()
        return head[:60], "academic"
    return cite.split("؛")[0][:60], "other"


def collect(dossier: dict) -> list[dict]:
    counts: Counter[str] = Counter()
    roles: dict[str, str] = {}
    for field in ("notes", "context", "classical", "modern", "critical", "research"):
        for item in dossier.get(field, []):
            name, role = work_of(item.get("cite", ""))
            counts[name] += 1
            roles[name] = role
    for field in dossier.get("extendedFields", {}).values():
        for entry in field.get("entries", []):
            name, role = work_of(entry.get("cite", ""))
            counts[name] += 1
            roles[name] = role
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [{"work": name, "role": roles[name], "entries": n} for name, n in ordered]
