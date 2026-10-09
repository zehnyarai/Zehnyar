"""
منطق تحلیل انتخاب رشته (بدون وابستگی به وب).

نکته‌ی مهم: محاسبه‌ی رسمی سازمان سنجش بر اساس «نمره‌ی تراز» انجام می‌شود.
اینجا «درصد وزنی» تخمینی است و فقط برای مقایسه و راهنمایی به کار می‌رود.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .textutil import norm

QUOTAS: list[tuple[str, str]] = [
    ("none", "بدون سهمیه (رقابت آزاد)"),
    ("martyr", "شاهد و ایثارگران"),
    ("basij", "بسیجیان"),
    ("local", "بومی (استانی)"),
    ("disabled", "معلولان"),
    ("needy", "مددجویان و کم‌برخوردار"),
    ("other", "سایر سهمیه‌ها"),
]
QUOTA_LABELS = dict(QUOTAS)
_QUOTA_BY_LABEL = {norm(label): key for key, label in QUOTAS}

UNI_TYPES_ORDER = [
    "دولتی", "وابسته", "آزاد اسلامی", "پیام نور", "غیرانتفاعی", "فرهنگیان",
    "جامع علمی‌کاربردی", "فنی و حرفه‌ای", "مجازی", "سایر",
]

# مترادف‌های علاقه‌مندی برای تطبیق بهتر با نام رشته‌ها
INTEREST_SYNONYMS: dict[str, list[str]] = {
    "برنامه‌نویسی": ["کامپیوتر", "نرم افزار", "هوش مصنوعی", "علوم کامپیوتر", "فناوری اطلاعات", "شبکه"],
    "پزشکی": ["پزشکی", "دندان", "داروساز", "پرستاری", "مامایی", "علوم آزمایشگاهی", "هوشبری", "فیزیوتراپی"],
    "طراحی": ["طراحی", "گرافیک", "صنعتی", "پوشاک", "تصویرسازی"],
    "حقوق": ["حقوق", "قضایی", "قضا"],
    "مدیریت": ["مدیریت", "حسابداری", "بازرگانی", "کسب و کار"],
    "روان‌شناسی": ["روان شناسی", "روانشناسی", "مشاوره"],
    "زبان": ["زبان", "مترجمی", "ترجمه", "آموزش زبان"],
    "معماری": ["معماری", "شهرسازی"],
    "عمران": ["عمران", "سازه", "راهسازی", "ساختمان"],
    "برق": ["برق", "الکترونیک", "مخابرات", "کنترل"],
    "مکانیک": ["مکانیک", "خودرو", "ساخت", "هوافضا"],
    "شیمی": ["شیمی", "پلیمر", "پتروشیمی"],
    "فیزیک": ["فیزیک", "هسته‌ای", "ستاره"],
    "ریاضی": ["ریاضی", "آمار"],
    "کشاورزی": ["کشاورزی", "زراعی", "باغی", "دامپروری", "گیاه"],
    "محیط زیست": ["محیط زیست", "منابع طبیعی", "آبزی", "شیلات"],
    "تاریخ": ["تاریخ", "باستان"],
    "اقتصاد": ["اقتصاد", "بازرگانی"],
    "هنر": ["هنر", "نقاشی", "گرافیک", "سینما", "موسیقی"],
    "سینما": ["سینما", "فیلم", "تصویربرداری", "تئاتر", "بازیگری"],
    "موسیقی": ["موسیقی", "آهنگسازی", "نوازندگی"],
    "ورزش": ["ورزش", "تربیت بدنی"],
    "دین": ["الهیات", "فقه", "قرآن", "معارف", "حدیث", "کلام"],
}


@dataclass
class Profile:
    gpa: float | None = None  # معدل کل سوابق از ۲۰
    pct: dict[str, float] = field(default_factory=dict)  # درصد هر درس
    coef: dict[str, float] = field(default_factory=dict)  # ضریب سفارشی هر درس
    rank_no_quota: int | None = None
    rank_quota: int | None = None
    quota: str = "none"
    province: str | None = None
    univ_types: list[str] = field(default_factory=list)
    interests: list[str] = field(default_factory=list)
    degree: str | None = None  # "کاردانی" | "کارشناسی" | None


def quota_key(value: str | None) -> str:
    if not value:
        return "none"
    v = value.strip()
    if v in QUOTA_LABELS:
        return v
    return _QUOTA_BY_LABEL.get(norm(v), "other")


def parse_interests(text: str | None) -> list[str]:
    parts = re.split(r"[،,;؛\n]+", text or "")
    return [p.strip() for p in parts if p.strip()][:8]


def interest_variants(term: str) -> list[str]:
    n = norm(term)
    variants = {n}
    for key, syns in INTEREST_SYNONYMS.items():
        group = [norm(key)] + [norm(s) for s in syns]
        if any(n == g or (len(n) >= 3 and n in g) for g in group):
            variants.update(group)
    return sorted(v for v in variants if v)


# ---------------------------------------------------------------- نمره‌ها
def exam_percent(group: dict, pct: dict[str, float], coef: dict[str, float]) -> tuple[float | None, list[str]]:
    """میانگین وزنی درصد دروس اختصاصی با ضرایب. دروس خالی نادیده گرفته می‌شوند."""
    total = 0.0
    weight = 0.0
    used: list[str] = []
    for subject in group["exam_subjects"]:
        key = subject["key"]
        p = pct.get(key)
        c = coef.get(key, subject["coef"])
        if p is None or c is None or c <= 0:
            continue
        total += p * c
        weight += c
        used.append(key)
    if weight == 0:
        return None, used
    return total / weight, used


def school_percent(gpa: float | None) -> float | None:
    if gpa is None:
        return None
    return max(0.0, min(20.0, gpa)) / 20 * 100


def combined_score(group: dict, profile: Profile) -> dict:
    """نمره‌ی ترکیبی تخمینی = وزن سوابق × درصد معدل + وزن آزمون × درصد آزمون."""
    warnings: list[str] = []
    exam, used = exam_percent(group, profile.pct, profile.coef)
    total_subjects = len(group["exam_subjects"])
    if exam is not None and len(used) < total_subjects:
        warnings.append("بعضی دروس آزمون وارد نشده‌اند؛ میانگین فقط از دروس واردشده محاسبه شد.")
    school = school_percent(profile.gpa)

    school_w = group["school_weight"] / 100
    exam_w = group["exam_weight"] / 100
    score = None
    if exam is None and school is None:
        warnings.append("برای محاسبه، حداقل معدل یا یک درصد آزمون را وارد کنید.")
    elif school is None:
        score = exam
        warnings.append("معدل وارد نشده؛ نمره فقط از آزمون محاسبه شده است.")
    elif exam is None:
        score = school
        warnings.append("درصد دروس آزمون وارد نشده؛ نمره فقط از معدل محاسبه شده است.")
    else:
        score = school_w * school + exam_w * exam

    if group.get("weights_status") != "verified":
        warnings.append("سهم‌بندی این گروه در منابع تأیید نشده؛ نتیجه تقریبی است.")
    if group.get("coef_status") == "unverified":
        warnings.append("ضرایب دروس این گروه تأیید نشده است؛ نتیجه تقریبی است.")

    return {
        "score": round(score, 2) if score is not None else None,
        "exam_percent": round(exam, 2) if exam is not None else None,
        "school_percent": round(school, 2) if school is not None else None,
        "weights": {"school": group["school_weight"], "exam": group["exam_weight"]},
        "subjects": [
            {
                "key": s["key"],
                "label": s["label"],
                "pct": profile.pct.get(s["key"]),
                "coef": profile.coef.get(s["key"], s["coef"]),
            }
            for s in group["exam_subjects"]
        ],
        "warnings": warnings,
    }


# ---------------------------------------------------------------- پیشنهاد رشته و دانشگاه
def field_suggestions(group_key: str, fields: list[dict], profile: Profile) -> list[dict]:
    """رشته‌های گروه را بر اساس علاقه‌مندی‌ها امتیازدهی می‌کند."""
    terms = [(t, interest_variants(t)) for t in profile.interests]
    out: list[dict] = []
    for f in fields:
        if group_key not in f["groups"]:
            continue
        if profile.degree and not any(d.startswith(profile.degree) for d in f["degrees"]):
            continue
        name_n = norm(f["name"])
        cat_n = norm(f["category"])
        score = 0
        reasons: list[str] = []
        padded = f" {name_n} "
        for label, variants in terms:
            if name_n == norm(label):                          # نام رشته دقیقاً همان علاقه است
                score += 8
                reasons.append(f"مرتبط با علاقه‌ی «{label}»")
            elif any(name_n == v for v in variants):           # نام رشته دقیقاً یکی از مترادف‌هاست
                score += 6
                reasons.append(f"مرتبط با علاقه‌ی «{label}»")
            elif any(f" {v} " in padded for v in variants):    # واژه‌ی کامل در نام
                score += 4
                reasons.append(f"مرتبط با علاقه‌ی «{label}»")
            elif any(v in name_n for v in variants):           # زیررشته (مثلاً «دامپزشکی» برای «پزشکی»)
                score += 2
                reasons.append(f"مرتبط با علاقه‌ی «{label}»")
            elif any(v in cat_n for v in variants):            # هم‌دسته
                score += 1
                reasons.append(f"هم‌دسته با علاقه‌ی «{label}»")
        out.append({"field": f, "score": score, "reasons": reasons})

    if terms:
        matched = [x for x in out if x["score"] > 0]
        if matched:
            out = matched
    out.sort(key=lambda x: (-x["score"], x["field"]["name"]))
    return out


def university_suggestions(group_key: str, unis: list[dict], profile: Profile) -> list[dict]:
    """دانشگاه‌های مرتبط با گروه؛ تخصصی‌ها بالاتر، سپس استان و نوع ترجیحی."""
    out: list[dict] = []
    wanted_types = set(profile.univ_types)
    for u in unis:
        if u["focus"] and group_key not in u["focus"]:
            continue
        if wanted_types and u["type"] not in wanted_types:
            continue
        score = 0
        reasons: list[str] = []
        if group_key in u["focus"]:
            score += 5
            reasons.append("تخصصی این گروه")
        else:
            score += 2
            reasons.append("عمومی و چندرشته‌ای")
        if profile.province and u["province"] == profile.province:
            score += 3
            reasons.append("در استان شما")
        if wanted_types:
            score += 2
            reasons.append("نوع دانشگاه مورد نظر")
        out.append({"university": u, "score": score, "reasons": reasons})
    out.sort(key=lambda x: (-x["score"], x["university"]["province"] != (profile.province or ""),
                            x["university"]["name"]))
    return out


# ---------------------------------------------------------------- شانس قبولی
CHANCE_LEVELS = {
    "high": "شانس بالا",
    "mid": "شانس متوسط",
    "close": "رقابتی (نزدیک مرز)",
    "low": "شانس پایین",
}
_CHANCE_ORDER = {"high": 0, "mid": 1, "close": 2, "low": 3}


def chance_level(rank: int, last_rank: int) -> str:
    """rank: رتبه‌ی داوطلب، last_rank: آخرین رتبه‌ی قبولی سال قبل (عدد بزرگ‌تر یعنی رقابت آسان‌تر)."""
    if rank <= last_rank * 0.85:
        return "high"
    if rank <= last_rank:
        return "mid"
    if rank <= last_rank * 1.15:
        return "close"
    return "low"


def chance_suggestions(group_key: str, cutoffs: list[dict], profile: Profile) -> list[dict]:
    """داده‌ی رتبه‌های قبولی را با رتبه‌ی داوطلب مقایسه می‌کند (فقط اگر داده‌ی سال قبل موجود باشد)."""
    latest: dict[tuple, dict] = {}
    for c in cutoffs:
        if c["group"] != group_key:
            continue
        key = (c["field"], c["university"], c["quota"])
        if key not in latest or c["year"] > latest[key]["year"]:
            latest[key] = c

    out: list[dict] = []
    for c in latest.values():
        if c["quota"] == "none":
            rank = profile.rank_no_quota
        elif profile.quota == c["quota"]:
            rank = profile.rank_quota
        else:
            continue
        if rank is None:
            continue
        level = chance_level(rank, c["last_rank"])
        out.append({
            "field": c["field"],
            "university": c["university"],
            "quota": QUOTA_LABELS.get(c["quota"], c["quota"]),
            "year": c["year"],
            "last_rank": c["last_rank"],
            "your_rank": rank,
            "level": level,
            "label": CHANCE_LEVELS[level],
        })
    # ابتدا بر اساس سطح شانس، سپس بیشترین حاشیه‌ی امنیت (آخرین رتبه - رتبه‌ی شما)
    out.sort(key=lambda x: (_CHANCE_ORDER[x["level"]], -(x["last_rank"] - x["your_rank"])))
    return out
