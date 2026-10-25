"""مهاجریار — برنامه‌ی FastAPI سامانه‌ی هوشمند مهاجرت."""
from __future__ import annotations

import time
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app import ai
from app.config import settings
from app.db import Database
from app.engine.advisor import (
    build_roadmap,
    documents_checklist,
    narrative,
    overall_readiness,
    quick_wins,
    rank_results,
)
from app.engine.base import all_program_meta, rules_verified_on
from app.engine.registry import assess_all
from app.engine.types import ProgramResult
from app.formatting import fa_date, fa_digits, fa_money, fa_number, fa_percent
from app.forms import parse_profile
from app.schemas import Profile

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
templates.env.filters.update(
    fa=fa_number,
    fa_digits=fa_digits,
    fa_money=fa_money,
    fa_date=fa_date,
    fa_percent=fa_percent,
)
def _fv(data: Any, path: str, default: Any = "") -> Any:
    """دسترسی امن به مقدار فرم در حالت dict یا مدل (برای بازنمایش)."""
    current: Any = data
    for part in path.split("."):
        if current is None:
            return default
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
    return default if current is None else current


templates.env.globals.update(
    fv=_fv,
    brand=settings.app_name,
    brand_en=settings.brand_en,
    tagline=settings.tagline,
    version=settings.version,
    rules_verified=rules_verified_on,
    today=date.today,
)

