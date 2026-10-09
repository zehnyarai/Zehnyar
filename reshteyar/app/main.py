"""رشته‌یار: راهنمای انتخاب رشته‌ی کنکور (FastAPI + Jinja2 + SQLite)."""
from __future__ import annotations

import base64
import re
import secrets
from urllib.parse import urlencode
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markupsafe import Markup
from pydantic import BaseModel, Field, field_validator
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import payments as pay
from .analysis import run_analysis
from .catalog import DEGREE_CHOICES, Catalog, parse_cutoffs
from .config import STATIC_DIR, payment_mode, settings, validate_settings
from .db import db, init_db
from .security import SecurityMiddleware, client_ip, limiter
from .licensing import COOKIE_NAME, find_active_license, from_iso, utcnow
from .payments import admin_stats
from .scoring import QUOTAS, Profile, parse_interests, quota_key
from .textutil import fa_digits, fa_number, jalali_date, jalali_datetime, toman

APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = APP_DIR / "templates"
MAX_CUTOFF_UPLOAD = 2_000_000
_ICON_CACHE: dict[str, str] = {}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("rz")

catalog = Catalog()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def icon(name: str, cls: str = "") -> Markup:
    """آیکن SVG (lucide) را inline می‌کند تا با CSS رنگی شود."""
    if name not in _ICON_CACHE:
        path = STATIC_DIR / "icons" / f"{name}.svg"
        svg = path.read_text(encoding="utf-8") if path.exists() else ""
        svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S).strip()
        _ICON_CACHE[name] = svg
    svg = _ICON_CACHE[name]
    if not svg:
        return Markup("")
    svg = re.sub(r'\s+class="[^"]*"', "", svg, count=1)
    return Markup(svg.replace("<svg", f'<svg class="icon {cls}" aria-hidden="true" focusable="false"', 1))


def _iso_jdate(value: str | None) -> str:
    return jalali_date(from_iso(value)) if value else "—"


def _iso_jdt(value: str | None) -> str:
    return jalali_datetime(from_iso(value)) if value else "—"


templates.env.filters.update({
    "fa": fa_digits, "num": fa_number, "toman": toman,
    "jiso": _iso_jdate, "jisodt": _iso_jdt,
})
templates.env.globals.update({"icon": icon})


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_settings()
    init_db()
    yield


