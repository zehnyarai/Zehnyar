"""ترکیب نتیجه‌ی کامل تحلیل برای یک گروه و یک پروفایل داوطلب."""
from __future__ import annotations

from .catalog import Catalog
from .scoring import (
    QUOTA_LABELS,
    Profile,
    chance_suggestions,
    combined_score,
    field_suggestions,
    university_suggestions,
)

NOTES = [
    "این نتیجه تخمینی و راهنماست؛ محاسبه‌ی رسمی سازمان سنجش بر اساس نمره‌ی تراز انجام می‌شود.",
    "ضرایب، سهم سوابق و آزمون و فهرست رشته‌ها باید با دفترچه‌ی انتخاب رشته‌ی همان سال تطبیق داده شود.",
    "داده‌ی رتبه‌های قبولی در این نسخه ثبت نشده است؛ بخش شانس قبولی فقط با داده‌ی رسمی فعال می‌شود.",
]


def _field_item(entry: dict) -> dict:
    return {**entry["field"], "reasons": entry["reasons"], "score": entry["score"],
            "groups": entry["field"]["groups"], "degrees": entry["field"]["degrees"]}


def _uni_item(entry: dict, catalog: Catalog) -> dict:
    return {**catalog.uni_view(entry["university"]), "reasons": entry["reasons"], "score": entry["score"]}


def run_analysis(catalog: Catalog, group_slug: str, profile: Profile, premium: bool,
                 free_limit: int) -> dict | None:
    group = catalog.group_by_slug.get(group_slug)
    if group is None:
        return None
    key = group["data_key"]

    score = combined_score(group, profile)
    fields_all = [{"field": catalog.field_view(x["field"]), "score": x["score"], "reasons": x["reasons"]}
                  for x in field_suggestions(key, catalog.fields, profile)]
    unis_all = university_suggestions(key, catalog.universities, profile)
    chances_all = chance_suggestions(key, catalog.cutoffs, profile) if catalog.cutoffs else []

    def cut(items: list) -> list:
        return items if premium else items[:free_limit]

    field_items = [_field_item(x) for x in cut(fields_all)]
    uni_items = [{**catalog.uni_view(x["university"]), "reasons": x["reasons"], "score": x["score"]}
                 for x in cut(unis_all)]

    if not catalog.cutoffs:
        chance_message = ("داده‌ی آخرین رتبه‌های قبولی هنوز بارگذاری نشده است. "
                          "پس از وارد شدن داده‌ی رسمی، شانس قبولی هر رشته و دانشگاه نشان داده می‌شود.")
    elif not chances_all:
        chance_message = "برای این گروه یا رتبه‌ی واردشده، داده‌ای در پایگاه داده‌ی رتبه‌ها پیدا نشد."
    else:
        chance_message = ""

    return {
        "group": {"slug": group_slug, "title": group["title"], "key": key},
        "score": score,
        "ranks": {
            "no_quota": profile.rank_no_quota,
            "quota": profile.rank_quota,
            "quota_label": QUOTA_LABELS.get(profile.quota, ""),
        },
        "fields": {
            "total": len(fields_all),
            "shown": len(field_items),
            "locked": (not premium) and len(fields_all) > len(field_items),
            "items": field_items,
            "interest_matched": bool(profile.interests) and any(x["score"] > 0 for x in fields_all),
        },
        "universities": {
            "total": len(unis_all),
            "shown": len(uni_items),
            "locked": (not premium) and len(unis_all) > len(uni_items),
            "items": uni_items,
        },
        "chances": {
            "available": bool(catalog.cutoffs),
            "total": len(chances_all),
            "shown": len(cut(chances_all)),
            "locked": (not premium) and len(chances_all) > free_limit,
            "items": cut(chances_all),
            "message": chance_message,
        },
        "premium": premium,
        "free_limit": free_limit,
        "notes": NOTES,
    }