app = FastAPI(
    title="مهاجریار | Mohajeryar API",
    description="API ارزیابی مسیرهای مهاجرت بر پایه‌ی قواعد رسمی ۲۰۲۶",
    version=settings.version,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
database = Database(settings.database_path)

_chat_hits: dict[str, list[float]] = defaultdict(list)
CHAT_LIMIT = 12
CHAT_WINDOW = 3600


# --------------------------------------------------------------------- middlewares
@app.middleware("http")
async def security_and_limits(request: Request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > settings.max_body_bytes:
            return JSONResponse({"detail": "حجم درخواست بیش از حد مجاز است."}, status_code=413)
        origin = request.headers.get("origin")
        if origin and settings.enforce_origin:
            if urlparse(origin).netloc != request.headers.get("host", ""):
                return JSONResponse({"detail": "منبع درخواست معتبر نیست."}, status_code=403)
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; font-src 'self'; connect-src 'self'; "
        "base-uri 'self'; form-action 'self'; frame-ancestors *",
    )
    if settings.production and request.url.scheme == "https":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


# --------------------------------------------------------------------- helpers
def _page(request: Request, name: str, context: dict[str, Any] | None = None, status_code: int = 200):
    data: dict[str, Any] = {"active": name, "settings": settings}
    if context:
        data.update(context)
    template_name = name if name.endswith(".html") else name + ".html"
    return templates.TemplateResponse(request, template_name, data, status_code=status_code)


def _results_from_assessment(assessment: dict) -> list[ProgramResult]:
    return [ProgramResult.model_validate(item) for item in assessment["results"]]


def _result_context(assessment: dict, profile: Profile) -> dict[str, Any]:
    results = _results_from_assessment(assessment)
    readiness = assessment.get("readiness") or overall_readiness(results, profile)
    top = results[0]
    context = {
        "assessment": assessment,
        "profile": profile,
        "results": results,
        "top": top,
        "readiness": readiness,
        "narrative": narrative(results, profile),
        "wins": quick_wins(results, profile, 4),
        "roadmap": build_roadmap(top, profile),
        "checklist": documents_checklist(profile, results),
        "eligible_count": sum(1 for r in results if r.status == "eligible"),
        "potential_count": sum(1 for r in results if r.status == "potential"),
        "needs_offer_count": sum(1 for r in results if r.status == "needs_job_offer"),
        "ineligible_count": sum(1 for r in results if r.status == "ineligible"),
        "rule_date": assessment.get("rule_date", date.today().isoformat()),
        "profiles_count": database.stats()["profiles"],
    }
    return context


def _assessment_payload(assessment: dict, profile: Profile) -> dict[str, Any]:
    results = _results_from_assessment(assessment)
    return {
        "id": assessment["id"],
        "profile_id": assessment["profile_id"],
        "created_at": assessment["created_at"],
        "rule_date": assessment["rule_date"],
        "readiness": assessment["readiness"],
        "profile": profile.model_dump(mode="json"),
        "narrative": narrative(results, profile),
        "quick_wins": quick_wins(results, profile, 5),
        "results": [r.model_dump(mode="json") for r in results],
        "disclaimer": _disclaimer(),
    }


def _disclaimer() -> str:
    return (
        "این ارزیابی خودکار و صرفاً راهنمای اولیه است؛ جایگزین مشاوره‌ی حقوقی یا بررسی سفارت نیست. "
        "قوانین مهاجرت تغییر می‌کند؛ پیش از هر اقدام، Conditions را در وب‌سایت رسمی کشور مقصد بررسی کنید."
    )


# --------------------------------------------------------------------- pages
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    programs = all_program_meta()
    countries = {}
    for item in programs:
        countries.setdefault(item["country_code"], item)
    return _page(
        request,
        "index",
        {
            "programs": programs,
            "countries": countries,
            "verified": rules_verified_on(),
            "disclaimer": _disclaimer(),
        },
    )


@app.get("/wizard", response_class=HTMLResponse)
async def wizard(request: Request, profile_id: str | None = None):
    form_data: dict[str, Any] = {}
    if profile_id:
        record = database.get_profile(profile_id)
        if record:
            form_data = record["profile"].model_dump(mode="json")
    return _page(
        request,
        "wizard",
        {
            "form": form_data,
            "profile_id": profile_id or "",
            "programs": all_program_meta(),
            "errors": {},
        },
    )


@app.post("/assess")
async def submit_assessment(request: Request):
    form = await request.form()
    profile, errors, raw = parse_profile(form)
    profile_id = str(form.get("profile_id") or "") or None
    if not profile or errors:
        return _page(
            request,
            "wizard",
            {
                "form": raw,
                "profile_id": profile_id or "",
                "programs": all_program_meta(),
                "errors": errors or {"form": "فرم را کامل کنید."},
            },
            status_code=422,
        )
    pid = database.save_profile(profile, profile_id)
    results = rank_results(assess_all(profile), profile)
    readiness = overall_readiness(results, profile)
    aid = database.save_assessment(
        pid,
        [item.model_dump(mode="json") for item in results],
        readiness,
        date.today().isoformat(),
    )
    return RedirectResponse(f"/results/{aid}", status_code=303)


@app.get("/results/{assessment_id}", response_class=HTMLResponse)
async def results_page(request: Request, assessment_id: str):
    assessment = database.get_assessment(assessment_id)
    if not assessment:
        return _page(request, "not_found", {"message": "این ارزیابی پیدا نشد."}, status_code=404)
    record = database.get_profile(assessment["profile_id"])
    if not record:
        return _page(request, "not_found", {"message": "پروفایل مربوط به این ارزیابی حذف شده است."}, status_code=404)
    context = _result_context(assessment, record["profile"])
    return _page(request, "results", context)


@app.get("/profiles", response_class=HTMLResponse)
async def profiles_page(request: Request):
    return _page(
        request,
        "profiles",
        {"profiles": database.list_profiles(), "stats": database.stats()},
    )


@app.get("/profiles/{profile_id}/latest")
async def profile_latest(profile_id: str):
    latest = database.latest_assessment(profile_id)
    if not latest:
        raise HTTPException(status_code=404, detail="ارزیابی‌ای برای این پروفایل ثبت نشده است")
    return RedirectResponse(f"/results/{latest['id']}", status_code=303)


@app.get("/profiles/{profile_id}/edit", response_class=HTMLResponse)
async def profile_edit(request: Request, profile_id: str):
    record = database.get_profile(profile_id)
    if not record:
        return _page(request, "not_found", {"message": "پروفایل پیدا نشد."}, status_code=404)
    return _page(
        request,
        "wizard",
        {
            "form": record["profile"].model_dump(mode="json"),
            "profile_id": profile_id,
            "programs": all_program_meta(),
            "errors": {},
        },
    )


@app.post("/profiles/{profile_id}/reassess")
async def profile_reassess(profile_id: str):
    record = database.get_profile(profile_id)
    if not record:
        raise HTTPException(status_code=404, detail="پروفایل پیدا نشد")
    profile = record["profile"]
    results = rank_results(assess_all(profile), profile)
    readiness = overall_readiness(results, profile)
    aid = database.save_assessment(
        profile_id,
        [item.model_dump(mode="json") for item in results],
        readiness,
        date.today().isoformat(),
    )
    return RedirectResponse(f"/results/{aid}", status_code=303)


@app.post("/profiles/{profile_id}/delete")
async def profile_delete(profile_id: str):
    database.delete_profile(profile_id)
    return RedirectResponse("/profiles", status_code=303)


@app.get("/compare/{assessment_id}", response_class=HTMLResponse)
async def compare_page(request: Request, assessment_id: str):
    assessment = database.get_assessment(assessment_id)
    if not assessment:
        return _page(request, "not_found", {"message": "ارزیابی پیدا نشد."}, status_code=404)
    record = database.get_profile(assessment["profile_id"])
    if not record:
        return _page(request, "not_found", {"message": "پروفایل پیدا نشد."}, status_code=404)
    results = _results_from_assessment(assessment)
    selected_ids = request.query_params.getlist("p")
    if selected_ids:
        selected = [r for r in results if r.program_id in selected_ids]
    else:
        selected = [r for r in results if r.status != "ineligible"][:4] or results[:4]
    return _page(
        request,
        "compare",
        {
            "assessment": assessment,
            "profile": record["profile"],
            "results": results,
            "selected": selected,
        },
    )


@app.get("/methodology", response_class=HTMLResponse)
async def methodology(request: Request):
    return _page(
        request,
        "methodology",
        {
            "programs": all_program_meta(),
            "verified": rules_verified_on(),
            "disclaimer": _disclaimer(),
        },
    )


@app.get("/offline", response_class=HTMLResponse)
async def offline(request: Request):
    return _page(request, "offline")


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(BASE / "static" / "icons" / "icon-192.png")


@app.get("/manifest.webmanifest")
async def manifest():
    return FileResponse(
        BASE / "static" / "manifest.webmanifest",
        media_type="application/manifest+json",
    )


@app.get("/sw.js")
async def service_worker():
    return FileResponse(
        BASE / "static" / "sw.js",
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
    )


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return "User-agent: *\nAllow: /\nDisallow: /api/\n"


# --------------------------------------------------------------------- API
@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": settings.version,
        "rules_verified_on": rules_verified_on().isoformat(),
        "database": database.stats(),
    }


