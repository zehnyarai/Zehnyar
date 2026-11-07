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
LATIN_RE = re.compile(r"[A-Za-z]{3}")

POLICY = {
    "sourcePolicyVersion": 2,
    "minimumDistinctWorksPerRecord": 3,
    "requiredSourceRoles": ["classical", "modern"],
    "maxShareOfContemporaryEntriesFromSingleWork": 0.6,
    "maxMuyassarEntriesPerRecord": 1,
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
