"""Zehnyar — transparent, evidence-first thematic exploration of the Qur'an.

The application deliberately separates lexical retrieval from heuristic thematic links.
It does not generate fatwas or present an automated summary as a substitute for tafsir.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

ARABIC_MARKS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u08d4-\u08ff]")
PUNCTUATION = re.compile(r"[^\w\s\u0600-\u06ff]")
WHITESPACE = re.compile(r"\s+")


def normalize(value: str) -> str:
    """Normalize Arabic/Persian text for retrieval while retaining display text unchanged."""
    value = ARABIC_MARKS.sub("", value or "")
    value = value.translate(
        str.maketrans(
            {
                "ٱ": "ا",
                "أ": "ا",
                "إ": "ا",
                "آ": "ا",
                "ى": "ی",
                "ي": "ی",
                "ئ": "ی",
                "ؤ": "و",
                "ك": "ک",
                "ة": "ه",
                "ـ": "",
                "‌": " ",
            }
        )
    )
    value = PUNCTUATION.sub(" ", value.lower())
    return WHITESPACE.sub(" ", value).strip()


# The vocabulary is intentionally small, reviewable, and shown to the user in the UI.
# It makes semantic expansion auditable rather than hiding an opaque embedding model.
TOPICS: dict[str, dict[str, Any]] = {
    "عدالت": {
        "aliases": ["عدالت", "عدل", "قسط", "انصاف", "میزان", "دادگری"],
        "terms": [
            ("عدل", "عدالت / توازن"),
            ("قسط", "دادگری"),
            ("میزان", "سنجش و تراز"),
            ("بالقسط", "به دادگری"),
            ("شهداء بالقسط", "گواهان به قسط"),
            ("عدالت", "ترجمهٔ عدالت"),
            ("انصاف", "ترجمهٔ انصاف"),
            ("دادگری", "ترجمهٔ دادگری"),
        ],
        "description": "عدالت در این نقشه با واژگان قسط، عدل و میزان دنبال می‌شود؛ دامنهٔ آن در هر آیه باید با سیاق همان آیه خوانده شود.",
        "questions": ["مخاطبِ فرمان به قسط در این آیه کیست؟", "آیا آیه ناظر به داوری، شهادت، اقتصاد یا رفتار فردی است؟"],
    },
    "رحمت": {
        "aliases": ["رحمت", "مهربانی", "بخشش", "آمرزش", "رأفت", "مغفرت"],
        "terms": [
            ("رحم", "رحمت"),
            ("رحمن", "بخشندگی فراگیر"),
            ("رحیم", "مهربانی"),
            ("رأف", "رأفت"),
            ("غفر", "آمرزش"),
            ("رحمت", "ترجمهٔ رحمت"),
            ("آمرزش", "ترجمهٔ آمرزش"),
            ("مهربان", "ترجمهٔ مهربانی"),
        ],
        "description": "این خوشه میان رحمت، رأفت و مغفرت تفاوت می‌گذارد و آن‌ها را به‌عنوان هم‌معناهای مطلق تلقی نمی‌کند.",
        "questions": ["رحمت در این آیه صفت الهی است یا دستور اخلاقی؟", "رابطهٔ رحمت با توبه، عمل یا هدایت در سیاق چیست؟"],
    },
    "علم": {
        "aliases": ["علم", "دانش", "آگاهی", "تعلیم", "تفکر", "اندیشه", "عقل", "یادگیری"],
        "terms": [
            ("علم", "دانش"),
            ("یعلم", "دانستن"),
            ("تعلم", "آموختن"),
            ("عقل", "خردورزی"),
            ("یتفکر", "اندیشیدن"),
            ("تدبر", "تدبر"),
            ("دانش", "ترجمهٔ دانش"),
            ("آگاه", "ترجمهٔ آگاهی"),
            ("بیندیش", "ترجمهٔ اندیشیدن"),
        ],
        "description": "در این مسیر، علم، تعقل و تفکر با برچسب‌های جدا بازیابی می‌شوند تا تفاوت نقش معرفتی آن‌ها پنهان نشود.",
        "questions": ["فاعلِ دانستن یا اندیشیدن در آیه کیست؟", "آیا سخن از دانایی الهی، تجربه، نشانه‌ها یا مسئولیت معرفتی است؟"],
    },
    "خانواده": {
        "aliases": ["خانواده", "ازدواج", "همسر", "والدین", "پدر", "مادر", "فرزند", "طلاق"],
        "terms": [
            ("زوج", "همسران"),
            ("نساء", "زنان"),
            ("والد", "والدین"),
            ("امهات", "مادران"),
            ("اباء", "پدران"),
            ("ابن", "فرزندان"),
            ("ذری", "ذریه"),
            ("نکاح", "ازدواج"),
            ("طلاق", "طلاق"),
            ("خانواده", "ترجمهٔ خانواده"),
            ("همسر", "ترجمهٔ همسر"),
            ("والدین", "ترجمهٔ والدین"),
            ("مادر", "ترجمهٔ مادر"),
            ("فرزند", "ترجمهٔ فرزند"),
        ],
        "description": "«خانواده» واژه‌ای پوششی است؛ نتایج بر پایهٔ نقش‌های خویشاوندی و احکام مربوط بازیابی و از هم تفکیک می‌شوند.",
        "questions": ["آیه دربارهٔ حق، مسئولیت یا توصیف یک رابطه سخن می‌گوید؟", "آیا قیدها و استثناهای آیه در نتیجه لحاظ شده‌اند؟"],
    },
    "صبر": {
        "aliases": ["صبر", "پایداری", "استقامت", "شکیبایی", "بردباری"],
        "terms": [
            ("صبر", "شکیبایی"),
            ("صابر", "صبرکنندگان"),
            ("اصبر", "فرمان به صبر"),
            ("استعینوا بالصبر", "یاری‌جستن از صبر"),
            ("صبر", "ترجمهٔ صبر"),
            ("شکیبا", "ترجمهٔ شکیبایی"),
            ("پایداری", "ترجمهٔ پایداری"),
        ],
        "description": "صبر با موقعیت‌های آزمون، عبادت و پایداری بررسی می‌شود؛ صرفِ هم‌جواری، هم‌معنایی قطعی نیست.",
        "questions": ["صبر در این آیه در برابر چه وضعیتی آمده است؟", "آیا آیه وعده، فرمان یا توصیف یک گروه را بیان می‌کند؟"],
    },
    "توبه": {
        "aliases": ["توبه", "بازگشت", "پشیمانی", "بخشش گناه", "استغفار"],
        "terms": [
            ("توب", "توبه"),
            ("استغفر", "آمرزش‌خواهی"),
            ("غفور", "بسیار آمرزنده"),
            ("غفار", "آمرزنده"),
            ("تابوا", "بازگشتند"),
            ("توبه", "ترجمهٔ توبه"),
            ("آمرزش", "ترجمهٔ آمرزش"),
            ("استغفار", "ترجمهٔ استغفار"),
        ],
        "description": "توبه، استغفار و مغفرت در نتایج با نسبت‌شان به متن نشان داده می‌شوند، نه به‌عنوان مراحل قطعی یک الگو.",
        "questions": ["آیا آیه شرط یا نشانه‌ای برای توبه مطرح می‌کند؟", "مخاطب و زمانِ بازگشت در سیاق آیه چیست؟"],
    },
    "انفاق": {
        "aliases": ["انفاق", "صدقه", "بخشش مالی", "زکات", "کمک", "بخشندگی"],
        "terms": [
            ("انفق", "انفاق"),
            ("زک", "زکات / پاکی"),
            ("صدقات", "صدقه"),
            ("اطعم", "خوراک‌دادن"),
            ("مال", "مال"),
            ("انفاق", "ترجمهٔ انفاق"),
            ("زکات", "ترجمهٔ زکات"),
            ("صدقه", "ترجمهٔ صدقه"),
        ],
        "description": "این خوشه میان انفاق، زکات، صدقه و اطعام تمایز می‌گذارد و نتایج را با واژهٔ شاهد نمایش می‌دهد.",
        "questions": ["موضوعِ بخشش در آیه چیست و مخاطب آن کیست؟", "آیا آیه قید نیت، زمان یا شیوهٔ پرداخت دارد؟"],
    },
    "آزادی و اختیار": {
        "aliases": ["آزادی", "اختیار", "اجبار", "انتخاب", "اراده", "مسئولیت"],
        "terms": [
            ("اکراه", "اجبار"),
            ("شاء", "خواستن"),
            ("اختار", "برگزیدن"),
            ("کسب", "کسب و مسئولیت"),
            ("اراده", "ترجمهٔ اراده"),
            ("اجبار", "ترجمهٔ اجبار"),
            ("اختیار", "ترجمهٔ اختیار"),
            ("انتخاب", "ترجمهٔ انتخاب"),
        ],
        "description": "این موضوعِ پیچیده با واژه‌های نزدیک بازیابی می‌شود؛ نسبت ارادهٔ الهی و کنش انسانی نیازمند مطالعهٔ تفسیری جداگانه است.",
        "questions": ["فاعلِ خواستن یا انتخاب در آیه کیست؟", "آیا آیه در مقام گزارش، دعوت یا داوری اخلاقی است؟"],
    },
}


def load_corpus() -> tuple[list[dict[str, Any]], dict[tuple[int, int], dict[str, Any]], dict[int, dict[str, Any]]]:
    with (DATA_DIR / "quran-uthmani.json").open(encoding="utf-8") as file:
        arabic = json.load(file)
    with (DATA_DIR / "quran-fa-ih.json").open(encoding="utf-8") as file:
        persian = json.load(file)
    with (DATA_DIR / "chapters.json").open(encoding="utf-8") as file:
        chapters_data = json.load(file)["chapters"]

    chapters = {item["id"]: item for item in chapters_data}
    corpus: list[dict[str, Any]] = []
    verse_map: dict[tuple[int, int], dict[str, Any]] = {}

    for chapter_key, ayat in arabic.items():
        for arabic_ayah, persian_ayah in zip(ayat, persian[chapter_key]):
            chapter = int(arabic_ayah["chapter"])
            verse = int(arabic_ayah["verse"])
            record = {
                "surah": chapter,
                "ayah": verse,
                "arabic": arabic_ayah["text"],
                "persian": persian_ayah["text"],
                "arabic_normalized": normalize(arabic_ayah["text"]),
                "persian_normalized": normalize(persian_ayah["text"]),
                "surah_name": chapters[chapter]["name"],
                "surah_type": "مدنی" if chapters[chapter]["type"] == "medinan" else "مکی",
            }
            corpus.append(record)
            verse_map[(chapter, verse)] = record
    return corpus, verse_map, chapters


CORPUS, VERSE_MAP, CHAPTERS = load_corpus()


class AnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=120)
    limit: int = Field(default=12, ge=6, le=24)
    include_context: bool = True


def find_topic(query: str) -> tuple[str | None, dict[str, Any] | None]:
    query_normalized = normalize(query)
    matches: list[tuple[int, str, dict[str, Any]]] = []
    for title, topic in TOPICS.items():
        for alias in topic["aliases"]:
            alias_normalized = normalize(alias)
            if alias_normalized and alias_normalized in query_normalized:
                matches.append((len(alias_normalized), title, topic))
    if not matches:
        return None, None
    _, title, topic = max(matches, key=lambda item: item[0])
    return title, topic


def contains_term(record: dict[str, Any], normalized_term: str) -> bool:
    return normalized_term in record["arabic_normalized"] or normalized_term in record["persian_normalized"]


def make_terms(query: str, topic: dict[str, Any] | None) -> list[tuple[str, str, bool]]:
    """Return normalized query expansion terms: term, readable label, is_query_term."""
    output: list[tuple[str, str, bool]] = []
    query_normalized = normalize(query)
    if query_normalized:
        output.append((query_normalized, "عبارتِ جست‌وجوشده", True))
        # Individual meaningful query tokens help a phrase such as «عدالت در تجارت».
        for token in query_normalized.split():
            if len(token) >= 3 and token != query_normalized:
                # A component of a multiword query is useful retrieval evidence,
                # but is not labelled as a direct mention of the whole phrase.
                output.append((token, f"واژهٔ «{token}»", False))
    if topic:
        for term, label in topic["terms"]:
            normalized_term = normalize(term)
            if normalized_term:
                output.append((normalized_term, label, normalized_term == query_normalized))

    seen: set[str] = set()
    unique: list[tuple[str, str, bool]] = []
    for item in output:
        if item[0] not in seen:
            unique.append(item)
            seen.add(item[0])
    return unique


def evidence_for(record: dict[str, Any], terms: list[tuple[str, str, bool]]) -> tuple[int, list[str], bool]:
    score = 0
    labels: list[str] = []
    direct = False
    for term, label, is_query_term in terms:
        if contains_term(record, term):
            labels.append(label)
            score += 8 if is_query_term else 4
            direct = direct or is_query_term
    # A compact preference for verses where the word occurs in the Arabic original.
    if labels and any(term in record["arabic_normalized"] for term, _, _ in terms):
        score += 1
    return score, labels[:4], direct


def serialize_verse(record: dict[str, Any], score: int, matches: list[str], relation: str) -> dict[str, Any]:
    return {
        "id": f"{record['surah']}:{record['ayah']}",
        "surah": record["surah"],
        "ayah": record["ayah"],
        "reference": f"{record['surah_name']} {record['surah']}:{record['ayah']}",
        "revelation": record["surah_type"],
        "arabic": record["arabic"],
        "persian": record["persian"],
        "score": score,
        "matches": matches,
        "relation": relation,
    }


def surrounding_context(record: dict[str, Any]) -> list[dict[str, Any]]:
    context: list[dict[str, Any]] = []
    for delta in (-1, 1):
        neighbor = VERSE_MAP.get((record["surah"], record["ayah"] + delta))
        if neighbor:
            context.append(
                serialize_verse(
                    neighbor,
                    0,
                    ["همسایگی خطی با آیهٔ بازیابی‌شده"],
                    "سیاق خطی",
                )
            )
    return context


def graph_payload(canonical: str, terms: list[tuple[str, str, bool]], verses: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = [
        {
            "id": "topic",
            "label": canonical,
            "meta": "پرسشِ کاربر",
            "kind": "topic",
            "weight": 1,
        }
    ]
    edges: list[dict[str, str]] = []
    term_nodes = []
    for index, (term, label, direct) in enumerate(terms[:4]):
        identifier = f"term-{index}"
        term_nodes.append((identifier, term, label))
        nodes.append(
            {
                "id": identifier,
                "label": label.replace("ترجمهٔ ", ""),
                "meta": "واژهٔ جست‌وجو" if direct else "واژهٔ هم‌خانواده",
                "kind": "term",
                "weight": 0.75,
            }
        )
        edges.append({"source": "topic", "target": identifier, "label": "گسترش شفاف"})

    for index, verse in enumerate(verses[:6]):
        identifier = f"verse-{index}"
        nodes.append(
            {
                "id": identifier,
                "label": verse["reference"],
                "meta": verse["relation"],
                "kind": "verse",
                "weight": 0.5,
            }
        )
        match_index = index % max(len(term_nodes), 1)
        source = term_nodes[match_index][0] if term_nodes else "topic"
        edges.append({"source": source, "target": identifier, "label": verse["relation"]})
    return {"nodes": nodes, "edges": edges}


def analyze(query: str, limit: int, include_context: bool) -> dict[str, Any]:
    cleaned_query = WHITESPACE.sub(" ", query).strip()
    if not cleaned_query:
        raise HTTPException(status_code=422, detail="عبارت جست‌وجو نمی‌تواند خالی باشد.")

    canonical, topic = find_topic(cleaned_query)
    terms = make_terms(cleaned_query, topic)
    candidates: list[tuple[dict[str, Any], int, list[str], bool]] = []
    for record in CORPUS:
        score, labels, direct = evidence_for(record, terms)
        if score:
            candidates.append((record, score, labels, direct))

    candidates.sort(key=lambda item: (-item[1], item[0]["surah"], item[0]["ayah"]))
    direct_candidates = [item for item in candidates if item[3]]
    thematic_candidates = [item for item in candidates if not item[3]]

    # Keep direct evidence first, then add transparent, tagged thematic evidence.
    selected = (direct_candidates + thematic_candidates)[:limit]
    verses = [
        serialize_verse(
            record,
            score,
            labels,
            "ذکر / ترجمهٔ مستقیم" if direct else "پیوند واژگانیِ موضوعی",
        )
        for record, score, labels, direct in selected
    ]

    contexts: list[dict[str, Any]] = []
    if include_context and selected:
        seen = {item["id"] for item in verses}
        for record, _, _, _ in selected[:3]:
            for neighbor in surrounding_context(record):
                if neighbor["id"] not in seen:
                    contexts.append(neighbor)
                    seen.add(neighbor["id"])
                if len(contexts) >= 4:
                    break
            if len(contexts) >= 4:
                break

    surah_counts = Counter(record["surah"] for record, _, _, _ in candidates)
    canonical_label = canonical or cleaned_query
    expansion_labels = [label for _, label, is_query in terms if not is_query][:6]
    summary = (
        f"برای «{canonical_label}»، {len(direct_candidates)} شاهدِ دارای عبارتِ جست‌وجوشده و "
        f"{len(thematic_candidates)} شاهدِ دارای واژه‌های هم‌خانواده بازیابی شد. "
        "نتایجِ موضوعی با برچسب واژهٔ شاهد نمایش داده شده‌اند تا مسیر استدلال قابل بازبینی بماند."
    )
    if not candidates:
        summary = (
            f"برای «{cleaned_query}» در بازیابی واژگانیِ فعلی شاهدی پیدا نشد. "
            "صورت عربیِ واژه، ریشهٔ کوتاه‌تر یا یکی از پیشنهادهای موضوعی را امتحان کنید."
        )

    method = {
        "title": "روشِ بازیابیِ قابل‌ممیزی",
        "steps": [
            "متن عربی و ترجمهٔ فارسی به‌صورت جداگانه نرمال‌سازی و جست‌وجو می‌شوند.",
            "ذکر مستقیم از پیوند واژگانیِ موضوعی جدا و روی هر آیه برچسب‌گذاری می‌شود.",
            "برای جلوگیری از بریده‌خوانی، همسایه‌های خطیِ چند آیهٔ اول نیز نشان داده می‌شوند.",
            "نقشهٔ گراف فقط پیوندهای قابل مشاهدهٔ همین بازیابی را نشان می‌دهد؛ نتیجهٔ تفسیریِ قطعی نیست.",
        ],
    }
    graph_terms = terms if terms else [(normalize(cleaned_query), "عبارتِ جست‌وجوشده", True)]
    return {
        "query": cleaned_query,
        "canonical_topic": canonical,
        "summary": summary,
        "topic_description": topic["description"] if topic else "جست‌وجوی آزاد، بدون توسعهٔ موضوعیِ ازپیش‌تعریف‌شده.",
        "questions": topic["questions"] if topic else [
            "این واژه در کدام نقش دستوری و سیاق به کار رفته است؟",
            "آیا صورت عربی یا واژهٔ هم‌ریشه‌ای برای جست‌وجوی دقیق‌تر وجود دارد؟",
        ],
        "stats": {
            "direct": len(direct_candidates),
            "thematic": len(thematic_candidates),
            "surahs": len(surah_counts),
            "shown": len(verses),
        },
        "expansion": expansion_labels,
        "verses": verses,
        "context": contexts,
        "graph": graph_payload(canonical_label, graph_terms, verses),
        "method": method,
        "corpus": {
            "arabic": "Tanzil Uthmani (verbatim)",
            "persian": "QuranEnc — Persian, Ihsan Elahi Zaheer",
            "total_verses": len(CORPUS),
        },
    }


app = FastAPI(
    title="ذهن‌یار | پژوهش موضوعی قرآن",
    version="1.0.0",
    description="بازیابی شفاف واژگانی و پیوندهای موضوعی در متن قرآن، با نمایش شواهد و سیاق.",
)


@app.get("/api/health", tags=["system"])
def health() -> dict[str, Any]:
    return {"status": "ok", "verses": len(CORPUS), "topics": len(TOPICS)}


@app.get("/api/meta", tags=["research"])
def meta() -> dict[str, Any]:
    return {
        "topics": [
            {"title": title, "aliases": topic["aliases"], "description": topic["description"]}
            for title, topic in TOPICS.items()
        ],
        "corpus": {"verses": len(CORPUS), "arabic": "Tanzil Uthmani", "persian": "QuranEnc Persian (Ihsan Elahi Zaheer)"},
    }


@app.post("/api/analyze", tags=["research"])
def analyze_topic(request: AnalyzeRequest) -> dict[str, Any]:
    return analyze(request.query, request.limit, request.include_context)


@app.get("/api/analyze", tags=["research"])
def analyze_topic_get(
    q: str = Query(..., min_length=1, max_length=120),
    limit: int = Query(default=12, ge=6, le=24),
) -> dict[str, Any]:
    return analyze(q, limit, True)


@app.get("/api/verse/{surah}/{ayah}", tags=["research"])
def get_verse(surah: int, ayah: int) -> dict[str, Any]:
    record = VERSE_MAP.get((surah, ayah))
    if not record:
        raise HTTPException(status_code=404, detail="آیه پیدا نشد.")
    return serialize_verse(record, 0, [], "متنِ پایه")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