@app.get("/api/programs")
async def api_programs():
    return {"verified_on": rules_verified_on().isoformat(), "items": all_program_meta()}


@app.post("/api/assess")
async def api_assess(profile: Profile):
    results = rank_results(assess_all(profile), profile)
    readiness = overall_readiness(results, profile)
    return {
        "readiness": readiness,
        "narrative": narrative(results, profile),
        "quick_wins": quick_wins(results, profile, 5),
        "results": [r.model_dump(mode="json") for r in results],
        "disclaimer": _disclaimer(),
    }


@app.get("/api/profiles")
async def api_profiles():
    return {"items": database.list_profiles()}


@app.get("/api/profiles/{profile_id}")
async def api_profile(profile_id: str):
    record = database.get_profile(profile_id)
    if not record:
        raise HTTPException(status_code=404, detail="پروفایل پیدا نشد")
    return {
        "id": record["id"],
        "name": record["name"],
        "profile": record["profile"].model_dump(mode="json"),
        "created_at": record["created_at"],
        "updated_at": record["updated_at"],
        "assessments": database.list_assessments(profile_id),
    }


@app.get("/api/assessments/{assessment_id}")
async def api_assessment(assessment_id: str):
    assessment = database.get_assessment(assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="ارزیابی پیدا نشد")
    record = database.get_profile(assessment["profile_id"])
    if not record:
        raise HTTPException(status_code=404, detail="پروفایل پیدا نشد")
    return _assessment_payload(assessment, record["profile"])


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=1500)
    assessment_id: str | None = None


@app.post("/api/chat")
async def chat(payload: ChatRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    hits = [t for t in _chat_hits[client_ip] if now - t < CHAT_WINDOW]
    if len(hits) >= CHAT_LIMIT:
        raise HTTPException(status_code=429, detail="تعداد پرسش‌ها زیاد است؛ کمی بعد دوباره تلاش کنید.")
    _chat_hits[client_ip] = hits + [now]

    context: dict[str, Any] = {}
    if payload.assessment_id:
        assessment = database.get_assessment(payload.assessment_id)
        if assessment:
            results = _results_from_assessment(assessment)
            context = {
                "readiness": assessment["readiness"],
                "top_programs": [
                    {
                        "program_name": r.program_name,
                        "country_name": r.country_name,
                        "status": r.status,
                        "score": r.score,
                        "threshold": r.score_threshold,
                        "readiness": r.readiness,
                        "total_cost_eur": r.total_cost_eur,
                        "timeline_months": r.timeline_months,
                        "gaps": [g.model_dump() for g in r.gaps[:4]],
                    }
                    for r in results[:5]
                ],
            }
    answer = None
    if settings.ai_enabled and ai.ai_enabled():
        answer = await ai.ask(payload.question, context)
    if not answer:
        answer = ai.fallback_answer(payload.question, context or {"top_programs": []})
    return {"answer": answer, "ai": bool(answer and settings.ai_enabled and ai.ai_enabled())}


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail or "پیدا نشد"}, status_code=404)
    return _page(request, "not_found", {"message": exc.detail or "صفحه پیدا نشد."}, status_code=404)