app = FastAPI(title="رشته‌یار", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
app.add_middleware(SecurityMiddleware)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# جدول‌ها همیشه قبل از اولین درخواست وجود دارند (حتی بدون اجرای lifespan، مثلاً در تست‌ها)
init_db()


def _rate_limit(request: Request, bucket: str, limit: int, window: int) -> None:
    ip = client_ip(request.scope)
    if not limiter.hit(f"{bucket}:{ip}", limit, window):
        log.warning("rate limit bucket=%s ip=%s", bucket, ip)
        raise HTTPException(status_code=429, detail="تعداد درخواست‌ها زیاد است؛ کمی بعد دوباره تلاش کنید.")


# ---------------------------------------------------------------- کمکی‌ها
def current_license(request: Request) -> dict | None:
    code = request.cookies.get(COOKIE_NAME)
    if not code:
        return None
    with db() as conn:
        row = find_active_license(conn, code)
    if row is None:
        return None
    lic = dict(row)
    plan = pay.find_plan(catalog.plans, lic["plan_id"])
    lic["plan_title"] = plan["title"] if plan else lic["plan_id"]
    return lic


def base_ctx(request: Request, *, active: str = "", premium: bool | None = None, **extra) -> dict:
    if premium is None:
        premium = current_license(request) is not None
    return {
        "active": active,
        "premium": premium,
        "mode": payment_mode(),
        "nav_groups": catalog.groups,
        "meta": catalog.meta,
        "free_limit": settings.free_results_limit,
        **extra,
    }


def render(request: Request, name: str, ctx: dict, status: int = 200) -> HTMLResponse:
    return templates.TemplateResponse(request, name, ctx, status_code=status)


def _license_cookie(response: Response, code: str) -> Response:
    with db() as conn:
        row = find_active_license(conn, code)
    if row is None:
        return response
    max_age = max(60, int((from_iso(row["expires_at"]) - utcnow()).total_seconds()))
    response.set_cookie(COOKIE_NAME, code, max_age=max_age, httponly=True, samesite="lax",
                        secure=settings.cookie_secure, path="/")
    return response


def require_admin(request: Request) -> None:
    if not settings.admin_password:
        raise HTTPException(status_code=503, detail="ADMIN_PASSWORD تنظیم نشده است؛ پنل مدیریت غیرفعال است.")
    _rate_limit(request, "admin", limit=30, window=900)
    header = request.headers.get("authorization", "")
    if header.lower().startswith("basic "):
        try:
            user, _, password = base64.b64decode(header[6:]).decode("utf-8").partition(":")
        except (ValueError, UnicodeDecodeError):
            user, password = "", ""
        ok_user = secrets.compare_digest(user.encode(), settings.admin_user.encode())
        ok_pass = secrets.compare_digest(password.encode(), settings.admin_password.encode())
        if ok_user and ok_pass:
            return
    log.warning("failed admin login ip=%s", client_ip(request.scope))
    raise HTTPException(status_code=401, detail="نیاز به ورود مدیر", headers={"WWW-Authenticate": 'Basic realm="admin"'})


def to_latin_digits(value: str) -> str:
    return (value or "").translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")).strip()


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/api/") or exc.status_code == 401:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)
    ctx = base_ctx(request, premium=False, code=exc.status_code, message=exc.detail)
    return render(request, "error.html", ctx, status=exc.status_code)


# ---------------------------------------------------------------- صفحات عمومی
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    cards = []
    for g in catalog.groups:
        cards.append({**g, "stats": catalog.group_stats(g["data_key"])})
    ctx = base_ctx(request, active="home", cards=cards,
                   totals={"fields": len(catalog.fields), "universities": len(catalog.universities),
                           "groups": len(catalog.groups)})
    return render(request, "home.html", ctx)


@app.get("/groups/{slug}", response_class=HTMLResponse)
def group_page(request: Request, slug: str):
    group = catalog.group_by_slug.get(slug)
    if group is None:
        raise HTTPException(status_code=404, detail="گروه پیدا نشد.")
    ctx = base_ctx(request, active="groups", group=group, stats=catalog.group_stats(group["data_key"]),
                   quotas=QUOTAS, provinces=catalog.provinces, uni_types=catalog.uni_types,
                   degrees=DEGREE_CHOICES, factors=catalog.factors, has_cutoffs=bool(catalog.cutoffs))
    return render(request, "group.html", ctx)


@app.get("/fields", response_class=HTMLResponse)
def fields_page(request: Request, group: str | None = None):
    ctx = base_ctx(request, active="fields", groups=catalog.groups, degrees=DEGREE_CHOICES,
                   preset_group=group or "", total=len(catalog.fields))
    return render(request, "fields.html", ctx)


@app.get("/universities", response_class=HTMLResponse)
def universities_page(request: Request, group: str | None = None):
    ctx = base_ctx(request, active="universities", groups=catalog.groups, uni_types=catalog.uni_types,
                   provinces=catalog.provinces, preset_group=group or "",
                   total=len(catalog.universities))
    return render(request, "universities.html", ctx)


@app.get("/factors", response_class=HTMLResponse)
def factors_page(request: Request):
    ctx = base_ctx(request, active="factors", factors=catalog.factors)
    return render(request, "factors.html", ctx)


@app.get("/about", response_class=HTMLResponse)
def about_page(request: Request):
    return render(request, "about.html", base_ctx(request, active="about"))


@app.get("/premium", response_class=HTMLResponse)
def premium_page(request: Request, error: str = ""):
    lic = current_license(request)
    ctx = base_ctx(request, active="premium", plans=catalog.plans, error=error, license=lic,
                   allow_checkout=payment_mode() != "unavailable")
    return render(request, "premium.html", ctx)


# ---------------------------------------------------------------- پرداخت
@app.post("/premium/checkout")
def premium_checkout(request: Request, plan: str = Form(..., max_length=40),
                     mobile: str = Form("", max_length=20), email: str = Form("", max_length=120)):
    _rate_limit(request, "checkout", limit=20, window=600)
    mobile_v = to_latin_digits(mobile)
    email_v = email.strip()
    p = pay.find_plan(catalog.plans, plan)

    def fail(message: str, status: int = 400):
        ctx = base_ctx(request, active="premium", plans=catalog.plans, error=message,
                       license=current_license(request), allow_checkout=payment_mode() != "unavailable")
        return render(request, "premium.html", ctx, status=status)

    if p is None:
        return fail("طرح انتخاب‌شده معتبر نیست.")
    if mobile_v and not pay.MOBILE_RE.match(mobile_v):
        return fail("شماره موبایل معتبر نیست (مثلاً ۰۹۱۲۳۴۵۶۷۸۹).")
    if email_v and not pay.EMAIL_RE.match(email_v):
        return fail("ایمیل معتبر نیست.")
    try:
        gateway = pay.get_gateway()
    except pay.PaymentError as exc:
        return fail(str(exc), status=503)

    callback_url = f"{settings.public_base_url}/premium/callback"
    with db() as conn:
        try:
            redirect_url, _token = pay.create_payment(conn, gateway, p, mobile=mobile_v or None,
                                                      email=email_v or None, callback_url=callback_url)
        except pay.PaymentError as exc:
            return fail(str(exc), status=502)
    return RedirectResponse(redirect_url, status_code=303)


@app.get("/premium/callback")
def premium_callback(Authority: str = Query("", max_length=64), Status: str = Query("", max_length=10)):
    if not Authority:
        raise HTTPException(status_code=400, detail="پارامترهای بازگشت از درگاه ناقص است.")
    try:
        gateway = pay.get_gateway()
    except pay.PaymentError:
        return RedirectResponse("/premium?" + urlencode({"error": "درگاه پرداخت پیکربندی نشده است."}), status_code=303)
    with db() as conn:
        result = pay.handle_callback(conn, gateway, catalog.plans, Authority, Status)
    if result["state"] == "unknown" or not result.get("token"):
        raise HTTPException(status_code=404, detail="پرداختی با این مشخصات پیدا نشد.")
    response = RedirectResponse(f"/premium/result?t={result['token']}", status_code=303)
    if result.get("code"):
        _license_cookie(response, result["code"])
    return response


@app.get("/premium/result", response_class=HTMLResponse)
def premium_result(request: Request, t: str = ""):
    with db() as conn:
        row = pay.payment_by_token(conn, t) if t else None
        if row is None:
            raise HTTPException(status_code=404, detail="نتیجه‌ی پرداخت پیدا نشد.")
        lic = conn.execute("SELECT * FROM licenses WHERE payment_id = ?", (row["id"],)).fetchone()
    plan = pay.find_plan(catalog.plans, row["plan_id"])
    ctx = base_ctx(request, active="premium", payment=dict(row), plan=plan,
                   license=dict(lic) if lic else None)
    return render(request, "payment_result.html", ctx)


@app.get("/premium/mock/{authority}", response_class=HTMLResponse)
def mock_gateway_page(request: Request, authority: str):
    if payment_mode() != "mock" or not authority.startswith("MOCK"):
        raise HTTPException(status_code=404, detail="صفحه پیدا نشد.")
    with db() as conn:
        row = conn.execute("SELECT * FROM payments WHERE authority = ?", (authority,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="پرداخت پیدا نشد.")
    plan = pay.find_plan(catalog.plans, row["plan_id"])
    return render(request, "mock_gateway.html", base_ctx(request, payment=dict(row), plan=plan,
                                                         authority=authority))


@app.post("/premium/mock/{authority}")
def mock_gateway_submit(request: Request, authority: str, outcome: str = Form("OK", max_length=10)):
    if payment_mode() != "mock" or not authority.startswith("MOCK") or len(authority) > 64:
        raise HTTPException(status_code=404, detail="صفحه پیدا نشد.")
    _rate_limit(request, "mock", limit=60, window=600)
    with db() as conn:
        pay.mock_confirm(conn, authority, approve=(outcome == "OK"))
    status = "OK" if outcome == "OK" else "NOK"
    return RedirectResponse(f"/premium/callback?Authority={authority}&Status={status}", status_code=303)


# ---------------------------------------------------------------- حساب کاربری
@app.get("/account", response_class=HTMLResponse)
def account_page(request: Request, error: str = "", info: str = ""):
    lic = current_license(request)
    ctx = base_ctx(request, active="account", license=lic, error=error, info=info)
    return render(request, "account.html", ctx)


@app.post("/account/activate")
def account_activate(request: Request, code: str = Form(..., max_length=40)):
    _rate_limit(request, "activate", limit=10, window=600)
    with db() as conn:
        row = find_active_license(conn, code)
    if row is None:
        ctx = base_ctx(request, active="account", license=None,
                       error="کد وارد شده معتبر نیست یا مهلت آن تمام شده است.")
        return render(request, "account.html", ctx, status=400)
    response = RedirectResponse("/account?info=activated", status_code=303)
    return _license_cookie(response, row["code"])


@app.post("/account/logout")
def account_logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(COOKIE_NAME, path="/")
    return response


# ---------------------------------------------------------------- پنل مدیریت
@app.get("/admin", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
def admin_dashboard(request: Request, msg: str = "", msg_type: str = "ok"):
    with db() as conn:
        stats = admin_stats(conn)
    ctx = base_ctx(request, active="admin", premium=False, stats=stats,
                   cutoffs_count=len(catalog.cutoffs), cutoff_errors=catalog.cutoff_errors[:30],
                   cutoffs_path=str(settings.cutoffs_path), msg=msg, msg_type=msg_type,
                   plans=catalog.plans)
    return render(request, "admin.html", ctx)


@app.post("/admin/cutoffs", dependencies=[Depends(require_admin)])
async def admin_upload_cutoffs(file: UploadFile = File(...)):
    raw = await file.read(MAX_CUTOFF_UPLOAD + 1)
    if len(raw) > MAX_CUTOFF_UPLOAD:
        return RedirectResponse("/admin?" + urlencode({"msg": "فایل از ۲ مگابایت بزرگ‌تر است.", "msg_type": "error"}), status_code=303)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return RedirectResponse("/admin?" + urlencode({"msg": "فایل باید UTF-8 باشد.", "msg_type": "error"}), status_code=303)
    rows, errors = parse_cutoffs(text, catalog)
    if not rows:
        reason = errors[0] if errors else "هیچ ردیف معتبری پیدا نشد"
        return RedirectResponse("/admin?" + urlencode({"msg": reason, "msg_type": "error"}), status_code=303)
    settings.cutoffs_path.parent.mkdir(parents=True, exist_ok=True)
    settings.cutoffs_path.write_text(text, encoding="utf-8")
    catalog.reload_cutoffs()
    message = f"{len(rows)} ردیف ثبت شد؛ {len(errors)} ردیف خطا داشت."
    return RedirectResponse("/admin?" + urlencode({"msg": message, "msg_type": "ok"}), status_code=303)


# ---------------------------------------------------------------- API
class AnalyzeIn(BaseModel):
    model_config = {"extra": "forbid"}
    gpa: float | None = Field(default=None, ge=0, le=20)
    pct: dict[str, float | None] = Field(default_factory=dict, max_length=20)
    coef: dict[str, float | None] = Field(default_factory=dict, max_length=20)
    rank_no_quota: int | None = Field(default=None, ge=1, le=10_000_000)
    rank_quota: int | None = Field(default=None, ge=1, le=10_000_000)
    quota: str = Field(default="none", max_length=60)
    province: str | None = Field(default=None, max_length=40)
    univ_types: list[str] = Field(default_factory=list, max_length=12)
    interests: str = Field(default="", max_length=300)
    degree: str | None = Field(default=None, max_length=20)

    @field_validator("pct")
    @classmethod
    def _pct_range(cls, value: dict) -> dict:
        for v in value.values():
            if v is not None and not 0 <= v <= 100:
                raise ValueError("درصد باید بین ۰ و ۱۰۰ باشد")
        return value

    @field_validator("pct", "coef")
    @classmethod
    def _keys_known(cls, value: dict) -> dict:
        for k in value:
            if not isinstance(k, str) or len(k) > 40:
                raise ValueError("نام درس نامعتبر است")
        return value

    @field_validator("coef")
    @classmethod
    def _coef_range(cls, value: dict) -> dict:
        for v in value.values():
            if v is not None and not 0 <= v <= 20:
                raise ValueError("ضریب باید بین ۰ و ۲۰ باشد")
        return value


@app.post("/api/groups/{slug}/analyze")
def api_analyze(request: Request, slug: str, body: AnalyzeIn):
    profile = Profile(
        gpa=body.gpa,
        pct={k: v for k, v in body.pct.items() if v is not None},
        coef={k: v for k, v in body.coef.items() if v is not None},
        rank_no_quota=body.rank_no_quota,
        rank_quota=body.rank_quota,
        quota=quota_key(body.quota),
        province=body.province if body.province in catalog.provinces else None,
        univ_types=[t for t in body.univ_types if t in catalog.uni_types],
        interests=parse_interests(body.interests),
        degree=body.degree if body.degree in DEGREE_CHOICES else None,
    )
    result = run_analysis(catalog, slug, profile, premium=current_license(request) is not None,
                          free_limit=settings.free_results_limit)
    if result is None:
        raise HTTPException(status_code=404, detail="گروه پیدا نشد")
    return result


@app.get("/api/fields")
def api_fields(q: str = Query("", max_length=100), group: str | None = Query(None, max_length=60),
               degree: str | None = Query(None, max_length=20),
               offset: int = Query(0, ge=0), limit: int = Query(40, ge=1, le=100)):
    key = None
    if group:
        key = catalog.group_key_from_any(group)
        if key is None:
            raise HTTPException(status_code=404, detail="گروه پیدا نشد")
    degree_v = degree if degree in DEGREE_CHOICES else None
    return catalog.search_fields(q, key, degree_v, offset, limit)


@app.get("/api/universities")
def api_universities(q: str = Query("", max_length=100),
                     utype: str | None = Query(None, alias="type", max_length=60),
                     province: str | None = Query(None, max_length=40),
                     group: str | None = Query(None, max_length=60),
                     mode: str = Query("all", pattern="^(all|related|specialized)$"),
                     offset: int = Query(0, ge=0), limit: int = Query(40, ge=1, le=100)):
    key = None
    if group:
        key = catalog.group_key_from_any(group)
        if key is None:
            raise HTTPException(status_code=404, detail="گروه پیدا نشد")
    return catalog.search_universities(q, utype or None, province or None, key, mode, offset, limit)


@app.get("/api/meta")
def api_meta():
    return {
        "groups": [{"slug": g["slug"], "title": g["title"], "key": g["data_key"]} for g in catalog.groups],
        "provinces": catalog.provinces,
        "uni_types": catalog.uni_types,
        "degrees": DEGREE_CHOICES,
        "quotas": [{"key": k, "label": v} for k, v in QUOTAS],
        "payment_mode": payment_mode(),
        "plans": catalog.plans,
        "counts": {"fields": len(catalog.fields), "universities": len(catalog.universities),
                   "cutoff_rows": len(catalog.cutoffs)},
    }


@app.get("/healthz")
def healthz():
    return {"ok": True}
