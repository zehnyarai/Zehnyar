"""مشاور هوشمند اختیاری (Groq) با بازگشت بی‌خطر به پاسخ قطعی.

اگر کلید API تنظیم نشده باشد، برنامه بدون هوش مصنوعی هم کامل کار می‌کند.
"""
from __future__ import annotations

import json
import os

import httpx

SYSTEM_PROMPT = (
    "تو «مهاجریار» هستی؛ دستیار تحلیل مسیر مهاجرت به زبان فارسی. "
    "فقط بر اساس داده‌های ارزیابی که در پیام کاربر آمده پاسخ بده و عدد یا قانون از خودت نساز. "
    "اگر داده‌ای در دسترس نیست صریح بگو که باید در صفحه‌ی رسمی بررسی شود. "
    "پاسخ کوتاه، ساختارمند و حداکثر ۲۰۰ کلمه باشد؛ از تعارف و وعده‌ی قطعی قبولی پرهیز کن. "
    "هیچ‌گاه نگو که جایگزین مشاور رسمی یا بررسی حقوقی هستی."
)


def ai_enabled() -> bool:
    return bool(os.environ.get("GROQ_API_KEY")) and os.environ.get("AI_ENABLED", "1") != "0"


async def ask(question: str, context: dict) -> str | None:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        return None
    model = os.environ.get("AI_MODEL", "llama-3.3-70b-versatile")
    payload = {
        "model": model,
        "temperature": 0.2,
        "max_tokens": 700,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "داده‌های ارزیابی (JSON):\n"
                + json.dumps(context, ensure_ascii=False)[:12000]
                + "\n\nپرسش کاربر:\n"
                + question[:2000],
            },
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json=payload,
            )
        if response.status_code >= 400:
            return None
        body = response.json()
        return body["choices"][0]["message"]["content"].strip()
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        return None


def fallback_answer(question: str, context: dict) -> str:
    """پاسخ قطعی وقتی مدل زبانی در دسترس نیست."""
    top = (context.get("top_programs") or [{}])[0]
    name = top.get("program_name", "مسیر پیشنهادی")
    country = top.get("country_name", "")
    gaps = top.get("gaps") or []
    lines = [
        f"در حالت آفلاین، پاسخ بر اساس همان موتور ارزیابی ساخته می‌شود: بهترین گزینه‌ی فعلی «{name}» در {country} است.",
    ]
    if gaps:
        lines.append("مهم‌ترین شکاف‌ها:")
        for item in gaps[:3]:
            lines.append(f"• {item.get('label')}: {item.get('fix')}")
    else:
        lines.append("مانع قانونی مهمی در این مسیر دیده نمی‌شود؛ گام بعدی تکمیل مدارک و ثبت درخواست است.")
    if "هزینه" in question or "cost" in question.lower():
        lines.append(f"برآورد هزینه‌ی این مسیر حدود {top.get('total_cost_eur', '—')} یورو است.")
    lines.append("برای پاسخ تحلیلی کامل، کلید GROQ_API_KEY را در فایل .env تنظیم کنید.")
    return "\n".join(lines)
