import base64
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_groq_key = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=_groq_key) if _groq_key else None

_reports = {}


class ChatRequest(BaseModel):
    message: str


def _now():
    return datetime.now(timezone.utc).isoformat()


def _scientific_disclaimer():
    return (
        "در این بررسی از جدیدترین اطلاعات علمی حوزه گیاه‌پزشکی و باغ پسته استفاده شده است. "
        "نتیجه احتمالی است و جایگزین تشخیص کارشناس محلی نیست."
    )


async def _vision_analyze(image_bytes, category, season):
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise HTTPException(
            status_code=503,
            detail={"error": {"code": "NETWORK", "message": "تحلیل تصویر روی سرور تنظیم نشده است."}},
        )

    b64 = base64.b64encode(image_bytes).decode("ascii")
    prompt = (
        "تو متخصص گیاه‌پزشکی باغ پسته هستی. عکس را بررسی کن. "
        "دسته تصویر: " + category + ". فصل: " + season + ". "
        "فقط JSON معتبر برگردان با کلیدهای diagnosis, confidence, symptoms, "
        "alternatives, actions, needMore, references. "
        "در متن به نام مدل یا شرکت اشاره نکن."
    )
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
                ]
            }
        ]
    }
    async with httpx.AsyncClient(timeout=60.0) as http:
        r = await http.post(url, params={"key": key}, json=payload)
    if r.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail={"error": {"code": "UNKNOWN", "message": "تحلیل تصویر الان انجام نشد."}},
        )
    body = r.json()
    try:
        text = body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        text = "{}"
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = {
            "diagnosis": "نتیجه قطعی از روی این تصویر به دست نیامد",
            "confidence": 40,
            "symptoms": [],
            "alternatives": [],
            "actions": ["عکس واضح تر در نور طبیعی بگیرید"],
            "needMore": [],
            "references": [],
        }
    return data


@app.get("/")
async def root():
    return {"message": "Zehnyar API is Running!"}


@app.post("/chat")
async def chat_with_pishai(request: ChatRequest):
    if client is None:
        return {"error": "GROQ_API_KEY روی سرور تنظیم نشده است."}
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "تو ذهن‌یار هستی. متخصص منطق و استدلال به زبان فارسی.",
                },
                {"role": "user", "content": request.message},
            ],
        )
        return {"response": completion.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}


@app.post("/analyses")
async def create_analysis(
    farmId: str = Form(...),
    category: str = Form("leaf"),
    season: str = Form(""),
    image: UploadFile = File(...),
):
    raw = await image.read()
    if not raw:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "IMAGE_UNSUITABLE", "message": "تصویر خالی است."}},
        )
    parsed = await _vision_analyze(raw, category, season)
    report_id = str(uuid.uuid4())
    report = {
        "id": report_id,
        "farmId": farmId,
        "category": category,
        "season": season,
        "createdAt": _now(),
        "diagnosis": parsed.get("diagnosis") or "نامشخص",
        "confidence": int(parsed.get("confidence") or 50),
        "symptoms": parsed.get("symptoms") or [],
        "alternatives": parsed.get("alternatives") or [],
        "actions": parsed.get("actions") or [],
        "needMore": parsed.get("needMore") or [],
        "references": parsed.get("references") or [],
        "disclaimer": _scientific_disclaimer(),
    }
    _reports[report_id] = report
    return report


@app.get("/analyses")
async def list_analyses(farmId: Optional[str] = None):
    items = list(_reports.values())
    if farmId:
        items = [r for r in items if r.get("farmId") == farmId]
    summaries = [
        {
            "id": r["id"],
            "diagnosis": r["diagnosis"],
            "confidence": r["confidence"],
            "category": r["category"],
            "createdAt": r["createdAt"],
            "farmId": r.get("farmId"),
        }
        for r in reversed(items)
    ]
    return {"items": summaries}


@app.get("/analyses/{report_id}")
async def get_analysis(report_id: str):
    r = _reports.get(report_id)
    if not r:
        raise HTTPException(status_code=404, detail="گزارش پیدا نشد")
    return r
