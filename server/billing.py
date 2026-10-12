"""Opt-in, admin-reviewed transfer receipts. Disabled by default; never auto-paid."""
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Literal
from fastapi import File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from starlette.concurrency import run_in_threadpool
from .database import connect, now_iso, uid
from .pricing import pricing_config, receipt_quote, register_pricing_routes
from .security import rate_limit

PACKAGES = [
    {'id': 'trial', 'name': 'بسته آزمایشی', 'analyses': 10, 'price_toman': 290000, 'description': 'مناسب برای شروع و آشنایی'},
    {'id': 'season', 'name': 'بسته فصلی', 'analyses': 40, 'price_toman': 990000, 'description': 'مناسب یک فصل باغداری'},
    {'id': 'large', 'name': 'بسته باغ بزرگ', 'analyses': 120, 'price_toman': 2490000, 'description': 'مناسب باغ‌های چند هکتاری'},
]
MAX_RECEIPT = 6 * 1024 * 1024
DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')

def tracking_key(value):
    normalized = re.sub(r'[\s\-‌]+', '', value.translate(DIGITS)).casefold()
    if not re.fullmatch(r'[a-z0-9]{4,100}', normalized):
        raise HTTPException(422, 'کد پیگیری باید شامل رقم یا حروف لاتین معتبر باشد.')
    return normalized


def ledger_balance(db, user_id):
    return db.execute('SELECT COALESCE(SUM(delta),0) FROM credit_ledger WHERE user_id=?', (user_id,)).fetchone()[0]

def billing_config(db, services, private=False):
    row = db.execute('SELECT * FROM billing_settings WHERE id=1').fetchone()
    bank = {key: row[key] if row else '' for key in ['card_number', 'holder', 'bank']}
    pricing = pricing_config(db, PACKAGES)
    globally_allowed = os.getenv('MANUAL_PAYMENTS_ENABLED', '').lower() != 'false'
    enabled = bool(globally_allowed and pricing['receiving_requested'] and pricing['ready'] and services()['vision_configured'] and all(bank.values()))
    return {'enabled': enabled, **(bank if private or enabled else {key: '' for key in bank}), 'packages': pricing['packages'], 'pricing': {k:v for k,v in pricing.items() if k != 'packages'}, 'notice': 'رسید تنها پس از تطبیق واقعی مبلغ پیشنهاد قیمت و تصمیم مدیر بررسی می‌شود.' if enabled else 'دریافت وجه فعلاً غیرفعال است. هیچ واریزی انجام ندهید؛ فعال‌سازی نیازمند مقصد تأییدشده، مدل آماده و قیمت/نرخ معتبر است.'}

def serialize_receipt(row):
    data = {key: row[key] for key in ['id', 'name', 'phone', 'tracking', 'package_id', 'status', 'created_at', 'reason']}
    data['price_toman'] = row['price_toman']
    data['analyses'] = row['analyses']
    data['price_snapshot'] = json.loads(row['price_snapshot'])
    data['image_url'] = f"/api/billing/receipts/{row['id']}/image"
    if 'user_name' in row.keys():
        data['user_name'] = row['user_name']
    return data

def credit_account(db, user_id):
    receipts = [serialize_receipt(r) for r in db.execute('SELECT * FROM credit_receipts WHERE user_id=? ORDER BY created_at DESC LIMIT 500', (user_id,))]
    history = [dict(r) for r in db.execute('SELECT id,reason,delta,created_at FROM credit_ledger WHERE user_id=? ORDER BY created_at DESC LIMIT 500', (user_id,))]
    purchased = db.execute("SELECT COALESCE(SUM(delta),0) FROM credit_ledger WHERE user_id=? AND kind='purchase'", (user_id,)).fetchone()[0]
    used = -db.execute("SELECT COALESCE(SUM(delta),0) FROM credit_ledger WHERE user_id=? AND kind='analysis'", (user_id,)).fetchone()[0]
    return {'balance': ledger_balance(db, user_id), 'purchased': purchased, 'used': used, 'receipts': receipts, 'history': history}

class BankInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    card_number: str = Field(max_length=16)
    holder: str = Field(max_length=100)
    bank: str = Field(max_length=80)

    @field_validator('card_number', mode='before')
    @classmethod
    def normalized_digits(cls, value):
        return value.translate(DIGITS) if isinstance(value, str) else value

    @model_validator(mode='after')
    def bank_valid(self):
        if (self.holder and len(self.holder) < 2) or (self.bank and len(self.bank) < 2):
            raise ValueError('Invalid bank display information')
        if not self.card_number:
            return self # Private draft; billing remains disabled.
        if not re.fullmatch(r'[0-9]{16}', self.card_number):
            raise ValueError('Card must have 16 digits')
        digits = [int(c) for c in self.card_number]
        checksum = sum((digit * 2 - 9 if digit * 2 > 9 else digit * 2) if i % 2 == 0 else digit for i, digit in enumerate(digits))
        if checksum % 10 or len(set(digits)) == 1:
            raise ValueError('Invalid card checksum')
        return self

class ReviewInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    status: Literal['approved', 'rejected']
    reason: str = Field(default='', max_length=300)

    @model_validator(mode='after')
    def rejection_reason(self):
        if self.status == 'rejected' and not self.reason:
            raise ValueError('Rejection needs a reason')
        return self


