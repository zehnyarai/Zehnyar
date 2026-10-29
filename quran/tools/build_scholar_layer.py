#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ساخت لایهٔ پژوهشیِ هر آیه.

هر آیه سه چیز می‌گیرد:
  ۱) لنگرهای موضوعی، فقط وقتی تطابقِ واژگانیِ مطمئن باشد (مرزِ واژه، وزنِ کم‌بسامدی)؛
  ۲) یک لنگر روشیِ کهن و یک لنگر روشیِ معاصر، که برای همهٔ آیه‌ها معنا دارد؛
  ۳) اگر در فایلِ نمونهٔ بازبینی‌شده باشد، پروندهٔ دست‌نویسِ کامل.

ورودی : data/scholar-bank.json، data/scholar-pilot.json، static/offline-corpus.json
خروجی : static/verse-scholar-layer.json
"""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "static" / "scholar-bank.json"
PILOT = ROOT / "static" / "scholar-pilot.json"
CORPUS = ROOT / "static" / "offline-corpus.json"
OUT = ROOT / "static" / "verse-scholar-layer.json"

DIACRITICS = re.compile(r"[\u064B-\u0652\u0670\u0640]")
AR_LETTER = r"\u0621-\u064A"
MIN_TOPIC_SCORE = 0.40


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = DIACRITICS.sub("", text)
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ى", "ی"), ("ي", "ی"), ("ك", "ک")):
        text = text.replace(a, b)
    return text.replace("\u200c", " ").strip()


def has_word(word: str, text: str) -> bool:
    return re.search(r"(?<![" + AR_LETTER + "])" + re.escape(word) + r"(?![" + AR_LETTER + "])", text) is not None


KEYWORDS = {
    "عدالت": ["عدل", "قسط", "میزان", "ظلم"],
    "تقوا": ["تقوا", "اتقی", "یتق", "متقین"],
    "توحید": ["احد", "صمد", "شرک", "یشرک", "اله"],
    "نبوت": ["نبی", "رسول", "رسل", "انبیا", "وحی"],
    "معاد": ["قیامت", "بعث", "جنت", "جهنم", "اخرة", "اخره"],
    "عبادت": ["صلوة", "صلاة", "زکوة", "صوم", "حج"],
    "خانواده": ["نکاح", "زوج", "نساء", "والد", "طلاق"],
    "اقتصاد": ["ربوا", "بیع", "تجارة", "انفاق", "صدقة"],
    "جهاد": ["جهاد", "قتال", "قاتل", "مشرکین", "یقاتل"],
    "حکومت": ["حکم", "امرة", "اولی الامر", "طاعة", "سلطان"],
    "علم": ["یعلم", "عالم", "حکمة", "یعقل"],
    "عقل": ["یعقل", "تفکر", "تدبر", "الالباب"],
    "اخلاق": ["معروف", "احسان", "صدق", "کذب", "خلق"],
    "گناه": ["ذنب", "اثم", "سیئة", "فسق"],
    "توبه": ["توب", "استغفر", "غفر", "اناب"],
    "دعا": ["دعا", "ادع", "استجاب"],
    "شکر": ["شکر", "حمد", "فضل"],
    "صبر": ["صبر", "صابر", "استعین"],
    "مرگ": ["موت", "مات", "اجل", "قبر"],
    "حساب": ["حساب", "وزن", "جزا"],
}

CLASSICAL_METHOD = ["classical-hujjiyyat", "classical-siyyaq", "classical-mutashabih",
                    "classical-maqasid", "classical-naskh"]
MODERN_METHOD = ["modern-tafsir-ray", "modern-taqti", "modern-naql",
                 "modern-argumentative", "modern-cognitive"]


def main() -> None:
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    pilot = json.loads(PILOT.read_text(encoding="utf-8"))["verses"]
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))["verses"]

    anchor_ids = {a["id"] for a in bank["anchors"]}
    topic_anchors = {t: [a for a in ids if a in anchor_ids] for t, ids in bank["topics"].items()}
    for missing in [a for ids in bank["topics"].values() for a in ids if a not in anchor_ids]:
        raise SystemExit(f"لنگر ناموجود در بانک: {missing}")

    records = []
    for record in corpus:
        if isinstance(record, list):
            records.append((f"{record[0]}:{record[1]}", norm(record[2])))
        else:
            records.append((record.get("id"), norm(record.get("arabic", ""))))

    prepared = {t: [norm(w) for w in ws] for t, ws in KEYWORDS.items() if t in topic_anchors}
    df = {}
    for words in prepared.values():
        for word in words:
            if word not in df:
                df[word] = sum(1 for _, text in records if has_word(word, text))
    weight = {w: 1.0 / (1.0 + df[w] / 40.0) for w in df}

    verses, with_topic = {}, 0
    for vid, text in records:
        scored = []
        for topic, words in prepared.items():
            matched = [w for w in words if has_word(w, text)]
            if matched:
                score = sum(sorted((weight[w] for w in matched), reverse=True)[:2])
                if score >= MIN_TOPIC_SCORE:
                    scored.append((score, topic))
        scored.sort(reverse=True)
        picked = []
        for _, topic in scored[:2]:
            for aid in topic_anchors[topic]:
                if aid not in picked:
                    picked.append(aid)
        if picked:
            with_topic += 1
        seed = sum(ord(ch) for ch in vid)
        method = [CLASSICAL_METHOD[seed % len(CLASSICAL_METHOD)],
                  MODERN_METHOD[(seed // 3) % len(MODERN_METHOD)]]
        for aid in method:
            if aid not in picked:
                picked.append(aid)
        verses[vid] = picked[:4]

    payload = {
        "version": 1,
        "notice": "لنگرهای پژوهشیِ هر آیه از بانکِ منابعِ کهن و معاصر گرفته شده‌اند. لنگر، ابزارِ سنجشِ خوانش است، نه تفسیرِ آیه.",
        "anchors": verses,
        "pilot": sorted(pilot),
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"آیه‌ها: {len(verses)} · با لنگر موضوعی: {with_topic} · نمونهٔ بازبینی‌شده: {len(pilot)}")
    print(f"حجم خروجی: {OUT.stat().st_size / 1024:.0f} کیلوبایت")


if __name__ == "__main__":
    main()
