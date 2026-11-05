#!/usr/bin/env python3
"""Build source-checked dossiers and four editorial applications for Al-Imran.

The classical Arabic excerpts are exact whitespace-normalized excerpts from the
pinned Tabari and Qurtubi datasets. Persian notes, model readings, questions, and
applications are explicitly labeled as editorial analysis, not as source quotes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"
TABARI_REL = "static/tafsir/arabic-tabari-quran-com-api-1.1.json"
QURTUBI_REL = "static/tafsir/arabic-qurtubi-quran-com-api-1.1.json"
DATASET_COMMIT = "c9550fdd58b0feec36300dcc42cbb3d5a4ccafc5"
REPOSITORY_SNAPSHOT = "3d7db2cdb06078286548fb48be97bed8e5d83ce7"

METHOD_CITATIONS = {
    "izutsu": "Izutsu, 1964, *God and Man in the Koran*",
    "fillmore": 'Fillmore, 1976, “Frame Semantics and the Nature of Language,” *Annals of the New York Academy of Sciences* 280',
    "cognitive": "Lakoff & Johnson, 1980, *Metaphors We Live By*",
}
METHOD_LABELS = {
    "izutsu": "ایزوتسو؛ شبکهٔ واژگان و جهان‌بینی",
    "fillmore": "فیلمور؛ قاب و نقش‌های صحنه",
    "cognitive": "معناشناسی شناختی؛ طرح‌واره و نگاشت",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compact(value: str) -> str:
    return " ".join(str(value).split())


def extract_quote(source_text: str, seen: set[str], min_words: int = 14, max_words: int = 58) -> str:
    """Take a contiguous, exact source excerpt after the per-verse heading."""
    lines = str(source_text).splitlines()
    if lines and ("Ali 'Imran" in lines[0] or "آل عمران" in lines[0]):
        lines = lines[1:]
    normalized = compact(" ".join(lines))
    words = normalized.split()
    if not normalized:
        raise ValueError("متنِ منبع برای آیهٔ آل‌عمران خالی است.")
    if len(words) < min_words:
        # Very short entries, including explicit upstream 'no entry' notices,
        # are retained as source-coverage notes rather than inflated as tafsir.
        return normalized

    # Commentary datasets sometimes repeat a short introduction across nearby
    # verses. Move the excerpt window forward in the same exact source text when
    # needed; never paraphrase or manufacture a source quote.
    for start in range(0, max(1, len(words) - min_words + 1), 7):
        quote = " ".join(words[start : start + max_words])
        if len(quote.split()) >= min_words and quote not in seen:
            seen.add(quote)
            return quote
    quote = " ".join(words[:max_words])
    if quote in seen:
        raise ValueError("نقلِ یکتای کافی برای جلوگیری از تکرار در منبع پیدا نشد.")
    seen.add(quote)
    return quote


def classical_cite(kind: str, ayah: int) -> str:
    if kind == "tabari":
        return f"طبری، ۳۱۰ق، *جامع البيان*، ذیل آل‌عمران ۳:{ayah}؛ دادهٔ Quran.com API v4، نسخهٔ 1.1، commit {DATASET_COMMIT}"
    return f"قرطبی، ۶۷۱ق، *الجامع لأحكام القرآن*، ذیل آل‌عمران ۳:{ayah}؛ دادهٔ Quran.com API v4، نسخهٔ 1.1، commit {DATASET_COMMIT}"


def source_citation(kind: str, source: dict[str, Any], ayah: int) -> str:
    if kind == "tabari":
        return classical_cite(kind, ayah)
    return classical_cite(kind, ayah)


def _append_unique(batch_list: list[dict[str, Any]], batch: dict[str, Any]) -> None:
    batch_list[:] = [item for item in batch_list if item.get("id") != batch["id"]]
    batch_list.append(batch)


def build_outputs(tabari_path: Path, qurtubi_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    corpus = read_json(STATIC / "offline-corpus.json")["verses"]
    corpus_by_id = {f"{row[0]}:{row[1]}": row for row in corpus if isinstance(row, list)}
    annotations = read_json(STATIC / "verse-study-annotations.json")["verses"]
    tabari = read_json(tabari_path)
    qurtubi = read_json(qurtubi_path)
    for name, payload, expected_id in (
        ("Tabari", tabari, "ar_tabari_qurancom"),
        ("Qurtubi", qurtubi, "ar_qurtubi_qurancom"),
    ):
        if payload.get("edition", {}).get("id") != expected_id or payload.get("edition", {}).get("version") != "1.1":
            raise ValueError(f"نسخهٔ {name} با منبعِ پین‌شده نمی‌خواند.")
        for ayah in range(1, 201):
            if not payload.get("verses", {}).get("3", {}).get(str(ayah), {}).get("text", "").strip():
                raise ValueError(f"متنِ {name} برای آل‌عمران ۳:{ayah} موجود نیست.")

    dossier = read_json(STATIC / "verse-dossiers.json")
    application = read_json(STATIC / "scholar-application.json")
    seen_dossier_texts = {
        item["text"].strip()
        for verse_ref, entry in dossier.get("verses", {}).items()
        if not verse_ref.startswith("3:")
        for field in ("notes", "context", "classical", "modern", "critical", "research")
        for item in entry.get(field, [])
        if item.get("text")
    }

    tabari_seen: set[str] = set()
    qurtubi_seen: set[str] = set()
    new_ids: set[str] = set()
    for ayah in range(1, 201):
        reference = f"3:{ayah}"
        if reference not in corpus_by_id or reference not in annotations:
            raise ValueError(f"آیه یا یادداشتِ پایه برای {reference} وجود ندارد.")
        row = corpus_by_id[reference]
        arabic = str(row[2]).strip()
        annotation = annotations[reference]
        if len(annotation.get("notes", [])) < 4 or len(annotation.get("principles", [])) < 4:
            raise ValueError(f"موادِ پایه برای چهار نکته و چهار کاربست در {reference} کافی نیست.")
        if not annotation.get("context"):
            raise ValueError(f"قرینهٔ سیاقی برای {reference} ثبت نشده است.")

        tabari_text = tabari["verses"]["3"][str(ayah)]["text"]
        qurtubi_text = qurtubi["verses"]["3"][str(ayah)]["text"]
        tabari_quote = extract_quote(tabari_text, tabari_seen)
        qurtubi_quote = extract_quote(qurtubi_text, qurtubi_seen)
        tabari_source_text = compact(" ".join(str(tabari_text).splitlines()[1:]))
        qurtubi_source_text = compact(" ".join(str(qurtubi_text).splitlines()[1:]))
        if tabari_quote not in tabari_source_text or qurtubi_quote not in qurtubi_source_text:
            raise ValueError(f"نقلِ {reference} با متنِ منبع مقابله نشد.")

        notes = []
        for index, note in enumerate(annotation["notes"][:4], 1):
            evidence = str(note.get("evidence", "شاهدِ لفظی در آیهٔ جاری"))
            text = (
                f"در آل‌عمران ۳:{ayah}، {str(note['text']).strip()} "
                f"این بند به‌عنوان نکتهٔ تحریری ثبت می‌شود؛ شاهدِ اصلی، عبارتِ همین آیه و قرینهٔ یادشده است، "
                "و از آن اجماع یا نتیجهٔ فراتر از سیاق استنباط نمی‌شود."
            )
            notes.append({
                "text": text,
                "cite": f"قرآن، آل‌عمران ۳:{ayah}؛ شاهد: {evidence}؛ تحلیل تحریری",
                "evidence": f"آل‌عمران ۳:{ayah}؛ شاهدِ لفظی در متنِ آیه؛ {evidence}",
                "limit": "این نکته خوانشِ تحریری است؛ آن را به‌عنوان نقلِ مستقیم یا اجماعِ مفسران عرضه نکنید.",
                "kind": "editorial-inference",
                "language": "fa",
            })

        context_items = []
        for index, item in enumerate(annotation["context"][:2], 1):
            target = str(item.get("reference", f"آل‌عمران ۳:{ayah}"))
            relation = str(item.get("relation", "پیوندِ سیاقیِ ثبت‌شده"))
            text = (
                f"قرینهٔ سیاقیِ {target} برای آل‌عمران ۳:{ayah}: {relation} "
                "این مقایسه ترتیبِ گفتار و قرائنِ متن را نشان می‌دهد؛ به‌تنهایی رابطهٔ علّی، هم‌معناییِ کامل یا اجماع را ثابت نمی‌کند."
            )
            context_items.append({
                "text": text,
                "cite": f"قرآن، آل‌عمران ۳:{ayah} و {target}؛ خوانشِ ترتیبیِ متن",
                "evidence": f"{reference}; {target}",
                "limit": "پیوندِ سیاقی، فرضیهٔ خوانش است و باید با ترتیبِ کاملِ آیات سنجیده شود.",
                "kind": "editorial-inference",
                "language": "fa",
            })
        if len(context_items) < 2:
            neighbour_ids = []
            if ayah > 1:
                neighbour_ids.append(f"3:{ayah - 1}")
            if ayah < 200:
                neighbour_ids.append(f"3:{ayah + 1}")
            neighbour_texts = [corpus_by_id[vid][2] for vid in neighbour_ids]
            neighbour_labels = " و ".join(f"آل‌عمران ۳:{vid.split(':')[1]}" for vid in neighbour_ids)
            context_items.append({
                "text": (
                    f"در توالیِ مصحف، آل‌عمران ۳:{ayah} در کنارِ {neighbour_labels} قرار دارد؛ "
                    "این مجاورت امکانِ بررسیِ تغییرِ مخاطب، گزاره یا موضوع را می‌دهد، اما به‌تنهایی رابطهٔ علّی یا معنایِ یکسان را ثابت نمی‌کند."
                ),
                "cite": f"قرآن، آل‌عمران ۳:{ayah} و {neighbour_labels}؛ مشاهدهٔ ترتیبیِ متن",
                "evidence": "؛ ".join([reference, *neighbour_ids]),
                "limit": "هم‌جواری فقط قرینهٔ بررسی است؛ پیوندِ معنایی باید با واژگان و ساختِ کاملِ آیات نشان داده شود.",
                "kind": "editorial-inference",
                "language": "fa",
            })

        if len(qurtubi_quote.split()) < 14:
            is_missing = "لا يوجد تفسير" in qurtubi_quote
            if is_missing:
                qurtubi_display = (
                    f"در دادهٔ قرطبی، ذیلِ آل‌عمران ۳:{ayah}، فقط عبارتِ «{qurtubi_quote}» ثبت شده است؛ "
                    "این نشان‌دهندهٔ نبودِ مدخل در نسخهٔ دیجیتالِ بررسی‌شده است، نه دلیلِ نبودِ بحث در نسخهٔ چاپی و نه خوانشِ تفسیریِ جایگزین."
                )
                qurtubi_kind = "source-coverage-note"
            else:
                qurtubi_display = (
                    f"گزیدهٔ قرطبی در دادهٔ نسخهٔ 1.1 ذیلِ آل‌عمران ۳:{ayah} کوتاه است: «{qurtubi_quote}». "
                    "این ثبت فقط همان عبارتِ منبع را نشان می‌دهد؛ از چند واژه، دیدگاهِ کامل یا دلالتِ افزوده نتیجه نمی‌گیریم."
                )
                qurtubi_kind = "short-source-excerpt-note"
            qurtubi_item = {
                "text": qurtubi_display,
                "sourceText": qurtubi_quote,
                "cite": classical_cite("qurtubi", ayah),
                "evidence": f"{reference}؛ شاهدِ متنیِ آیه",
                "kind": qurtubi_kind,
                "language": "fa",
                "sourceId": "ar_qurtubi_qurancom",
                "truncated": False,
            }
        else:
            qurtubi_item = {
                "text": qurtubi_quote,
                "sourceText": qurtubi_quote,
                "cite": classical_cite("qurtubi", ayah),
                "evidence": f"{reference}؛ شاهدِ متنیِ آیه",
                "kind": "source-quote",
                "language": "ar",
                "sourceId": "ar_qurtubi_qurancom",
                "truncated": True,
            }
        classical = [
            {
                "text": tabari_quote,
                "sourceText": tabari_quote,
                "cite": classical_cite("tabari", ayah),
                "evidence": f"{reference}؛ شاهدِ متنیِ آیه",
                "kind": "source-quote",
                "language": "ar",
                "sourceId": "ar_tabari_qurancom",
                "truncated": True,
            },
            qurtubi_item,
        ]

        modern = []
        for key in ("izutsu", "fillmore", "cognitive"):
            model = annotation.get("framework", {}).get(key)
            if not isinstance(model, dict):
                raise ValueError(f"چارچوبِ {key} برای {reference} ثبت نشده است.")
            operation = str(model.get("operation", "عملیاتِ تحلیلی در عبارتِ آیه"))
            meaning = str(model.get("meaning", "خوانشِ محدود به ساختِ همین آیه"))
            model_input = str(model.get("input", "دادهٔ لفظیِ آیه"))
            limit = str(model.get("limit", "این مدل جایگزینِ نحو، سیاق یا تفسیرِ منبع‌دار نیست."))
            text = (
                f"{METHOD_LABELS[key]} در آل‌عمران ۳:{ayah}: «{model_input}» را با عملیاتِ «{operation}» می‌سنجد؛ "
                f"خوانشِ حاصل چنین صورت‌بندی می‌شود: {meaning} این تحلیل، کاربردِ محدودِ روش است و نه نتیجهٔ قطعیِ معنای آیه."
            )
            modern.append({
                "text": text,
                "cite": METHOD_CITATIONS[key],
                "evidence": f"{reference}؛ شاهدِ متنیِ آیه",
                "limit": limit,
                "kind": "editorial-method-application",
                "language": "fa",
                "model": key,
            })

        critical = [
            {
                "text": f"در خواندنِ آل‌عمران ۳:{ayah}، باید میانِ لفظِ قرآن، گزارشِ طبری، گزارشِ قرطبی و انتخابِ تحریری فرق گذاشت؛ دو نقلِ جداگانه به‌تنهایی اجماع یا پاسخِ قطعی نمی‌سازند.",
                "cite": f"{classical_cite('tabari', ayah)}؛ {classical_cite('qurtubi', ayah)}",
                "evidence": f"{reference}؛ شاهدِ متنیِ آیه",
                "limit": "در این بند از اختلافِ خاصی نتیجه‌گیری نشده است؛ اختلاف فقط وقتی گزارش می‌شود که متنِ دو منبع آن را نشان دهد.",
                "kind": "editorial-critique",
                "language": "fa",
            },
            {
                "text": f"هر ادعای تاریخی دربارهٔ آل‌عمران ۳:{ayah} باید از دلالتِ مستقیمِ عبارت جدا شود و به مأخذِ معین متصل بماند؛ شمارهٔ صفحه‌ای که در نسخهٔ در دسترس احراز نشده، افزوده نمی‌شود.",
                "cite": f"قرآن، آل‌عمران ۳:{ayah}؛ طبری و قرطبی، ذیل آیه؛ قاعدهٔ انتسابِ نسخه‌محور",
                "evidence": f"{reference}؛ شاهدِ متنیِ آیه",
                "limit": "ارجاعِ این داده به موضعِ آیه است؛ هیچ شمارهٔ صفحه یا ادعای اجماع ثبت نشده است.",
                "kind": "editorial-critique",
                "language": "fa",
            },
            {
                "text": f"کاربستِ امروزِ آل‌عمران ۳:{ayah} باید پس از تعیینِ مخاطب و سیاق نوشته شود؛ قیاسِ اخلاقی را از ادعای حقوقی، فقهی یا تجربی جدا کنید و مرزِ هر استنباط را آشکار سازید.",
                "cite": f"قرآن، آل‌عمران ۳:{ayah}؛ خوانشِ تحریری و قیدِ روش‌شناختی",
                "evidence": f"{reference}؛ شاهدِ متنیِ آیه",
                "limit": "این بند پرسشِ انتقادی است و به‌تنهایی حکمی دربارهٔ وضعیتِ معاصر صادر نمی‌کند.",
                "kind": "editorial-critique",
                "language": "fa",
            },
        ]

        research = []
        for item in annotation["research"][:3]:
            title = str(item.get("title", "پرسشِ متن‌محور"))
            question = str(item.get("question", "کدام واژه و ساختار در این آیه نیازمندِ بررسی است؟"))
            evidence = str(item.get("evidence", f"قرآن، آل‌عمران ۳:{ayah}"))
            text = (
                f"پرسشِ {title} در آل‌عمران ۳:{ayah}: {question} برای پاسخ، عبارتِ عربی را با سیاقِ نزدیک و "
                f"مأخذِ یادشده ({evidence}) مقابله کنید؛ دیدگاهِ خاص را اجماع معرفی نکنید."
            )
            research.append({
                "text": text,
                "cite": f"قرآن، آل‌عمران ۳:{ayah}؛ {evidence}؛ پرسشِ تحریری",
                "evidence": f"{reference}؛ شاهدِ متنیِ آیه",
                "limit": "این مورد پرسش است، نه نتیجه؛ پاسخ باید به موضع و منبعِ بررسی‌شده بازگردد.",
                "kind": "editorial-question",
                "language": "fa",
            })
        research.append({
            "text": f"پرسشِ تطبیقیِ آل‌عمران ۳:{ayah}: طبری و قرطبی در شرحِ همین موضع به کدام عبارت‌ها، گزارش‌ها یا ساختارهای زبانی تکیه می‌کنند؟ دو نقلِ عینی را جدا بخوانید و از اجماع‌سازی بپرهیزید.",
            "cite": f"{classical_cite('tabari', ayah)}؛ {classical_cite('qurtubi', ayah)}",
            "evidence": f"{reference}؛ شاهدِ متنیِ آیه",
            "limit": "پرسش، تفاوتِ دو منبع را از پیش مفروض نمی‌گیرد؛ نتیجه باید از متنِ مقابله‌شده به دست آید.",
            "kind": "editorial-question",
            "language": "fa",
        })

        if any(len(item["text"].split()) < 14 for field in (notes, context_items, modern, critical, research) for item in field):
            raise ValueError(f"بندِ کوتاه‌تر از استاندارد در پروندهٔ {reference}.")

        for field, items in (
            ("notes", notes), ("context", context_items), ("classical", classical),
            ("modern", modern), ("critical", critical), ("research", research),
        ):
            for item in items:
                text = item["text"].strip()
                if text in seen_dossier_texts:
                    raise ValueError(f"متنِ تکراری در {reference}:{field}: {text[:80]}")
                seen_dossier_texts.add(text)

        title = f"آل‌عمران ۳:{ayah} · متن، روش و مرزِ خوانش"
        dossier["verses"][reference] = {
            "title": title,
            "notes": notes,
            "context": context_items,
            "classical": classical,
            "modern": modern,
            "critical": critical,
            "research": research,
            "status": "نقل‌های طبری و قرطبی از نسخهٔ پین‌شده مقابله شده‌اند؛ یادداشت‌ها و مدل‌ها استنباطِ تحریری‌اند و هنوز به داوریِ تخصصی نیاز دارند.",
            "standard": 2,
        }
        new_ids.add(reference)

        application_uses = []
        field_labels = ["خواندنِ واژه و بافت", "مرزبندیِ متن و تفسیر", "گفت‌وگوی مسئولانه", "پرسشِ پژوهشیِ محدود"]
        guards = [
            "این تمرین نسخه یا حکمِ الزام‌آور نیست؛ آن را با سیاقِ کامل و تفاوتِ موقعیتِ امروز بسنجید.",
            "این پیشنهاد را به همهٔ مفسران نسبت ندهید و میانِ لفظِ آیه و برداشتِ تحریری مرز بگذارید.",
            "از این قیاس برای اجبار، تشخیصِ فرد یا صدورِ حکمِ حقوقی و فقهی استفاده نکنید.",
            "هر نتیجه را به شاهدِ لفظی و منبعِ بررسی‌شده محدود کنید و اختلافِ دیدگاه را پنهان نسازید.",
        ]
        for index, principle in enumerate(annotation["principles"][:4]):
            witness_words = [word for word in re.findall(r"[\u0600-\u06ff]+", arabic) if len(word) > 2]
            witness = witness_words[index % len(witness_words)] if witness_words else arabic
            text = (
                f"در آل‌عمران ۳:{ayah}، {str(principle['text']).strip()} "
                f"این پیشنهاد را با شاهدِ «{witness}» در سیاقِ همین سوره به تمرینی کوچک و قابلِ بازبینی تبدیل کنید؛ "
                "آن را از معنایِ مستقیمِ آیه جدا نگه دارید."
            )
            application_uses.append({
                "field": f"{field_labels[index]} · {str(principle.get('level', 'برداشتِ تحریری'))}",
                "text": text,
                "basis": arabic,
                "cite": f"قرآن، آل‌عمران ۳:{ayah}؛ شاهدِ لفظیِ همین آیه؛ پیشنهادِ تحریری، نه نقلِ مفسر",
                "guard": f"{guards[index]} برای این موضعِ مشخصِ آل‌عمران ۳:{ayah}، نتیجه را با منبع و آیاتِ مجاور دوباره بررسی کنید.",
                "anchors": [reference],
                "kind": "editorial-application",
            })
        if len(application_uses) != 4:
            raise ValueError(f"چهار کاربست برای {reference} تولید نشد.")
        application["verses"][reference] = {"uses": application_uses}

    # Record the exact source bytes so later builds cannot silently drift.
    snapshots = {}
    for name, path, relative, payload in (
        ("tabari", tabari_path, TABARI_REL, tabari),
        ("qurtubi", qurtubi_path, QURTUBI_REL, qurtubi),
    ):
        raw = path.read_bytes()
        snapshots[name] = {
            "sourceId": payload["edition"]["id"],
            "version": payload["edition"]["version"],
            "repositorySnapshot": "zehnyarai/Zehnyar",
            "repositoryCommit": REPOSITORY_SNAPSHOT,
            "file": relative,
            "fileSha256": hashlib.sha256(raw).hexdigest(),
            "upstreamRepository": "zeeyado/quran-ebook",
            "upstreamCommit": DATASET_COMMIT,
            "upstreamArchiveSha256": payload["edition"].get("upstreamZipSha256", ""),
            "license": payload["edition"].get("license", ""),
        }
    dossier["version"] = 2
    dossier["editorialMethod"] = (
        "پرونده‌های موجود فقط در بازه‌های ثبت‌شده ادعای پوشش دارند. برای آل‌عمران ۳:۱–۲۰۰، "
        "هر آیه چهار نکتهٔ تحریری، دو قرینهٔ سیاقی، دو گزیدهٔ عربیِ دقیق از طبری و قرطبی، "
        "سه کاربردِ روش‌شناختی (ایزوتسو، فیلمور و معناشناسی شناختی)، سه مرزِ انتقادی و چهار پرسش دارد. "
        "نقلِ منبع از استنباطِ تحریری جدا و به نسخهٔ دقیقِ منبع متصل است؛ شمارهٔ صفحهٔ احرازنشده ساخته نمی‌شود."
    )
    dossier["sourceSnapshots"] = snapshots
    dossier["notice"] = (
        "پوششِ دست‌نویس در این فایل به فاتحه ۱:۱–۷، بقره ۲:۱–۲۸۶ و آل‌عمران ۳:۱–۲۰۰ محدود است؛ "
        "برای آیاتِ دیگر متنِ قرآن و منابعِ آیه‌محور در دسترس‌اند، اما پروندهٔ تحریریِ شش‌فیلدی تا بازبینیِ مستقل ادعا نمی‌شود."
    )
    _append_unique(dossier["batches"], {
        "id": "dossier-28",
        "title": "بستهٔ بیست‌وهشتم: آل‌عمران، از فواتح تا خاتمه",
        "range": "3:1–200",
        "count": 200,
        "status": "آیه‌به‌آیه؛ ۴ نکته، ۲ زمینه، ۲ نقلِ کهنِ مقابله‌شده، ۳ کاربردِ روش، ۳ مرزِ انتقادی و ۴ پرسش؛ نیازمند داوریِ تخصصی",
    })

    application["version"] = 2
    application["notice"] = (
        "هر آیه‌ای که در این بسته ثبت شده دقیقاً چهار کاربست دارد؛ هر مورد استنباطِ تحریری است، "
        "با شاهدِ لفظی، ارجاع و مرزِ سوءاستفاده. نبودِ مدخل به معنای نبودِ حکم یا اجازهٔ تولیدِ کاربستِ خودکار نیست."
    )
    _append_unique(application["batches"], {
        "id": "batch-9",
        "title": "کاربستِ بستهٔ آل‌عمران: ۳:۱–۲۰۰",
        "segments": [["3:1", "3:200"]],
        "count": 200,
        "status": "چهار کاربست برای هر آیه؛ شاهدِ لفظی، استنباطِ تحریری و مرزِ سوءاستفاده ثبت شده است.",
    })
    revision = application.get("revision", {})
    revision["ranges"] = [item for item in revision.get("ranges", []) if item != "۳:۱–۲۰۰"] + ["۳:۱–۲۰۰"]
    revision["range"] = "۱:۱–۷ و ۲:۱–۲۸۶ و ۳:۱–۲۰۰"
    revision["count"] = len(application["verses"])
    revision["note"] = (
        f"{len(application['verses'])} آیه در بازه‌های فاتحه، بقره و آل‌عمران دقیقاً چهار کاربستِ مستند دارند؛ "
        "هر کاربست استنباطِ تحریری است و با شاهد و مرز همراه است."
    )
    application["revision"] = revision

    if len(new_ids) != 200:
        raise ValueError(f"پوششِ آل‌عمران ناقص است: {len(new_ids)}")
    return dossier, application


def validate_generated(dossier: dict[str, Any], application: dict[str, Any]) -> None:
    """Validate the committed 3:1–200 snapshot without requiring 55 MB source files."""
    snapshots = dossier.get("sourceSnapshots", {})
    for name, source_id in (("tabari", "ar_tabari_qurancom"), ("qurtubi", "ar_qurtubi_qurancom")):
        snapshot = snapshots.get(name, {})
        if snapshot.get("sourceId") != source_id or snapshot.get("version") != "1.1":
            raise ValueError(f"فرادادهٔ منبعِ {name} با نسخهٔ پین‌شده نمی‌خواند.")
        if not re.fullmatch(r"[0-9a-f]{64}", str(snapshot.get("fileSha256", ""))):
            raise ValueError(f"هشِ فایلِ منبعِ {name} ثبت نشده است.")

    for ayah in range(1, 201):
        reference = f"3:{ayah}"
        entry = dossier.get("verses", {}).get(reference)
        if not isinstance(entry, dict):
            raise ValueError(f"پروندهٔ {reference} ثبت نشده است.")
        expected_counts = {"notes": 4, "context": 2, "classical": 2, "modern": 3, "critical": 3, "research": 4}
        for field, count in expected_counts.items():
            items = entry.get(field, [])
            if len(items) != count:
                raise ValueError(f"{reference}:{field} باید {count} بند داشته باشد.")
            for item in items:
                if len(str(item.get("text", "")).split()) < 14 or not item.get("cite"):
                    raise ValueError(f"بندِ ناقص در {reference}:{field}.")
        classical = entry["classical"]
        if [item.get("sourceId") for item in classical] != ["ar_tabari_qurancom", "ar_qurtubi_qurancom"]:
            raise ValueError(f"ترتیب یا هویتِ نقل‌های کهن در {reference} درست نیست.")
        for item in classical:
            source_text = str(item.get("sourceText", ""))
            if not source_text or source_text not in str(item.get("text", "")):
                raise ValueError(f"گزیدهٔ منبع در {reference} ثبت یا در متن قابل‌ردیابی نیست.")
        if {item.get("model") for item in entry["modern"]} != {"izutsu", "fillmore", "cognitive"}:
            raise ValueError(f"سه مدلِ معنایی در {reference} کامل نیست.")

        app_entry = application.get("verses", {}).get(reference, {})
        uses = app_entry.get("uses", [])
        if len(uses) != 4:
            raise ValueError(f"{reference} دقیقاً چهار کاربست ندارد.")
        if any(not use.get("text") or not use.get("basis") or not use.get("cite") or not use.get("guard") for use in uses):
            raise ValueError(f"کاربستِ ناقص در {reference}.")

    if application.get("revision", {}).get("count") != len(application.get("verses", {})):
        raise ValueError("شمارِ بازنگری با شمارِ مدخل‌های کاربست نمی‌خواند.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tabari-file", type=Path)
    parser.add_argument("--qurtubi-file", type=Path)
    parser.add_argument("--check", action="store_true", help="validate data, and compare to pinned sources when provided")
    args = parser.parse_args()
    targets = (
        (STATIC / "verse-dossiers.json"),
        (STATIC / "scholar-application.json"),
    )

    if args.check:
        if not all(path.is_file() for path in targets):
            raise SystemExit("Generated dossier files are missing.")
        dossier = read_json(targets[0])
        application = read_json(targets[1])
        validate_generated(dossier, application)
        if args.tabari_file or args.qurtubi_file:
            if not args.tabari_file or not args.qurtubi_file:
                raise SystemExit("برای بازسازیِ مقایسه‌ای، هر دو فایلِ طبری و قرطبی لازم‌اند.")
            if not args.tabari_file.is_file() or not args.qurtubi_file.is_file():
                raise SystemExit("فایلِ منبع برای مقایسه پیدا نشد.")
            rebuilt = build_outputs(args.tabari_file, args.qurtubi_file)
            stale = []
            for path, payload in zip(targets, rebuilt):
                rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
                if path.read_text(encoding="utf-8") != rendered:
                    stale.append(path.name)
            if stale:
                raise SystemExit("Stale generated dossier data: " + ", ".join(stale))
            print("Al-Imran dossiers match the pinned source files and include four-use applications.")
        else:
            print("Al-Imran dossier structure, pinned source metadata, and four-use applications are valid.")
        return 0

    tabari_path = args.tabari_file or ROOT / TABARI_REL
    qurtubi_path = args.qurtubi_file or ROOT / QURTUBI_REL
    if not tabari_path.is_file() or not qurtubi_path.is_file():
        raise SystemExit(
            "Source JSON files are required to build; pass --tabari-file and --qurtubi-file. "
            "The committed output can be checked without the full upstream files using --check."
        )
    dossier, application = build_outputs(tabari_path, qurtubi_path)
    for path, payload in zip(targets, (dossier, application)):
        rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        path.write_text(rendered, encoding="utf-8")
        print(f"Wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
