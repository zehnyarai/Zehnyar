"""Private field records and moderated experiences; no fabricated/live market data."""
import json
import math
from datetime import date
from typing import Literal
from fastapi import HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .database import connect, now_iso, uid

CATEGORIES = ['مبارزه با آفات', 'کوددهی', 'آبیاری', 'برداشت', 'هرس', 'سایر']
SOIL_LIMITS = {k: 100000 for k in ['nitrogen', 'phosphorus', 'potassium', 'calcium', 'magnesium', 'iron', 'zinc', 'boron']}
SOIL_LIMITS.update(ph=14, ec=100, organic=100, sar=1000)
WATER_LIMITS = {k: 100000 for k in ['tds', 'sodium', 'calcium', 'magnesium', 'chloride', 'boron', 'bicarbonate', 'carbonate', 'nitrate']}
WATER_LIMITS.update(ph=14, ec=100, sar=1000)

class StrictInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class LabInput(StrictInput):
    kind: Literal['soil', 'water']
    values: dict[str, float] = Field(min_length=1, max_length=12)
    method: Literal['saturated', '1:5', '1:2.5', 'unknown', 'water']
    sample_date: date
    depth: str = Field(max_length=80)
    orchard_id: str | None = Field(default=None, max_length=80)
    notes: str = Field(max_length=1000)

    @field_validator('values', mode='before')
    @classmethod
    def numeric_values(cls, value):
        if not isinstance(value, dict) or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in value.values()):
            raise ValueError('Numeric measurements only; missing is not zero')
        return value

    @model_validator(mode='after')
    def measurements(self):
        limits = SOIL_LIMITS if self.kind == 'soil' else WATER_LIMITS
        if any(key not in limits or val < 0 or val > limits[key] for key, val in self.values.items()):
            raise ValueError('Unknown field, unit or measurement outside bounds')
        if self.kind == 'water' and self.method != 'water':
            raise ValueError('Water EC method required')
        if self.kind == 'soil' and self.method == 'water':
            raise ValueError('Soil extraction method required')
        return self

class ExperienceInput(StrictInput):
    title: str = Field(min_length=3, max_length=160)
    category: str
    body: str = Field(min_length=20, max_length=4000)
    province: str = Field(min_length=2, max_length=60)
    cultivar: str = Field(max_length=60)
    season: str = Field(max_length=60)

    @field_validator('category')
    @classmethod
    def category_valid(cls, value):
        if value not in CATEGORIES:
            raise ValueError('Unknown category')
        return value

class MarketInput(StrictInput):
    cultivar: str = Field(min_length=2, max_length=60)
    price: float = Field(gt=0, le=1000000000, allow_inf_nan=False, strict=True)
    currency: Literal['toman', 'usd']
    province: str = Field(min_length=2, max_length=60)
    source: str = Field(min_length=3, max_length=300)
    observed_date: date
    grade: str = Field(max_length=120)

class ClimateInput(StrictInput):
    province: str = Field(min_length=2, max_length=60)
    observed_date: date
    minimum: float = Field(ge=-60, le=65, allow_inf_nan=False, strict=True)
    maximum: float = Field(ge=-60, le=65, allow_inf_nan=False, strict=True)
    humidity: float | None = Field(ge=0, le=100, allow_inf_nan=False, strict=True)
    wind: float | None = Field(ge=0, le=300, allow_inf_nan=False, strict=True)
    stage: str = Field(max_length=60)
    source: str = Field(min_length=3, max_length=300)

    @model_validator(mode='after')
    def temperature_order(self):
        if self.minimum > self.maximum:
            raise ValueError('Minimum exceeds maximum')
        return self

MODELS = {'labs': LabInput, 'experiences': ExperienceInput, 'prices': MarketInput, 'climate': ClimateInput}

def serialize(row):
    return {'id': row['id'], 'author': row['author'], 'visibility': row['visibility'], 'created_at': row['created_at'], 'data': json.loads(row['data'])}

def register_field_routes(app, require_user, require_admin, own_orchard, audit):
    @app.get('/api/field-records/{kind}')
    def get_records(kind: str, request: Request):
        if kind not in MODELS:
            raise HTTPException(404, 'نوع پرونده معتبر نیست.')
        with connect() as db:
            user = require_user(request, db)
            rows = db.execute("SELECT f.*,u.name author FROM field_records f JOIN users u ON u.id=f.user_id WHERE f.kind=? AND (f.user_id=? OR (f.kind='experiences' AND f.visibility='published')) ORDER BY f.created_at DESC LIMIT 500", (kind, user['id']))
            return [serialize(r) for r in rows]

    @app.post('/api/field-records/{kind}', status_code=201)
    async def create_record(kind: str, request: Request):
        if kind not in MODELS:
            raise HTTPException(404, 'نوع پرونده معتبر نیست.')
        try:
            model = MODELS[kind].model_validate(await request.json())
        except (ValueError, TypeError):
            raise HTTPException(422, 'فیلدها، مقادیر یا واحدهای فرم معتبر نیستند.')
        with connect() as db:
            user = require_user(request, db)
            if kind == 'labs':
                own_orchard(db, user['id'], model.orchard_id)
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT COUNT(*) FROM field_records WHERE kind=? AND user_id=?', (kind, user['id'])).fetchone()[0] >= 500:
                raise HTTPException(400, 'سقف ایمنی ۵۰۰ پرونده در این بخش تکمیل شده است.')
            record_id = uid()
            visibility = 'pending' if kind == 'experiences' and not user['is_demo'] else 'private'
            db.execute('INSERT INTO field_records (id,user_id,kind,data,visibility,created_at) VALUES (?,?,?,?,?,?)', (record_id, user['id'], kind, model.model_dump_json(), visibility, now_iso()))
            audit(db, user['id'], 'field_record_created', record_id)
            return serialize(db.execute('SELECT f.*,u.name author FROM field_records f JOIN users u ON u.id=f.user_id WHERE f.id=?', (record_id,)).fetchone())

    @app.delete('/api/field-records/{kind}/{record_id}')
    def delete_record(kind: str, record_id: str, request: Request):
        with connect() as db:
            user = require_user(request, db)
            if not db.execute('DELETE FROM field_records WHERE id=? AND kind=? AND user_id=?', (record_id, kind, user['id'])).rowcount:
                raise HTTPException(404, 'پرونده پیدا نشد.')
            audit(db, user['id'], 'field_record_deleted', record_id)
        return {'ok': True}

    @app.get('/api/admin/experiences')
    def moderate_list(request: Request):
        with connect() as db:
            require_admin(request, db)
            return [serialize(r) for r in db.execute("SELECT f.*,u.name author FROM field_records f JOIN users u ON u.id=f.user_id WHERE f.kind='experiences' ORDER BY f.created_at DESC LIMIT 500")]

    @app.post('/api/admin/experiences/{record_id}/publish')
    def publish_experience(record_id: str, request: Request):
        with connect() as db:
            admin = require_admin(request, db)
            if not db.execute("UPDATE field_records SET visibility='published' WHERE id=? AND kind='experiences' AND visibility='pending'", (record_id,)).rowcount:
                raise HTTPException(409, 'تجربه در وضعیت قابل انتشار نیست.')
            audit(db, admin['id'], 'experience_published', record_id)
        return {'ok': True}
