"""Write-only, HTTPS/admin-only runtime Gemini configuration.

No key is persisted to disk, returned, logged or embedded in the client. Use the
hosting platform's private environment secrets for durable production settings.
Request validation is inside the route so FastAPI cannot echo a key in a 422.
"""
import json
import os

from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from . import gemini
from .database import connect
from .security import rate_limit


class GeminiConfiguration(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    model: str = Field(min_length=3, max_length=100)
    replacement_key: SecretStr | None = None
    requests_enabled: bool = Field(default=False, strict=True)
    usage_approved: bool = Field(default=False, strict=True)

    @field_validator('model')
    @classmethod
    def supported_identifier(cls, value):
        name = gemini.model_name(value)
        if not name:
            raise ValueError('Invalid Gemini model identifier')
        return name

    @field_validator('replacement_key')
    @classmethod
    def bounded_secret(cls, value):
        if value is not None:
            raw = value.get_secret_value()
            if not 16 <= len(raw) <= 2048 or any(c.isspace() or ord(c) < 32 for c in raw):
                raise ValueError('Invalid secret input')
        return value


def configuration_status():
    provider = os.getenv('VISION_PROVIDER', '').lower()
    model = gemini.model_name(os.getenv('VISION_MODEL', '')) if provider == 'gemini' else None
    return {
        'provider': provider if provider in {'gemini', 'groq', 'openai', 'ollama'} else 'none',
        'model': model or '',
        'key_present': bool(os.getenv('GEMINI_API_KEY', '')),
        'requests_enabled': os.getenv('GEMINI_REQUESTS_ENABLED', 'false').lower() == 'true',
        'storage': 'server-memory-only',
        'notice': 'فرم فقط برای مدیر روی HTTPS است. کلید برگشت داده/ثبت فایل نمی‌شود. برای ماندگاری، Secret میزبان لازم است. ذخیره تنظیمات، آزمایش اتصال یا تأیید علمی نیست.',
    }


def register_vision_configuration(app, require_admin, audit):
    @app.get('/api/admin/vision/configuration')
    def read_configuration(request: Request):
        with connect() as db:
            require_admin(request, db)
        return configuration_status()

    @app.put('/api/admin/vision/configuration')
    async def write_configuration(request: Request):
        with connect() as db:
            admin = require_admin(request, db)
            admin_id = admin['id']
        if request.url.scheme != 'https':
            raise HTTPException(400, 'کلید فقط از اتصال HTTPS و حساب مدیر پذیرفته می‌شود.')
        rate_limit(f'vision-config:{admin_id}', 5, 600)
        try:
            raw = await request.body()
            if len(raw) > 8192:
                raise HTTPException(413, 'درخواست تنظیمات بیش از حد مجاز است.')
            data = GeminiConfiguration.model_validate(json.loads(raw))
        except (ValueError, TypeError):
            # Never expose validation errors: they can contain secret input.
            raise HTTPException(422, 'تنظیمات مدل یا ساختار کلید معتبر نیست. جزئیات محرمانه نمایش داده نمی‌شود.') from None
        if data.requests_enabled and not data.usage_approved:
            raise HTTPException(422, 'فعال‌سازی نیازمند تأیید صریح سهمیه/سیاست هزینه حساب Google است.')
        key = data.replacement_key.get_secret_value() if data.replacement_key else os.getenv('GEMINI_API_KEY', '')
        if data.requests_enabled and not key:
            raise HTTPException(422, 'کلید امن سرور موجود نیست؛ مدل فعال نشده است.')
        # No await between updates; a single-process pilot owns this environment.
        os.environ['VISION_PROVIDER'] = 'gemini'
        os.environ['VISION_MODEL'] = data.model
        if data.replacement_key is not None:
            os.environ['GEMINI_API_KEY'] = key
        os.environ['GEMINI_REQUESTS_ENABLED'] = 'true' if data.requests_enabled else 'false'
        with connect() as db:
            audit(db, admin_id, 'vision_runtime_configuration_updated', 'gemini')
        return configuration_status()

    @app.delete('/api/admin/vision/configuration')
    def clear_configuration(request: Request):
        with connect() as db:
            admin = require_admin(request, db)
            if request.url.scheme != 'https':
                raise HTTPException(400, 'تنظیمات محرمانه فقط روی HTTPS تغییر می‌کنند.')
            os.environ.pop('GEMINI_API_KEY', None)
            os.environ['GEMINI_REQUESTS_ENABLED'] = 'false'
            audit(db, admin['id'], 'vision_runtime_key_cleared', 'gemini')
        return configuration_status()