def register_billing_routes(app, require_user, require_admin, services, normalize_image, audit):
    register_pricing_routes(app, require_admin, PACKAGES, audit)
    @app.get('/api/billing/config')
    def public_config():
        with connect() as db:
            return billing_config(db, services)

    @app.get('/api/billing/my')
    def my_credit(request: Request):
        with connect() as db:
            user = require_user(request, db)
            return credit_account(db, user['id'])

    @app.post('/api/billing/receipts', status_code=201)
    async def submit_receipt(request: Request, image: UploadFile = File(...), name: str = Form(...), phone: str = Form(''), tracking: str = Form(...), package_id: str = Form(...), quote_id: str = Form('')):
        with connect() as db:
            user = require_user(request, db, real=True)
            user_id = user['id']
            if not billing_config(db, services)['enabled']:
                raise HTTPException(503, 'دریافت وجه فعال نیست؛ واریزی انجام ندهید. برای واریز قبلی با مدیر تطبیق دهید و دوباره واریز نکنید.')
            package, snapshot = receipt_quote(db, package_id, quote_id, PACKAGES)
            if not package or not 2 <= len(name.strip()) <= 80 or len(phone) > 20 or not 4 <= len(tracking.strip()) <= 100:
                raise HTTPException(422, 'اطلاعات رسید یا بسته معتبر نیست.')
            if db.execute('SELECT COUNT(*) FROM credit_receipts WHERE user_id=?', (user_id,)).fetchone()[0] >= 500:
                raise HTTPException(400, 'سقف ایمنی درخواست‌ها تکمیل شده است.')
        canonical_tracking = tracking_key(tracking)
        rate_limit(f'receipt:{user_id}', 10, 3600)
        raw = await image.read(MAX_RECEIPT + 1)
        await image.close()
        if len(raw) > MAX_RECEIPT:
            raise HTTPException(413, 'تصویر رسید باید کمتر از ۶ مگابایت باشد.')
        normalized = await run_in_threadpool(normalize_image, raw)
        record_id = uid()
        directory = Path(os.getenv('UPLOAD_DIR', 'storage/uploads')) / 'receipts'
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f'{record_id}.jpg'
        try:
            path.write_bytes(normalized)
            with connect() as db:
                db.execute('INSERT INTO credit_receipts (id,user_id,name,phone,tracking,tracking_key,package_id,price_toman,analyses,image_path,created_at,quote_id,price_snapshot) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (record_id, user_id, name.strip(), phone.strip(), tracking.strip(), canonical_tracking, package_id, package['price_toman'], package['analyses'], str(path.resolve()), now_iso(), quote_id, json.dumps(snapshot, ensure_ascii=False)))
                audit(db, user_id, 'receipt_submitted', record_id)
                return serialize_receipt(db.execute('SELECT * FROM credit_receipts WHERE id=?', (record_id,)).fetchone())
        except BaseException as error:
            path.unlink(missing_ok=True)
            if isinstance(error, sqlite3.IntegrityError):
                raise HTTPException(409, 'رسید با این کد پیگیری قابل ثبت دوباره نیست؛ با مدیر پیگیری کنید.')
            raise

    @app.get('/api/billing/receipts/{record_id}/image')
    def private_receipt(record_id: str, request: Request):
        with connect() as db:
            user = require_user(request, db, real=True)
            row = db.execute('SELECT * FROM credit_receipts WHERE id=?', (record_id,)).fetchone()
            if not row or (row['user_id'] != user['id'] and user['role'] != 'admin') or not Path(row['image_path']).is_file():
                raise HTTPException(404, 'رسید پیدا نشد.')
            return FileResponse(row['image_path'], media_type='image/jpeg')

    @app.get('/api/billing/admin')
    def admin_credit(request: Request):
        with connect() as db:
            require_admin(request, db)
            accounts = []
            for user in db.execute('SELECT id,name,email FROM users WHERE is_demo=0 ORDER BY created_at DESC LIMIT 500'):
                account = credit_account(db, user['id'])
                accounts.append({**dict(user), **{key: account[key] for key in ['balance','purchased','used']}})
            receipts = [serialize_receipt(r) for r in db.execute('SELECT c.*,u.name user_name FROM credit_receipts c JOIN users u ON u.id=c.user_id ORDER BY c.created_at DESC LIMIT 500')]
            return {'config': billing_config(db, services, private=True), 'receipts': receipts, 'accounts': accounts}

    @app.put('/api/billing/admin/bank')
    def update_bank(data: BankInput, request: Request):
        with connect() as db:
            user = require_admin(request, db)
            db.execute('INSERT INTO billing_settings (id,card_number,holder,bank) VALUES (1,?,?,?) ON CONFLICT(id) DO UPDATE SET card_number=excluded.card_number,holder=excluded.holder,bank=excluded.bank', (data.card_number, data.holder, data.bank))
            audit(db, user['id'], 'bank_destination_updated', 'billing')
        return {'ok': True}

    @app.post('/api/billing/admin/receipts/{record_id}/review')
    def review_receipt(record_id: str, data: ReviewInput, request: Request):
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            admin = require_admin(request, db)
            receipt = db.execute('SELECT * FROM credit_receipts WHERE id=?', (record_id,)).fetchone()
            if not receipt:
                raise HTTPException(404, 'رسید پیدا نشد.')
            if receipt['status'] == data.status:
                return {'status': data.status} # Idempotent retries never duplicate credit.
            if receipt['status'] != 'pending':
                raise HTTPException(409, 'رسید قبلاً بررسی شده است.')
            db.execute('UPDATE credit_receipts SET status=?,reason=?,reviewed_at=? WHERE id=?', (data.status, data.reason, now_iso(), record_id))
            if data.status == 'approved':
                db.execute('INSERT INTO credit_ledger VALUES (?,?,?,?,?,?)', (f'purchase-{record_id}', receipt['user_id'], receipt['analyses'], 'purchase', 'تأیید واریز توسط مدیر', now_iso()))
            audit(db, admin['id'], f'receipt_{data.status}', record_id)
        return {'status': data.status}
